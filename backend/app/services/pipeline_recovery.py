from datetime import datetime

from app.database import SessionLocal
from app.models.material import Material, PipelineRun
from app.services.material_inventory import create_pipeline_event


def recover_interrupted_pipeline_runs() -> dict[str, int]:
    db = SessionLocal()
    try:
        runs = (
            db.query(PipelineRun)
            .filter(PipelineRun.status.in_(["queued", "running"]))
            .order_by(PipelineRun.created_at.asc(), PipelineRun.id.asc())
            .all()
        )
        recovered = 0
        for run in runs:
            run.status = "failed"
            run.current_stage = "interrupted"
            run.failed = max(run.failed or 0, 1)
            run.finished_at = datetime.utcnow()
            run.error_message = "服务重启中断了后台任务，请重新发起 dry-run 或发布任务。"
            create_pipeline_event(
                db,
                run,
                "服务重启中断了后台任务，请重新发起任务",
                stage="interrupted",
                level="warning",
                payload={"recovered_at": run.finished_at.isoformat(), "previous_mode": run.mode},
            )
            recovered += 1

        materials = (
            db.query(Material)
            .filter(Material.pipeline_status.in_(["queued", "running"]))
            .all()
        )
        reset_materials = 0
        for material in materials:
            material.pipeline_status = "idle"
            reset_materials += 1

        db.commit()
        return {"runs_recovered": recovered, "materials_reset": reset_materials}
    finally:
        db.close()
