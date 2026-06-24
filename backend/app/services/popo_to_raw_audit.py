from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.material import Material, PipelineEvent, PipelineRun
from app.services.material_inventory import RAW_BUCKET
from app.services.luceon_review import minio_client


REQUIRED_RAW_FILES = [
    "clean.md",
    "preview.html",
    "manifest.json",
    "qa_report.md",
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


def audit_popo_to_raw_run(db: Session, run: PipelineRun) -> dict[str, Any]:
    if not run or run.mode != "popo2raw":
        return {}

    checks: list[dict[str, str]] = []
    summary = run.summary()
    preflight = as_dict(summary.get("preflight"))
    material_id = str(summary.get("material_id") or preflight.get("material_id") or "")
    published = bool(summary.get("published"))
    outline = as_dict(summary.get("outline_artifacts"))
    decision = as_dict(outline.get("outline_decision"))
    visual = as_dict(outline.get("visual_decisions"))
    apply_report = as_dict(outline.get("outline_apply_report"))
    image_report = as_dict(outline.get("image_closure_report"))
    chunk_report = as_dict(outline.get("chunk_boundary_report"))

    add(checks, "run_status_terminal", run.status in {"succeeded", "failed"}, f"status={run.status} stage={run.current_stage or ''}")
    add(checks, "run_succeeded", run.status == "succeeded", f"status={run.status} error={run.error_message or ''}")
    add(checks, "popo2raw_mode", run.mode == "popo2raw", f"mode={run.mode}")
    add(checks, "material_id_present", bool(material_id), f"material_id={material_id or '<missing>'}")

    if run.status == "succeeded":
        add(checks, "outline_decision_present", bool(decision.get("available")), f"decision_method={decision.get('decision_method')}")
        add(checks, "llm_decision_applied", decision.get("decision_method") == "llm_reviewed_candidate_outline", f"method={decision.get('decision_method')}")
        add(checks, "llm_usage_recorded", bool(as_dict(decision.get("llm")).get("call_count")), f"llm={as_dict(decision.get('llm')).get('provider')}/{as_dict(decision.get('llm')).get('model')}")
        add(checks, "visual_enabled", visual.get("enabled") is True, f"provider={visual.get('provider')} model={visual.get('model')}")
        add(checks, "visual_no_errors", number(visual.get("error_count")) == 0, f"errors={visual.get('error_count')}")
        visual_app = as_dict(decision.get("visual_application"))
        add(
            checks,
            "visual_no_pending_or_conflict",
            number(visual_app.get("pending_count")) == 0 and number(visual_app.get("conflict_count")) == 0,
            f"pending={visual_app.get('pending_count')} conflict={visual_app.get('conflict_count')}",
        )
        add(checks, "flooding_no_unassigned", number(apply_report.get("unassigned_block_count")) == 0, f"unassigned={apply_report.get('unassigned_block_count')}")
        add(
            checks,
            "images_closed",
            number(image_report.get("missing_image_count")) == 0 and number(image_report.get("markdown_refs_not_copied_count")) == 0,
            f"missing={image_report.get('missing_image_count')} uncopied={image_report.get('markdown_refs_not_copied_count')}",
        )
        empty_leaf = number(chunk_report.get("empty_leaf_count"))
        source_empty = number(chunk_report.get("source_empty_chunk_count"))
        add(checks, "empty_leaf_explained", empty_leaf <= source_empty, f"empty_leaf={empty_leaf} source_empty={source_empty}")

    body_final = str(summary.get("body_final") or "")
    if body_final:
        local_body = Path(body_final)
        missing = [name for name in REQUIRED_RAW_FILES if not (local_body / name).exists()]
        has_outline_view = (local_body / "outline-view.html").exists() or (local_body / "outline-anchor-check.html").exists()
        add(checks, "local_required_raw_files", not missing and has_outline_view, f"body_final={local_body} missing={missing} outline_view={has_outline_view}")
    else:
        add_na(checks, "local_required_raw_files", "run summary has no body_final")

    material_rows = (
        db.query(Material)
        .filter(Material.user_id == run.user_id, Material.material_id == material_id)
        .order_by(Material.id.asc())
        .all()
        if material_id
        else []
    )
    add(checks, "material_rows_present", bool(material_rows), f"rows={len(material_rows)}")

    if published:
        raw_manifest = str(summary.get("raw_manifest") or "")
        add(checks, "published_raw_manifest_recorded", bool(raw_manifest), f"raw_manifest={raw_manifest or '<missing>'}")
        raw_rows = [row for row in material_rows if row.raw_manifest_object]
        add(checks, "db_raw_manifest_present", bool(raw_rows), f"raw_rows={len(raw_rows)}")
        review_ready = [
            row
            for row in raw_rows
            if row.review_asset_id and row.raw_manifest_bucket == RAW_BUCKET and row.raw_manifest_object == raw_manifest
        ]
        add(
            checks,
            "outline_review_raw_source_ready",
            bool(review_ready),
            f"rows_with_review_asset_and_current_raw={len(review_ready)} raw_manifest={raw_manifest or '<missing>'}",
        )
        stale_rows = [row for row in raw_rows if row.stage_status == "clean_stale"]
        if summary.get("invalidated_clean"):
            add(checks, "clean_stale_after_forced_rebuild", bool(stale_rows), f"raw_rows={len(raw_rows)} clean_stale_rows={len(stale_rows)}")
        else:
            add_na(checks, "clean_stale_after_forced_rebuild", "run summary has no invalidated_clean block")
        refs = [{"bucket": RAW_BUCKET, "object": raw_manifest}]
        if raw_manifest.endswith("manifest.json"):
            refs.extend({"bucket": RAW_BUCKET, "object": raw_manifest[: -len("manifest.json")] + name} for name in REQUIRED_RAW_FILES)
        missing_objects = [ref for ref in refs if ref["object"] and not object_exists(ref["bucket"], ref["object"])]
        add(checks, "minio_raw_objects_exist", not missing_objects, f"checked={len(refs)} missing={len(missing_objects)}")
    else:
        add_na(checks, "published_raw_manifest_recorded", "dry-run or failed run")
        add_na(checks, "db_raw_manifest_present", "dry-run or failed run")
        add_na(checks, "outline_review_raw_source_ready", "dry-run or failed run")
        add_na(checks, "clean_stale_after_forced_rebuild", "dry-run or failed run")
        add_na(checks, "minio_raw_objects_exist", "dry-run or failed run")

    review_links = [row for row in material_rows if row.review_asset_id]
    add(checks, "review_asset_linked", bool(review_links), f"material_review_links={len(review_links)}")

    events = (
        db.query(PipelineEvent)
        .filter(PipelineEvent.run_id == run.id, PipelineEvent.user_id == run.user_id)
        .order_by(PipelineEvent.id.asc())
        .all()
    )
    stages = {event.stage or "" for event in events}
    if run.status == "succeeded":
        required_stages = {"candidate_collect", "llm_decision", "visual_review", "flooding", "qa"}
        if required_stages.issubset(stages):
            add(checks, "pipeline_evidence_events", True, f"stages={sorted(stages)}")
        elif outline:
            add_warn(checks, "pipeline_evidence_events", f"older run has summary evidence but coarse events: stages={sorted(stages)}")
        else:
            add(checks, "pipeline_evidence_events", False, f"stages={sorted(stages)}")
    else:
        add_na(checks, "pipeline_evidence_events", f"run not succeeded; stages={sorted(stages)}")

    hard_failures = [check for check in checks if check["status"] == "FAIL"]
    warnings = [check for check in checks if check["status"] == "WARN"]
    return {
        "kind": "popo2raw_acceptance",
        "passed": not hard_failures,
        "failed_count": len(hard_failures),
        "warning_count": len(warnings),
        "material_id": material_id,
        "published": published,
        "checks": checks,
    }


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def number(value: Any) -> int:
    return int(value) if isinstance(value, int | float) else 0


def add(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})


def add_na(checks: list[dict[str, str]], name: str, detail: str) -> None:
    checks.append({"name": name, "status": "N/A", "detail": detail})


def add_warn(checks: list[dict[str, str]], name: str, detail: str) -> None:
    checks.append({"name": name, "status": "WARN", "detail": detail})


def object_exists(bucket: str, object_name: str) -> bool:
    if not bucket or not object_name:
        return False
    try:
        minio_client.stat_object(bucket, object_name)
        return True
    except Exception:
        return False
