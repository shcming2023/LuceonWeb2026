#!/usr/bin/env python3
"""Classify remaining table/formula needs_page_bbox blockers without closing them."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def outcome_id_for_packet(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


def item_list(doc: dict[str, Any]) -> list[dict[str, Any]]:
    items = doc.get("items")
    return items if isinstance(items, list) else []


def classify_text_shape(text: str) -> list[str]:
    shape: list[str] = []
    stripped = text.strip()
    if "![" in text:
        shape.append("markdown_image")
    if "<table" in text.lower():
        shape.append("html_table")
    if re.search(r"^[A-H][\s\-.()]", stripped):
        shape.append("option_line")
    if re.search(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]", stripped):
        shape.append("circled_item")
    if "STEP" in text or "Step" in text:
        shape.append("procedure_text")
    if len(text) < 20:
        shape.append("short_formula")
    if len(text) > 180:
        shape.append("long_text_with_formula")
    return shape or ["formula_or_text"]


def recommended_action(audit_bucket: str, text_shape: list[str], packet_type: str) -> str:
    if packet_type == "table_visual_review":
        return "table_source_locator_or_manual_crop_review"
    if "markdown_image" in text_shape:
        return "reclassify_formula_packet_or_route_to_image_relation_review"
    if audit_bucket == "ambiguous_math_normalized_match":
        return "manual_select_source_candidate_or_add_disambiguation_rule"
    if audit_bucket == "ambiguous_short_global_match_needs_manual":
        return "manual_review_short_global_candidate"
    if audit_bucket == "too_short_for_location_rule":
        return "manual_source_crop_or_context_window_locator_required"
    if audit_bucket == "no_math_normalized_raw_match":
        return "raw_text_sequence_or_context_window_locator_required"
    return "manual_review_required"


def build_audit(standard_dir: Path) -> dict[str, Any]:
    outcomes = read_json(standard_dir / "standard_review_outcomes.json")
    packets = read_json(standard_dir / "standard_visual_review_packets.json")
    formula_audit = read_json(standard_dir / "formula_bbox_candidate_audit.json")
    packets_by_outcome = {outcome_id_for_packet(packet): packet for packet in item_list(packets)}
    formula_by_outcome = {
        str(item.get("outcome_id") or ""): item
        for item in item_list(formula_audit)
        if isinstance(item, dict) and item.get("outcome_id")
    }

    items: list[dict[str, Any]] = []
    for outcome in item_list(outcomes):
        if outcome.get("status") != "open" or not outcome.get("basic_print_blocking"):
            continue
        if outcome.get("decision") != "needs_page_bbox":
            continue
        packet_type = str(outcome.get("packet_type") or "")
        if packet_type not in {"formula_visual_review", "table_visual_review"}:
            continue
        packet = packets_by_outcome.get(str(outcome.get("outcome_id") or ""), {})
        formula_row = formula_by_outcome.get(str(outcome.get("outcome_id") or ""), {})
        clean_text = str(packet.get("clean_text") or formula_row.get("clean_text_preview") or "")
        text_shape = classify_text_shape(clean_text)
        audit_bucket = str(formula_row.get("bucket") or "table_needs_source_locator")
        items.append(
            {
                "outcome_id": outcome.get("outcome_id"),
                "block_id": outcome.get("block_id"),
                "packet_type": packet_type,
                "status": outcome.get("status"),
                "decision": outcome.get("decision"),
                "audit_bucket": audit_bucket,
                "text_shape": text_shape,
                "recommended_action": recommended_action(audit_bucket, text_shape, packet_type),
                "heading_path": packet.get("heading_path") or formula_row.get("heading_path") or [],
                "candidate_count": formula_row.get("candidate_count"),
                "candidate_pages": formula_row.get("candidate_pages"),
                "source_units": formula_row.get("source_units"),
                "math_location_key_length": formula_row.get("math_location_key_length"),
                "clean_text_preview": clean_text[:500],
            }
        )

    bucket_counts = Counter(str(item.get("audit_bucket") or "") for item in items)
    action_counts = Counter(str(item.get("recommended_action") or "") for item in items)
    packet_type_counts = Counter(str(item.get("packet_type") or "") for item in items)
    text_shape_counts: Counter[str] = Counter()
    for item in items:
        text_shape_counts["|".join(item.get("text_shape") or [])] += 1
    return {
        "schema": "luceon-standard-remaining-bbox-blocker-audit/v1",
        "standard_dir": str(standard_dir),
        "policy": "audit_only_no_bbox_backfill_no_closure",
        "decision_boundary": (
            "Remaining needs_page_bbox blockers are classified for next-step planning only. "
            "This audit does not backfill source bboxes, close outcomes, or change Basic Print status."
        ),
        "count": len(items),
        "packet_type_counts": dict(packet_type_counts),
        "bucket_counts": dict(bucket_counts),
        "text_shape_counts": dict(text_shape_counts),
        "recommended_action_counts": dict(action_counts),
        "items": items,
    }


def build_html(audit: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in audit.items() if k != "items"}, ensure_ascii=False, indent=2)
    rows = []
    for item in audit.get("items", [])[:500]:
        rows.append(
            "<article>"
            f"<h2>{html.escape(str(item.get('outcome_id') or ''))}</h2>"
            f"<p><strong>Action:</strong> {html.escape(str(item.get('recommended_action') or ''))} | "
            f"<strong>Bucket:</strong> {html.escape(str(item.get('audit_bucket') or ''))} | "
            f"<strong>Shape:</strong> {html.escape(', '.join(item.get('text_shape') or []))}</p>"
            f"<p><strong>Heading:</strong> {html.escape(' > '.join(item.get('heading_path') or []))}</p>"
            f"<pre>{html.escape(str(item.get('clean_text_preview') or ''))}</pre>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Remaining Bbox Blocker Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    article {{ border-top: 1px solid #ddd; padding: 16px 0; }}
    pre {{ white-space: pre-wrap; background: #f6f6f6; padding: 10px; overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <h1>Remaining Bbox Blocker Audit</h1>
  <pre>{html.escape(summary)}</pre>
  {''.join(rows)}
</body>
</html>
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    audit = build_audit(args.standard_dir)
    write_json(args.standard_dir / "remaining_bbox_blocker_audit.json", audit)
    (args.standard_dir / "remaining_bbox_blocker_audit.html").write_text(build_html(audit), encoding="utf-8")
    print(json.dumps({k: v for k, v in audit.items() if k != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
