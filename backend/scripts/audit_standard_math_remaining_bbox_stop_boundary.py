#!/usr/bin/env python3
"""Classify remaining Math formula bbox gaps after assignment locator passes."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from audit_standard_math_formula_bbox_from_assignments import normalize_formula_text
from standard_from_clean import write_json


REMAINING_STATUSES = {
    "ambiguous_exact",
    "ambiguous_containment",
    "unlocated_no_assignment_match",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def classify_text(text: str, normalized_text: str) -> str:
    stripped = str(text or "").strip()
    if re.match(r"^\([A-DＡ-Ｄ]\)", stripped):
        return "option_choice"
    if re.match(r"^\(\d+\)", stripped):
        return "numbered_subitem"
    if re.match(r"^\d+[.．]", stripped):
        return "numbered_question"
    if len(normalized_text or "") < 12:
        return "short_normalized_text"
    if "$" in stripped and len(stripped) < 40:
        return "short_formula_fragment"
    return "long_or_mixed_formula_text"


def build_content_rows(content_list_path: Path) -> list[dict[str, Any]]:
    data = read_json(content_list_path)
    if isinstance(data, dict):
        items = data.get("content_list") or data.get("items") or []
    else:
        items = data if isinstance(data, list) else []
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        text = item.get("text") or item.get("table_body") or item.get("latex") or ""
        bbox = item.get("bbox") or []
        if not text or len(bbox) != 4:
            continue
        rows.append(
            {
                "index": index,
                "type": item.get("type"),
                "page_idx": item.get("page_idx"),
                "page_number": int(item.get("page_idx") or 0) + 1,
                "bbox": bbox,
                "text": text,
                "normalized_text": normalize_formula_text(text),
            }
        )
    return rows


def content_list_status(key: str, rows: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    if not key:
        return "content_unlocated_empty_key", []
    exact = [row for row in rows if row.get("normalized_text") == key]
    if len(exact) == 1:
        return "content_located_exact", exact
    if len(exact) > 1:
        return "content_ambiguous_exact", exact[:5]
    containing = [
        row
        for row in rows
        if (key in row.get("normalized_text", "") or row.get("normalized_text", "") in key)
        and len(row.get("normalized_text", "")) >= 8
    ]
    if len(containing) == 1:
        return "content_located_containment", containing
    if len(containing) > 1:
        pages = {row.get("page_idx") for row in containing}
        if len(pages) == 1:
            return "content_same_page_multi", containing[:8]
        return "content_ambiguous_containment", containing[:5]
    return "content_unlocated", []


def build_audit(assignment_audit_path: Path, content_list_path: Path) -> dict[str, Any]:
    assignment_audit = read_json(assignment_audit_path)
    records = [
        record
        for record in assignment_audit.get("records") or []
        if record.get("status") in REMAINING_STATUSES
    ]
    content_rows = build_content_rows(content_list_path)
    output_records: list[dict[str, Any]] = []
    for record in records:
        normalized_text = str(record.get("normalized_clean_text") or "")
        content_status, candidates = content_list_status(normalized_text, content_rows)
        pattern = classify_text(str(record.get("clean_text") or ""), normalized_text)
        output_records.append(
            {
                "block_id": record.get("block_id"),
                "assignment_status": record.get("status"),
                "pattern": pattern,
                "content_list_status": content_status,
                "heading_path": record.get("heading_path") or [],
                "clean_text": record.get("clean_text") or "",
                "normalized_length": len(normalized_text),
                "assignment_candidate_count": record.get("candidate_count") or 0,
                "content_list_candidates": [
                    {
                        "page_number": candidate.get("page_number"),
                        "bbox": candidate.get("bbox") or [],
                        "type": candidate.get("type"),
                        "text_preview": str(candidate.get("text") or "")[:240],
                    }
                    for candidate in candidates
                ],
            }
        )

    assignment_counts = Counter(record["assignment_status"] for record in output_records)
    pattern_counts = Counter(record["pattern"] for record in output_records)
    content_counts = Counter(record["content_list_status"] for record in output_records)
    fallback_located_count = sum(
        count
        for status, count in content_counts.items()
        if status.startswith("content_located_") or status == "content_same_page_multi"
    )
    return {
        "schema": "luceon-standard-math-remaining-bbox-stop-boundary/v1",
        "assignment_audit": str(assignment_audit_path),
        "content_list": str(content_list_path),
        "policy": "stop_boundary_audit_only_no_standard_mutation_no_outcome_closure",
        "decision_boundary": (
            "Remaining assignment-unlocated or ambiguous formula packets are classified after exact and containment "
            "source-location passes. Content-list fallback is audited but not applied."
        ),
        "remaining_count": len(output_records),
        "assignment_status_counts": dict(assignment_counts),
        "pattern_counts": dict(pattern_counts),
        "content_list_status_counts": dict(content_counts),
        "content_list_fallback_located_count": fallback_located_count,
        "gate_implications": {
            "can_close_formula_outcomes": False,
            "can_promote_math_textbook_profile": False,
            "recommended_boundary": (
                "Keep ambiguous and content-list-unlocated records in review; do not lower thresholds or use "
                "short option/formula fragments as bbox evidence without stronger page/line context."
            ),
        },
        "records": output_records,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2)
    rows = []
    for record in report.get("records") or []:
        candidates = "<br>".join(
            html.escape(
                f"p{item.get('page_number')} {item.get('bbox')} {str(item.get('text_preview') or '')[:160]}"
            )
            for item in record.get("content_list_candidates") or []
        )
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(record.get('assignment_status') or ''))}</td>"
            f"<td>{html.escape(str(record.get('content_list_status') or ''))}</td>"
            f"<td>{html.escape(str(record.get('pattern') or ''))}</td>"
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
  <title>Math Remaining BBox Stop Boundary</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Math Remaining BBox Stop Boundary</h1>
  <pre>{html.escape(summary)}</pre>
  <table>
    <thead>
      <tr><th>Assignment</th><th>Content List</th><th>Pattern</th><th>Block</th><th>Heading</th><th>Clean Text</th><th>Content Candidates</th></tr>
    </thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assignment-audit", required=True, type=Path)
    parser.add_argument("--content-list", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_audit(args.assignment_audit, args.content_list)
    write_json(args.out_dir / "math_remaining_bbox_stop_boundary_audit.json", report)
    (args.out_dir / "math_remaining_bbox_stop_boundary_audit.html").write_text(
        build_html(report), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
