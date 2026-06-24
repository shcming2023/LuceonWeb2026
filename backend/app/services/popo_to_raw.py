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
from app.services.luceon_review import clean_path, minio_client, parse_json_bytes, read_object
from app.services.material_inventory import (
    CLEAN_BUCKET,
    INPUT_BUCKET,
    MINERU_BUCKET,
    POPO_BUCKET,
    RAW_BUCKET,
    create_pipeline_event,
    sync_material_inventory,
)
from app.services.runtime_settings import pipeline_env


SKILL_ROOT = Path(os.getenv("LUCEON_POPO_RAW_SKILL", "/skills/pdf-clean-markdown-rebuild"))
BOOTSTRAP_SCRIPT = SKILL_ROOT / "scripts" / "bootstrap_clean_markdown.py"
WORK_ROOT = Path(os.getenv("LUCEON_PIPELINE_WORK_ROOT", "/data/pipeline-work"))


class PopoToRawPreflightError(RuntimeError):
    def __init__(self, preflight: dict[str, Any]):
        super().__init__("Popo→Raw 预检未通过")
        self.preflight = preflight


class PopoToRawPublishError(RuntimeError):
    pass


def popo_to_raw_preflight(material: Material, force: bool = False, publish: bool = False) -> dict[str, Any]:
    run_env = pipeline_env()
    llm_required = run_env.get("LUCEON_RAW_OUTLINE_LLM", "1").lower() in {"1", "true", "yes", "on"}
    vision_required = run_env.get("LUCEON_RAW_OUTLINE_VISION", "").lower() in {"1", "true", "yes", "on"}
    material_id = material.material_id or ""
    popo_run_id = material.popo_run_id or ""
    mineru_run_id = resolve_mineru_run_id(material)
    raw_prefix = f"raw/{material_id}/{popo_run_id}/" if material_id and popo_run_id else ""
    checks = {
        "has_material_id": bool(material_id),
        "has_popo_manifest": bool(material.popo_manifest_bucket and material.popo_manifest_object),
        "has_popo_run_id": bool(popo_run_id),
        "has_mineru_run_id": bool(mineru_run_id),
        "skill_available": BOOTSTRAP_SCRIPT.exists(),
        "raw_exists": bool(raw_prefix and prefix_exists(RAW_BUCKET, raw_prefix)),
        "llm_required": llm_required,
        "deepseek_available": bool(run_env.get("DEEPSEEK_API_KEY", "").strip()),
        "vision_required": vision_required,
        "dashscope_vision_available": bool(run_env.get("DASHSCOPE_API_KEY", "").strip()),
        "hy_vision_available": bool(run_env.get("HY_VISION_API_KEY", "").strip() or run_env.get("TENCENTMAAS_API_KEY", "").strip()),
        "vision_model": run_env.get("VISION_MODEL") or run_env.get("DASHSCOPE_VISION_MODEL") or run_env.get("HY_VISION_MODEL") or "",
    }
    blockers = []
    if not checks["has_material_id"]:
        blockers.append("missing_material_id")
    if not checks["has_popo_manifest"] or not checks["has_popo_run_id"]:
        blockers.append("missing_popo_asset")
    if not checks["has_mineru_run_id"]:
        blockers.append("missing_mineru_asset")
    if not checks["skill_available"]:
        blockers.append("missing_skill_script")
    if publish and checks["raw_exists"] and not force:
        blockers.append("raw_already_exists")
    if checks["llm_required"] and not checks["deepseek_available"]:
        blockers.append("missing_deepseek_api_key")
    if checks["vision_required"] and not (checks["dashscope_vision_available"] or checks["hy_vision_available"]):
        blockers.append("missing_vision_api_key")
    return {
        "ready": not blockers,
        "stage": "popo2raw",
        "material_pk": str(material.id),
        "material_id": material_id,
        "filename": material.filename,
        "popo_run_id": popo_run_id,
        "mineru_run_id": mineru_run_id,
        "raw_bucket": RAW_BUCKET,
        "raw_prefix": raw_prefix,
        "publish": publish,
        "checks": checks,
        "blockers": blockers,
        "checked_at": datetime.utcnow().isoformat(),
    }


def start_popo_to_raw_run(db: Session, user_id: str, material: Material, publish: bool = False, force: bool = False) -> PipelineRun:
    active = (
        db.query(PipelineRun)
        .filter(PipelineRun.user_id == user_id, PipelineRun.status.in_(["queued", "running"]))
        .order_by(PipelineRun.created_at.desc())
        .first()
    )
    if active:
        if mark_stale_popo_to_raw_run(db, active):
            db.commit()
        else:
            return active

    preflight = popo_to_raw_preflight(material, force=force, publish=publish)
    if not preflight["ready"]:
        raise PopoToRawPreflightError(preflight)

    command = f"popo2raw material_id={preflight['material_id']} popo_run_id={preflight['popo_run_id']} publish={publish}"
    run = PipelineRun(
        user_id=user_id,
        status="queued",
        mode="popo2raw",
        command=command,
        current_stage="queued",
        total=1,
        summary_json=json.dumps({"preflight": preflight}, ensure_ascii=False),
        created_at=datetime.utcnow(),
    )
    material.pipeline_status = "queued"
    db.add(run)
    db.flush()
    create_pipeline_event(db, run, "已创建 Popo→Raw 单材料任务", stage="queued", payload={"preflight": preflight})
    db.commit()
    threading.Thread(target=run_popo_to_raw_subprocess, args=(run.id, int(material.id), publish, force), daemon=True).start()
    return run


def publish_popo_to_raw_dry_run(db: Session, user_id: str, material: Material, dry_run_id: int, force: bool = True) -> PipelineRun:
    active = (
        db.query(PipelineRun)
        .filter(PipelineRun.user_id == user_id, PipelineRun.status.in_(["queued", "running"]))
        .order_by(PipelineRun.created_at.desc())
        .first()
    )
    if active:
        if mark_stale_popo_to_raw_run(db, active):
            db.commit()
        else:
            raise PopoToRawPublishError(f"已有任务正在运行：run_id={active.id}")

    run = db.query(PipelineRun).filter(PipelineRun.id == dry_run_id, PipelineRun.user_id == user_id).first()
    if not run or run.mode != "popo2raw":
        raise PopoToRawPublishError("指定的 dry-run 不存在或不是 Popo→Raw 任务")
    if run.status != "succeeded":
        raise PopoToRawPublishError(f"只能发布已成功的 dry-run，当前状态为 {run.status}")
    summary = run.summary()
    if summary.get("published"):
        raise PopoToRawPublishError("该 Popo→Raw 结果已经发布")
    if str(summary.get("material_id") or "") != str(material.material_id or ""):
        raise PopoToRawPublishError("dry-run 与当前材料不匹配")

    body_final = Path(str(summary.get("body_final") or ""))
    if not body_final.exists():
        raise PopoToRawPublishError(f"dry-run 产物目录不存在：{body_final}")

    preflight = popo_to_raw_preflight(material, force=force, publish=True)
    if not preflight["ready"]:
        raise PopoToRawPreflightError(preflight)

    outline_summary = outline_artifact_summary(body_final)
    validate_outline_mechanical_qa(outline_summary)
    mineru_run_id = str(summary.get("mineru_run_id") or resolve_mineru_run_id(material))
    popo_run_id = str(summary.get("popo_run_id") or material.popo_run_id or "")
    raw_prefix = preflight["raw_prefix"]
    enrich_raw_manifest(body_final, material, raw_prefix, mineru_run_id, popo_run_id, publish=True)
    ensure_raw_deliverables(body_final)
    publish_directory_to_minio(body_final, RAW_BUCKET, raw_prefix)
    invalidated = invalidate_clean_after_raw_rebuild(db, user_id, str(material.material_id or ""))

    summary.update(
        {
            "published": True,
            "raw_bucket": RAW_BUCKET,
            "raw_prefix": raw_prefix,
            "raw_manifest": f"{raw_prefix}manifest.json",
            "outline_artifacts": outline_summary,
            "published_from_dry_run": True,
            "published_at": datetime.utcnow().isoformat(),
            "invalidated_clean": invalidated,
        }
    )
    run.summary_json = json.dumps(summary, ensure_ascii=False)
    run.current_stage = "publish"
    run.finished_at = datetime.utcnow()
    run.error_message = ""
    create_pipeline_event(db, run, "已确认发布 dry-run Raw 产物到 eduassets-raw", stage="publish", payload=summary)
    sync_material_inventory(db, user_id)
    stale_mark = mark_raw_rows_clean_stale(db, user_id, str(material.material_id or ""))
    summary["invalidated_clean"]["post_sync_clean_stale"] = stale_mark
    run.summary_json = json.dumps(summary, ensure_ascii=False)
    create_pipeline_event(db, run, "Raw 发布后材料状态已标记为 Clean 失效", stage="clean_stale", payload=stale_mark)
    db.commit()
    return run


def mark_stale_popo_to_raw_run(db: Session, run: PipelineRun) -> bool:
    if run.mode != "popo2raw" or run.status not in {"queued", "running"}:
        return False
    started = run.started_at or run.created_at
    if not started:
        return False
    stale_seconds = int(os.getenv("LUCEON_STALE_PIPELINE_SECONDS", "300"))
    age_seconds = (datetime.utcnow() - started).total_seconds()
    if age_seconds < stale_seconds:
        return False
    if run_has_live_process(run.id):
        return False
    run.status = "failed"
    run.current_stage = "stale"
    run.failed = 1
    run.finished_at = datetime.utcnow()
    run.error_message = f"Popo→Raw task marked stale after {int(age_seconds)}s without a live worker process."
    material_pk = ((run.summary() or {}).get("preflight") or {}).get("material_pk")
    try:
        material_id = int(material_pk) if material_pk else 0
    except (TypeError, ValueError):
        material_id = 0
    if material_id:
        material = db.query(Material).filter(Material.id == material_id).first()
        if material and material.pipeline_status == "running":
            material.pipeline_status = "failed"
    create_pipeline_event(
        db,
        run,
        "Popo→Raw 任务已标记为 stale，可重新启动",
        stage="stale",
        level="warning",
        payload={"age_seconds": int(age_seconds), "stale_seconds": stale_seconds},
    )
    return True


def latest_successful_popo_to_raw_dry_run(db: Session, user_id: str, material_id: str) -> PipelineRun | None:
    if not material_id:
        return None
    runs = (
        db.query(PipelineRun)
        .filter(PipelineRun.user_id == user_id, PipelineRun.mode == "popo2raw", PipelineRun.status == "succeeded")
        .order_by(PipelineRun.finished_at.desc().nullslast(), PipelineRun.created_at.desc())
        .limit(50)
        .all()
    )
    latest_published_at = None
    for run in runs:
        summary = run.summary()
        if str(summary.get("material_id") or "") != str(material_id):
            continue
        if not summary.get("published"):
            continue
        published_at = run.finished_at or run.created_at
        if latest_published_at is None or (published_at and published_at > latest_published_at):
            latest_published_at = published_at

    for run in runs:
        summary = run.summary()
        if summary.get("published"):
            continue
        if str(summary.get("material_id") or "") != str(material_id):
            continue
        run_at = run.finished_at or run.created_at
        if latest_published_at and run_at and run_at <= latest_published_at:
            continue
        body_final = Path(str(summary.get("body_final") or ""))
        if body_final.exists():
            return run
    return None


def run_has_live_process(run_id: int) -> bool:
    marker = f"run-{run_id}-"
    try:
        completed = subprocess.run(["ps", "-eo", "args"], text=True, capture_output=True, timeout=3)
    except Exception:
        return True
    if completed.returncode != 0:
        return True
    return marker in (completed.stdout or "")


def run_popo_to_raw_subprocess(run_id: int, material_pk: int, publish: bool, force: bool) -> None:
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
        create_pipeline_event(db, run, "开始物化 MinerU-Popo 与 MinerU 资产", stage="materialize")
        db.commit()

        result = execute_popo_to_raw(material, run_id=run_id, publish=publish, force=force, event_callback=lambda stage, message, payload=None: add_event(db, run, stage, message, payload))
        if publish and force:
            invalidated = invalidate_clean_after_raw_rebuild(db, run.user_id, result["material_id"])
            result["invalidated_clean"] = invalidated
            add_event(db, run, "invalidate_clean", "Raw 已重建，下游 Clean 已清空或标记失效，等待重新生成", invalidated)

        run.status = "succeeded"
        run.current_stage = "finished"
        run.processed = 1
        run.success = 1
        run.finished_at = datetime.utcnow()
        run.summary_json = json.dumps(result, ensure_ascii=False)
        material.pipeline_status = "idle"
        finished_message = "Popo→Raw 已发布到 eduassets-raw" if publish else "Popo→Raw dry-run 已完成，未写入 MinIO"
        create_pipeline_event(db, run, finished_message, stage="finished", payload=result)
        if publish:
            sync_material_inventory(db, run.user_id)
            if force:
                stale_mark = mark_raw_rows_clean_stale(db, run.user_id, result["material_id"])
                result["invalidated_clean"]["post_sync_clean_stale"] = stale_mark
                run.summary_json = json.dumps(result, ensure_ascii=False)
                add_event(db, run, "clean_stale", "Raw 发布后材料状态已标记为 Clean 失效", stale_mark)
        db.commit()
    except BaseException as exc:
        run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        material = db.query(Material).filter(Material.id == material_pk).first()
        if run:
            run.status = "failed"
            run.current_stage = "failed"
            run.failed = 1
            run.finished_at = datetime.utcnow()
            run.error_message = str(exc)
            create_pipeline_event(
                db,
                run,
                "Popo→Raw 任务失败",
                stage="failed",
                level="error",
                payload={"error": str(exc), "error_type": type(exc).__name__},
            )
        if material:
            material.pipeline_status = "failed"
        db.commit()
    finally:
        db.close()


def add_event(db: Session, run: PipelineRun, stage: str, message: str, payload: dict[str, Any] | None = None) -> None:
    run.current_stage = stage
    create_pipeline_event(db, run, message, stage=stage, payload=payload)
    db.commit()


def invalidate_clean_after_raw_rebuild(db: Session, user_id: str, material_id: str) -> dict[str, Any]:
    if not material_id:
        return {"material_id": material_id, "prefixes": [], "objects_deleted": 0, "rows_cleared": 0}

    clean_root = f"clean/{material_id}/"
    deleted = delete_prefix(CLEAN_BUCKET, clean_root)
    rows = (
        db.query(Material)
        .filter(Material.user_id == user_id, Material.material_id == material_id)
        .filter(Material.clean_manifest_object.isnot(None))
        .all()
    )
    for row in rows:
        row.clean_manifest_bucket = None
        row.clean_manifest_object = None
        row.clean_run_id = None
        if row.raw_manifest_object:
            row.stage_status = "clean_stale"
        elif row.popo_manifest_object:
            row.stage_status = "popo_done"
        elif row.mineru_manifest_object:
            row.stage_status = "mineru_done"
        else:
            row.stage_status = "input"
    db.flush()
    return {
        "material_id": material_id,
        "prefixes": [f"{CLEAN_BUCKET}/{clean_root}"],
        "objects_deleted": deleted,
        "rows_cleared": len(rows),
        "next_stage": "clean_stale",
    }


def mark_raw_rows_clean_stale(db: Session, user_id: str, material_id: str) -> dict[str, Any]:
    rows = (
        db.query(Material)
        .filter(Material.user_id == user_id, Material.material_id == material_id)
        .filter(Material.raw_manifest_object.isnot(None))
        .all()
    )
    changed = 0
    for row in rows:
        if row.stage_status != "clean_stale":
            row.stage_status = "clean_stale"
            changed += 1
    db.flush()
    return {
        "material_id": material_id,
        "raw_rows_seen": len(rows),
        "rows_marked_clean_stale": changed,
        "next_stage": "clean_stale",
    }


def delete_prefix(bucket: str, prefix: str) -> int:
    normalized = clean_path(prefix).rstrip("/") + "/"
    if bucket != CLEAN_BUCKET or not normalized.startswith("clean/"):
        raise RuntimeError(f"Unsafe clean invalidation target: {bucket}/{normalized}")
    deleted = 0
    for object_name in list_object_names(bucket, normalized):
        minio_client.remove_object(bucket, object_name)
        deleted += 1
    return deleted


def execute_popo_to_raw(material: Material, run_id: int, publish: bool, force: bool, event_callback) -> dict[str, Any]:
    preflight = popo_to_raw_preflight(material, force=force, publish=publish)
    if not preflight["ready"]:
        raise PopoToRawPreflightError(preflight)

    material_id = preflight["material_id"]
    popo_run_id = preflight["popo_run_id"]
    mineru_run_id = preflight["mineru_run_id"]
    raw_prefix = preflight["raw_prefix"]
    work_dir = WORK_ROOT / "popo2raw" / f"run-{run_id}-{material_id}-{popo_run_id}"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    download_dir = work_dir / "_minio_download"
    rebuild_input = work_dir / "rebuild_input"
    body_final = work_dir / "body-final"
    rebuild_input.mkdir(parents=True, exist_ok=True)

    download_prefix(POPO_BUCKET, f"minerupopo/{material_id}/{popo_run_id}/", download_dir / "minerupopo")
    download_prefix(MINERU_BUCKET, f"mineru/{material_id}/{mineru_run_id}/", download_dir / "mineru")
    download_prefix(INPUT_BUCKET, f"_status/{material_id}/", download_dir / "input_status")
    event_callback("materialize", "上游资产已下载到本地工作目录", {"work_dir": str(work_dir)})

    build_rebuild_input(download_dir, rebuild_input, material_id, popo_run_id, mineru_run_id)
    event_callback("rebuild_input", "已生成重建输入目录", {"rebuild_input": str(rebuild_input)})

    run_env = pipeline_env()
    event_callback("bootstrap", "开始调用 pdf-clean-markdown-rebuild 的 bootstrap_clean_markdown.py")
    bootstrap_cmd = ["python3", str(BOOTSTRAP_SCRIPT), str(rebuild_input), "--out-dir", str(body_final)]
    if run_env.get("LUCEON_RAW_OUTLINE_LLM", "1").lower() in {"1", "true", "yes", "on"}:
        bootstrap_cmd.append("--with-llm-outline")
    if run_env.get("LUCEON_RAW_OUTLINE_VISION", "").lower() in {"1", "true", "yes", "on"}:
        bootstrap_cmd.append("--with-visual-outline")
    bootstrap_cmd.extend(
        [
            "--llm-outline-max-risk-candidates",
            run_env.get("LUCEON_RAW_OUTLINE_LLM_MAX_RISK_CANDIDATES", "120"),
            "--visual-outline-max-candidates",
            run_env.get("LUCEON_RAW_OUTLINE_VISUAL_MAX_CANDIDATES", "40"),
        ]
    )
    completed = subprocess.run(
        bootstrap_cmd,
        cwd=str(SKILL_ROOT),
        env=run_env,
        text=True,
        capture_output=True,
        timeout=None,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or f"bootstrap exited {completed.returncode}")[-4000:])
    event_callback("bootstrap", "目录重建草稿已生成", {"stdout_tail": (completed.stdout or "")[-2000:]})

    outline_summary = outline_artifact_summary(body_final)
    emit_outline_stage_events(event_callback, outline_summary)
    validate_outline_mechanical_qa(outline_summary)
    enrich_raw_manifest(body_final, material, raw_prefix, mineru_run_id, popo_run_id, publish=publish)
    ensure_raw_deliverables(body_final)
    if publish:
        publish_directory_to_minio(body_final, RAW_BUCKET, raw_prefix)
        event_callback("publish", "Raw 产物已写入 eduassets-raw", {"raw_bucket": RAW_BUCKET, "raw_prefix": raw_prefix})
    else:
        event_callback("dry_run", "Raw dry-run 产物保留在本地工作目录，未写入 MinIO", {"work_dir": str(work_dir), "body_final": str(body_final)})
    return {
        "stage": "popo2raw",
        "material_id": material_id,
        "filename": material.filename,
        "popo_run_id": popo_run_id,
        "mineru_run_id": mineru_run_id,
        "raw_bucket": RAW_BUCKET,
        "raw_prefix": raw_prefix,
        "raw_manifest": f"{raw_prefix}manifest.json" if publish else "",
        "work_dir": str(work_dir),
        "body_final": str(body_final),
        "published": publish,
        "outline_artifacts": outline_summary,
    }


def emit_outline_stage_events(event_callback, summary: dict[str, Any]) -> None:
    candidates = summary.get("outline_candidates_summary") or {}
    decision = summary.get("outline_decision") or {}
    candidates = summary.get("outline_candidates_summary") or {}
    visual = summary.get("visual_decisions") or {}
    apply_report = summary.get("outline_apply_report") or {}
    image_report = summary.get("image_closure_report") or {}
    chunk_report = summary.get("chunk_boundary_report") or {}
    event_callback(
        "candidate_collect",
        "目录候选搜集完成",
        {
            "candidate_count": candidates.get("candidate_count") or candidates.get("total_count") or 0,
            "candidate_type_counts": candidates.get("candidate_type_counts") or candidates.get("type_counts") or {},
            "outline_candidates_jsonl": summary.get("outline_candidates_jsonl"),
        },
    )
    event_callback(
        "llm_decision",
        "LLM 目录推理完成",
        {
            "decision_method": decision.get("decision_method"),
            "final_outline_count": decision.get("final_outline_count"),
            "rejected_count": decision.get("rejected_count"),
            "needs_visual_count": decision.get("needs_visual_count"),
            "llm": decision.get("llm") or {},
        },
    )
    event_callback(
        "visual_review",
        "视觉核实完成",
        {
            "enabled": visual.get("enabled"),
            "provider": visual.get("provider"),
            "model": visual.get("model"),
            "candidate_count": visual.get("candidate_count"),
            "validated_count": visual.get("validated_count"),
            "error_count": visual.get("error_count"),
            "visual_application": decision.get("visual_application") or {},
        },
    )
    event_callback(
        "flooding",
        "规则洪泛与目录切分完成",
        {
            "eligible_block_count": apply_report.get("eligible_block_count"),
            "assigned_block_count": apply_report.get("assigned_block_count"),
            "unassigned_block_count": apply_report.get("unassigned_block_count"),
            "leaf_units_without_blocks_count": apply_report.get("leaf_units_without_blocks_count"),
            "unit_count": chunk_report.get("unit_count"),
            "leaf_count": chunk_report.get("leaf_count"),
        },
    )
    event_callback(
        "qa",
        "Raw 机械 QA 摘要已生成",
        {
            "missing_image_count": image_report.get("missing_image_count"),
            "markdown_refs_not_copied_count": image_report.get("markdown_refs_not_copied_count"),
            "empty_leaf_count": chunk_report.get("empty_leaf_count"),
            "source_empty_chunk_count": chunk_report.get("source_empty_chunk_count"),
        },
    )


def validate_outline_mechanical_qa(summary: dict[str, Any]) -> None:
    blockers: list[str] = []
    decision = summary.get("outline_decision") or {}
    candidates = summary.get("outline_candidates_summary") or {}
    visual = summary.get("visual_decisions") or {}
    apply_report = summary.get("outline_apply_report") or {}
    image_report = summary.get("image_closure_report") or {}
    chunk_report = summary.get("chunk_boundary_report") or {}
    heading_report = summary.get("heading_order_report") or {}
    run_env = pipeline_env()
    llm_required = run_env.get("LUCEON_RAW_OUTLINE_LLM", "1").lower() in {"1", "true", "yes", "on"}
    vision_required = run_env.get("LUCEON_RAW_OUTLINE_VISION", "").lower() in {"1", "true", "yes", "on"}

    if not decision.get("available"):
        blockers.append("missing_outline_decision")
    llm_decision_methods = {"llm_reviewed_candidate_outline", "llm_global_candidate_outline"}
    if llm_required and decision.get("decision_method") not in llm_decision_methods:
        blockers.append("llm_decision_not_applied")
    if llm_required and not (decision.get("llm") or {}).get("call_count"):
        blockers.append("missing_llm_usage")

    visual_app = decision.get("visual_application") or {}
    if vision_required and visual.get("enabled") is not True:
        blockers.append("visual_not_enabled")
    if visual.get("error_count"):
        blockers.append(f"visual_errors:{visual.get('error_count')}")
    if visual_app.get("conflict_count"):
        blockers.append(f"visual_conflicts:{visual_app.get('conflict_count')}")
    if visual_app.get("pending_count"):
        blockers.append(f"visual_pending:{visual_app.get('pending_count')}")

    if apply_report.get("unassigned_block_count"):
        blockers.append(f"unassigned_blocks:{apply_report.get('unassigned_block_count')}")
    if image_report.get("missing_image_count"):
        blockers.append(f"missing_images:{image_report.get('missing_image_count')}")
    if image_report.get("markdown_refs_not_copied_count"):
        blockers.append(f"uncopied_image_refs:{image_report.get('markdown_refs_not_copied_count')}")
    empty_leaf = int(chunk_report.get("empty_leaf_count") or 0)
    source_empty = int(chunk_report.get("source_empty_chunk_count") or 0)
    if empty_leaf > source_empty:
        blockers.append(f"empty_leaf_without_source_empty:{empty_leaf - source_empty}")
    if not chunk_report.get("unit_count"):
        blockers.append("missing_raw_units")
    if heading_report.get("parent_order_violation_count"):
        blockers.append(f"heading_parent_order:{heading_report.get('parent_order_violation_count')}")
    if heading_report.get("parent_level_violation_count"):
        blockers.append(f"heading_parent_level:{heading_report.get('parent_level_violation_count')}")
    if heading_report.get("duplicate_same_parent_count"):
        blockers.append(f"duplicate_same_parent_headings:{heading_report.get('duplicate_same_parent_count')}")
    if heading_report.get("nested_numbered_major_heading_count"):
        blockers.append(f"nested_numbered_major_headings:{heading_report.get('nested_numbered_major_heading_count')}")
    final_outline_count = int(decision.get("final_outline_count") or decision.get("selected_count") or 0)
    raw_unit_count = int(apply_report.get("unit_count") or chunk_report.get("unit_count") or 0)
    if decision.get("decision_method") == "llm_global_candidate_outline" and final_outline_count and raw_unit_count > final_outline_count:
        blockers.append(f"raw_units_exceed_final_outline:{raw_unit_count}>{final_outline_count}")
    candidate_types = candidates.get("candidate_type_counts") if isinstance(candidates.get("candidate_type_counts"), dict) else {}
    lesson_candidate_count = int(candidate_types.get("body_lesson_heading") or 0)
    max_heading_level = int(chunk_report.get("max_heading_level") or 0)
    if lesson_candidate_count >= 2 and max_heading_level < 2:
        blockers.append(f"lesson_candidates_not_emitted:{lesson_candidate_count}")

    if blockers:
        raise RuntimeError("Raw mechanical QA failed: " + "; ".join(blockers))


def resolve_mineru_run_id(material: Material) -> str:
    if material.mineru_run_id:
        return material.mineru_run_id
    if material.popo_manifest_bucket and material.popo_manifest_object:
        manifest = read_json_safe(material.popo_manifest_bucket, material.popo_manifest_object)
        upstream = manifest.get("upstream_mineru") if isinstance(manifest.get("upstream_mineru"), dict) else {}
        stage_run_ids = manifest.get("stage_run_ids") if isinstance(manifest.get("stage_run_ids"), dict) else {}
        run_id = str(upstream.get("run_id") or stage_run_ids.get("mineru") or "")
        if run_id and prefix_exists(MINERU_BUCKET, f"mineru/{material.material_id}/{run_id}/"):
            return run_id
        manifest_ref = upstream.get("manifest") if isinstance(upstream.get("manifest"), dict) else {}
        inferred = mineru_run_id_from_manifest_object(material.material_id or "", str(manifest_ref.get("object") or ""))
        if inferred and prefix_exists(MINERU_BUCKET, f"mineru/{material.material_id}/{inferred}/"):
            return inferred
    for run_id in list_prefix_children(MINERU_BUCKET, f"mineru/{material.material_id}/"):
        if prefix_exists(MINERU_BUCKET, f"mineru/{material.material_id}/{run_id}/"):
            return run_id
    return ""


def mineru_run_id_from_manifest_object(material_id: str, manifest_object: str) -> str:
    match = re.search(r"(?:^|/)mineru/%s/([^/]+)/manifest\.json$" % re.escape(material_id), str(manifest_object or ""))
    return match.group(1) if match else ""


def read_json_safe(bucket: str, object_name: str) -> dict[str, Any]:
    try:
        return parse_json_bytes(read_object(bucket, object_name))
    except Exception:
        return {}


def prefix_exists(bucket: str, prefix: str) -> bool:
    try:
        next(minio_client.list_objects(bucket, prefix=clean_path(prefix).rstrip("/") + "/", recursive=True))
        return True
    except StopIteration:
        return False
    except Exception:
        return False


def list_prefix_children(bucket: str, prefix: str) -> list[str]:
    children = []
    normalized = clean_path(prefix).rstrip("/") + "/"
    try:
        for item in minio_client.list_objects(bucket, prefix=normalized, recursive=False):
            object_name = clean_path(getattr(item, "object_name", ""))
            if not object_name:
                continue
            child = object_name[len(normalized):].strip("/").split("/")[0]
            if child and child not in children:
                children.append(child)
    except Exception:
        return []
    return sorted(children)


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


def build_rebuild_input(download_dir: Path, rebuild_input: Path, material_id: str, popo_run_id: str, mineru_run_id: str) -> None:
    mineru_vlm = find_mineru_vlm(download_dir)
    popo_vlm = find_popo_vlm(download_dir)
    if not mineru_vlm:
        raise RuntimeError("Could not find MinerU content_list assets in downloaded task.")
    if rebuild_input.exists():
        shutil.rmtree(rebuild_input)
    rebuild_input.mkdir(parents=True)

    for src_name, dest_name in [
        ("input_content_list.json", f"{material_id}_content_list.json"),
        ("input_content_list_v2.json", f"{material_id}_content_list_v2.json"),
        ("input_model.json", f"{material_id}_model.json"),
        ("input_middle.json", f"{material_id}_middle.json"),
        ("input_origin.pdf", f"{material_id}_origin.pdf"),
        ("input_layout.pdf", f"{material_id}_layout.pdf"),
        ("input.md", "full.md"),
    ]:
        copy_if_exists(mineru_vlm / src_name, rebuild_input / dest_name)
    copytree_if_exists(mineru_vlm / "images", rebuild_input / "images")
    if popo_vlm:
        copy_if_exists(popo_vlm / "input.md", rebuild_input / "popo_input.md")
        copytree_if_exists(popo_vlm / "images", rebuild_input / "popo_images")

    for dest_name, pattern, preferred in [
        ("popo_raw.json", "popo_raw.json", ("enhanced", "minerupopo")),
        ("popo_document_tree.json", "document_tree.json", ("enhanced", "minerupopo")),
        ("popo_document_tree.txt", "document_tree.txt", ("enhanced", "minerupopo")),
        ("popo_build_tree.json", "build_tree.json", ("build_tree", "minerupopo")),
        ("popo_inference.json", "inference.json", ("minerupopo",)),
        ("popo_label_normalization.json", "label_normalization.json", ("label_normalization", "minerupopo")),
    ]:
        src = find_best(download_dir, pattern, preferred_parts=preferred)
        if src:
            copy_if_exists(src, rebuild_input / dest_name)

    trace = {
        "pdf_id": material_id,
        "job_id": popo_run_id,
        "popo_job_id": popo_run_id,
        "mineru_job_id": mineru_run_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "rebuild_input_files": list_relative_files(rebuild_input),
    }
    (rebuild_input.parent / "source_trace.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")


def find_mineru_vlm(download_dir: Path) -> Path | None:
    candidates = []
    for content_path in download_dir.rglob("*content_list.json"):
        if content_path.name.endswith("_content_list.json") or content_path.name == "input_content_list.json":
            candidates.append(content_path.parent)
    if not candidates:
        return None

    def score(path: Path):
        parts = set(path.parts)
        return (("official" in parts) + ("input" in parts) + ("vlm" in parts), -len(path.parts))

    return sorted(candidates, key=score, reverse=True)[0]


def find_popo_vlm(download_dir: Path) -> Path | None:
    candidates = [path.parent for path in download_dir.rglob("input.md") if "minerupopo" in path.parts]
    return sorted(candidates, key=lambda path: len(path.parts))[0] if candidates else None


def find_best(root: Path, pattern: str, preferred_parts=()) -> Path | None:
    matches = sorted(root.rglob(pattern))
    if not matches:
        return None

    def score(path: Path):
        parts = set(path.parts)
        return (sum(1 for part in preferred_parts if part in parts), -len(path.parts), str(path))

    return sorted(matches, key=score, reverse=True)[0]


def copy_if_exists(src: Path, dest: Path) -> bool:
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return True
    return False


def copytree_if_exists(src: Path, dest: Path) -> bool:
    if src.exists():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        return True
    return False


def list_relative_files(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(str(p.relative_to(path)) for p in path.rglob("*") if p.is_file())


def heading_order_report(clean_md: Path) -> dict[str, Any]:
    chinese_digit_values = {
        "零": 0,
        "〇": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }

    def parse_chinese_number(text: str) -> int | None:
        if not text:
            return None
        if text in chinese_digit_values:
            return chinese_digit_values[text]
        if "十" in text:
            left, _, right = text.partition("十")
            tens = chinese_digit_values.get(left, 1 if left == "" else None)
            ones = chinese_digit_values.get(right, 0 if right == "" else None)
            if tens is not None and ones is not None:
                return tens * 10 + ones
        return None

    def heading_parent_number(title: str) -> int | None:
        title = title.strip()
        bare = re.match(r"^(\d{1,2})\s+\S+", title)
        if bare:
            return int(bare.group(1))
        chapter = re.match(r"^第\s*(\d{1,2})\s*章", title)
        if chapter:
            return int(chapter.group(1))
        chinese_chapter = re.match(r"^第\s*([零〇一二两三四五六七八九十]{1,3})\s*章", title)
        if chinese_chapter:
            return parse_chinese_number(chinese_chapter.group(1))
        return None

    def normalized_heading_title(title: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", " ", str(title or "")).strip().lower()
        return re.sub(r"\s+", " ", normalized)

    def bare_numbered_major_heading(title: str) -> bool:
        return bool(re.match(r"^\d{1,2}\s+\S+", str(title or "").strip()))

    def structural_container_title(title: str) -> bool:
        return bool(
            re.match(
                r"^(Part|Chapter|Unit|Module|Section)\s+\S+|^第\s*[零〇一二两三四五六七八九十百千万0-9]+\s*[章节单元篇]",
                str(title or "").strip(),
                re.I,
            )
        )

    headings: list[dict[str, Any]] = []
    if clean_md.exists():
        parent_stack: list[dict[str, Any]] = []
        for line_no, line in enumerate(clean_md.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            match = re.match(r"^(#{1,3})\s+(.+?)\s*$", line)
            if not match:
                continue
            level = len(match.group(1))
            title = match.group(2)
            parent_stack = [item for item in parent_stack if int(item.get("level") or 0) < level]
            parent_path = " > ".join(str(item.get("title") or "") for item in parent_stack)
            heading = {
                "line": line_no,
                "level": level,
                "title": title,
                "normalized_title": normalized_heading_title(title),
                "parent_path": parent_path,
            }
            headings.append(heading)
            parent_stack.append(heading)
    seen_parent_numbers: dict[int, dict[str, Any]] = {}
    order_violations: list[dict[str, Any]] = []
    level_violations: list[dict[str, Any]] = []
    duplicate_groups: dict[tuple[int, str, str], list[dict[str, Any]]] = {}
    nested_numbered_by_parent: dict[str, list[dict[str, Any]]] = {}
    for heading in headings:
        title = str(heading.get("title") or "")
        duplicate_key = (
            int(heading.get("level") or 0),
            str(heading.get("parent_path") or ""),
            str(heading.get("normalized_title") or ""),
        )
        if duplicate_key[2]:
            duplicate_groups.setdefault(duplicate_key, []).append(heading)
        if bare_numbered_major_heading(title) and int(heading.get("level") or 0) > 1:
            parent_path = str(heading.get("parent_path") or "")
            parent_title = parent_path.split(" > ")[-1] if parent_path else ""
            if parent_title and not structural_container_title(parent_title):
                nested_numbered_by_parent.setdefault(parent_path, []).append(heading)
        parent_number = heading_parent_number(title)
        if heading.get("level") == 1 and parent_number is not None:
            seen_parent_numbers[parent_number] = heading
        child = re.match(r"^(\d{1,2})\.\d+\b", title)
        if child:
            child_parent_number = int(child.group(1))
            parent_heading = seen_parent_numbers.get(child_parent_number)
            if parent_heading is None:
                order_violations.append(heading)
            elif int(heading.get("level") or 9) <= int(parent_heading.get("level") or 1):
                level_violations.append({"child": heading, "parent": parent_heading})
    duplicate_same_parent = []
    for (level, parent_path, _normalized), rows in duplicate_groups.items():
        if len(rows) < 2:
            continue
        first_title = str(rows[0].get("title") or "")
        if level != 1 and not re.search(r"\d", first_title):
            continue
        duplicate_same_parent.append(
            {
                "level": level,
                "title": first_title,
                "parent_path": parent_path,
                "lines": [row.get("line") for row in rows[:10]],
                "count": len(rows),
            }
        )
    nested_numbered_major_headings = [
        {
            "parent_path": parent_path,
            "count": len(rows),
            "headings": [
                {"line": row.get("line"), "level": row.get("level"), "title": row.get("title")}
                for row in rows[:10]
            ],
        }
        for parent_path, rows in nested_numbered_by_parent.items()
        if len(rows) >= 3
    ]
    return {
        "available": clean_md.exists(),
        "heading_count": len(headings),
        "parent_order_violation_count": len(order_violations),
        "parent_order_violations": order_violations[:20],
        "parent_level_violation_count": len(level_violations),
        "parent_level_violations": level_violations[:20],
        "duplicate_same_parent_count": len(duplicate_same_parent),
        "duplicate_same_parent_headings": duplicate_same_parent[:20],
        "nested_numbered_major_heading_count": len(nested_numbered_major_headings),
        "nested_numbered_major_headings": nested_numbered_major_headings[:20],
    }


def outline_artifact_summary(body_final: Path) -> dict[str, Any]:
    summary = read_local_json(body_final / "outline_candidates_summary.json")
    decision = read_local_json(body_final / "outline_decision.json")
    visual = read_local_json(body_final / "visual_decisions.json")
    apply_report = read_local_json(body_final / "outline_apply_report.json")
    image_closure = read_local_json(body_final / "image_closure_report.json")
    chunk_boundary = read_local_json(body_final / "chunk_boundary_report.json")
    heading_order = heading_order_report(body_final / "clean.md")
    return {
        "outline_candidates_jsonl": str(body_final / "outline_candidates.jsonl") if (body_final / "outline_candidates.jsonl").exists() else "",
        "raw_block_assignments_jsonl": str(body_final / "raw_block_assignments.jsonl") if (body_final / "raw_block_assignments.jsonl").exists() else "",
        "unassigned_blocks_jsonl": str(body_final / "unassigned_blocks.jsonl") if (body_final / "unassigned_blocks.jsonl").exists() else "",
        "outline_candidates_summary": summary,
        "outline_decision": {
            "available": bool(decision),
            "decision_method": decision.get("decision_method"),
            "selected_count": decision.get("selected_count"),
            "final_outline_count": decision.get("final_outline_count"),
            "final_outline_source": decision.get("final_outline_source"),
            "rejected_count": decision.get("rejected_count"),
            "needs_llm_count": decision.get("needs_llm_count"),
            "needs_visual_count": decision.get("needs_visual_count"),
            "llm": decision.get("llm"),
            "visual_application": decision.get("visual_application"),
        },
        "visual_decisions": {
            "available": bool(visual),
            "enabled": visual.get("enabled"),
            "provider": visual.get("provider"),
            "model": visual.get("model"),
            "candidate_count": visual.get("candidate_count"),
            "validated_count": visual.get("validated_count"),
            "usage": visual.get("usage"),
            "error_count": len(visual.get("errors") or []),
        },
        "outline_apply_report": {
            "available": bool(apply_report),
            "method": apply_report.get("method"),
            "unit_count": apply_report.get("unit_count"),
            "eligible_block_count": apply_report.get("eligible_block_count"),
            "assigned_block_count": apply_report.get("assigned_block_count"),
            "unassigned_block_count": apply_report.get("unassigned_block_count"),
            "leaf_units_without_blocks_count": len(apply_report.get("leaf_units_without_blocks") or []),
            "container_units_without_direct_blocks_count": len(apply_report.get("container_units_without_direct_blocks") or []),
        },
        "image_closure_report": {
            "available": bool(image_closure),
            "source_image_ref_count": image_closure.get("source_image_ref_count"),
            "markdown_image_ref_count": image_closure.get("markdown_image_ref_count"),
            "copied_image_count": image_closure.get("copied_image_count"),
            "missing_image_count": image_closure.get("missing_image_count"),
            "markdown_refs_not_copied_count": len(image_closure.get("markdown_refs_not_copied") or []),
        },
        "chunk_boundary_report": {
            "available": bool(chunk_boundary),
            "unit_count": chunk_boundary.get("unit_count"),
            "leaf_count": chunk_boundary.get("leaf_count"),
            "empty_leaf_count": chunk_boundary.get("empty_leaf_count"),
            "source_empty_chunk_count": chunk_boundary.get("source_empty_chunk_count"),
            "unassigned_block_count": chunk_boundary.get("unassigned_block_count"),
            "max_heading_level": chunk_boundary.get("max_heading_level"),
        },
        "heading_order_report": heading_order,
    }


def enrich_raw_manifest(body_final: Path, material: Material, raw_prefix: str, mineru_run_id: str, popo_run_id: str, publish: bool = True) -> None:
    manifest_path = body_final / "manifest.json"
    manifest = read_local_json(manifest_path)
    objects = manifest.get("objects") if isinstance(manifest.get("objects"), dict) else {}
    for name in [
        "clean.md",
        "preview.html",
        "qa_report.md",
        "popo_outline.json",
        "outline_candidates.jsonl",
        "outline_candidates_summary.json",
        "outline_decision.json",
        "visual_decisions.json",
        "raw_units.jsonl",
        "raw_block_assignments.jsonl",
        "unassigned_blocks.jsonl",
        "outline_apply_report.json",
        "image_closure_report.json",
        "chunk_boundary_report.json",
    ]:
        key = name.replace(".", "_").replace("-", "_")
        objects[key] = {"bucket": RAW_BUCKET if publish else "", "object": f"{raw_prefix}{name}" if publish else ""}
    manifest.update(
        {
            "schema": "luceon-eduassets-raw/v1",
            "material_id": material.material_id,
            "run_id": popo_run_id,
            "title": material.title,
            "filename": material.filename,
            "review_stage": "raw",
            "publish_mode": "publish" if publish else "dry_run",
            "source_pdf": {
                "input_bucket": material.input_bucket,
                "input_object": material.input_object,
                "filename": material.filename,
                "sha256": material.input_sha256,
                "size_bytes": material.size_bytes,
            },
            "upstream": {
                "mineru": {"bucket": MINERU_BUCKET, "run_id": mineru_run_id, "manifest": material.mineru_manifest_object},
                "minerupopo": {"bucket": POPO_BUCKET, "run_id": popo_run_id, "manifest": material.popo_manifest_object},
            },
            "stage_prefixes": {
                "raw": {"bucket": RAW_BUCKET, "prefix": raw_prefix, "official_prefix": raw_prefix},
                "mineru": {"bucket": MINERU_BUCKET, "prefix": f"mineru/{material.material_id}/{mineru_run_id}/"},
                "minerupopo": {"bucket": POPO_BUCKET, "prefix": f"minerupopo/{material.material_id}/{popo_run_id}/"},
            },
            "objects": objects,
        }
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    trace_path = body_final.parent / "source_trace.json"
    if trace_path.exists():
        shutil.copy2(trace_path, body_final / "source_trace.json")


def read_local_json(path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def ensure_raw_deliverables(local_dir: Path) -> None:
    missing = [
        name
        for name in [
            "clean.md",
            "preview.html",
            "manifest.json",
            "qa_report.md",
            "images",
            "outline_candidates.jsonl",
            "outline_candidates_summary.json",
            "outline_decision.json",
            "visual_decisions.json",
            "raw_units.jsonl",
            "raw_block_assignments.jsonl",
            "unassigned_blocks.jsonl",
            "outline_apply_report.json",
            "image_closure_report.json",
            "chunk_boundary_report.json",
        ]
        if not (local_dir / name).exists()
    ]
    if not (local_dir / "outline-view.html").exists() and not (local_dir / "outline-anchor-check.html").exists():
        missing.append("outline-view.html or outline-anchor-check.html")
    if missing:
        raise RuntimeError(f"Missing required raw deliverables: {', '.join(missing)}")


def publish_directory_to_minio(local_dir: Path, bucket: str, prefix: str) -> None:
    if bucket != RAW_BUCKET:
        raise RuntimeError(f"Unsafe raw target bucket: {bucket}")
    normalized = clean_path(prefix).rstrip("/") + "/"
    if not normalized.startswith("raw/"):
        raise RuntimeError(f"Unsafe raw target prefix: {normalized}")
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
