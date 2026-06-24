from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException

from app.services.runtime_settings import (
    check_backup_targets,
    check_gpu_runtime,
    check_minio_contract,
    check_model_connectivity,
    load_runtime_config,
    run_manual_backup,
    runtime_status,
    save_runtime_config,
)
from app.utils.user_dep import get_user_id

router = APIRouter()


@router.get("/runtime/settings")
def get_runtime_settings(user_id: str = Depends(get_user_id)):
    _ = user_id
    return load_runtime_config(include_secrets=False)


@router.put("/runtime/settings")
def update_runtime_settings(payload: dict[str, Any] = Body(...), user_id: str = Depends(get_user_id)):
    _ = user_id
    try:
        return save_runtime_config(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"保存运行设置失败: {exc}")


@router.get("/runtime/status")
def get_runtime_status(user_id: str = Depends(get_user_id)):
    _ = user_id
    try:
        return runtime_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取运行状态失败: {exc}")


@router.post("/runtime/minio/check")
def check_minio(user_id: str = Depends(get_user_id)):
    _ = user_id
    try:
        return check_minio_contract(create_missing=False)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"检查 MinIO 失败: {exc}")


@router.post("/runtime/minio/ensure-buckets")
def ensure_minio_buckets(user_id: str = Depends(get_user_id)):
    _ = user_id
    try:
        return check_minio_contract(create_missing=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"维护 MinIO 篮子失败: {exc}")


@router.post("/runtime/gpu/check")
def check_gpu(user_id: str = Depends(get_user_id)):
    _ = user_id
    try:
        return check_gpu_runtime()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"检查 GPU 服务失败: {exc}")


@router.post("/runtime/models/check")
def check_models(user_id: str = Depends(get_user_id)):
    _ = user_id
    try:
        return check_model_connectivity()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"检查模型连通性失败: {exc}")


@router.post("/runtime/backup/check")
def check_backup(user_id: str = Depends(get_user_id)):
    _ = user_id
    try:
        return check_backup_targets()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"检查备份路径失败: {exc}")


@router.post("/runtime/backup/run")
def run_backup(user_id: str = Depends(get_user_id)):
    _ = user_id
    try:
        return run_manual_backup()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"执行备份失败: {exc}")
