from __future__ import annotations

import json
from pathlib import Path

from app.database import SessionLocal as LegacySessionLocal
from app.models.material import Material
from app.services.codex_print_quality import build_print_quality_report
from app.services.luceon_review import minio_client, read_object
from app.workflow_v2.artifacts import publish_stage_directory
from app.workflow_v2.database import workflow_session_factory
from app.workflow_v2.models import QaFinding, StageRun, WorkflowJob


WORK_ROOT = Path("/data/workflow-v2")


def run_preliminary_layout_qa(public_id: str) -> dict:
    db = workflow_session_factory()()
    legacy_db = LegacySessionLocal()
    try:
        job = db.query(WorkflowJob).filter(WorkflowJob.public_id == public_id).one()
        stage = (
            db.query(StageRun)
            .filter(StageRun.workflow_job_id == job.id, StageRun.stage_key == "deterministic_elegantbook", StageRun.status == "succeeded")
            .order_by(StageRun.attempt.desc())
            .first()
        )
        if not stage:
            raise RuntimeError("no succeeded deterministic ElegantBook stage")
        material = legacy_db.query(Material).filter(Material.id == job.material_pk, Material.user_id == job.user_id).one()
        stage_root = WORK_ROOT / public_id / f"deterministic_elegantbook-attempt-{stage.attempt}"
        project = stage_root / "elegantbook"
        pdf = project / "main.pdf"
        if not pdf.exists():
            raise RuntimeError("compiled candidate is unavailable in the stage workspace")
        source_dir = stage_root / "inputs" / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        source_pdf = source_dir / "source.pdf"
        if not source_pdf.exists():
            source_pdf.write_bytes(read_object(material.input_bucket, material.input_object))
        report = build_print_quality_report(stage_root, pdf)
        qa_dir = stage_root / "preliminary-layout-qa"
        qa_dir.mkdir(parents=True, exist_ok=True)
        (qa_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        artifact = publish_stage_directory(
            db,
            minio_client,
            job=job,
            stage=stage,
            source_dir=qa_dir,
            artifact_kind="preliminary-layout-qa",
            contract={"schema": "luceon.preliminary-layout-qa/v1", "publisher_can_accept": False, "independent_of_generation": True},
        )
        existing_codes = {
            row.code
            for row in db.query(QaFinding).filter(QaFinding.workflow_job_id == job.id, QaFinding.stage_run_id == stage.id).all()
        }
        for issue in report.get("hard_blockers") or []:
            code = str(issue.get("code") or "unknown_layout_issue")
            if code in existing_codes:
                continue
            pages = issue.get("pages") if isinstance(issue.get("pages"), list) else []
            db.add(
                QaFinding(
                    workflow_job_id=job.id,
                    stage_run_id=stage.id,
                    code=code,
                    severity="P1",
                    page_number=int(pages[0]) if pages else None,
                    status="open",
                    evidence_artifact_id=artifact.id,
                    details_json=QaFinding.dump(issue),
                )
            )
        db.commit()
        return {"status": report.get("status"), "artifact_id": str(artifact.id), "artifact_sha256": artifact.sha256, "hard_blockers": report.get("hard_blockers") or [], "metrics": report.get("metrics") or {}}
    finally:
        legacy_db.close()
        db.close()
