#!/usr/bin/env python3
"""Backfill high-confidence Raw context-window bbox candidates for manual review."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from standard_from_clean import build_review_outcomes_html, refresh_visual_outcome_review_artifacts, refresh_workbook_profile_artifacts, write_json


DEFAULT_BUCKET = "context_window_candidate_high_confidence"
SOURCE_MATCH_RULE = "raw_context_window.high_confidence_for_manual_review"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def outcome_id_for_packet(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


def build_or_apply(standard_dir: Path, *, apply: bool, candidate_bucket: str = DEFAULT_BUCKET) -> dict[str, Any]:
    audit = read_json(standard_dir / "raw_context_bbox_candidate_audit.json")
    visual_path = standard_dir / "standard_visual_review_packets.json"
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    visual_packets = read_json(visual_path)
    review_outcomes = read_json(outcomes_path)
    packets_by_id = {outcome_id_for_packet(packet): packet for packet in visual_packets.get("items") or [] if isinstance(packet, dict)}
    outcomes_by_id = {str(item.get("outcome_id") or ""): item for item in review_outcomes.get("items") or [] if isinstance(item, dict)}
    now = datetime.utcnow().isoformat() + "Z"
    status_counts: Counter[str] = Counter()
    items: list[dict[str, Any]] = []

    for candidate in audit.get("items") or []:
        if candidate.get("bucket") != candidate_bucket:
            continue
        outcome_id = str(candidate.get("outcome_id") or "")
        packet = packets_by_id.get(outcome_id)
        outcome = outcomes_by_id.get(outcome_id)
        best = candidate.get("best_candidate") if isinstance(candidate.get("best_candidate"), dict) else {}
        if not packet or not outcome:
            status = "missing_packet_or_outcome"
        elif outcome.get("status") != "open" or not outcome.get("basic_print_blocking"):
            status = "not_open_blocking"
        elif outcome.get("decision") != "needs_page_bbox":
            status = "decision_not_needs_page_bbox"
        elif not best.get("source_page_number") or len(best.get("source_bbox") or []) != 4:
            status = "candidate_missing_page_bbox"
        else:
            status = "backfilled" if apply else "backfill_candidate"
            if apply:
                packet["source_page_idx"] = int(best.get("source_page_number")) - 1
                packet["source_page_number"] = best.get("source_page_number")
                packet["source_bbox"] = best.get("source_bbox") or []
                packet["source_content"] = best.get("source_content_preview") or ""
                packet["source_raw_type"] = "context_window"
                packet["source_match_rule"] = SOURCE_MATCH_RULE
                packet["source_match_score"] = best.get("score")
                packet["source_context_window"] = {
                    "raw_indices": best.get("raw_indices") or [],
                    "source_orders": best.get("source_orders") or [],
                    "window_size": best.get("window_size"),
                    "sequence_ratio": best.get("sequence_ratio"),
                    "token_overlap": best.get("token_overlap"),
                    "source_unit_title": best.get("source_unit_title") or "",
                }
                packet["source_crop_status"] = "ready_for_source_crop"
                outcome["source_page_number"] = packet["source_page_number"]
                outcome["source_bbox"] = packet["source_bbox"]
                outcome["source_crop_status"] = "ready_for_source_crop"
                outcome["source_evidence_ready"] = False
                outcome["decision"] = "needs_source_crop"
                outcome["status"] = "open"
                outcome["basic_print_blocking"] = True
                outcome["reviewer"] = "system:raw_context_bbox_candidate_backfill"
                outcome["reviewed_at"] = now
                outcome["notes"] = (
                    "Source page/bbox backfilled from high-confidence Raw context-window evidence; "
                    "source crop and manual visual review are still required."
                )
                outcome["evidence"] = [
                    "raw_context_bbox_candidate_audit.json",
                    SOURCE_MATCH_RULE,
                    "standard_visual_review_packets.json",
                ]
                outcome["next_action"] = "generate_source_crop_for_manual_review"
        status_counts[status] += 1
        items.append(
            {
                "outcome_id": outcome_id,
                "block_id": candidate.get("block_id"),
                "status": status,
                "candidate_bucket": candidate.get("bucket"),
                "source_page_number": best.get("source_page_number"),
                "source_bbox": best.get("source_bbox") or [],
                "score": best.get("score"),
                "sequence_ratio": best.get("sequence_ratio"),
                "token_overlap": best.get("token_overlap"),
                "raw_indices": best.get("raw_indices") or [],
                "source_orders": best.get("source_orders") or [],
                "clean_text_preview": candidate.get("clean_text_preview") or "",
                "source_content_preview": best.get("source_content_preview") or "",
            }
        )

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
        "schema": "luceon-standard-raw-context-bbox-backfill/v1",
        "standard_dir": str(standard_dir),
        "mode": "apply" if apply else "audit",
        "policy": "raw_context_window_backfill_is_source_location_evidence_not_closure",
        "candidate_bucket": candidate_bucket,
        "source_match_rule": SOURCE_MATCH_RULE,
        "status_counts": dict(status_counts),
        "items": items,
    }
    write_json(standard_dir / "raw_context_bbox_backfill_report.json", report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--candidate-bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_or_apply(args.standard_dir, apply=args.apply, candidate_bucket=args.candidate_bucket)
    print(json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
