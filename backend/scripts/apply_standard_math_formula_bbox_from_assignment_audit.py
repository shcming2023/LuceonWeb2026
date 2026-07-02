#!/usr/bin/env python3
"""Apply high-confidence Math formula bbox candidates from assignment audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def outcome_id_for_packet(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


def apply_audit(standard_dir: Path, audit_path: Path, allowed_statuses: set[str]) -> dict[str, Any]:
    visual_path = standard_dir / "standard_visual_review_packets.json"
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    visual_packets = read_json(visual_path)
    review_outcomes = read_json(outcomes_path)
    audit = read_json(audit_path)
    records_by_block = {
        str(record.get("block_id") or ""): record
        for record in audit.get("records") or []
        if record.get("status") in allowed_statuses and len(record.get("candidates") or []) == 1
    }
    outcomes_by_id = {str(item.get("outcome_id") or ""): item for item in review_outcomes.get("items") or []}
    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for packet in visual_packets.get("items") or []:
        if packet.get("type") != "formula_visual_review":
            continue
        block_id = str(packet.get("block_id") or "")
        record = records_by_block.get(block_id)
        if not record:
            continue
        if packet.get("source_page_number") and packet.get("source_bbox"):
            skipped.append({"block_id": block_id, "reason": "already_has_bbox"})
            continue
        candidate = (record.get("candidates") or [{}])[0]
        page_number = candidate.get("page_number")
        bbox = candidate.get("bbox") or []
        if not page_number or len(bbox) != 4:
            skipped.append({"block_id": block_id, "reason": "candidate_missing_page_or_bbox"})
            continue
        packet["source_page_idx"] = int(page_number) - 1
        packet["source_page_number"] = int(page_number)
        packet["source_bbox"] = bbox
        packet["source_content"] = candidate.get("text_preview") or ""
        packet["source_raw_type"] = "raw_block_assignment"
        packet["source_image"] = ""
        packet["source_match_rule"] = f"raw_assignment.{record.get('status')}"
        packet["source_match_score"] = 1.0
        packet["source_crop_status"] = "ready_for_source_crop"
        packet["crop_status"] = "ready_for_source_crop"
        outcome = outcomes_by_id.get(outcome_id_for_packet(packet))
        if outcome:
            outcome["source_page_number"] = packet["source_page_number"]
            outcome["source_bbox"] = packet["source_bbox"]
            outcome["source_crop_status"] = "ready_for_source_crop"
            outcome["source_evidence_ready"] = False
            outcome["decision"] = "needs_source_crop"
            outcome["next_action"] = "generate_source_crop_for_manual_review"
            outcome["notes"] = "High-confidence raw assignment bbox applied as source-location evidence only; outcome remains open."
        applied.append(
            {
                "block_id": block_id,
                "status": record.get("status"),
                "page_number": page_number,
                "bbox": bbox,
                "text_preview": candidate.get("text_preview") or "",
            }
        )

    write_json(visual_path, visual_packets)
    write_json(outcomes_path, review_outcomes)
    report = {
        "schema": "luceon-standard-math-formula-assignment-bbox-apply/v1",
        "standard_dir": str(standard_dir),
        "audit_path": str(audit_path),
        "policy": "apply_high_confidence_source_location_only_no_outcome_closure",
        "allowed_statuses": sorted(allowed_statuses),
        "applied_count": len(applied),
        "skipped_count": len(skipped),
        "gate_implications": {
            "can_close_formula_outcomes": False,
            "can_promote_math_textbook_profile": False,
            "required_next_action": "generate_source_crops_then_manual_or_rule_visual_review",
        },
        "applied": applied,
        "skipped": skipped,
    }
    write_json(standard_dir / "math_formula_assignment_bbox_apply_report.json", report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--allowed-status", action="append", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    allowed_statuses = set(args.allowed_status or ["located_exact"])
    report = apply_audit(args.standard_dir, args.audit, allowed_statuses)
    print(json.dumps({k: v for k, v in report.items() if k not in {"applied", "skipped"}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
