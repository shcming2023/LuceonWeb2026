import mimetypes
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.material import Material, PipelineEvent, PipelineRun
from app.services.material_inventory import (
    INPUT_BUCKET,
    PipelinePreflightError,
    latest_pipeline_run,
    material_summary,
    minio_client,
    run_pipeline_preflight,
    start_pipeline_run,
    sync_material_inventory,
    upload_input_pdfs,
)
from app.services.popo_to_raw import (
    PopoToRawPreflightError,
    PopoToRawPublishError,
    latest_successful_popo_to_raw_dry_run,
    popo_to_raw_preflight,
    publish_popo_to_raw_dry_run,
    start_popo_to_raw_run,
)
from app.services.popo_to_raw_audit import audit_popo_to_raw_run
from app.services.raw_to_clean import RawToCleanPreflightError, raw_to_clean_preflight, start_raw_to_clean_run
from app.utils.minio_client import get_presigned_url
from app.utils.user_dep import get_user_id

router = APIRouter()


class PipelineStartRequest(BaseModel):
    apply: bool = False
    limit: int = 5


class PipelinePreflightRequest(BaseModel):
    limit: int = 5


class PopoToRawStartRequest(BaseModel):
    publish: bool = False
    force: bool = False


class PopoToRawPublishDryRunRequest(BaseModel):
    run_id: int
    force: bool = True


class RawToCleanStartRequest(BaseModel):
    publish: bool = True
    force: bool = False


def _material_or_404(material_pk: int, user_id: str, db: Session) -> Material:
    material = db.query(Material).filter(Material.id == material_pk, Material.user_id == user_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="材料不存在")
    return material


@router.get("/materials")
def list_materials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", description="按文件名、material_id 或 MinIO 对象搜索"),
    stage: str = Query("", description="按阶段筛选"),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    query = db.query(Material).filter(Material.user_id == user_id, Material.ignored.is_(False))
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Material.title.like(like),
                Material.filename.like(like),
                Material.material_id.like(like),
                Material.input_object.like(like),
            )
        )
    if stage == "pdf":
        query = query.filter(Material.input_object.isnot(None))
    elif stage == "mineru":
        query = query.filter(or_(Material.mineru_manifest_object.isnot(None), Material.popo_manifest_object.isnot(None)))
    elif stage == "popo":
        query = query.filter(Material.popo_manifest_object.isnot(None))
    elif stage == "raw":
        query = query.filter(Material.raw_manifest_object.isnot(None))
    elif stage == "clean":
        query = query.filter(Material.clean_manifest_object.isnot(None))
    elif stage:
        query = query.filter(Material.stage_status == stage)

    total = query.count()
    rows = (
        query.order_by(
            Material.last_synced_at.is_(None),
            Material.last_synced_at.desc(),
            Material.created_at.desc(),
            Material.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    material_rows = []
    for row in rows:
        data = row.to_dict()
        dry_run = latest_successful_popo_to_raw_dry_run(db, user_id, row.material_id or "")
        data["raw_dry_run_available"] = bool(dry_run)
        data["raw_dry_run_id"] = str(dry_run.id) if dry_run else ""
        material_rows.append(data)
    return {"total": total, "page": page, "page_size": page_size, "materials": material_rows}


@router.get("/materials/summary")
def get_material_summary(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    return material_summary(db, user_id)


@router.post("/materials/sync")
def sync_materials(
    limit: int | None = Query(None, ge=1, le=1000),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    try:
        summary = sync_material_inventory(db, user_id, limit=limit)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"同步 MinIO 资产失败: {exc}")
    return summary


@router.post("/materials/upload")
async def upload_materials(
    files: list[UploadFile] = File(...),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    try:
        return await upload_input_pdfs(files, user_id, db)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"上传 PDF 失败: {exc}")


@router.get("/materials/pipeline/status")
def pipeline_status(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    run = latest_pipeline_run(db, user_id)
    events = []
    if run:
        events = (
            db.query(PipelineEvent)
            .filter(PipelineEvent.run_id == run.id, PipelineEvent.user_id == user_id)
            .order_by(PipelineEvent.created_at.desc(), PipelineEvent.id.desc())
            .limit(20)
            .all()
        )
    return {
        "run": run.to_dict() if run else None,
        "events": [event.to_dict() for event in events],
        "audit": audit_popo_to_raw_run(db, run) if run and run.mode == "popo2raw" else None,
    }


@router.get("/materials/pipeline/runs/{run_id}/artifact")
def pipeline_run_artifact(
    run_id: int,
    path: str = Query(..., min_length=1),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id, PipelineRun.user_id == user_id).first()
    if not run or run.mode != "popo2raw":
        raise HTTPException(status_code=404, detail="任务产物不存在")

    summary = run.summary()
    body_final = Path(str(summary.get("body_final") or "")).resolve()
    if not body_final.exists() or not body_final.is_dir():
        raise HTTPException(status_code=404, detail="dry-run 产物目录不存在")

    requested = (body_final / path).resolve()
    if body_final != requested and body_final not in requested.parents:
        raise HTTPException(status_code=400, detail="非法产物路径")
    if not requested.exists() or not requested.is_file():
        raise HTTPException(status_code=404, detail="产物文件不存在")

    media_type = mimetypes.guess_type(requested.name)[0] or "application/octet-stream"

    def iter_file():
        with requested.open("rb") as stream:
            while True:
                chunk = stream.read(64 * 1024)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(
        iter_file(),
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(requested.name)}"},
    )


@router.post("/materials/pipeline/preflight")
def pipeline_preflight(
    payload: PipelinePreflightRequest,
    user_id: str = Depends(get_user_id),
):
    _ = user_id
    try:
        return run_pipeline_preflight(payload.limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"解析预检失败: {exc}")


@router.post("/materials/pipeline/start")
def start_pipeline(
    payload: PipelineStartRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    try:
        run = start_pipeline_run(db, user_id, apply=payload.apply, limit=payload.limit)
    except PipelinePreflightError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail={"message": "综合预检未通过", "preflight": exc.preflight})
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"启动解析任务失败: {exc}")
    return run.to_dict()


@router.post("/materials/{material_pk}/popo2raw/preflight")
def preflight_popo_to_raw(
    material_pk: int,
    force: bool = Query(False),
    publish: bool = Query(False),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    try:
        return popo_to_raw_preflight(material, force=force, publish=publish)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Popo→Raw 预检失败: {exc}")


@router.post("/materials/{material_pk}/popo2raw/start")
def start_popo_to_raw(
    material_pk: int,
    payload: PopoToRawStartRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    try:
        run = start_popo_to_raw_run(db, user_id, material, publish=payload.publish, force=payload.force)
    except PopoToRawPreflightError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail={"message": "Popo→Raw 预检未通过", "preflight": exc.preflight})
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"启动 Popo→Raw 失败: {exc}")
    return run.to_dict()


@router.post("/materials/{material_pk}/popo2raw/publish_dry_run")
def publish_popo_to_raw_dry_run_endpoint(
    material_pk: int,
    payload: PopoToRawPublishDryRunRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    try:
        run = publish_popo_to_raw_dry_run(db, user_id, material, dry_run_id=payload.run_id, force=payload.force)
    except PopoToRawPreflightError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail={"message": "Popo→Raw 发布预检未通过", "preflight": exc.preflight})
    except PopoToRawPublishError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"发布 Popo→Raw dry-run 失败: {exc}")
    return run.to_dict()


@router.post("/materials/{material_pk}/raw2clean/preflight")
def preflight_raw_to_clean(
    material_pk: int,
    force: bool = Query(False),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    try:
        return raw_to_clean_preflight(material, force=force)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Raw→Clean 预检失败: {exc}")


@router.post("/materials/{material_pk}/raw2clean/start")
def start_raw_to_clean(
    material_pk: int,
    payload: RawToCleanStartRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    try:
        run = start_raw_to_clean_run(db, user_id, material, publish=payload.publish, force=payload.force)
    except RawToCleanPreflightError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail={"message": "Raw→Clean 预检未通过", "preflight": exc.preflight})
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"启动 Raw→Clean 失败: {exc}")
    return run.to_dict()


@router.get("/materials/{material_pk}")
def material_detail(
    material_pk: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    return _material_or_404(material_pk, user_id, db).to_dict()


@router.get("/materials/{material_pk}/download_url")
def material_download_url(
    material_pk: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    if not material.input_object:
        raise HTTPException(status_code=404, detail="源 PDF 不存在")
    return {"url": get_presigned_url(material.input_bucket or INPUT_BUCKET, material.input_object)}


@router.get("/materials/{material_pk}/content")
def material_content(
    material_pk: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    if not material.input_object:
        raise HTTPException(status_code=404, detail="源 PDF 不存在")

    try:
        response = minio_client.get_object(material.input_bucket or INPUT_BUCKET, material.input_object)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取源 PDF 失败: {exc}")

    def iter_file():
        try:
            stream = getattr(response, "stream", None)
            if stream:
                yield from stream(32 * 1024)
            else:
                yield response.read()
        finally:
            close = getattr(response, "close", None)
            if close:
                close()
            release_conn = getattr(response, "release_conn", None)
            if release_conn:
                release_conn()

    media_type = mimetypes.guess_type(material.filename)[0] or "application/pdf"
    encoded_filename = quote(material.filename)
    return StreamingResponse(
        iter_file(),
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"},
    )


@router.get("/materials/{material_pk}/review_target")
def material_review_target(
    material_pk: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    if not material.review_asset_id:
        raise HTTPException(status_code=404, detail="审查资产尚未同步")
    return {"review_asset_id": str(material.review_asset_id)}
