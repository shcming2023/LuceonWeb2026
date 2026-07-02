import hashlib
import json
import os
import posixpath
import subprocess
import threading
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.material import Material, PipelineEvent, PipelineRun
from app.models.review_asset import ReviewAsset
from app.services.luceon_review import (
    ObjectRef,
    clean_path,
    list_input_pdf_objects,
    list_manifest_objects,
    minio_client,
    parse_json_bytes,
    read_object,
    resolve_manifest,
)
from app.services.runtime_settings import pipeline_env


INPUT_BUCKET = "eduassets-input"
MINERU_BUCKET = "eduassets-mineru"
POPO_BUCKET = "eduassets-minerupopo"
RAW_BUCKET = "eduassets-raw"
CLEAN_BUCKET = "eduassets-clean"
STANDARD_BUCKET = "eduassets-standard"

DEFAULT_PIPELINE_SCRIPT = str(Path(__file__).resolve().parents[2] / "scripts" / "luceon_pdf_pipeline.py")
PIPELINE_SCRIPT = os.getenv("LUCEON_PIPELINE_SCRIPT", DEFAULT_PIPELINE_SCRIPT)
PIPELINE_WORKDIR = os.getenv("LUCEON_PIPELINE_WORKDIR", str(Path(PIPELINE_SCRIPT).resolve().parent))


class PipelinePreflightError(RuntimeError):
    def __init__(self, preflight: dict[str, Any]):
        super().__init__("综合预检未通过")
        self.preflight = preflight


def source_hash(bucket: str, object_name: str) -> str:
    return hashlib.sha256(f"{bucket}/{object_name}".encode("utf-8")).hexdigest()[:24]


def material_id_from_sha256(sha256: str) -> str:
    return f"pdf-{sha256[:16]}" if sha256 else ""


def is_material_placeholder(value: str | None) -> bool:
    cleaned = str(value or "").strip()
    return cleaned.startswith("pdf-") and "." not in Path(cleaned).name


def display_name_from_candidates(title: str, filename: str, input_ref: ObjectRef | None = None) -> str:
    for value in (filename, title):
        cleaned = str(value or "").strip()
        if cleaned and not is_material_placeholder(cleaned):
            return cleaned
    if input_ref:
        name = Path(input_ref.object).name
        if name:
            return name
    return filename or title


def infer_ids_from_manifest_path(manifest_object: str) -> tuple[str, str]:
    parts = clean_path(manifest_object).split("/")
    if len(parts) >= 4 and parts[-1] == "manifest.json":
        return parts[-3], parts[-2]
    return "", ""


def list_two_level_manifests(bucket: str, prefix: str, limit: int | None = None) -> list[str]:
    normalized_prefix = clean_path(prefix).rstrip("/") + "/"
    rows: list[str] = []
    for material_item in minio_client.list_objects(bucket, prefix=normalized_prefix, recursive=False):
        raw_material_prefix = str(getattr(material_item, "object_name", "") or "").replace("\\", "/").lstrip("/")
        if not raw_material_prefix.endswith("/") and not getattr(material_item, "is_dir", False):
            continue
        material_prefix = clean_path(raw_material_prefix).rstrip("/") + "/"
        for run_item in minio_client.list_objects(bucket, prefix=material_prefix, recursive=False):
            raw_run_prefix = str(getattr(run_item, "object_name", "") or "").replace("\\", "/").lstrip("/")
            if raw_run_prefix.endswith("/") or getattr(run_item, "is_dir", False):
                run_prefix = clean_path(raw_run_prefix).rstrip("/") + "/"
                manifest_object = f"{run_prefix}manifest.json"
                if object_exists(bucket, manifest_object):
                    rows.append(manifest_object)
                    if limit and len(rows) >= limit:
                        return sorted(rows)
    return sorted(rows)


def object_exists(bucket: str, object_name: str) -> bool:
    try:
        minio_client.stat_object(bucket, object_name)
        return True
    except Exception:
        return False


def object_stat(bucket: str, object_name: str) -> tuple[int | None, str | None]:
    try:
        stat = minio_client.stat_object(bucket, object_name)
    except Exception:
        return None, None
    return getattr(stat, "size", None), getattr(stat, "content_type", None)


def read_json_object(bucket: str, object_name: str) -> dict[str, Any]:
    try:
        return parse_json_bytes(read_object(bucket, object_name))
    except Exception:
        return {}


def material_query(db: Session, user_id: str, material_id: str = "", input_ref: ObjectRef | None = None):
    query = db.query(Material).filter(Material.user_id == user_id)
    by_material = query.filter(Material.material_id == material_id).first() if material_id else None
    by_input = (
        query.filter(Material.input_bucket == input_ref.bucket, Material.input_object == input_ref.object).first()
        if input_ref
        else None
    )
    if by_material and by_input and by_material.id != by_input.id:
        return merge_material_rows(db, by_input, by_material)
    return by_input or by_material


def merge_material_rows(db: Session, target: Material, duplicate: Material) -> Material:
    fields = [
        "material_id",
        "source_hash",
        "title",
        "filename",
        "source_type",
        "input_sha256",
        "size_bytes",
        "content_type",
        "mineru_manifest_bucket",
        "mineru_manifest_object",
        "mineru_run_id",
        "popo_manifest_bucket",
        "popo_manifest_object",
        "popo_run_id",
        "raw_manifest_bucket",
        "raw_manifest_object",
        "raw_run_id",
        "clean_manifest_bucket",
        "clean_manifest_object",
        "clean_run_id",
        "standard_manifest_bucket",
        "standard_manifest_object",
        "standard_run_id",
        "standard_quality_score",
        "review_asset_id",
    ]
    for field in fields:
        if not getattr(target, field) and getattr(duplicate, field):
            setattr(target, field, getattr(duplicate, field))
    target.promote_stage(duplicate.stage_status or "input")
    if duplicate.last_synced_at and not target.last_synced_at:
        target.last_synced_at = duplicate.last_synced_at
    db.delete(duplicate)
    db.flush()
    return target


def upsert_material(
    db: Session,
    user_id: str,
    title: str,
    filename: str,
    material_id: str = "",
    input_ref: ObjectRef | None = None,
    source_type: str = "imported",
) -> Material:
    display_name = display_name_from_candidates(title, filename, input_ref)
    material = material_query(db, user_id, material_id=material_id, input_ref=input_ref)
    if not material:
        material = Material(
            user_id=user_id,
            title=display_name or material_id or "untitled.pdf",
            filename=display_name or material_id or "untitled.pdf",
            material_id=material_id or None,
            source_type=source_type,
            stage_status="input",
            pipeline_status="idle",
        )
        db.add(material)
    if material_id and not material.material_id:
        material.material_id = material_id
    if display_name and (not material.title or is_material_placeholder(material.title)):
        material.title = display_name
    if display_name and (not material.filename or is_material_placeholder(material.filename)):
        material.filename = display_name
    if input_ref:
        material.input_bucket = input_ref.bucket
        material.input_object = input_ref.object
        material.source_hash = source_hash(input_ref.bucket, input_ref.object)
        size_bytes, content_type = object_stat(input_ref.bucket, input_ref.object)
        material.size_bytes = material.size_bytes or size_bytes
        material.content_type = material.content_type or content_type
    material.last_synced_at = datetime.utcnow()
    return material


def link_review_asset(db: Session, material: Material) -> None:
    query = db.query(ReviewAsset).filter(ReviewAsset.user_id == material.user_id)
    review_asset = None
    if material.material_id:
        review_asset = query.filter(ReviewAsset.material_id == material.material_id).order_by(ReviewAsset.id.desc()).first()
    if not review_asset and material.input_bucket and material.input_object:
        review_asset = query.filter(
            ReviewAsset.input_pdf_bucket == material.input_bucket,
            ReviewAsset.input_pdf_object == material.input_object,
        ).order_by(ReviewAsset.id.desc()).first()
    if review_asset:
        material.review_asset_id = review_asset.id


def ensure_input_review_asset(db: Session, user_id: str, bucket: str, object_name: str) -> ReviewAsset | None:
    existing = (
        db.query(ReviewAsset)
        .filter(
            ReviewAsset.user_id == user_id,
            ReviewAsset.input_pdf_bucket == bucket,
            ReviewAsset.input_pdf_object == object_name,
        )
        .order_by(ReviewAsset.id.desc())
        .first()
    )
    if existing:
        return existing

    filename = Path(object_name).name
    asset = ReviewAsset(
        user_id=user_id,
        title=filename,
        input_filename=filename,
        review_stage="input",
        manifest_bucket=bucket,
        manifest_object=f"__input__/{object_name}",
        input_pdf_bucket=bucket,
        input_pdf_object=object_name,
        review_status="pending",
    )
    db.add(asset)
    db.flush()
    return asset


def ensure_resolved_review_asset(db: Session, user_id: str, resolved) -> ReviewAsset:
    if resolved.input_pdf:
        input_only = (
            db.query(ReviewAsset)
            .filter(
                ReviewAsset.user_id == user_id,
                ReviewAsset.input_pdf_bucket == resolved.input_pdf.bucket,
                ReviewAsset.input_pdf_object == resolved.input_pdf.object,
                ReviewAsset.manifest_json.is_(None),
            )
            .first()
        )
        if input_only:
            db.delete(input_only)
            db.flush()

    asset = (
        db.query(ReviewAsset)
        .filter(
            ReviewAsset.user_id == user_id,
            ReviewAsset.manifest_bucket == resolved.manifest_ref.bucket,
            ReviewAsset.manifest_object == resolved.manifest_ref.object,
        )
        .first()
    )
    if not asset:
        asset = ReviewAsset(
            user_id=user_id,
            manifest_bucket=resolved.manifest_ref.bucket,
            manifest_object=resolved.manifest_ref.object,
            review_status="pending",
        )
        db.add(asset)

    fallback_title = resolved.title or resolved.input_filename or resolved.material_id or Path(resolved.manifest_ref.object).parent.name
    asset.title = asset.title or fallback_title
    asset.input_filename = resolved.input_filename or fallback_title
    asset.review_stage = resolved.review_stage
    asset.material_id = resolved.material_id
    asset.run_id = resolved.run_id
    asset.input_pdf_bucket = resolved.input_pdf.bucket if resolved.input_pdf else None
    asset.input_pdf_object = resolved.input_pdf.object if resolved.input_pdf else None
    asset.source_pdf_bucket = resolved.source_pdf.bucket if resolved.source_pdf else None
    asset.source_pdf_object = resolved.source_pdf.object if resolved.source_pdf else None
    asset.markdown_bucket = resolved.markdown.bucket if resolved.markdown else None
    asset.markdown_object = resolved.markdown.object if resolved.markdown else None
    asset.page_markdown_bucket = resolved.page_markdown.bucket if resolved.page_markdown else None
    asset.page_markdown_object = resolved.page_markdown.object if resolved.page_markdown else None
    asset.popo_markdown_bucket = resolved.popo_markdown.bucket if resolved.popo_markdown else None
    asset.popo_markdown_object = resolved.popo_markdown.object if resolved.popo_markdown else None
    asset.middle_json_bucket = resolved.middle_json.bucket if resolved.middle_json else None
    asset.middle_json_object = resolved.middle_json.object if resolved.middle_json else None
    asset.manifest_json = json.dumps(resolved.manifest, ensure_ascii=False)
    db.flush()
    return asset


def sync_input_materials(db: Session, user_id: str, limit: int | None = None) -> dict[str, int]:
    count = 0
    for object_name in list_input_pdf_objects(INPUT_BUCKET, limit=limit):
        filename = Path(object_name).name
        material = upsert_material(
            db,
            user_id,
            title=filename,
            filename=filename,
            input_ref=ObjectRef(INPUT_BUCKET, object_name),
        )
        material.promote_stage("input")
        asset = ensure_input_review_asset(db, user_id, INPUT_BUCKET, object_name)
        material.review_asset_id = asset.id if asset else material.review_asset_id
        link_review_asset(db, material)
        count += 1
    return {"input": count}


def sync_mineru_materials(db: Session, user_id: str, limit: int | None = None) -> dict[str, int]:
    count = 0
    for manifest_object in list_two_level_manifests(MINERU_BUCKET, "mineru/", limit=limit):
        resolved = resolve_manifest(MINERU_BUCKET, manifest_object, check_fallbacks=False)
        material_id = resolved.material_id
        run_id = resolved.run_id
        manifest = resolved.manifest
        source_pdf = manifest.get("source_pdf") if isinstance(manifest.get("source_pdf"), dict) else {}
        filename = str(source_pdf.get("filename") or material_id or Path(manifest_object).parent.name)
        input_object = clean_path(source_pdf.get("input_object"))
        input_ref = ObjectRef(str(source_pdf.get("input_bucket") or INPUT_BUCKET), input_object) if input_object else None
        material = upsert_material(db, user_id, filename, filename, material_id=material_id, input_ref=input_ref)
        asset = ensure_resolved_review_asset(db, user_id, resolved)
        material.mineru_manifest_bucket = MINERU_BUCKET
        material.mineru_manifest_object = manifest_object
        material.mineru_run_id = run_id
        material.promote_stage("mineru_done")
        material.review_asset_id = asset.id
        link_review_asset(db, material)
        count += 1
    return {"mineru": count}


def sync_popo_materials(db: Session, user_id: str, limit: int | None = None) -> dict[str, int]:
    count = 0
    for manifest_object in list_manifest_objects(POPO_BUCKET, "minerupopo/", limit=limit):
        resolved = resolve_manifest(POPO_BUCKET, manifest_object, check_fallbacks=False)
        resolved_filename = resolved.input_filename
        if not resolved_filename and resolved.input_pdf:
            resolved_filename = Path(resolved.input_pdf.object).name
        material = upsert_material(
            db,
            user_id,
            title=resolved_filename or resolved.title,
            filename=resolved_filename or resolved.title,
            material_id=resolved.material_id,
            input_ref=resolved.input_pdf,
        )
        asset = ensure_resolved_review_asset(db, user_id, resolved)
        material.popo_manifest_bucket = POPO_BUCKET
        material.popo_manifest_object = manifest_object
        material.popo_run_id = resolved.run_id
        if resolved.manifest:
            source_pdf = resolved.manifest.get("source_pdf") if isinstance(resolved.manifest.get("source_pdf"), dict) else {}
            material.input_sha256 = str(source_pdf.get("sha256") or material.input_sha256 or "")
            size = source_pdf.get("size_bytes")
            if isinstance(size, int):
                material.size_bytes = size
        material.promote_stage("popo_done")
        material.review_asset_id = asset.id
        link_review_asset(db, material)
        count += 1
    return {"popo": count}


def sync_downstream_stage(
    db: Session,
    user_id: str,
    bucket: str,
    prefix: str,
    stage: str,
    limit: int | None = None,
) -> dict[str, int]:
    count = 0
    for manifest_object in list_two_level_manifests(bucket, prefix, limit=limit):
        material_id, run_id = infer_ids_from_manifest_path(manifest_object)
        manifest = read_json_object(bucket, manifest_object)
        title = str(manifest.get("title") or manifest.get("filename") or material_id or Path(manifest_object).parent.name)
        material = upsert_material(db, user_id, title, title, material_id=material_id)
        if stage == "raw_done":
            material.raw_manifest_bucket = bucket
            material.raw_manifest_object = manifest_object
            material.raw_run_id = run_id
        elif stage == "clean_done":
            material.clean_manifest_bucket = bucket
            material.clean_manifest_object = manifest_object
            material.clean_run_id = run_id
        else:
            material.standard_manifest_bucket = bucket
            material.standard_manifest_object = manifest_object
            material.standard_run_id = run_id
            material.standard_quality_score = standard_quality_score_from_manifest(manifest)
        material.promote_stage(stage)
        link_review_asset(db, material)
        count += 1
    return {stage.replace("_done", ""): count}


def standard_quality_score_from_manifest(manifest: dict[str, Any]) -> int | None:
    score = manifest.get("quality_score")
    if isinstance(score, dict):
        score = score.get("score")
    if not isinstance(score, int):
        acceptance = manifest.get("acceptance") if isinstance(manifest.get("acceptance"), dict) else {}
        score = acceptance.get("quality_score")
        if isinstance(score, dict):
            score = score.get("score")
    if not isinstance(score, int):
        quality = manifest.get("quality") if isinstance(manifest.get("quality"), dict) else {}
        score = quality.get("score")
    if isinstance(score, int) and 0 <= score <= 100:
        return score
    return None


def sync_material_inventory(db: Session, user_id: str, limit: int | None = None) -> dict[str, Any]:
    summary: dict[str, int] = {}
    sync_steps = [
        lambda: sync_input_materials(db, user_id, limit),
        lambda: sync_mineru_materials(db, user_id, limit),
        lambda: sync_popo_materials(db, user_id, limit),
        lambda: sync_downstream_stage(db, user_id, RAW_BUCKET, "raw/", "raw_done", limit),
        lambda: sync_downstream_stage(db, user_id, CLEAN_BUCKET, "clean/", "clean_done", limit),
        lambda: sync_downstream_stage(db, user_id, STANDARD_BUCKET, "standard/", "standard_done", limit),
    ]
    for sync_step in sync_steps:
        partial = sync_step()
        summary.update(partial)
        db.flush()
    total = db.query(Material).filter(Material.user_id == user_id).count()
    stages = {
        stage: db.query(Material).filter(Material.user_id == user_id, Material.stage_status == stage).count()
        for stage in ["input", "mineru_done", "popo_done", "raw_done", "clean_stale", "clean_done", "standard_done", "failed"]
    }
    return {"total": total, "scanned": summary, "stages": stages, "availability": material_availability(db, user_id)}


async def upload_input_pdfs(files: list[UploadFile], user_id: str, db: Session) -> dict[str, Any]:
    results = []
    for file in files:
        filename = Path(file.filename or "untitled.pdf").name
        if not filename.lower().endswith(".pdf"):
            results.append({"filename": filename, "status": "failed", "error_message": "仅支持 PDF"})
            continue
        data = await file.read()
        sha256 = hashlib.sha256(data).hexdigest()
        material_id = material_id_from_sha256(sha256)
        object_name = filename
        if object_exists(INPUT_BUCKET, object_name):
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            object_name = f"{stem}-{sha256[:8]}{suffix}"
        minio_client.put_object(
            INPUT_BUCKET,
            object_name,
            BytesIO(data),
            length=len(data),
            content_type=file.content_type or "application/pdf",
        )
        material = upsert_material(
            db,
            user_id,
            filename,
            filename,
            material_id=material_id,
            input_ref=ObjectRef(INPUT_BUCKET, object_name),
            source_type="uploaded",
        )
        material.input_sha256 = sha256
        material.size_bytes = len(data)
        material.content_type = file.content_type or "application/pdf"
        material.promote_stage("input")
        asset = ensure_input_review_asset(db, user_id, INPUT_BUCKET, object_name)
        material.review_asset_id = asset.id if asset else material.review_asset_id
        db.flush()
        results.append({"filename": filename, "status": "success", "material": material.to_dict()})
    db.commit()
    return {
        "total": len(results),
        "success": sum(1 for item in results if item["status"] == "success"),
        "failed": sum(1 for item in results if item["status"] == "failed"),
        "files": results,
    }


def latest_pipeline_run(db: Session, user_id: str) -> PipelineRun | None:
    return (
        db.query(PipelineRun)
        .filter(PipelineRun.user_id == user_id)
        .order_by(PipelineRun.created_at.desc(), PipelineRun.id.desc())
        .first()
    )


def create_pipeline_event(db: Session, run: PipelineRun, message: str, stage: str = "", level: str = "info", payload: dict | None = None) -> None:
    db.add(
        PipelineEvent(
            run_id=run.id,
            user_id=run.user_id,
            level=level,
            stage=stage,
            message=message,
            payload_json=json.dumps(payload or {}, ensure_ascii=False),
        )
    )


def pipeline_limit(limit: int) -> int:
    return max(1, min(int(limit or 5), 5))


def pipeline_command(apply: bool, limit: int) -> list[str]:
    if apply:
        command = ["python3", PIPELINE_SCRIPT, "run-staged", "--limit", str(pipeline_limit(limit))]
        command.extend(["--skip-sha", "--input-status-only", "--apply", "--wait"])
    else:
        command = ["python3", PIPELINE_SCRIPT, "plan-next", "--limit", str(pipeline_limit(limit))]
        command.extend(["--skip-sha", "--input-status-only"])
    return command


def pipeline_preflight_command(limit: int) -> list[str]:
    command = ["python3", PIPELINE_SCRIPT, "preflight", "--limit", str(pipeline_limit(limit))]
    command.extend(["--skip-sha", "--input-status-only"])
    return command


def parse_pipeline_json(stdout: str) -> dict[str, Any]:
    try:
        parsed = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def run_pipeline_preflight(limit: int = 5) -> dict[str, Any]:
    command = pipeline_preflight_command(limit)
    completed = subprocess.run(
        command,
        cwd=PIPELINE_WORKDIR,
        env=pipeline_env(),
        text=True,
        capture_output=True,
        timeout=180,
    )
    payload = parse_pipeline_json(completed.stdout)
    payload.setdefault("ready", False)
    payload.setdefault("status", "ERROR" if completed.returncode else "UNKNOWN")
    payload.setdefault("checked_at", datetime.utcnow().isoformat())
    payload["returncode"] = completed.returncode
    payload["command_text"] = " ".join(command)
    if completed.returncode != 0:
        payload["ready"] = False
        payload["stdout_tail"] = (completed.stdout or "")[-4000:]
        payload["stderr_tail"] = (completed.stderr or "")[-4000:]
    return payload


def start_pipeline_run(db: Session, user_id: str, apply: bool = False, limit: int = 5) -> PipelineRun:
    active = (
        db.query(PipelineRun)
        .filter(PipelineRun.user_id == user_id, PipelineRun.status.in_(["queued", "running"]))
        .order_by(PipelineRun.created_at.desc())
        .first()
    )
    if active:
        return active
    preflight = run_pipeline_preflight(limit) if apply else None
    if apply and not bool(preflight and preflight.get("ready")):
        raise PipelinePreflightError(preflight or {})
    run = PipelineRun(
        user_id=user_id,
        status="queued",
        mode="apply" if apply else "dry_run",
        command=" ".join(pipeline_command(apply=apply, limit=limit)),
        current_stage="queued",
        total=int(preflight.get("selected_count") or 0) if preflight else 0,
        summary_json=json.dumps({"preflight": preflight}, ensure_ascii=False) if preflight else None,
        created_at=datetime.utcnow(),
    )
    db.add(run)
    db.flush()
    create_pipeline_event(
        db,
        run,
        "已创建解析任务，等待后台执行" if apply else "已创建解析预检任务，默认不提交 GPU",
        stage="queued",
        payload={"preflight": preflight} if preflight else None,
    )
    db.commit()
    threading.Thread(target=run_pipeline_subprocess, args=(run.id, apply, limit), daemon=True).start()
    return run


def run_pipeline_subprocess(run_id: int, apply: bool, limit: int) -> None:
    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        if not run:
            return
        run.status = "running"
        run.started_at = datetime.utcnow()
        run.current_stage = "pipeline_command"
        create_pipeline_event(db, run, "开始执行现有 Luceon first-stage 调度脚本", stage="pipeline_command")
        db.commit()

        command = pipeline_command(apply=apply, limit=limit)
        completed = subprocess.run(
            command,
            cwd=PIPELINE_WORKDIR,
            env=pipeline_env(),
            text=True,
            capture_output=True,
            timeout=None if apply else 180,
        )
        output = (completed.stdout or "")[-8000:]
        error = (completed.stderr or "")[-4000:]
        run.finished_at = datetime.utcnow()
        run.summary_json = json.dumps({"returncode": completed.returncode, "stdout_tail": output, "stderr_tail": error}, ensure_ascii=False)
        if completed.returncode == 0:
            run.status = "succeeded"
            run.current_stage = "finished"
            create_pipeline_event(db, run, "解析任务执行完成", stage="finished", payload={"returncode": completed.returncode})
            sync_material_inventory(db, run.user_id)
        else:
            run.status = "failed"
            run.current_stage = "failed"
            run.error_message = error or output or f"pipeline exited with {completed.returncode}"
            create_pipeline_event(db, run, "解析任务执行失败", stage="failed", level="error", payload={"returncode": completed.returncode})
        db.commit()
    except Exception as exc:
        run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        if run:
            run.status = "failed"
            run.current_stage = "failed"
            run.finished_at = datetime.utcnow()
            run.error_message = str(exc)
            create_pipeline_event(db, run, "解析任务异常退出", stage="failed", level="error", payload={"error": str(exc)})
            db.commit()
    finally:
        db.close()


def material_summary(db: Session, user_id: str) -> dict[str, Any]:
    total = db.query(Material).filter(Material.user_id == user_id).count()
    stages = {
        stage: db.query(Material).filter(Material.user_id == user_id, Material.stage_status == stage).count()
        for stage in ["input", "mineru_done", "popo_done", "raw_done", "clean_stale", "clean_done", "standard_done", "failed"]
    }
    latest = latest_pipeline_run(db, user_id)
    return {
        "total": total,
        "stages": stages,
        "availability": material_availability(db, user_id),
        "latest_run": latest.to_dict() if latest else None,
    }


def material_availability(db: Session, user_id: str) -> dict[str, int]:
    rows = db.query(Material).filter(Material.user_id == user_id, Material.ignored.is_(False)).all()
    return {
        "input": sum(1 for row in rows if row.input_object),
        "mineru_done": sum(1 for row in rows if row.mineru_manifest_object or row.popo_manifest_object),
        "popo_done": sum(1 for row in rows if row.popo_manifest_object),
        "raw_done": sum(1 for row in rows if row.raw_manifest_object),
        "clean_done": sum(1 for row in rows if row.clean_manifest_object),
        "standard_done": sum(1 for row in rows if row.standard_manifest_object),
    }
