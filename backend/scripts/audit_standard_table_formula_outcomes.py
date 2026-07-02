#!/usr/bin/env python3
"""Audit Standard table/formula review outcomes before deterministic closure."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

from standard_from_clean import normalize_review_compact_text, normalize_review_text, write_json

TABLE_FORMULA_PACKET_TYPES = {"table_visual_review", "formula_visual_review"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def outcome_id_for_packet(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


def packet_items(doc: dict[str, Any]) -> list[dict[str, Any]]:
    items = doc.get("items")
    return items if isinstance(items, list) else []


def classify_outcome(outcome: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    clean_text = str(packet.get("clean_text") or "")
    source_content = str(packet.get("source_content") or "")
    source_crop_status = str(outcome.get("source_crop_status") or packet.get("source_crop_status") or "")
    has_crop = source_crop_status in {"created", "reused"}
    has_bbox = bool(outcome.get("source_page_number") and outcome.get("source_bbox"))
    exact_match = bool(source_content) and normalize_review_text(clean_text) == normalize_review_text(source_content)
    clean_compact = normalize_review_compact_text(clean_text)
    source_compact = normalize_review_compact_text(source_content)
    compact_match = bool(source_content) and len(clean_compact) >= 40 and clean_compact == source_compact
    if not has_bbox:
        bucket = "needs_page_bbox"
    elif not has_crop:
        bucket = "needs_source_crop"
    elif exact_match:
        bucket = "deterministic_closure_candidate_exact_match"
    elif compact_match:
        bucket = "deterministic_closure_candidate_compact_match"
    elif source_content:
        bucket = "needs_manual_visual_review_source_mismatch"
    else:
        bucket = "needs_source_content"
    return {
        "outcome_id": outcome.get("outcome_id"),
        "packet_type": outcome.get("packet_type"),
        "block_id": outcome.get("block_id"),
        "status": outcome.get("status"),
        "decision": outcome.get("decision"),
        "bucket": bucket,
        "source_page_number": outcome.get("source_page_number"),
        "source_bbox": outcome.get("source_bbox") or [],
        "source_crop": outcome.get("source_crop") or packet.get("source_crop") or "",
        "source_crop_status": source_crop_status,
        "source_evidence_ready": bool(has_bbox and has_crop),
        "exact_normalized_match": exact_match,
        "compact_exact_match": compact_match,
        "clean_text_preview": clean_text[:500],
        "source_content_preview": source_content[:500],
    }


def build_audit(standard_dir: Path) -> dict[str, Any]:
    outcomes = read_json(standard_dir / "standard_review_outcomes.json")
    packets = read_json(standard_dir / "standard_visual_review_packets.json")
    packets_by_outcome = {outcome_id_for_packet(packet): packet for packet in packet_items(packets)}
    items: list[dict[str, Any]] = []
    for outcome in packet_items(outcomes):
        if outcome.get("packet_type") not in TABLE_FORMULA_PACKET_TYPES:
            continue
        packet = packets_by_outcome.get(str(outcome.get("outcome_id") or ""), {})
        items.append(classify_outcome(outcome, packet))

    bucket_counts = Counter(str(item.get("bucket") or "") for item in items)
    packet_type_counts = Counter(str(item.get("packet_type") or "") for item in items)
    bucket_by_packet_type: dict[str, dict[str, int]] = {}
    for item in items:
        packet_type = str(item.get("packet_type") or "")
        bucket = str(item.get("bucket") or "")
        row = bucket_by_packet_type.setdefault(packet_type, {})
        row[bucket] = row.get(bucket, 0) + 1
    closure_candidate_count = sum(
        1 for item in items if str(item.get("bucket") or "").startswith("deterministic_closure_candidate")
    )
    open_blocking_count = sum(
        1 for item in packet_items(outcomes) if item.get("status") == "open" and item.get("basic_print_blocking")
    )
    return {
        "schema": "luceon-standard-table-formula-outcome-audit/v1",
        "standard_dir": str(standard_dir),
        "policy": "audit_only_no_gate_closure",
        "decision_boundary": (
            "Deterministic closure candidates still require an explicit closure run; "
            "missing page/bbox and source mismatches remain blocking."
        ),
        "count": len(items),
        "packet_type_counts": dict(packet_type_counts),
        "bucket_counts": dict(bucket_counts),
        "bucket_by_packet_type": bucket_by_packet_type,
        "deterministic_closure_candidate_count": closure_candidate_count,
        "open_blocking_count_before_closure": open_blocking_count,
        "items": items,
    }


def build_html(audit: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in audit.items() if k != "items"}, ensure_ascii=False, indent=2)
    rows = []
    for item in audit.get("items", [])[:500]:
        crop = str(item.get("source_crop") or "")
        crop_html = f'<img src="{html.escape(crop)}" alt="source crop">' if crop else ""
        rows.append(
            "<article>"
            f"<h2>{html.escape(str(item.get('outcome_id') or ''))}</h2>"
            f"<p><strong>Bucket:</strong> {html.escape(str(item.get('bucket') or ''))} | "
            f"<strong>Type:</strong> {html.escape(str(item.get('packet_type') or ''))} | "
            f"<strong>Decision:</strong> {html.escape(str(item.get('decision') or ''))}</p>"
            f"{crop_html}"
            "<div class=\"pair\">"
            f"<pre>{html.escape(str(item.get('clean_text_preview') or ''))}</pre>"
            f"<pre>{html.escape(str(item.get('source_content_preview') or ''))}</pre>"
            "</div>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Table/Formula Outcome Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    pre {{ white-space: pre-wrap; border: 1px solid #bbb; padding: 12px; }}
    article {{ break-inside: avoid; border-top: 1px solid #bbb; padding: 14px 0; }}
    img {{ max-width: 100%; border: 1px solid #ccc; background: #fff; }}
    .pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  </style>
</head>
<body>
  <h1>Table/Formula Outcome Audit</h1>
  <pre>{html.escape(summary)}</pre>
  {''.join(rows)}
</body>
</html>"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    audit = build_audit(args.standard_dir)
    write_json(args.standard_dir / "table_formula_outcome_audit.json", audit)
    (args.standard_dir / "table_formula_outcome_audit.html").write_text(build_html(audit), encoding="utf-8")
    print(json.dumps({k: v for k, v in audit.items() if k != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
