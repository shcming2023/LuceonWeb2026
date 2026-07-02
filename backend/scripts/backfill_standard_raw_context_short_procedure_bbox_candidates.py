#!/usr/bin/env python3
"""Backfill short exact procedure Raw context bboxes for manual review."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_standard_formula_bbox_candidates import enrich_raw_rows_with_assignments  # noqa: E402
from audit_standard_raw_context_bbox_candidates import bbox_union, compact_key, same_unit_rows  # noqa: E402
from close_standard_review_outcomes import load_raw_content_rows, raw_row_text, standard_raw_dir  # noqa: E402
from standard_from_clean import (  # noqa: E402
    build_review_outcomes_html,
    refresh_visual_outcome_review_artifacts,
    refresh_workbook_profile_artifacts,
    write_json,
)


SOURCE_MATCH_RULE = "raw_context_window.short_procedure_exact_same_unit_for_manual_review"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def outcome_id_for_packet(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


def unique_short_procedure_match(clean_text: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    key = compact_key(clean_text)
    if not (8 <= len(key) < 24):
        return None
    if not key.startswith("step"):
        return None
    matches: list[dict[str, Any]] = []
    for row in rows:
        if compact_key(raw_row_text(row)) == key:
            matches.append(row)
    if len(matches) != 1:
        return None
    match = matches[0]
    return {
        "source_page_number": int(match["page_idx"]) + 1,
        "source_bbox": bbox_union([match]),
        "window_size": 1,
        "raw_indices": [match.get("_raw_index")],
        "source_orders": [match.get("source_order")] if match.get("source_order") is not None else [],
        "source_unit_title": match.get("unit_title") or "",
        "source_content_preview": raw_row_text(match)[:500],
    }


def build_or_apply(standard_dir: Path, *, apply: bool) -> dict[str, Any]:
    audit = read_json(standard_dir / "raw_context_bbox_candidate_audit.json")
    visual_path = standard_dir / "standard_visual_review_packets.json"
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    visual_packets = read_json(visual_path)
    review_outcomes = read_json(outcomes_path)
    packets_by_id = {
        outcome_id_for_packet(packet): packet
        for packet in visual_packets.get("items") or []
        if isinstance(packet, dict)
    }
    outcomes_by_id = {
        str(outcome.get("outcome_id") or ""): outcome
        for outcome in review_outcomes.get("items") or []
        if isinstance(outcome, dict)
    }
    raw_dir = standard_raw_dir(standard_dir)
    raw_rows, assignment_summary = enrich_raw_rows_with_assignments(load_raw_content_rows(raw_dir), raw_dir)

    candidates: list[dict[str, Any]] = []
    for item in audit.get("items") or []:
        if item.get("bucket") != "context_window_candidate_weak":
            continue
        if "procedure_text" not in (item.get("text_shape") or []):
            continue
        clean_text = str(item.get("clean_text_preview") or "")
        match = unique_short_procedure_match(clean_text, same_unit_rows(raw_rows, item.get("heading_path") or []))
        if not match:
            continue
        candidates.append(
            {
                "outcome_id": item.get("outcome_id"),
                "block_id": item.get("block_id"),
                "heading_path": item.get("heading_path") or [],
                "clean_text_preview": clean_text,
                **match,
            }
        )

    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    status_counts: Counter[str] = Counter()
    report_items: list[dict[str, Any]] = []
    for candidate in candidates:
        outcome_id = str(candidate.get("outcome_id") or "")
        packet = packets_by_id.get(outcome_id)
        outcome = outcomes_by_id.get(outcome_id)
        if not packet or not outcome:
            status = "missing_packet_or_outcome"
        elif outcome.get("status") != "open" or not outcome.get("basic_print_blocking"):
            status = "not_open_blocking"
        elif outcome.get("decision") != "needs_page_bbox":
            status = "decision_not_needs_page_bbox"
        elif not candidate.get("source_page_number") or len(candidate.get("source_bbox") or []) != 4:
            status = "candidate_missing_page_bbox"
        else:
            status = "backfilled" if apply else "backfill_candidate"
            if apply:
                packet["source_page_idx"] = int(candidate["source_page_number"]) - 1
                packet["source_page_number"] = candidate.get("source_page_number")
                packet["source_bbox"] = candidate.get("source_bbox") or []
                packet["source_content"] = candidate.get("source_content_preview") or ""
                packet["source_raw_type"] = "context_window"
                packet["source_match_rule"] = SOURCE_MATCH_RULE
                packet["source_match_score"] = 1.0
                packet["source_context_window"] = {
                    "raw_indices": candidate.get("raw_indices") or [],
                    "source_orders": candidate.get("source_orders") or [],
                    "window_size": candidate.get("window_size"),
                    "source_unit_title": candidate.get("source_unit_title") or "",
                }
                packet["source_crop_status"] = "ready_for_source_crop"
                outcome["source_page_number"] = packet["source_page_number"]
                outcome["source_bbox"] = packet["source_bbox"]
                outcome["source_crop_status"] = "ready_for_source_crop"
                outcome["source_evidence_ready"] = False
                outcome["decision"] = "needs_source_crop"
                outcome["status"] = "open"
                outcome["basic_print_blocking"] = True
                outcome["reviewer"] = "system:raw_context_short_procedure_bbox_backfill"
                outcome["reviewed_at"] = now
                outcome["notes"] = (
                    "Source page/bbox backfilled from unique short procedure Raw context evidence; "
                    "source crop and manual visual review are still required."
                )
                outcome["evidence"] = [
                    "raw_context_bbox_candidate_audit.json",
                    SOURCE_MATCH_RULE,
                    "standard_visual_review_packets.json",
                ]
                outcome["next_action"] = "generate_source_crop_for_manual_review"
        status_counts[status] += 1
        row = dict(candidate)
        row["status"] = status
        report_items.append(row)

    if apply:
        write_json(visual_path, visual_packets)
        review_outcomes["decision_counts"] = dict(Counter(str(item.get("decision") or "") for item in review_outcomes.get("items") or []))
        review_outcomes["open_blocking_count"] = sum(
            1 for item in review_outcomes.get("items") or [] if item.get("status") == "open" and item.get("basic_print_blocking")
        )
        review_outcomes["closed_count"] = sum(1 for item in review_outcomes.get("items") or [] if item.get("status") == "closed")
        review_outcomes["updated_at"] = now
        write_json(outcomes_path, review_outcomes)
        (standard_dir / "review_outcomes.html").write_text(build_review_outcomes_html(review_outcomes), encoding="utf-8")
        refresh_visual_outcome_review_artifacts(standard_dir)
        refresh_workbook_profile_artifacts(standard_dir)

    report = {
        "schema": "luceon-standard-raw-context-short-procedure-bbox-backfill/v1",
        "standard_dir": str(standard_dir),
        "mode": "apply" if apply else "audit",
        "policy": "raw_context_short_procedure_exact_same_unit_backfill_is_source_location_evidence_not_closure",
        "source_match_rule": SOURCE_MATCH_RULE,
        "raw_assignment_summary": assignment_summary,
        "status_counts": dict(status_counts),
        "candidate_count": len(candidates),
        "items": report_items,
    }
    write_json(standard_dir / "raw_context_short_procedure_bbox_backfill_report.json", report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_or_apply(args.standard_dir, apply=args.apply)
    print(json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
