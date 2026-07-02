#!/usr/bin/env python3
"""Close table/formula review outcomes from a prior audit artifact."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from close_standard_review_outcomes import (
    build_closure_html,
    build_closure_report,
    update_acceptance_and_manifest,
)
from standard_from_clean import (
    build_review_outcomes_html,
    refresh_visual_outcome_review_artifacts,
    refresh_workbook_profile_artifacts,
    write_json,
)

CLOSABLE_BUCKETS = {
    "deterministic_closure_candidate_exact_match": "raw_content_list.exact_normalized_match",
    "deterministic_closure_candidate_compact_match": "raw_content_list.compact_exact_match",
}
READY_CROP_STATUSES = {"created", "reused"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def close_from_audit(standard_dir: Path) -> dict[str, Any]:
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    audit_path = standard_dir / "table_formula_outcome_audit.json"
    if not outcomes_path.exists():
        raise FileNotFoundError(f"Missing standard review outcomes: {outcomes_path}")
    if not audit_path.exists():
        raise FileNotFoundError(f"Missing table/formula audit: {audit_path}")

    outcomes = read_json(outcomes_path)
    audit = read_json(audit_path)
    audit_by_id = {
        str(item.get("outcome_id") or ""): item
        for item in audit.get("items") or []
        if isinstance(item, dict) and item.get("outcome_id")
    }
    now = datetime.utcnow().isoformat() + "Z"
    closed_count = 0
    for item in outcomes.get("items") or []:
        outcome_id = str(item.get("outcome_id") or "")
        audit_item = audit_by_id.get(outcome_id)
        if not audit_item:
            continue
        bucket = str(audit_item.get("bucket") or "")
        if bucket in CLOSABLE_BUCKETS:
            source_rule = CLOSABLE_BUCKETS[bucket]
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
                    "reviewer": "system:table_formula_outcome_audit",
                    "reviewed_at": now,
                    "notes": f"Closed by {source_rule} plus generated/reused source PDF crop.",
                    "evidence": [
                        "table_formula_outcome_audit.json",
                        audit_item.get("source_crop") or "",
                        source_rule,
                    ],
                    "next_action": "none",
                }
            )
            closed_count += 1
        elif bucket == "needs_page_bbox":
            item.update(
                {
                    "decision": "needs_page_bbox",
                    "status": "open",
                    "basic_print_blocking": True,
                    "source_evidence_ready": False,
                    "next_action": "locate_source_page_bbox",
                }
            )

    decision_counts: dict[str, int] = {}
    for item in outcomes.get("items") or []:
        decision = str(item.get("decision") or "")
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
    outcomes["decision_counts"] = decision_counts
    outcomes["open_blocking_count"] = sum(
        1 for item in outcomes.get("items") or [] if item.get("status") == "open" and item.get("basic_print_blocking")
    )
    outcomes["closed_count"] = sum(1 for item in outcomes.get("items") or [] if item.get("status") == "closed")
    outcomes["updated_at"] = now
    outcomes["table_formula_outcome_audit"] = "table_formula_outcome_audit.json"
    write_json(outcomes_path, outcomes)
    (standard_dir / "review_outcomes.html").write_text(build_review_outcomes_html(outcomes), encoding="utf-8")
    refresh_visual_outcome_review_artifacts(standard_dir)
    refresh_workbook_profile_artifacts(standard_dir)
    return {"review_outcomes": outcomes, "audit": audit, "closed_count": closed_count}


def crop_summary_from_audit(audit: dict[str, Any]) -> dict[str, Any]:
    summary = audit.get("summary")
    if isinstance(summary, dict) and summary:
        return summary
    items = [item for item in audit.get("items") or [] if isinstance(item, dict)]
    status_counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("source_crop_status") or "")
        status_counts[status] = status_counts.get(status, 0) + 1
    source_crop_count = sum(1 for item in items if item.get("source_crop_status") in READY_CROP_STATUSES)
    return {
        "source_crop_count": source_crop_count,
        "source_crop_required_count": len(items),
        "source_crop_status_counts": status_counts,
        "source_crop_generation": "precomputed_audit",
        "source_crop_dir": "visual_source_crops/",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = close_from_audit(args.standard_dir)
    crop_summary = crop_summary_from_audit(result["audit"])
    acceptance = update_acceptance_and_manifest(args.standard_dir, result["review_outcomes"], crop_summary)
    report = build_closure_report(args.standard_dir, acceptance, result["review_outcomes"], crop_summary)
    report["table_formula_outcome_audit"] = "table_formula_outcome_audit.json"
    report["closed_from_audit_count"] = result["closed_count"]
    write_json(args.standard_dir / "basic_print_closure_report.json", report)
    (args.standard_dir / "basic_print_closure.html").write_text(build_closure_html(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "standard_dir": str(args.standard_dir),
                "closed_from_audit_count": result["closed_count"],
                "status": report["status"],
                "open_blocking_count": result["review_outcomes"].get("open_blocking_count"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
