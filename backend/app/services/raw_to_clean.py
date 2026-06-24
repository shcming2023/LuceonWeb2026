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
from app.services.material_inventory import CLEAN_BUCKET, RAW_BUCKET, create_pipeline_event, sync_material_inventory
from app.services.runtime_settings import pipeline_env


SKILL_ROOT = Path(os.getenv("LUCEON_RAW_CLEAN_SKILL", "/skills/eduassets-raw-cleaner"))
CLEAN_SCRIPT = SKILL_ROOT / "scripts" / "clean_raw_sample.py"
WORK_ROOT = Path(os.getenv("LUCEON_PIPELINE_WORK_ROOT", "/data/pipeline-work"))


class RawToCleanPreflightError(RuntimeError):
    def __init__(self, preflight: dict[str, Any]):
        super().__init__("Raw→Clean 预检未通过")
        self.preflight = preflight


def raw_to_clean_preflight(material: Material, force: bool = False) -> dict[str, Any]:
    material_id = material.material_id or ""
    raw_run_id = resolve_raw_run_id(material)
    raw_prefix = resolve_raw_prefix(material, material_id, raw_run_id)
    clean_prefix = f"clean/{material_id}/{raw_run_id}/" if material_id and raw_run_id else ""
    checks = {
        "has_material_id": bool(material_id),
        "has_raw_manifest": bool(material.raw_manifest_bucket and material.raw_manifest_object),
        "has_raw_run_id": bool(raw_run_id),
        "skill_available": CLEAN_SCRIPT.exists(),
        "raw_exists": bool(raw_prefix and prefix_exists(RAW_BUCKET, raw_prefix)),
        "clean_exists": bool(clean_prefix and prefix_exists(CLEAN_BUCKET, clean_prefix)),
        "deepseek_available": bool(os.getenv("DEEPSEEK_API_KEY", "").strip()),
    }
    blockers = []
    if not checks["has_material_id"]:
        blockers.append("missing_material_id")
    if not checks["has_raw_manifest"] or not checks["has_raw_run_id"] or not checks["raw_exists"]:
        blockers.append("missing_raw_asset")
    if not checks["skill_available"]:
        blockers.append("missing_skill_script")
    if checks["clean_exists"] and not force:
        blockers.append("clean_already_exists")
    return {
        "ready": not blockers,
        "stage": "raw2clean",
        "material_pk": str(material.id),
        "material_id": material_id,
        "filename": material.filename,
        "raw_run_id": raw_run_id,
        "raw_bucket": RAW_BUCKET,
        "raw_prefix": raw_prefix,
        "clean_bucket": CLEAN_BUCKET,
        "clean_prefix": clean_prefix,
        "llm_mode": "auto",
        "checks": checks,
        "blockers": blockers,
        "checked_at": datetime.utcnow().isoformat(),
    }


def start_raw_to_clean_run(db: Session, user_id: str, material: Material, publish: bool = True, force: bool = False) -> PipelineRun:
    active = (
        db.query(PipelineRun)
        .filter(PipelineRun.user_id == user_id, PipelineRun.status.in_(["queued", "running"]))
        .order_by(PipelineRun.created_at.desc())
        .first()
    )
    if active:
        return active

    preflight = raw_to_clean_preflight(material, force=force)
    if not preflight["ready"]:
        raise RawToCleanPreflightError(preflight)
    if not publish:
        raise RawToCleanPreflightError({**preflight, "blockers": ["publish_not_confirmed"]})

    command = f"raw2clean material_id={preflight['material_id']} raw_run_id={preflight['raw_run_id']}"
    run = PipelineRun(
        user_id=user_id,
        status="queued",
        mode="raw2clean",
        command=command,
        current_stage="queued",
        total=1,
        summary_json=json.dumps({"preflight": preflight}, ensure_ascii=False),
        created_at=datetime.utcnow(),
    )
    material.pipeline_status = "queued"
    db.add(run)
    db.flush()
    create_pipeline_event(db, run, "已创建 Raw→Clean 单材料任务", stage="queued", payload={"preflight": preflight})
    db.commit()
    threading.Thread(target=run_raw_to_clean_subprocess, args=(run.id, int(material.id), force), daemon=True).start()
    return run


def run_raw_to_clean_subprocess(run_id: int, material_pk: int, force: bool) -> None:
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
        create_pipeline_event(db, run, "开始物化 Raw 资产", stage="materialize")
        db.commit()

        result = execute_raw_to_clean(material, run_id=run_id, force=force, event_callback=lambda stage, message, payload=None: add_event(db, run, stage, message, payload))

        run.status = "succeeded"
        run.current_stage = "finished"
        run.processed = 1
        run.success = 1
        run.finished_at = datetime.utcnow()
        run.summary_json = json.dumps(result, ensure_ascii=False)
        material.pipeline_status = "idle"
        create_pipeline_event(db, run, "Raw→Clean 已发布到 eduassets-clean", stage="finished", payload=result)
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
            create_pipeline_event(db, run, "Raw→Clean 任务失败", stage="failed", level="error", payload={"error": str(exc)})
        if material:
            material.pipeline_status = "failed"
        db.commit()
    finally:
        db.close()


def add_event(db: Session, run: PipelineRun, stage: str, message: str, payload: dict[str, Any] | None = None) -> None:
    run.current_stage = stage
    create_pipeline_event(db, run, message, stage=stage, payload=payload)
    db.commit()


def execute_raw_to_clean(material: Material, run_id: int, force: bool, event_callback) -> dict[str, Any]:
    preflight = raw_to_clean_preflight(material, force=force)
    if not preflight["ready"]:
        raise RawToCleanPreflightError(preflight)

    material_id = preflight["material_id"]
    raw_run_id = preflight["raw_run_id"]
    raw_prefix = preflight["raw_prefix"]
    clean_prefix = preflight["clean_prefix"]
    work_dir = WORK_ROOT / "raw2clean" / f"run-{run_id}-{material_id}-{raw_run_id}"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    raw_input = work_dir / "raw_input"
    clean_final = work_dir / "clean-final"
    raw_input.mkdir(parents=True, exist_ok=True)

    download_prefix(RAW_BUCKET, raw_prefix, raw_input)
    event_callback("materialize", "Raw 资产已下载到本地工作目录", {"work_dir": str(work_dir), "raw_prefix": raw_prefix})

    event_callback("clean", "开始调用 eduassets-raw-cleaner 的 clean_raw_sample.py")
    completed = subprocess.run(
        [
            "python3",
            str(CLEAN_SCRIPT),
            "--raw-input-dir",
            str(raw_input),
            "--raw-prefix",
            raw_prefix.rstrip("/"),
            "--out-dir",
            str(clean_final),
            "--llm",
            "auto",
            "--media-policy",
            "review",
        ],
        cwd=str(SKILL_ROOT),
        env=pipeline_env(),
        text=True,
        capture_output=True,
        timeout=None,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or f"clean_raw_sample exited {completed.returncode}")[-4000:])
    event_callback("clean", "Clean 候选已生成", {"stdout_tail": (completed.stdout or "")[-2000:]})

    enrich_clean_manifest(clean_final, material, raw_prefix, clean_prefix, raw_run_id)
    ensure_clean_deliverables(clean_final)
    publish_directory_to_minio(clean_final, CLEAN_BUCKET, clean_prefix)
    event_callback("publish", "Clean 产物已写入 eduassets-clean", {"clean_bucket": CLEAN_BUCKET, "clean_prefix": clean_prefix})
    return {
        "stage": "raw2clean",
        "material_id": material_id,
        "filename": material.filename,
        "raw_run_id": raw_run_id,
        "raw_bucket": RAW_BUCKET,
        "raw_prefix": raw_prefix,
        "clean_bucket": CLEAN_BUCKET,
        "clean_prefix": clean_prefix,
        "clean_manifest": f"{clean_prefix}manifest.json",
        "work_dir": str(work_dir),
        "published": True,
    }


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


def infer_ids_from_manifest_path(manifest_object: str) -> tuple[str, str]:
    parts = clean_path(manifest_object).split("/")
    if len(parts) >= 4 and parts[-1] == "manifest.json":
        return parts[-3], parts[-2]
    return "", ""


def prefix_exists(bucket: str, prefix: str) -> bool:
    try:
        next(minio_client.list_objects(bucket, prefix=clean_path(prefix).rstrip("/") + "/", recursive=True))
        return True
    except StopIteration:
        return False
    except Exception:
        return False


def download_prefix(bucket: str, prefix: str, dest: Path) -> None:
    normalized = clean_path(prefix).rstrip("/") + "/"
    found = False
    for item in minio_client.list_objects(bucket, prefix=normalized, recursive=True):
        object_name = clean_path(getattr(item, "object_name", ""))
        if not object_name or object_name.endswith("/"):
            continue
        relative = object_name[len(normalized):].lstrip("/")
        if not relative:
            continue
        found = True
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        response = minio_client.get_object(bucket, object_name)
        try:
            with target.open("wb") as fh:
                shutil.copyfileobj(response, fh)
        finally:
            close = getattr(response, "close", None)
            if close:
                close()
            release_conn = getattr(response, "release_conn", None)
            if release_conn:
                release_conn()
    if not found:
        raise RuntimeError(f"MinIO prefix is empty: {bucket}/{normalized}")


def enrich_clean_manifest(clean_final: Path, material: Material, raw_prefix: str, clean_prefix: str, raw_run_id: str) -> None:
    manifest_path = clean_final / "manifest.json"
    manifest = read_local_json(manifest_path)
    objects = manifest.get("objects") if isinstance(manifest.get("objects"), dict) else {}
    for name in [
        "clean.md",
        "clean.html",
        "raw.html",
        "review.html",
        "clean.pdf",
        "quality_report.md",
        "manifest.json",
        "source_map.json",
        "llm_usage.json",
        "media_report.json",
        "fidelity_report.json",
        "review_items.json",
        "render_report.json",
        "structure_report.json",
        "readability_report.json",
        "loss_audit.json",
        "acceptance_report.json",
    ]:
        if (clean_final / name).exists():
            key = name.replace(".", "_").replace("-", "_")
            objects[key] = {"bucket": CLEAN_BUCKET, "object": f"{clean_prefix}{name}"}
    manifest.update(
        {
            "schema": "luceon-eduassets-clean/v1",
            "material_id": material.material_id,
            "run_id": raw_run_id,
            "title": material.title,
            "filename": material.filename,
            "review_stage": "clean",
            "source_pdf": {
                "input_bucket": material.input_bucket,
                "input_object": material.input_object,
                "filename": material.filename,
                "sha256": material.input_sha256,
                "size_bytes": material.size_bytes,
            },
            "upstream": {
                "raw": {"bucket": RAW_BUCKET, "run_id": raw_run_id, "manifest": material.raw_manifest_object},
            },
            "stage_prefixes": {
                "clean": {"bucket": CLEAN_BUCKET, "prefix": clean_prefix, "official_prefix": clean_prefix},
                "raw": {"bucket": RAW_BUCKET, "prefix": raw_prefix, "official_prefix": raw_prefix},
            },
            "objects": objects,
        }
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_local_json(path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def ensure_clean_deliverables(local_dir: Path) -> None:
    missing = [
        name
        for name in [
            "clean.md",
            "clean.html",
            "raw.html",
            "review.html",
            "manifest.json",
            "quality_report.md",
            "source_map.json",
            "llm_usage.json",
            "media_report.json",
            "fidelity_report.json",
            "review_items.json",
            "structure_report.json",
            "readability_report.json",
            "loss_audit.json",
            "acceptance_report.json",
        ]
        if not (local_dir / name).exists()
    ]
    if missing:
        raise RuntimeError(f"Missing required clean deliverables: {', '.join(missing)}")
    acceptance = read_local_json(local_dir / "acceptance_report.json")
    if acceptance.get("status") == "fail" or int(acceptance.get("hard_failure_count") or 0) > 0:
        failures = acceptance.get("hard_failures") or []
        raise RuntimeError(f"Clean acceptance failed: {json.dumps(failures[:5], ensure_ascii=False)}")


def publish_directory_to_minio(local_dir: Path, bucket: str, prefix: str) -> None:
    if bucket != CLEAN_BUCKET:
        raise RuntimeError(f"Unsafe clean target bucket: {bucket}")
    normalized = clean_path(prefix).rstrip("/") + "/"
    if not normalized.startswith("clean/"):
        raise RuntimeError(f"Unsafe clean target prefix: {normalized}")
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


def list_object_names(bucket: str, prefix: str) -> list[str]:
    normalized = clean_path(prefix).rstrip("/") + "/"
    names = []
    for item in minio_client.list_objects(bucket, prefix=normalized, recursive=True):
        object_name = clean_path(getattr(item, "object_name", ""))
        if object_name and not object_name.endswith("/"):
            names.append(object_name)
    return names
