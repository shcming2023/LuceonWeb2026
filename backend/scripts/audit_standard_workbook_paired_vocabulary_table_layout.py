#!/usr/bin/env python3
"""Audit paired vocabulary table layout candidates without mutating Standard."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from audit_standard_workbook_relation_gap_patterns import block_text, compact_text, read_json  # noqa: E402
from standard_from_clean import write_json


TD_RE = re.compile(r"<td>(.*?)</td>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
TR_RE = re.compile(r"<tr>(.*?)</tr>", re.I | re.S)
VOCAB_TERMS_RE = re.compile(r"\b(?:vocabulary|definition|term|word)\b", re.I)
USE_VOCAB_RE = re.compile(r"\bUse Vocabulary in Writing\b", re.I)


def strip_html(value: str) -> str:
    return compact_text(TAG_RE.sub(" ", value or ""))


def table_cells(table_text: str) -> list[str]:
    return [strip_html(match.group(1)) for match in TD_RE.finditer(table_text or "")]


def table_row_count(table_text: str) -> int:
    return len(TR_RE.findall(table_text or ""))


def first_cell(table_text: str) -> str:
    cells = table_cells(table_text)
    return cells[0] if cells else ""


def block_summary(block: dict[str, Any] | None) -> dict[str, Any]:
    block = block or {}
    return {
        "id": block.get("id"),
        "type": block.get("type"),
        "subtype": block.get("subtype") or "",
        "line_start": block.get("line_start"),
        "text": block_text(block)[:360],
    }


def load_policy_records(standard_dir: Path) -> list[dict[str, Any]]:
    policy = read_json(standard_dir / "workbook_table_attachment_policy_simulation.json")
    return [
        record
        for record in policy.get("records_sample") or []
        if record.get("policy_bucket") == "paired_vocabulary_table_needs_layout_rule"
    ]


def previous_word_bank(blocks: list[dict[str, Any]], index: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    cursor = index - 1
    while cursor >= 0:
        block = blocks[cursor]
        if block.get("type") != "paragraph":
            break
        text = block_text(block)
        if not text or len(text) > 160:
            break
        if USE_VOCAB_RE.search(text):
            break
        if VOCAB_TERMS_RE.search(text) and len(records) == 0:
            break
        records.append(block_summary(block))
        cursor -= 1
        if len(records) >= 12:
            break
    records.reverse()
    return records


def classify_layout(
    record: dict[str, Any],
    block: dict[str, Any],
    previous_block: dict[str, Any] | None,
    next_block: dict[str, Any] | None,
    word_bank: list[dict[str, Any]],
) -> tuple[str, str, str]:
    table_text = block_text(block)
    first = first_cell(table_text).lower()
    previous_text = block_text(previous_block)
    next_text = block_text(next_block)
    previous_is_table = (previous_block or {}).get("type") == "table"
    previous_first = first_cell(block_text(previous_block)).lower() if previous_is_table else ""

    if previous_is_table and "vocabulary word" in previous_first and "definition" in first:
        return (
            "two_table_vocabulary_definition_pair",
            "candidate_needs_horizontal_pair_renderer",
            "previous table is a Vocabulary Word list and current table is the matching Definition list",
        )
    if "definition" in first and word_bank and USE_VOCAB_RE.search(next_text):
        return (
            "word_bank_paragraphs_plus_definition_table",
            "candidate_needs_word_bank_grouping_and_table_renderer",
            "short preceding paragraph terms plus a Definition/Example table form a topic-review vocabulary exercise",
        )
    if "definition" in first and VOCAB_TERMS_RE.search(previous_text):
        return (
            "near_vocabulary_context_manual_review",
            "manual_review",
            "definition table has vocabulary context, but the word-bank structure is not mechanically complete",
        )
    return (
        "paired_vocabulary_manual_review",
        "manual_review",
        "record was flagged as paired vocabulary, but no narrower generic layout shape was detected",
    )


def build_audit(standard_dir: Path) -> dict[str, Any]:
    document = read_json(standard_dir / "standard_document.json")
    blocks = document.get("blocks") if isinstance(document.get("blocks"), list) else []
    by_id = {str(block.get("id") or ""): block for block in blocks}
    index_by_id = {str(block.get("id") or ""): index for index, block in enumerate(blocks)}
    records = load_policy_records(standard_dir)

    items: list[dict[str, Any]] = []
    layout_counts: Counter[str] = Counter()
    readiness_counts: Counter[str] = Counter()
    for record in records:
        block_id = str(record.get("block_id") or "")
        block = by_id.get(block_id, {})
        index = index_by_id.get(block_id, -1)
        previous_block = blocks[index - 1] if index > 0 else None
        next_block = blocks[index + 1] if index >= 0 and index + 1 < len(blocks) else None
        word_bank = previous_word_bank(blocks, index) if index >= 0 else []
        layout, readiness, reason = classify_layout(record, block, previous_block, next_block, word_bank)
        layout_counts[layout] += 1
        readiness_counts[readiness] += 1
        table_text = block_text(block)
        items.append(
            {
                "block_id": block_id,
                "line_start": block.get("line_start"),
                "heading_path": block.get("heading_path") or [],
                "layout_bucket": layout,
                "readiness": readiness,
                "reason": reason,
                "table_first_cell": first_cell(table_text),
                "table_row_count": table_row_count(table_text),
                "table_cell_count": len(table_cells(table_text)),
                "previous_block": block_summary(previous_block),
                "next_block": block_summary(next_block),
                "word_bank_count": len(word_bank),
                "word_bank_blocks": word_bank,
                "text": table_text[:900],
            }
        )

    compiler_candidate_count = sum(
        readiness_counts[key]
        for key in (
            "candidate_needs_horizontal_pair_renderer",
            "candidate_needs_word_bank_grouping_and_table_renderer",
        )
    )
    return {
        "schema": "luceon-standard-workbook-paired-vocabulary-table-layout-audit/v1",
        "standard_dir": str(standard_dir),
        "policy": "audit_only_no_profile_mutation_no_gate_closure",
        "decision_boundary": (
            "This report narrows paired/vocabulary table gaps into layout-rule candidates. "
            "It does not attach tables, alter grouping, close gates, or change Basic Print status."
        ),
        "source_table_policy_simulation": "workbook_table_attachment_policy_simulation.json",
        "paired_vocabulary_record_count": len(records),
        "layout_bucket_counts": dict(layout_counts),
        "readiness_counts": dict(readiness_counts),
        "compiler_candidate_count": compiler_candidate_count,
        "manual_review_count": len(records) - compiler_candidate_count,
        "candidate_rule_verdict": "layout_subrules_identified_but_need_visual_confirmation_before_compiler",
        "items": items,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "items"}, ensure_ascii=False, indent=2)
    rows = []
    for item in report.get("items") or []:
        word_bank = "; ".join(str(block.get("text") or "") for block in item.get("word_bank_blocks") or [])
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('layout_bucket') or ''))}</td>"
            f"<td>{html.escape(str(item.get('readiness') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(' > '.join(item.get('heading_path') or []))}</td>"
            f"<td>{html.escape(str(item.get('table_first_cell') or ''))}</td>"
            f"<td>{html.escape(word_bank)}</td>"
            f"<td>{html.escape(str(item.get('text') or ''))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paired Vocabulary Table Layout Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Paired Vocabulary Table Layout Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Layout</th><th>Readiness</th><th>Block</th><th>Heading</th><th>First Cell</th><th>Word Bank</th><th>Table</th></tr></thead>
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
    write_json(args.standard_dir / "workbook_paired_vocabulary_table_layout_audit.json", report)
    (args.standard_dir / "workbook_paired_vocabulary_table_layout_audit.html").write_text(
        build_html(report),
        encoding="utf-8",
    )
    print(json.dumps({k: v for k, v in report.items() if k != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
