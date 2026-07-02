#!/usr/bin/env python3
"""Source-context spot audit for non-paired table-attachment candidates."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

import fitz

from standard_from_clean import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def candidate_records(contract_audit: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        record
        for record in contract_audit.get("records") or []
        if record.get("contract_status") == "candidate_needs_source_visual_spot_audit"
    ]


def packet_by_block_id(standard_dir: Path) -> dict[str, dict[str, Any]]:
    packets = read_json(standard_dir / "standard_visual_review_packets.json")
    items = packets.get("items") if isinstance(packets.get("items"), list) else []
    return {str(item.get("block_id") or ""): item for item in items if str(item.get("block_id") or "")}


def review_outcome_by_block_id(standard_dir: Path) -> dict[str, dict[str, Any]]:
    outcomes = read_json(standard_dir / "standard_review_outcomes.json")
    items = outcomes.get("items") if isinstance(outcomes.get("items"), list) else []
    return {str(item.get("block_id") or ""): item for item in items if str(item.get("block_id") or "")}


def classify_context(record: dict[str, Any]) -> tuple[str, str, str]:
    previous = str(record.get("previous_text") or "")
    next_text = str(record.get("next_text") or "")
    table_shape = str(record.get("table_shape") or "")
    if "Look for Relationships" in previous and next_text.startswith("STEP"):
        return (
            "accepted_for_contract_by_source_context",
            "example_step_data_table_keep_with_explanation",
            "Source context places the table inside an example flow between a Look for Relationships prompt and STEP explanation.",
        )
    if previous.startswith("Complete each sentence by matching") and next_text.startswith("Use Vocabulary in Writing"):
        return (
            "accepted_for_contract_by_source_context",
            "single_table_vocabulary_review",
            "Source context places the table directly under a Vocabulary Review matching instruction and before Use Vocabulary in Writing.",
        )
    if table_shape in {"data_table", "math_table"}:
        return (
            "needs_visual_review_before_contract",
            "non_paired_data_or_math_table",
            "Non-paired data/math table does not match a currently accepted source-context contract.",
        )
    return (
        "needs_visual_review_before_contract",
        "unclassified_non_paired_table",
        "No accepted source-context contract matched.",
    )


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
        rect = page.rect
        crop_path = crop_dir / f"{block_id}-full-page.png"
        if not crop_path.exists():
            page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False).save(crop_path)
        source_rect = fitz.Rect(*bbox)
        expanded = fitz.Rect(source_rect.x0 - 140, source_rect.y0 - 190, source_rect.x1 + 180, source_rect.y1 + 240)
        expanded &= rect
        expanded_path = crop_dir / f"{block_id}-expanded-context.png"
        if not expanded_path.exists():
            page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=expanded, alpha=False).save(expanded_path)


def build_audit(base_dir: Path, contract_audit_path: Path, source_pdf: Path, out_dir: Path) -> dict[str, Any]:
    contract = read_json(contract_audit_path)
    records = candidate_records(contract)
    packets = packet_by_block_id(base_dir)
    outcomes = review_outcome_by_block_id(base_dir)
    render_context_crops(source_pdf, records, packets, out_dir)
    audited_records: list[dict[str, Any]] = []
    for record in records:
        block_id = str(record.get("block_id") or "")
        packet = packets.get(block_id) or {}
        outcome = outcomes.get(block_id) or {}
        decision, contract_family, reason = classify_context(record)
        audited_records.append(
            {
                "block_id": block_id,
                "spot_audit_decision": decision,
                "contract_family": contract_family,
                "reason": reason,
                "profile_contract_ready": decision == "accepted_for_contract_by_source_context",
                "source_page_number": packet.get("source_page_number"),
                "source_bbox": packet.get("source_bbox") or [],
                "source_crop": packet.get("source_crop") or "",
                "source_crop_status": packet.get("source_crop_status") or "",
                "full_page_context_crop": f"source_context_crops/{block_id}-full-page.png",
                "expanded_context_crop": f"source_context_crops/{block_id}-expanded-context.png",
                "visual_review_decision": outcome.get("decision") or "",
                "visual_review_status": outcome.get("status") or "",
                "policy_bucket": record.get("policy_bucket") or "",
                "risk_level": record.get("risk_level") or "",
                "table_shape": record.get("table_shape") or "",
                "previous_context_kind": record.get("previous_context_kind") or "",
                "next_context_kind": record.get("next_context_kind") or "",
                "heading_path": record.get("heading_path") or [],
                "previous_text": record.get("previous_text") or "",
                "table_text": record.get("text") or "",
                "next_text": record.get("next_text") or "",
            }
        )
    ready_count = sum(1 for record in audited_records if record["profile_contract_ready"])
    return {
        "schema": "luceon-standard-workbook-table-attachment-spot-audit/v1",
        "base_standard_dir": str(base_dir),
        "contract_audit": str(contract_audit_path),
        "source_pdf": str(source_pdf),
        "policy": "source_context_spot_audit_no_gate_closure",
        "decision_boundary": (
            "This audit checks only the non-paired low/medium table-attachment candidates that disappeared "
            "in the comparison run. It can propose narrow source-context contract families, but it does not "
            "close exercise_workbook profile gates or authorize broad table attachment."
        ),
        "candidate_count": len(audited_records),
        "contract_ready_count": ready_count,
        "needs_visual_review_count": len(audited_records) - ready_count,
        "contract_family_counts": {
            family: sum(1 for record in audited_records if record["contract_family"] == family)
            for family in sorted({record["contract_family"] for record in audited_records})
        },
        "gate_implications": {
            "can_promote_exercise_workbook_profile": False,
            "can_add_broad_table_attachment_rule": False,
            "can_add_non_paired_spot_contracts": ready_count == len(audited_records) and ready_count > 0,
            "required_next_action": "encode_only_the_two_source_context_contract_families_or_keep_as_review_until_cross_sample_evidence",
        },
        "records": audited_records,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2)
    rows = []
    for record in report.get("records") or []:
        full = record.get("full_page_context_crop") or ""
        expanded = record.get("expanded_context_crop") or ""
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(record.get('spot_audit_decision') or ''))}</td>"
            f"<td>{html.escape(str(record.get('contract_family') or ''))}</td>"
            f"<td>{html.escape(str(record.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(record.get('reason') or ''))}</td>"
            f"<td>{'<img src=' + html.escape(full) + '>' if full else ''}</td>"
            f"<td>{'<img src=' + html.escape(expanded) + '>' if expanded else ''}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Table Attachment Spot Audit</title>
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
  <h1>Workbook Table Attachment Spot Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Decision</th><th>Contract Family</th><th>Block</th><th>Reason</th><th>Full Page</th><th>Expanded</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-standard-dir", required=True, type=Path)
    parser.add_argument("--contract-audit", required=True, type=Path)
    parser.add_argument("--source-pdf", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_audit(args.base_standard_dir, args.contract_audit, args.source_pdf, args.out_dir)
    write_json(args.out_dir / "workbook_table_attachment_spot_audit.json", report)
    (args.out_dir / "workbook_table_attachment_spot_audit.html").write_text(build_html(report), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
