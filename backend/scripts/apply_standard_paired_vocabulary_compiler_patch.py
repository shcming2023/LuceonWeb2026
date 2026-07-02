#!/usr/bin/env python3
"""Apply a compiler-adjacent paired vocabulary patch into isolated artifacts."""

from __future__ import annotations

import argparse
import copy
import html
import json
import re
from pathlib import Path
from typing import Any

from prototype_standard_paired_vocabulary_renderer import render_table_with_answer_spaces  # noqa: E402
from standard_from_clean import safe_slug, write_json


TABLE_RE = re.compile(r"<table\b.*?</table>", re.I | re.S)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def block_text(block: dict[str, Any] | None) -> str:
    block = block or {}
    return re.sub(r"\s+", " ", str(block.get("markdown") or block.get("text") or "")).strip()


def block_by_id(blocks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(block.get("id") or ""): block for block in blocks}


def index_by_id(blocks: list[dict[str, Any]]) -> dict[str, int]:
    return {str(block.get("id") or ""): index for index, block in enumerate(blocks)}


def group_child_ids(record: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> list[str]:
    child_ids: list[str] = []
    previous_text_id = str(((record.get("previous_block") or {}).get("id")) or "")
    if previous_text_id and previous_text_id in by_id and by_id[previous_text_id].get("type") != "table":
        child_ids.append(previous_text_id)
    for word in record.get("word_bank_blocks") or []:
        word_id = str(word.get("id") or "")
        if word_id and word_id in by_id and word_id not in child_ids:
            child_ids.append(word_id)
    previous_table_id = str(record.get("previous_table_block_id") or "")
    if previous_table_id and previous_table_id in by_id and previous_table_id not in child_ids:
        child_ids.append(previous_table_id)
    block_id = str(record.get("block_id") or "")
    if block_id and block_id in by_id and block_id not in child_ids:
        child_ids.append(block_id)
    next_id = str(((record.get("next_block") or {}).get("id")) or "")
    if next_id and next_id in by_id and by_id[next_id].get("markdown") == "Use Vocabulary in Writing":
        child_ids.append(next_id)
    return child_ids


def render_table(markdown: str, *, preserve_answer_spaces: bool) -> str:
    table_match = TABLE_RE.search(markdown or "")
    table_html = table_match.group(0) if table_match else markdown
    if not preserve_answer_spaces:
        return table_html
    rendered, _empty, _inline = render_table_with_answer_spaces(table_html)
    return rendered


def render_group(group: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> str:
    layout = str(group.get("paired_vocabulary_layout") or "")
    child_ids = [str(item) for item in group.get("children") or []]
    child_blocks = [by_id[item] for item in child_ids if item in by_id]
    tables = [block for block in child_blocks if block.get("type") == "table"]
    word_blocks = [
        block
        for block in child_blocks
        if block.get("type") in {"paragraph", "note"} and block.get("markdown") != "Use Vocabulary in Writing"
    ]
    follow_ups = [block for block in child_blocks if block.get("markdown") == "Use Vocabulary in Writing"]
    source_crop = str(group.get("source_context_crop") or "")
    source_link = f'<p class="source-ref">source: {html.escape(source_crop)}</p>' if source_crop else ""
    if layout == "two_table_vocabulary_definition_pair" and len(tables) >= 2:
        body = (
            '<div class="paired-vocab-grid">'
            f'<div class="paired-vocab-panel">{render_table(block_text(tables[0]), preserve_answer_spaces=True)}</div>'
            f'<div class="paired-vocab-panel">{render_table(block_text(tables[1]), preserve_answer_spaces=True)}</div>'
            "</div>"
        )
    else:
        word_items = "".join(
            f"<span>{html.escape(block_text(block))}</span>"
            for block in word_blocks
            if block_text(block) and block_text(block) != "Vocabulary"
        )
        word_bank = f'<div class="paired-vocab-word-bank">{word_items}</div>' if word_items else ""
        table = render_table(block_text(tables[-1]), preserve_answer_spaces=True) if tables else ""
        body = word_bank + f'<div class="paired-vocab-table">{table}</div>'
    follow = "".join(f'<p class="paired-vocab-follow">{html.escape(block_text(block))}</p>' for block in follow_ups)
    classes = f"block block-question_group paired-vocab-group paired-vocab-{safe_slug(layout)}"
    return f'<section id="{html.escape(str(group.get("id") or ""))}" class="{classes}">{source_link}{body}{follow}</section>'


def build_patched_html(document: dict[str, Any], groups: list[dict[str, Any]]) -> str:
    blocks = document.get("blocks") if isinstance(document.get("blocks"), list) else []
    by_id = block_by_id(blocks)
    group_by_first_child = {str((group.get("children") or [""])[0]): group for group in groups if group.get("children")}
    skip_ids = {
        str(child_id)
        for group in groups
        for child_id in (group.get("children") or [])
    }
    body_parts: list[str] = []
    for block in blocks:
        block_id = str(block.get("id") or "")
        group = group_by_first_child.get(block_id)
        if group:
            body_parts.append(render_group(group, by_id))
        if block_id in skip_ids:
            continue
        markdown = block_text(block)
        block_type = str(block.get("type") or "paragraph")
        if TABLE_RE.match(markdown):
            body_parts.append(
                f'<div id="{html.escape(block_id)}" class="block block-table table-wrap">{render_table(markdown, preserve_answer_spaces=False)}</div>'
            )
        elif markdown.startswith("#"):
            level = min(len(markdown) - len(markdown.lstrip("#")) + 1, 6)
            body_parts.append(f'<h{level} id="{html.escape(block_id)}">{html.escape(markdown.lstrip("#").strip())}</h{level}>')
        else:
            tag = "div" if block_type in {"question_group", "question", "option"} else "p"
            body_parts.append(f'<{tag} id="{html.escape(block_id)}" class="block block-{html.escape(block_type)}">{html.escape(markdown)}</{tag}>')
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(str(document.get("title") or "Paired Vocabulary Patch"))}</title>
  <style>
    @page {{ size: A4; margin: 16mm 15mm 18mm; }}
    body {{ margin: 0; color: #111; font-family: Arial, Helvetica, sans-serif; font-size: 10.5pt; line-height: 1.42; }}
    main {{ max-width: 178mm; margin: 0 auto; }}
    p, .block {{ margin: 0 0 6pt; }}
    table {{ width: 100%; border-collapse: collapse; margin: 0; }}
    td, th {{ border: 0.5pt solid #777; padding: 4pt 5pt; vertical-align: top; }}
    .paired-vocab-group {{ border: 0.6pt solid #888; padding: 7pt; margin: 8pt 0; break-inside: avoid; page-break-inside: avoid; }}
    .paired-vocab-grid {{ display: grid; grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.25fr); gap: 8pt; align-items: start; }}
    .paired-vocab-word-bank {{ border: 0.6pt solid #9a7b93; padding: 5pt 7pt; margin-bottom: 7pt; display: flex; flex-wrap: wrap; gap: 4pt 12pt; }}
    .paired-vocab-word-bank span {{ white-space: nowrap; }}
    .answer-cell {{ min-height: 20pt; }}
    .answer-space {{ display: block; min-height: 18pt; border-bottom: 0.8pt solid #111; margin: 3pt 1pt; }}
    .answer-line {{ display: inline-block; width: 14mm; border-bottom: 0.8pt solid #111; vertical-align: -0.1em; margin: 0 1.5mm; }}
    .source-ref {{ font-size: 8pt; color: #666; margin-bottom: 4pt; }}
    .paired-vocab-follow {{ margin-top: 6pt; font-weight: 600; }}
  </style>
</head>
<body><main>
{''.join(body_parts)}
</main></body>
</html>
"""


def build_patch_preview_html(document: dict[str, Any], report: dict[str, Any]) -> str:
    blocks = document.get("blocks") if isinstance(document.get("blocks"), list) else []
    by_id = block_by_id(blocks)
    summary = json.dumps({key: value for key, value in report.items() if key != "groups"}, ensure_ascii=False, indent=2)
    groups = report.get("groups") if isinstance(report.get("groups"), list) else []
    sections = []
    for group in groups:
        sections.append(
            "<article>"
            f"<h2>{html.escape(str(group.get('id') or ''))}</h2>"
            f"<p><strong>Layout:</strong> {html.escape(str(group.get('paired_vocabulary_layout') or ''))} | "
            f"<strong>Children:</strong> {html.escape(', '.join(str(child) for child in group.get('children') or []))}</p>"
            f"{render_group(group, by_id)}"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paired Vocabulary Compiler Patch Preview</title>
  <style>
    body {{ margin: 24px; color: #111; font-family: Arial, Helvetica, sans-serif; font-size: 14px; }}
    pre {{ white-space: pre-wrap; border: 1px solid #bbb; padding: 12px; background: #f7f7f7; }}
    article {{ border-top: 1px solid #bbb; padding: 18px 0; break-inside: avoid; }}
    table {{ width: 100%; border-collapse: collapse; margin: 0; }}
    td, th {{ border: 1px solid #888; padding: 6px 8px; vertical-align: top; }}
    .paired-vocab-group {{ border: 1px solid #aaa; padding: 12px; }}
    .paired-vocab-grid {{ display: grid; grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.25fr); gap: 14px; }}
    .paired-vocab-word-bank {{ border: 1px solid #9a7b93; padding: 8px; margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 8px 18px; }}
    .paired-vocab-word-bank span {{ white-space: nowrap; }}
    .answer-space {{ display: block; min-height: 28px; border-bottom: 1.5px solid #333; margin: 6px 2px; }}
    .answer-line {{ display: inline-block; width: 38px; border-bottom: 1.5px solid #333; margin: 0 3px; vertical-align: -0.1em; }}
    .source-ref {{ font-size: 12px; color: #666; }}
  </style>
</head>
<body>
  <h1>Paired Vocabulary Compiler Patch Preview</h1>
  <pre>{html.escape(summary)}</pre>
  {''.join(sections)}
</body>
</html>
"""


def build_patch(standard_dir: Path) -> dict[str, Any]:
    document = read_json(standard_dir / "standard_document.json")
    confirmation = read_json(standard_dir / "paired_vocabulary_source_confirmation.json")
    contract = read_json(standard_dir / "paired_vocabulary_renderer_contract_audit.json")
    original_audit = read_json(standard_dir / "workbook_relation_audit.json")
    blocks = copy.deepcopy(document.get("blocks") if isinstance(document.get("blocks"), list) else [])
    by_id = block_by_id(blocks)
    idx = index_by_id(blocks)
    groups: list[dict[str, Any]] = []
    patched_table_ids: set[str] = set()
    for record in confirmation.get("records") or []:
        block_id = str(record.get("block_id") or "")
        if block_id not in by_id:
            continue
        children = group_child_ids(record, by_id)
        if not children:
            continue
        group_id = f"paired-vocab:{block_id}"
        group = {
            "id": group_id,
            "type": "question_group",
            "subtype": "paired_vocabulary",
            "markdown": "Vocabulary Review",
            "line_start": by_id[children[0]].get("line_start"),
            "line_end": by_id[children[-1]].get("line_end") or by_id[children[-1]].get("line_start"),
            "heading_path": by_id[block_id].get("heading_path") or [],
            "layout": {
                "keep_together": True,
                "profile_intent": "paired_vocabulary_group",
                "layout_intent": "paired_vocabulary",
            },
            "children": children,
            "paired_vocabulary_layout": record.get("layout_bucket"),
            "source_context_crop": record.get("source_context_crop") or "",
            "source_layout_confirmed": True,
        }
        groups.append(group)
        for child_id in children:
            child = by_id.get(str(child_id))
            if not child:
                continue
            child["parent_id"] = group_id
            child.setdefault("layout", {})["paired_vocabulary_child"] = True
            if child.get("type") == "table":
                patched_table_ids.add(str(child.get("id") or ""))

    patched_document = copy.deepcopy(document)
    patched_document["blocks"] = blocks
    patched_document.setdefault("relations", [])
    for group in groups:
        patched_document["relations"].append(
            {"from": group["id"], "type": "paired_vocabulary_contains", "to": list(group.get("children") or [])}
        )
    patched_document.setdefault("metadata", {})["paired_vocabulary_patch"] = {
        "policy": "compiler_adjacent_artifact_only",
        "group_count": len(groups),
        "patched_table_count": len(patched_table_ids),
    }

    original_real_gaps = int(original_audit.get("real_profile_gap_count") or 0)
    original_orphan_tables = [
        item
        for item in original_audit.get("items") or []
        if item.get("kind") == "orphan_table_question" and item.get("disposition") == "real_profile_gap"
    ]
    original_orphan_table_ids = {str(item.get("block_id") or "") for item in original_orphan_tables}
    removed_orphan_table_ids = sorted(original_orphan_table_ids & patched_table_ids)
    remaining_orphan_table_ids = sorted(original_orphan_table_ids - patched_table_ids)
    reconstruction_ids = set(contract.get("known_reconstruction_blocker_block_ids") or [])
    report = {
        "schema": "luceon-standard-paired-vocabulary-compiler-patch/v1",
        "standard_dir": str(standard_dir),
        "policy": "compiler_adjacent_artifact_only_no_main_standard_mutation_no_gate_closure",
        "decision_boundary": (
            "This patch applies source-confirmed paired vocabulary grouping/rendering into isolated artifacts. "
            "It does not overwrite standard_document.json, standard.html, standard.pdf, or acceptance reports."
        ),
        "source_confirmation": "paired_vocabulary_source_confirmation.json",
        "source_contract": "paired_vocabulary_renderer_contract_audit.json",
        "group_count": len(groups),
        "patched_table_count": len(patched_table_ids),
        "removed_orphan_table_gap_count": len(removed_orphan_table_ids),
        "removed_orphan_table_gap_block_ids": removed_orphan_table_ids,
        "remaining_original_orphan_table_gap_count": len(remaining_orphan_table_ids),
        "original_real_profile_gap_count": original_real_gaps,
        "projected_real_profile_gap_count_after_patch": original_real_gaps - len(removed_orphan_table_ids),
        "reconstruction_blocker_retained_count": len(reconstruction_ids & patched_table_ids),
        "reconstruction_blocker_retained_block_ids": sorted(reconstruction_ids & patched_table_ids),
        "candidate_rule_verdict": "compiler_patch_artifact_ready_for_pdf_visual_regression_not_gate_closure",
        "groups": groups,
    }
    return {"document": patched_document, "report": report}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    patch = build_patch(args.standard_dir)
    out_dir = args.standard_dir / "paired_vocabulary_compiler_patch"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "patched_standard_document.json", patch["document"])
    write_json(out_dir / "paired_vocabulary_compiler_patch_report.json", patch["report"])
    (out_dir / "patched_standard.html").write_text(build_patched_html(patch["document"], patch["report"]["groups"]), encoding="utf-8")
    (out_dir / "patched_groups_preview.html").write_text(build_patch_preview_html(patch["document"], patch["report"]), encoding="utf-8")
    print(json.dumps({k: v for k, v in patch["report"].items() if k != "groups"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
