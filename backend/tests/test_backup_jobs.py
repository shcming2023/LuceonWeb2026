from __future__ import annotations

import io
import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.material import BackupJob
from app.services.backup_jobs import (
    acknowledge_backup_alert,
    claim_next_backup_job,
    enqueue_backup_job,
    execute_backup_job,
    recover_stale_backup_jobs,
    retry_backup_job,
)
from app.services.runtime_settings import CURRENT_ASSET_BUCKETS, LEGACY_ASSET_BUCKETS


class FakeMinio:
    def __init__(self, objects: dict[str, dict[str, bytes]]):
        self.objects = objects

    def bucket_exists(self, bucket: str) -> bool:
        return bucket in self.objects

    def list_objects(self, bucket: str, recursive: bool = True):
        assert recursive is True
        for name, payload in self.objects.get(bucket, {}).items():
            yield SimpleNamespace(object_name=name, size=len(payload), etag=f"etag-{name}")

    def get_object(self, bucket: str, object_name: str):
        return io.BytesIO(self.objects[bucket][object_name])


class ShortReadMinio(FakeMinio):
    def get_object(self, bucket: str, object_name: str):
        return io.BytesIO(self.objects[bucket][object_name][:-1])


def complete_objects(extra: dict[str, dict[str, bytes]]) -> dict[str, dict[str, bytes]]:
    return {**{bucket: {} for bucket in CURRENT_ASSET_BUCKETS}, **extra}


@pytest.fixture()
def sessions(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'jobs.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def runtime_config(tmp_path, mode: str = "manifest", max_objects: int = 50000) -> dict:
    return {
        "backup": {
            "mode": mode,
            "include_legacy": True,
            "max_objects": max_objects,
            "targets": [
                {
                    "id": "snapshot",
                    "label": "snapshot",
                    "kind": "filesystem",
                    "path": str(tmp_path / "snapshots"),
                    "enabled": True,
                    "external": False,
                },
                {
                    "id": "external",
                    "label": "external",
                    "kind": "filesystem",
                    "path": str(tmp_path / "external"),
                    "enabled": True,
                    "external": True,
                },
            ],
        }
    }


def test_job_freezes_complete_current_and_legacy_scope(sessions, tmp_path):
    db = sessions()
    try:
        job = enqueue_backup_job(db, "7", config=runtime_config(tmp_path))
        assert job.status == "queued"
        assert job.buckets() == [*CURRENT_ASSET_BUCKETS, *LEGACY_ASSET_BUCKETS]
        assert {row["id"] for row in job.targets()} == {"snapshot", "external"}
    finally:
        db.close()


def test_manifest_job_writes_manifests_without_copying_objects(sessions, tmp_path):
    db = sessions()
    try:
        queued = enqueue_backup_job(db, "7", config=runtime_config(tmp_path, "manifest"))
        job = claim_next_backup_job(db, "worker-1")
        assert job and job.id == queued.id
    finally:
        db.close()

    result = execute_backup_job(
        queued.id,
        "worker-1",
        client=FakeMinio(complete_objects({"eduassets-input": {"book.pdf": b"pdf"}})),
        session_factory=sessions,
    )

    assert result["status"] == "succeeded"
    assert result["object_count"] == 1
    assert result["copied_count"] == 0
    for target in result["result"]["targets"]:
        manifest_path = tmp_path / ("snapshots" if target["id"] == "snapshot" else "external") / f"luceon-backup-job-{queued.id}" / "backup-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["schema"] == "luceon-backup-manifest/v2"
        assert manifest["objects"][0]["object"] == "book.pdf"
        assert not (manifest_path.parent / "objects").exists()


def test_copy_job_copies_every_object_to_each_target(sessions, tmp_path):
    config = runtime_config(tmp_path, "copy")
    db = sessions()
    try:
        queued = enqueue_backup_job(db, "7", config=config)
        assert claim_next_backup_job(db, "worker-1")
    finally:
        db.close()

    result = execute_backup_job(
        queued.id,
        "worker-1",
        client=FakeMinio(
            complete_objects({
                "eduassets-input": {"nested/book.pdf": b"pdf"},
                "eduassets-standard": {"m/standard-final/main.tex": b"latex"},
            })
        ),
        session_factory=sessions,
    )

    assert result["status"] == "succeeded"
    assert result["object_count"] == 2
    assert result["copied_count"] == 4
    for root in (tmp_path / "snapshots", tmp_path / "external"):
        job_root = root / f"luceon-backup-job-{queued.id}" / "objects"
        assert (job_root / "eduassets-input/nested/book.pdf").read_bytes() == b"pdf"
        assert (job_root / "eduassets-standard/m/standard-final/main.tex").read_bytes() == b"latex"


def test_truncated_copy_fails_and_records_acknowledgeable_alert(sessions, tmp_path):
    db = sessions()
    try:
        queued = enqueue_backup_job(db, "7", config=runtime_config(tmp_path, "copy", max_objects=1))
        assert claim_next_backup_job(db, "worker-1")
    finally:
        db.close()

    with pytest.raises(RuntimeError, match="不完整结果"):
        execute_backup_job(
            queued.id,
            "worker-1",
            client=FakeMinio(complete_objects({"eduassets-input": {"a.pdf": b"a", "b.pdf": b"b"}})),
            session_factory=sessions,
        )

    db = sessions()
    try:
        failed = db.query(BackupJob).filter(BackupJob.id == queued.id).one()
        assert failed.status == "failed"
        assert failed.truncated is True
        assert failed.alert_level == "critical"
        retry = retry_backup_job(db, failed, "9")
        assert retry.parent_job_id == failed.id
        assert retry.targets() == failed.targets()
        acknowledged = acknowledge_backup_alert(db, failed)
        assert acknowledged.alert_acknowledged_at is not None
    finally:
        db.close()


def test_short_object_copy_fails_instead_of_claiming_success(sessions, tmp_path):
    db = sessions()
    try:
        queued = enqueue_backup_job(db, "7", config=runtime_config(tmp_path, "copy"))
        assert claim_next_backup_job(db, "worker-1")
    finally:
        db.close()

    with pytest.raises(RuntimeError, match="大小不一致"):
        execute_backup_job(
            queued.id,
            "worker-1",
            client=ShortReadMinio(complete_objects({"eduassets-input": {"book.pdf": b"pdf"}})),
            session_factory=sessions,
        )

    db = sessions()
    try:
        failed = db.query(BackupJob).filter(BackupJob.id == queued.id).one()
        assert failed.status == "failed"
        assert failed.alert_level == "critical"
        assert failed.copied_count == 0
    finally:
        db.close()


def test_stale_worker_lease_is_requeued(sessions, tmp_path):
    db = sessions()
    try:
        job = enqueue_backup_job(db, "7", config=runtime_config(tmp_path))
        job.status = "running"
        job.worker_id = "dead-worker"
        job.lease_expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
        assert recover_stale_backup_jobs(db) == 1
        db.refresh(job)
        assert job.status == "queued"
        assert job.worker_id is None
        assert "重新排队" in job.warnings()[0]
    finally:
        db.close()


def test_missing_current_bucket_fails_instead_of_producing_partial_success(sessions, tmp_path):
    db = sessions()
    try:
        queued = enqueue_backup_job(db, "7", config=runtime_config(tmp_path, "manifest"))
        assert claim_next_backup_job(db, "worker-1")
    finally:
        db.close()

    with pytest.raises(RuntimeError, match="Bucket 缺失"):
        execute_backup_job(
            queued.id,
            "worker-1",
            client=FakeMinio({"eduassets-input": {"book.pdf": b"pdf"}}),
            session_factory=sessions,
        )

    db = sessions()
    try:
        failed = db.query(BackupJob).filter(BackupJob.id == queued.id).one()
        assert failed.status == "failed"
        assert failed.alert_level == "critical"
    finally:
        db.close()
