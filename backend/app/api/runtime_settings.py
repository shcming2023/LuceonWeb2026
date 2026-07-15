from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.material import BackupJob
from app.models.user import User
from app.services.backup_jobs import (
    acknowledge_backup_alert,
    enqueue_backup_job,
    get_backup_job,
    list_backup_jobs,
    retry_backup_job,
)
from app.services.runtime_settings import (
    check_backup_targets,
    check_gpu_runtime,
    check_minio_contract,
    check_model_connectivity,
    load_runtime_config,
    runtime_status,
    save_runtime_config,
)
from app.utils.user_dep import require_runtime_admin

router = APIRouter()


@router.get("/runtime/settings")
def get_runtime_settings(admin_user: User = Depends(require_runtime_admin)):
    _ = admin_user
    return load_runtime_config(include_secrets=False)


@router.put("/runtime/settings")
def update_runtime_settings(payload: dict[str, Any] = Body(...), admin_user: User = Depends(require_runtime_admin)):
    _ = admin_user
    try:
        return save_runtime_config(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"保存运行设置失败: {exc}")


@router.get("/runtime/status")
def get_runtime_status(admin_user: User = Depends(require_runtime_admin)):
    _ = admin_user
    try:
        return runtime_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取运行状态失败: {exc}")


@router.post("/runtime/minio/check")
def check_minio(admin_user: User = Depends(require_runtime_admin)):
    _ = admin_user
    try:
        return check_minio_contract(create_missing=False)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"检查 MinIO 失败: {exc}")


@router.post("/runtime/minio/ensure-buckets")
def ensure_minio_buckets(admin_user: User = Depends(require_runtime_admin)):
    _ = admin_user
    try:
        return check_minio_contract(create_missing=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"维护 MinIO 篮子失败: {exc}")


@router.post("/runtime/gpu/check")
def check_gpu(admin_user: User = Depends(require_runtime_admin)):
    _ = admin_user
    try:
        return check_gpu_runtime()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"检查 GPU 服务失败: {exc}")


@router.post("/runtime/models/check")
def check_models(admin_user: User = Depends(require_runtime_admin)):
    _ = admin_user
    try:
        return check_model_connectivity()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"检查模型连通性失败: {exc}")


@router.post("/runtime/backup/check")
def check_backup(admin_user: User = Depends(require_runtime_admin)):
    _ = admin_user
    try:
        return check_backup_targets()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"检查备份路径失败: {exc}")


@router.post("/runtime/backup/jobs", status_code=202)
def run_backup(
    admin_user: User = Depends(require_runtime_admin),
    db: Session = Depends(get_db),
):
    try:
        return enqueue_backup_job(db, str(admin_user.id)).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"创建备份任务失败: {exc}")


@router.get("/runtime/backup/jobs")
def get_backup_jobs(
    limit: int = 50,
    admin_user: User = Depends(require_runtime_admin),
    db: Session = Depends(get_db),
):
    _ = admin_user
    return {"items": [job.to_dict() for job in list_backup_jobs(db, limit)]}


def _backup_job_or_404(db: Session, job_id: int) -> BackupJob:
    job = get_backup_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="备份任务不存在")
    return job


@router.get("/runtime/backup/jobs/{job_id}")
def get_backup_job_detail(
    job_id: int,
    admin_user: User = Depends(require_runtime_admin),
    db: Session = Depends(get_db),
):
    _ = admin_user
    return _backup_job_or_404(db, job_id).to_dict()


@router.post("/runtime/backup/jobs/{job_id}/retry", status_code=202)
def retry_backup(
    job_id: int,
    admin_user: User = Depends(require_runtime_admin),
    db: Session = Depends(get_db),
):
    try:
        return retry_backup_job(db, _backup_job_or_404(db, job_id), str(admin_user.id)).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/runtime/backup/jobs/{job_id}/alerts/acknowledge")
def acknowledge_backup_job_alert(
    job_id: int,
    admin_user: User = Depends(require_runtime_admin),
    db: Session = Depends(get_db),
):
    _ = admin_user
    try:
        return acknowledge_backup_alert(db, _backup_job_or_404(db, job_id)).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
