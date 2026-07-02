#!/usr/bin/env python3
"""Create a renderer contract audit for paired vocabulary workbook tables."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


EMPTY_TD_RE = re.compile(r"<td>\s*</td>", re.I)
UNDERSCORE_RE = re.compile(r"_{2,}")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def current_html_fragment(standard_dir: Path, block_id: str, *, radius: int = 900) -> str:
    html_path = standard_dir / "standard.html"
    if not html_path.exists():
        return ""
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    index = text.find(f'id="{block_id}"')
    if index < 0:
        index = text.find(block_id)
    if index < 0:
        return ""
    return text[max(0, index - radius) : index + radius]


def classify_current_render_gap(record: dict[str, Any], fragment: str) -> list[str]:
    gaps: list[str] = []
    layout = str(record.get("layout_bucket") or "")
    if layout == "two_table_vocabulary_definition_pair" and "paired-vocabulary" not in fragment:
        gaps.append("two_table_pair_not_rendered_as_horizontal_pair_group")
    if layout == "word_bank_paragraphs_plus_definition_table" and "paired-vocabulary" not in fragment:
        gaps.append("word_bank_and_definition_table_not_rendered_as_single_group")
    table_text = str(record.get("standard_table_text") or "")
    if EMPTY_TD_RE.search(table_text):
        gaps.append("empty_example_cells_need_printable_answer_space")
    if UNDERSCORE_RE.search(table_text):
        gaps.append("inline_underscore_blanks_need_preserved_blank_width")
    return gaps


def build_contract(standard_dir: Path) -> dict[str, Any]:
    confirmation = read_json(standard_dir / "paired_vocabulary_source_confirmation.json")
    records = confirmation.get("records") if isinstance(confirmation.get("records"), list) else []
    layout_counts: Counter[str] = Counter()
    render_gap_counts: Counter[str] = Counter()
    items: list[dict[str, Any]] = []
    for record in records:
        block_id = str(record.get("block_id") or "")
        fragment = current_html_fragment(standard_dir, block_id)
        gaps = classify_current_render_gap(record, fragment)
        layout = str(record.get("layout_bucket") or "")
        layout_counts[layout] += 1
        render_gap_counts.update(gaps)
        items.append(
            {
                "block_id": block_id,
                "layout_bucket": layout,
                "source_layout_confirmed": bool(record.get("source_context_crop")),
                "source_context_crop": record.get("source_context_crop") or "",
                "current_render_gap_flags": gaps,
                "contract_action": (
                    "render_horizontal_vocabulary_definition_pair"
                    if layout == "two_table_vocabulary_definition_pair"
                    else "render_word_bank_plus_definition_example_table"
                ),
                "requires_blank_preservation": any(
                    gap in gaps
                    for gap in {
                        "empty_example_cells_need_printable_answer_space",
                        "inline_underscore_blanks_need_preserved_blank_width",
                    }
                ),
            }
        )

    reconstruction_block_ids = (
        (confirmation.get("manual_visual_inspection") or {}).get("known_content_reconstruction_blocker_block_ids") or []
    )
    contract = {
        "schema": "luceon-standard-paired-vocabulary-renderer-contract-audit/v1",
        "standard_dir": str(standard_dir),
        "policy": "contract_audit_only_no_compiler_mutation_no_gate_closure",
        "decision_boundary": (
            "This audit defines a candidate renderer/profile contract for paired vocabulary workbook tables. "
            "It does not implement the renderer, attach tables, close relation gaps, or change acceptance status."
        ),
        "source_confirmation": "paired_vocabulary_source_confirmation.json",
        "record_count": len(records),
        "source_layout_confirmed_count": int(
            (confirmation.get("manual_visual_inspection") or {}).get("source_layout_confirmed_count") or 0
        ),
        "layout_bucket_counts": dict(layout_counts),
        "current_render_gap_counts": dict(render_gap_counts),
        "known_reconstruction_blocker_count": len(reconstruction_block_ids),
        "known_reconstruction_blocker_block_ids": reconstruction_block_ids,
        "contract_requirements": [
            {
                "id": "paired_vocab_group_boundary",
                "requirement": "Wrap the vocabulary instruction, word bank or paired table, definition/example table, and immediate follow-up label as one reviewable exercise group when source layout confirms the relation.",
                "acceptance": "No involved table remains an orphan_table_question; group must be traceable to source context crop.",
                "hard_stop": "Do not group if source context crop is missing or if intervening content is not a short vocabulary word bank/table pair.",
            },
            {
                "id": "two_table_horizontal_pair",
                "requirement": "Render Vocabulary Word and Definition tables as a side-by-side matching pair when their source bboxes share a page and vertical band.",
                "acceptance": "The rendered pair preserves left/right matching semantics and remains printable without splitting the two tables across pages.",
                "hard_stop": "If the pair is cross-page, vertically stacked in source, or bbox evidence is ambiguous, keep review.",
            },
            {
                "id": "word_bank_definition_table",
                "requirement": "Render short vocabulary word-bank paragraphs together with the following Definition/Example table as one compact vocabulary review unit.",
                "acceptance": "The word bank stays visibly above or adjacent to the definition table, and the table remains keep-together where feasible.",
                "hard_stop": "Do not absorb long paragraphs, examples, or unrelated review text as word-bank items.",
            },
            {
                "id": "blank_box_preservation",
                "requirement": "Preserve printable answer blanks and empty example cells as visible answer spaces, not empty table cells or lost source blanks.",
                "acceptance": "Source blank boxes or underline blanks remain visible in Standard HTML/PDF and are represented in structured evidence.",
                "hard_stop": "If source blank geometry is visible but missing from Standard table content, keep needs_reconstruction rather than accepted_by_rule.",
            },
        ],
        "gate_implications": {
            "can_reduce_relation_gap_count_after_implementation": len(records),
            "cannot_close_existing_reconstruction_blockers_without_blank_preservation": len(reconstruction_block_ids),
            "must_remain_review_until_visual_regression_passes": True,
        },
        "candidate_rule_verdict": "contract_ready_for_compiler_prototype_but_not_gate_closure",
        "items": items,
    }
    return contract


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "items"}, ensure_ascii=False, indent=2)
    requirement_rows = []
    for req in report.get("contract_requirements") or []:
        requirement_rows.append(
            "<tr>"
            f"<td>{html.escape(str(req.get('id') or ''))}</td>"
            f"<td>{html.escape(str(req.get('requirement') or ''))}</td>"
            f"<td>{html.escape(str(req.get('acceptance') or ''))}</td>"
            f"<td>{html.escape(str(req.get('hard_stop') or ''))}</td>"
            "</tr>"
        )
    item_rows = []
    for item in report.get("items") or []:
        item_rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(item.get('layout_bucket') or ''))}</td>"
            f"<td>{html.escape(str(item.get('contract_action') or ''))}</td>"
            f"<td>{html.escape(', '.join(item.get('current_render_gap_flags') or []))}</td>"
            f"<td>{html.escape(str(item.get('requires_blank_preservation') or False))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paired Vocabulary Renderer Contract Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Paired Vocabulary Renderer Contract Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <h2>Contract Requirements</h2>
  <table><thead><tr><th>ID</th><th>Requirement</th><th>Acceptance</th><th>Hard Stop</th></tr></thead><tbody>{"".join(requirement_rows)}</tbody></table>
  <h2>Candidate Items</h2>
  <table><thead><tr><th>Block</th><th>Layout</th><th>Action</th><th>Current Gaps</th><th>Blank Preservation</th></tr></thead><tbody>{"".join(item_rows)}</tbody></table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_contract(args.standard_dir)
    write_json(args.standard_dir / "paired_vocabulary_renderer_contract_audit.json", report)
    (args.standard_dir / "paired_vocabulary_renderer_contract_audit.html").write_text(
        build_html(report),
        encoding="utf-8",
    )
    print(json.dumps({k: v for k, v in report.items() if k != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
