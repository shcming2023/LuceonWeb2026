import json
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.models.base import Base


STAGE_ORDER = {
    "input": 10,
    "mineru_done": 20,
    "popo_done": 30,
    "latex_done": 70,
    "raw_done": 40,
    "clean_stale": 45,
    "clean_done": 50,
    "standard_done": 60,
    "failed": 5,
}


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    material_id = Column(String(128), nullable=True, index=True)
    source_hash = Column(String(64), nullable=True, index=True)
    title = Column(String(512), nullable=False, index=True)
    filename = Column(String(512), nullable=False, index=True)
    source_type = Column(String(32), nullable=False, default="imported", index=True)

    input_bucket = Column(String(128), nullable=True)
    input_object = Column(String(1024), nullable=True)
    input_sha256 = Column(String(128), nullable=True, index=True)
    size_bytes = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    content_type = Column(String(128), nullable=True)

    stage_status = Column(String(32), nullable=False, default="input", index=True)
    pipeline_status = Column(String(32), nullable=False, default="idle", index=True)

    mineru_manifest_bucket = Column(String(128), nullable=True)
    mineru_manifest_object = Column(String(1024), nullable=True)
    mineru_run_id = Column(String(128), nullable=True)

    popo_manifest_bucket = Column(String(128), nullable=True)
    popo_manifest_object = Column(String(1024), nullable=True)
    popo_run_id = Column(String(128), nullable=True)

    latex_manifest_bucket = Column(String(128), nullable=True)
    latex_manifest_object = Column(String(1024), nullable=True)
    latex_run_id = Column(String(128), nullable=True)

    raw_manifest_bucket = Column(String(128), nullable=True)
    raw_manifest_object = Column(String(1024), nullable=True)
    raw_run_id = Column(String(128), nullable=True)

    clean_manifest_bucket = Column(String(128), nullable=True)
    clean_manifest_object = Column(String(1024), nullable=True)
    clean_run_id = Column(String(128), nullable=True)

    standard_manifest_bucket = Column(String(128), nullable=True)
    standard_manifest_object = Column(String(1024), nullable=True)
    standard_run_id = Column(String(128), nullable=True)
    standard_quality_score = Column(Integer, nullable=True)

    review_asset_id = Column(Integer, nullable=True, index=True)
    ignored = Column(Boolean, nullable=False, default=False)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("idx_material_user_input", "user_id", "input_bucket", "input_object", unique=True),
        Index("idx_material_user_material", "user_id", "material_id", unique=False),
    )

    def promote_stage(self, stage: str) -> None:
        if STAGE_ORDER.get(stage, 0) >= STAGE_ORDER.get(self.stage_status or "input", 0):
            self.stage_status = stage

    def to_dict(self) -> dict:
        mineru_available = bool(self.mineru_manifest_bucket and self.mineru_manifest_object) or bool(
            self.popo_manifest_bucket and self.popo_manifest_object
        )
        return {
            "id": str(self.id),
            "material_id": self.material_id or "",
            "source_hash": self.source_hash or "",
            "title": self.title,
            "filename": self.filename,
            "source_type": self.source_type,
            "input_bucket": self.input_bucket or "",
            "input_object": self.input_object or "",
            "input_sha256": self.input_sha256 or "",
            "size": self.size_bytes or 0,
            "page_count": self.page_count or 0,
            "content_type": self.content_type or "",
            "stage_status": self.stage_status or "input",
            "pipeline_status": self.pipeline_status or "idle",
            "mineru_manifest": self._ref(self.mineru_manifest_bucket, self.mineru_manifest_object),
            "popo_manifest": self._ref(self.popo_manifest_bucket, self.popo_manifest_object),
            "latex_manifest": self._ref(self.latex_manifest_bucket, self.latex_manifest_object),
            "raw_manifest": self._ref(self.raw_manifest_bucket, self.raw_manifest_object),
            "clean_manifest": self._ref(self.clean_manifest_bucket, self.clean_manifest_object),
            "standard_manifest": self._ref(self.standard_manifest_bucket, self.standard_manifest_object),
            "mineru_available": mineru_available,
            "popo_available": bool(self.popo_manifest_bucket and self.popo_manifest_object),
            "latex_available": bool(self.latex_manifest_bucket and self.latex_manifest_object),
            "raw_available": bool(self.raw_manifest_bucket and self.raw_manifest_object),
            "clean_available": bool(self.clean_manifest_bucket and self.clean_manifest_object),
            "standard_available": bool(self.standard_manifest_bucket and self.standard_manifest_object),
            "mineru_run_id": self.mineru_run_id or "",
            "popo_run_id": self.popo_run_id or "",
            "latex_run_id": self.latex_run_id or "",
            "raw_run_id": self.raw_run_id or "",
            "clean_run_id": self.clean_run_id or "",
            "standard_run_id": self.standard_run_id or "",
            "standard_quality_score": self.standard_quality_score,
            "review_asset_id": str(self.review_asset_id) if self.review_asset_id else "",
            "ignored": bool(self.ignored),
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @staticmethod
    def _ref(bucket: str | None, object_name: str | None) -> dict[str, str]:
        return {"bucket": bucket or "", "object": object_name or ""}


class MaterialOutput(Base):
    __tablename__ = "material_outputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    material_pk = Column(Integer, nullable=True, index=True)
    material_id = Column(String(128), nullable=False, index=True)
    review_asset_id = Column(Integer, nullable=True, index=True)
    output_type = Column(String(64), nullable=False, default="elegantbook", index=True)
    origin = Column(String(64), nullable=False, default="codex_skill", index=True)
    status = Column(String(32), nullable=False, default="candidate", index=True)
    quality_status = Column(String(32), nullable=False, default="unchecked", index=True)
    is_current = Column(Boolean, nullable=False, default=False, index=True)

    manifest_bucket = Column(String(128), nullable=False)
    manifest_object = Column(String(1024), nullable=False)
    output_run_id = Column(String(128), nullable=True, index=True)
    popo_run_id = Column(String(128), nullable=True, index=True)
    skill_name = Column(String(128), nullable=True, index=True)
    skill_version = Column(String(128), nullable=True)
    codex_job_id = Column(Integer, nullable=True, index=True)
    version_label = Column(String(128), nullable=True)
    metadata_json = Column(Text, nullable=True)
    promoted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "manifest_bucket", "manifest_object", name="uq_material_output_manifest"),
        Index("idx_material_output_lookup", "user_id", "material_id", "output_type"),
    )

    def metadata_dict(self) -> dict:
        if not self.metadata_json:
            return {}
        try:
            value = json.loads(self.metadata_json)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "material_pk": str(self.material_pk) if self.material_pk else "",
            "material_id": self.material_id,
            "review_asset_id": str(self.review_asset_id) if self.review_asset_id else "",
            "output_type": self.output_type,
            "origin": self.origin,
            "status": self.status,
            "quality_status": self.quality_status,
            "is_current": bool(self.is_current),
            "manifest": self._ref(self.manifest_bucket, self.manifest_object),
            "manifest_bucket": self.manifest_bucket,
            "manifest_object": self.manifest_object,
            "output_run_id": self.output_run_id or "",
            "popo_run_id": self.popo_run_id or "",
            "skill_name": self.skill_name or "",
            "skill_version": self.skill_version or "",
            "codex_job_id": str(self.codex_job_id) if self.codex_job_id else "",
            "version_label": self.version_label or "",
            "metadata": self.metadata_dict(),
            "promoted_at": self.promoted_at.isoformat() if self.promoted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @staticmethod
    def _ref(bucket: str | None, object_name: str | None) -> dict[str, str]:
        return {"bucket": bucket or "", "object": object_name or ""}


class BackupJob(Base):
    __tablename__ = "backup_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requested_by_user_id = Column(String(64), nullable=False, index=True)
    parent_job_id = Column(Integer, nullable=True, index=True)
    status = Column(String(32), nullable=False, default="queued", index=True)
    mode = Column(String(16), nullable=False, default="manifest", index=True)
    idempotency_key = Column(String(128), nullable=False, unique=True, index=True)
    target_snapshot_json = Column(Text, nullable=False)
    bucket_scope_json = Column(Text, nullable=False)
    include_legacy = Column(Boolean, nullable=False, default=True)
    max_objects = Column(Integer, nullable=False, default=2000000)
    worker_id = Column(String(128), nullable=True, index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    heartbeat_at = Column(DateTime, nullable=True)
    lease_expires_at = Column(DateTime, nullable=True, index=True)
    object_count = Column(Integer, nullable=False, default=0)
    copied_count = Column(Integer, nullable=False, default=0)
    bytes_copied = Column(Integer, nullable=False, default=0)
    truncated = Column(Boolean, nullable=False, default=False)
    result_json = Column(Text, nullable=True)
    warnings_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    alert_level = Column(String(16), nullable=True)
    alert_message = Column(Text, nullable=True)
    alert_acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def targets(self) -> list[dict]:
        return self._list(self.target_snapshot_json)

    def buckets(self) -> list[str]:
        return [str(item) for item in self._list(self.bucket_scope_json)]

    def result(self) -> dict:
        return self._dict(self.result_json)

    def warnings(self) -> list[str]:
        return [str(item) for item in self._list(self.warnings_json)]

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "parent_job_id": str(self.parent_job_id) if self.parent_job_id else "",
            "status": self.status,
            "mode": self.mode,
            "targets": self.targets(),
            "buckets": self.buckets(),
            "include_legacy": bool(self.include_legacy),
            "max_objects": self.max_objects,
            "attempt_count": self.attempt_count,
            "worker_id": self.worker_id or "",
            "object_count": self.object_count,
            "copied_count": self.copied_count,
            "bytes_copied": self.bytes_copied,
            "truncated": bool(self.truncated),
            "result": self.result(),
            "warnings": self.warnings(),
            "error_message": self.error_message or "",
            "alert": {
                "level": self.alert_level or "",
                "message": self.alert_message or "",
                "acknowledged": bool(self.alert_acknowledged_at),
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }

    @staticmethod
    def _list(raw: str | None) -> list:
        try:
            value = json.loads(raw or "[]")
        except json.JSONDecodeError:
            return []
        return value if isinstance(value, list) else []

    @staticmethod
    def _dict(raw: str | None) -> dict:
        try:
            value = json.loads(raw or "{}")
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}


class CodexSkillJob(Base):
    __tablename__ = "codex_skill_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    material_pk = Column(Integer, nullable=True, index=True)
    material_id = Column(String(128), nullable=False, index=True)
    review_asset_id = Column(Integer, nullable=True, index=True)
    mode = Column(String(64), nullable=False, default="new_pdf", index=True)
    status = Column(String(32), nullable=False, default="queued", index=True)
    requested_skill = Column(String(128), nullable=False, default="luceon-popo-to-refined-elegantbook")
    skill_version = Column(String(128), nullable=False, default="draft")
    idempotency_key = Column(String(128), nullable=False, index=True)

    source_popo_manifest_bucket = Column(String(128), nullable=True)
    source_popo_manifest_object = Column(String(1024), nullable=True)
    baseline_manifest_bucket = Column(String(128), nullable=True)
    baseline_manifest_object = Column(String(1024), nullable=True)
    output_manifest_bucket = Column(String(128), nullable=True)
    output_manifest_object = Column(String(1024), nullable=True)

    codex_thread_id = Column(String(128), nullable=True, index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    staging_dir = Column(String(1024), nullable=True)
    error_message = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True)
    result_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_codex_skill_job_idempotency"),
        Index("idx_codex_skill_job_material", "user_id", "material_id", "status"),
    )

    def payload(self) -> dict:
        return self._json(self.payload_json)

    def result(self) -> dict:
        return self._json(self.result_json)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "material_pk": str(self.material_pk) if self.material_pk else "",
            "material_id": self.material_id,
            "review_asset_id": str(self.review_asset_id) if self.review_asset_id else "",
            "mode": self.mode,
            "status": self.status,
            "requested_skill": self.requested_skill,
            "skill_version": self.skill_version,
            "source_popo_manifest": self._ref(self.source_popo_manifest_bucket, self.source_popo_manifest_object),
            "baseline_manifest": self._ref(self.baseline_manifest_bucket, self.baseline_manifest_object),
            "output_manifest": self._ref(self.output_manifest_bucket, self.output_manifest_object),
            "codex_thread_id": self.codex_thread_id or "",
            "attempt_count": self.attempt_count,
            "staging_dir": self.staging_dir or "",
            "error_message": self.error_message or "",
            "payload": self.payload(),
            "result": self.result(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }

    @staticmethod
    def _json(raw: str | None) -> dict:
        if not raw:
            return {}
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _ref(bucket: str | None, object_name: str | None) -> dict[str, str]:
        return {"bucket": bucket or "", "object": object_name or ""}


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="idle", index=True)
    mode = Column(String(32), nullable=False, default="full")
    idempotency_key = Column(String(128), nullable=True, index=True)
    queue_slot = Column(String(32), nullable=True)
    command = Column(Text, nullable=True)
    request_json = Column(Text, nullable=True)
    current_stage = Column(String(64), nullable=True)
    total = Column(Integer, nullable=False, default=0)
    processed = Column(Integer, nullable=False, default=0)
    success = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    summary_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    worker_id = Column(String(128), nullable=True, index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    heartbeat_at = Column(DateTime, nullable=True)
    lease_expires_at = Column(DateTime, nullable=True, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint("queue_slot", name="uq_pipeline_runs_queue_slot"),)

    def summary(self) -> dict:
        if not self.summary_json:
            return {}
        try:
            value = json.loads(self.summary_json)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def request(self) -> dict:
        if not self.request_json:
            return {}
        try:
            value = json.loads(self.request_json)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "status": self.status,
            "mode": self.mode,
            "idempotency_key": self.idempotency_key or "",
            "queue_slot": self.queue_slot or "",
            "current_stage": self.current_stage or "",
            "total": self.total,
            "processed": self.processed,
            "success": self.success,
            "failed": self.failed,
            "summary": self.summary(),
            "request": self.request(),
            "error_message": self.error_message or "",
            "worker_id": self.worker_id or "",
            "attempt_count": self.attempt_count,
            "heartbeat_at": self.heartbeat_at.isoformat() if self.heartbeat_at else None,
            "lease_expires_at": self.lease_expires_at.isoformat() if self.lease_expires_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PipelineEvent(Base):
    __tablename__ = "pipeline_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    level = Column(String(16), nullable=False, default="info")
    stage = Column(String(64), nullable=True)
    message = Column(Text, nullable=False)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        payload = {}
        if self.payload_json:
            try:
                parsed = json.loads(self.payload_json)
                payload = parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                payload = {}
        return {
            "id": str(self.id),
            "run_id": str(self.run_id),
            "level": self.level,
            "stage": self.stage or "",
            "message": self.message,
            "payload": payload,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PipelineRunItem(Base):
    __tablename__ = "pipeline_run_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    material_pk = Column(Integer, nullable=False, index=True)
    material_id = Column(String(128), nullable=False, index=True)
    input_bucket = Column(String(128), nullable=False)
    input_object = Column(String(1024), nullable=False)
    input_sha256 = Column(String(128), nullable=True, index=True)
    filename = Column(String(512), nullable=False)
    status = Column(String(32), nullable=False, default="queued", index=True)
    current_stage = Column(String(64), nullable=False, default="queued", index=True)
    mineru_run_id = Column(String(128), nullable=True, index=True)
    mineru_manifest_bucket = Column(String(128), nullable=True)
    mineru_manifest_object = Column(String(1024), nullable=True)
    popo_run_id = Column(String(128), nullable=True, index=True)
    popo_manifest_bucket = Column(String(128), nullable=True)
    popo_manifest_object = Column(String(1024), nullable=True)
    error_code = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("run_id", "material_pk", name="uq_pipeline_run_item_material"),
        Index("idx_pipeline_run_item_status", "run_id", "status"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "run_id": str(self.run_id),
            "material_pk": str(self.material_pk),
            "material_id": self.material_id,
            "filename": self.filename,
            "input": {
                "bucket": self.input_bucket,
                "object": self.input_object,
                "sha256": self.input_sha256 or "",
            },
            "status": self.status,
            "current_stage": self.current_stage,
            "mineru_run_id": self.mineru_run_id or "",
            "mineru_manifest": Material._ref(self.mineru_manifest_bucket, self.mineru_manifest_object),
            "popo_run_id": self.popo_run_id or "",
            "popo_manifest": Material._ref(self.popo_manifest_bucket, self.popo_manifest_object),
            "error_code": self.error_code or "",
            "error_message": self.error_message or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


class PipelineStageAttempt(Base):
    __tablename__ = "pipeline_stage_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_item_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    stage = Column(String(64), nullable=False, index=True)
    attempt = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="queued", index=True)
    external_batch_id = Column(String(128), nullable=True, index=True)
    external_run_id = Column(String(128), nullable=True, index=True)
    input_manifest_bucket = Column(String(128), nullable=True)
    input_manifest_object = Column(String(1024), nullable=True)
    output_manifest_bucket = Column(String(128), nullable=True)
    output_manifest_object = Column(String(1024), nullable=True)
    error_code = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("run_item_id", "stage", "attempt", name="uq_pipeline_stage_attempt"),
    )

    def evidence(self) -> dict:
        if not self.evidence_json:
            return {}
        try:
            value = json.loads(self.evidence_json)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "run_item_id": str(self.run_item_id),
            "stage": self.stage,
            "attempt": self.attempt,
            "status": self.status,
            "external_batch_id": self.external_batch_id or "",
            "external_run_id": self.external_run_id or "",
            "input_manifest": Material._ref(self.input_manifest_bucket, self.input_manifest_object),
            "output_manifest": Material._ref(self.output_manifest_bucket, self.output_manifest_object),
            "error_code": self.error_code or "",
            "error_message": self.error_message or "",
            "evidence": self.evidence(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


class MetadataJob(Base):
    __tablename__ = "metadata_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    material_pk = Column(Integer, nullable=False, index=True)
    material_id = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="queued", index=True)
    idempotency_key = Column(String(128), nullable=False, index=True)
    source_manifest_bucket = Column(String(128), nullable=True)
    source_manifest_object = Column(String(1024), nullable=True)
    source_manifest_sha256 = Column(String(128), nullable=True, index=True)
    model = Column(String(128), nullable=True)
    prompt_version = Column(String(128), nullable=False, default="material-metadata-v1")
    force = Column(Boolean, nullable=False, default=False)
    attempt_count = Column(Integer, nullable=False, default=0)
    worker_id = Column(String(128), nullable=True, index=True)
    heartbeat_at = Column(DateTime, nullable=True)
    lease_expires_at = Column(DateTime, nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    result_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_metadata_job_idempotency"),
    )

    def result(self) -> dict:
        if not self.result_json:
            return {}
        try:
            value = json.loads(self.result_json)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "material_pk": str(self.material_pk),
            "material_id": self.material_id,
            "status": self.status,
            "idempotency_key": self.idempotency_key,
            "source_manifest": Material._ref(self.source_manifest_bucket, self.source_manifest_object),
            "source_manifest_sha256": self.source_manifest_sha256 or "",
            "model": self.model or "",
            "prompt_version": self.prompt_version,
            "force": bool(self.force),
            "attempt_count": self.attempt_count,
            "worker_id": self.worker_id or "",
            "error_message": self.error_message or "",
            "result": self.result(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }
