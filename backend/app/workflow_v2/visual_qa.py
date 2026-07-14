from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import fitz
import httpx
from sqlalchemy.orm import Session

from app.workflow_v2.models import ModelCall, StageRun, WorkflowJob
from app.workflow_v2.state_machine import record_stage_progress

VISUAL_PROMPT_NAME = "independent-page-review-v10-triple-consensus"
ALLOWED_FINDING_CODES = {
    "CLIPPING",
    "OVERLAP",
    "BROKEN_GLYPHS",
    "EXCESSIVE_BLANK_SPACE",
    "OVERSIZED_QR",
    "UNREADABLE_LOW_RESOLUTION_IMAGES",
    "BROKEN_QUESTION_OPTIONS",
    "SPLIT_SENTENCE",
    "MISSING_WRITING_SPACE",
    "WORKFLOW_RESIDUE",
}

class VisualQaError(RuntimeError):
    def __init__(self, message: str, *, attempts: list[dict] | None = None):
        super().__init__(message)
        self.attempts = attempts or []


def review_all_pages(db: Session, *, job: WorkflowJob, stage: StageRun, pdf: Path, render_dir: Path, batch_size: int = 7) -> dict:
    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        raise VisualQaError("DASHSCOPE_API_KEY is unavailable")
    model = os.getenv("DASHSCOPE_VISION_MODEL") or os.getenv("VISION_MODEL") or "qwen3.7-plus"
    document = fitz.open(pdf)
    pdf_sha256 = __import__("hashlib").sha256(pdf.read_bytes()).hexdigest()
    render_dir.mkdir(parents=True, exist_ok=True)
    rendered = []
    for page_number, page in enumerate(document, 1):
        path = render_dir / f"page-{page_number:04d}.png"
        page.get_pixmap(matrix=fitz.Matrix(1.35, 1.35), alpha=False).save(path)
        rendered.append((page_number, path))
    document.close()
    rows = []
    reviewed_pages = set()
    previous_calls = (
        db.query(ModelCall)
        .filter(ModelCall.workflow_job_id == job.id, ModelCall.purpose.like("independent_visual_qa_pages_%"), ModelCall.status == "succeeded")
        .order_by(ModelCall.id.asc())
        .all()
    )
    for call in previous_calls:
        evidence = call.load(call.input_evidence_json, [])
        if call.prompt_version != f"{stage.stage_version}:{VISUAL_PROMPT_NAME}":
            continue
        if not any(isinstance(row, dict) and row.get("pdf_sha256") == pdf_sha256 for row in evidence):
            continue
        for row in call.load(call.result_json, {}).get("pages") or []:
            page = int(row.get("page") or 0)
            image = render_dir / f"page-{page:04d}.png"
            rows.append({"page": page, "image": image.as_posix(), "status": row.get("status") or "failed", "findings": row.get("findings") or [], "summary": str(row.get("summary") or "")})
            reviewed_pages.add(page)
    remaining = [(number, path) for number, path in rendered if number not in reviewed_pages]
    batches = [remaining[offset : offset + batch_size] for offset in range(0, len(remaining), batch_size)]
    with ThreadPoolExecutor(max_workers=min(4, len(batches) or 1)) as executor:
        futures = {executor.submit(_review_batch, batch, api_key=api_key, model=model): batch for batch in batches}
        batch_failures = []
        for future in as_completed(futures):
            batch = futures[future]
            try:
                result, audit = future.result()
            except VisualQaError as exc:
                _record_visual_batch_failure(db, job, stage, pdf_sha256, model, batch, exc)
                batch_failures.append(f"pages {batch[0][0]}-{batch[-1][0]}: {exc}")
                db.commit()
                continue
            _record_visual_batch(db, job, stage, pdf_sha256, model, batch, result, audit, rows)
            if stage.status == "running":
                record_stage_progress(
                    db,
                    job.public_id,
                    step="independent_visual_qa",
                    message="Independent visual QA batch completed.",
                    payload={"reviewed_pages": len({int(row["page"]) for row in rows}), "total_pages": len(rendered), "batch_pages": [number for number, _path in batch]},
                )
            db.commit()
    if batch_failures:
        raise VisualQaError("visual QA batches failed after retries: " + "; ".join(batch_failures))
    rows.sort(key=lambda row: row["page"])
    _discard_blank_space_false_positives(pdf, rows)
    _confirm_failed_pages(db, job=job, stage=stage, pdf_sha256=pdf_sha256, model=model, api_key=api_key, rows=rows)
    _discard_unverified_source_footer_claims(rows)
    if [row["page"] for row in rows] != list(range(1, len(rendered) + 1)):
        raise VisualQaError("visual QA ledger is not a complete ordered page set")
    return {"schema": "luceon.page-review/v2", "review_owner": "independent_qa", "model": model, "pdf_sha256": pdf_sha256, "page_count": len(rows), "pages": rows}


def _confirm_failed_pages(db: Session, *, job: WorkflowJob, stage: StageRun, pdf_sha256: str, model: str, api_key: str, rows: list[dict]) -> None:
    failed = [row for row in rows if row.get("status") == "failed"]
    if not failed:
        return
    with ThreadPoolExecutor(max_workers=min(4, len(failed))) as executor:
        futures = {
            executor.submit(
                _review_confirmation_pair,
                int(row["page"]),
                Path(row["image"]),
                api_key=api_key,
                model=model,
            ): row
            for row in failed
        }
        for future in as_completed(futures):
            row = futures[future]
            page = int(row["page"])
            try:
                confirmations = future.result()
            except VisualQaError as exc:
                _record_visual_batch_failure(db, job, stage, pdf_sha256, model, [(page, Path(row["image"]))], exc)
                db.commit()
                raise
            first, second = confirmations
            row["findings"] = consensus_findings(
                row.get("findings") or [],
                first[0].get("findings") or [],
                second[0].get("findings") or [],
            )
            row["status"] = "failed" if row["findings"] else "passed"
            _record_visual_confirmation(db, job, stage, pdf_sha256, model, page, first[0], first[1], round_number=1)
            _record_visual_confirmation(db, job, stage, pdf_sha256, model, page, second[0], second[1], round_number=2)
            db.commit()
    if stage.status == "running":
        record_stage_progress(
            db,
            job.public_id,
            step="independent_visual_qa_confirmation",
            message="Failed pages received independent single-page confirmation.",
            payload={"initial_failed_pages": len(failed), "confirmed_failed_pages": sum(row.get("status") == "failed" for row in rows)},
        )
        db.commit()


def _review_confirmation_pair(page: int, image: Path, *, api_key: str, model: str):
    calls = []
    for _round in range(2):
        result, audit = _review_batch([(page, image)], api_key=api_key, model=model)
        confirmed = result[0] if len(result) == 1 and int(result[0].get("page") or 0) == page else {}
        calls.append((confirmed, audit))
    return calls


def consensus_findings(initial: list[dict], confirmed: list[dict], second_confirmed: list[dict] | None = None) -> list[dict]:
    confirmed_codes = {str(row.get("code") or "").upper() for row in confirmed}
    if second_confirmed is None:
        return [row for row in initial if str(row.get("code") or "").upper() in confirmed_codes]
    second_codes = {str(row.get("code") or "").upper() for row in second_confirmed}
    return [
        row
        for row in initial
        if str(row.get("code") or "").upper() in confirmed_codes & second_codes
    ]


def _record_visual_confirmation(db, job, stage, pdf_sha256: str, model: str, page: int, result: dict, audit: dict, *, round_number: int) -> None:
    db.add(ModelCall(
        workflow_job_id=job.id,
        stage_run_id=stage.id,
        provider="dashscope",
        model=model,
        response_id=audit["response_id"],
        prompt_version=f"{stage.stage_version}:{VISUAL_PROMPT_NAME}",
        purpose=f"independent_visual_qa_confirmation_{round_number}_page_{page}",
        input_evidence_json=ModelCall.dump([{"pdf_sha256": pdf_sha256, "pages": [page]}]),
        usage_json=ModelCall.dump(audit["usage"]),
        result_json=ModelCall.dump({"page": result, "attempt_count": audit.get("attempt_count", 1)}),
        estimated_cost=None,
        status="succeeded",
        error_message="",
    ))


def _discard_blank_space_false_positives(pdf: Path, rows: list[dict]) -> None:
    document = fitz.open(pdf)
    try:
        for row in rows:
            page = int(row.get("page") or 0)
            if page < 1 or page > len(document):
                continue
            text_length = len(re.sub(r"\s+", "", document[page - 1].get_text("text")))
            findings = []
            for finding in row.get("findings") or []:
                code = str(finding.get("code") or "").upper()
                if code == "EXCESSIVE_BLANK_SPACE" and (
                    text_length >= 500
                    or (text_length >= 150 and _is_followed_by_chapter_start(document, page - 1))
                    or _is_complete_scored_exercise_tail(document, page - 1)
                    or (
                        text_length >= 50
                        and _is_followed_by_chapter_start(document, page - 1)
                        and _horizontal_answer_rule_count(document[page - 1]) >= 2
                    )
                    or (
                        _is_followed_by_chapter_start(document, page - 1)
                        and _horizontal_answer_rule_count(document[page - 1]) >= 4
                    )
                ):
                    continue
                if code == "SPLIT_SENTENCE" and _is_normal_page_continuation(document, page - 1):
                    continue
                if code == "CLIPPING" and _continues_from_previous_page(document, page - 1):
                    continue
                if code == "BROKEN_GLYPHS" and _quoted_token_exists_in_text(finding, document[page - 1].get_text("text")):
                    continue
                findings.append(finding)
            row["findings"] = findings
            row["status"] = "failed" if findings else "passed"
    finally:
        document.close()


def _discard_unverified_source_footer_claims(rows: list[dict]) -> None:
    if not shutil.which("tesseract"):
        return
    for row in rows:
        claims = []
        for finding in row.get("findings") or []:
            code = str(finding.get("code") or "").upper()
            detail = str(finding.get("detail") or "")
            if code not in {"OVERLAP", "WORKFLOW_RESIDUE"}:
                continue
            for quoted in re.findall(r"['‘“]([^'’”]{8,})['’”]", detail):
                if re.search(r"\bSection\s+\d+\b", quoted, re.IGNORECASE):
                    claims.append((finding, quoted))

        if not claims:
            continue
        try:
            result = subprocess.run(
                ["tesseract", str(row["image"]), "stdout", "--psm", "6"],
                check=True,
                text=True,
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        ocr_tokens = set(re.findall(r"[a-z0-9]+", result.stdout.lower()))
        discarded = []
        kept = []
        claimed_findings = {id(finding): quoted for finding, quoted in claims}
        for finding in row.get("findings") or []:
            quoted = claimed_findings.get(id(finding))
            if not quoted:
                kept.append(finding)
                continue
            required = set(re.findall(r"[a-z0-9]+", quoted.lower()))
            if required and len(required & ocr_tokens) / len(required) >= 0.6:
                kept.append(finding)
            else:
                discarded.append({"code": finding.get("code"), "reason": "quoted source footer absent from current-page OCR", "claim": quoted})
        if discarded:
            row.setdefault("evidence_adjustments", []).extend(discarded)
            row["findings"] = kept
            row["status"] = "failed" if kept else "passed"


def _is_normal_page_continuation(document: fitz.Document, page_index: int) -> bool:
    if page_index + 1 >= len(document):
        return False
    current = [line.strip() for line in document[page_index].get_text("text").splitlines() if line.strip()]
    following = [line.strip() for line in document[page_index + 1].get_text("text").splitlines() if line.strip()]
    current = [line for line in current if not line.isdigit()]
    following = [line for line in following if not line.isdigit()]
    if not current or not following:
        return False
    last = current[-1]
    first = following[0]
    if last.endswith(("。", "！", "？", ".", "!", "?", ";", "；", ":", "：")):
        return False
    return not re.match(r"^(Chapter|第\s*\d+\s*章|Quiz|Task\s*\d+|[IVX]+\.)\b", first, re.IGNORECASE)


def _is_followed_by_chapter_start(document: fitz.Document, page_index: int) -> bool:
    if page_index + 1 >= len(document):
        return False
    following = "\n".join(line.strip() for line in document[page_index + 1].get_text("text").splitlines() if line.strip())
    return bool(re.search(r"(^|\n)(Chapter\s+\d+\b|第\s*\d+\s*章)", following, re.IGNORECASE))


def _is_complete_scored_exercise_tail(document: fitz.Document, page_index: int) -> bool:
    if not _is_followed_by_chapter_start(document, page_index):
        return False
    lines = [line.strip() for line in document[page_index].get_text("text").splitlines() if line.strip()]
    lines = [line for line in lines if not line.isdigit()]
    body = " ".join(lines[1:])
    score_marks = re.findall(r"\[\s*\d+\s*\]", body)
    return len(re.sub(r"\s+", "", body)) >= 60 and len(score_marks) >= 2 and bool(re.search(r"\[\s*\d+\s*\]\s*$", body))


def _continues_from_previous_page(document: fitz.Document, page_index: int) -> bool:
    if page_index <= 0:
        return False
    previous = [line.strip() for line in document[page_index - 1].get_text("text").splitlines() if line.strip()]
    current = [line.strip() for line in document[page_index].get_text("text").splitlines() if line.strip()]
    previous = [line for line in previous if not line.isdigit()]
    current = [line for line in current if not line.isdigit()]
    if not previous or not current:
        return False
    return bool(re.match(r"^[a-z]", current[0])) and not previous[-1].endswith(("。", "！", "？", ".", "!", "?"))


def _quoted_token_exists_in_text(finding: dict, page_text: str) -> bool:
    detail = str(finding.get("detail") or "")
    tokens = re.findall(r"['\"‘’“”]([A-Za-z]+(?:['’][A-Za-z]+)?)['\"‘’“”]", detail)
    normalized_page = page_text.replace("’", "'")
    return any(token.replace("’", "'") in normalized_page for token in tokens)


def _horizontal_answer_rule_count(page: fitz.Page) -> int:
    count = 0
    for drawing in page.get_drawings():
        for item in drawing.get("items") or []:
            if item[0] != "l":
                continue
            start, end = item[1], item[2]
            if abs(start.y - end.y) <= 1.0 and abs(start.x - end.x) >= page.rect.width * 0.45:
                count += 1
    return count


def _record_visual_batch(db, job, stage, pdf_sha256: str, model: str, batch, result: list[dict], audit: dict, rows: list[dict]) -> None:
    if len(batch) == 1 and len(result) == 1:
        result[0]["page"] = batch[0][0]
    expected = {page for page, _path in batch}
    returned = {int(row.get("page") or 0) for row in result}
    if returned != expected:
        raise VisualQaError(f"visual QA page set mismatch: expected {sorted(expected)}, got {sorted(returned)}")
    for row in result:
        page = int(row["page"])
        status = str(row.get("status") or "failed").lower()
        if status not in {"passed", "failed"}:
            status = "failed"
        findings = row.get("findings") if isinstance(row.get("findings"), list) else []
        image = next(path for number, path in batch if number == page)
        rows.append({"page": page, "image": image.as_posix(), "status": status, "findings": findings, "summary": str(row.get("summary") or "")})
    db.add(ModelCall(
        workflow_job_id=job.id,
        stage_run_id=stage.id,
        provider="dashscope",
        model=model,
        response_id=audit["response_id"],
        prompt_version=f"{stage.stage_version}:{VISUAL_PROMPT_NAME}",
        purpose=f"independent_visual_qa_pages_{batch[0][0]}_{batch[-1][0]}",
        input_evidence_json=ModelCall.dump([{"pdf_sha256": pdf_sha256, "pages": sorted(expected)}]),
        usage_json=ModelCall.dump(audit["usage"]),
        result_json=ModelCall.dump({
            "pages": result,
            "attempt_count": audit.get("attempt_count", 1),
            "prior_errors": audit.get("prior_errors", []),
        }),
        estimated_cost=None,
        status="succeeded",
        error_message="",
    ))


def _record_visual_batch_failure(db, job, stage, pdf_sha256: str, model: str, batch, error: VisualQaError) -> None:
    expected = sorted(page for page, _path in batch)
    db.add(ModelCall(
        workflow_job_id=job.id,
        stage_run_id=stage.id,
        provider="dashscope",
        model=model,
        response_id="",
        prompt_version=f"{stage.stage_version}:{VISUAL_PROMPT_NAME}",
        purpose=f"independent_visual_qa_pages_{batch[0][0]}_{batch[-1][0]}",
        input_evidence_json=ModelCall.dump([{"pdf_sha256": pdf_sha256, "pages": expected}]),
        usage_json=ModelCall.dump({}),
        result_json=ModelCall.dump({"attempts": error.attempts}),
        estimated_cost=None,
        status="failed",
        error_message=str(error)[:2000],
    ))


def _review_batch(batch: list[tuple[int, Path]], *, api_key: str, model: str) -> tuple[list[dict], dict]:
    pages = [number for number, _path in batch]
    content = [
        {
            "type": "text",
            "text": (
                f"Review the attached rendered textbook pages in order {pages}. Return JSON only: "
                '{"pages":[{"page":number,"status":"passed|failed","findings":[{"code":string,"detail":string}],"summary":string}]}. '
                "Fail clipping, overlap, broken glyphs, excessive blank/orphan space, oversized QR/decorative images, unreadable low-resolution images, broken question options, split sentences, missing writing space, or visible workflow residue. "
                "Use only these finding codes: CLIPPING, OVERLAP, BROKEN_GLYPHS, EXCESSIVE_BLANK_SPACE, OVERSIZED_QR, UNREADABLE_LOW_RESOLUTION_IMAGES, BROKEN_QUESTION_OPTIONS, SPLIT_SENTENCE, MISSING_WRITING_SPACE, WORKFLOW_RESIDUE. "
                "Normal reading-profile metadata (语篇类型, 词数, 难度, 范围, 教材链接), Quiz labels, chapter transitions, and printed folio offsets caused by cover/TOC pages are legitimate and must not be called workflow residue or page-number mismatch. "
                "Normal paragraph continuation across a page boundary is not a split sentence unless text is disconnected, obscured, duplicated, or missing. Blank ruled answer space is intentional writing space. "
                "A short final exercise page immediately before a new chapter is legitimate when its question parts and score marks are complete; do not fail it merely because the remaining area is blank. "
                "Question options may continue on the immediately following supplied page; do not mark them missing or truncated unless the adjacent page also lacks them. "
                "Each image is preceded by its exact rendered page label. Copy that label when assigning the page number; never transfer a finding to another image in the batch. "
                "Report only defects visibly present on that labeled page. Do not infer missing later questions, source mismatch, diagram correctness, or content beyond the page. "
                "A compact textbook exercise does not require added writing space merely because students must calculate; report MISSING_WRITING_SPACE only when a visible answer surface is clearly clipped or collapsed. "
                "Small decorative icons may be low resolution without blocking print; report UNREADABLE_LOW_RESOLUTION_IMAGES only when required instructional text, symbols, or diagrams are unreadable. "
                "Incidental text photographed on a physical object, such as an e-reader, phone screen, shelf label, or background sign shown only as an illustration, is not required instructional text; do not fail it unless the surrounding task explicitly asks the learner to read that text. "
                "Do not judge source completeness, spelling, pedagogy, design preference, or publication readiness. Return exactly one row for every supplied page."
            ),
        }
    ]
    for number, path in batch:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        content.append({"type": "text", "text": f"Rendered page {number}:"})
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}})
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an independent print-layout inspector. You can report findings only; you cannot edit, publish, or waive gates."},
            {"role": "user", "content": content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 1600,
        "enable_thinking": False,
    }
    base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").rstrip("/")
    attempts = []
    for attempt in range(1, 4):
        started = time.monotonic()
        try:
            with httpx.Client(timeout=httpx.Timeout(240, connect=20)) as client:
                response = client.post(f"{base_url}/chat/completions", headers={"Authorization": f"Bearer {api_key}"}, json=payload)
            if response.status_code >= 400:
                raise VisualQaError(f"HTTP {response.status_code}: {response.text[-1000:]}")
            raw = response.json()
            parsed = json.loads(raw["choices"][0]["message"]["content"])
            rows = _normalize_visual_rows(parsed["pages"])
            if not isinstance(rows, list):
                raise VisualQaError("pages must be an array")
            return rows, {
                "response_id": str(raw.get("id") or ""),
                "usage": raw.get("usage") or {},
                "attempt_count": attempt,
                "prior_errors": attempts,
            }
        except (VisualQaError, httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            attempts.append({"attempt": attempt, "elapsed_seconds": round(time.monotonic() - started, 3), "error": str(exc)[:1000]})
            if attempt < 3:
                time.sleep(2 ** (attempt - 1))
    raise VisualQaError("visual QA batch exhausted 3 attempts", attempts=attempts)


def _normalize_visual_rows(rows: object) -> list[dict]:
    if not isinstance(rows, list):
        raise VisualQaError("pages must be an array")
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        findings = []
        for finding in row.get("findings") or []:
            if not isinstance(finding, dict):
                continue
            code = str(finding.get("code") or "").upper()
            detail = str(finding.get("detail") or "")
            if code == "BROKEN_SENTENCE":
                code = "SPLIT_SENTENCE"
            if code == "WORKFLOW_RESIDUE":
                lower = detail.lower()
                if "duplicate" in lower:
                    code = "OVERLAP"
                elif not any(token in lower for token in ("worker", "candidate", "source table evidence", "latex", "json", "file path", "((")):
                    continue
            if code == "SPLIT_SENTENCE" and "page break" in detail.lower() and not any(
                token in detail.lower() for token in ("disconnect", "obscur", "duplicat", "missing")
            ):
                continue
            if code not in ALLOWED_FINDING_CODES:
                continue
            findings.append({"code": code, "detail": detail})
        normalized.append({
            "page": row.get("page"),
            "status": "failed" if findings else "passed",
            "findings": findings,
            "summary": str(row.get("summary") or ""),
        })
    return normalized
