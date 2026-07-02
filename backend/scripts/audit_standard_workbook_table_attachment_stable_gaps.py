#!/usr/bin/env python3
"""Audit stable workbook table-attachment gaps that delta evidence did not close."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import fitz

from standard_from_clean import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def stable_records(contract_audit: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        record
        for record in contract_audit.get("records") or []
        if record.get("contract_status") == "not_proven_stable_gap"
    ]


def items_by_block_id(path: Path, key: str = "items") -> dict[str, dict[str, Any]]:
    data = read_json(path)
    items = data.get(key) if isinstance(data.get(key), list) else []
    return {str(item.get("block_id") or ""): item for item in items if str(item.get("block_id") or "")}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def classify_stable_gap(record: dict[str, Any]) -> tuple[str, str, str]:
    heading = " > ".join(record.get("heading_path") or [])
    previous = normalize_text(str(record.get("previous_text") or ""))
    table = normalize_text(str(record.get("text") or ""))
    next_text = normalize_text(str(record.get("next_text") or ""))
    policy = str(record.get("policy_bucket") or "")
    shape = str(record.get("table_shape") or "")
    prev_kind = str(record.get("previous_context_kind") or "")
    next_kind = str(record.get("next_context_kind") or "")

    if "Topic Review" in heading and "Vocabulary Term" in table and "Use Vocabulary in Writing" in next_text:
        return (
            "contract_candidate_requires_rule_rerun",
            "single_table_vocabulary_review",
            "Source context is a topic-review vocabulary matching table, but the gap is stable and still needs an explicit compiler rule rerun.",
        )
    if next_kind == "adjacent_table":
        return (
            "keep_review_requires_multi_table_grouping",
            "paired_or_adjacent_sample_tables",
            "The table is followed by another table, so a single-table attachment rule would risk splitting a multi-table sample unit.",
        )
    if "scatter plot" in (previous + " " + next_text).lower() and shape in {"data_table", "math_table"}:
        return (
            "contract_candidate_requires_rule_rerun",
            "exercise_scatter_plot_data_table",
            "The table is the data source for a scatter-plot exercise, but it remained a relation gap and needs an exercise-data-table rule rerun.",
        )
    if "bar diagram" in previous.lower() or "bar diagram" in next_text.lower():
        return (
            "contract_candidate_requires_rule_rerun",
            "example_bar_diagram_table_model",
            "The table is a visual model tied to a bar-diagram instruction and equation, requiring a narrow model-table rendering rule.",
        )
    if prev_kind == "instruction" and "classify each number" in previous.lower() and "rational" in table.lower():
        return (
            "contract_candidate_requires_rule_rerun",
            "exercise_classification_data_table",
            "The table supplies values for a classification exercise, but it is still stable as an orphan table and needs a grouping rule rerun.",
        )
    if "frequency table" in (previous + " " + next_text).lower() and shape in {"data_table", "blank_answer_table"}:
        return (
            "contract_candidate_requires_rule_rerun",
            "example_frequency_table_explanation",
            "The table is embedded in a frequency-table teaching explanation, but stable-gap status requires explicit rule testing.",
        )
    if "mean" in table.lower() and ("mad" in table.lower() or "absolute deviation" in table.lower()):
        return (
            "contract_candidate_requires_rule_rerun",
            "example_statistics_summary_table",
            "The table summarizes mean/MAD values for a statistics explanation, but it still needs a profile rule rerun before closure.",
        )
    if "constant of proportionality" in next_text.lower() or "look for a pattern" in previous.lower():
        return (
            "contract_candidate_requires_rule_rerun",
            "example_pattern_or_rate_table",
            "The table supports a worked pattern/rate explanation, but this audit cannot close a stable relation gap by inspection alone.",
        )
    if policy == "question_like_paragraph_table_needs_visual_review":
        return (
            "keep_review_needs_source_visual_contract",
            "unclassified_question_like_table",
            "Question-like table context has no narrow accepted contract family yet; keep review instead of adding a broad rule.",
        )
    return (
        "keep_review_no_contract_signal",
        "unclassified_stable_table_gap",
        "No source-context contract family matched; keep as review.",
    )


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
        page.get_pixmap(matrix=fitz.Matrix(1.15, 1.15), alpha=False).save(crop_dir / f"{block_id}-full-page.png")
        rect = fitz.Rect(*bbox)
        expanded = fitz.Rect(rect.x0 - 170, rect.y0 - 220, rect.x1 + 240, rect.y1 + 260) & page.rect
        page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=expanded, alpha=False).save(
            crop_dir / f"{block_id}-expanded-context.png"
        )


def build_audit(base_dir: Path, contract_audit_path: Path, source_pdf: Path, out_dir: Path) -> dict[str, Any]:
    contract = read_json(contract_audit_path)
    records = stable_records(contract)
    packets = items_by_block_id(base_dir / "standard_visual_review_packets.json")
    outcomes = items_by_block_id(base_dir / "standard_review_outcomes.json")
    relation_items = items_by_block_id(base_dir / "workbook_relation_audit.json")
    render_crops(source_pdf, records, packets, out_dir)

    audited: list[dict[str, Any]] = []
    for record in records:
        block_id = str(record.get("block_id") or "")
        packet = packets.get(block_id) or {}
        outcome = outcomes.get(block_id) or {}
        relation = relation_items.get(block_id) or {}
        decision, family, reason = classify_stable_gap(record)
        audited.append(
            {
                "block_id": block_id,
                "stable_gap_decision": decision,
                "contract_family": family,
                "reason": reason,
                "profile_contract_ready": False,
                "requires_compiler_rerun": decision == "contract_candidate_requires_rule_rerun",
                "relation_disposition": relation.get("disposition") or "",
                "relation_kind": relation.get("kind") or "",
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

    decision_counts = Counter(record["stable_gap_decision"] for record in audited)
    family_counts = Counter(record["contract_family"] for record in audited)
    candidate_count = decision_counts["contract_candidate_requires_rule_rerun"]
    keep_review_count = len(audited) - candidate_count
    return {
        "schema": "luceon-standard-workbook-table-attachment-stable-gap-audit/v1",
        "base_standard_dir": str(base_dir),
        "contract_audit": str(contract_audit_path),
        "source_pdf": str(source_pdf),
        "policy": "stable_gap_audit_no_gate_closure_no_broad_rule",
        "decision_boundary": (
            "This audit reviews the stable low/medium orphan-table gaps that were not removed by the comparison run. "
            "Because these gaps remain real relation gaps, this audit can only propose narrow compiler-rule candidates "
            "or keep review; it cannot mark them accepted, close the profile, or authorize broad table attachment."
        ),
        "stable_gap_count": len(audited),
        "contract_candidate_requires_rule_rerun_count": candidate_count,
        "keep_review_count": keep_review_count,
        "stable_gap_decision_counts": dict(decision_counts),
        "contract_family_counts": dict(family_counts),
        "gate_implications": {
            "can_promote_exercise_workbook_profile": False,
            "can_close_stable_table_gaps": False,
            "can_add_broad_table_attachment_rule": False,
            "can_add_contract_without_compiler_rerun": False,
            "required_next_action": "encode_narrow_candidate_rules_then_rerun_g7plus_relation_audit_or_keep_review",
        },
        "records": audited,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2)
    rows = []
    for record in report.get("records") or []:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(record.get('stable_gap_decision') or ''))}</td>"
            f"<td>{html.escape(str(record.get('contract_family') or ''))}</td>"
            f"<td>{html.escape(str(record.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(record.get('reason') or ''))}</td>"
            f"<td>{html.escape(str(record.get('visual_review_decision') or ''))}</td>"
            f"<td><img src=\"{html.escape(str(record.get('full_page_context_crop') or ''))}\"></td>"
            f"<td><img src=\"{html.escape(str(record.get('expanded_context_crop') or ''))}\"></td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Table Attachment Stable Gap Audit</title>
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
  <h1>Workbook Table Attachment Stable Gap Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Decision</th><th>Contract Family</th><th>Block</th><th>Reason</th><th>Outcome</th><th>Full Page</th><th>Expanded</th></tr></thead>
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
    write_json(args.out_dir / "workbook_table_attachment_stable_gap_audit.json", report)
    (args.out_dir / "workbook_table_attachment_stable_gap_audit.html").write_text(
        build_html(report), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
