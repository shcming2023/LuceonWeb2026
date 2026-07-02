#!/usr/bin/env python3
"""Audit blank-box reconstruction patterns across Standard workbook samples."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from prototype_standard_paired_vocabulary_blank_reconstruction import reconstruct_cell
from standard_from_clean import write_json


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


def table_cells(table_html: str) -> list[str]:
    return [clean_text(re.sub(r"<[^>]+>", " ", match.group(1))) for match in re.finditer(r"<td>(.*?)</td>", table_html or "", re.I | re.S)]


def extract_table_reconstruction_items(sample_id: str, standard_dir: Path) -> list[dict[str, Any]]:
    outcomes = list_items(read_json(standard_dir / "standard_review_outcomes.json")) or list_items(
        read_json(standard_dir / "visual_outcome_review.json")
    )
    packets = list_items(read_json(standard_dir / "standard_visual_review_packets.json"))
    packet_by_block = {str(packet.get("block_id") or ""): packet for packet in packets}
    document = read_json(standard_dir / "standard_document.json")
    blocks = {
        str(block.get("id") or ""): block
        for block in document.get("blocks", [])
        if isinstance(block, dict)
    }
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
        table_text = str(block.get("markdown") or packet.get("clean_text") or outcome.get("clean_text") or "")
        records.append(
            {
                "sample_id": sample_id,
                "source": "standard_review_outcomes",
                "standard_dir": str(standard_dir),
                "outcome_id": outcome_id,
                "block_id": block_id,
                "packet_type": packet_type,
                "source_page_number": packet.get("source_page_number"),
                "source_bbox": packet.get("source_bbox") or [],
                "source_crop": packet.get("source_crop") or "",
                "table_text": table_text,
            }
        )
    return records


def extract_paired_blank_audit_items(sample_id: str, audit_path: Path) -> list[dict[str, Any]]:
    audit = read_json(audit_path)
    records: list[dict[str, Any]] = []
    for record in audit.get("records") or []:
        if not record.get("known_content_reconstruction_blocker"):
            continue
        records.append(
            {
                "sample_id": sample_id,
                "source": "paired_vocabulary_blank_box_reconstruction_audit",
                "standard_dir": audit.get("standard_dir") or "",
                "outcome_id": "",
                "block_id": record.get("block_id") or "",
                "packet_type": "table_visual_review",
                "source_page_number": record.get("source_page_number"),
                "source_bbox": record.get("current_table_source_bbox") or [],
                "source_crop": record.get("source_context_crop") or record.get("existing_table_source_crop") or "",
                "table_text": record.get("standard_table_text") or "",
            }
        )
    return records


def classify_record(record: dict[str, Any]) -> dict[str, Any]:
    cells = table_cells(str(record.get("table_text") or ""))
    rule_hits: list[dict[str, Any]] = []
    for cell in cells:
        reconstructed, rules = reconstruct_cell(cell)
        if rules:
            rule_hits.append({"original": cell, "reconstructed": reconstructed, "rules": rules})
    header = [cell.lower() for cell in cells[:5]]
    if rule_hits:
        verdict = "blank_pattern_reconstructable"
    elif {"affirmative", "negative", "questions"}.issubset(set(header)):
        verdict = "non_blank_grammar_paradigm_table_reconstruction"
    else:
        verdict = "manual_reconstruction_review"
    return {
        **record,
        "unique_key": f"{record.get('sample_id')}:{record.get('block_id')}:{clean_text(str(record.get('table_text') or ''))[:120]}",
        "cell_count": len(cells),
        "blank_pattern_hit_count": sum(len(hit["rules"]) for hit in rule_hits),
        "blank_pattern_cell_count": len(rule_hits),
        "blank_pattern_hits": rule_hits,
        "verdict": verdict,
    }


def build_audit(samples: list[str], paired_blank_audits: list[str], output_dir: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for spec in samples:
        sample_id, standard_dir = spec.split("=", 1)
        records.extend(extract_table_reconstruction_items(sample_id, Path(standard_dir)))
    for spec in paired_blank_audits:
        sample_id, audit_path = spec.split("=", 1)
        records.extend(extract_paired_blank_audit_items(sample_id, Path(audit_path)))
    classified = [classify_record(record) for record in records]
    verdict_counts = Counter(str(record.get("verdict") or "") for record in classified)
    sample_counts = Counter(str(record.get("sample_id") or "") for record in classified)
    unique_by_text: dict[str, dict[str, Any]] = {}
    for record in classified:
        key = f"{record.get('block_id')}:{clean_text(str(record.get('table_text') or ''))[:180]}"
        unique_by_text.setdefault(key, record)
    unique_verdict_counts = Counter(str(record.get("verdict") or "") for record in unique_by_text.values())
    report = {
        "schema": "luceon-standard-blank-reconstruction-pattern-cross-sample-audit/v1",
        "policy": "audit_only_no_compiler_mutation_no_gate_closure",
        "decision_boundary": (
            "This audit tests whether the paired-vocabulary blank-box reconstruction patterns generalize across "
            "workbook reconstruction cases. A positive match here is only a candidate rule surface; non-blank "
            "reconstruction cases must stay on separate layout/table-rebuild tracks."
        ),
        "sample_specs": samples,
        "paired_blank_audit_specs": paired_blank_audits,
        "record_count": len(classified),
        "unique_reconstruction_case_count": len(unique_by_text),
        "verdict_counts": dict(verdict_counts),
        "unique_verdict_counts": dict(unique_verdict_counts),
        "sample_counts": dict(sample_counts),
        "compiler_readiness": (
            "not_ready_blank_rules_apply_only_to_g7plus_paired_vocabulary_blockers"
            if verdict_counts.get("blank_pattern_reconstructable", 0) and verdict_counts.get("non_blank_grammar_paradigm_table_reconstruction", 0)
            else "not_ready_needs_more_evidence"
        ),
        "items": classified,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "blank_reconstruction_cross_sample_audit.json", report)
    (output_dir / "blank_reconstruction_cross_sample_audit.html").write_text(build_html(report), encoding="utf-8")
    return report


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False, indent=2)
    rows: list[str] = []
    for item in report.get("items") or []:
        hits = html.escape(json.dumps(item.get("blank_pattern_hits") or [], ensure_ascii=False, indent=2))
        text = html.escape(clean_text(str(item.get("table_text") or ""))[:900])
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('sample_id') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(item.get('source') or ''))}</td>"
            f"<td>{html.escape(str(item.get('verdict') or ''))}</td>"
            f"<td>{html.escape(str(item.get('blank_pattern_hit_count') or 0))}</td>"
            f"<td><pre>{hits}</pre></td>"
            f"<td><pre>{text}</pre></td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Blank Reconstruction Cross-Sample Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Blank Reconstruction Cross-Sample Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Sample</th><th>Block</th><th>Source</th><th>Verdict</th><th>Blank Hits</th><th>Rules</th><th>Table Text</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", action="append", default=[], help="sample_id=/path/to/standard-final")
    parser.add_argument("--paired-blank-audit", action="append", default=[], help="sample_id=/path/to/audit.json")
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_audit(args.sample, args.paired_blank_audit, args.out_dir)
    print(json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
