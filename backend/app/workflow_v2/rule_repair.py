from __future__ import annotations

import json
import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import SessionLocal as LegacySessionLocal
from app.models.material import Material
from app.services.codex_print_quality import build_print_quality_report
from app.services.codex_workbook_repair import repair_workbook_project
from app.services.luceon_review import minio_client, read_object
from app.workflow_v2.artifacts import materialize_artifact, publish_stage_directory
from app.workflow_v2.models import ArtifactVersion, QaFinding, RepairAttempt, StageRun, WorkflowJob
from app.workflow_v2.runner import WORK_ROOT, _compile_reproducibly, _material_access_allowed
from app.workflow_v2.source_image_reconstruction import reconstruct_source_images


def apply_current_rule_repairs(db: Session, public_id: str, *, source_artifact_id: int | None = None) -> dict:
    job = db.query(WorkflowJob).filter(WorkflowJob.public_id == public_id).with_for_update().one()
    stage = (
        db.query(StageRun)
        .filter(StageRun.workflow_job_id == job.id, StageRun.stage_key == "independent_final_review", StageRun.status == "failed")
        .order_by(StageRun.attempt.desc())
        .first()
    )
    if not stage:
        raise ValueError("a failed independent review is required")
    source = (
        db.query(ArtifactVersion).filter(ArtifactVersion.id == source_artifact_id, ArtifactVersion.workflow_job_id == job.id).one()
        if source_artifact_id is not None
        else _latest_candidate(db, job.id)
    )
    if not source:
        raise ValueError("a refined candidate is required")
    root = WORK_ROOT / job.public_id / f"rule-repair-after-stage-{stage.id}"
    if root.exists():
        shutil.rmtree(root)
    output = root / "output"
    materialize_artifact(minio_client, source, output)
    project = output / "project"
    blocker_codes = {
        row.code
        for row in db.query(QaFinding).filter(QaFinding.stage_run_id == stage.id, QaFinding.status == "open").all()
    }
    repair_report = repair_workbook_project(project, requested_blockers=blocker_codes)
    legacy_db = LegacySessionLocal()
    try:
        material = legacy_db.query(Material).filter(Material.id == job.material_pk).one()
        if not _material_access_allowed(job, job.load(job.payload_json, {}), material):
            raise ValueError("source material is not accessible to this workflow job")
        source_dir = output / "inputs" / "source"
        source_dir.mkdir(parents=True)
        source_pdf = source_dir / "source.pdf"
        source_pdf.write_bytes(read_object(material.input_bucket, material.input_object))
        image_report = reconstruct_source_images(project, source_pdf)
    finally:
        legacy_db.close()
    (output / "rule-repair-report.json").write_text(json.dumps(repair_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    compile_report = _compile_reproducibly(project, f"{job.public_id}-rule-repair", stage.attempt)
    (output / "rule-repair-compile.json").write_text(json.dumps(compile_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    quality = build_print_quality_report(output, project / "main.pdf")
    (output / "rule-repair-quality.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.rmtree(output / "inputs")
    artifact = publish_stage_directory(
        db,
        minio_client,
        job=job,
        stage=stage,
        source_dir=output,
        artifact_kind="rule-repaired-candidate",
        contract={"schema": "luceon.rule-repaired-candidate/v1", "source_artifact_id": str(source.id), "independent_qa_required": True},
    )
    repair = RepairAttempt(
        workflow_job_id=job.id,
        repair_kind="deterministic_rule_upgrade",
        status="succeeded",
        allowed_scope_json=RepairAttempt.dump({"files": ["project/chapters/content.tex"], "blocker_codes": sorted(blocker_codes)}),
        invariants_json=RepairAttempt.dump({"before": repair_report["before"], "after": repair_report["after"]}),
        result_json=RepairAttempt.dump({
            "source_artifact_id": str(source.id),
            "candidate_artifact_id": str(artifact.id),
            "candidate_sha256": artifact.sha256,
            "quality_status": quality.get("status"),
            "remaining_blockers": [row.get("code") for row in quality.get("hard_blockers") or []],
            "repair_counts": {
                "choice_matrices": repair_report["choice_matrices_regrouped"],
                "qr_figures": repair_report["qr_marketing_figures_removed"],
                "numbering_blocks": repair_report["exercise_numbering_blocks_fixed"],
                "answer_spaces": repair_report["translation_answer_spaces_added"],
                "low_resolution_images": repair_report["low_resolution_images_capped"],
                "source_images_reconstructed": len(image_report["replacements"]),
            },
        }),
        error_message="",
    )
    db.add(repair)
    db.flush()
    return repair.load(repair.result_json, {})


def apply_current_source_image_repairs(db: Session, public_id: str, *, source_artifact_id: int) -> dict:
    job = db.query(WorkflowJob).filter(WorkflowJob.public_id == public_id).with_for_update().one()
    stage = (
        db.query(StageRun)
        .filter(StageRun.workflow_job_id == job.id, StageRun.stage_key == "independent_final_review", StageRun.status == "failed")
        .order_by(StageRun.attempt.desc())
        .first()
    )
    if not stage:
        raise ValueError("a failed independent review is required")
    source = db.query(ArtifactVersion).filter(
        ArtifactVersion.id == source_artifact_id,
        ArtifactVersion.workflow_job_id == job.id,
    ).one()
    root = WORK_ROOT / job.public_id / f"source-image-repair-after-stage-{stage.id}"
    if root.exists():
        shutil.rmtree(root)
    output = root / "output"
    materialize_artifact(minio_client, source, output)
    legacy_db = LegacySessionLocal()
    try:
        material = legacy_db.query(Material).filter(Material.id == job.material_pk).one()
        if not _material_access_allowed(job, job.load(job.payload_json, {}), material):
            raise ValueError("source material is not accessible to this workflow job")
        source_dir = output / "inputs" / "source"
        source_dir.mkdir(parents=True)
        source_pdf = source_dir / "source.pdf"
        source_pdf.write_bytes(read_object(material.input_bucket, material.input_object))
        image_report = reconstruct_source_images(output / "project", source_pdf)
    finally:
        legacy_db.close()
    if not image_report["replacements"] and not image_report["layout_changes"]:
        raise ValueError("no source image repairs matched the candidate")
    (output / "source-image-repair-report.json").write_text(
        json.dumps(image_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    compile_report = _compile_reproducibly(output / "project", f"{job.public_id}-source-image-repair", stage.attempt)
    (output / "source-image-repair-compile.json").write_text(
        json.dumps(compile_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    quality = build_print_quality_report(output, output / "project" / "main.pdf")
    (output / "source-image-repair-quality.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.rmtree(output / "inputs")
    artifact = publish_stage_directory(
        db,
        minio_client,
        job=job,
        stage=stage,
        source_dir=output,
        artifact_kind="rule-repaired-candidate",
        contract={
            "schema": "luceon.source-image-repaired-candidate/v1",
            "source_artifact_id": str(source.id),
            "independent_qa_required": True,
        },
    )
    result = {
        "source_artifact_id": str(source.id),
        "candidate_artifact_id": str(artifact.id),
        "candidate_sha256": artifact.sha256,
        "replacements": image_report["replacements"],
        "layout_changes": image_report["layout_changes"],
    }
    db.add(RepairAttempt(
        workflow_job_id=job.id,
        repair_kind="deterministic_source_image_upgrade",
        status="succeeded",
        allowed_scope_json=RepairAttempt.dump({"files": ["project/images/*"], "source_artifact_id": str(source.id)}),
        invariants_json=RepairAttempt.dump({"latex_text_unchanged": True, "independent_qa_required": True}),
        result_json=RepairAttempt.dump(result),
        error_message="",
    ))
    db.flush()
    return result


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
