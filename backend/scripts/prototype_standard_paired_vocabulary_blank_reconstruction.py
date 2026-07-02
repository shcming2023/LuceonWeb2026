#!/usr/bin/env python3
"""Prototype conservative blank-box reconstruction for paired-vocabulary tables."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

from standard_from_clean import TD_RE, write_json


BLANK_TOKEN = "@@SOURCE_BLANK_BOX@@"
BLANK_HTML = '<span class="source-blank-box"></span>'


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def reconstruct_cell(text: str) -> tuple[str, list[str]]:
    """Insert visual blanks for high-confidence missing source blank patterns."""
    rules: list[tuple[str, str, str]] = [
        ("leading_you_when", r"^(\s*\d+\.\s+You)\s+(when\b)", rf"\1 {BLANK_TOKEN} \2"),
        ("leading_a_is", r"^(\s*\d+\.\s+A)\s+(is\b)", rf"\1 {BLANK_TOKEN} \2"),
        ("leading_the_states", r"^(\s*\d+\.\s+The)\s+(states\b)", rf"\1 {BLANK_TOKEN} \2"),
        ("use_the_to", r"\b(use the)\s+(to\b)", rf"\1 {BLANK_TOKEN} \2"),
        ("terminal_is_an", r"\b(is a\(n\))\s*\.$", rf"\1 {BLANK_TOKEN}."),
    ]
    applied: list[str] = []
    result = text
    for rule_id, pattern, replacement in rules:
        updated, count = re.subn(pattern, replacement, result, flags=re.I)
        if count:
            applied.append(rule_id)
            result = updated
    return result, applied


def render_reconstructed_text(value: str) -> str:
    return html.escape(value).replace(BLANK_TOKEN, BLANK_HTML)


def reconstruct_table(table_html: str) -> tuple[str, int, list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []

    def replace_cell(match: re.Match[str]) -> str:
        raw = match.group(1)
        text = re.sub(r"\s+", " ", raw).strip()
        reconstructed, rules = reconstruct_cell(text)
        if rules:
            records.append({"original": text, "reconstructed": reconstructed, "rules": rules})
        return f"<td>{render_reconstructed_text(reconstructed)}</td>"

    rendered = TD_RE.sub(replace_cell, table_html)
    return rendered, sum(len(item["rules"]) for item in records), records


def build_prototype(standard_dir: Path) -> dict[str, Any]:
    audit = read_json(standard_dir / "paired_vocabulary_blank_box_reconstruction_audit.json")
    out_dir = standard_dir / "paired_vocabulary_blank_reconstruction_prototype"
    out_dir.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    total_blanks = 0
    total_cells = 0
    for record in audit.get("records") or []:
        if not record.get("known_content_reconstruction_blocker"):
            continue
        table_html = str(record.get("standard_table_text") or "")
        rendered_table, blank_count, cell_records = reconstruct_table(table_html)
        total_blanks += blank_count
        total_cells += len(cell_records)
        items.append(
            {
                "block_id": record.get("block_id"),
                "table_ids": record.get("table_ids") or [],
                "layout_bucket": record.get("layout_bucket"),
                "source_context_crop": record.get("source_context_crop") or "",
                "blank_count": blank_count,
                "reconstructed_cell_count": len(cell_records),
                "cell_records": cell_records,
                "prototype_html": rendered_table,
                "prototype_verdict": "pattern_reconstructable" if blank_count else "not_reconstructable_by_current_rules",
            }
        )
    report = {
        "schema": "luceon-standard-paired-vocabulary-blank-reconstruction-prototype/v1",
        "standard_dir": str(standard_dir),
        "source_audit": "paired_vocabulary_blank_box_reconstruction_audit.json",
        "policy": "isolated_prototype_no_compiler_mutation_no_gate_closure",
        "decision_boundary": (
            "This prototype tests conservative text-pattern insertion of visible blanks for already source-confirmed "
            "paired-vocabulary reconstruction blockers. It does not prove source visual equivalence, does not mutate "
            "standard_document.json, and must not close gates without real PDF visual regression."
        ),
        "record_count": len(items),
        "pattern_reconstructable_count": sum(1 for item in items if item["prototype_verdict"] == "pattern_reconstructable"),
        "total_reconstructed_blank_count": total_blanks,
        "total_reconstructed_cell_count": total_cells,
        "candidate_rules": [
            "leading_you_when",
            "leading_a_is",
            "leading_the_states",
            "use_the_to",
            "terminal_is_an",
        ],
        "compiler_readiness": "not_ready_requires_cross_sample_audit_and_real_pdf_visual_regression",
        "items": items,
    }
    write_json(out_dir / "paired_vocabulary_blank_reconstruction_prototype_report.json", report)
    (out_dir / "paired_vocabulary_blank_reconstruction_prototype.html").write_text(build_html(report), encoding="utf-8")
    return report


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False, indent=2)
    sections: list[str] = []
    for item in report.get("items") or []:
        crop = str(item.get("source_context_crop") or "")
        crop_html = f'<img src="../{html.escape(crop)}" alt="source context">' if crop else "<p>No source crop.</p>"
        cell_records = html.escape(json.dumps(item.get("cell_records") or [], ensure_ascii=False, indent=2))
        sections.append(
            "<section>"
            f"<h2>{html.escape(str(item.get('block_id') or ''))}</h2>"
            f"<p><strong>Verdict:</strong> {html.escape(str(item.get('prototype_verdict') or ''))} | "
            f"<strong>Blanks:</strong> {html.escape(str(item.get('blank_count') or 0))}</p>"
            f"<div class=\"grid\"><div>{crop_html}</div><div>{item.get('prototype_html') or ''}</div></div>"
            f"<pre>{cell_records}</pre>"
            "</section>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paired Vocabulary Blank Reconstruction Prototype</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }}
    img {{ max-width: 100%; border: 1px solid #ccc; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    td {{ border: 1px solid #9db0bf; padding: 10px; vertical-align: top; }}
    tr:first-child td {{ background: #7b1969; color: #fff; font-weight: bold; text-align: center; }}
    .source-blank-box {{ display: inline-block; min-width: 96px; height: 28px; border: 2px solid #a9bac8; border-radius: 6px; vertical-align: middle; margin: 0 4px; background: #fff; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
    section {{ margin-bottom: 32px; }}
  </style>
</head>
<body>
  <h1>Paired Vocabulary Blank Reconstruction Prototype</h1>
  <pre>{html.escape(summary)}</pre>
  {"".join(sections)}
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
    print(json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
