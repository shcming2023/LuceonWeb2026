#!/usr/bin/env python3
"""Simulate exercise-workbook grouping state-machine rules without mutating Standard."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from audit_standard_workbook_relation_gap_patterns import (  # noqa: E402
    INSTRUCTION_START_RE,
    SECTION_LABELS,
    block_text,
    classify_table_gap,
    read_json,
)
from standard_from_clean import write_json


QUESTION_LIKE_TYPES = {"question", "option", "answer_blank", "captioned_figure", "formula", "table"}
HARD_RESET_TYPES = {"unit_opener", "section", "reading_passage"}


def normalize_label(text: str) -> str:
    return text.strip("* ").lower()


def is_virtual_group_starter(block: dict[str, Any]) -> tuple[bool, str]:
    text = block_text(block)
    norm = normalize_label(text)
    if norm in SECTION_LABELS:
        return True, "section_label"
    if INSTRUCTION_START_RE.match(text):
        return True, "instruction_paragraph"
    if text.endswith(":") and len(text) <= 120:
        return True, "colon_label"
    return False, ""


def relation_gap_ids(audit: dict[str, Any]) -> tuple[set[str], set[str]]:
    question_ids = {
        str(item.get("block_id") or "")
        for item in audit.get("items") or []
        if item.get("kind") == "ungrouped_question" and item.get("disposition") == "real_profile_gap"
    }
    table_ids = {
        str(item.get("block_id") or "")
        for item in audit.get("items") or []
        if item.get("kind") == "orphan_table_question" and item.get("disposition") == "real_profile_gap"
    }
    return question_ids, table_ids


def simulate_persistent_group(blocks: list[dict[str, Any]], question_gap_ids: set[str], table_gap_ids: set[str]) -> dict[str, Any]:
    active_group: dict[str, Any] | None = None
    active_question: dict[str, Any] | None = None
    covered_question_ids: set[str] = set()
    covered_table_ids: set[str] = set()
    virtual_group_count = 0
    starter_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    sample: list[dict[str, Any]] = []

    for index, block in enumerate(blocks):
        block_id = str(block.get("id") or "")
        block_type = str(block.get("type") or "")
        if block_type in HARD_RESET_TYPES:
            active_group = None
            active_question = None
            continue
        is_starter, starter_kind = is_virtual_group_starter(block)
        if is_starter:
            active_group = {
                "id": f"virtual:{block_id}",
                "block_id": block_id,
                "line_start": block.get("line_start"),
                "heading_path": block.get("heading_path") or [],
                "starter_kind": starter_kind,
                "text": block_text(block)[:240],
            }
            active_question = None
            virtual_group_count += 1
            starter_counts[starter_kind] += 1
            continue
        if block_type == "question":
            if active_group and block_id in question_gap_ids:
                covered_question_ids.add(block_id)
                if len(sample) < 80:
                    sample.append(
                        {
                            "covered_kind": "question",
                            "block_id": block_id,
                            "line_start": block.get("line_start"),
                            "group_starter": active_group,
                            "text": block_text(block)[:300],
                        }
                    )
            active_question = block
            continue
        if block_type == "table" and block_id in table_gap_ids:
            if active_question or active_group:
                covered_table_ids.add(block_id)
                if active_question:
                    risk_counts["table_attached_to_active_question_or_group"] += 1
                else:
                    risk_counts["table_attached_to_active_group_only"] += 1
                if len(sample) < 80:
                    sample.append(
                        {
                            "covered_kind": "table",
                            "block_id": block_id,
                            "line_start": block.get("line_start"),
                            "group_starter": active_group or {},
                            "active_question_id": (active_question or {}).get("id"),
                            "text": block_text(block)[:300],
                        }
                    )
            continue
        if block_type not in QUESTION_LIKE_TYPES and block_type == "paragraph":
            text = block_text(block)
            if normalize_label(text) in SECTION_LABELS:
                active_question = None
            elif len(text) > 180 and not INSTRUCTION_START_RE.match(text):
                risk_counts["long_paragraph_inside_active_group"] += 1

    by_id = {str(block.get("id") or ""): block for block in blocks}
    remaining_question_ids = sorted(question_gap_ids - covered_question_ids)
    remaining_table_ids = sorted(table_gap_ids - covered_table_ids)
    remaining_sample = []
    for block_id in (remaining_question_ids + remaining_table_ids)[:20]:
        block = by_id.get(block_id, {})
        remaining_sample.append(
            {
                "block_id": block_id,
                "type": block.get("type"),
                "subtype": block.get("subtype") or "",
                "line_start": block.get("line_start"),
                "heading_path": block.get("heading_path") or [],
                "text": block_text(block)[:300],
            }
        )
    risk_level = "high" if risk_counts else "medium"
    return {
        "policy": "persistent_virtual_group_until_section_or_new_starter",
        "risk_level": risk_level,
        "virtual_group_count": virtual_group_count,
        "starter_counts": dict(starter_counts),
        "covered_question_gap_count": len(covered_question_ids),
        "covered_table_gap_count": len(covered_table_ids),
        "covered_total_gap_count": len(covered_question_ids) + len(covered_table_ids),
        "remaining_question_gap_count": len(question_gap_ids - covered_question_ids),
        "remaining_table_gap_count": len(table_gap_ids - covered_table_ids),
        "risk_counts": dict(risk_counts),
        "remaining_sample": remaining_sample,
        "sample": sample,
    }


def simulate_guarded_group(blocks: list[dict[str, Any]], question_gap_ids: set[str], table_gap_ids: set[str]) -> dict[str, Any]:
    active_group: dict[str, Any] | None = None
    active_question: dict[str, Any] | None = None
    covered_question_ids: set[str] = set()
    covered_table_ids: set[str] = set()
    virtual_group_count = 0
    starter_counts: Counter[str] = Counter()
    stop_counts: Counter[str] = Counter()
    sample: list[dict[str, Any]] = []

    for block in blocks:
        block_id = str(block.get("id") or "")
        block_type = str(block.get("type") or "")
        if block_type in HARD_RESET_TYPES:
            active_group = None
            active_question = None
            stop_counts["hard_section_reset"] += 1
            continue
        is_starter, starter_kind = is_virtual_group_starter(block)
        if is_starter:
            active_group = {
                "id": f"virtual:{block_id}",
                "block_id": block_id,
                "line_start": block.get("line_start"),
                "heading_path": block.get("heading_path") or [],
                "starter_kind": starter_kind,
                "text": block_text(block)[:240],
            }
            active_question = None
            virtual_group_count += 1
            starter_counts[starter_kind] += 1
            continue
        if block_type == "paragraph":
            text = block_text(block)
            if len(text) > 180 and not INSTRUCTION_START_RE.match(text):
                active_group = None
                active_question = None
                stop_counts["long_paragraph_reset"] += 1
            continue
        if block_type == "question":
            if active_group and block_id in question_gap_ids:
                covered_question_ids.add(block_id)
                if len(sample) < 80:
                    sample.append(
                        {
                            "covered_kind": "question",
                            "block_id": block_id,
                            "line_start": block.get("line_start"),
                            "group_starter": active_group,
                            "text": block_text(block)[:300],
                        }
                    )
            active_question = block
            continue
        if block_type == "table" and block_id in table_gap_ids:
            if active_question:
                covered_table_ids.add(block_id)
                if len(sample) < 80:
                    sample.append(
                        {
                            "covered_kind": "table",
                            "block_id": block_id,
                            "line_start": block.get("line_start"),
                            "group_starter": active_group or {},
                            "active_question_id": active_question.get("id"),
                            "text": block_text(block)[:300],
                        }
                    )
            continue

    by_id = {str(block.get("id") or ""): block for block in blocks}
    remaining_question_ids = sorted(question_gap_ids - covered_question_ids)
    remaining_table_ids = sorted(table_gap_ids - covered_table_ids)
    remaining_sample = []
    for block_id in (remaining_question_ids + remaining_table_ids)[:20]:
        block = by_id.get(block_id, {})
        remaining_sample.append(
            {
                "block_id": block_id,
                "type": block.get("type"),
                "subtype": block.get("subtype") or "",
                "line_start": block.get("line_start"),
                "heading_path": block.get("heading_path") or [],
                "text": block_text(block)[:300],
            }
        )
    return {
        "policy": "guarded_virtual_group_long_paragraph_reset_table_requires_question",
        "risk_level": "medium",
        "virtual_group_count": virtual_group_count,
        "starter_counts": dict(starter_counts),
        "covered_question_gap_count": len(covered_question_ids),
        "covered_table_gap_count": len(covered_table_ids),
        "covered_total_gap_count": len(covered_question_ids) + len(covered_table_ids),
        "remaining_question_gap_count": len(question_gap_ids - covered_question_ids),
        "remaining_table_gap_count": len(table_gap_ids - covered_table_ids),
        "stop_counts": dict(stop_counts),
        "remaining_sample": remaining_sample,
        "sample": sample,
    }


def conservative_starter_run(pattern_audit: dict[str, Any], real_profile_gap_count: int) -> dict[str, Any]:
    question_bucket_counts = pattern_audit.get("question_count_by_run_bucket") or {}
    table_bucket_counts = pattern_audit.get("table_gap_bucket_counts") or {}
    covered_questions = (
        int(question_bucket_counts.get("section_label_should_start_group") or 0)
        + int(question_bucket_counts.get("instruction_paragraph_should_start_group") or 0)
        + int(question_bucket_counts.get("colon_label_should_start_group") or 0)
    )
    covered_tables = (
        int(table_bucket_counts.get("table_after_instruction_should_attach") or 0)
        + int(table_bucket_counts.get("table_after_section_label_should_attach") or 0)
        + int(table_bucket_counts.get("table_adjacent_to_question_should_attach") or 0)
    )
    return {
        "policy": "cover_only_runs_immediately_after_known_starter",
        "covered_question_gap_count": covered_questions,
        "covered_table_gap_count": covered_tables,
        "covered_total_gap_count": covered_questions + covered_tables,
        "remaining_question_gap_count": int(pattern_audit.get("question_gap_count") or 0) - covered_questions,
        "remaining_table_gap_count": int(pattern_audit.get("table_gap_count") or 0) - covered_tables,
        "remaining_real_profile_gap_count": real_profile_gap_count - covered_questions - covered_tables,
        "risk_note": "Conservative run coverage is safer but leaves most figure/answer/formula-interrupted runs unresolved.",
    }


def build_audit(standard_dir: Path) -> dict[str, Any]:
    document = read_json(standard_dir / "standard_document.json")
    relation_audit = read_json(standard_dir / "workbook_relation_audit.json")
    pattern_audit = read_json(standard_dir / "workbook_relation_gap_pattern_audit.json")
    blocks = document.get("blocks") if isinstance(document.get("blocks"), list) else []
    question_gap_ids, table_gap_ids = relation_gap_ids(relation_audit)

    real_profile_gap_count = int(relation_audit.get("real_profile_gap_count") or 0)
    persistent = simulate_persistent_group(blocks, question_gap_ids, table_gap_ids)
    persistent["remaining_real_profile_gap_count"] = real_profile_gap_count - int(persistent["covered_total_gap_count"])
    guarded = simulate_guarded_group(blocks, question_gap_ids, table_gap_ids)
    guarded["remaining_real_profile_gap_count"] = real_profile_gap_count - int(guarded["covered_total_gap_count"])
    conservative = conservative_starter_run(pattern_audit, real_profile_gap_count)
    return {
        "schema": "luceon-standard-workbook-grouping-state-machine-simulation/v1",
        "standard_dir": str(standard_dir),
        "policy": "dry_run_no_profile_mutation_no_gate_closure",
        "decision_boundary": (
            "This simulation estimates relation-gap reduction from generic exercise_workbook grouping rules. "
            "It does not create groups, edit Standard artifacts, or change acceptance status."
        ),
        "source_relation_audit": "workbook_relation_audit.json",
        "source_pattern_audit": "workbook_relation_gap_pattern_audit.json",
        "real_profile_gap_count": real_profile_gap_count,
        "question_gap_count": len(question_gap_ids),
        "table_gap_count": len(table_gap_ids),
        "conservative_starter_run": conservative,
        "persistent_state_machine": persistent,
        "guarded_state_machine": guarded,
        "candidate_rule_verdict": "audit_promising_but_not_ready_for_compiler"
        if persistent["covered_total_gap_count"] > conservative["covered_total_gap_count"] and persistent.get("risk_counts")
        else "needs_engineering_validation",
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "persistent_state_machine"}, ensure_ascii=False, indent=2)
    sample_rows = []
    for item in (report.get("persistent_state_machine") or {}).get("sample") or []:
        starter = item.get("group_starter") or {}
        sample_rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('covered_kind') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(starter.get('starter_kind') or ''))}</td>"
            f"<td>{html.escape(str(starter.get('text') or ''))}</td>"
            f"<td>{html.escape(str(item.get('text') or ''))}</td>"
            "</tr>"
        )
    guarded_rows = []
    for item in (report.get("guarded_state_machine") or {}).get("sample") or []:
        starter = item.get("group_starter") or {}
        guarded_rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('covered_kind') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(starter.get('starter_kind') or ''))}</td>"
            f"<td>{html.escape(str(starter.get('text') or ''))}</td>"
            f"<td>{html.escape(str(item.get('text') or ''))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Grouping State-Machine Simulation</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Workbook Grouping State-Machine Simulation</h1>
  <pre>{html.escape(summary)}</pre>
  <h2>Persistent State-Machine Sample</h2>
  <table><thead><tr><th>Kind</th><th>Block</th><th>Starter Kind</th><th>Starter</th><th>Text</th></tr></thead><tbody>{"".join(sample_rows)}</tbody></table>
  <h2>Guarded State-Machine Sample</h2>
  <table><thead><tr><th>Kind</th><th>Block</th><th>Starter Kind</th><th>Starter</th><th>Text</th></tr></thead><tbody>{"".join(guarded_rows)}</tbody></table>
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
    write_json(args.standard_dir / "workbook_grouping_state_machine_simulation.json", report)
    (args.standard_dir / "workbook_grouping_state_machine_simulation.html").write_text(build_html(report), encoding="utf-8")
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in {"persistent_state_machine", "guarded_state_machine"}
            }
            | {
                "persistent_state_machine": {k: v for k, v in report["persistent_state_machine"].items() if k != "sample"},
                "guarded_state_machine": {k: v for k, v in report["guarded_state_machine"].items() if k != "sample"},
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
