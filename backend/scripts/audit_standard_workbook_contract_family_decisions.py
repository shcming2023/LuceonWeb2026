#!/usr/bin/env python3
"""Classify remaining workbook relation contract packets by family risk."""

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


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def body_blocks(document: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = document.get("blocks")
    if isinstance(blocks, list):
        return blocks
    body = document.get("body")
    return body if isinstance(body, list) else []


def block_context(blocks: list[dict[str, Any]], block_id: str) -> dict[str, Any]:
    by_id = {str(block.get("id") or ""): index for index, block in enumerate(blocks)}
    index = by_id.get(block_id)
    if index is None:
        return {}
    block = blocks[index]
    previous_block = blocks[index - 1] if index > 0 else {}
    next_block = blocks[index + 1] if index + 1 < len(blocks) else {}
    return {
        "previous_block_id": previous_block.get("id") or "",
        "previous_block_type": previous_block.get("type") or "",
        "previous_text": normalize_text(str(previous_block.get("markdown") or previous_block.get("text") or "")),
        "table_text": normalize_text(str(block.get("markdown") or block.get("text") or "")),
        "next_block_id": next_block.get("id") or "",
        "next_block_type": next_block.get("type") or "",
        "next_text": normalize_text(str(next_block.get("markdown") or next_block.get("text") or "")),
        "heading_path": block.get("heading_path") or [],
    }


def classify_contract(record: dict[str, Any], context: dict[str, Any]) -> tuple[str, str, str, str]:
    family = str(record.get("family") or "")
    previous_type = str(context.get("previous_block_type") or "")
    next_type = str(context.get("next_block_type") or "")
    previous = str(context.get("previous_text") or "")
    table = str(context.get("table_text") or "")
    next_text = str(context.get("next_text") or "")
    combined = f"{previous} {table} {next_text}".lower()

    if next_type == "table":
        return (
            "keep_review_multi_table_or_model_unit",
            "math_heavy_multi_table_model",
            "Adjacency to another table means a single-table attachment rule would split one visual/model unit.",
            "math_heavy_profile_boundary",
        )
    if previous_type == "captioned_figure":
        return (
            "keep_review_figure_table_compound_unit",
            "figure_table_compound_probability_or_data_unit",
            "The table follows a source figure and should be reviewed as a compound figure/table unit, not a generic table attachment.",
            "math_heavy_profile_boundary",
        )
    if "convince me" in previous.lower() and "<td></td>" in table:
        return (
            "keep_review_answer_space_rendering_policy_needed",
            "blank_answer_table_after_prompt",
            "The table appears to be a printable response/answer-space table and needs rendering policy before relation closure.",
            "rendering_policy_needed",
        )
    if family == "classification_answer_table":
        return (
            "contract_candidate_needs_math_visual_group_policy",
            "classification_table_or_number-system_diagram",
            "Classification tables are source-adjacent to explanation/question prompts but overlap with math visual diagram semantics.",
            "math_heavy_profile_boundary",
        )
    if family == "step_or_method_model_table":
        return (
            "contract_candidate_needs_math_step_model_policy",
            "worked_example_step_or_model_table",
            "The table is part of a worked example step/model sequence; relation and layout should be governed by math example policy.",
            "math_heavy_profile_boundary",
        )
    if family == "frequency_table_explanation":
        return (
            "contract_candidate_needs_math_frequency_policy",
            "frequency_table_explanation_or_response_table",
            "Frequency tables are tightly coupled to math explanations or response prompts and need a math-data-table contract.",
            "math_heavy_profile_boundary",
        )
    if family == "transformation_rule_table":
        return (
            "contract_candidate_needs_math_rule_table_policy",
            "transformation_rule_summary_table",
            "The table summarizes coordinate transformation rules and is more like a math reference/model table than a workbook option table.",
            "math_heavy_profile_boundary",
        )
    if family == "probability_data_table":
        if "develop a probability model" in next_text.lower() or "estimate the number" in next_text.lower():
            return (
                "contract_candidate_needs_probability_data_policy",
                "probability_model_data_table",
                "The table supplies data for a probability model task and should stay with its task/model context.",
                "math_heavy_profile_boundary",
            )
        return (
            "contract_candidate_needs_probability_example_policy",
            "probability_example_data_table",
            "The table supplies data inside a probability example and needs a math-example relation/rendering contract.",
            "math_heavy_profile_boundary",
        )
    if family == "data_table_for_graph_or_association":
        return (
            "contract_candidate_needs_data_graph_policy",
            "data_table_for_graph_or_association",
            "The table is the data source for a graph/association task, which should be handled as math data evidence.",
            "math_heavy_profile_boundary",
        )
    if "step" in combined or "example" in combined:
        return (
            "contract_candidate_needs_math_example_policy",
            "math_example_table",
            "The surrounding context is a worked math example; keep as a profile-boundary candidate.",
            "math_heavy_profile_boundary",
        )
    return (
        "keep_review_no_safe_family_rule",
        "unclassified_contract_packet",
        "No low-risk reusable family rule is evident from source context and document context.",
        "review_only",
    )


def build_audit(standard_dir: Path, source_context_audit: Path) -> dict[str, Any]:
    source_report = read_json(source_context_audit)
    blocks = body_blocks(read_json(standard_dir / "standard_document.json"))
    audited: list[dict[str, Any]] = []
    for record in source_report.get("records") or []:
        if record.get("source_context_decision") != "source_context_packet_ready_for_contract_review":
            continue
        block_id = str(record.get("block_id") or "")
        context = block_context(blocks, block_id)
        decision, refined_family, reason, profile_boundary = classify_contract(record, context)
        audited.append(
            {
                "block_id": block_id,
                "source_family": record.get("family") or "",
                "source_decision": record.get("decision") or "",
                "contract_family_decision": decision,
                "refined_family": refined_family,
                "profile_boundary": profile_boundary,
                "reason": reason,
                "compiler_rerun_recommendation": "do_not_rerun_as_generic_exercise_workbook_rule",
                "needs_math_heavy_profile_review": profile_boundary == "math_heavy_profile_boundary",
                "source_page_number": record.get("source_page_number"),
                "source_bbox": record.get("source_bbox") or [],
                "expanded_context_crop": record.get("expanded_context_crop") or "",
                "full_page_context_crop": record.get("full_page_context_crop") or "",
                **context,
            }
        )

    decision_counts = Counter(item["contract_family_decision"] for item in audited)
    refined_counts = Counter(item["refined_family"] for item in audited)
    boundary_counts = Counter(item["profile_boundary"] for item in audited)
    math_heavy_count = boundary_counts["math_heavy_profile_boundary"]
    return {
        "schema": "luceon-standard-workbook-contract-family-decision-audit/v1",
        "standard_dir": str(standard_dir),
        "source_context_audit": str(source_context_audit),
        "policy": "family_decision_no_compiler_mutation_no_gate_closure",
        "decision_boundary": (
            "This audit classifies the 18 source-context contract-review packets by reusable family risk. "
            "It does not close relation gaps, modify Standard output, or authorize a broad exercise_workbook table rule."
        ),
        "record_count": len(audited),
        "contract_family_decision_counts": dict(decision_counts),
        "refined_family_counts": dict(refined_counts),
        "profile_boundary_counts": dict(boundary_counts),
        "math_heavy_profile_boundary_count": math_heavy_count,
        "generic_exercise_workbook_rerun_recommended": False,
        "gate_implications": {
            "can_promote_exercise_workbook_profile": False,
            "can_close_remaining_relation_gaps": False,
            "can_add_generic_exercise_workbook_table_rule": False,
            "recommended_next_action": "treat_these_packets_as_math_heavy_relation_family_review_before_any_compiler_rule",
        },
        "records": audited,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2)
    rows = []
    for item in report.get("records") or []:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('contract_family_decision') or ''))}</td>"
            f"<td>{html.escape(str(item.get('refined_family') or ''))}</td>"
            f"<td>{html.escape(str(item.get('profile_boundary') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(item.get('source_family') or ''))}</td>"
            f"<td>{html.escape(str(item.get('reason') or ''))}</td>"
            f"<td>{html.escape(str(item.get('previous_block_type') or ''))}: {html.escape(str(item.get('previous_text') or '')[:220])}</td>"
            f"<td>{html.escape(str(item.get('next_block_type') or ''))}: {html.escape(str(item.get('next_text') or '')[:220])}</td>"
            f"<td><img src=\"{html.escape(str(item.get('expanded_context_crop') or ''))}\"></td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Contract Family Decision Audit</title>
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
  <h1>Workbook Contract Family Decision Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Decision</th><th>Refined Family</th><th>Boundary</th><th>Block</th><th>Source Family</th><th>Reason</th><th>Previous</th><th>Next</th><th>Source Context</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--source-context-audit", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_audit(args.standard_dir, args.source_context_audit)
    write_json(args.out_dir / "workbook_contract_family_decision_audit.json", report)
    (args.out_dir / "workbook_contract_family_decision_audit.html").write_text(
        build_html(report),
        encoding="utf-8",
    )
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
