#!/usr/bin/env python3
"""Import legacy four-skill selfloop outputs into the Luceon LaTeX stage.

This is a bridge for already-finished selfloop runs. It does not rerun the
skills. It publishes compatibility artifacts to eduassets-latex and advances
matching material rows to latex_done.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
BACKEND_ROOT = SCRIPT_PATH.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


DEFAULT_DB = REPO_ROOT / "runtime" / "backend" / "mineru.db"
DEFAULT_RUN_ROOT = (
    Path("/Users/concm/prod_workspace/minerupopo-raw-clean-elegantbook")
    / "work"
    / "selfloop"
    / "runs"
    / "run-20260704-full-123"
)
LATEX_BUCKET = "eduassets-latex"
LATEX_SCHEMA = "luceon-latex-material/v1"
LATEX_OBJECTS = {
    "main_tex": "main.tex",
    "main_fallback_tex": "main-fallback.tex",
    "reference_bib": "reference.bib",
    "chapters_dir": "chapters/",
    "images_dir": "images/",
    "compiled_pdf": "compiled.pdf",
    "package_zip": "latex-project.zip",
    "compile_report": "compile_report.json",
    "outline_review": "outline_review.json",
    "safe_fixes_report": "safe_fixes_report.json",
    "final_review_report": "final_review_report.md",
    "final_review_report_json": "final_review_report.json",
    "clean_markdown": "clean.md",
    "decision_log": "decision_log.json",
    "model_calls": "model_calls.jsonl",
    "qa_report": "qa_report.md",
    "render_review": "render_review.md",
    "render_review_json": "render_review.json",
    "run_state": "run_state.json",
}
WORKER_STAGE_IDS = (
    "materialize",
    "clean_markdown",
    "outline_review",
    "safe_fixes",
    "semantic_annotate",
    "cleanlatex_bridge",
    "elegantbook",
    "compile",
    "render_review",
    "final_ai_review",
    "publish",
)


@dataclass(frozen=True)
class MaterialRow:
    id: int
    user_id: str
    material_id: str
    title: str
    filename: str
    input_bucket: str
    input_object: str
    mineru_manifest_bucket: str
    mineru_manifest_object: str
    mineru_run_id: str
    popo_manifest_bucket: str
    popo_manifest_object: str
    popo_run_id: str
    review_asset_id: int | None
    stage_status: str


@dataclass(frozen=True)
class UploadItem:
    relative_object: str
    path: Path | None = None
    data: bytes | None = None
    content_type: str = "application/octet-stream"


def utc_now() -> str:
    return datetime.utcnow().isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_bytes(data: Any) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def clean_object(value: str) -> str:
    parts = [part for part in value.replace("\\", "/").lstrip("/").split("/") if part and part not in {".", ".."}]
    return "/".join(parts)


def workspace_root_for_run(run_root: Path) -> Path:
    try:
        return run_root.parents[3]
    except IndexError:
        return run_root


def legacy_path(run_root: Path, value: str | None) -> Path:
    raw = str(value or "").strip()
    if not raw:
        return run_root / "__missing__"
    path = Path(raw)
    if path.is_absolute():
        return path
    workspace_candidate = workspace_root_for_run(run_root) / path
    if workspace_candidate.exists():
        return workspace_candidate
    return run_root / path


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists() and path.is_file():
            return path
    return None


def load_legacy_samples(run_root: Path) -> list[dict[str, Any]]:
    basket = read_json(run_root / "sample_basket.json", {})
    state = read_json(run_root / "run_state.json", {})
    visual = read_json(run_root / "visual_review_queue.json", {})
    final = read_json(run_root / "final_all_after_visual_approval_preserve_fix.json", {})

    selected = basket.get("selected") if isinstance(basket, dict) else []
    state_rows = {row.get("sample_id"): row for row in state.get("samples", []) if isinstance(row, dict)}
    visual_rows = {row.get("sample_id"): row for row in visual.get("rows", []) if isinstance(row, dict)}
    final_rows = {row.get("sample_id"): row for row in final.get("results", []) if isinstance(row, dict)}

    samples: list[dict[str, Any]] = []
    for index, row in enumerate(selected or [], start=1):
        if not isinstance(row, dict):
            continue
        sample_id = str(row.get("sample_id") or "").strip()
        if not sample_id:
            continue
        samples.append(
            {
                "index": index,
                "basket": row,
                "state": state_rows.get(sample_id, {}),
                "visual": visual_rows.get(sample_id, {}),
                "final": final_rows.get(sample_id, {}),
            }
        )
    return samples


def sample_id(sample: dict[str, Any]) -> str:
    return str(sample.get("basket", {}).get("sample_id") or "").strip()


def material_id(sample: dict[str, Any]) -> str:
    return str(sample.get("basket", {}).get("pdf_id") or "").strip()


def popo_run_id(sample: dict[str, Any]) -> str:
    return str(sample.get("basket", {}).get("job_id") or "").strip()


def sample_dir(run_root: Path, sample: dict[str, Any]) -> Path:
    return run_root / "samples" / sample_id(sample)


def artifact_paths(run_root: Path, sample: dict[str, Any]) -> dict[str, Path | None]:
    root = sample_dir(run_root, sample)
    body_final = root / "01-intake-outline-clean" / "body-final"
    annotation = root / "02-semantic-annotation" / "annotation"
    render_root = root / "03-elegantbook-render"
    project = render_root / "elegantbook"
    compile_dir = render_root / "compile"
    review = root / "04-final-review"
    review_pack = review / "review_pack"
    return {
        "sample_dir": root,
        "body_final": body_final,
        "annotation": annotation,
        "project": project,
        "compile_dir": compile_dir,
        "review": review,
        "review_pack": review_pack,
        "clean_md": first_existing([body_final / "clean.md"]),
        "main_tex": first_existing([project / "main.tex"]),
        "main_fallback_tex": first_existing([project / "main-fallback.tex", project / "main.tex"]),
        "compiled_pdf": first_existing([project / "main.pdf", compile_dir / "main.pdf"]),
        "package_zip": first_existing([render_root / "elegantbook-overleaf.zip"]),
        "compile_report": first_existing([compile_dir / "overleaf_compile_report.json"]),
        "outline_review": first_existing([body_final / "outline_decision.json", body_final / "popo_outline.json"]),
        "qa_report": first_existing([body_final / "qa_report.md"]),
        "final_review_json": first_existing([review / "final_review_gate.json"]),
        "final_review_md": first_existing([review / "final_review_gate.md"]),
        "automated_review_json": first_existing([review_pack / "automated_review_report.json"]),
        "automated_review_md": first_existing([review_pack / "automated_review_report.md"]),
        "visual_review_json": first_existing([review_pack / "visual_review_status.json"]),
        "contact_sheet": first_existing([review_pack / "contact_sheet.png"]),
        "chapters": project / "chapters" if (project / "chapters").is_dir() else None,
        "images": project / "images" if (project / "images").is_dir() else None,
        "elegantbook_cls": first_existing([project / "elegantbook.cls"]),
        "main_log": first_existing([project / "main.log", compile_dir / "main.log"]),
    }


def rows_for_exact_samples(db_path: Path, user_ids: set[str] | None = None) -> dict[tuple[str, str], list[MaterialRow]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            select id, user_id, material_id, title, filename,
                   input_bucket, input_object,
                   mineru_manifest_bucket, mineru_manifest_object, mineru_run_id,
                   popo_manifest_bucket, popo_manifest_object, popo_run_id,
                   review_asset_id, stage_status
            from materials
            where ignored = 0
              and material_id is not null
              and popo_run_id is not null
            """
        ).fetchall()
    finally:
        conn.close()
    mapped: dict[tuple[str, str], list[MaterialRow]] = {}
    for row in rows:
        user_id = str(row["user_id"] or "")
        if user_ids is not None and user_id not in user_ids:
            continue
        item = MaterialRow(
            id=int(row["id"]),
            user_id=user_id,
            material_id=str(row["material_id"] or ""),
            title=str(row["title"] or ""),
            filename=str(row["filename"] or ""),
            input_bucket=str(row["input_bucket"] or ""),
            input_object=str(row["input_object"] or ""),
            mineru_manifest_bucket=str(row["mineru_manifest_bucket"] or ""),
            mineru_manifest_object=str(row["mineru_manifest_object"] or ""),
            mineru_run_id=str(row["mineru_run_id"] or ""),
            popo_manifest_bucket=str(row["popo_manifest_bucket"] or ""),
            popo_manifest_object=str(row["popo_manifest_object"] or ""),
            popo_run_id=str(row["popo_run_id"] or ""),
            review_asset_id=int(row["review_asset_id"]) if row["review_asset_id"] is not None else None,
            stage_status=str(row["stage_status"] or ""),
        )
        mapped.setdefault((item.material_id, item.popo_run_id), []).append(item)
    return mapped


def representative_material(matches: list[MaterialRow], sample: dict[str, Any]) -> MaterialRow | None:
    if not matches:
        return None
    source_hash = str(sample.get("basket", {}).get("source_hash") or "")
    if source_hash:
        for row in matches:
            if source_hash and source_hash in {row.input_object, row.filename, row.title}:
                return row
    return sorted(matches, key=lambda row: (row.user_id != "1", row.user_id, row.id))[0]


def source_from_material(row: MaterialRow | None, sample: dict[str, Any]) -> dict[str, Any]:
    basket = sample.get("basket", {})
    mineru_run = ""
    mineru_runs = basket.get("mineru_runs")
    if isinstance(mineru_runs, list) and mineru_runs:
        mineru_run = str(mineru_runs[0] or "")
    if row:
        mineru_run = row.mineru_run_id or mineru_run
    popo_prefix = str(basket.get("popo_prefix") or "").strip()
    popo_manifest_object = ""
    if popo_prefix:
        if "/" in popo_prefix:
            popo_manifest_object = popo_prefix.split("/", 1)[1].rstrip("/") + "/manifest.json"
        else:
            popo_manifest_object = popo_prefix.rstrip("/") + "/manifest.json"
    return {
        "input_bucket": row.input_bucket if row else "eduassets-input",
        "input_object": row.input_object if row else "",
        "mineru_bucket": row.mineru_manifest_bucket if row and row.mineru_manifest_bucket else "eduassets-mineru",
        "mineru_manifest": row.mineru_manifest_object if row else "",
        "mineru_run_id": mineru_run,
        "popo_bucket": row.popo_manifest_bucket if row and row.popo_manifest_bucket else "eduassets-minerupopo",
        "popo_manifest": row.popo_manifest_object if row else popo_manifest_object,
        "popo_run_id": popo_run_id(sample),
    }


def read_dict(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def old_stage(sample: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for stage in sample.get("state", {}).get("stages", []) or []:
        if isinstance(stage, dict) and stage.get("id") == stage_id:
            return stage
    return {}


def stage_result(stage_id: str, status: str, message: str, outputs: dict[str, Any] | None = None) -> dict[str, Any]:
    now = utc_now()
    return {
        "stage_id": stage_id,
        "status": status,
        "message": message,
        "started_at": now,
        "finished_at": now,
        "attempts": 1 if status != "skipped" else 0,
        "tool_id": f"legacy_selfloop.{stage_id}",
        "outputs": outputs or {},
        "payload": {"legacy_import": True},
        "error": "",
    }


def build_run_state(sample: dict[str, Any], paths: dict[str, Path | None]) -> dict[str, Any]:
    clean_status = "succeeded" if old_stage(sample, "01-intake-outline-clean").get("status") == "passed" else "failed"
    semantic_status = "succeeded" if old_stage(sample, "02-semantic-annotation").get("status") == "passed" else "failed"
    elegant_status = "succeeded" if old_stage(sample, "03-elegantbook-render").get("status") == "passed" else "failed"
    final_status = "succeeded" if old_stage(sample, "04-final-review").get("status") == "passed" else "failed"
    stages = {
        "materialize": stage_result("materialize", "succeeded", "Imported legacy MinerU-Popo evidence"),
        "clean_markdown": stage_result("clean_markdown", clean_status, "Imported pdf-clean-markdown-rebuild output", {"clean_markdown": "clean.md"}),
        "outline_review": stage_result("outline_review", "succeeded" if paths.get("outline_review") else "skipped", "Imported legacy outline decision"),
        "safe_fixes": stage_result("safe_fixes", "skipped", "No product-side safe fixes were applied during legacy import"),
        "semantic_annotate": stage_result("semantic_annotate", semantic_status, "Imported material-semantic-annotator output"),
        "cleanlatex_bridge": stage_result("cleanlatex_bridge", elegant_status, "Imported legacy CleanLaTeX bridge output"),
        "elegantbook": stage_result("elegantbook", elegant_status, "Imported cleanlatex-to-elegantbook project"),
        "compile": stage_result("compile", "succeeded" if paths.get("compiled_pdf") else "failed", "Imported legacy compiled PDF", {"compiled_pdf": "compiled.pdf"}),
        "render_review": stage_result("render_review", final_status, "Imported legacy rendered visual review"),
        "final_ai_review": stage_result("final_ai_review", final_status, "Imported finished-textbook-final-review report"),
        "publish": stage_result("publish", "succeeded", "Published legacy artifacts to eduassets-latex"),
    }
    return {
        "schema": "luceon-latex-run-state/v1",
        "updated_at": utc_now(),
        "stage_order": list(WORKER_STAGE_IDS),
        "stages": stages,
    }


def build_compile_report(sample: dict[str, Any], paths: dict[str, Path | None]) -> dict[str, Any]:
    old = read_dict(paths.get("compile_report"))
    final_status = str(sample.get("visual", {}).get("final_stage_status") or sample.get("state", {}).get("status") or "")
    success = bool(old.get("success")) or bool(paths.get("compiled_pdf")) and final_status in {"passed", ""}
    report = {
        "schema": "luceon-latex-compile-report/v1",
        "status": "succeeded" if success else "legacy_imported",
        "engine": old.get("engine") or old.get("container") or "legacy-selfloop-overleaf",
        "compiled_pdf": "compiled.pdf",
        "legacy_selfloop": {
            "sample_id": sample_id(sample),
            "source_report": str(paths.get("compile_report") or ""),
            "source_pdf": str(paths.get("compiled_pdf") or ""),
        },
    }
    if old:
        report["legacy_overleaf_report"] = old
    return report


def build_render_review(sample: dict[str, Any], paths: dict[str, Path | None]) -> dict[str, Any]:
    automated = read_dict(paths.get("automated_review_json"))
    visual = sample.get("visual", {}) if isinstance(sample.get("visual"), dict) else {}
    pdfinfo = automated.get("pdfinfo") if isinstance(automated.get("pdfinfo"), dict) else {}
    page_count = int(pdfinfo.get("pages") or 0)
    rendered_pages = []
    for raw in visual.get("rendered_pages", []) or []:
        page_name = Path(raw).name
        page_no = 0
        stem = Path(page_name).stem
        if stem.startswith("page-"):
            try:
                page_no = int(stem.split("-", 1)[1])
            except ValueError:
                page_no = 0
        rendered_pages.append({"page": page_no, "image": f"render-pages/{page_name}", "blank": False})
    status = "pass" if visual.get("visual_status") == "agent_approved" or visual.get("final_stage_status") == "passed" else "needs_source_confirmation"
    return {
        "schema": "luceon-latex-render-review/v1",
        "status": status,
        "compiled_pdf": "compiled.pdf",
        "page_count": page_count,
        "representative_pages": rendered_pages,
        "blank_pages": [],
        "failed_pages": [],
        "errors": [],
        "legacy_selfloop": {
            "sample_id": sample_id(sample),
            "visual_status": visual.get("visual_status") or "",
            "final_stage_status": visual.get("final_stage_status") or "",
            "contact_sheet": "review_pack/contact_sheet.png" if paths.get("contact_sheet") else "",
        },
    }


def render_review_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# Render Review",
        "",
        f"- Status: {review.get('status')}",
        f"- Compiled PDF: {review.get('compiled_pdf')}",
        f"- Page count: {review.get('page_count')}",
        f"- Legacy visual status: {review.get('legacy_selfloop', {}).get('visual_status')}",
        f"- Legacy final stage: {review.get('legacy_selfloop', {}).get('final_stage_status')}",
        "",
        "## Representative Pages",
    ]
    pages = review.get("representative_pages") or []
    if pages:
        lines.extend(f"- Page {item.get('page')}: {item.get('image')}" for item in pages)
    else:
        lines.append("- None recorded")
    return "\n".join(lines) + "\n"


def build_final_review_report(sample: dict[str, Any], paths: dict[str, Path | None], compile_report: dict[str, Any], render_review: dict[str, Any]) -> dict[str, Any]:
    final_gate = read_dict(paths.get("final_review_json"))
    accepted = bool(sample.get("state", {}).get("accepted")) or sample.get("state", {}).get("status") == "passed"
    conclusion = "pass" if accepted and render_review.get("status") == "pass" else "needs_source_confirmation"
    return {
        "schema": "luceon-latex-final-review/v1",
        "conclusion": conclusion,
        "material": sample.get("basket", {}).get("source_name") or sample_id(sample),
        "material_id": material_id(sample),
        "popo_run_id": popo_run_id(sample),
        "mineru_run_id": (sample.get("basket", {}).get("mineru_runs") or [""])[0],
        "compile_status": compile_report.get("status"),
        "render_status": render_review.get("status"),
        "blockers": [],
        "needs_source_confirmation": [] if conclusion == "pass" else ["legacy_import_requires_manual_compare"],
        "legacy_selfloop": {
            "sample_id": sample_id(sample),
            "source_report": str(paths.get("final_review_json") or ""),
            "final_gate": final_gate,
        },
    }


def final_review_markdown(report: dict[str, Any], old_md: Path | None) -> str:
    lines = [
        "# LaTeX Node Internal Final Review",
        "",
        f"- Conclusion: {report.get('conclusion')}",
        f"- Material: {report.get('material')}",
        f"- Material ID: {report.get('material_id')}",
        f"- Popo run: {report.get('popo_run_id')}",
        f"- Compile status: {report.get('compile_status')}",
        f"- Render status: {report.get('render_status')}",
        "",
        "Imported from the legacy four-skill selfloop run. Human product review should use the PDF compare workbench.",
    ]
    if old_md and old_md.exists():
        lines.extend(["", "## Legacy Gate Report", "", old_md.read_text(encoding="utf-8", errors="replace")])
    return "\n".join(lines).rstrip() + "\n"


def build_outline_review(paths: dict[str, Path | None]) -> dict[str, Any]:
    old = read_dict(paths.get("outline_review"))
    return {
        "schema": "luceon-latex-outline-review/v1",
        "mode": "legacy_selfloop_import",
        "status": "succeeded" if old else "skipped",
        "suggestions": [],
        "error": "",
        "legacy_outline_decision": old,
    }


def build_safe_fixes_report() -> dict[str, Any]:
    return {
        "schema": "luceon-latex-safe-fixes/v1",
        "mode": "legacy_selfloop_import",
        "applied_count": 0,
        "rejected_count": 0,
        "applied": [],
        "rejected": [],
    }


def build_decision_log(sample: dict[str, Any], matches: list[MaterialRow]) -> dict[str, Any]:
    return {
        "schema": "luceon-latex-worker-evidence/v1",
        "material_label": sample.get("basket", {}).get("source_name") or sample_id(sample),
        "decisions": [
            {
                "stage": "legacy_import",
                "status": "ok",
                "message": "Accepted existing four-skill selfloop outputs without rerunning skills",
                "payload": {
                    "sample_id": sample_id(sample),
                    "material_id": material_id(sample),
                    "popo_run_id": popo_run_id(sample),
                    "matched_material_rows": [row.id for row in matches],
                },
            }
        ],
    }


def qa_report(sample: dict[str, Any], paths: dict[str, Path | None]) -> str:
    lines = [
        "# LaTeX Legacy Import QA",
        "",
        f"- Sample ID: {sample_id(sample)}",
        f"- Material ID: {material_id(sample)}",
        f"- Popo run: {popo_run_id(sample)}",
        f"- Source: {sample.get('basket', {}).get('source_name') or ''}",
        f"- Compiled PDF present: {bool(paths.get('compiled_pdf'))}",
        f"- Main TEX present: {bool(paths.get('main_tex'))}",
        f"- Contact sheet present: {bool(paths.get('contact_sheet'))}",
    ]
    old = paths.get("qa_report")
    if old and old.exists():
        lines.extend(["", "## Legacy Clean QA", "", old.read_text(encoding="utf-8", errors="replace")])
    return "\n".join(lines).rstrip() + "\n"


def build_manifest(
    sample: dict[str, Any],
    row: MaterialRow | None,
    compile_report: dict[str, Any],
    run_state: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": LATEX_SCHEMA,
        "stage": "latex",
        "material_id": material_id(sample),
        "run_id": popo_run_id(sample),
        "created_at": utc_now(),
        "title": (row.title if row else "") or sample.get("basket", {}).get("source_name") or sample_id(sample),
        "filename": (row.filename if row else "") or sample.get("basket", {}).get("source_name") or "",
        "source": source_from_material(row, sample),
        "objects": dict(LATEX_OBJECTS),
        "compile": {"status": compile_report.get("status"), "engine": compile_report.get("engine") or ""},
        "workflow": [
            {"stage_id": stage_id, "contract": "legacy_selfloop_import", "status": "imported"}
            for stage_id in WORKER_STAGE_IDS
        ],
        "run_state": list(run_state.get("stages", {}).values()),
        "tools": [],
        "skills": [
            {"skill": stage.get("skill"), "status": stage.get("status"), "legacy_stage": stage.get("id")}
            for stage in sample.get("state", {}).get("stages", []) or []
            if isinstance(stage, dict)
        ],
        "legacy_selfloop": {
            "schema": "minerupopo-elegantbook-selfloop/run-state/v1",
            "sample_id": sample_id(sample),
            "source_name": sample.get("basket", {}).get("source_name") or "",
            "source_hash": sample.get("basket", {}).get("source_hash") or "",
            "source_pdf_sha256": sample.get("basket", {}).get("source_pdf_sha256") or "",
        },
    }


def add_file(items: list[UploadItem], relative: str, path: Path | None, content_type: str | None = None) -> None:
    if path and path.exists() and path.is_file():
        items.append(
            UploadItem(
                clean_object(relative),
                path=path,
                content_type=content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            )
        )


def add_bytes(items: list[UploadItem], relative: str, data: bytes | str, content_type: str) -> None:
    payload = data.encode("utf-8") if isinstance(data, str) else data
    items.append(UploadItem(clean_object(relative), data=payload, content_type=content_type))


def add_tree(items: list[UploadItem], relative_prefix: str, root: Path | None) -> None:
    if not root or not root.exists() or not root.is_dir():
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = clean_object(f"{relative_prefix.rstrip('/')}/{path.relative_to(root).as_posix()}")
        add_file(items, relative, path)


def add_review_pack_pages(run_root: Path, sample: dict[str, Any], items: list[UploadItem]) -> None:
    visual = sample.get("visual", {}) if isinstance(sample.get("visual"), dict) else {}
    seen: set[str] = set()
    for raw in visual.get("rendered_pages", []) or []:
        path = legacy_path(run_root, str(raw))
        if not path.exists() or not path.is_file() or path.name in seen:
            continue
        seen.add(path.name)
        add_file(items, f"render-pages/{path.name}", path, "image/png")


def build_upload_items(run_root: Path, sample: dict[str, Any], matches: list[MaterialRow], include_sources: bool) -> tuple[list[UploadItem], dict[str, Any]]:
    paths = artifact_paths(run_root, sample)
    row = representative_material(matches, sample)
    compile_report = build_compile_report(sample, paths)
    render_review = build_render_review(sample, paths)
    final_review = build_final_review_report(sample, paths, compile_report, render_review)
    run_state = build_run_state(sample, paths)
    manifest = build_manifest(sample, row, compile_report, run_state)

    items: list[UploadItem] = []
    add_file(items, "main.tex", paths.get("main_tex"), "text/x-tex")
    add_file(items, "main-fallback.tex", paths.get("main_fallback_tex"), "text/x-tex")
    add_bytes(items, "reference.bib", "", "text/plain")
    add_file(items, "compiled.pdf", paths.get("compiled_pdf"), "application/pdf")
    add_file(items, "latex-project.zip", paths.get("package_zip"), "application/zip")
    add_file(items, "clean.md", paths.get("clean_md"), "text/markdown")
    add_bytes(items, "compile_report.json", write_json_bytes(compile_report), "application/json")
    add_bytes(items, "outline_review.json", write_json_bytes(build_outline_review(paths)), "application/json")
    add_bytes(items, "safe_fixes_report.json", write_json_bytes(build_safe_fixes_report()), "application/json")
    add_bytes(items, "final_review_report.json", write_json_bytes(final_review), "application/json")
    add_bytes(items, "final_review_report.md", final_review_markdown(final_review, paths.get("final_review_md")), "text/markdown")
    add_bytes(items, "decision_log.json", write_json_bytes(build_decision_log(sample, matches)), "application/json")
    add_bytes(items, "model_calls.jsonl", b"", "application/jsonl")
    add_bytes(items, "qa_report.md", qa_report(sample, paths), "text/markdown")
    add_bytes(items, "render_review.json", write_json_bytes(render_review), "application/json")
    add_bytes(items, "render_review.md", render_review_markdown(render_review), "text/markdown")
    add_bytes(items, "run_state.json", write_json_bytes(run_state), "application/json")
    add_bytes(items, "manifest.json", write_json_bytes(manifest), "application/json")
    add_file(items, "legacy/elegantbook.cls", paths.get("elegantbook_cls"))
    add_file(items, "legacy/main.log", paths.get("main_log"), "text/plain")
    add_file(items, "review_pack/contact_sheet.png", paths.get("contact_sheet"), "image/png")
    add_file(items, "review_pack/visual_review_status.json", paths.get("visual_review_json"), "application/json")
    add_file(items, "review_pack/automated_review_report.json", paths.get("automated_review_json"), "application/json")
    add_file(items, "review_pack/automated_review_report.md", paths.get("automated_review_md"), "text/markdown")
    add_review_pack_pages(run_root, sample, items)
    if include_sources:
        add_tree(items, "chapters", paths.get("chapters"))
        add_tree(items, "images", paths.get("images"))

    summary = {
        "sample_id": sample_id(sample),
        "material_id": material_id(sample),
        "popo_run_id": popo_run_id(sample),
        "prefix": latex_prefix(sample),
        "matched_material_rows": [row.id for row in matches],
        "matched_users": sorted({row.user_id for row in matches}),
        "upload_items": len(items),
        "upload_bytes": sum((item.path.stat().st_size if item.path else len(item.data or b"")) for item in items),
        "compiled_pdf": bool(paths.get("compiled_pdf")),
        "main_tex": bool(paths.get("main_tex")),
        "package_zip": bool(paths.get("package_zip")),
        "contact_sheet": bool(paths.get("contact_sheet")),
        "status": sample.get("state", {}).get("status") or "",
        "accepted": bool(sample.get("state", {}).get("accepted")),
    }
    return items, summary


def latex_prefix(sample: dict[str, Any]) -> str:
    return f"latex/{material_id(sample)}/{popo_run_id(sample)}/"


def import_report(
    db_path: Path,
    run_root: Path,
    user_ids: set[str] | None,
    include_sources: bool,
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[MaterialRow]]]:
    rows_by_key = rows_for_exact_samples(db_path, user_ids=user_ids)
    report = []
    for sample in load_legacy_samples(run_root):
        key = (material_id(sample), popo_run_id(sample))
        matches = rows_by_key.get(key, [])
        items, summary = build_upload_items(run_root, sample, matches, include_sources=include_sources)
        missing_required = []
        for required in ("manifest.json", "compiled.pdf", "main.tex", "latex-project.zip", "compile_report.json"):
            if not any(item.relative_object == required for item in items):
                missing_required.append(required)
        summary["missing_required"] = missing_required
        summary["will_update_db"] = bool(matches and not missing_required)
        report.append(summary)
    return report, rows_by_key


def ensure_bucket(client: Any, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def object_exists(client: Any, bucket: str, object_name: str) -> bool:
    try:
        client.stat_object(bucket, object_name)
        return True
    except Exception:
        return False


def put_item(client: Any, bucket: str, prefix: str, item: UploadItem, overwrite: bool) -> bool:
    object_name = clean_object(prefix + item.relative_object)
    if not overwrite and object_exists(client, bucket, object_name):
        return False
    if item.path:
        fput_object = getattr(client, "fput_object", None)
        if fput_object:
            fput_object(bucket, object_name, str(item.path), content_type=item.content_type)
            return True
        data = item.path.read_bytes()
    else:
        data = item.data or b""
    client.put_object(bucket, object_name, BytesIO(data), length=len(data), content_type=item.content_type)
    return True


def backup_db(db_path: Path) -> Path:
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    backup = db_path.with_suffix(db_path.suffix + f".bak-latex-import-{stamp}")
    shutil.copy2(db_path, backup)
    return backup


def update_material_rows(db_path: Path, updates: list[tuple[int, str, str]]) -> int:
    conn = sqlite3.connect(db_path)
    try:
        now = datetime.utcnow().isoformat()
        conn.executemany(
            """
            update materials
               set latex_manifest_bucket = ?,
                   latex_manifest_object = ?,
                   latex_run_id = ?,
                   stage_status = 'latex_done',
                   pipeline_status = 'idle',
                   last_synced_at = ?,
                   updated_at = ?
             where id = ?
            """,
            [(LATEX_BUCKET, manifest_object, run_id, now, now, material_pk) for material_pk, manifest_object, run_id in updates],
        )
        changed = conn.total_changes
        conn.commit()
        return changed
    finally:
        conn.close()


def parse_user_ids(value: str) -> set[str] | None:
    cleaned = value.strip().lower()
    if cleaned in {"", "all", "*"}:
        return None
    return {part.strip() for part in value.split(",") if part.strip()}


def run(args: argparse.Namespace) -> dict[str, Any]:
    db_path = Path(args.db).resolve()
    run_root = Path(args.run_root).resolve()
    user_ids = parse_user_ids(args.user_ids)
    include_sources = not args.core_only
    samples = load_legacy_samples(run_root)
    rows_by_key = rows_for_exact_samples(db_path, user_ids=user_ids)
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, Any]] = []
    updates: list[tuple[int, str, str]] = []
    uploaded_objects = 0
    skipped_objects = 0
    uploaded_bytes = 0
    backup = ""

    client = None
    if args.apply:
        from app.utils.minio_client import minio_client

        client = minio_client
        ensure_bucket(client, LATEX_BUCKET)
        backup = str(backup_db(db_path))

    for index, sample in enumerate(samples, start=1):
        key = (material_id(sample), popo_run_id(sample))
        matches = rows_by_key.get(key, [])
        items, summary = build_upload_items(run_root, sample, matches, include_sources=include_sources)
        missing_required = []
        for required in ("manifest.json", "compiled.pdf", "main.tex", "latex-project.zip", "compile_report.json"):
            if not any(item.relative_object == required for item in items):
                missing_required.append(required)
        summary["missing_required"] = missing_required
        summary["will_update_db"] = bool(matches and not missing_required)

        if args.apply and client and not missing_required:
            prefix = latex_prefix(sample)
            for item in items:
                if put_item(client, LATEX_BUCKET, prefix, item, overwrite=args.overwrite):
                    uploaded_objects += 1
                    uploaded_bytes += item.path.stat().st_size if item.path else len(item.data or b"")
                else:
                    skipped_objects += 1
            manifest_object = f"{prefix}manifest.json"
            for row in matches:
                updates.append((row.id, manifest_object, popo_run_id(sample)))
        summaries.append(summary)
        if args.progress and (index % args.progress == 0 or index == len(samples)):
            print(f"processed {index}/{len(samples)} samples", file=sys.stderr)

    changed_rows = update_material_rows(db_path, updates) if args.apply and updates else 0
    result = {
        "schema": "luceon-legacy-selfloop-latex-import-report/v1",
        "created_at": utc_now(),
        "mode": "apply" if args.apply else "dry_run",
        "db_path": str(db_path),
        "db_backup": backup,
        "run_root": str(run_root),
        "bucket": LATEX_BUCKET,
        "sample_count": len(samples),
        "matched_samples": sum(1 for row in summaries if row["matched_material_rows"]),
        "updatable_samples": sum(1 for row in summaries if row["will_update_db"]),
        "matched_material_rows": sum(len(row["matched_material_rows"]) for row in summaries),
        "changed_material_rows": changed_rows,
        "uploaded_objects": uploaded_objects,
        "skipped_existing_objects": skipped_objects,
        "uploaded_bytes": uploaded_bytes,
        "include_sources": include_sources,
        "rows": summaries,
    }
    report_path = output_dir / ("legacy_selfloop_latex_import_apply.json" if args.apply else "legacy_selfloop_latex_import_dry_run.json")
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["report_path"] = str(report_path)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to mineru.db")
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT), help="Legacy selfloop run root")
    parser.add_argument("--user-ids", default="all", help="Comma-separated user ids to update, or all")
    parser.add_argument("--output-dir", default=str(REPO_ROOT / "runtime" / "uat"), help="Directory for import reports")
    parser.add_argument("--apply", action="store_true", help="Publish to MinIO and update materials")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing MinIO objects")
    parser.add_argument("--core-only", action="store_true", help="Skip chapters/ and images/ object publishing")
    parser.add_argument("--progress", type=int, default=10, help="Print progress every N samples")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run(args)
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
