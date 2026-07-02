#!/usr/bin/env python3
"""Close Math table/formula outcomes with native Raw content exact-match evidence."""

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


CLOSABLE_BUCKET = "deterministic_closure_candidate_exact_match"
CLOSABLE_RAW_TYPES = {"text", "equation", "table"}
READY_CROP_STATUSES = {"created", "reused"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def outcome_id_for_packet(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


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


def is_native_exact_closable(audit_item: dict[str, Any], packet: dict[str, Any]) -> tuple[bool, str]:
    if audit_item.get("bucket") != CLOSABLE_BUCKET:
        return False, "bucket_not_exact_match"
    source_match_rule = str(packet.get("source_match_rule") or "")
    if source_match_rule:
        return False, "source_match_rule_not_native_raw_content"
    source_raw_type = str(packet.get("source_raw_type") or "")
    if source_raw_type not in CLOSABLE_RAW_TYPES:
        return False, "source_raw_type_not_allowed"
    crop_status = str(audit_item.get("source_crop_status") or packet.get("source_crop_status") or "")
    if crop_status not in READY_CROP_STATUSES:
        return False, "source_crop_not_ready"
    if not audit_item.get("source_page_number") or not audit_item.get("source_bbox"):
        return False, "source_page_bbox_missing"
    if not audit_item.get("source_crop"):
        return False, "source_crop_missing"
    return True, "native_raw_content_exact_match_with_crop"


def close_native_exact(standard_dir: Path, *, apply: bool) -> dict[str, Any]:
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    audit_path = standard_dir / "table_formula_outcome_audit.json"
    packets_path = standard_dir / "standard_visual_review_packets.json"
    if not outcomes_path.exists():
        raise FileNotFoundError(f"Missing standard review outcomes: {outcomes_path}")
    if not audit_path.exists():
        raise FileNotFoundError(f"Missing table/formula audit: {audit_path}")
    if not packets_path.exists():
        raise FileNotFoundError(f"Missing visual review packets: {packets_path}")

    outcomes = read_json(outcomes_path)
    audit = read_json(audit_path)
    packets = read_json(packets_path)
    audit_by_id = {
        str(item.get("outcome_id") or ""): item
        for item in audit.get("items") or []
        if isinstance(item, dict) and item.get("outcome_id")
    }
    packets_by_id = {
        outcome_id_for_packet(packet): packet
        for packet in packets.get("items") or []
        if isinstance(packet, dict)
    }
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    candidates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    newly_closed = 0
    already_closed = 0

    for item in outcomes.get("items") or []:
        outcome_id = str(item.get("outcome_id") or "")
        audit_item = audit_by_id.get(outcome_id)
        packet = packets_by_id.get(outcome_id, {})
        if not audit_item:
            continue
        closable, reason = is_native_exact_closable(audit_item, packet)
        if not closable:
            if audit_item.get("bucket") == CLOSABLE_BUCKET:
                skipped.append(
                    {
                        "outcome_id": outcome_id,
                        "block_id": item.get("block_id"),
                        "packet_type": item.get("packet_type"),
                        "reason": reason,
                        "source_match_rule": packet.get("source_match_rule") or "",
                        "source_raw_type": packet.get("source_raw_type") or "",
                        "source_crop_status": audit_item.get("source_crop_status") or packet.get("source_crop_status") or "",
                    }
                )
            continue
        candidates.append(
            {
                "outcome_id": outcome_id,
                "block_id": item.get("block_id"),
                "packet_type": item.get("packet_type"),
                "source_raw_type": packet.get("source_raw_type") or "",
                "source_crop": audit_item.get("source_crop") or "",
                "source_crop_status": audit_item.get("source_crop_status") or "",
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
                    "reviewer": "system:math_native_raw_content_exact_closure",
                    "reviewed_at": now,
                    "notes": "Closed by native Raw content exact normalized match plus generated/reused source PDF crop.",
                    "evidence": [
                        "table_formula_outcome_audit.json",
                        audit_item.get("source_crop") or "",
                        "native_raw_content_exact_match",
                    ],
                    "next_action": "none",
                }
            )
            newly_closed += 1

    if apply:
        summarize_review_outcomes(outcomes)
        outcomes["updated_at"] = now
        outcomes["math_native_exact_closure_summary"] = {
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
        "audit": audit,
        "mode": "apply" if apply else "dry_run",
        "newly_closed": newly_closed,
        "already_closed": already_closed,
        "candidates": candidates,
        "skipped_exact_bucket": skipped,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--apply", action="store_true", help="Write closures. Default is dry-run.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = close_native_exact(args.standard_dir, apply=args.apply)
    report = {
        "schema": "luceon-standard-math-native-exact-content-closure/v1",
        "standard_dir": str(args.standard_dir),
        "mode": result["mode"],
        "policy": "close_only_native_raw_content_exact_match_with_source_crop_no_raw_assignment_closure",
        "closable_bucket": CLOSABLE_BUCKET,
        "closable_raw_types": sorted(CLOSABLE_RAW_TYPES),
        "ready_crop_statuses": sorted(READY_CROP_STATUSES),
        "candidate_count": len(result["candidates"]),
        "newly_closed": result["newly_closed"],
        "already_closed": result["already_closed"],
        "skipped_exact_bucket_count": len(result["skipped_exact_bucket"]),
        "items": result["candidates"],
        "skipped_exact_bucket": result["skipped_exact_bucket"],
    }
    write_json(args.standard_dir / "math_native_exact_content_closure_report.json", report)
    if args.apply:
        crop_summary = crop_summary_from_existing_artifacts(args.standard_dir)
        acceptance = update_acceptance_and_manifest(args.standard_dir, result["review_outcomes"], crop_summary)
        closure = build_closure_report(args.standard_dir, acceptance, result["review_outcomes"], crop_summary, {})
        closure["math_native_exact_content_closure_report"] = "math_native_exact_content_closure_report.json"
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
                "skipped_exact_bucket_count": len(result["skipped_exact_bucket"]),
                "open_blocking_count": result["review_outcomes"].get("open_blocking_count"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
