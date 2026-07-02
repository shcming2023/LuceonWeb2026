#!/usr/bin/env python3
"""Simulate workbook table attachment policies without mutating Standard."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from audit_standard_workbook_relation_gap_patterns import (  # noqa: E402
    INSTRUCTION_START_RE,
    SECTION_LABELS,
    block_text,
    compact_text,
    read_json,
)
from standard_from_clean import write_json


STEP_RE = re.compile(r"^STEP\s+\d+\b", re.I)
EXPLANATION_LABEL_RE = re.compile(r"^(?:EXAMPLE|ONE WAY|ANOTHER WAY|STEP\s+\d+|Convince Me!|Try It!)\b", re.I)
QUESTION_SIGNAL_RE = re.compile(r"\?|(?:Classify|Complete|Draw|Fill|Find|Graph|Match|Organize|Solve|Use|Write)\b", re.I)


def normalize_label(text: str) -> str:
    return compact_text(text).strip("* ").lower()


def relation_table_gap_items(relation_audit: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in relation_audit.get("items") or []
        if item.get("kind") == "orphan_table_question" and item.get("disposition") == "real_profile_gap"
    ]


def block_summary(block: dict[str, Any] | None) -> dict[str, Any]:
    block = block or {}
    return {
        "id": block.get("id"),
        "type": block.get("type"),
        "subtype": block.get("subtype") or "",
        "line_start": block.get("line_start"),
        "text": block_text(block)[:300],
    }


def table_shape(table_text: str) -> str:
    lowered = table_text.lower()
    if "vocabulary word" in lowered or "definition" in lowered:
        return "vocabulary_or_definition_table"
    if re.search(r">\s*</td>|<td>\s*</td>", table_text):
        return "blank_answer_table"
    if re.search(r"\$\s*|\\frac|\\sqrt|\\times|\\cdot|\\text", table_text):
        return "math_table"
    if re.search(r"\d", table_text):
        return "data_table"
    return "text_table"


def previous_context_kind(previous: dict[str, Any]) -> str:
    prev_text = compact_text(str(previous.get("text") or ""))
    prev_norm = normalize_label(prev_text)
    prev_type = str(previous.get("type") or "")
    if prev_type == "question":
        return "adjacent_question"
    if prev_type == "table":
        return "adjacent_table"
    if prev_norm in SECTION_LABELS:
        return "section_label"
    if STEP_RE.match(prev_text):
        return "step_explanation"
    if INSTRUCTION_START_RE.match(prev_text):
        return "instruction"
    if EXPLANATION_LABEL_RE.match(prev_text):
        return "explanation_label"
    if prev_text.endswith(":"):
        return "colon_prompt"
    if len(prev_text) <= 40 and not QUESTION_SIGNAL_RE.search(prev_text):
        return "short_label_or_fragment"
    if QUESTION_SIGNAL_RE.search(prev_text):
        return "question_like_paragraph"
    return "paragraph"


def next_context_kind(next_block: dict[str, Any]) -> str:
    next_text = compact_text(str(next_block.get("text") or ""))
    next_norm = normalize_label(next_text)
    next_type = str(next_block.get("type") or "")
    if next_type == "question":
        return "adjacent_question"
    if next_type == "table":
        return "adjacent_table"
    if next_type == "captioned_figure":
        return "figure"
    if next_norm in SECTION_LABELS:
        return "section_label"
    if STEP_RE.match(next_text):
        return "step_explanation"
    if EXPLANATION_LABEL_RE.match(next_text):
        return "explanation_label"
    if INSTRUCTION_START_RE.match(next_text):
        return "instruction"
    if QUESTION_SIGNAL_RE.search(next_text):
        return "question_like_paragraph"
    return "paragraph"


def classify_policy(item: dict[str, Any]) -> tuple[str, str, str]:
    previous = item.get("previous_block") if isinstance(item.get("previous_block"), dict) else {}
    next_block = item.get("next_block") if isinstance(item.get("next_block"), dict) else {}
    table_text = compact_text(str(item.get("text") or ""))
    shape = table_shape(table_text)
    prev_kind = previous_context_kind(previous)
    next_kind = next_context_kind(next_block)

    if prev_kind == "adjacent_question" or next_kind == "adjacent_question":
        return (
            "auto_attach_adjacent_question_candidate",
            "low",
            "table is immediately adjacent to a question block",
        )
    if prev_kind == "instruction" and next_kind not in {"explanation_label", "section_label"}:
        return (
            "auto_attach_instruction_table_candidate",
            "medium",
            "table follows a direct exercise instruction and does not immediately enter a new labelled explanation/section",
        )
    if shape == "vocabulary_or_definition_table" or (prev_kind == "adjacent_table" and shape in {"text_table", "vocabulary_or_definition_table"}):
        return (
            "paired_vocabulary_table_needs_layout_rule",
            "medium",
            "table appears to be part of a vocabulary/matching pair and needs paired-table rendering semantics",
        )
    if prev_kind in {"step_explanation", "explanation_label"} or next_kind in {"step_explanation", "explanation_label"}:
        return (
            "explanation_or_step_table_keep_review",
            "high",
            "table is inside step/example explanation context and should not be blindly attached as an exercise answer table",
        )
    if prev_kind == "question_like_paragraph" and shape in {"blank_answer_table", "data_table", "math_table"}:
        return (
            "question_like_paragraph_table_needs_visual_review",
            "medium",
            "preceding paragraph is question-like but not typed as a question; visual/source review is needed before auto-attach",
        )
    if prev_kind in {"section_label", "colon_prompt"} and shape in {"blank_answer_table", "data_table", "math_table"}:
        return (
            "section_or_colon_prompt_table_candidate",
            "medium",
            "table follows a section label or colon prompt; candidate only because group boundary is broad",
        )
    return (
        "manual_review_or_compiler_boundary_gap",
        "high",
        "no generic low-risk table attachment signal found",
    )


def build_audit(standard_dir: Path) -> dict[str, Any]:
    relation_audit = read_json(standard_dir / "workbook_relation_audit.json")
    grouping = read_json(standard_dir / "workbook_grouping_state_machine_simulation.json")
    items = relation_table_gap_items(relation_audit)

    records: list[dict[str, Any]] = []
    policy_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    shape_counts: Counter[str] = Counter()
    context_counts: Counter[str] = Counter()
    for item in items:
        previous = item.get("previous_block") if isinstance(item.get("previous_block"), dict) else {}
        next_block = item.get("next_block") if isinstance(item.get("next_block"), dict) else {}
        table_text = compact_text(str(item.get("text") or ""))
        policy, risk, reason = classify_policy(item)
        shape = table_shape(table_text)
        prev_kind = previous_context_kind(previous)
        next_kind = next_context_kind(next_block)
        policy_counts[policy] += 1
        risk_counts[risk] += 1
        shape_counts[shape] += 1
        context_counts[f"{prev_kind}->{next_kind}"] += 1
        records.append(
            {
                "policy_bucket": policy,
                "risk_level": risk,
                "reason": reason,
                "block_id": item.get("block_id"),
                "line_start": item.get("line_start"),
                "heading_path": item.get("heading_path") or [],
                "table_shape": shape,
                "previous_context_kind": prev_kind,
                "next_context_kind": next_kind,
                "previous_block": block_summary(previous),
                "next_block": block_summary(next_block),
                "text": str(item.get("text") or "")[:700],
            }
        )

    auto_candidate_count = sum(
        policy_counts[key]
        for key in ("auto_attach_adjacent_question_candidate", "auto_attach_instruction_table_candidate")
    )
    needs_special_rule_count = policy_counts["paired_vocabulary_table_needs_layout_rule"]
    needs_review_count = len(items) - auto_candidate_count

    return {
        "schema": "luceon-standard-workbook-table-attachment-policy-simulation/v1",
        "standard_dir": str(standard_dir),
        "policy": "dry_run_no_profile_mutation_no_gate_closure",
        "decision_boundary": (
            "This simulation classifies orphan table-question gaps into generic attachment policy families. "
            "It does not attach tables, close relation gates, or change Standard acceptance status."
        ),
        "source_relation_audit": "workbook_relation_audit.json",
        "source_grouping_simulation": "workbook_grouping_state_machine_simulation.json",
        "table_gap_count": len(items),
        "policy_bucket_counts": dict(policy_counts),
        "risk_level_counts": dict(risk_counts),
        "table_shape_counts": dict(shape_counts),
        "context_transition_counts": dict(context_counts.most_common()),
        "auto_attach_candidate_count": auto_candidate_count,
        "needs_special_layout_rule_count": needs_special_rule_count,
        "needs_visual_or_manual_review_count": needs_review_count,
        "guarded_grouping_remaining_table_gap_count": (grouping.get("guarded_state_machine") or {}).get(
            "remaining_table_gap_count"
        ),
        "candidate_rule_verdict": "table_policy_requires_visual_review_before_compiler_rule",
        "records_sample": records[:120],
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records_sample"}, ensure_ascii=False, indent=2)
    rows = []
    for item in report.get("records_sample") or []:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('policy_bucket') or ''))}</td>"
            f"<td>{html.escape(str(item.get('risk_level') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(item.get('line_start') or ''))}</td>"
            f"<td>{html.escape(' > '.join(item.get('heading_path') or []))}</td>"
            f"<td>{html.escape(str(item.get('table_shape') or ''))}</td>"
            f"<td>{html.escape(str((item.get('previous_block') or {}).get('text') or ''))}</td>"
            f"<td>{html.escape(str(item.get('text') or ''))}</td>"
            f"<td>{html.escape(str((item.get('next_block') or {}).get('text') or ''))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Table Attachment Policy Simulation</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Workbook Table Attachment Policy Simulation</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Policy</th><th>Risk</th><th>Block</th><th>Line</th><th>Heading</th><th>Shape</th><th>Previous</th><th>Table</th><th>Next</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_audit(args.standard_dir)
    write_json(args.standard_dir / "workbook_table_attachment_policy_simulation.json", report)
    (args.standard_dir / "workbook_table_attachment_policy_simulation.html").write_text(
        build_html(report),
        encoding="utf-8",
    )
    print(json.dumps({k: v for k, v in report.items() if k != "records_sample"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
