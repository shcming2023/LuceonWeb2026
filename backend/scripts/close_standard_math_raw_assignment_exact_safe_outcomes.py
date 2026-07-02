#!/usr/bin/env python3
"""Close Math formula outcomes with audited safe raw-assignment exact evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from close_standard_review_outcomes import build_closure_html, build_closure_report, update_acceptance_and_manifest
from standard_from_clean import (
    build_review_outcomes_html,
    refresh_visual_outcome_review_artifacts,
    refresh_workbook_profile_artifacts,
    write_json,
)


CLOSABLE_RISK_BUCKETS = {"compact_surface_safe", "short_option_surface_safe", "punctuation_spacing_safe"}
READY_CROP_STATUSES = {"created", "reused"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def summarize_review_outcomes(outcomes: dict[str, Any]) -> None:
    items = outcomes.get("items") or []
    outcomes["decision_counts"] = dict(Counter(str(item.get("decision") or "") for item in items))
    outcomes["open_blocking_count"] = sum(
        1 for item in items if item.get("status") == "open" and item.get("basic_print_blocking")
    )
    outcomes["closed_count"] = sum(1 for item in items if item.get("status") == "closed")


def crop_summary_from_existing_artifacts(standard_dir: Path) -> dict[str, Any]:
    audit = read_json(standard_dir / "visual_source_crop_audit.json")
    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else None
    return summary or {}


def is_closable(risk_item: dict[str, Any]) -> tuple[bool, str]:
    if risk_item.get("risk_bucket") not in CLOSABLE_RISK_BUCKETS:
        return False, "risk_bucket_not_closable"
    if risk_item.get("source_crop_status") not in READY_CROP_STATUSES:
        return False, "source_crop_not_ready"
    if not risk_item.get("source_page_number") or not risk_item.get("source_bbox"):
        return False, "source_page_bbox_missing"
    if not risk_item.get("source_crop"):
        return False, "source_crop_missing"
    return True, "safe_raw_assignment_exact_surface_match"


def close_safe_raw_assignment_exact(standard_dir: Path, risk_audit_path: Path, *, apply: bool) -> dict[str, Any]:
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    if not outcomes_path.exists():
        raise FileNotFoundError(f"Missing standard review outcomes: {outcomes_path}")
    if not risk_audit_path.exists():
        raise FileNotFoundError(f"Missing raw-assignment risk audit: {risk_audit_path}")
    outcomes = read_json(outcomes_path)
    risk_audit = read_json(risk_audit_path)
    risk_by_id = {
        str(item.get("outcome_id") or ""): item
        for item in risk_audit.get("items") or []
        if isinstance(item, dict) and item.get("outcome_id")
    }
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    candidates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    newly_closed = 0
    already_closed = 0
    for item in outcomes.get("items") or []:
        outcome_id = str(item.get("outcome_id") or "")
        risk_item = risk_by_id.get(outcome_id)
        if not risk_item:
            continue
        closable, reason = is_closable(risk_item)
        if not closable:
            skipped.append(
                {
                    "outcome_id": outcome_id,
                    "block_id": item.get("block_id"),
                    "reason": reason,
                    "risk_bucket": risk_item.get("risk_bucket"),
                    "source_crop_status": risk_item.get("source_crop_status"),
                }
            )
            continue
        candidates.append(
            {
                "outcome_id": outcome_id,
                "block_id": item.get("block_id"),
                "risk_bucket": risk_item.get("risk_bucket"),
                "source_crop": risk_item.get("source_crop") or "",
                "source_crop_status": risk_item.get("source_crop_status") or "",
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
                    "source_page_number": risk_item.get("source_page_number"),
                    "source_bbox": risk_item.get("source_bbox") or [],
                    "source_crop": risk_item.get("source_crop") or "",
                    "source_crop_status": risk_item.get("source_crop_status") or "",
                    "reviewer": "system:math_raw_assignment_exact_safe_closure",
                    "reviewed_at": now,
                    "notes": "Closed by audited safe raw_assignment.located_exact surface match with source PDF crop; digit-spacing risk excluded.",
                    "evidence": [
                        str(risk_audit_path.name),
                        risk_item.get("source_crop") or "",
                        str(risk_item.get("risk_bucket") or ""),
                    ],
                    "next_action": "none",
                }
            )
            newly_closed += 1

    if apply:
        summarize_review_outcomes(outcomes)
        outcomes["updated_at"] = now
        outcomes["math_raw_assignment_exact_safe_closure_summary"] = {
            "closed_count": newly_closed,
            "already_closed": already_closed,
            "status": "applied",
        }
        write_json(outcomes_path, outcomes)
        (standard_dir / "review_outcomes.html").write_text(build_review_outcomes_html(outcomes), encoding="utf-8")
        refresh_visual_outcome_review_artifacts(standard_dir)
        refresh_workbook_profile_artifacts(standard_dir)
    return {
        "review_outcomes": outcomes,
        "risk_audit": risk_audit,
        "mode": "apply" if apply else "dry_run",
        "newly_closed": newly_closed,
        "already_closed": already_closed,
        "candidates": candidates,
        "skipped": skipped,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--risk-audit", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = close_safe_raw_assignment_exact(args.standard_dir, args.risk_audit, apply=args.apply)
    report = {
        "schema": "luceon-standard-math-raw-assignment-exact-safe-closure/v1",
        "standard_dir": str(args.standard_dir),
        "risk_audit": str(args.risk_audit),
        "mode": result["mode"],
        "policy": "close_only_audited_safe_raw_assignment_exact_surface_matches_digit_spacing_excluded",
        "closable_risk_buckets": sorted(CLOSABLE_RISK_BUCKETS),
        "candidate_count": len(result["candidates"]),
        "newly_closed": result["newly_closed"],
        "already_closed": result["already_closed"],
        "skipped_count": len(result["skipped"]),
        "items": result["candidates"],
        "skipped": result["skipped"],
    }
    write_json(args.standard_dir / "math_raw_assignment_exact_safe_closure_report.json", report)
    if args.apply:
        crop_summary = crop_summary_from_existing_artifacts(args.standard_dir)
        acceptance = update_acceptance_and_manifest(args.standard_dir, result["review_outcomes"], crop_summary)
        closure = build_closure_report(args.standard_dir, acceptance, result["review_outcomes"], crop_summary, {})
        closure["math_raw_assignment_exact_safe_closure_report"] = "math_raw_assignment_exact_safe_closure_report.json"
        write_json(args.standard_dir / "basic_print_closure_report.json", closure)
        (args.standard_dir / "basic_print_closure.html").write_text(build_closure_html(closure), encoding="utf-8")
    print(
        json.dumps(
            {
                "standard_dir": str(args.standard_dir),
                "mode": result["mode"],
                "candidate_count": len(result["candidates"]),
                "newly_closed": result["newly_closed"],
                "already_closed": result["already_closed"],
                "skipped_count": len(result["skipped"]),
                "open_blocking_count": result["review_outcomes"].get("open_blocking_count"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
