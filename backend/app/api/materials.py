import mimetypes
import re
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.material import Material, PipelineEvent, PipelineRun
from app.models.material_metadata import MaterialMetadata
from app.services.clean_to_standard import CleanToStandardPreflightError, clean_to_standard_preflight, start_clean_to_standard_run
from app.services.codex_skill_jobs import (
    CodexSkillJobError,
    cancel_codex_skill_job,
    create_codex_skill_job,
    enqueue_legacy_refresh_codex_jobs,
    get_codex_skill_job,
    latest_codex_skill_job_for_material,
    list_codex_skill_jobs,
    retry_codex_skill_job,
)
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
from app.services.material_metadata import (
    MetadataExtractionError,
    extract_metadata_with_ai,
    get_or_create_metadata,
    metadata_for_materials,
    metadata_options,
    metadata_to_dict,
    upsert_manual_metadata,
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
RUN_STAMP_PATTERN = re.compile(r"(20\d{12})")


def _run_stamp(value: str | None) -> str:
    match = RUN_STAMP_PATTERN.search(str(value or ""))
    return match.group(1) if match else ""


def _material_activity_sort_key(material: Material) -> tuple[str, str, str, int]:
    run_stamp = max(
        _run_stamp(material.latex_run_id),
        _run_stamp(material.standard_run_id),
        _run_stamp(material.clean_run_id),
        _run_stamp(material.raw_run_id),
        _run_stamp(material.popo_run_id),
        _run_stamp(material.mineru_run_id),
    )
    created = material.created_at.isoformat() if material.created_at else ""
    synced = material.last_synced_at.isoformat() if material.last_synced_at else ""
    return (run_stamp, created, synced, int(material.id or 0))


class PipelineStartRequest(BaseModel):
    apply: bool = False
    limit: int = 5
    material_id: str = ""
    input_object: str = ""


class PipelinePreflightRequest(BaseModel):
    limit: int = 5
    material_id: str = ""
    input_object: str = ""


class PopoToRawStartRequest(BaseModel):
    publish: bool = False
    force: bool = False


class PopoToRawPublishDryRunRequest(BaseModel):
    run_id: int
    force: bool = True


class RawToCleanStartRequest(BaseModel):
    publish: bool = True
    force: bool = False


class CleanToStandardStartRequest(BaseModel):
    publish: bool = True
    force: bool = False


class CodexSkillJobCreateRequest(BaseModel):
    mode: str = "new_pdf"
    requested_skill: str = "luceon-popo-to-refined-elegantbook"
    skill_version: str = "draft"
    run_reason: str = ""
    force: bool = False
    payload: dict = Field(default_factory=dict)


class CodexSkillBatchRefreshRequest(BaseModel):
    limit: int = 10
    material_ids: list[str] = Field(default_factory=list)


class MaterialMetadataUpdateRequest(BaseModel):
    original_title: str = ""
    publication_date: str = ""
    publication_year: int | None = None
    edition: str = ""
    subject: str = ""
    publication_country: str = ""
    series_name: str = ""
    publisher: str = ""
    isbn: str = ""
    language: str = ""
    grade_level: str = ""
    confidence: float | None = None
    evidence: list[dict] = []


class MaterialMetadataExtractRequest(BaseModel):
    force: bool = False


def _material_or_404(material_pk: int, user_id: str, db: Session) -> Material:
    material = db.query(Material).filter(Material.id == material_pk, Material.user_id == user_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="材料不存在")
    return material


def _legacy_stage_gone() -> None:
    raise HTTPException(status_code=410, detail="Raw/Clean/Standard 节点已下线")


def _popo_latex_gone() -> None:
    raise HTTPException(
        status_code=410,
        detail="LuceonWeb 不再执行 Popo→LaTeX/PDF；请由 Codex 异步产出 ElegantBook 后同步消费",
    )


@router.get("/materials")
def list_materials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", description="按文件名、material_id、MinIO 对象或教材元数据搜索"),
    stage: str = Query("", description="按阶段筛选"),
    metadata_status: str = Query("", description="按元数据状态筛选"),
    subject: str = Query("", description="按学科筛选"),
    country: str = Query("", description="按出版国家筛选"),
    series: str = Query("", description="按系列名筛选"),
    year_from: int | None = Query(None, ge=0, le=2200),
    year_to: int | None = Query(None, ge=0, le=2200),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    metadata_join = and_(MaterialMetadata.user_id == user_id, MaterialMetadata.material_pk == Material.id)
    query = db.query(Material).outerjoin(MaterialMetadata, metadata_join).filter(Material.user_id == user_id, Material.ignored.is_(False))
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Material.title.like(like),
                Material.filename.like(like),
                Material.material_id.like(like),
                Material.input_object.like(like),
                MaterialMetadata.original_title.like(like),
                MaterialMetadata.series_name.like(like),
                MaterialMetadata.publisher.like(like),
                MaterialMetadata.isbn.like(like),
                MaterialMetadata.subject.like(like),
                MaterialMetadata.edition.like(like),
            )
        )
    if metadata_status == "missing":
        query = query.filter(or_(MaterialMetadata.id.is_(None), MaterialMetadata.status == "missing"))
    elif metadata_status:
        query = query.filter(MaterialMetadata.status == metadata_status)
    if subject:
        query = query.filter(MaterialMetadata.subject == subject)
    if country:
        query = query.filter(MaterialMetadata.publication_country == country)
    if series:
        query = query.filter(MaterialMetadata.series_name.like(f"%{series}%"))
    if year_from is not None:
        query = query.filter(MaterialMetadata.publication_year >= year_from)
    if year_to is not None:
        query = query.filter(MaterialMetadata.publication_year <= year_to)
    if stage == "pdf":
        query = query.filter(Material.input_object.isnot(None))
    elif stage == "mineru":
        query = query.filter(or_(Material.mineru_manifest_object.isnot(None), Material.popo_manifest_object.isnot(None)))
    elif stage == "popo":
        query = query.filter(Material.popo_manifest_object.isnot(None))
    elif stage == "latex":
        query = query.filter(Material.latex_manifest_object.isnot(None))
    elif stage:
        query = query.filter(Material.stage_status == stage)

    rows_all = query.all()
    total = len(rows_all)
    rows_all.sort(key=_material_activity_sort_key, reverse=True)
    rows = rows_all[(page - 1) * page_size : page * page_size]
    metadata_map = metadata_for_materials(db, user_id, [row.id for row in rows])
    material_rows = []
    for row in rows:
        data = row.to_dict()
        data["book_metadata"] = metadata_to_dict(metadata_map.get(row.id))
        dry_run = latest_successful_popo_to_raw_dry_run(db, user_id, row.material_id or "")
        data["raw_dry_run_available"] = bool(dry_run)
        data["raw_dry_run_id"] = str(dry_run.id) if dry_run else ""
        latest_codex_job = latest_codex_skill_job_for_material(db, user_id, row)
        data["codex_job"] = latest_codex_job.to_dict() if latest_codex_job else None
        material_rows.append(data)
    return {"total": total, "page": page, "page_size": page_size, "materials": material_rows}


@router.get("/materials/metadata/options")
def get_material_metadata_options(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    return metadata_options(db, user_id)


@router.get("/materials/{material_pk}/metadata")
def get_material_metadata(
    material_pk: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    metadata = get_or_create_metadata(db, user_id, material)
    db.commit()
    db.refresh(metadata)
    return metadata.to_dict()


@router.patch("/materials/{material_pk}/metadata")
def update_material_metadata(
    material_pk: int,
    payload: MaterialMetadataUpdateRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    metadata = upsert_manual_metadata(db, user_id, material, payload.model_dump())
    db.commit()
    db.refresh(metadata)
    return metadata.to_dict()


@router.post("/materials/{material_pk}/metadata/extract")
def extract_material_metadata(
    material_pk: int,
    payload: MaterialMetadataExtractRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    try:
        metadata = extract_metadata_with_ai(db, user_id, material, force=payload.force)
        db.commit()
        db.refresh(metadata)
        return metadata.to_dict()
    except MetadataExtractionError as exc:
        db.rollback()
        metadata = get_or_create_metadata(db, user_id, material)
        metadata.status = "failed"
        metadata.extraction_error = str(exc)
        db.commit()
        if str(exc) == "manual_override":
            raise HTTPException(status_code=409, detail="该材料元数据已被人工修改；如需覆盖，请勾选强制重新提取")
        raise HTTPException(status_code=409, detail=f"元数据提取失败：{exc}")


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


@router.post("/materials/{material_pk}/codex-jobs")
def create_material_codex_job(
    material_pk: int,
    payload: CodexSkillJobCreateRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    try:
        job_payload = dict(payload.payload or {})
        if payload.run_reason:
            job_payload["run_reason"] = payload.run_reason
        job = create_codex_skill_job(
            db,
            user_id,
            material,
            mode=payload.mode,
            requested_skill=payload.requested_skill,
            skill_version=payload.skill_version,
            force=payload.force,
            payload=job_payload,
        )
        db.commit()
        db.refresh(job)
    except CodexSkillJobError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建 Codex 精修任务失败: {exc}")
    return job.to_dict()


@router.get("/materials/{material_pk}/codex-jobs")
def list_material_codex_jobs(
    material_pk: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    return {"jobs": [job.to_dict() for job in list_codex_skill_jobs(db, user_id, material)]}


@router.post("/materials/codex-jobs/batch-refresh-legacy")
def create_legacy_refresh_codex_jobs(
    payload: CodexSkillBatchRefreshRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    try:
        summary = enqueue_legacy_refresh_codex_jobs(
            db,
            user_id,
            limit=payload.limit,
            material_ids=payload.material_ids,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建旧产物刷新队列失败: {exc}")
    return summary


@router.get("/materials/codex-jobs/{job_id}")
def get_material_codex_job(
    job_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    job = get_codex_skill_job(db, user_id, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Codex 精修任务不存在")
    return job.to_dict()


@router.post("/materials/codex-jobs/{job_id}/cancel")
def cancel_material_codex_job(
    job_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    job = get_codex_skill_job(db, user_id, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Codex 精修任务不存在")
    try:
        cancel_codex_skill_job(job)
        db.commit()
        db.refresh(job)
    except CodexSkillJobError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    return job.to_dict()


@router.post("/materials/codex-jobs/{job_id}/retry")
def retry_material_codex_job(
    job_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    job = get_codex_skill_job(db, user_id, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Codex 精修任务不存在")
    try:
        retry_codex_skill_job(job)
        db.commit()
        db.refresh(job)
    except CodexSkillJobError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    return job.to_dict()


@router.post("/materials/pipeline/preflight")
def pipeline_preflight(
    payload: PipelinePreflightRequest,
    user_id: str = Depends(get_user_id),
):
    _ = user_id
    try:
        return run_pipeline_preflight(payload.limit, material_id=payload.material_id, input_object=payload.input_object)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"解析预检失败: {exc}")


@router.post("/materials/pipeline/start")
def start_pipeline(
    payload: PipelineStartRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    try:
        run = start_pipeline_run(
            db,
            user_id,
            apply=payload.apply,
            limit=payload.limit,
            material_id=payload.material_id,
            input_object=payload.input_object,
        )
    except PipelinePreflightError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail={"message": "综合预检未通过", "preflight": exc.preflight})
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"启动解析任务失败: {exc}")
    return run.to_dict()


@router.post("/materials/{material_pk}/popo2latex/preflight")
def preflight_popo_to_latex(
    material_pk: int,
    force: bool = Query(False),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    _ = (material_pk, force, user_id, db)
    _popo_latex_gone()


@router.post("/materials/{material_pk}/popo2latex/start")
def start_popo_to_latex(
    material_pk: int,
    payload: dict | None = None,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    _ = (material_pk, payload, user_id, db)
    _popo_latex_gone()


@router.post("/materials/{material_pk}/popo2raw/preflight")
def preflight_popo_to_raw(
    material_pk: int,
    force: bool = Query(False),
    publish: bool = Query(False),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    _ = (material_pk, force, publish, user_id, db)
    _legacy_stage_gone()


@router.post("/materials/{material_pk}/popo2raw/start")
def start_popo_to_raw(
    material_pk: int,
    payload: PopoToRawStartRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    _ = (material_pk, payload, user_id, db)
    _legacy_stage_gone()


@router.post("/materials/{material_pk}/popo2raw/publish_dry_run")
def publish_popo_to_raw_dry_run_endpoint(
    material_pk: int,
    payload: PopoToRawPublishDryRunRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    _ = (material_pk, payload, user_id, db)
    _legacy_stage_gone()


@router.post("/materials/{material_pk}/raw2clean/preflight")
def preflight_raw_to_clean(
    material_pk: int,
    force: bool = Query(False),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    _ = (material_pk, force, user_id, db)
    _legacy_stage_gone()


@router.post("/materials/{material_pk}/raw2clean/start")
def start_raw_to_clean(
    material_pk: int,
    payload: RawToCleanStartRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    _ = (material_pk, payload, user_id, db)
    _legacy_stage_gone()


@router.post("/materials/{material_pk}/clean2standard/preflight")
def preflight_clean_to_standard(
    material_pk: int,
    force: bool = Query(False),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    _ = (material_pk, force, user_id, db)
    _legacy_stage_gone()


@router.post("/materials/{material_pk}/clean2standard/start")
def start_clean_to_standard(
    material_pk: int,
    payload: CleanToStandardStartRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    _ = (material_pk, payload, user_id, db)
    _legacy_stage_gone()


@router.get("/materials/{material_pk}")
def material_detail(
    material_pk: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    material = _material_or_404(material_pk, user_id, db)
    data = material.to_dict()
    latest_codex_job = latest_codex_skill_job_for_material(db, user_id, material)
    data["codex_job"] = latest_codex_job.to_dict() if latest_codex_job else None
    return data


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


@router.get("/materials/{material_pk}/popo_latex_export")
def material_popo_latex_export(
    material_pk: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    _ = (material_pk, user_id, db)
    _popo_latex_gone()


@router.get("/materials/{material_pk}/latex_export")
def material_latex_export(
    material_pk: int,
    stage: str = Query("popo", description="已下线；请在 PDF 比对页下载 Codex ElegantBook ZIP"),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    _ = (material_pk, stage, user_id, db)
    _popo_latex_gone()


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
