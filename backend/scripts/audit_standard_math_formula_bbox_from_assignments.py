#!/usr/bin/env python3
"""Audit Math formula source bbox candidates from Raw block assignments."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


PUNCT_TRANS = str.maketrans(
    {
        "（": "(",
        "）": ")",
        "；": ";",
        "，": ",",
        "。": ".",
        "、": ",",
        "：": ":",
        "－": "-",
        "—": "-",
        "＝": "=",
        "±": r"\pm",
    }
)


def normalize_formula_text(text: str) -> str:
    value = str(text or "").translate(PUNCT_TRANS).lower()
    value = value.replace(r"\_", "_")
    value = re.sub(r"\\hspace\{[^}]*\}", "____", value)
    value = re.sub(r"\\underline\{[^}]*\}", "____", value)
    value = re.sub(r"\s+", "", value)
    value = value.replace("$$", "$")
    value = value.replace("\\left", "").replace("\\right", "")
    value = value.replace("\\,", "").replace("\\;", "")
    value = value.replace(" ", "")
    return value


def candidate_status(key: str, rows: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]], str]:
    if not key:
        return "unlocated_empty_key", [], "empty normalized clean text"
    exact = [row for row in rows if row.get("normalized_text") == key]
    if len(exact) == 1:
        return "located_exact", exact, "unique normalized exact match"
    if len(exact) > 1:
        return "ambiguous_exact", exact[:5], f"{len(exact)} exact matches"

    containing = [row for row in rows if key in row.get("normalized_text", "") or row.get("normalized_text", "") in key]
    containing = [row for row in containing if len(row.get("normalized_text", "")) >= 8]
    if len(containing) == 1:
        return "located_containment", containing, "unique normalized containment match"
    if len(containing) > 1:
        by_page: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in containing:
            by_page[int(row.get("page_idx") or -1)].append(row)
        if len(by_page) == 1:
            merged = merge_page_rows(containing)
            return "located_same_page_cluster", [merged], f"{len(containing)} matches on one source page merged as review bbox"
        return "ambiguous_containment", containing[:5], f"{len(containing)} containment matches across pages"

    return "unlocated_no_assignment_match", [], "no assignment exact or containment match"


def merge_page_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    page_idx = int(rows[0].get("page_idx") or 0)
    x0 = min(float((row.get("bbox") or [0, 0, 0, 0])[0]) for row in rows)
    y0 = min(float((row.get("bbox") or [0, 0, 0, 0])[1]) for row in rows)
    x1 = max(float((row.get("bbox") or [0, 0, 0, 0])[2]) for row in rows)
    y1 = max(float((row.get("bbox") or [0, 0, 0, 0])[3]) for row in rows)
    return {
        "block_ref": ",".join(str(row.get("block_ref") or "") for row in rows[:8]),
        "page_idx": page_idx,
        "bbox": [x0, y0, x1, y1],
        "text_preview": "\n".join(str(row.get("text_preview") or "") for row in rows[:8]),
        "formula_signal": any(bool(row.get("formula_signal")) for row in rows),
        "source_order": min(int(row.get("source_order") or 0) for row in rows),
        "merged_assignment_count": len(rows),
    }


def build_assignment_rows(raw_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for row in read_jsonl(raw_dir / "raw_block_assignments.jsonl"):
        text = str(row.get("text_preview") or "")
        bbox = row.get("bbox") or []
        if not text or len(bbox) != 4:
            continue
        item = dict(row)
        item["normalized_text"] = normalize_formula_text(text)
        rows.append(item)
    return rows


def build_audit(standard_dir: Path, raw_dir: Path) -> dict[str, Any]:
    packets = read_json(standard_dir / "standard_visual_review_packets.json").get("items") or []
    rows = build_assignment_rows(raw_dir)
    missing_packets = [
        packet
        for packet in packets
        if packet.get("type") == "formula_visual_review"
        and not (packet.get("source_page_number") and packet.get("source_bbox"))
    ]
    records: list[dict[str, Any]] = []
    for packet in missing_packets:
        clean_text = str(packet.get("clean_text") or "")
        key = normalize_formula_text(clean_text)
        status, matches, reason = candidate_status(key, rows)
        match_records = []
        for match in matches:
            page_idx = int(match.get("page_idx") or 0)
            match_records.append(
                {
                    "block_ref": match.get("block_ref") or "",
                    "page_idx": page_idx,
                    "page_number": page_idx + 1,
                    "bbox": match.get("bbox") or [],
                    "text_preview": match.get("text_preview") or "",
                    "formula_signal": bool(match.get("formula_signal")),
                    "source_order": match.get("source_order"),
                    "merged_assignment_count": match.get("merged_assignment_count"),
                }
            )
        records.append(
            {
                "block_id": packet.get("block_id"),
                "clean_lines": packet.get("clean_lines") or [],
                "heading_path": packet.get("heading_path") or [],
                "clean_text": clean_text,
                "normalized_clean_text": key,
                "status": status,
                "reason": reason,
                "candidate_count": len(matches),
                "candidates": match_records,
            }
        )

    status_counts = Counter(record["status"] for record in records)
    located_count = sum(count for status, count in status_counts.items() if status.startswith("located_"))
    ambiguous_count = sum(count for status, count in status_counts.items() if status.startswith("ambiguous_"))
    unlocated_count = sum(count for status, count in status_counts.items() if status.startswith("unlocated_"))
    return {
        "schema": "luceon-standard-math-formula-assignment-bbox-audit/v1",
        "standard_dir": str(standard_dir),
        "raw_dir": str(raw_dir),
        "policy": "raw_assignment_bbox_candidates_are_source_location_evidence_not_visual_acceptance",
        "decision_boundary": (
            "This audit proposes source page/bbox candidates for missing formula visual review packets using "
            "raw_block_assignments.jsonl. It does not mutate Standard artifacts, generate crops, or close outcomes."
        ),
        "missing_formula_packet_count": len(records),
        "assignment_row_count": len(rows),
        "status_counts": dict(status_counts),
        "located_candidate_count": located_count,
        "ambiguous_candidate_count": ambiguous_count,
        "unlocated_candidate_count": unlocated_count,
        "gate_implications": {
            "can_close_formula_outcomes": False,
            "can_promote_math_textbook_profile": False,
            "next_action": "review_located_candidates_before_optional_apply_and_crop_generation",
        },
        "records": records,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2)
    rows = []
    for record in report.get("records") or []:
        candidates = "<br>".join(
            html.escape(
                f"p{item.get('page_number')} {item.get('bbox')} {str(item.get('text_preview') or '')[:180]}"
            )
            for item in record.get("candidates") or []
        )
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(record.get('status') or ''))}</td>"
            f"<td>{html.escape(str(record.get('block_id') or ''))}</td>"
            f"<td>{html.escape(' > '.join(str(x) for x in record.get('heading_path') or []))}</td>"
            f"<td>{html.escape(str(record.get('clean_text') or '')[:260])}</td>"
            f"<td>{candidates}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Math Formula Assignment BBox Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Math Formula Assignment BBox Audit</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead><tr><th>Status</th><th>Block</th><th>Heading</th><th>Clean Text</th><th>Candidates</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_audit(args.standard_dir, args.raw_dir)
    write_json(args.out_dir / "math_formula_assignment_bbox_audit.json", report)
    (args.out_dir / "math_formula_assignment_bbox_audit.html").write_text(build_html(report), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
