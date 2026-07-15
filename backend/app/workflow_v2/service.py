from __future__ import annotations

import hashlib
import uuid

from sqlalchemy.orm import Session

from app.models.material import Material
from app.workflow_v2.contracts import STAGE_CONTRACTS, WORKFLOW_VERSION
from app.workflow_v2.models import ArtifactVersion, ModelCall, QaFinding, RepairAttempt, StageEvent, StageRun, WorkflowJob


def create_workflow_job(
    db: Session,
    *,
    user_id: str,
    material: Material,
    payload: dict | None = None,
    priority: int = 100,
) -> tuple[WorkflowJob, bool]:
    if not material.material_id:
        raise ValueError("material_id is required")
    if not material.popo_manifest_bucket or not material.popo_manifest_object:
        raise ValueError("Popo manifest is required")
    idempotency_key = workflow_idempotency_key(material, user_id)
    existing = db.query(WorkflowJob).filter(WorkflowJob.idempotency_key == idempotency_key).first()
    if existing:
        return existing, False

    job = WorkflowJob(
        public_id=str(uuid.uuid4()),
        user_id=user_id,
        material_pk=int(material.id),
        material_id=material.material_id,
        source_popo_bucket=material.popo_manifest_bucket,
        source_popo_object=material.popo_manifest_object,
        workflow_version=WORKFLOW_VERSION,
        status="queued",
        current_stage_key=STAGE_CONTRACTS[0].key,
        idempotency_key=idempotency_key,
        priority=priority,
        payload_json=WorkflowJob.dump(payload or {}),
    )
    db.add(job)
    db.flush()
    for contract in STAGE_CONTRACTS:
        db.add(
            StageRun(
                workflow_job_id=job.id,
                stage_key=contract.key,
                stage_version=contract.version,
                attempt=1,
                status="queued" if contract.order == STAGE_CONTRACTS[0].order else "pending",
                owner=contract.owner,
            )
        )
    db.add(
        StageEvent(
            workflow_job_id=job.id,
            event_type="job_created",
            level="info",
            message="Worker V2.3 job recorded; no production stage has executed yet.",
            payload_json=StageEvent.dump(
                {
                    "workflow_version": WORKFLOW_VERSION,
                    "first_stage": STAGE_CONTRACTS[0].key,
                    "legacy_outputs_preserved": True,
                }
            ),
        )
    )
    db.flush()
    return job, True


def workflow_idempotency_key(material: Material, user_id: str) -> str:
    value = "\n".join(
        [
            user_id,
            material.material_id or "",
            material.popo_manifest_bucket or "",
            material.popo_manifest_object or "",
            WORKFLOW_VERSION,
        ]
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def workflow_job_detail(db: Session, public_id: str) -> dict | None:
    job = db.query(WorkflowJob).filter(WorkflowJob.public_id == public_id).first()
    if not job:
        return None
    stages = (
        db.query(StageRun)
        .filter(StageRun.workflow_job_id == job.id)
        .order_by(StageRun.id.asc())
        .all()
    )
    events = (
        db.query(StageEvent)
        .filter(StageEvent.workflow_job_id == job.id)
        .order_by(StageEvent.id.asc())
        .all()
    )
    artifacts = db.query(ArtifactVersion).filter(ArtifactVersion.workflow_job_id == job.id).order_by(ArtifactVersion.id.asc()).all()
    model_calls = db.query(ModelCall).filter(ModelCall.workflow_job_id == job.id).order_by(ModelCall.id.asc()).all()
    findings = db.query(QaFinding).filter(QaFinding.workflow_job_id == job.id).order_by(QaFinding.id.asc()).all()
    repairs = db.query(RepairAttempt).filter(RepairAttempt.workflow_job_id == job.id).order_by(RepairAttempt.id.asc()).all()
    return {
        **job.to_dict(),
        "stages": [stage.to_dict() for stage in stages],
        "events": [event.to_dict() for event in events],
        "artifacts": [_artifact_dict(row) for row in artifacts],
        "model_calls": [_model_call_dict(row) for row in model_calls],
        "qa_findings": [_finding_dict(row) for row in findings],
        "repair_attempts": [_repair_dict(row) for row in repairs],
    }


def list_workflow_jobs(db: Session, *, user_id: str, material_pk: int | None = None, limit: int = 50) -> list[dict]:
    query = db.query(WorkflowJob).filter(WorkflowJob.user_id == user_id)
    if material_pk is not None:
        query = query.filter(WorkflowJob.material_pk == material_pk)
    jobs = query.order_by(WorkflowJob.created_at.desc()).limit(min(max(limit, 1), 200)).all()
    return [workflow_job_detail(db, job.public_id) for job in jobs]


def _workflow_job_summary(db: Session, job: WorkflowJob) -> dict:
    stages = db.query(StageRun).filter(StageRun.workflow_job_id == job.id).order_by(StageRun.id.asc()).all()
    current = [stage for stage in stages if stage.stage_key == job.current_stage_key]
    current_stage = max(current, key=lambda stage: stage.attempt) if current else None
    return {
        "id": job.public_id,
        "material_pk": str(job.material_pk),
        "material_id": job.material_id,
        "source_popo_manifest": {"bucket": job.source_popo_bucket, "object": job.source_popo_object},
        "workflow_version": job.workflow_version,
        "is_current_workflow": job.workflow_version == WORKFLOW_VERSION,
        "status": job.status,
        "current_stage_key": job.current_stage_key,
        "current_stage_status": current_stage.status if current_stage else "",
        "current_attempt": current_stage.attempt if current_stage else 0,
        "stages": [{"key": stage.stage_key, "attempt": stage.attempt, "status": stage.status} for stage in stages],
        "event_count": db.query(StageEvent).filter(StageEvent.workflow_job_id == job.id).count(),
        "artifact_count": db.query(ArtifactVersion).filter(ArtifactVersion.workflow_job_id == job.id).count(),
        "model_call_count": db.query(ModelCall).filter(ModelCall.workflow_job_id == job.id).count(),
        "open_finding_count": db.query(QaFinding).filter(QaFinding.workflow_job_id == job.id, QaFinding.status == "open").count(),
        "error": {"code": job.error_code, "message": job.error_message},
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


def list_workflow_job_summaries(db: Session, *, user_id: str, limit: int = 200) -> list[dict]:
    jobs = db.query(WorkflowJob).filter(WorkflowJob.user_id == user_id).order_by(WorkflowJob.created_at.desc()).limit(min(max(limit, 1), 500)).all()
    return [_workflow_job_summary(db, job) for job in jobs]


def list_workflow_job_summary_page(
    db: Session,
    *,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    status: str = "",
) -> dict:
    query = db.query(WorkflowJob).filter(WorkflowJob.user_id == user_id)
    if status:
        query = query.filter(WorkflowJob.status == status)
    total = query.count()
    jobs = (
        query.order_by(WorkflowJob.created_at.desc(), WorkflowJob.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "jobs": [_workflow_job_summary(db, job) for job in jobs],
    }


def _artifact_dict(row: ArtifactVersion) -> dict:
    return {"id": str(row.id), "stage_run_id": str(row.stage_run_id), "kind": row.artifact_kind, "bucket": row.bucket, "object": row.object_name, "sha256": row.sha256, "size_bytes": row.size_bytes, "status": row.status, "immutable": row.immutable, "metadata": row.load(row.metadata_json, {}), "created_at": row.created_at.isoformat() if row.created_at else None}


def _model_call_dict(row: ModelCall) -> dict:
    return {"id": str(row.id), "stage_run_id": str(row.stage_run_id), "provider": row.provider, "model": row.model, "response_id": row.response_id, "prompt_version": row.prompt_version, "purpose": row.purpose, "input_evidence": row.load(row.input_evidence_json, []), "usage": row.load(row.usage_json, {}), "result": row.load(row.result_json, {}), "estimated_cost": str(row.estimated_cost) if row.estimated_cost is not None else None, "status": row.status, "error_message": row.error_message}


def _finding_dict(row: QaFinding) -> dict:
    return {"id": str(row.id), "stage_run_id": str(row.stage_run_id), "code": row.code, "severity": row.severity, "page_number": row.page_number, "status": row.status, "evidence_artifact_id": str(row.evidence_artifact_id) if row.evidence_artifact_id else "", "details": row.load(row.details_json, {})}


def _repair_dict(row: RepairAttempt) -> dict:
    return {"id": str(row.id), "source_finding_id": str(row.source_finding_id) if row.source_finding_id else "", "repair_kind": row.repair_kind, "status": row.status, "allowed_scope": row.load(row.allowed_scope_json, {}), "invariants": row.load(row.invariants_json, {}), "patch_artifact_id": str(row.patch_artifact_id) if row.patch_artifact_id else "", "result": row.load(row.result_json, {}), "error_message": row.error_message}
