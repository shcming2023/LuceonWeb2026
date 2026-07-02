#!/usr/bin/env python3
"""Backfill missing Standard visual review source bboxes from Raw evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from close_standard_review_outcomes import (
    find_table_source_fallback,
    load_content_table_evidence,
    load_content_text_evidence,
    load_raw_content_rows,
    normalize_review_compact_text,
    normalize_review_text,
    standard_raw_dir,
)
from standard_from_clean import write_json

TABLE_FORMULA_PACKET_TYPES = {"table_visual_review", "formula_visual_review"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def outcome_id_for_packet(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


def find_evidence(packet: dict[str, Any], table_evidence: dict[str, list[dict[str, Any]]], text_evidence: dict[str, list[dict[str, Any]]], raw_rows: list[dict[str, Any]]) -> dict[str, Any]:
    packet_type = str(packet.get("type") or "")
    clean_text = str(packet.get("clean_text") or "")
    key = normalize_review_text(clean_text)
    if not key:
        return {}
    if packet_type == "table_visual_review":
        compact_key = normalize_review_compact_text(clean_text)
        matches = table_evidence.get(key) or table_evidence.get(f"compact:{compact_key}") or []
        if matches:
            evidence = dict(matches[0])
            evidence.setdefault("match_rule", "raw_content_list.exact_or_compact_table_match")
            return evidence
        return find_table_source_fallback(clean_text, raw_rows)
    if packet_type == "formula_visual_review":
        matches = text_evidence.get(key) or []
        if matches:
            evidence = dict(matches[0])
            evidence.setdefault("match_rule", "raw_content_list.exact_text_match")
            return evidence
    return {}


def build_or_apply(standard_dir: Path, *, apply: bool) -> dict[str, Any]:
    visual_path = standard_dir / "standard_visual_review_packets.json"
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    visual_packets = read_json(visual_path)
    review_outcomes = read_json(outcomes_path)
    raw_dir = standard_raw_dir(standard_dir)
    table_evidence = load_content_table_evidence(raw_dir)
    text_evidence = load_content_text_evidence(raw_dir)
    raw_rows = load_raw_content_rows(raw_dir)
    outcomes_by_id = {str(item.get("outcome_id") or ""): item for item in review_outcomes.get("items") or []}
    status_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    items: list[dict[str, Any]] = []

    for packet in visual_packets.get("items") or []:
        if packet.get("type") not in TABLE_FORMULA_PACKET_TYPES:
            continue
        outcome_id = outcome_id_for_packet(packet)
        outcome = outcomes_by_id.get(outcome_id, {})
        has_bbox = bool(packet.get("source_page_number") and packet.get("source_bbox"))
        if has_bbox or outcome.get("decision") != "needs_page_bbox":
            continue
        evidence = find_evidence(packet, table_evidence, text_evidence, raw_rows)
        if evidence and evidence.get("page_number") and evidence.get("bbox"):
            status = "located"
            match_rule = str(evidence.get("match_rule") or "")
            if apply:
                packet["source_page_idx"] = evidence.get("page_idx")
                packet["source_page_number"] = evidence.get("page_number")
                packet["source_bbox"] = evidence.get("bbox") or []
                packet["source_content"] = str(evidence.get("content") or "")
                packet["source_raw_type"] = evidence.get("raw_type") or ""
                packet["source_image"] = evidence.get("img_path") or ""
                packet["source_match_rule"] = match_rule
                packet["source_match_score"] = evidence.get("match_score")
                packet["source_crop_status"] = "ready_for_source_crop"
                outcome["source_page_number"] = packet["source_page_number"]
                outcome["source_bbox"] = packet["source_bbox"]
                outcome["source_crop_status"] = "ready_for_source_crop"
                outcome["next_action"] = "generate_source_crop_for_manual_review"
        else:
            status = "unlocated"
            match_rule = ""
        status_counts[f"{packet.get('type')}:{status}"] += 1
        if match_rule:
            rule_counts[match_rule] += 1
        items.append(
            {
                "outcome_id": outcome_id,
                "packet_type": packet.get("type"),
                "block_id": packet.get("block_id"),
                "status": status,
                "match_rule": match_rule,
                "source_page_number": evidence.get("page_number") if evidence else None,
                "source_bbox": evidence.get("bbox") if evidence else [],
                "match_score": evidence.get("match_score") if evidence else None,
                "clean_text_preview": str(packet.get("clean_text") or "")[:500],
                "source_content_preview": str(evidence.get("content") or "")[:500] if evidence else "",
            }
        )

    report = {
        "schema": "luceon-standard-visual-bbox-backfill-audit/v1",
        "standard_dir": str(standard_dir),
        "mode": "apply" if apply else "audit",
        "policy": "raw_fallback_bboxes_are_source_location_evidence_not_automatic_acceptance",
        "raw_dir": str(raw_dir) if raw_dir else "",
        "status_counts": dict(status_counts),
        "match_rule_counts": dict(rule_counts),
        "items": items,
    }
    write_json(standard_dir / "visual_bbox_backfill_audit.json", report)
    if apply:
        write_json(visual_path, visual_packets)
        write_json(outcomes_path, review_outcomes)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_or_apply(args.standard_dir, apply=args.apply)
    print(json.dumps({k: v for k, v in report.items() if k != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
