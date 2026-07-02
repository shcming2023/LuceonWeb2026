#!/usr/bin/env python3
"""Audit the effect surface of workbook virtual question grouping."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def relation_by_block_id(standard_dir: Path) -> dict[str, dict[str, Any]]:
    relation = read_json(standard_dir / "workbook_relation_audit.json")
    return {
        str(item.get("block_id") or ""): item
        for item in relation.get("items") or []
        if item.get("kind") == "ungrouped_question" and str(item.get("block_id") or "")
    }


def real_gap_keys(standard_dir: Path) -> set[tuple[str, str]]:
    relation = read_json(standard_dir / "workbook_relation_audit.json")
    return {
        (str(item.get("kind") or ""), str(item.get("block_id") or ""))
        for item in relation.get("items") or []
        if item.get("disposition") == "real_profile_gap" and str(item.get("block_id") or "")
    }


def build_audit(base_dir: Path, current_dir: Path, out_dir: Path) -> dict[str, Any]:
    base_relation = relation_by_block_id(base_dir)
    base_real = real_gap_keys(base_dir)
    current_real = real_gap_keys(current_dir)
    virtual = read_json(current_dir / "workbook_virtual_question_group_report.json")
    grouped_ids = [
        str(child_id)
        for group in virtual.get("groups") or []
        for child_id in group.get("children") or []
        if str(child_id)
    ]
    grouped_counts: Counter[str] = Counter()
    grouped_reason_counts: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    for block_id in grouped_ids:
        base_item = base_relation.get(block_id) or {}
        disposition = str(base_item.get("disposition") or "not_in_base_ungrouped_question")
        reason = str(base_item.get("reason") or "not_in_base_ungrouped_question")
        grouped_counts[disposition] += 1
        grouped_reason_counts[reason] += 1
        records.append(
            {
                "block_id": block_id,
                "base_disposition": disposition,
                "base_reason": reason,
                "line_start": base_item.get("line_start"),
                "heading_path": base_item.get("heading_path") or [],
                "previous_text": ((base_item.get("previous_block") or {}).get("text") or "")[:300],
                "text": str(base_item.get("text") or "")[:500],
            }
        )

    removed_real = base_real - current_real
    added_real = current_real - base_real
    report = {
        "schema": "luceon-standard-workbook-virtual-group-effects-audit/v1",
        "base_standard_dir": str(base_dir),
        "current_standard_dir": str(current_dir),
        "virtual_group_report": str(current_dir / "workbook_virtual_question_group_report.json"),
        "policy": "audit_only_no_gate_closure_no_profile_promotion",
        "decision_boundary": (
            "This audit checks what the virtual question grouping rule absorbed relative to the base relation audit. "
            "Grouping old real gaps is expected; grouping old artifact buckets must be recorded as a classifier-boundary risk."
        ),
        "grouped_question_count": len(grouped_ids),
        "grouped_unique_question_count": len(set(grouped_ids)),
        "grouped_base_disposition_counts": dict(grouped_counts),
        "grouped_base_reason_counts": dict(grouped_reason_counts),
        "removed_real_profile_gap_count": len(removed_real),
        "added_real_profile_gap_count": len(added_real),
        "removed_real_kind_counts": dict(Counter(kind for kind, _block_id in removed_real)),
        "added_real_kind_counts": dict(Counter(kind for kind, _block_id in added_real)),
        "risk_flags": {
            "absorbed_prior_explanation_artifact_count": grouped_counts.get("explanation_artifact", 0),
            "has_added_real_gaps": bool(added_real),
            "requires_classifier_boundary_followup": grouped_counts.get("explanation_artifact", 0) > 0,
        },
        "gate_implications": {
            "can_promote_exercise_workbook_profile": False,
            "can_treat_virtual_grouping_as_full_acceptance": False,
            "required_next_action": "document_classifier_boundary_then_audit_remaining_61_relation_gaps",
        },
        "records": records,
    }
    write_json(out_dir / "workbook_virtual_group_effects_audit.json", report)
    (out_dir / "workbook_virtual_group_effects_audit.html").write_text(build_html(report), encoding="utf-8")
    return report


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2)
    rows = []
    for record in report.get("records") or []:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(record.get('base_disposition') or ''))}</td>"
            f"<td>{html.escape(str(record.get('base_reason') or ''))}</td>"
            f"<td>{html.escape(str(record.get('block_id') or ''))}</td>"
            f"<td>{html.escape(' > '.join(record.get('heading_path') or []))}</td>"
            f"<td>{html.escape(str(record.get('previous_text') or ''))}</td>"
            f"<td>{html.escape(str(record.get('text') or ''))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Virtual Group Effects Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Workbook Virtual Group Effects Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Base Disposition</th><th>Base Reason</th><th>Block</th><th>Heading</th><th>Previous</th><th>Text</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-standard-dir", required=True, type=Path)
    parser.add_argument("--current-standard-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_audit(args.base_standard_dir, args.current_standard_dir, args.out_dir)
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
