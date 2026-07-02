#!/usr/bin/env python3
"""Prototype source-confirmed paired vocabulary workbook rendering."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


TD_RE = re.compile(r"<td>(.*?)</td>", re.I | re.S)
EMPTY_TD_RE = re.compile(r"<td>\s*</td>", re.I)
TABLE_RE = re.compile(r"<table\b.*?</table>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def block_text(block: dict[str, Any] | None) -> str:
    block = block or {}
    return re.sub(r"\s+", " ", str(block.get("markdown") or block.get("text") or "")).strip()


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", value or "")).strip()


def render_table_cell_text(text: str) -> str:
    placeholder = "@@ANSWER_LINE@@"
    protected = re.sub(r"(?:\\_)+|_{2,}", placeholder, text)
    escaped = html.escape(protected)
    return escaped.replace(placeholder, '<span class="answer-line"></span>')


def render_table_with_answer_spaces(table_html: str) -> tuple[str, int, int]:
    empty_cell_count = 0
    inline_blank_count = 0

    def render_cell(match: re.Match[str]) -> str:
        nonlocal empty_cell_count, inline_blank_count
        raw = match.group(1)
        text = strip_tags(raw)
        if not text:
            empty_cell_count += 1
            return '<td class="answer-cell"><div class="answer-space"></div></td>'
        before = len(re.findall(r"(?:\\_)+|_{2,}", text))
        inline_blank_count += before
        return f"<td>{render_table_cell_text(text)}</td>"

    rendered = TD_RE.sub(render_cell, table_html)
    return rendered, empty_cell_count, inline_blank_count


def render_word_bank(blocks: list[dict[str, Any]]) -> str:
    items = []
    for block in blocks:
        text = str(block.get("text") or "").strip()
        if text:
            items.append(f"<span>{html.escape(text)}</span>")
    return f'<div class="paired-vocab-word-bank">{"".join(items)}</div>' if items else ""


def render_two_table_pair(record: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    previous = record.get("previous_table_standard_text") or ""
    current = record.get("standard_table_text") or ""
    previous_table = TABLE_RE.search(previous)
    current_table = TABLE_RE.search(current)
    previous_html, previous_empty, previous_inline = render_table_with_answer_spaces(previous_table.group(0) if previous_table else previous)
    current_html, current_empty, current_inline = render_table_with_answer_spaces(current_table.group(0) if current_table else current)
    metrics = {
        "answer_space_count": previous_empty + current_empty,
        "inline_blank_count": previous_inline + current_inline,
        "rendered_pair_count": 1,
    }
    return (
        '<section class="paired-vocab-prototype paired-vocab-two-table">'
        '<div class="paired-vocab-grid">'
        f'<div class="paired-vocab-panel">{previous_html}</div>'
        f'<div class="paired-vocab-panel">{current_html}</div>'
        "</div>"
        "</section>",
        metrics,
    )


def render_word_bank_definition(record: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    table_text = record.get("standard_table_text") or ""
    table_match = TABLE_RE.search(table_text)
    table_html, empty_count, inline_blank_count = render_table_with_answer_spaces(table_match.group(0) if table_match else table_text)
    word_bank = render_word_bank(record.get("word_bank_blocks") or [])
    metrics = {
        "answer_space_count": empty_count,
        "inline_blank_count": inline_blank_count,
        "rendered_word_bank_group_count": 1,
    }
    return (
        '<section class="paired-vocab-prototype paired-vocab-word-bank-table">'
        f"{word_bank}"
        f'<div class="paired-vocab-table">{table_html}</div>'
        "</section>",
        metrics,
    )


def build_previous_table_text(document: dict[str, Any], previous_block_id: str) -> str:
    for block in document.get("blocks") or []:
        if str(block.get("id") or "") == previous_block_id:
            return block_text(block)
    return ""


def build_prototype(standard_dir: Path) -> dict[str, Any]:
    contract = read_json(standard_dir / "paired_vocabulary_renderer_contract_audit.json")
    confirmation = read_json(standard_dir / "paired_vocabulary_source_confirmation.json")
    document = read_json(standard_dir / "standard_document.json")
    confirmation_by_block = {str(item.get("block_id") or ""): item for item in confirmation.get("records") or []}
    reconstruction_ids = set(contract.get("known_reconstruction_blocker_block_ids") or [])

    records: list[dict[str, Any]] = []
    total_answer_spaces = 0
    total_inline_blanks = 0
    rendered_two_table = 0
    rendered_word_bank = 0
    reconstruction_retained = 0
    for item in contract.get("items") or []:
        block_id = str(item.get("block_id") or "")
        source = confirmation_by_block.get(block_id, {})
        layout = str(item.get("layout_bucket") or "")
        record = {**source, **item}
        previous_block_id = str(source.get("previous_table_block_id") or "")
        record["previous_table_standard_text"] = build_previous_table_text(document, previous_block_id)
        if layout == "two_table_vocabulary_definition_pair":
            prototype_html, metrics = render_two_table_pair(record)
            rendered_two_table += 1
        else:
            prototype_html, metrics = render_word_bank_definition(record)
            rendered_word_bank += 1
        answer_spaces = int(metrics.get("answer_space_count") or 0)
        inline_blanks = int(metrics.get("inline_blank_count") or 0)
        total_answer_spaces += answer_spaces
        total_inline_blanks += inline_blanks
        is_reconstruction = block_id in reconstruction_ids
        if is_reconstruction:
            reconstruction_retained += 1
        records.append(
            {
                "block_id": block_id,
                "layout_bucket": layout,
                "source_context_crop": source.get("source_context_crop") or "",
                "prototype_html": prototype_html,
                "answer_space_count": answer_spaces,
                "inline_blank_count": inline_blanks,
                "reconstruction_blocker_retained": is_reconstruction,
                "prototype_verdict": (
                    "prototype_rendered_but_reconstruction_blocker_retained"
                    if is_reconstruction
                    else "prototype_rendered_for_visual_regression"
                ),
            }
        )

    return {
        "schema": "luceon-standard-paired-vocabulary-renderer-prototype/v1",
        "standard_dir": str(standard_dir),
        "policy": "prototype_only_no_standard_mutation_no_gate_closure",
        "decision_boundary": (
            "This prototype renders only source-confirmed paired vocabulary candidates into a review artifact. "
            "It does not mutate standard.html, close workbook relation gaps, or change acceptance status."
        ),
        "source_contract": "paired_vocabulary_renderer_contract_audit.json",
        "record_count": len(records),
        "rendered_two_table_pair_count": rendered_two_table,
        "rendered_word_bank_table_count": rendered_word_bank,
        "prototype_answer_space_count": total_answer_spaces,
        "prototype_inline_blank_count": total_inline_blanks,
        "reconstruction_blocker_retained_count": reconstruction_retained,
        "candidate_rule_verdict": "prototype_render_ready_for_visual_regression_not_gate_closure",
        "records": records,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2)
    sections = []
    for record in report.get("records") or []:
        crop = str(record.get("source_context_crop") or "")
        crop_html = f'<img src="{html.escape(crop)}" alt="source context">' if crop else "<p>No source crop.</p>"
        badge = "reconstruction retained" if record.get("reconstruction_blocker_retained") else "visual regression candidate"
        sections.append(
            "<article>"
            f"<h2>{html.escape(str(record.get('block_id') or ''))} - {html.escape(str(record.get('layout_bucket') or ''))}</h2>"
            f"<p><strong>Verdict:</strong> {html.escape(str(record.get('prototype_verdict') or ''))} | "
            f"<strong>{html.escape(badge)}</strong></p>"
            '<div class="compare">'
            f'<section><h3>Source Context</h3>{crop_html}</section>'
            f'<section><h3>Prototype Render</h3>{record.get("prototype_html") or ""}</section>'
            "</div>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paired Vocabulary Renderer Prototype</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; font-size: 14px; }}
    pre {{ white-space: pre-wrap; border: 1px solid #bbb; padding: 12px; background: #f7f7f7; }}
    article {{ border-top: 1px solid #bbb; padding: 18px 0; break-inside: avoid; }}
    .compare {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 18px; align-items: start; }}
    img {{ max-width: 100%; border: 1px solid #ccc; background: #fff; }}
    .paired-vocab-prototype {{ border: 1px solid #bbb; padding: 12px; break-inside: avoid; }}
    .paired-vocab-grid {{ display: grid; grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr); gap: 14px; align-items: start; }}
    .paired-vocab-word-bank {{ border: 1px solid #9a7b93; padding: 8px; margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 8px 18px; }}
    .paired-vocab-word-bank span {{ white-space: nowrap; }}
    table {{ width: 100%; border-collapse: collapse; margin: 0; }}
    td, th {{ border: 1px solid #888; padding: 6px 8px; vertical-align: top; }}
    .answer-cell {{ min-height: 32px; }}
    .answer-space {{ display: block; min-height: 28px; border-bottom: 1.5px solid #333; margin: 6px 2px; }}
    .answer-line {{ display: inline-block; width: 38px; border-bottom: 1.5px solid #333; margin: 0 3px; vertical-align: -0.1em; }}
  </style>
</head>
<body>
  <h1>Paired Vocabulary Renderer Prototype</h1>
  <pre>{html.escape(summary)}</pre>
  {''.join(sections)}
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_prototype(args.standard_dir)
    write_json(args.standard_dir / "paired_vocabulary_renderer_prototype_report.json", report)
    (args.standard_dir / "paired_vocabulary_renderer_prototype.html").write_text(build_html(report), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
