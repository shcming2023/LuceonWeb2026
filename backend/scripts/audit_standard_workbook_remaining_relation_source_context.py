#!/usr/bin/env python3
"""Create source-context review package for remaining workbook relation gaps."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

import fitz

from standard_from_clean import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def packet_by_block_id(standard_dir: Path) -> dict[str, dict[str, Any]]:
    packets: dict[str, dict[str, Any]] = {}
    for name in ("standard_visual_review_packets.json", "image_visual_confirmation_packets.json"):
        data = read_json(standard_dir / name)
        for item in data.get("items") or []:
            block_id = str(item.get("block_id") or "")
            if block_id:
                packets[block_id] = item
    return packets


def render_context_crops(source_pdf: Path, records: list[dict[str, Any]], packets: dict[str, dict[str, Any]], out_dir: Path) -> None:
    if not source_pdf.exists():
        return
    crop_dir = out_dir / "source_context_crops"
    crop_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(source_pdf)
    for record in records:
        block_id = str(record.get("block_id") or "")
        packet = packets.get(block_id) or {}
        page_number = packet.get("source_page_number")
        bbox = packet.get("source_bbox")
        if not page_number or not bbox:
            continue
        page = doc[int(page_number) - 1]
        page.get_pixmap(matrix=fitz.Matrix(1.05, 1.05), alpha=False).save(crop_dir / f"{block_id}-full-page.png")
        rect = fitz.Rect(*bbox)
        expanded = fitz.Rect(rect.x0 - 180, rect.y0 - 240, rect.x1 + 260, rect.y1 + 280) & page.rect
        page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=expanded, alpha=False).save(
            crop_dir / f"{block_id}-expanded-context.png"
        )


def source_decision(record: dict[str, Any], packet: dict[str, Any]) -> tuple[str, str]:
    decision = str(record.get("decision") or "")
    if not packet.get("source_page_number") or not packet.get("source_bbox"):
        return "needs_source_bbox", "No page/bbox source location is available for focused review."
    if decision.startswith("contract_candidate"):
        return (
            "source_context_packet_ready_for_contract_review",
            "Candidate family has focused source context crops; it still needs family-level rule review before compiler promotion.",
        )
    return (
        "source_context_packet_ready_keep_review",
        "Review-only family has source context crops for manual/source-visual decision; do not auto-close.",
    )


def build_audit(standard_dir: Path, remaining_gap_audit: Path, source_pdf: Path, out_dir: Path) -> dict[str, Any]:
    remaining = read_json(remaining_gap_audit)
    source_records = [dict(record) for record in remaining.get("records") or []]
    packets = packet_by_block_id(standard_dir)
    render_context_crops(source_pdf, source_records, packets, out_dir)
    audited: list[dict[str, Any]] = []
    decision_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    for record in source_records:
        block_id = str(record.get("block_id") or "")
        packet = packets.get(block_id) or {}
        decision, reason = source_decision(record, packet)
        decision_counts[decision] += 1
        family_counts[str(record.get("family") or "")] += 1
        source_counts["has_source_bbox" if packet.get("source_page_number") and packet.get("source_bbox") else "missing_source_bbox"] += 1
        audited.append(
            {
                **record,
                "source_context_decision": decision,
                "source_context_reason": reason,
                "source_page_number": packet.get("source_page_number"),
                "source_bbox": packet.get("source_bbox") or [],
                "source_crop_status": packet.get("source_crop_status") or packet.get("crop_status") or "",
                "full_page_context_crop": f"source_context_crops/{block_id}-full-page.png" if packet else "",
                "expanded_context_crop": f"source_context_crops/{block_id}-expanded-context.png" if packet else "",
            }
        )
    return {
        "schema": "luceon-standard-workbook-remaining-relation-source-context-audit/v1",
        "standard_dir": str(standard_dir),
        "remaining_gap_audit": str(remaining_gap_audit),
        "source_pdf": str(source_pdf),
        "policy": "focused_source_context_review_package_no_gate_closure",
        "decision_boundary": (
            "This audit creates source-context review evidence for the remaining workbook relation gaps. "
            "It does not close relation gates or promote table/figure families without a later compiler rerun."
        ),
        "record_count": len(audited),
        "source_location_counts": dict(source_counts),
        "source_context_decision_counts": dict(decision_counts),
        "family_counts": dict(family_counts),
        "gate_implications": {
            "can_promote_exercise_workbook_profile": False,
            "can_close_remaining_relation_gaps": False,
            "required_next_action": "review_source_context_crops_then_encode_only_narrow_table_or_figure_contracts",
        },
        "records": audited,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2)
    rows = []
    for item in report.get("records") or []:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('source_context_decision') or ''))}</td>"
            f"<td>{html.escape(str(item.get('decision') or ''))}</td>"
            f"<td>{html.escape(str(item.get('family') or ''))}</td>"
            f"<td>{html.escape(str(item.get('kind') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(item.get('source_page_number') or ''))}</td>"
            f"<td><img src=\"{html.escape(str(item.get('expanded_context_crop') or ''))}\"></td>"
            f"<td><img src=\"{html.escape(str(item.get('full_page_context_crop') or ''))}\"></td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Remaining Relation Source Context Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    img {{ max-width: 520px; border: 1px solid #bbb; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Workbook Remaining Relation Source Context Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Source Decision</th><th>Gap Decision</th><th>Family</th><th>Kind</th><th>Block</th><th>Page</th><th>Expanded</th><th>Full Page</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--remaining-gap-audit", required=True, type=Path)
    parser.add_argument("--source-pdf", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_audit(args.standard_dir, args.remaining_gap_audit, args.source_pdf, args.out_dir)
    write_json(args.out_dir / "workbook_remaining_relation_source_context_audit.json", report)
    (args.out_dir / "workbook_remaining_relation_source_context_audit.html").write_text(
        build_html(report),
        encoding="utf-8",
    )
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
