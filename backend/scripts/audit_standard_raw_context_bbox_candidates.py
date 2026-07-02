#!/usr/bin/env python3
"""Audit Raw context-window bbox candidates for remaining formula/text blockers."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_standard_formula_bbox_candidates import enrich_raw_rows_with_assignments
from close_standard_review_outcomes import load_raw_content_rows, raw_row_text, standard_raw_dir
from standard_from_clean import write_json


RAW_CONTEXT_TYPES = {"text", "list", "equation", "chart"}
TARGET_ACTION = "raw_text_sequence_or_context_window_locator_required"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def normalize_context_text(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\\cdot", " times ").replace("\\times", " times ").replace("\\div", " div ")
    text = text.replace("\\pm", " plusminus ").replace("\\leq", " le ").replace("\\geq", " ge ")
    text = re.sub(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r" frac \1 over \2 ", text)
    text = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r" sqrt \1 ", text)
    text = re.sub(r"\\text\s*\{([^{}]+)\}", r" \1 ", text)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    text = re.sub(r"[$*_`{}()[\],.;:!?©®™|]+", " ", text)
    return re.sub(r"[^a-zA-Z0-9+\-*/=<>.%]+", " ", text).lower().strip()


def compact_key(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9+\-*/=<>.%]+", "", normalize_context_text(value))


def token_set(value: str) -> set[str]:
    return {token for token in normalize_context_text(value).split() if len(token) > 1}


def bbox_union(rows: list[dict[str, Any]]) -> list[float]:
    boxes = [row.get("bbox") for row in rows if isinstance(row.get("bbox"), list) and len(row.get("bbox")) == 4]
    if not boxes:
        return []
    return [min(float(b[0]) for b in boxes), min(float(b[1]) for b in boxes), max(float(b[2]) for b in boxes), max(float(b[3]) for b in boxes)]


def same_unit_rows(raw_rows: list[dict[str, Any]], heading_path: list[str]) -> list[dict[str, Any]]:
    headings = [str(item) for item in heading_path if item]
    if not headings:
        return []
    exact_titles = set(headings)
    rows = [
        row
        for row in raw_rows
        if row.get("type") in RAW_CONTEXT_TYPES
        and row.get("page_idx") is not None
        and row.get("bbox")
        and str(row.get("unit_title") or "") in exact_titles
    ]
    if rows:
        return rows
    topic = headings[0]
    return [
        row
        for row in raw_rows
        if row.get("type") in RAW_CONTEXT_TYPES
        and row.get("page_idx") is not None
        and row.get("bbox")
        and str(row.get("unit_title") or "") == topic
    ]


def score_window(clean_text: str, window_text: str) -> dict[str, Any]:
    clean_compact = compact_key(clean_text)
    window_compact = compact_key(window_text)
    sequence_ratio = SequenceMatcher(None, clean_compact, window_compact).ratio() if clean_compact or window_compact else 0.0
    clean_tokens = token_set(clean_text)
    window_tokens = token_set(window_text)
    token_overlap = len(clean_tokens & window_tokens) / len(clean_tokens) if clean_tokens else 0.0
    contains_compact = (
        len(clean_compact) >= 24
        and len(window_compact) >= 24
        and (clean_compact in window_compact or window_compact in clean_compact)
    )
    return {
        "sequence_ratio": round(sequence_ratio, 6),
        "token_overlap": round(token_overlap, 6),
        "contains_compact": contains_compact,
        "score": round(max(sequence_ratio, token_overlap), 6),
    }


def classify_candidate(best: dict[str, Any] | None, second: dict[str, Any] | None) -> str:
    if not best:
        return "no_context_candidate"
    score = float(best.get("score") or 0.0)
    sequence_ratio = float(best.get("sequence_ratio") or 0.0)
    token_overlap = float(best.get("token_overlap") or 0.0)
    margin = score - float(second.get("score") or 0.0) if second else score
    if sequence_ratio >= 0.98 and margin >= 0.03:
        return "context_window_candidate_high_confidence"
    if token_overlap >= 0.98 and sequence_ratio >= 0.8 and margin >= 0.03:
        return "context_window_candidate_high_confidence"
    if score >= 0.92 and margin >= 0.05:
        return "context_window_candidate_review"
    if score >= 0.82:
        return "context_window_candidate_weak"
    return "no_context_candidate"


def best_windows(clean_text: str, rows: list[dict[str, Any]], *, max_window: int = 6) -> list[dict[str, Any]]:
    by_page: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_page[int(row["page_idx"])].append(row)
    candidates: list[dict[str, Any]] = []
    for page_idx, page_rows in by_page.items():
        page_rows = sorted(page_rows, key=lambda row: int(row.get("_raw_index") or 0))
        for start in range(len(page_rows)):
            for size in range(1, max_window + 1):
                window = page_rows[start : start + size]
                if len(window) != size:
                    continue
                text = " ".join(raw_row_text(row) for row in window)
                if not text.strip():
                    continue
                scores = score_window(clean_text, text)
                candidates.append(
                    {
                        **scores,
                        "page_idx": page_idx,
                        "source_page_number": page_idx + 1,
                        "source_bbox": bbox_union(window),
                        "window_size": size,
                        "raw_indices": [row.get("_raw_index") for row in window],
                        "source_orders": [row.get("source_order") for row in window if row.get("source_order") is not None],
                        "source_unit_title": window[0].get("unit_title") or "",
                        "source_content_preview": text[:500],
                    }
                )
    candidates.sort(key=lambda item: (float(item.get("score") or 0), float(item.get("token_overlap") or 0), -int(item.get("window_size") or 0)), reverse=True)
    return candidates[:5]


def build_audit(standard_dir: Path) -> dict[str, Any]:
    remaining = read_json(standard_dir / "remaining_bbox_blocker_audit.json")
    raw_dir = standard_raw_dir(standard_dir)
    raw_rows, assignment_summary = enrich_raw_rows_with_assignments(load_raw_content_rows(raw_dir), raw_dir)
    items: list[dict[str, Any]] = []
    for item in remaining.get("items") or []:
        if item.get("recommended_action") != TARGET_ACTION:
            continue
        clean_text = str(item.get("clean_text_preview") or "")
        rows = same_unit_rows(raw_rows, item.get("heading_path") or [])
        candidates = best_windows(clean_text, rows)
        best = candidates[0] if candidates else None
        second = candidates[1] if len(candidates) > 1 else None
        bucket = classify_candidate(best, second)
        items.append(
            {
                "outcome_id": item.get("outcome_id"),
                "block_id": item.get("block_id"),
                "heading_path": item.get("heading_path") or [],
                "text_shape": item.get("text_shape") or [],
                "source_row_scope_count": len(rows),
                "bucket": bucket,
                "best_candidate": best or {},
                "second_candidate": second or {},
                "candidate_count": len(candidates),
                "clean_text_preview": clean_text[:500],
            }
        )
    bucket_counts = Counter(str(item.get("bucket") or "") for item in items)
    return {
        "schema": "luceon-standard-raw-context-bbox-candidate-audit/v1",
        "standard_dir": str(standard_dir),
        "policy": "audit_only_context_window_candidates_do_not_backfill_or_close",
        "raw_dir": str(raw_dir) if raw_dir else "",
        "raw_assignment_summary": assignment_summary,
        "count": len(items),
        "bucket_counts": dict(bucket_counts),
        "target_action": TARGET_ACTION,
        "items": items,
    }


def build_html(audit: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in audit.items() if k != "items"}, ensure_ascii=False, indent=2)
    rows = []
    for item in audit.get("items", [])[:500]:
        rows.append(
            "<article>"
            f"<h2>{html.escape(str(item.get('outcome_id') or ''))}</h2>"
            f"<p><strong>Bucket:</strong> {html.escape(str(item.get('bucket') or ''))} | "
            f"<strong>Rows:</strong> {html.escape(str(item.get('source_row_scope_count') or 0))}</p>"
            f"<p><strong>Heading:</strong> {html.escape(' > '.join(item.get('heading_path') or []))}</p>"
            "<div class=\"pair\">"
            f"<pre>{html.escape(str(item.get('clean_text_preview') or ''))}</pre>"
            f"<pre>{html.escape(json.dumps(item.get('best_candidate') or {}, ensure_ascii=False, indent=2))}</pre>"
            "</div>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Raw Context Bbox Candidate Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    article {{ border-top: 1px solid #ddd; padding: 16px 0; }}
    .pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    pre {{ white-space: pre-wrap; background: #f6f6f6; padding: 10px; overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <h1>Raw Context Bbox Candidate Audit</h1>
  <pre>{html.escape(summary)}</pre>
  {''.join(rows)}
</body>
</html>
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    audit = build_audit(args.standard_dir)
    write_json(args.standard_dir / "raw_context_bbox_candidate_audit.json", audit)
    (args.standard_dir / "raw_context_bbox_candidate_audit.html").write_text(build_html(audit), encoding="utf-8")
    print(json.dumps({k: v for k, v in audit.items() if k != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
