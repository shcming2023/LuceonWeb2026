from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import sqlite3
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.material import BackupJob
from app.services.runtime_settings import (
    CURRENT_ASSET_BUCKETS,
    LEGACY_ASSET_BUCKETS,
    load_runtime_config,
    minio_client_from_config,
)


BACKUP_LEASE_SECONDS = 90


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _enabled_targets(config: dict[str, Any]) -> list[dict[str, Any]]:
    targets = []
    for row in config.get("backup", {}).get("targets", []):
        if not isinstance(row, dict) or not row.get("enabled"):
            continue
        if row.get("id") not in {"snapshot", "external"} or row.get("kind") != "filesystem":
            continue
        targets.append(
            {
                "id": str(row["id"]),
                "label": str(row.get("label") or row["id"]),
                "kind": "filesystem",
                "path": str(row.get("path") or ""),
                "external": bool(row.get("external")),
            }
        )
    return targets


def enqueue_backup_job(
    db: Session,
    requested_by_user_id: str,
    *,
    idempotency_key: str | None = None,
    parent_job_id: int | None = None,
    config: dict[str, Any] | None = None,
) -> BackupJob:
    runtime = config or load_runtime_config(include_secrets=True)
    backup = runtime.get("backup", {})
    targets = _enabled_targets(runtime)
    if not targets:
        raise ValueError("没有启用且受服务器控制的备份目标")
    include_legacy = bool(backup.get("include_legacy", True))
    buckets = list(CURRENT_ASSET_BUCKETS)
    if include_legacy:
        buckets.extend(LEGACY_ASSET_BUCKETS)
    key = idempotency_key or f"manual:{uuid.uuid4()}"
    existing = db.query(BackupJob).filter(BackupJob.idempotency_key == key).first()
    if existing:
        return existing
    job = BackupJob(
        requested_by_user_id=str(requested_by_user_id),
        parent_job_id=parent_job_id,
        status="queued",
        mode=str(backup.get("mode") or "manifest"),
        idempotency_key=key,
        target_snapshot_json=_json(targets),
        bucket_scope_json=_json(buckets),
        include_legacy=include_legacy,
        max_objects=max(1, int(backup.get("max_objects") or 2000000)),
        warnings_json="[]",
        result_json="{}",
    )
    if job.mode not in {"manifest", "copy"}:
        raise ValueError("不支持的备份模式")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_backup_jobs(db: Session, limit: int = 50) -> list[BackupJob]:
    return db.query(BackupJob).order_by(BackupJob.id.desc()).limit(max(1, min(limit, 200))).all()


def get_backup_job(db: Session, job_id: int) -> BackupJob | None:
    return db.query(BackupJob).filter(BackupJob.id == job_id).first()


def recover_stale_backup_jobs(db: Session, now: datetime | None = None) -> int:
    now = now or datetime.utcnow()
    stale = (
        db.query(BackupJob)
        .filter(BackupJob.status == "running", BackupJob.lease_expires_at < now)
        .all()
    )
    for job in stale:
        job.status = "queued"
        job.worker_id = None
        job.heartbeat_at = None
        job.lease_expires_at = None
        job.warnings_json = _json(job.warnings() + ["上一次 Worker 租约过期，任务已重新排队"])
    if stale:
        db.commit()
    return len(stale)


def claim_next_backup_job(db: Session, worker_id: str, now: datetime | None = None) -> BackupJob | None:
    now = now or datetime.utcnow()
    recover_stale_backup_jobs(db, now)
    candidate = db.query(BackupJob).filter(BackupJob.status == "queued").order_by(BackupJob.id.asc()).first()
    if not candidate:
        return None
    updated = (
        db.query(BackupJob)
        .filter(BackupJob.id == candidate.id, BackupJob.status == "queued")
        .update(
            {
                BackupJob.status: "running",
                BackupJob.worker_id: worker_id,
                BackupJob.attempt_count: BackupJob.attempt_count + 1,
                BackupJob.started_at: candidate.started_at or now,
                BackupJob.heartbeat_at: now,
                BackupJob.lease_expires_at: now + timedelta(seconds=BACKUP_LEASE_SECONDS),
                BackupJob.error_message: None,
            },
            synchronize_session=False,
        )
    )
    db.commit()
    return get_backup_job(db, candidate.id) if updated else None


def retry_backup_job(db: Session, source: BackupJob, requested_by_user_id: str) -> BackupJob:
    if source.status not in {"failed", "succeeded"}:
        raise ValueError("只有已结束的备份任务可以重试")
    job = BackupJob(
        requested_by_user_id=str(requested_by_user_id),
        parent_job_id=source.id,
        status="queued",
        mode=source.mode,
        idempotency_key=f"retry:{source.id}:{uuid.uuid4()}",
        target_snapshot_json=source.target_snapshot_json,
        bucket_scope_json=source.bucket_scope_json,
        include_legacy=source.include_legacy,
        max_objects=source.max_objects,
        warnings_json="[]",
        result_json="{}",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def acknowledge_backup_alert(db: Session, job: BackupJob) -> BackupJob:
    if not job.alert_level:
        raise ValueError("该任务没有待确认告警")
    job.alert_acknowledged_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


def _safe_destination(root: Path, bucket: str, object_name: str) -> Path:
    destination = (root / "objects" / bucket / object_name).resolve()
    object_root = (root / "objects").resolve()
    try:
        destination.relative_to(object_root)
    except ValueError as exc:
        raise ValueError(f"非法对象路径: {bucket}/{object_name}") from exc
    return destination


def _close_response(response: Any) -> None:
    close = getattr(response, "close", None)
    if close:
        close()
    release_conn = getattr(response, "release_conn", None)
    if release_conn:
        release_conn()


def _record_backup_worker_heartbeat(worker_id: str) -> None:
    try:
        from app.services.runtime_health import record_runtime_worker_heartbeat

        record_runtime_worker_heartbeat("backup", worker_id)
    except Exception:
        pass


def _sqlite_path(database_url: str) -> Path | None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    path = Path(database_url[len(prefix):])
    return path if path.is_absolute() else path.resolve()


def _runtime_sqlite_databases() -> dict[str, Path]:
    databases = {}
    for name, variable in (("application", "DATABASE_URL"), ("workflow", "WORKFLOW_DATABASE_URL")):
        path = _sqlite_path(os.getenv(variable, ""))
        if path and path.is_file():
            databases[name] = path
    return databases


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_sqlite_database(
    source: Path,
    destination: Path,
    *,
    completed_backup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_db = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    target_db = sqlite3.connect(destination)
    try:
        source_db.backup(target_db)
        if completed_backup:
            table_exists = target_db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='backup_jobs'"
            ).fetchone()
            if table_exists:
                finished_at = datetime.utcnow()
                target_db.execute(
                    """
                    UPDATE backup_jobs
                    SET status = 'succeeded', object_count = ?, copied_count = ?, bytes_copied = ?,
                        truncated = 0, heartbeat_at = ?, lease_expires_at = NULL, finished_at = ?,
                        error_message = NULL, alert_level = NULL, alert_message = NULL,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        int(completed_backup["object_count"]),
                        int(completed_backup["copied_count"]),
                        int(completed_backup["bytes_copied"]) + destination.stat().st_size,
                        finished_at,
                        finished_at,
                        finished_at,
                        int(completed_backup["job_id"]),
                    ),
                )
                target_db.commit()
        integrity = [str(row[0]) for row in target_db.execute("PRAGMA integrity_check")]
        if integrity != ["ok"]:
            raise RuntimeError(f"SQLite 备份完整性失败: {source} {integrity[:5]}")
    finally:
        target_db.close()
        source_db.close()
    destination.chmod(0o600)
    return {
        "source": str(source),
        "file": str(destination.name),
        "size_bytes": destination.stat().st_size,
        "sha256": _sha256(destination),
        "integrity_check": "ok",
    }


def execute_backup_job(
    job_id: int,
    worker_id: str,
    *,
    client: Any | None = None,
    session_factory: Callable[[], Session] | None = None,
    database_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    session_factory = session_factory or SessionLocal
    db = session_factory()
    completed_targets: list[dict[str, Any]] = []
    partial_roots: list[Path] = []
    objects: list[dict[str, Any]] = []
    warnings: list[str] = []
    truncated = False
    try:
        job = get_backup_job(db, job_id)
        if not job or job.status != "running" or job.worker_id != worker_id:
            raise ValueError("备份任务未被当前 Worker 持有")
        job.object_count = 0
        job.copied_count = 0
        job.bytes_copied = 0
        job.truncated = False
        db.commit()
        _record_backup_worker_heartbeat(worker_id)
        minio = client or minio_client_from_config()
        last_heartbeat = time.monotonic()
        for bucket in job.buckets():
            if not minio.bucket_exists(bucket):
                if bucket in CURRENT_ASSET_BUCKETS:
                    raise RuntimeError(f"当前资产 Bucket 缺失: {bucket}")
                warnings.append(f"历史 Bucket 不存在，已跳过: {bucket}")
                continue
            for item in minio.list_objects(bucket, recursive=True):
                if len(objects) >= job.max_objects:
                    truncated = True
                    break
                objects.append(
                    {
                        "bucket": bucket,
                        "object": str(getattr(item, "object_name", "") or ""),
                        "size": int(getattr(item, "size", 0) or 0),
                        "etag": str(getattr(item, "etag", "") or ""),
                    }
                )
                if time.monotonic() - last_heartbeat >= 10:
                    now = datetime.utcnow()
                    job.object_count = len(objects)
                    job.heartbeat_at = now
                    job.lease_expires_at = now + timedelta(seconds=BACKUP_LEASE_SECONDS)
                    db.commit()
                    _record_backup_worker_heartbeat(worker_id)
                    last_heartbeat = time.monotonic()
            if truncated:
                break
        if truncated:
            raise RuntimeError("备份清单达到对象上限，已拒绝将不完整结果标记为成功")

        manifest = {
            "schema": "luceon-backup-manifest/v2",
            "job_id": str(job.id),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "mode": job.mode,
            "buckets": job.buckets(),
            "object_count": len(objects),
            "truncated": truncated,
            "objects": objects,
        }
        copied_count = 0
        bytes_copied = 0
        sqlite_sources = database_paths if database_paths is not None else _runtime_sqlite_databases()
        for target in job.targets():
            target_root = Path(str(target["path"]))
            final_root = target_root / f"luceon-backup-job-{job.id}"
            partial_root = target_root / f".luceon-backup-job-{job.id}.partial"
            if final_root.exists():
                raise FileExistsError(f"备份目标已存在: {final_root}")
            if partial_root.exists():
                if job.attempt_count <= 1:
                    raise FileExistsError(f"备份临时目标已存在: {partial_root}")
                shutil.rmtree(partial_root)
                warnings.append(f"已清理同一任务上一次 attempt 的未完成目录: {partial_root.name}")
            partial_root.mkdir(parents=True, exist_ok=False)
            partial_roots.append(partial_root)
            target_copied = 0
            target_bytes = 0
            database_snapshots = []
            if job.mode == "copy":
                for row in objects:
                    destination = _safe_destination(partial_root, row["bucket"], row["object"])
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    response = minio.get_object(row["bucket"], row["object"])
                    try:
                        with destination.open("wb") as stream:
                            shutil.copyfileobj(response, stream)
                        actual_size = destination.stat().st_size
                        expected_size = int(row["size"])
                        if actual_size != expected_size:
                            raise RuntimeError(
                                f"备份对象大小不一致: {row['bucket']}/{row['object']} "
                                f"expected={expected_size} actual={actual_size}"
                            )
                        target_copied += 1
                        target_bytes += actual_size
                    finally:
                        _close_response(response)
                    if time.monotonic() - last_heartbeat >= 10:
                        now = datetime.utcnow()
                        job.object_count = len(objects)
                        job.copied_count = copied_count + target_copied
                        job.bytes_copied = bytes_copied + target_bytes
                        job.heartbeat_at = now
                        job.lease_expires_at = now + timedelta(seconds=BACKUP_LEASE_SECONDS)
                        db.commit()
                        _record_backup_worker_heartbeat(worker_id)
                        last_heartbeat = time.monotonic()
                for name, source in sqlite_sources.items():
                    snapshot = _snapshot_sqlite_database(
                        source,
                        partial_root / "databases" / f"{name}.db",
                        completed_backup={
                            "job_id": job.id,
                            "object_count": len(objects),
                            "copied_count": target_copied,
                            "bytes_copied": target_bytes,
                        }
                        if name == "application"
                        else None,
                    )
                    snapshot["name"] = name
                    database_snapshots.append(snapshot)
                    target_bytes += int(snapshot["size_bytes"])
            target_manifest = {**manifest, "databases": database_snapshots}
            manifest_path = partial_root / "backup-manifest.json"
            manifest_path.write_text(json.dumps(target_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            partial_root.rename(final_root)
            partial_roots.remove(partial_root)
            copied_count += target_copied
            bytes_copied += target_bytes
            completed_targets.append(
                {
                    "id": str(target["id"]),
                    "path": str(final_root),
                    "manifest": str(final_root / "backup-manifest.json"),
                    "copied_count": target_copied,
                    "bytes_copied": target_bytes,
                    "database_count": len(database_snapshots),
                    "databases": database_snapshots,
                }
            )

        job.object_count = len(objects)
        job.copied_count = copied_count
        job.bytes_copied = bytes_copied
        job.truncated = truncated
        job.result_json = _json({"targets": completed_targets})
        job.warnings_json = _json(warnings)
        job.status = "succeeded"
        job.finished_at = datetime.utcnow()
        job.heartbeat_at = job.finished_at
        job.lease_expires_at = None
        db.commit()
        return job.to_dict()
    except Exception as exc:
        for path in partial_roots:
            shutil.rmtree(path, ignore_errors=True)
        job = get_backup_job(db, job_id)
        if job:
            db.rollback()
            job = get_backup_job(db, job_id)
            if job:
                job.status = "failed"
                job.finished_at = datetime.utcnow()
                job.lease_expires_at = None
                job.object_count = len(objects)
                job.truncated = truncated
                job.warnings_json = _json(warnings)
                job.error_message = str(exc)[:2000]
                job.result_json = _json({"targets": completed_targets})
                job.alert_level = "critical"
                job.alert_message = f"备份任务失败: {str(exc)[:1000]}"
                db.commit()
        raise
    finally:
        db.close()


def enqueue_scheduled_backup_if_due(db: Session, now: datetime | None = None) -> BackupJob | None:
    now = now or datetime.utcnow()
    config = load_runtime_config(include_secrets=True)
    backup = config.get("backup", {})
    if not backup.get("enabled") or not backup.get("schedule_enabled"):
        return None
    interval_hours = max(1, int(backup.get("interval_hours") or 24))
    include_legacy = bool(backup.get("include_legacy", True))
    buckets = list(CURRENT_ASSET_BUCKETS)
    if include_legacy:
        buckets.extend(LEGACY_ASSET_BUCKETS)
    recent_successes = (
        db.query(BackupJob)
        .filter(
            BackupJob.status == "succeeded",
            BackupJob.truncated.is_(False),
            BackupJob.finished_at >= now - timedelta(hours=interval_hours),
            BackupJob.mode == str(backup.get("mode") or "manifest"),
            BackupJob.bucket_scope_json == _json(buckets),
            BackupJob.include_legacy == include_legacy,
            BackupJob.max_objects == max(1, int(backup.get("max_objects") or 2000000)),
        )
        .all()
    )
    target_fields = ("id", "kind", "path", "external")
    expected_targets = [
        {field: target[field] for field in target_fields}
        for target in _enabled_targets(config)
    ]
    for recent_success in recent_successes:
        actual_targets = [
            {field: target.get(field) for field in target_fields}
            for target in recent_success.targets()
        ]
        if actual_targets == expected_targets:
            return None
    window = int(now.timestamp()) // (interval_hours * 3600)
    return enqueue_backup_job(
        db,
        "scheduler",
        idempotency_key=f"scheduled:{interval_hours}h:{window}",
        config=config,
    )


def default_backup_worker_id() -> str:
    return f"backup-{socket.gethostname()}-{os.getpid()}"
