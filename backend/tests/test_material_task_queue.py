from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.material import Material, MetadataJob, PipelineRun, PipelineRunItem, PipelineStageAttempt
from app.models.material_metadata import MaterialMetadata
from app.services.material_task_queue import (
    MaterialTaskError,
    add_pipeline_run_items,
    claim_next_pipeline_run,
    enqueue_metadata_job,
    material_snapshot,
    pipeline_idempotency_key,
    project_pipeline_result,
    recover_stale_tasks,
    retry_metadata_job,
)
from app.services import material_inventory


def make_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def add_material(db, index: int, *, user_id: str = "u1") -> Material:
    material = Material(
        user_id=user_id,
        material_id=f"pdf-{index:016x}",
        source_hash=f"source-{index}",
        title=f"Book {index}",
        filename=f"book-{index}.pdf",
        source_type="uploaded",
        input_bucket="eduassets-input",
        input_object=f"book-{index}.pdf",
        input_sha256=f"{index:064x}",
        stage_status="input",
        pipeline_status="idle",
    )
    db.add(material)
    db.flush()
    return material


def add_run(db, materials: list[Material], *, mode: str = "apply") -> PipelineRun:
    snapshot = material_snapshot(db, "u1", [row.id for row in materials])
    run = PipelineRun(
        user_id="u1",
        status="running",
        mode=mode,
        idempotency_key=pipeline_idempotency_key("u1", mode, snapshot),
        request_json="{}",
        total=len(snapshot),
        current_stage="pipeline_command",
        created_at=datetime.utcnow(),
    )
    db.add(run)
    db.flush()
    add_pipeline_run_items(db, run, snapshot)
    return run


def freeze(material: Material, stage: str) -> dict:
    run_id = f"{stage}-run-{material.id}"
    bucket = "eduassets-mineru" if stage == "mineru" else "eduassets-minerupopo"
    prefix = "mineru" if stage == "mineru" else "minerupopo"
    return {
        "material_id": material.material_id,
        "run_id": run_id,
        "manifest": {"bucket": bucket, "object": f"{prefix}/{material.material_id}/{run_id}/manifest.json"},
    }


def test_snapshot_is_explicit_ordered_and_rejects_duplicate_content():
    db = make_session()
    first = add_material(db, 1)
    second = add_material(db, 2)

    snapshot = material_snapshot(db, "u1", [second.id, first.id])
    assert [row["material_pk"] for row in snapshot] == [second.id, first.id]

    second.input_sha256 = first.input_sha256
    with pytest.raises(MaterialTaskError, match="重复PDF"):
        material_snapshot(db, "u1", [first.id, second.id])


def test_three_item_result_is_partial_and_preserves_two_frozen_assets():
    db = make_session()
    materials = [add_material(db, value) for value in (1, 2, 3)]
    run = add_run(db, materials)
    payload = {
        "status": "PARTIAL",
        "mineru_batch_id": "mineru-batch",
        "mineru_freezes": [freeze(material, "mineru") for material in materials],
        "mineru_errors": [],
        "popo": {
            "batch_id": "popo-batch",
            "freezes": [freeze(materials[0], "popo"), freeze(materials[1], "popo")],
            "errors": [
                {
                    "material_id": materials[2].material_id,
                    "run_id": "popo-run-failed",
                    "stage": "popo",
                    "reason": "popo_stage_failed",
                    "error": {"message": "wrapper failure"},
                }
            ],
        },
    }

    outcome = project_pipeline_result(db, run, payload)
    db.commit()

    assert outcome == "partial"
    assert (run.total, run.success, run.failed) == (3, 2, 1)
    items = db.query(PipelineRunItem).order_by(PipelineRunItem.id).all()
    assert [item.status for item in items] == ["succeeded", "succeeded", "failed"]
    assert materials[0].popo_manifest_object.endswith("/manifest.json")
    assert materials[1].popo_manifest_object.endswith("/manifest.json")
    assert materials[2].popo_manifest_object is None
    assert db.query(MetadataJob).count() == 2
    assert db.query(PipelineStageAttempt).filter(PipelineStageAttempt.stage == "popo").count() == 3


def test_popo_resume_records_reused_mineru_without_new_mineru_freeze():
    db = make_session()
    material = add_material(db, 7)
    material.mineru_run_id = "mineru-frozen"
    material.mineru_manifest_bucket = "eduassets-mineru"
    material.mineru_manifest_object = f"mineru/{material.material_id}/mineru-frozen/manifest.json"
    run = add_run(db, [material], mode="resume_popo")

    outcome = project_pipeline_result(
        db,
        run,
        {
            "status": "DONE",
            "existing_mineru_batch_id": "mineru-batch",
            "mineru_freezes": [],
            "mineru_errors": [],
            "popo": {"batch_id": "popo-batch", "freezes": [freeze(material, "popo")], "errors": []},
        },
    )
    db.commit()

    mineru_attempt = db.query(PipelineStageAttempt).filter(PipelineStageAttempt.stage == "mineru").one()
    assert outcome == "succeeded"
    assert mineru_attempt.status == "succeeded"
    assert mineru_attempt.evidence()["reused"] is True
    assert mineru_attempt.external_run_id == "mineru-frozen"


def test_expired_pipeline_lease_is_requeued_and_claimed_after_restart():
    db = make_session()
    run = PipelineRun(
        user_id="u1",
        status="running",
        mode="apply",
        current_stage="pipeline_command",
        worker_id="dead-worker",
        lease_expires_at=datetime.utcnow() - timedelta(seconds=1),
        created_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()

    recovered = recover_stale_tasks(db)
    claimed = claim_next_pipeline_run(db, "new-worker")

    assert recovered["pipeline_runs"] == 1
    assert claimed.id == run.id
    assert claimed.status == "running"
    assert claimed.worker_id == "new-worker"
    assert claimed.attempt_count == 1


def test_automatic_metadata_job_never_overwrites_manual_override():
    db = make_session()
    material = add_material(db, 9)
    db.add(
        MaterialMetadata(
            user_id="u1",
            material_pk=material.id,
            status="manual",
            source="manual",
            manual_override=True,
        )
    )
    db.commit()

    assert enqueue_metadata_job(db, "u1", material, automatic=True) is None
    with pytest.raises(MaterialTaskError, match="不会覆盖"):
        enqueue_metadata_job(db, "u1", material)
    forced = enqueue_metadata_job(db, "u1", material, force=True)
    duplicate = enqueue_metadata_job(db, "u1", material, force=True)
    assert forced.id == duplicate.id


def test_duplicate_submit_reuses_active_run_and_global_gpu_slot(monkeypatch):
    db = make_session()
    first = add_material(db, 21)
    second = add_material(db, 22)
    monkeypatch.setattr(
        material_inventory,
        "run_pipeline_preflight",
        lambda *_args, **_kwargs: {"ready": True, "status": "DRY_RUN", "selected_count": 1},
    )

    run = material_inventory.start_pipeline_run(db, "u1", apply=True, material_pks=[first.id])
    duplicate = material_inventory.start_pipeline_run(db, "u1", apply=True, material_pks=[first.id])

    assert duplicate.id == run.id
    assert run.queue_slot == "gpu"
    assert db.query(PipelineRun).count() == 1
    with pytest.raises(MaterialTaskError, match="串行GPU队列"):
        material_inventory.start_pipeline_run(db, "u1", apply=True, material_pks=[second.id])


def test_failed_metadata_job_retries_but_manual_override_remains_protected():
    db = make_session()
    material = add_material(db, 23)
    job = enqueue_metadata_job(db, "u1", material)
    job.status = "failed"
    job.error_message = "temporary model error"
    db.commit()

    retried = retry_metadata_job(db, "u1", material.id, job.id)
    assert retried.status == "queued"
    assert retried.error_message is None

    retried.status = "failed"
    db.add(MaterialMetadata(user_id="u1", material_pk=material.id, status="manual", source="manual", manual_override=True))
    db.commit()
    with pytest.raises(MaterialTaskError, match="人工元数据"):
        retry_metadata_job(db, "u1", material.id, job.id)
