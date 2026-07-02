#!/usr/bin/env python3
"""Build a Clean LLM fallback integrity ledger from progress and review items."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

from standard_from_clean import read_json, write_json


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def matching_review_item(record: dict[str, Any], review_items: list[dict[str, Any]]) -> dict[str, Any]:
    chunk_index = record.get("chunk_index")
    status = record.get("status")
    expected_type = {
        "failed": "llm_chunk_failed",
        "reverted_structure_drift": "llm_chunk_reverted_teaching_structure",
    }.get(str(status))
    for item in review_items:
        if item.get("chunk_index") == chunk_index and item.get("type") == expected_type:
            return item
    return {}


def standard_summary(standard_dir: Path | None) -> dict[str, Any]:
    if not standard_dir:
        return {}
    acceptance = read_json(standard_dir / "standard_acceptance_report.json")
    summary = acceptance.get("summary") if isinstance(acceptance.get("summary"), dict) else {}
    gates = acceptance.get("gates") if isinstance(acceptance.get("gates"), dict) else {}
    source = gates.get("source_fidelity") if isinstance(gates.get("source_fidelity"), dict) else {}
    return {
        "acceptance_status": acceptance.get("status"),
        "source_fidelity_status": source.get("status"),
        "standard_text_hash_equals_clean_text_hash": bool(
            source.get("clean_text_hash") and source.get("clean_text_hash") == source.get("standard_text_hash")
        ),
        "open_blocking_review_outcomes": summary.get("review_outcome_open_blocking_count"),
    }


def build_ledger(clean_dir: Path, standard_dir: Path | None) -> dict[str, Any]:
    progress = read_jsonl(clean_dir / "llm_progress.jsonl")
    review_data = read_json(clean_dir / "review_items.json")
    review_items = review_data if isinstance(review_data, list) else []
    structure = read_json(clean_dir / "structure_report.json")
    loss = read_json(clean_dir / "loss_audit.json")
    render = read_json(clean_dir / "render_report.json")
    readability = read_json(clean_dir / "readability_report.json")
    usage = read_json(clean_dir / "llm_usage.json")
    standard = standard_summary(standard_dir)

    fallback_records = [
        record for record in progress if record.get("status") in {"failed", "reverted_structure_drift"}
    ]
    ledger_items: list[dict[str, Any]] = []
    for record in fallback_records:
        review_item = matching_review_item(record, review_items)
        blockers: list[str] = []
        if not review_item:
            blockers.append("missing_matching_review_item")
        ledger_items.append(
            {
                "chunk_index": record.get("chunk_index"),
                "title": record.get("title"),
                "status": record.get("status"),
                "fallback_action": "pre_llm_deterministic_chunk_retained",
                "review_item_type": review_item.get("type"),
                "review_item_message": review_item.get("message"),
                "structure_violations": record.get("structure_violations") or review_item.get("violations") or [],
                "blockers": blockers,
            }
        )

    global_reverts = [
        item for item in review_items if item.get("type") in {"llm_global_reverted_teaching_structure", "llm_sections_reverted_teaching_structure"}
    ]
    required = {
        "llm_progress_present": bool(progress),
        "llm_usage_recorded": bool(usage.get("enabled")),
        "all_failed_or_reverted_chunks_have_review_items": not any(item["blockers"] for item in ledger_items),
        "global_or_section_fallback_recorded": bool(global_reverts),
        "clean_structure_pass": structure.get("status") == "pass",
        "clean_structure_violations_zero": len(structure.get("violations") or []) == 0,
        "loss_audit_pass": loss.get("status") == "pass",
        "forbidden_losses_zero": len(loss.get("forbidden_losses") or []) == 0,
        "render_pdf_ok": bool(render.get("pdf_ok")),
        "readability_pass": readability.get("status") == "pass",
    }
    if standard:
        required.update(
            {
                "standard_source_fidelity_pass": standard.get("source_fidelity_status") == "pass",
                "standard_text_hash_equals_clean_text_hash": standard.get("standard_text_hash_equals_clean_text_hash") is True,
                "standard_open_blocking_zero": standard.get("open_blocking_review_outcomes") == 0,
            }
        )
    blockers = [name for name, ok in required.items() if not ok]
    status_counts = Counter(str(record.get("status") or "") for record in progress)
    verdict = "llm_fallback_ledger_pass" if not blockers else "llm_fallback_ledger_review"
    return {
        "schema": "luceon-clean-llm-fallback-ledger/v1",
        "policy": "audit_only_no_clean_status_mutation",
        "clean_dir": str(clean_dir),
        "standard_dir": str(standard_dir) if standard_dir else None,
        "verdict": verdict,
        "promotion_gate_candidate": verdict == "llm_fallback_ledger_pass",
        "summary": {
            "progress_record_count": len(progress),
            "status_counts": dict(status_counts),
            "fallback_record_count": len(fallback_records),
            "failed_count": status_counts.get("failed", 0),
            "reverted_structure_drift_count": status_counts.get("reverted_structure_drift", 0),
            "global_revert_count": len(global_reverts),
            "open_blocking_item_count": len(blockers),
        },
        "fallback_contract": {
            "failed_chunk_action": "cleaner appends the pre-LLM deterministic chunk when LLM call fails in non-required mode",
            "reverted_chunk_action": "cleaner discards LLM output and appends the pre-LLM deterministic chunk when protected teaching structure drifts",
            "global_revert_action": "cleaner returns source_md when H1/H2 segment count or signature changes",
            "contract_evidence": [
                "/Users/concm/.codex/skills/eduassets-raw-cleaner/SKILL.md",
                "/Users/concm/.codex/skills/eduassets-raw-cleaner/scripts/clean_raw_sample.py",
            ],
        },
        "closure_requirements": required,
        "blockers": blockers,
        "global_reverts": global_reverts,
        "items": ledger_items,
        "evidence_paths": {
            "llm_progress": str(clean_dir / "llm_progress.jsonl"),
            "llm_usage": str(clean_dir / "llm_usage.json"),
            "review_items": str(clean_dir / "review_items.json"),
            "structure_report": str(clean_dir / "structure_report.json"),
            "loss_audit": str(clean_dir / "loss_audit.json"),
            "render_report": str(clean_dir / "render_report.json"),
            "readability_report": str(clean_dir / "readability_report.json"),
        },
    }


def render_html(report: dict[str, Any]) -> str:
    rows = []
    for item in report["items"]:
        cls = "bad" if item["blockers"] else "ok"
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item['chunk_index']))}</td>"
            f"<td>{html.escape(str(item['title']))}</td>"
            f"<td>{html.escape(str(item['status']))}</td>"
            f"<td>{html.escape(str(item['fallback_action']))}</td>"
            f"<td class=\"{cls}\">{html.escape(', '.join(item['blockers']))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Clean LLM Fallback Ledger</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #202124; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border: 1px solid #d0d7de; padding: 6px; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.ok {{ color: #116329; }}
.bad {{ color: #a40e26; font-weight: 600; }}
pre {{ background: #f6f8fa; border: 1px solid #d0d7de; padding: 12px; overflow: auto; }}
</style>
</head>
<body>
<h1>Clean LLM Fallback Ledger</h1>
<p><strong>Verdict:</strong> {html.escape(report['verdict'])}</p>
<pre>{html.escape(json.dumps(report['summary'], ensure_ascii=False, indent=2))}</pre>
<h2>Closure Requirements</h2>
<pre>{html.escape(json.dumps(report['closure_requirements'], ensure_ascii=False, indent=2))}</pre>
<table>
<thead><tr><th>Chunk</th><th>Title</th><th>Status</th><th>Fallback</th><th>Blockers</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</body>
</html>
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-dir", required=True, type=Path)
    parser.add_argument("--standard-dir", type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_ledger(args.clean_dir, args.standard_dir)
    write_json(args.out_dir / "clean_llm_fallback_ledger.json", report)
    (args.out_dir / "clean_llm_fallback_ledger.html").write_text(render_html(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(args.out_dir / "clean_llm_fallback_ledger.json"),
                "html": str(args.out_dir / "clean_llm_fallback_ledger.html"),
                "verdict": report["verdict"],
                "summary": report["summary"],
                "blockers": report["blockers"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
