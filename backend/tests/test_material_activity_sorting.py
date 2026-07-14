from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.api.materials import _material_activity_sort_key


def material(material_id: int, created_at: datetime, *, source_type: str = "imported", stage: str = "latex_done"):
    return SimpleNamespace(
        id=material_id,
        source_type=source_type,
        stage_status=stage,
        pipeline_status="idle",
        created_at=created_at,
        mineru_run_id="",
        popo_run_id="",
        raw_run_id="",
        clean_run_id="",
        standard_run_id="",
        latex_run_id="",
    )


def codex_job(status: str, created_at: datetime):
    return SimpleNamespace(status=status, created_at=created_at)


def test_recent_upload_sorts_above_stale_queued_job():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    recent_upload = material(2, now, source_type="uploaded", stage="input")
    stale_material = material(1, now - timedelta(days=3))
    stale_queue = codex_job("queued", now - timedelta(days=3))

    assert _material_activity_sort_key(recent_upload) > _material_activity_sort_key(stale_material, stale_queue)


def test_running_job_stays_above_recent_upload():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    recent_upload = material(2, now, source_type="uploaded", stage="input")
    running_material = material(1, now - timedelta(days=3))
    running_job = codex_job("running", now - timedelta(days=3))

    assert _material_activity_sort_key(running_material, running_job) > _material_activity_sort_key(recent_upload)
