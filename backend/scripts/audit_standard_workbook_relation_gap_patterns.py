#!/usr/bin/env python3
"""Audit workbook relation real gaps by contiguous exercise patterns."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


SECTION_LABELS = {
    "assessment practice",
    "do you know how?",
    "do you understand?",
    "practice",
    "practice & problem solving",
    "leveled practice",
    "reflect",
    "act 1",
    "act 2",
    "act 3",
    "sequel",
}
INSTRUCTION_START_RE = re.compile(
    r"^(?:Choose|Complete|Write|Look|Read|Find|Correct|Fill|Circle|Answer|Ask|Tell|Work|"
    r"Determine|Classify|Evaluate|Simplify|Solve|Graph|Use|Draw|Estimate|Compare|Order|"
    r"Match|Name|Identify|Explain|Describe|Select|Calculate|Convert|Round|Model|Represent|"
    r"Make|Copy|Connect|Decide|Show)\b",
    re.I,
)
NUMBER_DOT_RE = re.compile(r"^\d{1,3}\.\s+")
NUMBER_SPACE_RE = re.compile(r"^\d{1,3}\s+\S+")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def block_text(block: dict[str, Any] | None) -> str:
    if not block:
        return ""
    return compact_text(str(block.get("markdown") or block.get("text") or ""))


def block_id_number(block_id: str) -> int:
    match = re.search(r"(\d+)$", block_id or "")
    return int(match.group(1)) if match else -1


def classify_question_shape(text: str) -> str:
    if NUMBER_DOT_RE.match(text):
        return "number_dot_question"
    if NUMBER_SPACE_RE.match(text):
        return "number_space_fragment_or_question"
    if re.search(r"\$.*\$|\\frac|\\begin", text):
        return "math_text"
    if "?" in text:
        return "question_mark_text"
    if len(text) > 240:
        return "long_text"
    return "other_question_like_text"


def classify_run_starter(previous: dict[str, Any] | None, first_text: str) -> tuple[str, str]:
    prev_text = block_text(previous)
    prev_norm = prev_text.strip("* ").lower()
    prev_type = str((previous or {}).get("type") or "")
    if not prev_text and NUMBER_DOT_RE.match(first_text):
        return "missing_front_context", "numbered run starts without a preceding block"
    if prev_text == "TOPICS":
        return "front_matter_topic_list_artifact", "topic list misread as an exercise question"
    if prev_norm in SECTION_LABELS:
        return "section_label_should_start_group", "known workbook section label should start an exercise group"
    if INSTRUCTION_START_RE.match(prev_text):
        return "instruction_paragraph_should_start_group", "instruction paragraph should start an exercise group"
    if prev_type == "question":
        return "continues_existing_ungrouped_question_run", "run starts after another question-like block"
    if re.match(r"^[A-Z]$", prev_text):
        return "part_letter_should_start_group", "part letter should start or continue an exercise group"
    if prev_text.endswith(":"):
        return "colon_label_should_start_group", "colon-ended prompt likely introduces exercise items"
    return "unknown_or_manual_group_boundary", "no generic grouping signal found"


def is_real_gap_question(item: dict[str, Any]) -> bool:
    return item.get("kind") == "ungrouped_question" and item.get("disposition") == "real_profile_gap"


def is_real_gap_table(item: dict[str, Any]) -> bool:
    return item.get("kind") == "orphan_table_question" and item.get("disposition") == "real_profile_gap"


def build_question_runs(blocks: list[dict[str, Any]], audit_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gap_ids = {str(item.get("block_id") or "") for item in audit_items if is_real_gap_question(item)}
    by_id = {str(block.get("id") or ""): block for block in blocks}
    ordered_ids = [str(block.get("id") or "") for block in blocks]
    runs: list[list[str]] = []
    current: list[str] = []
    for block_id in ordered_ids:
        if block_id in gap_ids:
            if current and block_id_number(block_id) == block_id_number(current[-1]) + 1:
                current.append(block_id)
            else:
                if current:
                    runs.append(current)
                current = [block_id]
        else:
            if current:
                runs.append(current)
                current = []
    if current:
        runs.append(current)

    block_index = {str(block.get("id") or ""): index for index, block in enumerate(blocks)}
    records: list[dict[str, Any]] = []
    for run in runs:
        first = by_id[run[0]]
        last = by_id[run[-1]]
        first_index = block_index[run[0]]
        previous = blocks[first_index - 1] if first_index > 0 else None
        next_block = blocks[block_index[run[-1]] + 1] if block_index[run[-1]] + 1 < len(blocks) else None
        starter_bucket, starter_reason = classify_run_starter(previous, block_text(first))
        shape_counts = Counter(classify_question_shape(block_text(by_id[block_id])) for block_id in run)
        records.append(
            {
                "starter_bucket": starter_bucket,
                "starter_reason": starter_reason,
                "run_length": len(run),
                "first_block_id": run[0],
                "last_block_id": run[-1],
                "line_start": first.get("line_start"),
                "heading_path": first.get("heading_path") or [],
                "previous_block": {
                    "id": (previous or {}).get("id"),
                    "type": (previous or {}).get("type"),
                    "subtype": (previous or {}).get("subtype") or "",
                    "text": block_text(previous)[:240],
                },
                "next_block": {
                    "id": (next_block or {}).get("id"),
                    "type": (next_block or {}).get("type"),
                    "subtype": (next_block or {}).get("subtype") or "",
                    "text": block_text(next_block)[:240],
                },
                "shape_counts": dict(shape_counts),
                "first_text": block_text(first)[:500],
                "last_text": block_text(last)[:500],
            }
        )
    return records


def classify_table_gap(item: dict[str, Any]) -> tuple[str, str]:
    previous = item.get("previous_block") if isinstance(item.get("previous_block"), dict) else {}
    next_block = item.get("next_block") if isinstance(item.get("next_block"), dict) else {}
    prev_type = str(previous.get("type") or "")
    next_type = str(next_block.get("type") or "")
    prev_text = compact_text(str(previous.get("text") or ""))
    next_text = compact_text(str(next_block.get("text") or ""))
    table_text = compact_text(str(item.get("text") or ""))
    if prev_type == "question" or next_type == "question":
        return "table_adjacent_to_question_should_attach", "table is adjacent to a question-like block"
    if INSTRUCTION_START_RE.match(prev_text):
        return "table_after_instruction_should_attach", "table follows an exercise instruction"
    if prev_text.strip("* ").lower() in SECTION_LABELS:
        return "table_after_section_label_should_attach", "table follows a workbook section label"
    if "answer" in table_text.lower() or "definition" in table_text.lower() or "example" in table_text.lower():
        return "table_may_be_exercise_or_explanation_needs_visual_review", "table content needs visual/context review before grouping"
    return "table_manual_group_boundary", "no generic table grouping signal found"


def build_audit(standard_dir: Path) -> dict[str, Any]:
    document = read_json(standard_dir / "standard_document.json")
    relation_audit = read_json(standard_dir / "workbook_relation_audit.json")
    blocks = document.get("blocks") if isinstance(document.get("blocks"), list) else []
    items = relation_audit.get("items") if isinstance(relation_audit.get("items"), list) else []
    question_runs = build_question_runs(blocks, items)
    table_items = [item for item in items if is_real_gap_table(item)]
    table_records = []
    for item in table_items:
        bucket, reason = classify_table_gap(item)
        table_records.append(
            {
                "bucket": bucket,
                "reason": reason,
                "block_id": item.get("block_id"),
                "line_start": item.get("line_start"),
                "heading_path": item.get("heading_path") or [],
                "previous_block": item.get("previous_block") or {},
                "next_block": item.get("next_block") or {},
                "text": str(item.get("text") or "")[:500],
            }
        )

    run_bucket_counts = Counter(record["starter_bucket"] for record in question_runs)
    question_count_by_bucket: Counter[str] = Counter()
    for record in question_runs:
        question_count_by_bucket[record["starter_bucket"]] += int(record.get("run_length") or 0)
    table_bucket_counts = Counter(record["bucket"] for record in table_records)
    return {
        "schema": "luceon-standard-workbook-relation-gap-pattern-audit/v1",
        "standard_dir": str(standard_dir),
        "policy": "audit_only_no_profile_mutation_no_closure",
        "decision_boundary": (
            "This report classifies relation gaps into candidate profile-rule families. It does not "
            "create question groups, attach tables, close gates, or change Basic Print status."
        ),
        "source_relation_audit": "workbook_relation_audit.json",
        "real_profile_gap_count": int(relation_audit.get("real_profile_gap_count") or 0),
        "question_gap_count": sum(record["run_length"] for record in question_runs),
        "question_run_count": len(question_runs),
        "question_run_bucket_counts": dict(run_bucket_counts),
        "question_count_by_run_bucket": dict(question_count_by_bucket),
        "table_gap_count": len(table_records),
        "table_gap_bucket_counts": dict(table_bucket_counts),
        "question_runs_sample": question_runs[:80],
        "table_gaps_sample": table_records[:80],
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k not in {"question_runs_sample", "table_gaps_sample"}}, ensure_ascii=False, indent=2)
    question_rows = []
    for item in report.get("question_runs_sample") or []:
        question_rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('starter_bucket') or ''))}</td>"
            f"<td>{html.escape(str(item.get('run_length') or ''))}</td>"
            f"<td>{html.escape(str(item.get('first_block_id') or ''))}</td>"
            f"<td>{html.escape(' > '.join(item.get('heading_path') or []))}</td>"
            f"<td>{html.escape(str((item.get('previous_block') or {}).get('text') or ''))}</td>"
            f"<td>{html.escape(str(item.get('first_text') or ''))}</td>"
            "</tr>"
        )
    table_rows = []
    for item in report.get("table_gaps_sample") or []:
        table_rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('bucket') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(' > '.join(item.get('heading_path') or []))}</td>"
            f"<td>{html.escape(str((item.get('previous_block') or {}).get('text') or ''))}</td>"
            f"<td>{html.escape(str(item.get('text') or ''))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Relation Gap Pattern Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Workbook Relation Gap Pattern Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <h2>Question Run Sample</h2>
  <table><thead><tr><th>Bucket</th><th>Run</th><th>First</th><th>Heading</th><th>Previous</th><th>First Text</th></tr></thead><tbody>{"".join(question_rows)}</tbody></table>
  <h2>Table Gap Sample</h2>
  <table><thead><tr><th>Bucket</th><th>Block</th><th>Heading</th><th>Previous</th><th>Text</th></tr></thead><tbody>{"".join(table_rows)}</tbody></table>
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
    write_json(args.standard_dir / "workbook_relation_gap_pattern_audit.json", report)
    (args.standard_dir / "workbook_relation_gap_pattern_audit.html").write_text(build_html(report), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"question_runs_sample", "table_gaps_sample"}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
