#!/usr/bin/env python3
"""Compare paired-vocabulary compiler groups with source-confirmed evidence."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def source_table_ids(source_confirmation: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for record in source_confirmation.get("records") or []:
        block_id = str(record.get("block_id") or "")
        if block_id:
            ids.add(block_id)
        previous_id = str(record.get("previous_table_block_id") or "")
        if previous_id:
            ids.add(previous_id)
    return ids


def compiler_table_ids(paired_report: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for group in paired_report.get("groups") or []:
        ids.update(str(table_id) for table_id in group.get("table_ids") or [] if table_id)
    return ids


def context_for_block(document: dict[str, Any], block_id: str, radius: int = 4) -> list[dict[str, Any]]:
    blocks = document.get("blocks") if isinstance(document.get("blocks"), list) else []
    index_by_id = {str(block.get("id") or ""): index for index, block in enumerate(blocks)}
    index = index_by_id.get(block_id)
    if index is None:
        return []
    result: list[dict[str, Any]] = []
    for pos in range(max(0, index - radius), min(len(blocks), index + radius + 1)):
        block = blocks[pos]
        result.append(
            {
                "id": block.get("id"),
                "type": block.get("type"),
                "subtype": block.get("subtype") or "",
                "parent_id": block.get("parent_id") or "",
                "line_start": block.get("line_start"),
                "heading_path": block.get("heading_path") or [],
                "text": str(block.get("markdown") or "").replace("\n", " ")[:500],
            }
        )
    return result


def build_audit(standard_dir: Path, source_confirmation_path: Path) -> dict[str, Any]:
    paired_report = read_json(standard_dir / "paired_vocabulary_report.json")
    document = read_json(standard_dir / "standard_document.json")
    source_confirmation = read_json(source_confirmation_path)
    compiler_ids = compiler_table_ids(paired_report)
    confirmed_ids = source_table_ids(source_confirmation)
    confirmed_records = {
        str(record.get("block_id") or ""): record for record in source_confirmation.get("records") or []
    }
    previous_to_record = {
        str(record.get("previous_table_block_id") or ""): record
        for record in source_confirmation.get("records") or []
        if record.get("previous_table_block_id")
    }
    confirmed_records.update(previous_to_record)

    items: list[dict[str, Any]] = []
    for table_id in sorted(compiler_ids | confirmed_ids):
        compiler_group = None
        for group in paired_report.get("groups") or []:
            if table_id in [str(value) for value in group.get("table_ids") or []]:
                compiler_group = group
                break
        source_record = confirmed_records.get(table_id) or {}
        if table_id in compiler_ids and table_id in confirmed_ids:
            status = "compiler_and_source_confirmed"
        elif table_id in compiler_ids:
            status = "compiler_candidate_needs_source_confirmation"
        else:
            status = "source_confirmed_missing_from_compiler"
        items.append(
            {
                "table_id": table_id,
                "status": status,
                "compiler_group_id": (compiler_group or {}).get("id") or "",
                "compiler_layout": (compiler_group or {}).get("layout") or "",
                "compiler_children": (compiler_group or {}).get("children") or [],
                "source_layout_bucket": source_record.get("layout_bucket") or "",
                "source_context_crop": source_record.get("source_context_crop") or "",
                "source_page_number": source_record.get("source_page_number"),
                "context": context_for_block(document, table_id),
            }
        )

    status_counts: dict[str, int] = {}
    for item in items:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1
    return {
        "schema": "luceon-standard-paired-vocabulary-compiler-evidence-audit/v1",
        "standard_dir": str(standard_dir),
        "source_confirmation": str(source_confirmation_path),
        "policy": "audit_only_no_gate_closure_no_source_visual_promotion",
        "decision_boundary": (
            "This audit compares compiler-detected paired vocabulary groups with source-confirmed "
            "visual evidence. Compiler-only candidates require source PDF visual confirmation before "
            "being used as gate closure evidence."
        ),
        "compiler_group_count": paired_report.get("group_count") or 0,
        "compiler_table_count": len(compiler_ids),
        "source_confirmed_table_count": len(confirmed_ids),
        "status_counts": status_counts,
        "compiler_only_table_ids": sorted(compiler_ids - confirmed_ids),
        "source_only_table_ids": sorted(confirmed_ids - compiler_ids),
        "confirmed_compiler_table_ids": sorted(compiler_ids & confirmed_ids),
        "items": items,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False, indent=2)
    rows: list[str] = []
    for item in report.get("items") or []:
        context = "<br>".join(
            html.escape(f"{block.get('id')} {block.get('type')} {block.get('text')}")
            for block in item.get("context") or []
        )
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('table_id') or ''))}</td>"
            f"<td>{html.escape(str(item.get('status') or ''))}</td>"
            f"<td>{html.escape(str(item.get('compiler_layout') or ''))}</td>"
            f"<td>{html.escape(str(item.get('source_layout_bucket') or ''))}</td>"
            f"<td>{html.escape(str(item.get('source_context_crop') or ''))}</td>"
            f"<td>{context}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paired Vocabulary Compiler Evidence Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Paired Vocabulary Compiler Evidence Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Table</th><th>Status</th><th>Compiler Layout</th><th>Source Layout</th><th>Source Crop</th><th>Context</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--source-confirmation", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_audit(args.standard_dir, args.source_confirmation)
    write_json(args.standard_dir / "paired_vocabulary_compiler_evidence_audit.json", report)
    (args.standard_dir / "paired_vocabulary_compiler_evidence_audit.html").write_text(
        build_html(report),
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
