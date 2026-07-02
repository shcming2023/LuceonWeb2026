#!/usr/bin/env python3
"""Backfill duplicate formula source bboxes by same-unit ordinal evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_standard_formula_bbox_candidates import (  # noqa: E402
    build_raw_index,
    display_text,
    enrich_raw_rows_with_assignments,
    math_location_key,
    same_unit_matches,
)
from close_standard_review_outcomes import load_raw_content_rows, raw_row_text, standard_raw_dir  # noqa: E402
from standard_from_clean import (  # noqa: E402
    build_review_outcomes_html,
    refresh_visual_outcome_review_artifacts,
    refresh_workbook_profile_artifacts,
    write_json,
)


FORMULA_PACKET_TYPE = "formula_visual_review"
ORDINAL_BUCKET = "source_location_candidate_math_duplicate_same_unit_ordinal"
SOURCE_MATCH_RULE = "raw_content_list.math_normalized_duplicate_same_unit_ordinal_for_manual_review"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def outcome_id_for_packet(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


def block_sort_key(packet: dict[str, Any]) -> tuple[int, str]:
    block_id = str(packet.get("block_id") or "")
    match = re.search(r"(\d+)$", block_id)
    return (int(match.group(1)) if match else 10**12, block_id)


def group_key_for_packet(packet: dict[str, Any]) -> tuple[str, str]:
    heading_path = packet.get("heading_path") if isinstance(packet.get("heading_path"), list) else []
    leaf_heading = str(heading_path[-1]) if heading_path else ""
    return (leaf_heading, math_location_key(str(packet.get("clean_text") or "")))


def candidate_item(outcome_id: str, packet: dict[str, Any], raw_row: dict[str, Any]) -> dict[str, Any]:
    heading_path = packet.get("heading_path") if isinstance(packet.get("heading_path"), list) else []
    return {
        "outcome_id": outcome_id,
        "block_id": packet.get("block_id") or "",
        "bucket": ORDINAL_BUCKET,
        "heading_path": heading_path,
        "math_location_key": math_location_key(str(packet.get("clean_text") or "")),
        "source_page_number": int(raw_row["page_idx"]) + 1,
        "source_bbox": raw_row.get("bbox") or [],
        "source_raw_type": raw_row.get("type") or "",
        "source_unit_title": raw_row.get("unit_title") or "",
        "source_raw_index": raw_row.get("_raw_index"),
        "source_order": raw_row.get("source_order"),
        "source_unit_id": raw_row.get("unit_id") or "",
        "assignment_method": raw_row.get("assignment_method") or "",
        "clean_text_preview": display_text(str(packet.get("clean_text") or ""))[:500],
        "source_content_preview": display_text(raw_row_text(raw_row))[:500],
    }


def build_or_apply(standard_dir: Path, *, apply: bool) -> dict[str, Any]:
    visual_path = standard_dir / "standard_visual_review_packets.json"
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    visual_packets = read_json(visual_path)
    review_outcomes = read_json(outcomes_path)
    audit = read_json(standard_dir / "formula_bbox_candidate_audit.json")
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
    _, by_unit_key = build_raw_index(raw_rows)

    grouped_outcomes: dict[tuple[str, str], list[tuple[str, dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for item in audit.get("items") or []:
        if item.get("bucket") != "ambiguous_math_normalized_match":
            continue
        outcome_id = str(item.get("outcome_id") or "")
        packet = packets_by_id.get(outcome_id)
        outcome = outcomes_by_id.get(outcome_id)
        if not packet or not outcome:
            continue
        key = group_key_for_packet(packet)
        if len(key[1]) < 6:
            continue
        grouped_outcomes[key].append((outcome_id, packet, outcome))

    candidates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for key, rows in sorted(grouped_outcomes.items()):
        rows.sort(key=lambda row: block_sort_key(row[1]))
        sample_packet = rows[0][1]
        math_key = key[1]
        matches = same_unit_matches(sample_packet, math_key, by_unit_key)
        matches = sorted(matches, key=lambda row: (int(row.get("source_order") or 10**12), int(row.get("_raw_index") or 10**12)))
        group_record = {
            "heading": key[0],
            "math_location_key": math_key,
            "outcome_count": len(rows),
            "candidate_count": len(matches),
            "outcome_block_ids": [row[1].get("block_id") for row in rows],
            "candidate_source_orders": [row.get("source_order") for row in matches],
        }
        if len(rows) != len(matches) or len(rows) < 2:
            group_record["status"] = "not_ordinal_deterministic"
            skipped.append(group_record)
            continue
        for (outcome_id, packet, _outcome), raw_row in zip(rows, matches):
            candidates.append(candidate_item(outcome_id, packet, raw_row))

    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    status_counts: Counter[str] = Counter()
    items: list[dict[str, Any]] = []
    for candidate in candidates:
        outcome_id = str(candidate.get("outcome_id") or "")
        packet = packets_by_id.get(outcome_id)
        outcome = outcomes_by_id.get(outcome_id)
        if not packet or not outcome:
            status = "missing_packet_or_outcome"
        elif outcome.get("packet_type") != FORMULA_PACKET_TYPE:
            status = "not_formula_outcome"
        elif outcome.get("status") != "open" or not outcome.get("basic_print_blocking"):
            status = "not_open_blocking"
        elif outcome.get("decision") != "needs_page_bbox":
            status = "decision_not_needs_page_bbox"
        elif not candidate.get("source_page_number") or len(candidate.get("source_bbox") or []) != 4:
            status = "candidate_missing_page_bbox"
        else:
            status = "backfilled" if apply else "backfill_candidate"
            if apply:
                packet["source_page_number"] = candidate.get("source_page_number")
                packet["source_page_idx"] = int(candidate["source_page_number"]) - 1
                packet["source_bbox"] = candidate.get("source_bbox") or []
                packet["source_content"] = candidate.get("source_content_preview") or ""
                packet["source_raw_type"] = candidate.get("source_raw_type") or ""
                packet["source_match_rule"] = SOURCE_MATCH_RULE
                packet["source_match_score"] = 1.0
                packet["source_order"] = candidate.get("source_order")
                packet["source_unit_id"] = candidate.get("source_unit_id") or ""
                packet["source_unit_title"] = candidate.get("source_unit_title") or ""
                packet["source_assignment_method"] = candidate.get("assignment_method") or ""
                packet["source_crop_status"] = "ready_for_source_crop"
                outcome["source_page_number"] = packet["source_page_number"]
                outcome["source_bbox"] = packet["source_bbox"]
                outcome["source_crop_status"] = "ready_for_source_crop"
                outcome["source_evidence_ready"] = False
                outcome["decision"] = "needs_source_crop"
                outcome["status"] = "open"
                outcome["basic_print_blocking"] = True
                outcome["reviewer"] = "system:formula_ordinal_bbox_backfill"
                outcome["reviewed_at"] = now
                outcome["notes"] = (
                    "Source page/bbox backfilled by same-unit duplicate formula ordinal evidence; "
                    "manual visual review and source crop are still required."
                )
                outcome["evidence"] = [
                    "formula_bbox_candidate_audit.json",
                    "raw_block_assignments.jsonl",
                    "standard_visual_review_packets.json",
                    SOURCE_MATCH_RULE,
                ]
                outcome["next_action"] = "generate_source_crop_for_manual_review"
        status_counts[status] += 1
        item = dict(candidate)
        item["status"] = status
        items.append(item)

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
        "schema": "luceon-standard-formula-ordinal-bbox-backfill/v1",
        "standard_dir": str(standard_dir),
        "mode": "apply" if apply else "audit",
        "policy": "duplicate_formula_same_unit_ordinal_backfill_is_source_location_evidence_not_closure",
        "source_match_rule": SOURCE_MATCH_RULE,
        "raw_assignment_summary": assignment_summary,
        "status_counts": dict(status_counts),
        "candidate_count": len(candidates),
        "skipped_groups": skipped,
        "items": items,
    }
    write_json(standard_dir / "formula_bbox_ordinal_backfill_report.json", report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_or_apply(args.standard_dir, apply=args.apply)
    print(json.dumps({key: value for key, value in report.items() if key not in {"items", "skipped_groups"}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
