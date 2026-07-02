#!/usr/bin/env python3
"""Source-context audit for table candidates that required visual review before contract."""

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
        if record.get("contract_status") == "candidate_requires_visual_review_before_contract"
    ]


def packet_by_block_id(standard_dir: Path) -> dict[str, dict[str, Any]]:
    packets = read_json(standard_dir / "standard_visual_review_packets.json")
    items = packets.get("items") if isinstance(packets.get("items"), list) else []
    return {str(item.get("block_id") or ""): item for item in items if str(item.get("block_id") or "")}


def outcome_by_block_id(standard_dir: Path) -> dict[str, dict[str, Any]]:
    outcomes = read_json(standard_dir / "standard_review_outcomes.json")
    items = outcomes.get("items") if isinstance(outcomes.get("items"), list) else []
    return {str(item.get("block_id") or ""): item for item in items if str(item.get("block_id") or "")}


def classify_context(record: dict[str, Any]) -> tuple[str, str, str]:
    heading = " > ".join(record.get("heading_path") or [])
    previous = str(record.get("previous_text") or "")
    next_text = str(record.get("next_text") or "")
    if "Two-Way Relative Frequency Tables" in heading and "relative frequency table" in previous:
        return (
            "accepted_for_contract_by_source_context",
            "example_relative_frequency_question_table_explanation",
            "Source page shows an example question, its relative-frequency table, and the immediate explanation as one teaching unit.",
        )
    if "Make Comparative Inferences About Populations" in heading and "measures of center and variability" in previous:
        return (
            "accepted_for_contract_by_source_context",
            "example_statistics_question_table_explanation",
            "Source page shows an example statistics question, supporting table, and immediate inferential explanation as one teaching unit.",
        )
    if next_text:
        return (
            "keep_review",
            "unclassified_question_table_explanation",
            "The table has neighboring explanation text but does not match an accepted source-context family.",
        )
    return ("keep_review", "unclassified_question_table", "No accepted source-context family matched.")


def render_crops(source_pdf: Path, records: list[dict[str, Any]], packets: dict[str, dict[str, Any]], out_dir: Path) -> None:
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
        page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False).save(crop_dir / f"{block_id}-full-page.png")
        rect = fitz.Rect(*bbox)
        expanded = fitz.Rect(rect.x0 - 160, rect.y0 - 210, rect.x1 + 220, rect.y1 + 250) & page.rect
        page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=expanded, alpha=False).save(
            crop_dir / f"{block_id}-expanded-context.png"
        )


def build_audit(base_dir: Path, contract_audit_path: Path, source_pdf: Path, out_dir: Path) -> dict[str, Any]:
    contract = read_json(contract_audit_path)
    records = candidate_records(contract)
    packets = packet_by_block_id(base_dir)
    outcomes = outcome_by_block_id(base_dir)
    render_crops(source_pdf, records, packets, out_dir)
    audited: list[dict[str, Any]] = []
    for record in records:
        block_id = str(record.get("block_id") or "")
        packet = packets.get(block_id) or {}
        outcome = outcomes.get(block_id) or {}
        decision, family, reason = classify_context(record)
        audited.append(
            {
                "block_id": block_id,
                "visual_review_contract_decision": decision,
                "contract_family": family,
                "profile_contract_ready": decision == "accepted_for_contract_by_source_context",
                "reason": reason,
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
                "heading_path": record.get("heading_path") or [],
                "previous_text": record.get("previous_text") or "",
                "table_text": record.get("text") or "",
                "next_text": record.get("next_text") or "",
            }
        )
    ready_count = sum(1 for record in audited if record["profile_contract_ready"])
    return {
        "schema": "luceon-standard-workbook-table-attachment-visual-review-audit/v1",
        "base_standard_dir": str(base_dir),
        "contract_audit": str(contract_audit_path),
        "source_pdf": str(source_pdf),
        "policy": "source_context_visual_review_no_gate_closure",
        "decision_boundary": (
            "This audit reviews only the question-like table candidates that previously required visual review "
            "before contract. It can propose narrow example-table contract families, but it does not authorize "
            "broad question-like table attachment or promote exercise_workbook."
        ),
        "candidate_count": len(audited),
        "contract_ready_count": ready_count,
        "keep_review_count": len(audited) - ready_count,
        "contract_family_counts": {
            family: sum(1 for record in audited if record["contract_family"] == family)
            for family in sorted({record["contract_family"] for record in audited})
        },
        "gate_implications": {
            "can_promote_exercise_workbook_profile": False,
            "can_add_broad_question_like_table_rule": False,
            "can_add_visual_reviewed_example_table_contracts": ready_count == len(audited) and ready_count > 0,
            "required_next_action": "encode_only_the_visual_reviewed_example_table_families_or_test_cross_sample_before_compiler_promotion",
        },
        "records": audited,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2)
    rows = []
    for record in report.get("records") or []:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(record.get('visual_review_contract_decision') or ''))}</td>"
            f"<td>{html.escape(str(record.get('contract_family') or ''))}</td>"
            f"<td>{html.escape(str(record.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(record.get('reason') or ''))}</td>"
            f"<td><img src=\"{html.escape(str(record.get('full_page_context_crop') or ''))}\"></td>"
            f"<td><img src=\"{html.escape(str(record.get('expanded_context_crop') or ''))}\"></td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Table Attachment Visual Review Audit</title>
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
  <h1>Workbook Table Attachment Visual Review Audit</h1>
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
    write_json(args.out_dir / "workbook_table_attachment_visual_review_audit.json", report)
    (args.out_dir / "workbook_table_attachment_visual_review_audit.html").write_text(
        build_html(report), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
