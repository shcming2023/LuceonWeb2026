#!/usr/bin/env python3
"""Classify remaining workbook relation gaps after virtual grouping."""

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


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_image_text(text: str) -> bool:
    return text.startswith("![") or "](images/" in text


def text_of(item: dict[str, Any], key: str) -> str:
    return compact(str((item.get(key) or {}).get("text") or ""))


def classify_question(item: dict[str, Any]) -> tuple[str, str, str]:
    previous = text_of(item, "previous_block")
    text = compact(str(item.get("text") or ""))
    heading = " > ".join(item.get("heading_path") or "")
    if not item.get("heading_path") and previous.upper() == "TOPICS":
        return (
            "downgrade_candidate_front_matter_topic_list",
            "front_matter_artifact",
            "Topic list was read as a numbered question and should not block exercise_workbook.",
        )
    if is_image_text(previous) and "3-Act Mathematical Modeling" in heading:
        return (
            "contract_candidate_image_interrupted_3act_question_run",
            "image_interrupted_3act_question",
            "3-Act question run is interrupted by a source image; needs narrow question-only continuation rule.",
        )
    if "3-Act Mathematical Modeling" in heading and re.match(r"^\d+\.\s", text):
        return (
            "contract_candidate_3act_question_continuation",
            "three_act_question_continuation",
            "Question continues a 3-Act modeling run after prior question text.",
        )
    if is_image_text(previous) and re.match(r"^\d+\.\s", text):
        return (
            "contract_candidate_image_interrupted_question_run",
            "image_interrupted_question",
            "Question run is interrupted by a figure or answer-choice image; needs a guarded continuation rule.",
        )
    if re.match(r"^\d+\.\s", text):
        return (
            "contract_candidate_question_run_continuation",
            "question_run_continuation",
            "Numbered question continues a nearby run but lacks a current virtual group starter.",
        )
    return ("keep_review_unclassified_question", "unclassified_question_gap", "No narrow question grouping family matched.")


def classify_table(item: dict[str, Any]) -> tuple[str, str, str]:
    previous = text_of(item, "previous_block")
    text = compact(str(item.get("text") or ""))
    lower = f"{previous} {text}".lower()
    if "morgan's sample" in lower or "maddy's sample" in lower or "jeremy's sample" in lower:
        return (
            "review_multi_table_sample_group",
            "paired_or_multi_sample_tables",
            "Adjacent sample tables must be grouped as a multi-table unit, not single-table attached.",
        )
    if "bank statement" in lower or "saving account number" in lower or "withdrawal" in lower or "deposit" in lower:
        return (
            "review_source_visual_multi_table_document",
            "financial_statement_model_table",
            "Financial statement tables are document-like models that need visual/source grouping.",
        )
    if "step 1" in lower or "one way" in lower or "another way" in lower:
        return (
            "contract_candidate_step_or_method_table",
            "step_or_method_model_table",
            "Table is directly tied to a STEP/ONE WAY method explanation; needs narrow example-table rule.",
        )
    if "classify each number" in lower or "rational" in lower and "irrational" in lower:
        return (
            "contract_candidate_classification_table",
            "classification_answer_table",
            "Rational/irrational classification table follows a direct exercise prompt.",
        )
    if "two-way frequency" in lower or "relative frequency" in lower or "digital" in lower and "print" in lower:
        return (
            "contract_candidate_frequency_table_explanation",
            "frequency_table_explanation",
            "Frequency table is part of a worked explanation or practice prompt.",
        )
    if "scatter" in lower or "arm span" in lower or "height" in lower:
        return (
            "contract_candidate_data_table_for_graph_or_association",
            "data_table_for_graph_or_association",
            "Data table supports a graph/association exercise or example.",
        )
    if "probability" in lower or "marbles" in lower or "winners" in lower or "frequency" in lower:
        return (
            "contract_candidate_probability_data_table",
            "probability_data_table",
            "Probability/frequency data table is tied to nearby exercise/example text.",
        )
    if "angle of rotation" in lower or "counterclockwise rotations" in lower:
        return (
            "contract_candidate_transformation_rule_table",
            "transformation_rule_table",
            "Transformation rule table belongs to an explanation block.",
        )
    if "mean" in lower or "mad" in lower or "hours that 20 students" in lower or "curl-ups" in lower:
        return (
            "review_statistics_table_boundary",
            "statistics_data_or_summary_table",
            "Statistics tables include short-title and multi-table boundaries; keep review until source grouping is explicit.",
        )
    return ("keep_review_unclassified_table", "unclassified_table_gap", "No narrow table family matched.")


def classify_figure(item: dict[str, Any]) -> tuple[str, str, str]:
    previous = text_of(item, "previous_block")
    if "experimental probability" in previous.lower():
        return (
            "review_source_visual_probability_figure",
            "probability_explanation_figure",
            "Figure needs source-visual relation review before attaching to exercise or explanation.",
        )
    return ("keep_review_unclassified_figure", "unclassified_figure_gap", "No narrow figure relation family matched.")


def build_audit(standard_dir: Path) -> dict[str, Any]:
    relation = read_json(standard_dir / "workbook_relation_audit.json")
    records: list[dict[str, Any]] = []
    decision_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    kind_counts: Counter[str] = Counter()
    for item in relation.get("items") or []:
        if item.get("disposition") != "real_profile_gap":
            continue
        kind = str(item.get("kind") or "")
        if kind == "ungrouped_question":
            decision, family, reason = classify_question(item)
        elif kind == "orphan_table_question":
            decision, family, reason = classify_table(item)
        elif kind == "orphan_figure_relation_candidate":
            decision, family, reason = classify_figure(item)
        else:
            decision, family, reason = "keep_review_unknown_kind", "unknown_kind", "Unknown relation gap kind."
        decision_counts[decision] += 1
        family_counts[family] += 1
        kind_counts[kind] += 1
        records.append(
            {
                "block_id": item.get("block_id"),
                "kind": kind,
                "decision": decision,
                "family": family,
                "reason": reason,
                "line_start": item.get("line_start"),
                "heading_path": item.get("heading_path") or [],
                "previous_text": text_of(item, "previous_block")[:400],
                "text": compact(str(item.get("text") or ""))[:700],
                "next_text": text_of(item, "next_block")[:400],
            }
        )
    rule_candidate_count = sum(1 for record in records if str(record["decision"]).startswith("contract_candidate"))
    review_count = len(records) - rule_candidate_count
    return {
        "schema": "luceon-standard-workbook-remaining-relation-gap-audit/v1",
        "standard_dir": str(standard_dir),
        "policy": "audit_only_no_gate_closure_no_profile_promotion",
        "decision_boundary": (
            "This audit classifies remaining real relation gaps after virtual question grouping. "
            "It may identify narrow rule candidates, but it does not close gates or promote exercise_workbook."
        ),
        "remaining_real_profile_gap_count": len(records),
        "kind_counts": dict(kind_counts),
        "decision_counts": dict(decision_counts),
        "family_counts": dict(family_counts),
        "contract_candidate_count": rule_candidate_count,
        "keep_review_count": review_count,
        "gate_implications": {
            "can_promote_exercise_workbook_profile": False,
            "can_close_remaining_relation_gaps": False,
            "required_next_action": "encode_only_low_risk_question_continuation_or_source_audit_table_families_first",
        },
        "records": records,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2)
    rows = []
    for item in report.get("records") or []:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('decision') or ''))}</td>"
            f"<td>{html.escape(str(item.get('family') or ''))}</td>"
            f"<td>{html.escape(str(item.get('kind') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(' > '.join(item.get('heading_path') or []))}</td>"
            f"<td>{html.escape(str(item.get('previous_text') or ''))}</td>"
            f"<td>{html.escape(str(item.get('text') or ''))}</td>"
            f"<td>{html.escape(str(item.get('next_text') or ''))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Remaining Relation Gap Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Workbook Remaining Relation Gap Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Decision</th><th>Family</th><th>Kind</th><th>Block</th><th>Heading</th><th>Previous</th><th>Text</th><th>Next</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_audit(args.standard_dir)
    write_json(args.out_dir / "workbook_remaining_relation_gap_audit.json", report)
    (args.out_dir / "workbook_remaining_relation_gap_audit.html").write_text(build_html(report), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
