import json
import mimetypes
import os
import re
import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.material import Material, PipelineRun
from app.services.luceon_review import clean_path, minio_client
from app.services.material_inventory import CLEAN_BUCKET, INPUT_BUCKET, RAW_BUCKET, STANDARD_BUCKET, create_pipeline_event, sync_material_inventory
from app.services.raw_to_clean import download_prefix, infer_ids_from_manifest_path, list_object_names, prefix_exists, read_local_json
from app.services.runtime_settings import pipeline_env


STANDARD_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "standard_from_clean.py"
WORK_ROOT = Path(os.getenv("LUCEON_PIPELINE_WORK_ROOT", "/data/pipeline-work"))


class CleanToStandardPreflightError(RuntimeError):
    def __init__(self, preflight: dict[str, Any]):
        super().__init__("Clean→Standard 预检未通过")
        self.preflight = preflight


def clean_to_standard_preflight(material: Material, force: bool = False) -> dict[str, Any]:
    material_id = material.material_id or ""
    clean_run_id = resolve_clean_run_id(material)
    clean_prefix = resolve_clean_prefix(material, material_id, clean_run_id)
    raw_run_id = resolve_raw_run_id(material)
    raw_prefix = resolve_raw_prefix(material, material_id, raw_run_id)
    standard_prefix = f"standard/{material_id}/{clean_run_id}/" if material_id and clean_run_id else ""
    checks = {
        "has_material_id": bool(material_id),
        "has_clean_manifest": bool(material.clean_manifest_bucket and material.clean_manifest_object),
        "has_clean_run_id": bool(clean_run_id),
        "script_available": STANDARD_SCRIPT.exists(),
        "clean_exists": bool(clean_prefix and prefix_exists(CLEAN_BUCKET, clean_prefix)),
        "raw_exists": bool(raw_prefix and prefix_exists(RAW_BUCKET, raw_prefix)),
        "standard_exists": bool(standard_prefix and prefix_exists(STANDARD_BUCKET, standard_prefix)),
    }
    blockers = []
    if not checks["has_material_id"]:
        blockers.append("missing_material_id")
    if not checks["has_clean_manifest"] or not checks["has_clean_run_id"] or not checks["clean_exists"]:
        blockers.append("missing_clean_asset")
    if not checks["script_available"]:
        blockers.append("missing_standard_script")
    if checks["standard_exists"] and not force:
        blockers.append("standard_already_exists")
    return {
        "ready": not blockers,
        "stage": "clean2standard",
        "material_pk": str(material.id),
        "material_id": material_id,
        "filename": material.filename,
        "clean_run_id": clean_run_id,
        "clean_bucket": CLEAN_BUCKET,
        "clean_prefix": clean_prefix,
        "raw_bucket": RAW_BUCKET,
        "raw_prefix": raw_prefix,
        "standard_bucket": STANDARD_BUCKET,
        "standard_prefix": standard_prefix,
        "checks": checks,
        "blockers": blockers,
        "checked_at": datetime.utcnow().isoformat(),
    }


def start_clean_to_standard_run(db: Session, user_id: str, material: Material, publish: bool = True, force: bool = False) -> PipelineRun:
    active = (
        db.query(PipelineRun)
        .filter(PipelineRun.user_id == user_id, PipelineRun.status.in_(["queued", "running"]))
        .order_by(PipelineRun.created_at.desc())
        .first()
    )
    if active:
        return active

    preflight = clean_to_standard_preflight(material, force=force)
    if not preflight["ready"]:
        raise CleanToStandardPreflightError(preflight)
    if not publish:
        raise CleanToStandardPreflightError({**preflight, "blockers": ["publish_not_confirmed"]})

    command = f"clean2standard material_id={preflight['material_id']} clean_run_id={preflight['clean_run_id']}"
    run = PipelineRun(
        user_id=user_id,
        status="queued",
        mode="clean2standard",
        command=command,
        current_stage="queued",
        total=1,
        summary_json=json.dumps({"preflight": preflight}, ensure_ascii=False),
        created_at=datetime.utcnow(),
    )
    material.pipeline_status = "queued"
    db.add(run)
    db.flush()
    create_pipeline_event(db, run, "已创建 Clean→Standard 单材料任务", stage="queued", payload={"preflight": preflight})
    db.commit()
    threading.Thread(target=run_clean_to_standard_subprocess, args=(run.id, int(material.id), force), daemon=True).start()
    return run


def run_clean_to_standard_subprocess(run_id: int, material_pk: int, force: bool) -> None:
    db = SessionLocal()
    try:
        run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        material = db.query(Material).filter(Material.id == material_pk).first()
        if not run or not material:
            return
        run.status = "running"
        run.started_at = datetime.utcnow()
        run.current_stage = "materialize"
        material.pipeline_status = "running"
        create_pipeline_event(db, run, "开始物化 Clean/Raw 资产", stage="materialize")
        db.commit()

        result = execute_clean_to_standard(material, run_id=run_id, force=force, event_callback=lambda stage, message, payload=None: add_event(db, run, stage, message, payload))

        run.status = "succeeded"
        run.current_stage = "finished"
        run.processed = 1
        run.success = 1
        run.finished_at = datetime.utcnow()
        run.summary_json = json.dumps(result, ensure_ascii=False)
        material.pipeline_status = "idle"
        create_pipeline_event(db, run, "Clean→Standard 已发布到 eduassets-standard", stage="finished", payload=result)
        sync_material_inventory(db, run.user_id)
        db.commit()
    except Exception as exc:
        run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        material = db.query(Material).filter(Material.id == material_pk).first()
        if run:
            run.status = "failed"
            run.current_stage = "failed"
            run.failed = 1
            run.finished_at = datetime.utcnow()
            run.error_message = str(exc)
            create_pipeline_event(db, run, "Clean→Standard 任务失败", stage="failed", level="error", payload={"error": str(exc)})
        if material:
            material.pipeline_status = "failed"
        db.commit()
    finally:
        db.close()


def add_event(db: Session, run: PipelineRun, stage: str, message: str, payload: dict[str, Any] | None = None) -> None:
    run.current_stage = stage
    create_pipeline_event(db, run, message, stage=stage, payload=payload)
    db.commit()


def download_source_pdf(material: Material, dest: Path) -> Path | None:
    object_name = clean_path(material.input_object or "")
    if not object_name:
        return None
    bucket = material.input_bucket or INPUT_BUCKET
    dest.parent.mkdir(parents=True, exist_ok=True)
    response = minio_client.get_object(bucket, object_name)
    try:
        with dest.open("wb") as fh:
            shutil.copyfileobj(response, fh)
    finally:
        close = getattr(response, "close", None)
        if close:
            close()
        release_conn = getattr(response, "release_conn", None)
        if release_conn:
            release_conn()
    return dest


def execute_clean_to_standard(material: Material, run_id: int, force: bool, event_callback) -> dict[str, Any]:
    preflight = clean_to_standard_preflight(material, force=force)
    if not preflight["ready"]:
        raise CleanToStandardPreflightError(preflight)

    material_id = preflight["material_id"]
    clean_run_id = preflight["clean_run_id"]
    clean_prefix = preflight["clean_prefix"]
    raw_prefix = preflight["raw_prefix"]
    standard_prefix = preflight["standard_prefix"]
    safe_run_id = re.sub(r"[^A-Za-z0-9._-]+", "_", f"{material_id}-{clean_run_id}".strip("-")) or "standard"
    work_dir = WORK_ROOT / "clean2standard" / f"run-{run_id}-{safe_run_id}"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    clean_input = work_dir / "clean_input"
    raw_input = work_dir / "raw_input"
    source_pdf_input = work_dir / "source_input" / "source.pdf"
    standard_final = work_dir / "standard-final"
    clean_input.mkdir(parents=True, exist_ok=True)

    download_prefix(CLEAN_BUCKET, clean_prefix, clean_input)
    if raw_prefix and prefix_exists(RAW_BUCKET, raw_prefix):
        raw_input.mkdir(parents=True, exist_ok=True)
        download_prefix(RAW_BUCKET, raw_prefix, raw_input)
    source_pdf_error = ""
    try:
        downloaded_source_pdf = download_source_pdf(material, source_pdf_input)
    except Exception as exc:
        downloaded_source_pdf = None
        source_pdf_error = str(exc)
    event_callback(
        "materialize",
        "Clean/Raw/Source 资产已下载到本地工作目录",
        {
            "work_dir": str(work_dir),
            "clean_prefix": clean_prefix,
            "raw_prefix": raw_prefix,
            "source_pdf": str(downloaded_source_pdf) if downloaded_source_pdf else "",
            "source_pdf_error": source_pdf_error,
        },
    )

    command = [
        "python3",
        str(STANDARD_SCRIPT),
        "--clean-dir",
        str(clean_input),
        "--out-dir",
        str(standard_final),
        "--force",
    ]
    if raw_input.exists():
        command.extend(["--raw-dir", str(raw_input)])
    if downloaded_source_pdf:
        command.extend(["--source-pdf", str(downloaded_source_pdf)])
    event_callback("standard", "开始调用 standard_from_clean.py", {"command": command})
    completed = subprocess.run(command, env=pipeline_env(), text=True, capture_output=True, timeout=None)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or f"standard_from_clean exited {completed.returncode}")[-4000:])
    event_callback("standard", "Standard 候选已生成", {"stdout_tail": (completed.stdout or "")[-2000:]})

    enrich_standard_manifest(standard_final, material, clean_prefix, raw_prefix, standard_prefix, clean_run_id)
    ensure_standard_deliverables(standard_final)
    publish_directory_to_minio(standard_final, STANDARD_BUCKET, standard_prefix)
    event_callback("publish", "Standard 产物已写入 eduassets-standard", {"standard_bucket": STANDARD_BUCKET, "standard_prefix": standard_prefix})
    return {
        "stage": "clean2standard",
        "material_id": material_id,
        "filename": material.filename,
        "clean_run_id": clean_run_id,
        "clean_bucket": CLEAN_BUCKET,
        "clean_prefix": clean_prefix,
        "raw_bucket": RAW_BUCKET,
        "raw_prefix": raw_prefix,
        "standard_bucket": STANDARD_BUCKET,
        "standard_prefix": standard_prefix,
        "standard_manifest": f"{standard_prefix}manifest.json",
        "work_dir": str(work_dir),
        "published": True,
    }


def resolve_clean_run_id(material: Material) -> str:
    if material.clean_run_id:
        return material.clean_run_id
    material_id, run_id = infer_ids_from_manifest_path(material.clean_manifest_object or "")
    if material_id and (not material.material_id or material_id == material.material_id):
        return run_id
    return ""


def resolve_clean_prefix(material: Material, material_id: str, clean_run_id: str) -> str:
    object_name = clean_path(material.clean_manifest_object or "")
    if object_name.endswith("/manifest.json"):
        return object_name.rsplit("/", 1)[0] + "/"
    if material_id and clean_run_id:
        return f"clean/{material_id}/{clean_run_id}/"
    return ""


def resolve_raw_run_id(material: Material) -> str:
    if material.raw_run_id:
        return material.raw_run_id
    material_id, run_id = infer_ids_from_manifest_path(material.raw_manifest_object or "")
    if material_id and (not material.material_id or material_id == material.material_id):
        return run_id
    return ""


def resolve_raw_prefix(material: Material, material_id: str, raw_run_id: str) -> str:
    object_name = clean_path(material.raw_manifest_object or "")
    if object_name.endswith("/manifest.json"):
        return object_name.rsplit("/", 1)[0] + "/"
    if material_id and raw_run_id:
        return f"raw/{material_id}/{raw_run_id}/"
    return ""


def enrich_standard_manifest(standard_final: Path, material: Material, clean_prefix: str, raw_prefix: str, standard_prefix: str, clean_run_id: str) -> None:
    manifest_path = standard_final / "manifest.json"
    manifest = read_local_json(manifest_path)
    objects = manifest.get("objects") if isinstance(manifest.get("objects"), dict) else {}
    for name in [
        "standard.md",
        "standard.html",
        "standard.pdf",
        "review.html",
        "manifest.json",
        "standard_document.json",
        "standard_issue_candidates.json",
        "standard_visual_review_packets.json",
        "standard_review_outcomes.json",
        "review_outcomes.html",
        "visual_outcome_review.json",
        "visual_outcome_review.html",
        "correction_log.json",
        "layout_report.json",
        "image_relation_report.json",
        "workbook_relation_audit.json",
        "workbook_relation_audit.html",
        "image_visual_confirmation_packets.json",
        "image_visual_confirmation.html",
        "workbook_profile_report.json",
        "workbook_profile.html",
        "print_qa_report.json",
        "standard_acceptance_report.json",
        "standard_quality_score.json",
        "standard_product_status.json",
    ]:
        if (standard_final / name).exists():
            key = name.replace(".", "_").replace("-", "_")
            objects[key] = {"bucket": STANDARD_BUCKET, "object": f"{standard_prefix}{name}"}
    manifest.update(
        {
            "schema": "luceon-eduassets-standard/v1",
            "material_id": material.material_id,
            "run_id": clean_run_id,
            "title": material.title,
            "filename": material.filename,
            "review_stage": "standard",
            "source_pdf": {
                "input_bucket": material.input_bucket,
                "input_object": material.input_object,
                "filename": material.filename,
                "sha256": material.input_sha256,
                "size_bytes": material.size_bytes,
            },
            "upstream": {
                "clean": {"bucket": CLEAN_BUCKET, "run_id": clean_run_id, "manifest": material.clean_manifest_object},
                "raw": {"bucket": RAW_BUCKET, "run_id": material.raw_run_id, "manifest": material.raw_manifest_object},
            },
            "stage_prefixes": {
                "standard": {"bucket": STANDARD_BUCKET, "prefix": standard_prefix, "official_prefix": standard_prefix},
                "clean": {"bucket": CLEAN_BUCKET, "prefix": clean_prefix, "official_prefix": clean_prefix},
                "raw": {"bucket": RAW_BUCKET, "prefix": raw_prefix, "official_prefix": raw_prefix},
            },
            "objects": objects,
        }
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_standard_deliverables(local_dir: Path) -> None:
    missing = [
        name
        for name in [
            "standard.md",
            "standard.html",
            "standard.pdf",
            "review.html",
            "manifest.json",
            "standard_document.json",
            "standard_issue_candidates.json",
            "standard_visual_review_packets.json",
            "standard_review_outcomes.json",
            "review_outcomes.html",
            "visual_outcome_review.json",
            "visual_outcome_review.html",
            "correction_log.json",
            "layout_report.json",
            "image_relation_report.json",
            "workbook_relation_audit.json",
            "workbook_relation_audit.html",
            "image_visual_confirmation_packets.json",
            "image_visual_confirmation.html",
            "workbook_profile_report.json",
            "workbook_profile.html",
            "print_qa_report.json",
            "standard_acceptance_report.json",
            "standard_quality_score.json",
            "standard_product_status.json",
        ]
        if not (local_dir / name).exists()
    ]
    if missing:
        raise RuntimeError(f"Missing required standard deliverables: {', '.join(missing)}")
    acceptance = read_local_json(local_dir / "standard_acceptance_report.json")
    if acceptance.get("status") == "fail":
        raise RuntimeError("Standard acceptance failed")


def publish_directory_to_minio(local_dir: Path, bucket: str, prefix: str) -> None:
    if bucket != STANDARD_BUCKET:
        raise RuntimeError(f"Unsafe standard target bucket: {bucket}")
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)
    normalized = clean_path(prefix).rstrip("/") + "/"
    if not normalized.startswith("standard/"):
        raise RuntimeError(f"Unsafe standard target prefix: {normalized}")
    published: set[str] = set()
    for path in sorted(local_dir.rglob("*")):
        if not path.is_file():
            continue
        object_name = f"{normalized}{path.relative_to(local_dir).as_posix()}"
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with path.open("rb") as fh:
            minio_client.put_object(bucket, object_name, fh, length=path.stat().st_size, content_type=content_type)
        published.add(object_name)
    for object_name in list_object_names(bucket, normalized):
        if object_name not in published:
            minio_client.remove_object(bucket, object_name)
