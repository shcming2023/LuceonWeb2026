#!/usr/bin/env python3
"""Close formula outcomes that pass the formula source-mismatch semantic audit."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from close_standard_review_outcomes import build_closure_html, build_closure_report, update_acceptance_and_manifest
from standard_from_clean import build_review_outcomes_html, refresh_visual_outcome_review_artifacts, refresh_workbook_profile_artifacts, write_json


CLOSABLE_BUCKET = "deterministic_formula_semantic_equivalent"
READY_CROP_STATUSES = {"created", "reused"}
CLOSABLE_SOURCE_RULES = {
    "raw_content_list.formula_semantic_key_match",
    "raw_content_list.math_normalized_unique_same_unit_for_manual_review",
    "raw_content_list.math_normalized_duplicate_same_unit_ordinal_for_manual_review",
    "raw_context_window.compact_exact_same_unit_for_manual_review",
    "raw_context_window.high_confidence_for_manual_review",
    "raw_context_window.short_option_formula_exact_same_unit_for_manual_review",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def crop_summary_from_existing_artifacts(standard_dir: Path) -> dict[str, Any]:
    audit = read_json(standard_dir / "visual_source_crop_audit.json")
    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else None
    return summary or {}


def summarize_review_outcomes(outcomes: dict[str, Any]) -> None:
    items = outcomes.get("items") or []
    outcomes["decision_counts"] = dict(Counter(str(item.get("decision") or "") for item in items))
    outcomes["open_blocking_count"] = sum(
        1 for item in items if item.get("status") == "open" and item.get("basic_print_blocking")
    )
    outcomes["closed_count"] = sum(1 for item in items if item.get("status") == "closed")


def cumulative_formula_semantic_closure_count(outcomes: dict[str, Any]) -> int:
    return sum(
        1
        for item in outcomes.get("items") or []
        if item.get("reviewer") == "system:formula_semantic_equivalent_closure"
        and item.get("decision") == "accepted_by_rule"
        and item.get("status") == "closed"
    )


def is_closable_formula_semantic_equivalent(audit_item: dict[str, Any]) -> bool:
    source_rule = str(audit_item.get("source_match_rule") or "")
    crop_status = str(audit_item.get("source_crop_status") or "")
    return (
        audit_item.get("bucket") == CLOSABLE_BUCKET
        and audit_item.get("semantic_key_equal") is True
        and source_rule in CLOSABLE_SOURCE_RULES
        and bool(audit_item.get("source_page_number"))
        and bool(audit_item.get("source_bbox"))
        and bool(audit_item.get("source_crop"))
        and crop_status in READY_CROP_STATUSES
    )


def close_from_formula_audit(standard_dir: Path, *, apply: bool) -> dict[str, Any]:
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    audit_path = standard_dir / "formula_source_mismatch_audit.json"
    if not outcomes_path.exists():
        raise FileNotFoundError(f"Missing standard review outcomes: {outcomes_path}")
    if not audit_path.exists():
        raise FileNotFoundError(f"Missing formula source mismatch audit: {audit_path}")

    outcomes = read_json(outcomes_path)
    audit = read_json(audit_path)
    audit_by_id = {
        str(item.get("outcome_id") or ""): item
        for item in audit.get("items") or []
        if isinstance(item, dict) and item.get("outcome_id")
    }
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    newly_closed = 0
    already_closed = 0
    candidates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for item in outcomes.get("items") or []:
        outcome_id = str(item.get("outcome_id") or "")
        audit_item = audit_by_id.get(outcome_id)
        if not audit_item:
            continue
        if audit_item.get("bucket") == CLOSABLE_BUCKET and not is_closable_formula_semantic_equivalent(audit_item):
            skipped.append(
                {
                    "outcome_id": outcome_id,
                    "bucket": audit_item.get("bucket"),
                    "source_match_rule": audit_item.get("source_match_rule"),
                    "source_crop_status": audit_item.get("source_crop_status"),
                    "reason": "deterministic_bucket_but_closure_requirements_not_met",
                }
            )
            continue
        if not is_closable_formula_semantic_equivalent(audit_item):
            continue
        source_rule = str(audit_item.get("source_match_rule") or "")
        candidates.append(
            {
                "outcome_id": outcome_id,
                "block_id": item.get("block_id"),
                "source_match_rule": source_rule,
                "source_crop": audit_item.get("source_crop"),
                "source_crop_status": audit_item.get("source_crop_status"),
                "semantic_key_similarity": audit_item.get("semantic_key_similarity"),
            }
        )
        if item.get("status") == "closed" and item.get("decision") == "accepted_by_rule":
            already_closed += 1
            continue
        if apply:
            item.update(
                {
                    "decision": "accepted_by_rule",
                    "status": "closed",
                    "basic_print_blocking": False,
                    "source_evidence_ready": True,
                    "source_page_number": audit_item.get("source_page_number"),
                    "source_bbox": audit_item.get("source_bbox") or [],
                    "source_crop": audit_item.get("source_crop") or "",
                    "source_crop_status": audit_item.get("source_crop_status") or "",
                    "reviewer": "system:formula_semantic_equivalent_closure",
                    "reviewed_at": now,
                    "notes": f"Closed by {source_rule} plus exact formula semantic key match and generated/reused source PDF crop.",
                    "evidence": [
                        "formula_source_mismatch_audit.json",
                        audit_item.get("source_crop") or "",
                        source_rule,
                        "deterministic_formula_semantic_equivalent",
                    ],
                    "next_action": "none",
                }
            )
            newly_closed += 1

    if apply:
        summarize_review_outcomes(outcomes)
        outcomes["updated_at"] = now
        outcomes["formula_semantic_equivalent_closure_summary"] = {
            "closed_count": newly_closed,
            "already_closed": already_closed,
            "status": "applied",
        }
        outcomes["formula_source_mismatch_audit"] = "formula_source_mismatch_audit.json"
        write_json(outcomes_path, outcomes)
        (standard_dir / "review_outcomes.html").write_text(build_review_outcomes_html(outcomes), encoding="utf-8")
        refresh_visual_outcome_review_artifacts(standard_dir)
        refresh_workbook_profile_artifacts(standard_dir)
    return {
        "review_outcomes": outcomes,
        "audit": audit,
        "newly_closed": newly_closed,
        "already_closed": already_closed,
        "candidates": candidates,
        "skipped": skipped,
        "mode": "apply" if apply else "dry_run",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Close formula outcomes using formula source-mismatch audit results.")
    parser.add_argument("--standard-dir", required=True, type=Path, help="Existing standard-final directory.")
    parser.add_argument("--apply", action="store_true", help="Write accepted_by_rule closures. Default is dry-run.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    standard_dir = args.standard_dir
    result = close_from_formula_audit(standard_dir, apply=args.apply)
    crop_summary = crop_summary_from_existing_artifacts(standard_dir)
    report = {
        "schema": "luceon-standard-formula-semantic-equivalent-closure/v1",
        "standard_dir": str(standard_dir),
        "mode": result["mode"],
        "policy": "close_only_deterministic_formula_semantic_equivalent_with_allowed_source_rule_and_crop",
        "allowed_source_rules": sorted(CLOSABLE_SOURCE_RULES),
        "candidate_count": len(result["candidates"]),
        "newly_closed": result["newly_closed"],
        "already_closed": result["already_closed"],
        "cumulative_closed_by_reviewer": cumulative_formula_semantic_closure_count(result["review_outcomes"]),
        "items": result["candidates"],
        "skipped_items": result["skipped"],
    }
    write_json(standard_dir / "formula_semantic_equivalent_closure_report.json", report)
    if args.apply:
        acceptance = update_acceptance_and_manifest(standard_dir, result["review_outcomes"], crop_summary)
        closure = build_closure_report(standard_dir, acceptance, result["review_outcomes"], crop_summary, {})
        write_json(standard_dir / "basic_print_closure_report.json", closure)
        (standard_dir / "basic_print_closure.html").write_text(build_closure_html(closure), encoding="utf-8")
    print(
        json.dumps(
            {
                "standard_dir": str(standard_dir),
                "mode": result["mode"],
                "candidate_count": len(result["candidates"]),
                "newly_closed": result["newly_closed"],
                "already_closed": result["already_closed"],
                "open_blocking_count": result["review_outcomes"]["open_blocking_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
