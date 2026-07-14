from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base


WorkflowBase = declarative_base()


class JsonMixin:
    @staticmethod
    def dump(value) -> str:
        return json.dumps(value if value is not None else {}, ensure_ascii=False)

    @staticmethod
    def load(value: str | None, default):
        try:
            parsed = json.loads(value or "")
        except (TypeError, json.JSONDecodeError):
            return default
        return parsed


class WorkflowJob(WorkflowBase, JsonMixin):
    __tablename__ = "workflow_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    public_id = Column(String(36), nullable=False, unique=True, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    material_pk = Column(Integer, nullable=False, index=True)
    material_id = Column(String(128), nullable=False, index=True)
    source_popo_bucket = Column(String(128), nullable=False)
    source_popo_object = Column(String(1024), nullable=False)
    workflow_version = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="queued", index=True)
    current_stage_key = Column(String(64), nullable=False, default="canonical_clean_material")
    idempotency_key = Column(String(64), nullable=False, unique=True, index=True)
    priority = Column(Integer, nullable=False, default=100)
    cancellation_requested = Column(Boolean, nullable=False, default=False)
    payload_json = Column(Text, nullable=False, default="{}")
    error_code = Column(String(128), nullable=False, default="")
    error_message = Column(Text, nullable=False, default="")
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_workflow_job_material_status", "user_id", "material_id", "status"),)

    def to_dict(self) -> dict:
        return {
            "id": self.public_id,
            "user_id": self.user_id,
            "material_pk": str(self.material_pk),
            "material_id": self.material_id,
            "source_popo_manifest": {"bucket": self.source_popo_bucket, "object": self.source_popo_object},
            "workflow_version": self.workflow_version,
            "status": self.status,
            "current_stage_key": self.current_stage_key,
            "priority": self.priority,
            "cancellation_requested": self.cancellation_requested,
            "payload": self.load(self.payload_json, {}),
            "error": {"code": self.error_code, "message": self.error_message},
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class StageRun(WorkflowBase, JsonMixin):
    __tablename__ = "stage_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_job_id = Column(Integer, ForeignKey("workflow_jobs.id"), nullable=False, index=True)
    stage_key = Column(String(64), nullable=False, index=True)
    stage_version = Column(String(128), nullable=False)
    attempt = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="queued", index=True)
    owner = Column(String(32), nullable=False)
    input_manifest_sha256 = Column(String(64), nullable=False, default="")
    output_manifest_bucket = Column(String(128), nullable=False, default="")
    output_manifest_object = Column(String(1024), nullable=False, default="")
    output_manifest_sha256 = Column(String(64), nullable=False, default="")
    code_version = Column(String(64), nullable=False, default="")
    prompt_version = Column(String(64), nullable=False, default="")
    metrics_json = Column(Text, nullable=False, default="{}")
    error_code = Column(String(128), nullable=False, default="")
    error_message = Column(Text, nullable=False, default="")
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    heartbeat_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("workflow_job_id", "stage_key", "attempt", name="uq_stage_run_attempt"),
        Index("idx_stage_run_job_status", "workflow_job_id", "status"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "stage_key": self.stage_key,
            "stage_version": self.stage_version,
            "attempt": self.attempt,
            "status": self.status,
            "owner": self.owner,
            "input_manifest_sha256": self.input_manifest_sha256,
            "output_manifest": {
                "bucket": self.output_manifest_bucket,
                "object": self.output_manifest_object,
                "sha256": self.output_manifest_sha256,
            },
            "code_version": self.code_version,
            "prompt_version": self.prompt_version,
            "metrics": self.load(self.metrics_json, {}),
            "error": {"code": self.error_code, "message": self.error_message},
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "heartbeat_at": self.heartbeat_at.isoformat() if self.heartbeat_at else None,
        }


class StageEvent(WorkflowBase, JsonMixin):
    __tablename__ = "stage_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_job_id = Column(Integer, ForeignKey("workflow_jobs.id"), nullable=False, index=True)
    stage_run_id = Column(Integer, ForeignKey("stage_runs.id"), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    level = Column(String(16), nullable=False, default="info")
    message = Column(Text, nullable=False)
    payload_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "stage_run_id": str(self.stage_run_id) if self.stage_run_id else "",
            "event_type": self.event_type,
            "level": self.level,
            "message": self.message,
            "payload": self.load(self.payload_json, {}),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ArtifactVersion(WorkflowBase, JsonMixin):
    __tablename__ = "artifact_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_job_id = Column(Integer, ForeignKey("workflow_jobs.id"), nullable=False, index=True)
    stage_run_id = Column(Integer, ForeignKey("stage_runs.id"), nullable=False, index=True)
    artifact_kind = Column(String(64), nullable=False, index=True)
    bucket = Column(String(128), nullable=False)
    object_name = Column(String(1024), nullable=False)
    object_identity_hash = Column(String(64), nullable=False, unique=True, index=True)
    sha256 = Column(String(64), nullable=False)
    size_bytes = Column(Integer, nullable=False, default=0)
    content_type = Column(String(128), nullable=False, default="application/octet-stream")
    status = Column(String(32), nullable=False, default="candidate", index=True)
    immutable = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class ModelCall(WorkflowBase, JsonMixin):
    __tablename__ = "model_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_job_id = Column(Integer, ForeignKey("workflow_jobs.id"), nullable=False, index=True)
    stage_run_id = Column(Integer, ForeignKey("stage_runs.id"), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    model = Column(String(128), nullable=False)
    response_id = Column(String(128), nullable=False, default="", index=True)
    prompt_version = Column(String(64), nullable=False)
    purpose = Column(String(128), nullable=False)
    input_evidence_json = Column(Text, nullable=False, default="[]")
    usage_json = Column(Text, nullable=False, default="{}")
    result_json = Column(Text, nullable=False, default="{}")
    estimated_cost = Column(Numeric(14, 6), nullable=True)
    status = Column(String(32), nullable=False, index=True)
    error_message = Column(Text, nullable=False, default="")
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class QaFinding(WorkflowBase, JsonMixin):
    __tablename__ = "qa_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_job_id = Column(Integer, ForeignKey("workflow_jobs.id"), nullable=False, index=True)
    stage_run_id = Column(Integer, ForeignKey("stage_runs.id"), nullable=False, index=True)
    code = Column(String(128), nullable=False, index=True)
    severity = Column(String(16), nullable=False, index=True)
    page_number = Column(Integer, nullable=True, index=True)
    status = Column(String(32), nullable=False, default="open", index=True)
    evidence_artifact_id = Column(Integer, ForeignKey("artifact_versions.id"), nullable=True)
    details_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class RepairAttempt(WorkflowBase, JsonMixin):
    __tablename__ = "repair_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_job_id = Column(Integer, ForeignKey("workflow_jobs.id"), nullable=False, index=True)
    source_finding_id = Column(Integer, ForeignKey("qa_findings.id"), nullable=True, index=True)
    repair_kind = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="queued", index=True)
    allowed_scope_json = Column(Text, nullable=False, default="{}")
    invariants_json = Column(Text, nullable=False, default="{}")
    patch_artifact_id = Column(Integer, ForeignKey("artifact_versions.id"), nullable=True)
    result_json = Column(Text, nullable=False, default="{}")
    error_message = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "source_finding_id": str(self.source_finding_id) if self.source_finding_id else "",
            "repair_kind": self.repair_kind,
            "status": self.status,
            "allowed_scope": self.load(self.allowed_scope_json, {}),
            "invariants": self.load(self.invariants_json, {}),
            "patch_artifact_id": str(self.patch_artifact_id) if self.patch_artifact_id else "",
            "result": self.load(self.result_json, {}),
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


class GoldenRegressionCase(WorkflowBase, JsonMixin):
    __tablename__ = "golden_regression_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cohort_version = Column(String(64), nullable=False, index=True)
    case_key = Column(String(64), nullable=False, unique=True, index=True)
    material_pk = Column(Integer, nullable=False, unique=True, index=True)
    material_id = Column(String(128), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    dimensions_json = Column(Text, nullable=False, default="[]")
    selection_reason = Column(Text, nullable=False)
    baseline_json = Column(Text, nullable=False, default="{}")
    status = Column(String(32), nullable=False, default="selected", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
