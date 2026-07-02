#!/usr/bin/env python3
"""Audit formula review outcomes that still need source page/bbox evidence."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from close_standard_review_outcomes import load_raw_content_rows, raw_row_text, standard_raw_dir
from standard_from_clean import write_json


FORMULA_PACKET_TYPE = "formula_visual_review"
RAW_FORMULA_LOCATION_TYPES = {"equation", "text", "list", "chart"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def outcome_id_for_packet(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


def strip_markdown_image(value: str) -> str:
    return re.sub(r"!\[[^\]]*\]\([^)]+\)", "", value)


def math_location_key(value: str) -> str:
    text = html.unescape(value or "")
    text = strip_markdown_image(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\$\$?", " ", text)
    text = re.sub(r"\\stackrel\s*\{\s*\?\s*\}\s*\{\s*=\s*\}", " question_equals ", text)
    command_tokens = {
        r"\\geq\b|\\ge\b": " ge ",
        r"\\leq\b|\\le\b": " le ",
        r"\\neq\b|\\ne\b": " ne ",
        r"\\approx\b": " approx ",
        r"\\sim\b": " sim ",
        r"\\times\b": " times ",
        r"\\cdot\b": " cdot ",
        r"\\div\b": " div ",
        r"\\pm\b": " pm ",
        r"\\mp\b": " mp ",
        r"\\pi\b": " pi ",
        r"\\sqrt\b": " sqrt ",
    }
    for pattern, replacement in command_tokens.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"\\begin\{[^}]+\}|\\end\{[^}]+\}", " ", text)
    text = text.replace("\\left", " ").replace("\\right", " ")
    text = text.replace("\\quad", " ").replace("\\,", " ")
    text = re.sub(r"\\boxed\s*\{\s*\}", " boxedblank ", text)
    text = re.sub(r"\\boxed\s*\{\\quad\}", " boxedblank ", text)
    text = re.sub(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r" frac \1 over \2 ", text)
    text = re.sub(r"\\sqrt\s*\[([^{}]+)\]\s*\{([^{}]+)\}", r" sqrtroot \1 \2 ", text)
    text = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r" sqrt \1 ", text)
    text = re.sub(r"\\text\s*\{([^{}]+)\}", r" \1 ", text)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    return re.sub(r"[^a-zA-Z0-9+\-*/=<>.%]+", "", text).lower()


def display_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def is_formula_like_packet(packet: dict[str, Any]) -> bool:
    block_type = str(packet.get("block_type") or "")
    clean_text = str(packet.get("clean_text") or "")
    if block_type == "captioned_figure" and strip_markdown_image(clean_text).strip() == "":
        return False
    return bool(math_location_key(clean_text))


def build_raw_index(raw_rows: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_unit_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in raw_rows:
        if row.get("type") not in RAW_FORMULA_LOCATION_TYPES:
            continue
        if row.get("page_idx") is None or not row.get("bbox"):
            continue
        key = math_location_key(raw_row_text(row))
        if not key:
            continue
        copied = dict(row)
        copied["_math_location_key"] = key
        by_key[key].append(copied)
        unit_title = str(row.get("unit_title") or "")
        if unit_title:
            by_unit_key[f"{unit_title}\n{key}"].append(copied)
    return by_key, by_unit_key


def same_bbox(left: Any, right: Any) -> bool:
    if not isinstance(left, list) or not isinstance(right, list) or len(left) != 4 or len(right) != 4:
        return False
    return all(abs(float(a) - float(b)) <= 1.0 for a, b in zip(left, right))


def load_raw_assignments(raw_dir: Path | None) -> dict[int, dict[str, Any]]:
    if not raw_dir:
        return {}
    path = raw_dir / "raw_block_assignments.jsonl"
    if not path.exists():
        return {}
    by_source_order: dict[int, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            source_order = row.get("source_order")
            if isinstance(source_order, int):
                by_source_order[source_order] = row
    return by_source_order


def enrich_raw_rows_with_assignments(raw_rows: list[dict[str, Any]], raw_dir: Path | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    assignments = load_raw_assignments(raw_dir)
    enriched: list[dict[str, Any]] = []
    matched = 0
    mismatched = 0
    for row in raw_rows:
        copied = dict(row)
        raw_index = row.get("_raw_index")
        assignment = assignments.get(int(raw_index) + 1) if isinstance(raw_index, int) else None
        if assignment and assignment.get("type") == row.get("type") and assignment.get("page_idx") == row.get("page_idx") and same_bbox(assignment.get("bbox"), row.get("bbox")):
            matched += 1
            copied["source_order"] = assignment.get("source_order")
            copied["unit_id"] = assignment.get("unit_id") or ""
            copied["unit_title"] = assignment.get("unit_title") or ""
            copied["unit_order"] = assignment.get("unit_order")
            copied["assignment_method"] = assignment.get("assignment_method") or ""
        elif assignment:
            mismatched += 1
        enriched.append(copied)
    return enriched, {
        "raw_assignment_count": len(assignments),
        "raw_assignment_matched_count": matched,
        "raw_assignment_mismatched_count": mismatched,
        "source_order_policy": "content_list_index_plus_one_with_type_page_bbox_cross_check",
    }


def same_unit_matches(packet: dict[str, Any], key: str, by_unit_key: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    heading_path = packet.get("heading_path") if isinstance(packet.get("heading_path"), list) else []
    for heading in reversed(heading_path):
        matches = by_unit_key.get(f"{heading}\n{key}") or []
        if matches:
            return matches
    return []


def classify_packet(packet: dict[str, Any], outcome: dict[str, Any], by_key: dict[str, list[dict[str, Any]]], by_unit_key: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    clean_text = str(packet.get("clean_text") or "")
    key = math_location_key(clean_text)
    heading_path = packet.get("heading_path") if isinstance(packet.get("heading_path"), list) else []
    result: dict[str, Any] = {
        "outcome_id": outcome.get("outcome_id") or outcome_id_for_packet(packet),
        "block_id": packet.get("block_id") or outcome.get("block_id"),
        "packet_type": FORMULA_PACKET_TYPE,
        "decision": outcome.get("decision"),
        "next_action": outcome.get("next_action"),
        "heading_path": heading_path,
        "clean_text_preview": display_text(clean_text)[:500],
        "math_location_key": key[:240],
        "math_location_key_length": len(key),
    }
    if not is_formula_like_packet(packet):
        result.update({"bucket": "non_formula_image_alt_or_empty_after_normalization", "candidate_count": 0})
        return result
    if len(key) < 4:
        result.update({"bucket": "too_short_for_location_rule", "candidate_count": 0})
        return result

    unit_matches = same_unit_matches(packet, key, by_unit_key)
    all_matches = by_key.get(key) or []
    matches = unit_matches or all_matches
    result["candidate_count"] = len(matches)
    result["same_unit_candidate_count"] = len(unit_matches)
    result["global_candidate_count"] = len(all_matches)
    if not matches:
        result["bucket"] = "no_math_normalized_raw_match"
        return result
    if len(matches) == 1:
        match = matches[0]
        same_unit = bool(unit_matches)
        long_enough = len(key) >= 8
        result.update(
            {
                "bucket": (
                    "source_location_candidate_math_exact_unique_same_unit"
                    if same_unit
                    else "source_location_candidate_math_exact_unique_global"
                    if long_enough
                    else "ambiguous_short_global_match_needs_manual"
                ),
                "source_page_number": int(match["page_idx"]) + 1,
                "source_bbox": match.get("bbox") or [],
                "source_raw_type": match.get("type") or "",
                "source_unit_title": match.get("unit_title") or "",
                "source_raw_index": match.get("_raw_index"),
                "source_order": match.get("source_order"),
                "source_unit_id": match.get("unit_id") or "",
                "assignment_method": match.get("assignment_method") or "",
                "source_content_preview": display_text(raw_row_text(match))[:500],
            }
        )
        return result
    pages = sorted({int(match["page_idx"]) + 1 for match in matches if match.get("page_idx") is not None})
    result.update(
        {
            "bucket": "ambiguous_math_normalized_match",
            "candidate_pages": pages[:20],
            "source_units": sorted({str(match.get("unit_title") or "") for match in matches})[:20],
            "source_content_preview": display_text(raw_row_text(matches[0]))[:500],
        }
    )
    return result


def build_audit(standard_dir: Path) -> dict[str, Any]:
    packets = read_json(standard_dir / "standard_visual_review_packets.json").get("items") or []
    outcomes = read_json(standard_dir / "standard_review_outcomes.json").get("items") or []
    packets_by_id = {outcome_id_for_packet(packet): packet for packet in packets if isinstance(packet, dict)}
    raw_dir = standard_raw_dir(standard_dir)
    raw_rows, assignment_summary = enrich_raw_rows_with_assignments(load_raw_content_rows(raw_dir), raw_dir)
    by_key, by_unit_key = build_raw_index(raw_rows)
    items: list[dict[str, Any]] = []
    for outcome in outcomes:
        if not isinstance(outcome, dict):
            continue
        if outcome.get("packet_type") != FORMULA_PACKET_TYPE:
            continue
        if outcome.get("status") != "open" or not outcome.get("basic_print_blocking"):
            continue
        if outcome.get("decision") != "needs_page_bbox":
            continue
        packet = packets_by_id.get(str(outcome.get("outcome_id") or ""))
        if not packet:
            continue
        items.append(classify_packet(packet, outcome, by_key, by_unit_key))

    bucket_counts = Counter(str(item.get("bucket") or "") for item in items)
    return {
        "schema": "luceon-standard-formula-bbox-candidate-audit/v1",
        "standard_dir": str(standard_dir),
        "policy": "audit_only_math_normalized_location_candidates_do_not_close_outcomes",
        "raw_dir": str(raw_dir) if raw_dir else "",
        "raw_location_types": sorted(RAW_FORMULA_LOCATION_TYPES),
        "raw_assignment_summary": assignment_summary,
        "count": len(items),
        "bucket_counts": dict(bucket_counts),
        "candidate_count": sum(1 for item in items if str(item.get("bucket") or "").startswith("source_location_candidate")),
        "ambiguous_count": sum(1 for item in items if str(item.get("bucket") or "").startswith("ambiguous")),
        "no_match_count": int(bucket_counts.get("no_math_normalized_raw_match") or 0),
        "items": items,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = {key: value for key, value in report.items() if key != "items"}
    rows = []
    for item in report.get("items") or []:
        rows.append(
            "<article>"
            f"<h2>{html.escape(str(item.get('outcome_id') or ''))}</h2>"
            f"<p><strong>Bucket:</strong> {html.escape(str(item.get('bucket') or ''))} | "
            f"<strong>Page:</strong> {html.escape(str(item.get('source_page_number') or ''))} | "
            f"<strong>Candidates:</strong> {html.escape(str(item.get('candidate_count') or 0))}</p>"
            f"<p><strong>Heading:</strong> {html.escape(' > '.join(item.get('heading_path') or []))}</p>"
            "<div class=\"pair\">"
            f"<pre>{html.escape(str(item.get('clean_text_preview') or ''))}</pre>"
            f"<pre>{html.escape(str(item.get('source_content_preview') or ''))}</pre>"
            "</div>"
            f"<pre>{html.escape(json.dumps({k: item.get(k) for k in ['math_location_key', 'source_bbox', 'source_raw_type', 'source_unit_title', 'candidate_pages', 'source_units']}, ensure_ascii=False, indent=2))}</pre>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Formula Bbox Candidate Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    pre {{ white-space: pre-wrap; border: 1px solid #bbb; padding: 12px; }}
    article {{ break-inside: avoid; border-top: 1px solid #bbb; padding: 14px 0; }}
    .pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  </style>
</head>
<body>
  <h1>Formula Bbox Candidate Audit</h1>
  <pre>{html.escape(json.dumps(summary, ensure_ascii=False, indent=2))}</pre>
  {''.join(rows)}
</body>
</html>"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_audit(args.standard_dir)
    write_json(args.standard_dir / "formula_bbox_candidate_audit.json", report)
    (args.standard_dir / "formula_bbox_candidate_audit.html").write_text(build_html(report), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
