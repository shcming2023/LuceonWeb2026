#!/usr/bin/env python3
"""Aggregate paired-vocabulary source blank-box reconstruction blockers."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def source_record_ids(record: dict[str, Any]) -> list[str]:
    ids = [str(record.get("block_id") or "")]
    previous = str(record.get("previous_table_block_id") or "")
    if previous:
        ids.append(previous)
    return [value for value in ids if value]


def collect_records(path: Path, source_label: str) -> list[dict[str, Any]]:
    data = read_json(path)
    manual = data.get("manual_visual_inspection") or {}
    manual_blockers = set(str(value) for value in manual.get("known_content_reconstruction_blocker_block_ids") or [])
    records: list[dict[str, Any]] = []
    for record in data.get("records") or []:
        ids = source_record_ids(record)
        block_id = str(record.get("block_id") or "")
        is_blocker = bool(record.get("known_content_reconstruction_blocker")) or bool(manual_blockers & set(ids))
        records.append(
            {
                "source_label": source_label,
                "source_report": str(path),
                "block_id": block_id,
                "table_ids": ids,
                "layout_bucket": record.get("layout_bucket") or "",
                "source_page_number": record.get("source_page_number"),
                "source_context_crop": record.get("source_context_crop") or "",
                "existing_table_source_crop": record.get("existing_table_source_crop") or "",
                "word_bank_count": record.get("word_bank_count"),
                "manual_visual_outcome": record.get("manual_visual_outcome") or "",
                "known_content_reconstruction_blocker": is_blocker,
                "known_content_reconstruction_blocker_reason": record.get("known_content_reconstruction_blocker_reason")
                or manual.get("finding")
                or "",
                "standard_table_text": str(record.get("standard_table_text") or "")[:1400],
            }
        )
    return records


def section_for_paired_vocab_table(standard_html: str, table_id: str) -> str:
    if not table_id:
        return ""
    section_match = re.search(
        rf'<section\b[^>]*\bid="{re.escape("paired-vocab:" + table_id)}"[^>]*>.*?</section>',
        standard_html,
        flags=re.I | re.S,
    )
    if section_match:
        return section_match.group(0)
    block_match = re.search(
        rf'<[^>]+\bid="{re.escape(table_id)}"[^>]*>.*?(?=<[^>]+\bid="b-[^"]+"|</body>|$)',
        standard_html,
        flags=re.I | re.S,
    )
    return block_match.group(0) if block_match else ""


def source_blank_preservation(record: dict[str, Any], standard_html: str) -> dict[str, Any]:
    table_ids = [str(value) for value in record.get("table_ids") or [] if str(value)]
    sections: dict[str, dict[str, Any]] = {}
    total_count = 0
    for table_id in table_ids:
        section = section_for_paired_vocab_table(standard_html, table_id)
        count = section.count("answer-line-source")
        total_count += count
        sections[table_id] = {
            "paired_vocab_section_found": bool(section),
            "answer_line_source_count": count,
        }
    status = "preserved_in_standard_html" if total_count > 0 else "missing_from_standard_html"
    return {
        "source_blank_preservation_status": status,
        "source_blank_preserved": total_count > 0,
        "source_blank_preserved_count": total_count,
        "standard_html_section_checks": sections,
    }


def build_audit(standard_dir: Path, source_reports: list[Path]) -> dict[str, Any]:
    paired = read_json(standard_dir / "paired_vocabulary_report.json")
    print_qa = read_json(standard_dir / "print_qa_report.json")
    standard_html = (standard_dir / "standard.html").read_text(encoding="utf-8") if (standard_dir / "standard.html").exists() else ""
    groups = paired.get("groups") if isinstance(paired.get("groups"), list) else []
    records: list[dict[str, Any]] = []
    for index, path in enumerate(source_reports, start=1):
        label = "base_source_confirmation" if index == 1 else f"delta_source_confirmation_{index - 1}"
        records.extend(collect_records(path, label))

    for record in records:
        record.update(source_blank_preservation(record, standard_html))

    blocker_records = [record for record in records if record.get("known_content_reconstruction_blocker")]
    resolved_blocker_records = [record for record in blocker_records if record.get("source_blank_preserved")]
    remaining_blocker_records = [record for record in blocker_records if not record.get("source_blank_preserved")]
    resolved_blocker_ids = sorted({table_id for record in resolved_blocker_records for table_id in record.get("table_ids") or []})
    remaining_blocker_ids = sorted({table_id for record in remaining_blocker_records for table_id in record.get("table_ids") or []})
    source_blank_preserved_blocker_count = sum(
        int(record.get("source_blank_preserved_count") or 0) for record in resolved_blocker_records
    )
    compiler_table_ids = sorted(
        {
            str(table_id)
            for group in groups
            for table_id in group.get("table_ids") or []
            if str(table_id)
        }
    )
    confirmed_table_ids = sorted({table_id for record in records for table_id in record.get("table_ids") or []})
    table_id_sets_match = compiler_table_ids == confirmed_table_ids
    real_pdf_render_ok = bool(print_qa.get("pdf_ok"))
    can_close_paired_gap = table_id_sets_match and not remaining_blocker_ids and real_pdf_render_ok
    return {
        "schema": "luceon-standard-paired-vocabulary-blank-box-reconstruction-audit/v2",
        "standard_dir": str(standard_dir),
        "source_reports": [str(path) for path in source_reports],
        "policy": "close_paired_vocabulary_blank_box_subrule_only_when_source_blanks_are_preserved_in_standard_html_and_real_pdf_renders",
        "decision_boundary": (
            "This audit aggregates source-confirmed paired-vocabulary tables whose source blank boxes "
            "were previously missing from Standard table text/rendering. A blocker can close for this "
            "paired-vocabulary subrule only when the compiler/source-confirmed table sets match, source "
            "blank placeholders are present in Standard HTML for the blocker records, and a real Standard PDF render passes. "
            "This does not promote the whole exercise_workbook profile."
        ),
        "compiler_group_count": paired.get("group_count") or 0,
        "compiler_table_ids": compiler_table_ids,
        "source_confirmed_table_ids": confirmed_table_ids,
        "compiler_source_table_ids_match": table_id_sets_match,
        "real_pdf_render_ok": real_pdf_render_ok,
        "pdf_page_count": print_qa.get("pdf_page_count"),
        "source_confirmed_record_count": len(records),
        "known_blank_box_reconstruction_blocker_count": len(remaining_blocker_ids),
        "known_blank_box_reconstruction_blocker_table_ids": remaining_blocker_ids,
        "source_blank_preserved_blocker_table_ids": resolved_blocker_ids,
        "source_blank_preserved_blocker_record_count": len(resolved_blocker_records),
        "source_blank_preserved_blocker_count": source_blank_preserved_blocker_count,
        "gate_implications": {
            "can_close_paired_vocabulary_relation_gap": can_close_paired_gap,
            "can_promote_exercise_workbook_profile": False,
            "required_next_action": (
                "paired_vocabulary_blank_box_subrule_closed_keep_g7plus_review_for_broader_relation_formula_table_blockers"
                if can_close_paired_gap
                else "implement_source_blank_box_preservation_or_table_rebuild_then_run_real_pdf_visual_regression"
            ),
        },
        "records": records,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({key: value for key, value in report.items() if key != "records"}, ensure_ascii=False, indent=2)
    rows: list[str] = []
    for record in report.get("records") or []:
        crop = str(record.get("source_context_crop") or "")
        crop_html = f'<img src="{html.escape(crop)}" alt="source context">' if crop else ""
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(record.get('block_id') or ''))}</td>"
            f"<td>{html.escape(', '.join(record.get('table_ids') or []))}</td>"
            f"<td>{html.escape(str(record.get('layout_bucket') or ''))}</td>"
            f"<td>{html.escape(str(record.get('known_content_reconstruction_blocker') or False))}</td>"
            f"<td>{html.escape(str(record.get('source_blank_preservation_status') or ''))}</td>"
            f"<td>{html.escape(str(record.get('source_blank_preserved_count') or 0))}</td>"
            f"<td>{html.escape(str(record.get('known_content_reconstruction_blocker_reason') or ''))}</td>"
            f"<td>{crop_html}</td>"
            f"<td><pre>{html.escape(str(record.get('standard_table_text') or ''))}</pre></td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paired Vocabulary Blank-Box Reconstruction Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    img {{ max-width: 420px; border: 1px solid #ccc; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Paired Vocabulary Blank-Box Reconstruction Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead>
      <tr><th>Block</th><th>Table IDs</th><th>Layout</th><th>Prior Blocker</th><th>Blank Status</th><th>Blank Count</th><th>Reason</th><th>Source Crop</th><th>Standard Table Text</th></tr>
    </thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--source-report", action="append", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_audit(args.standard_dir, args.source_report)
    write_json(args.standard_dir / "paired_vocabulary_blank_box_reconstruction_audit.json", report)
    (args.standard_dir / "paired_vocabulary_blank_box_reconstruction_audit.html").write_text(
        build_html(report),
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in report.items() if key != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
