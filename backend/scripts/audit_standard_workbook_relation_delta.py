#!/usr/bin/env python3
"""Compare workbook relation gaps between two Standard runs."""

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


def real_gap_items(relation_audit: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in relation_audit.get("items") or []
        if item.get("disposition") == "real_profile_gap" and str(item.get("block_id") or "")
    ]


def gap_map(relation_audit: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(item.get("kind") or ""), str(item.get("block_id") or "")): item for item in real_gap_items(relation_audit)}


def paired_vocabulary_table_ids(standard_dir: Path) -> set[str]:
    report = read_json(standard_dir / "paired_vocabulary_report.json")
    return {
        str(table_id)
        for group in report.get("groups") or []
        for table_id in group.get("table_ids") or []
        if str(table_id)
    }


def table_policy_by_id(standard_dir: Path) -> dict[str, dict[str, Any]]:
    report = read_json(standard_dir / "workbook_table_attachment_policy_simulation.json")
    records = report.get("records_sample") if isinstance(report.get("records_sample"), list) else []
    return {str(record.get("block_id") or ""): record for record in records if str(record.get("block_id") or "")}


def summarize_profile(standard_dir: Path) -> dict[str, Any]:
    acceptance = read_json(standard_dir / "standard_acceptance_report.json")
    profile = read_json(standard_dir / "workbook_profile_report.json")
    relation = read_json(standard_dir / "workbook_relation_audit.json")
    metrics = ((profile.get("exercise_relation_contract") or {}).get("metrics") or {})
    return {
        "standard_dir": str(standard_dir),
        "acceptance_status": acceptance.get("status"),
        "quality_score": (acceptance.get("quality_score") or {}).get("score"),
        "workbook_profile_status": profile.get("status"),
        "basic_print_blockers": profile.get("basic_print_blockers") or [],
        "real_profile_gap_count": relation.get("real_profile_gap_count"),
        "question_groups": metrics.get("question_groups"),
        "ungrouped_questions": metrics.get("ungrouped_questions"),
        "orphan_table_questions": metrics.get("orphan_table_questions"),
        "orphan_options": metrics.get("orphan_options"),
        "orphan_answer_blanks": metrics.get("orphan_answer_blanks"),
    }


def bucket_table_delta(
    item: dict[str, Any],
    base_policy: dict[str, dict[str, Any]],
    current_paired_ids: set[str],
) -> dict[str, Any]:
    block_id = str(item.get("block_id") or "")
    policy = base_policy.get(block_id) or {}
    if block_id in current_paired_ids:
        delta_bucket = "paired_vocabulary_compiler_rule"
    elif policy.get("policy_bucket"):
        delta_bucket = f"baseline_policy:{policy.get('policy_bucket')}"
    else:
        delta_bucket = "no_baseline_policy_record"
    return {
        "block_id": block_id,
        "kind": item.get("kind"),
        "delta_bucket": delta_bucket,
        "baseline_policy_bucket": policy.get("policy_bucket") or "",
        "baseline_risk_level": policy.get("risk_level") or "",
        "baseline_table_shape": policy.get("table_shape") or "",
        "line_start": item.get("line_start"),
        "heading_path": item.get("heading_path") or [],
        "text": str(item.get("text") or "")[:700],
    }


def build_audit(base_dir: Path, current_dir: Path, out_dir: Path) -> dict[str, Any]:
    base_relation = read_json(base_dir / "workbook_relation_audit.json")
    current_relation = read_json(current_dir / "workbook_relation_audit.json")
    base_gaps = gap_map(base_relation)
    current_gaps = gap_map(current_relation)
    removed_keys = sorted(set(base_gaps) - set(current_gaps))
    added_keys = sorted(set(current_gaps) - set(base_gaps))
    stable_keys = sorted(set(base_gaps) & set(current_gaps))

    current_paired_ids = paired_vocabulary_table_ids(current_dir)
    base_policy = table_policy_by_id(base_dir)
    removed_records: list[dict[str, Any]] = []
    added_records: list[dict[str, Any]] = []
    removed_kind_counts: Counter[str] = Counter()
    added_kind_counts: Counter[str] = Counter()
    stable_kind_counts: Counter[str] = Counter()
    removed_table_delta_counts: Counter[str] = Counter()
    removed_table_policy_counts: Counter[str] = Counter()
    removed_table_risk_counts: Counter[str] = Counter()

    for key in removed_keys:
        kind, _block_id = key
        item = base_gaps[key]
        removed_kind_counts[kind] += 1
        if kind == "orphan_table_question":
            record = bucket_table_delta(item, base_policy, current_paired_ids)
            removed_table_delta_counts[record["delta_bucket"]] += 1
            removed_table_policy_counts[record["baseline_policy_bucket"] or ""] += 1
            removed_table_risk_counts[record["baseline_risk_level"] or ""] += 1
            removed_records.append(record)
        elif len(removed_records) < 160:
            removed_records.append(
                {
                    "block_id": item.get("block_id"),
                    "kind": kind,
                    "delta_bucket": "non_table_relation_gap_removed",
                    "line_start": item.get("line_start"),
                    "heading_path": item.get("heading_path") or [],
                    "text": str(item.get("text") or "")[:500],
                }
            )

    for key in added_keys[:160]:
        kind, _block_id = key
        item = current_gaps[key]
        added_kind_counts[kind] += 1
        added_records.append(
            {
                "block_id": item.get("block_id"),
                "kind": kind,
                "line_start": item.get("line_start"),
                "heading_path": item.get("heading_path") or [],
                "text": str(item.get("text") or "")[:500],
            }
        )
    for key in added_keys[160:]:
        added_kind_counts[key[0]] += 1
    for key in stable_keys:
        stable_kind_counts[key[0]] += 1

    base_count = int(base_relation.get("real_profile_gap_count") or len(base_gaps))
    current_count = int(current_relation.get("real_profile_gap_count") or len(current_gaps))
    high_risk_removed_tables = int(removed_table_risk_counts.get("high") or 0)
    paired_removed_tables = int(removed_table_delta_counts.get("paired_vocabulary_compiler_rule") or 0)
    profile_contract_status = (
        "not_ready_high_risk_relation_delta_needs_rule_split"
        if high_risk_removed_tables
        else "candidate_rule_needs_full_acceptance_rerun"
    )
    report = {
        "schema": "luceon-standard-workbook-relation-delta-audit/v1",
        "base_standard_dir": str(base_dir),
        "current_standard_dir": str(current_dir),
        "policy": "audit_only_no_gate_closure_no_profile_promotion",
        "decision_boundary": (
            "This audit compares real relation gaps between two Standard runs. It can identify promising "
            "compiler/profile deltas, but it does not prove Basic Print acceptance because review outcomes, "
            "source evidence, and visual closure must be replayed in the target run."
        ),
        "base_profile_summary": summarize_profile(base_dir),
        "current_profile_summary": summarize_profile(current_dir),
        "base_real_profile_gap_count": base_count,
        "current_real_profile_gap_count": current_count,
        "removed_real_profile_gap_count": len(removed_keys),
        "added_real_profile_gap_count": len(added_keys),
        "stable_real_profile_gap_count": len(stable_keys),
        "net_real_profile_gap_delta": current_count - base_count,
        "removed_kind_counts": dict(removed_kind_counts),
        "added_kind_counts": dict(added_kind_counts),
        "stable_kind_counts": dict(stable_kind_counts),
        "current_paired_vocabulary_table_ids": sorted(current_paired_ids),
        "removed_table_gap_count": sum(count for bucket, count in removed_kind_counts.items() if bucket == "orphan_table_question"),
        "removed_table_delta_bucket_counts": dict(removed_table_delta_counts),
        "removed_table_baseline_policy_counts": dict(removed_table_policy_counts),
        "removed_table_baseline_risk_counts": dict(removed_table_risk_counts),
        "paired_vocabulary_removed_table_gap_count": paired_removed_tables,
        "high_risk_removed_table_gap_count": high_risk_removed_tables,
        "profile_contract_candidate_status": profile_contract_status,
        "gate_implications": {
            "can_promote_exercise_workbook_profile": False,
            "can_treat_current_run_as_basic_print_candidate": False,
            "required_next_action": "turn_relation_delta_into_profile_contract_then_rerun_full_acceptance_with_source_evidence",
        },
        "removed_records_sample": removed_records[:220],
        "added_records_sample": added_records,
    }
    write_json(out_dir / "workbook_relation_delta_audit.json", report)
    (out_dir / "workbook_relation_delta_audit.html").write_text(build_html(report), encoding="utf-8")
    return report


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps(
        {k: v for k, v in report.items() if k not in {"removed_records_sample", "added_records_sample"}},
        ensure_ascii=False,
        indent=2,
    )
    rows: list[str] = []
    for item in report.get("removed_records_sample") or []:
        rows.append(
            "<tr>"
            f"<td>removed</td>"
            f"<td>{html.escape(str(item.get('kind') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(item.get('delta_bucket') or ''))}</td>"
            f"<td>{html.escape(str(item.get('baseline_risk_level') or ''))}</td>"
            f"<td>{html.escape(' > '.join(item.get('heading_path') or []))}</td>"
            f"<td>{html.escape(str(item.get('text') or ''))}</td>"
            "</tr>"
        )
    for item in report.get("added_records_sample") or []:
        rows.append(
            "<tr>"
            f"<td>added</td>"
            f"<td>{html.escape(str(item.get('kind') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td></td><td></td>"
            f"<td>{html.escape(' > '.join(item.get('heading_path') or []))}</td>"
            f"<td>{html.escape(str(item.get('text') or ''))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Relation Delta Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Workbook Relation Delta Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Delta</th><th>Kind</th><th>Block</th><th>Bucket</th><th>Risk</th><th>Heading</th><th>Text</th></tr></thead>
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
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in {"removed_records_sample", "added_records_sample"}},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
