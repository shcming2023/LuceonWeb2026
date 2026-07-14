from __future__ import annotations

import json
import hashlib
import re
import shutil
from difflib import SequenceMatcher
from pathlib import Path

import fitz
from sqlalchemy.orm import Session

from app.database import SessionLocal as LegacySessionLocal
from app.models.material import Material
from app.services.codex_workbook_repair import choice_option_counts
from app.services.luceon_review import minio_client, read_object
from app.workflow_v2.artifacts import materialize_artifact, publish_stage_directory
from app.workflow_v2.models import ArtifactVersion, QaFinding, RepairAttempt, StageRun, WorkflowJob
from app.workflow_v2.runner import _material_access_allowed


WORK_ROOT = Path("/data/workflow-v2-sidecar")
ALLOWED_PATCH_FILES = ("project/chapters/content.tex", "project/main.tex")


def prepare_codex_repair_request(db: Session, public_id: str) -> tuple[RepairAttempt, ArtifactVersion]:
    job = db.query(WorkflowJob).filter(WorkflowJob.public_id == public_id).with_for_update().one()
    if job.status != "failed" or job.current_stage_key != "independent_final_review":
        raise ValueError("Codex sidecar requires a failed independent final review")
    stage = (
        db.query(StageRun)
        .filter(StageRun.workflow_job_id == job.id, StageRun.stage_key == "independent_final_review", StageRun.status == "failed")
        .order_by(StageRun.attempt.desc())
        .first()
    )
    review = (
        db.query(ArtifactVersion)
        .filter(ArtifactVersion.workflow_job_id == job.id, ArtifactVersion.artifact_kind == "final-review", ArtifactVersion.stage_run_id == stage.id)
        .order_by(ArtifactVersion.id.desc())
        .first()
    )
    if not review:
        raise ValueError("independent final review artifact is missing")
    source_candidate = _latest_candidate(db, job.id)
    if not source_candidate:
        raise ValueError("sidecar source candidate is missing")
    schema = "luceon.codex-targeted-repair-request/v8"
    existing = _queued_repair_for_schema(db, job.id, stage.id, schema)
    if existing:
        return existing
    _supersede_legacy_queued_repairs(db, job.id, stage.id, schema)
    root = WORK_ROOT / job.public_id / f"request-{stage.attempt}"
    if root.exists():
        shutil.rmtree(root)
    review_dir = root / "review"
    request_dir = root / "request"
    materialize_artifact(minio_client, review, review_dir)
    ledger = json.loads((review_dir / "page_review.json").read_text(encoding="utf-8"))
    all_failed_rows = [row for row in ledger.get("pages") or [] if row.get("status") != "passed"]
    if not all_failed_rows:
        raise ValueError("independent review has no failed page rows")
    failed_rows = _select_target_pages(all_failed_rows)
    content_path = review_dir / "project" / "chapters" / "content.tex"
    content = content_path.read_text(encoding="utf-8")
    snippets = _page_snippets(review_dir / "project" / "main.pdf", content, [int(row["page"]) for row in failed_rows])
    request_dir.mkdir(parents=True)
    pages_dir = request_dir / "failed-pages"
    pages_dir.mkdir()
    source_pages_dir = request_dir / "source-pages"
    source_pages_dir.mkdir()
    source_page_numbers = {
        int(source_page)
        for snippet in snippets.values()
        if snippet.get("status") == "mapped"
        for source_page in snippet.get("source_pages") or ([snippet.get("source_page")] if snippet.get("source_page") else [])
    }
    source_page_evidence = _render_source_pages(job, source_page_numbers, source_pages_dir)
    page_rows = []
    for row in failed_rows:
        page = int(row["page"])
        source = review_dir / str(row["image"])
        target = pages_dir / f"page-{page:04d}.png"
        shutil.copy2(source, target)
        snippet = snippets.get(page, {})
        source_page = int(snippet.get("source_page") or 0)
        source_pages = [int(value) for value in snippet.get("source_pages") or ([source_page] if source_page else [])]
        page_rows.append(
            {
                "page": page,
                "image": target.relative_to(request_dir).as_posix(),
                "findings": row.get("findings") or [],
                "latex_snippet": snippet,
                "source_page_evidence": source_page_evidence.get(source_page, {"status": "unmapped"}),
                "source_pages_evidence": [source_page_evidence[value] for value in source_pages if value in source_page_evidence],
            }
        )
    invariants = _latex_invariants(content)
    request = {
        "schema": schema,
        "workflow_job_id": job.public_id,
        "material_id": job.material_id,
        "source_review_artifact": {"id": str(review.id), "sha256": review.sha256},
        "source_candidate_artifact": {"id": str(source_candidate.id), "sha256": source_candidate.sha256},
        "allowed_patch_files": list(ALLOWED_PATCH_FILES),
        "forbidden_operations": ["database_write", "minio_publish", "workflow_retry", "source_content_invention", "qa_waiver"],
        "protected_invariants": invariants,
        "all_failed_page_count": len(all_failed_rows),
        "targeted_page_count": len(page_rows),
        "failed_pages": page_rows,
        "response_schema": {"patch_file": "repair.diff", "rationale_file": "rationale.json", "rule_suggestions_file": "rule-suggestions.json"},
    }
    (request_dir / "request.json").write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    artifact = publish_stage_directory(db, minio_client, job=job, stage=stage, source_dir=request_dir, artifact_kind="codex-repair-request", contract={"schema": request["schema"], "patch_only": True, "allowed_files": list(ALLOWED_PATCH_FILES)})
    finding = db.query(QaFinding).filter(QaFinding.workflow_job_id == job.id, QaFinding.stage_run_id == stage.id, QaFinding.status == "open").order_by(QaFinding.id).first()
    repair = RepairAttempt(
        workflow_job_id=job.id,
        source_finding_id=finding.id if finding else None,
        repair_kind="codex_sidecar_patch",
        status="queued",
        allowed_scope_json=RepairAttempt.dump({"files": list(ALLOWED_PATCH_FILES), "failed_pages": [row["page"] for row in page_rows]}),
        invariants_json=RepairAttempt.dump(invariants),
        result_json=RepairAttempt.dump({"request_artifact_id": str(artifact.id), "request_artifact_sha256": artifact.sha256, "request_schema": schema}),
        error_message="",
    )
    db.add(repair)
    db.flush()
    return repair, artifact


def _queued_repair_for_schema(
    db: Session,
    job_id: int,
    stage_id: int,
    schema: str,
) -> tuple[RepairAttempt, ArtifactVersion] | None:
    repairs = (
        db.query(RepairAttempt)
        .filter(
            RepairAttempt.workflow_job_id == job_id,
            RepairAttempt.repair_kind == "codex_sidecar_patch",
            RepairAttempt.status == "queued",
        )
        .order_by(RepairAttempt.id.desc())
        .all()
    )
    for repair in repairs:
        artifact_id = int(repair.load(repair.result_json, {}).get("request_artifact_id") or 0)
        artifact = db.query(ArtifactVersion).filter(ArtifactVersion.id == artifact_id).one_or_none()
        if not artifact or artifact.stage_run_id != stage_id:
            continue
        if repair.load(repair.result_json, {}).get("request_schema") == schema:
            return repair, artifact
    return None


def _supersede_legacy_queued_repairs(db: Session, job_id: int, stage_id: int, schema: str) -> None:
    repairs = (
        db.query(RepairAttempt)
        .filter(
            RepairAttempt.workflow_job_id == job_id,
            RepairAttempt.repair_kind == "codex_sidecar_patch",
            RepairAttempt.status == "queued",
        )
        .all()
    )
    for repair in repairs:
        artifact_id = int(repair.load(repair.result_json, {}).get("request_artifact_id") or 0)
        artifact = db.query(ArtifactVersion).filter(ArtifactVersion.id == artifact_id).one_or_none()
        if not artifact or artifact.stage_run_id != stage_id:
            continue
        old_schema = str(repair.load(repair.result_json, {}).get("request_schema") or "")
        if old_schema != schema:
            repair.status = "failed"
            repair.error_message = f"superseded by sidecar request schema {schema}"


def _latest_candidate(db: Session, job_id: int) -> ArtifactVersion | None:
    return (
        db.query(ArtifactVersion)
        .filter(
            ArtifactVersion.workflow_job_id == job_id,
            ArtifactVersion.artifact_kind.in_(("rule-repaired-candidate", "codex-patched-candidate", "refined-candidate")),
        )
        .order_by(ArtifactVersion.id.desc())
        .first()
    )


def _page_snippets(pdf: Path, content: str, pages: list[int]) -> dict[int, dict]:
    lines = content.splitlines()
    normalized = [_normalize_latex_line(line) for line in lines]
    document = fitz.open(pdf)
    page_lines = []
    line_frequency: dict[str, int] = {}
    for page in document:
        values = {_normalize(line) for line in page.get_text("text").splitlines() if len(_normalize(line)) >= 12}
        page_lines.append(values)
        for value in values:
            line_frequency[value] = line_frequency.get(value, 0) + 1
    result = {}
    for page_number in pages:
        anchors = sorted((value for value in page_lines[page_number - 1] if line_frequency.get(value, 0) <= 2), key=len, reverse=True)
        matched_indices = []
        for anchor in anchors:
            needle = anchor[:96]
            matches = [index for index, line in enumerate(normalized) if needle in line or (len(line) >= 32 and line[:96] in anchor)]
            if len(matches) == 1:
                matched_indices.append(matches[0])
        matched_indices = sorted(set(matched_indices))
        if not matched_indices:
            fuzzy_match = _best_fuzzy_anchor(anchors, normalized)
            if fuzzy_match is not None:
                matched_indices = [fuzzy_match]
        if not matched_indices:
            result[page_number] = {"status": "unmapped", "reason": "No reliable local LaTeX anchor found; Codex must not edit this page."}
            continue
        matched_indices = _densest_bounded_anchor_window(matched_indices, max_span=160)
        first_match = matched_indices[0]
        last_match = matched_indices[-1]
        start = max(0, first_match - 70)
        end = min(len(lines), last_match + 71)
        result[page_number] = {
            "status": "mapped",
            "file": "project/chapters/content.tex",
            "start_line": start + 1,
            "end_line": end,
            "source_page": _source_page_for_line(lines, first_match),
            "source_pages": _source_pages_for_window(lines, start, end),
            "text": "\n".join(lines[start:end]),
        }
    document.close()
    return result


def _densest_bounded_anchor_window(indices: list[int], *, max_span: int) -> list[int]:
    """Keep the strongest local page cluster when repeated material creates remote anchors."""
    best = indices[:1]
    right = 0
    for left, start in enumerate(indices):
        right = max(right, left)
        while right + 1 < len(indices) and indices[right + 1] - start <= max_span:
            right += 1
        candidate = indices[left : right + 1]
        if len(candidate) > len(best) or (len(candidate) == len(best) and candidate[-1] - candidate[0] < best[-1] - best[0]):
            best = candidate
    return best


def _best_fuzzy_anchor(anchors: list[str], normalized_lines: list[str]) -> int | None:
    candidates: dict[int, float] = {}
    for anchor in anchors[:12]:
        for index, line in enumerate(normalized_lines):
            if len(line) < 32:
                continue
            score = SequenceMatcher(None, anchor[:160], line[:160], autojunk=False).ratio()
            candidates[index] = max(candidates.get(index, 0.0), score)
    ranked = sorted(candidates.items(), key=lambda row: row[1], reverse=True)
    if not ranked or ranked[0][1] < 0.72:
        return None
    if len(ranked) > 1 and ranked[0][1] - ranked[1][1] < 0.08:
        return None
    return ranked[0][0]


SOURCE_PAGE_MARKER_RE = re.compile(r"source.*?idx.*?:\s*(\d+)", re.I)


def _source_page_for_line(lines: list[str], line_index: int) -> int | None:
    for line in reversed(lines[: line_index + 1]):
        match = SOURCE_PAGE_MARKER_RE.search(line)
        if match:
            return int(match.group(1)) + 1
    return None


def _source_pages_for_window(lines: list[str], start: int, end: int) -> list[int]:
    pages = []
    preceding = _source_page_for_line(lines, start)
    if preceding:
        pages.append(preceding)
    for line in lines[start:end]:
        match = SOURCE_PAGE_MARKER_RE.search(line)
        if match:
            page = int(match.group(1)) + 1
            if page not in pages:
                pages.append(page)
    return pages


def _render_source_pages(job: WorkflowJob, pages: set[int], destination: Path) -> dict[int, dict]:
    if not pages:
        return {}
    legacy_db = LegacySessionLocal()
    try:
        material = legacy_db.query(Material).filter(Material.id == job.material_pk).one()
        if not _material_access_allowed(job, job.load(job.payload_json, {}), material):
            raise ValueError("sidecar source material is not accessible to this workflow job")
        source_pdf = read_object(material.input_bucket, material.input_object)
    finally:
        legacy_db.close()
    document = fitz.open(stream=source_pdf, filetype="pdf")
    result = {}
    try:
        for page_number in sorted(pages):
            if page_number < 1 or page_number > document.page_count:
                result[page_number] = {"status": "out_of_range", "page": page_number}
                continue
            target = destination / f"source-page-{page_number:04d}.png"
            document[page_number - 1].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False).save(target)
            result[page_number] = {
                "status": "mapped",
                "page": page_number,
                "image": target.relative_to(destination.parent).as_posix(),
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            }
    finally:
        document.close()
    return result


def _latex_invariants(text: str) -> dict:
    return {
        "chapter_count": len(re.findall(r"\\chapter\*?\s*\{", text)),
        "exercise_heading_count": len(re.findall(r"\\exerciseheading\s*\{", text)),
        "answer_surface_count": len(re.findall(r"\\(?:workbookanswerspace|printanswerline|printshortanswer|printmediumanswer|printlonganswer|printlistanswer|printwritingbox|printchapterendwritingbox)\b", text)),
        "explicit_writing_rule_count": len(re.findall(r"\\rule\{0?\.(?:[3-9]|\d{2,})\\linewidth\}\{0\.4pt\}", text)),
        "choice_option_counts": choice_option_counts(text),
    }


def _normalize(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value).lower()


def _normalize_latex_line(value: str) -> str:
    formatting_commands = r"(?:frac|dfrac|tfrac|quad|qquad|text|textrm|textsf|texttt|mathrm|mathbf|mathit|operatorname|left|right)"
    return _normalize(re.sub(rf"\\{formatting_commands}\*?", "", value))


def _select_target_pages(rows: list[dict], limit: int = 12) -> list[dict]:
    selected = []
    selected_pages = set()
    by_code: dict[str, list[dict]] = {}
    for row in rows:
        codes = {str(item.get("code") or "visual_failure") for item in row.get("findings") or [] if isinstance(item, dict)} or {"visual_failure"}
        for code in codes:
            by_code.setdefault(code, []).append(row)
    for code in sorted(by_code):
        for row in by_code[code]:
            page = int(row.get("page") or 0)
            if page not in selected_pages:
                selected.append(row)
                selected_pages.add(page)
                break
        if len(selected) >= limit:
            return sorted(selected, key=lambda row: int(row["page"]))
    for row in rows:
        page = int(row.get("page") or 0)
        if page not in selected_pages:
            selected.append(row)
            selected_pages.add(page)
        if len(selected) >= limit:
            break
    return sorted(selected, key=lambda row: int(row["page"]))
