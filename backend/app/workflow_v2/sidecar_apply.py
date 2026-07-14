from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import SessionLocal as LegacySessionLocal
from app.models.material import Material
from app.services.codex_print_quality import build_print_quality_report
from app.services.luceon_review import minio_client, read_object
from app.workflow_v2.artifacts import materialize_artifact, publish_stage_directory
from app.workflow_v2.models import ArtifactVersion, RepairAttempt, StageRun, WorkflowJob
from app.workflow_v2.runner import _compile_reproducibly, _material_access_allowed
from app.workflow_v2.sidecar import _latex_invariants
from app.workflow_v2.state_machine import retry_failed_stage


DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$", re.M)
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@", re.M)


def register_codex_response(db: Session, *, repair_id: int, response_dir: Path) -> dict:
    repair = db.query(RepairAttempt).filter(RepairAttempt.id == repair_id).with_for_update().one()
    if repair.repair_kind != "codex_sidecar_patch" or repair.status != "queued":
        raise ValueError("Codex repair is not awaiting a response")
    job = db.query(WorkflowJob).filter(WorkflowJob.id == repair.workflow_job_id).one()
    stage = db.query(StageRun).filter(StageRun.id == _latest_failed_review_stage_id(db, job.id)).one()
    request_artifact_id = int(repair.load(repair.result_json, {}).get("request_artifact_id") or 0)
    request_artifact = db.query(ArtifactVersion).filter(ArtifactVersion.id == request_artifact_id).one()
    request_root = Path("/data/workflow-v2-sidecar") / job.public_id / f"register-{repair.id}" / "request"
    if request_root.parent.exists():
        shutil.rmtree(request_root.parent)
    materialize_artifact(minio_client, request_artifact, request_root)
    request = json.loads((request_root / "request.json").read_text(encoding="utf-8"))
    validation = validate_codex_response(response_dir, request)
    response_artifact = publish_stage_directory(
        db,
        minio_client,
        job=job,
        stage=stage,
        source_dir=response_dir,
        artifact_kind="codex-repair-response",
        contract={"schema": "luceon.codex-targeted-repair-response/v1", "validation": validation},
    )
    result = repair.load(repair.result_json, {})
    result.update({
        "response_artifact_id": str(response_artifact.id),
        "response_artifact_sha256": response_artifact.sha256,
        "response_validation": validation,
    })
    repair.result_json = RepairAttempt.dump(result)
    db.flush()
    return {"repair_id": str(repair.id), "response_artifact_id": str(response_artifact.id), "validation": validation}


def run_registered_codex_repair(public_id: str, repair_id: int) -> dict:
    from app.workflow_v2.database import workflow_session_factory

    db = workflow_session_factory()()
    try:
        job = db.query(WorkflowJob).filter(WorkflowJob.public_id == public_id).one()
        repair = db.query(RepairAttempt).filter(
            RepairAttempt.id == repair_id,
            RepairAttempt.workflow_job_id == job.id,
        ).with_for_update().one()
        response_artifact_id = int(repair.load(repair.result_json, {}).get("response_artifact_id") or 0)
        if repair.status != "queued" or not response_artifact_id:
            raise ValueError("Codex repair response is not ready to apply")
        response_artifact = db.query(ArtifactVersion).filter(ArtifactVersion.id == response_artifact_id).one()
        response_dir = Path("/data/workflow-v2-sidecar") / public_id / f"registered-response-{repair_id}"
        if response_dir.exists():
            shutil.rmtree(response_dir)
        materialize_artifact(minio_client, response_artifact, response_dir)
        result = apply_codex_repair(db, repair_id=repair_id, response_dir=response_dir)
        _, retry = retry_failed_stage(db, public_id)
        db.commit()
        return {
            "ok": True,
            "kind": "codex_repair",
            "job_id": public_id,
            "repair_id": str(repair_id),
            "job_status": "queued",
            "review_attempt": retry.attempt,
            "result": result,
        }
    except Exception as exc:
        db.rollback()
        try:
            repair = db.query(RepairAttempt).filter(RepairAttempt.id == repair_id).one_or_none()
            if repair and repair.status == "queued":
                repair.status = "failed"
                repair.error_message = str(exc)[:2000]
                repair.finished_at = datetime.utcnow()
                db.commit()
        except Exception:
            db.rollback()
        return {"ok": False, "kind": "codex_repair", "job_id": public_id, "repair_id": str(repair_id), "error": str(exc)}
    finally:
        db.close()


def apply_codex_repair(db: Session, *, repair_id: int, response_dir: Path) -> dict:
    repair = db.query(RepairAttempt).filter(RepairAttempt.id == repair_id).with_for_update().one()
    job = db.query(WorkflowJob).filter(WorkflowJob.id == repair.workflow_job_id).one()
    stage = db.query(StageRun).filter(StageRun.id == _latest_failed_review_stage_id(db, job.id)).one()
    request_artifact_id = int(repair.load(repair.result_json, {}).get("request_artifact_id") or 0)
    request_artifact = db.query(ArtifactVersion).filter(ArtifactVersion.id == request_artifact_id).one()
    request_root = Path("/data/workflow-v2-sidecar") / job.public_id / f"apply-{repair.id}" / "request"
    work_root = request_root.parent
    if work_root.exists():
        shutil.rmtree(work_root)
    materialize_artifact(minio_client, request_artifact, request_root)
    request = json.loads((request_root / "request.json").read_text(encoding="utf-8"))
    validation = validate_codex_response(response_dir, request)
    publishable_response = work_root / "response"
    publishable_response.mkdir()
    for name in ("repair.diff", "rationale.json", "rule-suggestions.json"):
        shutil.copy2(response_dir / name, publishable_response / name)
    patch_artifact = publish_stage_directory(db, minio_client, job=job, stage=stage, source_dir=publishable_response, artifact_kind="codex-repair-patch", contract={"schema": "luceon.codex-targeted-repair-response/v1", "validation": validation})
    source_candidate_data = request.get("source_candidate_artifact") or {}
    source_candidate_id = int(source_candidate_data.get("id") or 0)
    refined = db.query(ArtifactVersion).filter(ArtifactVersion.id == source_candidate_id, ArtifactVersion.workflow_job_id == job.id).one_or_none()
    if not refined or refined.sha256 != source_candidate_data.get("sha256"):
        raise ValueError("locked sidecar source candidate is missing or changed")
    output = work_root / "candidate"
    materialize_artifact(minio_client, refined, output)
    before_path = output / "project" / "chapters" / "content.tex"
    before = _latex_invariants(before_path.read_text(encoding="utf-8"))
    subprocess.run(["git", "apply", "--recount", "--check", str(response_dir / "repair.diff")], cwd=output, check=True, text=True, capture_output=True)
    subprocess.run(["git", "apply", "--recount", str(response_dir / "repair.diff")], cwd=output, check=True, text=True, capture_output=True)
    after = _latex_invariants(before_path.read_text(encoding="utf-8"))
    _assert_invariants(request["protected_invariants"], before, after)
    compile_report = _compile_reproducibly(output / "project", f"{job.public_id}-codex-repair-{repair.id}", repair.id)
    (output / "codex-repair-validation.json").write_text(json.dumps({"validation": validation, "before": before, "after": after, "compile": compile_report}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    legacy_db = LegacySessionLocal()
    try:
        material = legacy_db.query(Material).filter(Material.id == job.material_pk).one()
        if not _material_access_allowed(job, job.load(job.payload_json, {}), material):
            raise ValueError("sidecar source material is not accessible to this workflow job")
        inputs = output / "inputs" / "source"
        inputs.mkdir(parents=True)
        (inputs / "source.pdf").write_bytes(read_object(material.input_bucket, material.input_object))
        quality = build_print_quality_report(output, output / "project" / "main.pdf")
        (output / "post-codex-quality-report.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.rmtree(output / "inputs")
    finally:
        legacy_db.close()
    candidate_artifact = publish_stage_directory(db, minio_client, job=job, stage=stage, source_dir=output, artifact_kind="codex-patched-candidate", contract={"schema": "luceon.codex-patched-candidate/v1", "source_patch_artifact_id": str(patch_artifact.id), "independent_qa_required": True})
    repair.status = "succeeded"
    repair.finished_at = datetime.utcnow()
    repair.patch_artifact_id = patch_artifact.id
    result = repair.load(repair.result_json, {})
    result.update({"patch_validation": validation, "candidate_artifact_id": str(candidate_artifact.id), "candidate_sha256": candidate_artifact.sha256, "post_patch_quality_status": quality.get("status"), "remaining_blockers": [row.get("code") for row in quality.get("hard_blockers") or []]})
    repair.result_json = RepairAttempt.dump(result)
    db.flush()
    return result


def validate_codex_response(response_dir: Path, request: dict) -> dict:
    required = ["repair.diff", "rationale.json", "rule-suggestions.json"]
    missing = [name for name in required if not (response_dir / name).is_file()]
    if missing:
        raise ValueError(f"Codex response is incomplete: {', '.join(missing)}")
    diff = (response_dir / "repair.diff").read_text(encoding="utf-8")
    rationale = json.loads((response_dir / "rationale.json").read_text(encoding="utf-8"))
    suggestions = json.loads((response_dir / "rule-suggestions.json").read_text(encoding="utf-8"))
    files = sorted(set(DIFF_FILE_RE.findall(diff)))
    allowed = set(request.get("allowed_patch_files") or [])
    if not files or set(files) - allowed:
        raise ValueError(f"Codex patch touched disallowed files: {files}")
    windows = {}
    for row in request.get("failed_pages") or []:
        snippet = row.get("latex_snippet") if isinstance(row.get("latex_snippet"), dict) else {}
        if snippet.get("status") == "mapped":
            windows.setdefault(snippet.get("file"), []).append((int(snippet["start_line"]), int(snippet["end_line"]), int(row["page"])))
    hunks = []
    for start_raw, count_raw in HUNK_RE.findall(diff):
        start = int(start_raw)
        count = int(count_raw or 1)
        end = start + max(count, 1) - 1
        matches = [(window_start, window_end, page) for window_start, window_end, page in windows.get(files[0], []) if start >= window_start - 3 and end <= window_end + 3]
        if not matches:
            raise ValueError(f"Codex hunk {start}-{end} is outside mapped repair windows")
        hunks.append({"start_line": start, "end_line": end, "evidence_pages": sorted({page for _a, _b, page in matches})})
    if not hunks:
        raise ValueError("Codex patch contains no hunks")
    return {"files": files, "hunks": hunks, "rationale_valid": isinstance(rationale, dict), "rule_suggestions_valid": isinstance(suggestions, (dict, list))}


def _assert_invariants(protected: dict, before: dict, after: dict) -> None:
    if before.get("chapter_count") != after.get("chapter_count") or after.get("chapter_count") != protected.get("chapter_count"):
        raise ValueError("Codex patch changed protected invariant: chapter_count")
    if before.get("exercise_heading_count") != protected.get("exercise_heading_count"):
        raise ValueError("Codex patch source does not match protected invariant: exercise_heading_count")
    if after.get("exercise_heading_count", 0) < before.get("exercise_heading_count", 0):
        raise ValueError("Codex patch removed protected exercise headings")
    before_answers = before.get("answer_surface_count", 0) + before.get("explicit_writing_rule_count", 0)
    after_answers = after.get("answer_surface_count", 0) + after.get("explicit_writing_rule_count", 0)
    if after_answers < before_answers:
        raise ValueError("Codex patch removed answer surfaces")
    for label, count in (protected.get("choice_option_counts") or {}).items():
        if int(after.get("choice_option_counts", {}).get(label, 0)) < int(count):
            raise ValueError(f"Codex patch removed {label} choices")


def _latest_failed_review_stage_id(db: Session, job_id: int) -> int:
    stage = db.query(StageRun).filter(StageRun.workflow_job_id == job_id, StageRun.stage_key == "independent_final_review", StageRun.status == "failed").order_by(StageRun.attempt.desc()).first()
    if not stage:
        raise ValueError("failed final review stage is missing")
    return stage.id
