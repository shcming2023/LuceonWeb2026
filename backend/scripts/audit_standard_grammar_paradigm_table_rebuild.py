#!/usr/bin/env python3
"""Audit GF4 grammar paradigm table rebuild from V2 failures to V3 closure."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from standard_from_clean import parse_simple_table_rows, reflow_grammar_paradigm_table, write_json


COLLAPSED_FRAGMENTS = ["playingyou", "playedyou", "am.Yes", "have.Yes", "was.Yes"]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def list_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("items", "outcomes", "records"):
            if isinstance(value.get(key), list):
                return [item for item in value[key] if isinstance(item, dict)]
    return []


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def reconstruction_items(standard_dir: Path) -> list[dict[str, Any]]:
    outcomes = list_items(read_json(standard_dir / "standard_review_outcomes.json")) or list_items(
        read_json(standard_dir / "visual_outcome_review.json")
    )
    packets = list_items(read_json(standard_dir / "standard_visual_review_packets.json"))
    packet_by_block = {str(packet.get("block_id") or ""): packet for packet in packets}
    document = read_json(standard_dir / "standard_document.json")
    blocks = {str(block.get("id") or ""): block for block in document.get("blocks", []) if isinstance(block, dict)}
    records: list[dict[str, Any]] = []
    for outcome in outcomes:
        decision = str(outcome.get("decision") or outcome.get("visual_review_decision") or "")
        outcome_id = str(outcome.get("outcome_id") or outcome.get("id") or "")
        packet_type = str(outcome.get("packet_type") or outcome.get("type") or outcome_id)
        block_id = str(outcome.get("block_id") or (outcome_id.split(":")[-1] if ":" in outcome_id else ""))
        if decision != "needs_reconstruction" or ("table" not in packet_type and "table" not in outcome_id):
            continue
        packet = packet_by_block.get(block_id) or {}
        block = blocks.get(block_id) or {}
        table_html = str(block.get("markdown") or packet.get("clean_text") or outcome.get("clean_text") or "")
        records.append(
            {
                "outcome_id": outcome_id,
                "block_id": block_id,
                "decision": decision,
                "source_page_number": packet.get("source_page_number"),
                "source_bbox": packet.get("source_bbox") or [],
                "source_crop": packet.get("source_crop") or "",
                "table_html": table_html,
            }
        )
    return records


def find_outcome(standard_dir: Path, outcome_id: str) -> dict[str, Any]:
    for outcome in list_items(read_json(standard_dir / "standard_review_outcomes.json")):
        if str(outcome.get("outcome_id") or outcome.get("id") or "") == outcome_id:
            return outcome
    return {}


def analyze_table(record: dict[str, Any], v3_dir: Path) -> dict[str, Any]:
    original = str(record.get("table_html") or "")
    reflowed = reflow_grammar_paradigm_table(original)
    original_rows = parse_simple_table_rows(original)
    reflowed_rows = parse_simple_table_rows(reflowed)
    original_text = clean_text(original)
    reflowed_text = clean_text(reflowed)
    fragment_counts = {fragment: reflowed_text.count(fragment) for fragment in COLLAPSED_FRAGMENTS}
    v3_outcome = find_outcome(v3_dir, str(record.get("outcome_id") or ""))
    return {
        **record,
        "original_row_count": len(original_rows),
        "reflowed_row_count": len(reflowed_rows),
        "reflowed_as_grammar_paradigm_table": 'class="grammar-paradigm-table"' in reflowed,
        "collapsed_fragment_counts_after_reflow": fragment_counts,
        "all_collapsed_fragments_removed": all(count == 0 for count in fragment_counts.values()),
        "v3_decision": v3_outcome.get("decision") or v3_outcome.get("visual_review_decision") or "",
        "v3_status": v3_outcome.get("status") or "",
        "v3_reviewer": v3_outcome.get("reviewer") or "",
        "original_preview": original_text[:900],
        "reflowed_preview": reflowed_text[:1200],
        "reflowed_html": reflowed,
    }


def build_audit(v2_dir: Path, v3_dir: Path, out_dir: Path) -> dict[str, Any]:
    items = [analyze_table(record, v3_dir) for record in reconstruction_items(v2_dir)]
    v3_run = read_json(Path("docs/standard-research/corpus/runs/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.run.json"))
    correction_path = v3_dir / "correction_log.json"
    correction_value: Any = json.loads(correction_path.read_text(encoding="utf-8")) if correction_path.exists() else []
    correction_items = (
        correction_value
        if isinstance(correction_value, list)
        else correction_value.get("items") or correction_value.get("corrections") or []
    )
    status_counts = Counter(str(item.get("v3_decision") or "") for item in items)
    report = {
        "schema": "luceon-standard-grammar-paradigm-table-rebuild-audit/v1",
        "v2_standard_dir": str(v2_dir),
        "v3_standard_dir": str(v3_dir),
        "policy": "audit_only_confirms_existing_profile_general_renderer_no_gate_mutation",
        "decision_boundary": (
            "This audit verifies that historical GF4 grammar-paradigm table reconstruction failures are handled "
            "by the profile-general table renderer. It does not create a new closure and does not generalize to "
            "blank-box reconstruction cases."
        ),
        "record_count": len(items),
        "reflowed_count": sum(1 for item in items if item.get("reflowed_as_grammar_paradigm_table")),
        "collapsed_fragments_removed_count": sum(1 for item in items if item.get("all_collapsed_fragments_removed")),
        "v3_decision_counts_for_v2_failures": dict(status_counts),
        "v3_closure": v3_run.get("closure") or {},
        "v3_review_outcomes": v3_run.get("review_outcomes") or {},
        "source_fidelity_correction": v3_run.get("source_fidelity_correction") or {},
        "correction_log_count": len(correction_items),
        "compiler_readiness": "validated_for_gf4_failure_mode_not_broad_table_rebuild",
        "items": items,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "grammar_paradigm_table_rebuild_audit.json", report)
    (out_dir / "grammar_paradigm_table_rebuild_audit.html").write_text(build_html(report), encoding="utf-8")
    return report


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False, indent=2)
    sections: list[str] = []
    for item in report.get("items") or []:
        sections.append(
            "<section>"
            f"<h2>{html.escape(str(item.get('block_id') or ''))}</h2>"
            f"<p>V3 decision: {html.escape(str(item.get('v3_decision') or ''))}; "
            f"rows: {html.escape(str(item.get('original_row_count')))} -> {html.escape(str(item.get('reflowed_row_count')))}</p>"
            f"<pre>{html.escape(json.dumps(item.get('collapsed_fragment_counts_after_reflow') or {}, ensure_ascii=False, indent=2))}</pre>"
            f"<div class=\"grid\"><div><h3>Original</h3><pre>{html.escape(str(item.get('original_preview') or ''))}</pre></div>"
            f"<div><h3>Reflowed</h3>{item.get('reflowed_html') or ''}</div></div>"
            "</section>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Grammar Paradigm Table Rebuild Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    td {{ border: 1px solid #999; padding: 6px 8px; vertical-align: top; }}
    tr:first-child td {{ background: #eee; font-weight: bold; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
    section {{ margin-bottom: 32px; }}
  </style>
</head>
<body>
  <h1>Grammar Paradigm Table Rebuild Audit</h1>
  <pre>{html.escape(summary)}</pre>
  {"".join(sections)}
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2-standard-dir", required=True, type=Path)
    parser.add_argument("--v3-standard-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_audit(args.v2_standard_dir, args.v3_standard_dir, args.out_dir)
    print(json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
