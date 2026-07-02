#!/usr/bin/env python3
"""Audit candidate table-attachment profile contracts from relation delta evidence."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


LOW_MEDIUM_POLICIES = {
    "auto_attach_adjacent_question_candidate",
    "auto_attach_instruction_table_candidate",
    "paired_vocabulary_table_needs_layout_rule",
    "question_like_paragraph_table_needs_visual_review",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def real_gap_keys(path: Path) -> set[tuple[str, str]]:
    relation = read_json(path / "workbook_relation_audit.json")
    return {
        (str(item.get("kind") or ""), str(item.get("block_id") or ""))
        for item in relation.get("items") or []
        if item.get("disposition") == "real_profile_gap" and str(item.get("block_id") or "")
    }


def paired_table_ids(path: Path) -> set[str]:
    paired = read_json(path / "paired_vocabulary_report.json")
    return {
        str(table_id)
        for group in paired.get("groups") or []
        for table_id in group.get("table_ids") or []
        if str(table_id)
    }


def classify_contract(record: dict[str, Any], removed: bool, paired_ids: set[str]) -> tuple[str, str]:
    block_id = str(record.get("block_id") or "")
    policy = str(record.get("policy_bucket") or "")
    risk = str(record.get("risk_level") or "")
    if risk == "high":
        return "excluded_high_risk_review", "High-risk table movement must stay review until source visual evidence proves no semantic misbinding."
    if block_id in paired_ids and removed:
        return "contract_ready_paired_vocabulary_only", "Removed by the paired-vocabulary compiler rule and covered by source-confirmed paired-vocabulary evidence."
    if removed and policy in {"auto_attach_adjacent_question_candidate", "auto_attach_instruction_table_candidate"}:
        return "candidate_needs_source_visual_spot_audit", "Low/medium-risk attachment disappeared in the comparison run, but no dedicated source visual contract has verified it."
    if removed and policy == "question_like_paragraph_table_needs_visual_review":
        return "candidate_requires_visual_review_before_contract", "Question-like paragraph attachment disappeared, but the baseline policy already requires visual review."
    if not removed and policy in LOW_MEDIUM_POLICIES:
        return "not_proven_stable_gap", "The table remains a real relation gap in the comparison run, so the policy is not proven by this delta."
    return "review_no_contract_signal", "No low-risk contract signal."


def build_audit(base_dir: Path, current_dir: Path, relation_delta: Path, out_dir: Path) -> dict[str, Any]:
    policy_report = read_json(base_dir / "workbook_table_attachment_policy_simulation.json")
    delta_report = read_json(relation_delta)
    records = policy_report.get("records_sample") if isinstance(policy_report.get("records_sample"), list) else []
    current_gaps = real_gap_keys(current_dir)
    paired_ids = paired_table_ids(current_dir)

    contract_records: list[dict[str, Any]] = []
    contract_counts: Counter[str] = Counter()
    policy_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    removed_counts: Counter[str] = Counter()
    for record in records:
        risk = str(record.get("risk_level") or "")
        policy = str(record.get("policy_bucket") or "")
        block_id = str(record.get("block_id") or "")
        removed = ("orphan_table_question", block_id) not in current_gaps
        contract_status, reason = classify_contract(record, removed, paired_ids)
        contract_counts[contract_status] += 1
        policy_counts[policy] += 1
        risk_counts[risk] += 1
        removed_counts["removed_from_current_run" if removed else "stable_in_current_run"] += 1
        contract_records.append(
            {
                "block_id": block_id,
                "contract_status": contract_status,
                "reason": reason,
                "removed_from_current_run": removed,
                "policy_bucket": policy,
                "risk_level": risk,
                "table_shape": record.get("table_shape") or "",
                "previous_context_kind": record.get("previous_context_kind") or "",
                "next_context_kind": record.get("next_context_kind") or "",
                "heading_path": record.get("heading_path") or [],
                "previous_text": ((record.get("previous_block") or {}).get("text") or "")[:300],
                "next_text": ((record.get("next_block") or {}).get("text") or "")[:300],
                "text": str(record.get("text") or "")[:700],
            }
        )

    ready_count = contract_counts["contract_ready_paired_vocabulary_only"]
    visual_spot_count = contract_counts["candidate_needs_source_visual_spot_audit"]
    visual_review_count = contract_counts["candidate_requires_visual_review_before_contract"]
    stable_count = contract_counts["not_proven_stable_gap"]
    high_count = contract_counts["excluded_high_risk_review"]
    report = {
        "schema": "luceon-standard-workbook-table-attachment-contract-audit/v1",
        "base_standard_dir": str(base_dir),
        "current_standard_dir": str(current_dir),
        "relation_delta_audit": str(relation_delta),
        "policy": "audit_only_contract_split_no_gate_closure",
        "decision_boundary": (
            "This audit splits table-attachment delta evidence into explicit profile-contract buckets. "
            "Only the paired-vocabulary subset is currently contract-ready; other low/medium-risk movement "
            "requires source visual spot audit, and high-risk movement must remain review."
        ),
        "source_relation_delta_status": delta_report.get("profile_contract_candidate_status"),
        "table_gap_count": len(records),
        "contract_status_counts": dict(contract_counts),
        "policy_bucket_counts": dict(policy_counts),
        "risk_level_counts": dict(risk_counts),
        "current_delta_counts": dict(removed_counts),
        "contract_ready_count": ready_count,
        "candidate_source_visual_spot_audit_count": visual_spot_count,
        "candidate_visual_review_before_contract_count": visual_review_count,
        "not_proven_stable_gap_count": stable_count,
        "excluded_high_risk_review_count": high_count,
        "gate_implications": {
            "can_promote_exercise_workbook_profile": False,
            "can_add_broad_table_attachment_rule": False,
            "can_add_paired_vocabulary_contract": ready_count > 0 and visual_spot_count + visual_review_count + high_count > 0,
            "required_next_action": "source_visual_spot_audit_low_medium_non_paired_candidates_before_any_new_table_attachment_contract",
        },
        "records": contract_records,
    }
    write_json(out_dir / "workbook_table_attachment_contract_audit.json", report)
    (out_dir / "workbook_table_attachment_contract_audit.html").write_text(build_html(report), encoding="utf-8")
    return report


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2)
    rows = []
    for item in report.get("records") or []:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('contract_status') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(item.get('removed_from_current_run') or False))}</td>"
            f"<td>{html.escape(str(item.get('policy_bucket') or ''))}</td>"
            f"<td>{html.escape(str(item.get('risk_level') or ''))}</td>"
            f"<td>{html.escape(' > '.join(item.get('heading_path') or []))}</td>"
            f"<td>{html.escape(str(item.get('previous_text') or ''))}</td>"
            f"<td>{html.escape(str(item.get('text') or ''))}</td>"
            f"<td>{html.escape(str(item.get('next_text') or ''))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Table Attachment Contract Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Workbook Table Attachment Contract Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Status</th><th>Block</th><th>Removed</th><th>Policy</th><th>Risk</th><th>Heading</th><th>Previous</th><th>Table</th><th>Next</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-standard-dir", required=True, type=Path)
    parser.add_argument("--current-standard-dir", required=True, type=Path)
    parser.add_argument("--relation-delta", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_audit(args.base_standard_dir, args.current_standard_dir, args.relation_delta, args.out_dir)
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
