from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import subprocess
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.material import CodexSkillJob, Material
from app.services.codex_elegantbook import output_from_ref
from app.services.codex_print_quality import build_print_quality_report
from app.services.luceon_review import ObjectRef, clean_path, minio_client, read_object
from app.services.material_outputs import promote_material_output, register_elegantbook_output
from app.services.worker_v1_policy import v1_batch_enabled


DEFAULT_SKILL_NAME = "luceon-popo-to-refined-elegantbook"
DEFAULT_SKILL_VERSION = "draft"
DEFAULT_STAGING_ROOT = Path("/data/codex-skill-work")
DEFAULT_PUBLISH_BUCKET = os.getenv("LUCEON_CODEX_PUBLISH_BUCKET", "eduassets-elegantbook")
DEFAULT_PUBLISH_PREFIX = clean_path(os.getenv("LUCEON_CODEX_PUBLISH_PREFIX", "elegantbook")).rstrip("/")
DEFAULT_CODEX_BIN = os.getenv("LUCEON_CODEX_BIN", "codex")
DEFAULT_CODEX_MODEL = os.getenv("LUCEON_CODEX_MODEL", "gpt-5.5")
ACTIVE_STATUSES = {"queued", "running", "dry_run_succeeded", "validating"}
RETRYABLE_STATUSES = {"failed", "cancelled", "dry_run_succeeded"}


class CodexSkillJobError(Exception):
    pass


def create_codex_skill_job(
    db: Session,
    user_id: str,
    material: Material,
    *,
    mode: str = "new_pdf",
    requested_skill: str = DEFAULT_SKILL_NAME,
    skill_version: str = DEFAULT_SKILL_VERSION,
    force: bool = False,
    payload: dict[str, Any] | None = None,
) -> CodexSkillJob:
    if not material.material_id:
        raise CodexSkillJobError("材料缺少 material_id")
    if not material.popo_manifest_bucket or not material.popo_manifest_object:
        raise CodexSkillJobError("材料尚无 Popo manifest，不能创建 Codex 精修任务")

    idempotency_key = _idempotency_key(user_id, material, mode, requested_skill, skill_version)
    existing = (
        db.query(CodexSkillJob)
        .filter(CodexSkillJob.user_id == user_id, CodexSkillJob.idempotency_key == idempotency_key)
        .order_by(CodexSkillJob.id.desc())
        .first()
    )
    if existing and not force:
        return existing
    if existing and force and existing.status in ACTIVE_STATUSES:
        raise CodexSkillJobError("已有活跃 Codex 精修任务，不能强制重复创建")

    job = CodexSkillJob(
        user_id=user_id,
        material_pk=material.id,
        material_id=material.material_id,
        review_asset_id=material.review_asset_id,
        mode=mode,
        status="queued",
        requested_skill=requested_skill,
        skill_version=skill_version,
        idempotency_key=idempotency_key if not force else f"{idempotency_key}:{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
        source_popo_manifest_bucket=material.popo_manifest_bucket,
        source_popo_manifest_object=material.popo_manifest_object,
        baseline_manifest_bucket=material.latex_manifest_bucket,
        baseline_manifest_object=material.latex_manifest_object,
        attempt_count=(existing.attempt_count + 1) if existing else 0,
        payload_json=json.dumps(payload or {}, ensure_ascii=False),
    )
    db.add(job)
    db.flush()
    return job


def list_codex_skill_jobs(db: Session, user_id: str, material: Material | None = None) -> list[CodexSkillJob]:
    query = db.query(CodexSkillJob).filter(CodexSkillJob.user_id == user_id)
    if material:
        query = query.filter(CodexSkillJob.material_id == (material.material_id or ""))
    return query.order_by(CodexSkillJob.created_at.desc(), CodexSkillJob.id.desc()).all()


def latest_codex_skill_job_for_material(db: Session, user_id: str, material: Material) -> CodexSkillJob | None:
    return (
        db.query(CodexSkillJob)
        .filter(CodexSkillJob.user_id == user_id, CodexSkillJob.material_id == (material.material_id or ""))
        .order_by(CodexSkillJob.created_at.desc(), CodexSkillJob.id.desc())
        .first()
    )


def enqueue_new_pdf_codex_jobs(db: Session, user_id: str, *, limit: int | None = None) -> dict[str, int | bool]:
    if not v1_batch_enabled():
        return {"selected": 0, "created": 0, "existing": 0, "failed": 0, "frozen": True}
    query = (
        db.query(Material)
        .filter(
            Material.user_id == user_id,
            Material.ignored.is_(False),
            Material.popo_manifest_object.isnot(None),
            Material.latex_manifest_object.is_(None),
        )
        .order_by(Material.last_synced_at.desc(), Material.id.desc())
    )
    if limit:
        query = query.limit(limit)
    return _enqueue_materials(db, user_id, query.all(), mode="new_pdf")


def enqueue_legacy_refresh_codex_jobs(
    db: Session,
    user_id: str,
    *,
    limit: int = 10,
    material_ids: list[str] | None = None,
) -> dict[str, int]:
    query = (
        db.query(Material)
        .filter(
            Material.user_id == user_id,
            Material.ignored.is_(False),
            Material.popo_manifest_object.isnot(None),
            Material.latex_manifest_object.isnot(None),
            or_(Material.latex_manifest_bucket == "eduassets-latex", Material.latex_manifest_object.like("latex/%")),
        )
        .order_by(Material.last_synced_at.desc(), Material.id.desc())
    )
    cleaned_ids = [value.strip() for value in material_ids or [] if value.strip()]
    if cleaned_ids:
        query = query.filter(Material.material_id.in_(cleaned_ids))
    else:
        query = query.limit(max(1, min(int(limit or 10), 200)))
    return _enqueue_materials(db, user_id, query.all(), mode="refresh_legacy")


def get_codex_skill_job(db: Session, user_id: str, job_id: int) -> CodexSkillJob | None:
    return db.query(CodexSkillJob).filter(CodexSkillJob.id == job_id, CodexSkillJob.user_id == user_id).first()


def cancel_codex_skill_job(job: CodexSkillJob) -> CodexSkillJob:
    if job.status not in {"queued", "running", "dry_run_succeeded"}:
        raise CodexSkillJobError("当前状态不能取消")
    job.status = "cancelled"
    job.finished_at = datetime.utcnow()
    return job


def retry_codex_skill_job(job: CodexSkillJob) -> CodexSkillJob:
    if job.status not in RETRYABLE_STATUSES:
        raise CodexSkillJobError("当前状态不能重试")
    job.status = "queued"
    job.error_message = ""
    job.started_at = None
    job.finished_at = None
    job.result_json = None
    job.staging_dir = None
    job.output_manifest_bucket = None
    job.output_manifest_object = None
    job.attempt_count = int(job.attempt_count or 0) + 1
    return job


def run_dry_run_job(db: Session, job: CodexSkillJob, *, staging_root: Path = DEFAULT_STAGING_ROOT) -> CodexSkillJob:
    if job.status not in {"queued", "running"}:
        raise CodexSkillJobError("只有 queued/running 任务可以 dry-run")
    job.status = "running"
    job.started_at = job.started_at or datetime.utcnow()
    db.flush()

    staging_dir = staging_root / f"job-{job.id}"
    staging_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = staging_dir / "codex_prompt.md"
    manifest_path = staging_dir / "dry_run_manifest.json"
    report_path = staging_dir / "dry_run_report.json"

    prompt_path.write_text(_dry_run_prompt(job), encoding="utf-8")
    manifest = {
        "schema": "luceon-codex-skill-dry-run/v1",
        "job_id": str(job.id),
        "material_id": job.material_id,
        "mode": job.mode,
        "requested_skill": job.requested_skill,
        "skill_version": job.skill_version,
        "source_popo_manifest": job._ref(job.source_popo_manifest_bucket, job.source_popo_manifest_object),
        "baseline_manifest": job._ref(job.baseline_manifest_bucket, job.baseline_manifest_object),
        "published": False,
        "created_at": datetime.utcnow().isoformat(),
        "objects": {
            "prompt": str(prompt_path),
            "dry_run_report": str(report_path),
        },
    }
    report = {
        "status": "dry_run_succeeded",
        "published": False,
        "staging_dir": str(staging_dir),
        "next_step": "Run live Codex skill execution, validate output, then publish to MinIO.",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    job.status = "dry_run_succeeded"
    job.staging_dir = str(staging_dir)
    job.result_json = json.dumps({"manifest": str(manifest_path), **report}, ensure_ascii=False)
    job.finished_at = datetime.utcnow()
    return job


def run_codex_skill_job(
    db: Session,
    job: CodexSkillJob,
    *,
    staging_root: Path = DEFAULT_STAGING_ROOT,
    codex_bin: str = DEFAULT_CODEX_BIN,
    timeout: int | None = None,
) -> CodexSkillJob:
    if job.status not in {"queued", "running", "dry_run_succeeded"}:
        raise CodexSkillJobError("只有 queued/running/dry-run 任务可以执行 Codex")
    material = _job_material(db, job)
    if not material:
        raise CodexSkillJobError("任务对应材料不存在")
    job.status = "running"
    job.started_at = job.started_at or datetime.utcnow()
    staging_dir = _writable_staging_dir(job, staging_root)
    staging_dir.mkdir(parents=True, exist_ok=True)
    job.staging_dir = str(staging_dir)
    input_paths = materialize_job_inputs(job, material, staging_dir)
    prompt_path = staging_dir / "codex_exec_prompt.md"
    stdout_path = staging_dir / "codex_exec_stdout.jsonl"
    final_path = staging_dir / "codex_exec_final.md"
    prompt_path.write_text(_codex_exec_prompt(job, material, staging_dir, input_paths), encoding="utf-8")
    db.flush()

    command = [
        codex_bin,
        "exec",
        "--model",
        DEFAULT_CODEX_MODEL,
        "--json",
        "--dangerously-bypass-approvals-and-sandbox",
        "--cd",
        str(staging_dir),
        "-o",
        str(final_path),
        "-",
    ]
    try:
        completed = subprocess.run(
            command,
            input=prompt_path.read_text(encoding="utf-8"),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        job.status = "failed"
        job.error_message = f"Codex CLI 不存在: {codex_bin}"
        job.finished_at = datetime.utcnow()
        raise CodexSkillJobError(job.error_message) from exc
    except subprocess.TimeoutExpired as exc:
        job.status = "failed"
        job.error_message = "Codex CLI 执行超时"
        job.result_json = json.dumps({"stdout": str(stdout_path), "stderr": str(staging_dir / "codex_exec_stderr.log"), "staging_dir": str(staging_dir)}, ensure_ascii=False)
        job.finished_at = datetime.utcnow()
        raise CodexSkillJobError(job.error_message) from exc
    except KeyboardInterrupt:
        job.status = "failed"
        job.error_message = "Codex CLI 执行被中断"
        job.result_json = json.dumps({"stdout": str(stdout_path), "stderr": str(staging_dir / "codex_exec_stderr.log"), "staging_dir": str(staging_dir)}, ensure_ascii=False)
        job.finished_at = datetime.utcnow()
        raise CodexSkillJobError(job.error_message)
    stdout_path.write_text(completed.stdout or "", encoding="utf-8")
    (staging_dir / "codex_exec_stderr.log").write_text(completed.stderr or "", encoding="utf-8")
    if completed.returncode != 0:
        job.status = "failed"
        job.error_message = f"Codex CLI 执行失败: {completed.returncode}"
        job.result_json = json.dumps({"codex_returncode": completed.returncode, "stdout": str(stdout_path), "stderr": str(staging_dir / "codex_exec_stderr.log")}, ensure_ascii=False)
        job.finished_at = datetime.utcnow()
        raise CodexSkillJobError(job.error_message)
    job.status = "dry_run_succeeded"
    job.result_json = json.dumps(
        {
            **job.result(),
            "codex_returncode": completed.returncode,
            "codex_stdout": str(stdout_path),
            "codex_final": str(final_path),
            "staging_dir": str(staging_dir),
        },
        ensure_ascii=False,
    )
    job.finished_at = datetime.utcnow()
    return job


def publish_staging_job(
    db: Session,
    job: CodexSkillJob,
    *,
    target_bucket: str = DEFAULT_PUBLISH_BUCKET,
    target_prefix: str = DEFAULT_PUBLISH_PREFIX,
    promote: bool = True,
) -> CodexSkillJob:
    if job.status not in {"dry_run_succeeded", "validating"}:
        raise CodexSkillJobError("只有 dry-run 通过的任务可以发布")
    material = _job_material(db, job)
    if not material:
        raise CodexSkillJobError("任务对应材料不存在")
    staging_dir = Path(job.staging_dir or "")
    if not staging_dir.exists() or not staging_dir.is_dir():
        raise CodexSkillJobError("staging 目录不存在")

    compiled_pdf = _first_existing(staging_dir, ["compiled.pdf", "main.pdf", "output.pdf"])
    package_zip = _first_existing(staging_dir, ["refined-overleaf.zip", "latex-project.zip", "package.zip"])
    if not compiled_pdf or not package_zip:
        job.status = "failed"
        job.error_message = "staging 缺少 compiled PDF 或 LaTeX ZIP，不能发布"
        job.finished_at = datetime.utcnow()
        raise CodexSkillJobError(job.error_message)
    if not _has_magic(compiled_pdf, b"%PDF"):
        job.status = "failed"
        job.error_message = "compiled PDF 文件头无效，不能发布"
        job.finished_at = datetime.utcnow()
        raise CodexSkillJobError(job.error_message)
    if not _has_magic(package_zip, b"PK"):
        job.status = "failed"
        job.error_message = "LaTeX ZIP 文件头无效，不能发布"
        job.finished_at = datetime.utcnow()
        raise CodexSkillJobError(job.error_message)
    final_review = _read_json_file(staging_dir / "final_review_report.json")
    compile_report = _read_json_file(staging_dir / "compile_report.json")
    print_quality = build_print_quality_report(staging_dir, compiled_pdf, job.payload())
    (staging_dir / "worker_quality_report.json").write_text(
        json.dumps(print_quality, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    qa = final_review.get("qa") if isinstance(final_review.get("qa"), dict) else {}
    qa_status = str(qa.get("status") or final_review.get("status") or "needs_fix")
    quality_status = "passed" if qa_status == "passed" else "needs_fix"
    validation_error = _candidate_validation_error(final_review, compile_report, print_quality)
    if validation_error:
        job.status = "failed"
        job.error_message = validation_error
        job.result_json = json.dumps(
            {
                **job.result(),
                "published": False,
                "staging_dir": str(staging_dir),
                "validation": {"status": "blocked", "reason": validation_error},
            },
            ensure_ascii=False,
        )
        job.finished_at = datetime.utcnow()
        raise CodexSkillJobError(validation_error)

    job.status = "validating"
    db.flush()
    run_id = f"codex-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-job-{job.id}-attempt-{int(job.attempt_count or 0)}"
    prefix = clean_path(f"{target_prefix}/{job.material_id}/{material.popo_run_id or 'popo'}/{run_id}")
    files = _publishable_files(staging_dir)
    object_map: dict[str, str] = {}
    _ensure_bucket(target_bucket)
    for path in files:
        relative_path = path.relative_to(staging_dir).as_posix()
        object_name = clean_path(f"{prefix}/{relative_path}")
        _put_file(target_bucket, object_name, path)
        object_map[relative_path] = relative_path
        if path.parent == staging_dir:
            object_map[path.name] = relative_path
        else:
            object_map.setdefault(path.name, relative_path)

    manifest = _published_manifest(job, material, run_id, object_map, compiled_pdf, package_zip, final_review, compile_report)
    manifest_object = clean_path(f"{prefix}/manifest.json")
    _put_bytes(target_bucket, manifest_object, json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"), "application/json")
    output = output_from_ref(ObjectRef(target_bucket, manifest_object), material, manifest)
    if not output:
        job.status = "failed"
        job.error_message = "发布 manifest 后无法解析输出"
        job.finished_at = datetime.utcnow()
        raise CodexSkillJobError(job.error_message)

    row = register_elegantbook_output(db, job.user_id, material, output, status="published", quality_status=quality_status)
    row.codex_job_id = job.id
    promoted = bool(promote and quality_status == "passed")
    if promoted:
        promote_material_output(db, row, material)
    db.flush()
    job.status = "published"
    job.output_manifest_bucket = target_bucket
    job.output_manifest_object = manifest_object
    job.result_json = json.dumps(
        {
            **job.result(),
            "status": "published",
            "published": True,
            "promoted": promoted,
            "quality_status": quality_status,
            "manifest": {"bucket": target_bucket, "object": manifest_object},
            "material_output_id": str(row.id),
        },
        ensure_ascii=False,
    )
    job.finished_at = datetime.utcnow()
    return job


def _idempotency_key(user_id: str, material: Material, mode: str, requested_skill: str, skill_version: str) -> str:
    raw = "|".join(
        [
            user_id,
            material.material_id or "",
            material.popo_manifest_bucket or "",
            material.popo_manifest_object or "",
            mode,
            requested_skill,
            skill_version,
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _enqueue_materials(db: Session, user_id: str, materials: list[Material], *, mode: str) -> dict[str, int]:
    created = 0
    existing = 0
    failed = 0
    for material in materials:
        before = (
            db.query(CodexSkillJob)
            .filter(
                CodexSkillJob.user_id == user_id,
                CodexSkillJob.material_id == (material.material_id or ""),
                CodexSkillJob.mode == mode,
                CodexSkillJob.requested_skill == DEFAULT_SKILL_NAME,
                CodexSkillJob.skill_version == DEFAULT_SKILL_VERSION,
            )
            .count()
        )
        try:
            create_codex_skill_job(db, user_id, material, mode=mode)
            after = (
                db.query(CodexSkillJob)
                .filter(
                    CodexSkillJob.user_id == user_id,
                    CodexSkillJob.material_id == (material.material_id or ""),
                    CodexSkillJob.mode == mode,
                    CodexSkillJob.requested_skill == DEFAULT_SKILL_NAME,
                    CodexSkillJob.skill_version == DEFAULT_SKILL_VERSION,
                )
                .count()
            )
            if after > before:
                created += 1
            else:
                existing += 1
        except CodexSkillJobError:
            failed += 1
    db.flush()
    return {"selected": len(materials), "created": created, "existing": existing, "failed": failed}


def _dry_run_prompt(job: CodexSkillJob) -> str:
    return "\n".join(
        [
            f"# Codex Skill Dry Run: job {job.id}",
            "",
            f"- material_id: {job.material_id}",
            f"- mode: {job.mode}",
            f"- skill: {job.requested_skill}",
            f"- skill_version: {job.skill_version}",
            f"- source_popo_manifest: {job.source_popo_manifest_bucket}/{job.source_popo_manifest_object}",
            f"- baseline_manifest: {job.baseline_manifest_bucket or ''}/{job.baseline_manifest_object or ''}",
            "",
            "Dry-run only. Do not publish to MinIO from this staging directory.",
        ]
    )


def materialize_job_inputs(job: CodexSkillJob, material: Material, staging_dir: Path) -> dict[str, str]:
    inputs_dir = staging_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    rows: dict[str, str] = {}
    popo_manifest = _materialize_manifest_with_objects(
        job.source_popo_manifest_bucket,
        job.source_popo_manifest_object,
        inputs_dir / "popo",
        keys=("document_tree", "document_tree_txt", "popo_raw", "label_normalization", "inference", "full_tree"),
    )
    rows.update({f"popo_{key}": value for key, value in popo_manifest.items()})
    legacy_manifest = _materialize_manifest_with_objects(
        job.baseline_manifest_bucket,
        job.baseline_manifest_object,
        inputs_dir / "legacy",
        keys=("compiled_pdf", "package_zip", "main_tex", "main_fallback_tex", "compile_report", "final_review_report_json", "clean_markdown", "run_state"),
    )
    rows.update({f"legacy_{key}": value for key, value in legacy_manifest.items()})
    if material.input_bucket and material.input_object:
        path = _download_ref(material.input_bucket, material.input_object, inputs_dir / "source" / Path(material.input_object).name)
        if path:
            rows["source_pdf"] = str(path)
    return rows


def _materialize_manifest_with_objects(bucket: str | None, object_name: str | None, output_dir: Path, keys: tuple[str, ...]) -> dict[str, str]:
    rows: dict[str, str] = {}
    if not bucket or not object_name:
        return rows
    manifest_path = _download_ref(bucket, object_name, output_dir / "manifest.json")
    if manifest_path:
        rows["manifest"] = str(manifest_path)
    manifest = _read_json_file(manifest_path) if manifest_path else {}
    objects = manifest.get("objects") if isinstance(manifest.get("objects"), dict) else {}
    for key in keys:
        ref = _object_value_ref(bucket, object_name, objects.get(key))
        if not ref:
            continue
        suffix = Path(ref.object).suffix
        local_name = f"{key}{suffix}" if suffix else key
        local_path = _download_ref(ref.bucket, ref.object, output_dir / local_name)
        if local_path:
            rows[key] = str(local_path)
    return rows


def _object_value_ref(default_bucket: str, manifest_object: str, value: Any) -> ObjectRef | None:
    bucket = default_bucket
    raw = ""
    if isinstance(value, dict):
        bucket = str(value.get("bucket") or default_bucket)
        raw = clean_path(value.get("object") or value.get("key") or value.get("path"))
    elif isinstance(value, str):
        raw = clean_path(value)
    if not raw or raw.endswith("/"):
        return None
    if "/" not in raw:
        prefix = manifest_object.rsplit("/", 1)[0] + "/" if "/" in manifest_object else ""
        raw = clean_path(f"{prefix}{raw}")
    return ObjectRef(bucket, raw)


def _download_ref(bucket: str, object_name: str, path: Path) -> Path | None:
    try:
        data = read_object(bucket, object_name)
    except Exception:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _codex_exec_prompt(job: CodexSkillJob, material: Material, staging_dir: Path, input_paths: dict[str, str]) -> str:
    input_lines = [f"- {key}: {value}" for key, value in sorted(input_paths.items())]
    return "\n".join(
        [
            "Use $luceon-popo-to-refined-elegantbook in produce-selected mode.",
            "",
            "You are producing artifacts for LuceonWeb. Write all local outputs directly into this staging directory:",
            str(staging_dir),
            "",
            "Required successful local outputs before you finish:",
            "- compiled.pdf",
            "- refined-overleaf.zip",
            "- main.tex",
            "- main-fallback.tex",
            "- compile_report.json",
            "- latex_polish_report.md",
            "- latex_polish_report.json",
            "- final_review_report.md",
            "- final_review_report.json",
            "- render_review.md",
            "- render_review.json",
            "- decision_log.json",
            "- model_calls.jsonl",
            "- run_state.json",
            "- source_trace.json",
            "- source_outline_ledger.json",
            "- page_review.md",
            "- page_review.json",
            "",
            "Run the actual stage modules from $luceon-popo-to-refined-elegantbook: source-to-clean-material or the project cleaner, cleanlatex-to-elegantbook, and refine-elegantbook-latex. Do not replace these stages with an ad hoc script.",
            "For compilation, invoke refine_elegantbook_latex.py with --compile --render. The project host may not have TeX in PATH; use the existing Overleaf Community Edition container sharelatex, whose TeX Live 2025 toolchain is the required compiler.",
            "Do not create or use make_luceon_candidate.py. Do not use PyMuPDF, ReportLab, HTML-to-PDF, or plain-text rendering as a substitute for a compiled ElegantBook PDF.",
            "Preserve source images and figures: materialize the image assets into the LaTeX project and reference them from chapters. Never replace missing images with textual descriptions just to make a PDF.",
            "The final compile_report.json must report status=succeeded and a real engine containing xelatex, lualatex, or pdflatex. final_review_report.json must report qa.status=passed with no hard_blockers before you finish.",
            "Only after those gates pass, copy the real compiled PDF and ZIP to the staging root as compiled.pdf and refined-overleaf.zip, then write the required root reports.",
            "If the stages or real TeX compilation cannot complete, write run_state.json and final_review_report.json with qa.status=blocked and explain why. Do not publish a needs_fix candidate as a finished refinement.",
            "",
            "This output is a classroom exercise workbook. Passing compilation is not delivery acceptance. The PDF must be directly printable for teaching and student practice.",
            "Before semantic annotation, inspect the source PDF table of contents and recurring material metadata. Write source_outline_ledger.json as {items:[{index,title,source_pages,output_chapter,status:'mapped'}]} with every source teaching item mapped exactly once. A source page may contain multiple teaching items.",
            "Do not continue when metadata/title groups outnumber clean Markdown headings. Repair the clean Markdown outline first so no later material remains as an unstructured tail after the last chapter.",
            "Remove QR-code images, scan-code prompts, subscription/audio/video access wording, repeated publisher running headers/footers, test strings, and OCR placeholder runs from the printable edition.",
            "Keep content-bearing figures, but suppress inferred AI descriptions such as '(no text or symbols visible)' unless equivalent caption text is visibly present in the source.",
            "Never place a figure between two fragments of the same sentence. Move it to the preceding paragraph boundary, preserve the joined sentence text, and use a source-appropriate width instead of forcing a dominant image.",
            "Keep chapter metadata together: 语篇类型, 词数, 难度, 范围/范畴, and 教材链接 belong in one aligned Reading profile box. Format compact vocabulary lists as term/meaning rows, emphasize the source example sentence in Language tips, and keep simple word banks in a bordered row.",
            "Preserve each question stem, blank, table, image, and A/B/C option identity. Count A/B/C option rows in the CleanLaTeX input and in the refined project; the refined counts must never decrease. Keep malformed but source-backed options for repair instead of deleting an uncertain matrix. Never convert every option or exercise line into repeated item number '1.'.",
            "Run the 03.5 refiner with --print-layout classroom --answer-density workbook. Translation, dialogue completion, explanation, table-completion, note-taking, and other written-production tasks need practical answer room.",
            "Never disable, relax, redefine, or empty \\clearpage or \\cleardoublepage. Doing so breaks ElegantBook chapter boundaries and can prevent the final buffered pages from reaching the PDF. Compact layout only with safe image sizing, ordinary spacing, and \\Needspace guards.",
            "A chapter heading must not overlap any preceding body line and must not begin in the final 42 percent of a page. Use standard chapter page breaks, or for a compact short-unit workbook use titlesec's straight chapter class with positive title spacing plus a per-chapter \\Needspace guard; never trade content completeness for a page-count target.",
            "Remove visible Markdown image syntax and editorial alt text such as ![Illustration ...] or 'Illustration of ...'. Keep the real source image when it exists, without printing its workflow description.",
            "Do not enlarge low-resolution raster photos into a dominant half-page image. Keep informational diagrams legible, but cap decorative or low-resolution photos using both width and height with keepaspectratio.",
            "Verify the final substantive tail of every source teaching item appears in the compiled PDF. Counting chapter headings is insufficient; a truncated last chapter is a hard blocker.",
            "Avoid interior orphan pages and half-empty spill pages caused by one short fragment, footer, or answer token. Reflow related exercise content while preserving source order.",
            "Render every output PDF page for final review, not only representative samples. Store those PNGs under 04-final-review/rendered-all/ and write page_review.json as {pdf_sha256,page_count,pages:[{page,image,status,findings}]}. The hash and page count must describe the final root compiled.pdf, every image must be a real render, and every page must pass before final QA can pass.",
            "The Worker performs a second independent print-quality audit and will reject incomplete outline coverage or source tails, lost A/B/C options, missing cloze numbers, unsafe metadata lists, missing local translation answer space, unsafe page-flush suppression, chapter collisions or late starts, stale all-page review evidence, visible Markdown/editorial residue, QR/access residue, AI captions, broken numbering, ungrouped A/B/C choice matrices, OCR runs, missing answer space, low-resolution image enlargement, suspicious page inflation, and orphan pages.",
            "If worker_quality_report.json already exists, this is a quality-repair pass. Read every hard_blocker and its page list first, reuse the already-correct stages, repair the copied LaTeX project, recompile, rerender all pages, and replace the root reports. Do not rerun stable upstream work unless a blocker is owned there.",
            "If deterministic_repair_report.json exists with status=changed, its project_dir is the only allowed 03.5 repair baseline. The host Worker has already regrouped strict option matrices, capped low-resolution images, or removed duplicate image-label OCR while protecting chapter and exercise-heading counts and never reducing answer surfaces. Do not run a broad polish pass over that project. Compile it, inspect every newly rendered page, and package that exact project.",
            "For broken_list_numbering, merge adjacent one-item enumerate environments into real sequential lists and rebuild cloze option matrices so each question keeps its A/B/C choices together. For ocr_placeholder_run, normalize malformed escaped blank tokens into ordinary answer rules without changing the surrounding words.",
            "For unsafe_page_flush_suppression, restore the standard page-flush commands before recompiling. For chapter_heading_collision or late_chapter_start, repair chapter boundaries with real page breaks or \\Needspace. For source_tail_anchor_missing, restore the missing source-backed body before any layout tuning.",
            "Do not mark every rendered page passed mechanically. A page record may pass only after checking its actual image for useful content density, correct numbering, legible text, retained question structure, and practical writing space.",
            "",
            "Do not publish to MinIO. Do not edit the LuceonWeb repo. Do not overwrite legacy outputs.",
            "Use the local input files below. Do not search the whole filesystem for this material.",
            *input_lines,
            "If you cannot produce a valid compiled PDF and Overleaf ZIP, write run_state.json and final_review_report.json with qa.status=blocked and explain why.",
            "",
            f"material_pk: {material.id}",
            f"material_id: {job.material_id}",
            f"popo_run_id: {material.popo_run_id or ''}",
            f"source_popo_manifest: {job.source_popo_manifest_bucket}/{job.source_popo_manifest_object}",
            f"legacy_baseline_manifest: {job.baseline_manifest_bucket or ''}/{job.baseline_manifest_object or ''}",
            f"job_payload: {json.dumps(job.payload(), ensure_ascii=False)}",
        ]
    )


def _job_material(db: Session, job: CodexSkillJob) -> Material | None:
    query = db.query(Material).filter(Material.user_id == job.user_id)
    if job.material_pk:
        material = query.filter(Material.id == job.material_pk).first()
        if material:
            return material
    return query.filter(Material.material_id == job.material_id).order_by(Material.id.desc()).first()


def _writable_staging_dir(job: CodexSkillJob, staging_root: Path) -> Path:
    if not job.staging_dir:
        return staging_root / f"job-{job.id}"
    current = Path(job.staging_dir)
    try:
        current.mkdir(parents=True, exist_ok=True)
        probe = current / ".write-test"
        probe.write_text("", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return current
    except OSError:
        return staging_root / f"job-{job.id}"


def _first_existing(root: Path, names: list[str]) -> Path | None:
    for name in names:
        path = root / name
        if path.exists() and path.is_file():
            return path
    return None


def _has_magic(path: Path, magic: bytes) -> bool:
    try:
        with path.open("rb") as stream:
            return stream.read(len(magic)) == magic
    except OSError:
        return False


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _candidate_validation_error(
    final_review: dict[str, Any],
    compile_report: dict[str, Any],
    print_quality: dict[str, Any] | None = None,
) -> str:
    """Keep existence-only or text-rendered candidates out of the published catalog."""
    qa = final_review.get("qa") if isinstance(final_review.get("qa"), dict) else {}
    qa_status = str(qa.get("status") or final_review.get("status") or "")
    if qa_status != "passed":
        return f"精修候选 QA 未通过，禁止发布: {qa_status or 'unknown'}"
    hard_blockers = qa.get("hard_blockers")
    if isinstance(hard_blockers, list) and hard_blockers:
        return "精修候选存在硬阻塞项，禁止发布"
    compile_status = str(compile_report.get("status") or "")
    if compile_status not in {"succeeded", "passed"}:
        return f"精修候选未通过真实 TeX 编译，禁止发布: {compile_status or 'unknown'}"
    engine = str(compile_report.get("engine") or "").lower()
    if not any(name in engine for name in ("xelatex", "lualatex", "pdflatex")):
        return f"编译引擎不是 TeX 引擎，禁止发布: {engine or 'unknown'}"
    if compile_report.get("tex_engine_available") is False:
        return "报告明确标记 TeX 引擎不可用，禁止发布"
    print_quality = print_quality or {}
    if str(print_quality.get("status") or "") != "passed":
        blockers = print_quality.get("hard_blockers") if isinstance(print_quality.get("hard_blockers"), list) else []
        codes = [str(row.get("code") or "") for row in blockers if isinstance(row, dict)]
        summary = ", ".join(code for code in codes if code) or "unknown"
        return f"逐页打印质量审查未通过，禁止发布: {summary}"
    return ""


def _publishable_files(root: Path) -> list[Path]:
    allowed_suffixes = {".pdf", ".zip", ".json", ".md", ".tex", ".sty", ".cls", ".bib", ".png", ".jpg", ".jpeg"}
    excluded_root_names = {"codex_exec_final.md", "codex_exec_prompt.md", "manifest.json"}
    rows = {
        path
        for path in root.iterdir()
        if path.is_file()
        and path.name not in excluded_root_names
        and path.suffix.lower() in allowed_suffixes
    }
    for directory_name in ("chapters", "images"):
        directory = root / directory_name
        if not directory.is_dir():
            continue
        rows.update(
            path
            for path in directory.rglob("*")
            if path.is_file() and path.suffix.lower() in allowed_suffixes
        )
    page_review = _read_json_file(root / "page_review.json")
    review_rows = page_review.get("pages") if isinstance(page_review.get("pages"), list) else []
    resolved_root = root.resolve()
    for row in review_rows:
        if not isinstance(row, dict):
            continue
        value = str(row.get("image") or "").strip()
        if not value:
            continue
        path = Path(value)
        path = path if path.is_absolute() else root / path
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(resolved_root)
        except (OSError, ValueError):
            continue
        if resolved.is_file() and resolved.suffix.lower() in allowed_suffixes:
            rows.add(resolved)
    return sorted(rows)


def _ensure_bucket(bucket: str) -> None:
    try:
        exists = minio_client.bucket_exists(bucket)
    except Exception:
        exists = True
    if not exists:
        minio_client.make_bucket(bucket)


def _put_file(bucket: str, object_name: str, path: Path) -> None:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with path.open("rb") as stream:
        minio_client.put_object(bucket, object_name, stream, length=path.stat().st_size, content_type=content_type)


def _put_bytes(bucket: str, object_name: str, data: bytes, content_type: str) -> None:
    minio_client.put_object(bucket, object_name, BytesIO(data), length=len(data), content_type=content_type)


def _published_manifest(
    job: CodexSkillJob,
    material: Material,
    run_id: str,
    object_map: dict[str, str],
    compiled_pdf: Path,
    package_zip: Path,
    final_review: dict[str, Any],
    compile_report: dict[str, Any],
) -> dict[str, Any]:
    now = datetime.utcnow().isoformat()
    final_qa = final_review.get("qa") if isinstance(final_review.get("qa"), dict) else {}
    qa_status = str(final_qa.get("status") or final_review.get("status") or "needs_fix")
    hard_blockers = final_qa.get("hard_blockers") if isinstance(final_qa.get("hard_blockers"), list) else []
    review_status = str(final_qa.get("review_status") or qa_status)
    compile_pages = compile_report.get("pages") if isinstance(compile_report.get("pages"), int) else None
    compile_engine = str(compile_report.get("engine") or "codex-worker")
    return {
        "schema": "luceon-codex-elegantbook/v1",
        "stage": "elegantbook",
        "origin": "codex_refined",
        "material_id": job.material_id,
        "popo_run_id": material.popo_run_id or "",
        "codex_run_id": run_id,
        "job_id": str(job.id),
        "skill_name": job.requested_skill,
        "skill_version": job.skill_version,
        "created_at": now,
        "updated_at": now,
        "source": {
            "input_pdf": job._ref(material.input_bucket, material.input_object),
            "mineru_manifest": job._ref(material.mineru_manifest_bucket, material.mineru_manifest_object),
            "popo_manifest": job._ref(job.source_popo_manifest_bucket, job.source_popo_manifest_object),
            "legacy_latex_manifest": job._ref(job.baseline_manifest_bucket, job.baseline_manifest_object),
        },
        "compile": {"status": "succeeded", "engine": compile_engine, "pages": compile_pages},
        "qa": {"status": qa_status, "hard_blockers": hard_blockers, "review_status": review_status},
        "stages": [{"skill": job.requested_skill, "status": "passed", "mode": job.mode}],
        "objects": _manifest_objects(object_map, compiled_pdf, package_zip),
    }


def _manifest_objects(object_map: dict[str, str], compiled_pdf: Path, package_zip: Path) -> dict[str, str]:
    objects: dict[str, str] = {
        "compiled_pdf": object_map.get(compiled_pdf.name, compiled_pdf.name),
        "refined_overleaf_zip": object_map.get(package_zip.name, package_zip.name),
        "package_zip": object_map.get(package_zip.name, package_zip.name),
    }
    optional_files = {
        "main_tex": "main.tex",
        "main_fallback_tex": "main-fallback.tex",
        "compile_report": "compile_report.json",
        "latex_polish_report": "latex_polish_report.md",
        "latex_polish_report_json": "latex_polish_report.json",
        "final_review_report": "final_review_report.md",
        "final_review_report_json": "final_review_report.json",
        "render_review": "render_review.md",
        "render_review_json": "render_review.json",
        "decision_log": "decision_log.json",
        "model_calls": "model_calls.jsonl",
        "run_state": "run_state.json",
        "source_trace": "source_trace.json",
        "source_outline_ledger": "source_outline_ledger.json",
        "page_review": "page_review.md",
        "page_review_json": "page_review.json",
        "worker_quality_report": "worker_quality_report.json",
        "deterministic_repair_report": "deterministic_repair_report.json",
    }
    for key, filename in optional_files.items():
        if filename in object_map:
            objects[key] = object_map[filename]
    if "run_state" not in objects and "dry_run_report.json" in object_map:
        objects["run_state"] = object_map["dry_run_report.json"]
    if any(path.startswith("chapters/") for path in object_map.values()):
        objects["chapters_dir"] = "chapters/"
    if any(path.startswith("images/") for path in object_map.values()):
        objects["images_dir"] = "images/"
    return objects
