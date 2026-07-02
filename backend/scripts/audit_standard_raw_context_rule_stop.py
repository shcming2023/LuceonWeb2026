#!/usr/bin/env python3
"""Classify remaining Raw context candidates where rule expansion should stop."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def normalize_words(value: str) -> list[str]:
    text = html.unescape(value or "").lower()
    text = re.sub(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r" \1 \2 ", text)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return [token for token in text.split() if token]


def has_different_numbers(clean_text: str, source_text: str) -> bool:
    clean_nums = re.findall(r"\d+(?:\.\d+)?", clean_text or "")
    source_nums = re.findall(r"\d+(?:\.\d+)?", source_text or "")
    return bool(clean_nums and source_nums and clean_nums != source_nums)


def classify_item(item: dict[str, Any]) -> tuple[str, str]:
    bucket = str(item.get("bucket") or "")
    clean_text = str(item.get("clean_text_preview") or "")
    best = item.get("best_candidate") if isinstance(item.get("best_candidate"), dict) else {}
    source_text = str(best.get("source_content_preview") or "")
    sequence_ratio = float(best.get("sequence_ratio") or 0.0)
    token_overlap = float(best.get("token_overlap") or 0.0)
    score = float(best.get("score") or 0.0)
    text_shape = item.get("text_shape") if isinstance(item.get("text_shape"), list) else []

    if bucket == "no_context_candidate":
        if score >= 0.75 and has_different_numbers(clean_text, source_text):
            return "no_candidate_near_mismatch_different_numbers", "near text exists but numeric content differs"
        return "no_candidate_requires_manual_or_source_reconstruction", "no deterministic same-unit context-window candidate"

    if bucket == "context_window_candidate_review":
        return "review_candidate_token_overlap_only", "token overlap is high but sequence/location evidence is insufficient"

    if bucket == "context_window_candidate_weak":
        if sequence_ratio >= 0.98 and 0 < token_overlap < 0.98:
            return "weak_formula_spacing_or_tokenization_review", "compact sequence is high but token overlap is partial"
        if sequence_ratio >= 0.95 and has_different_numbers(clean_text, source_text):
            return "weak_false_positive_different_numbers", "similar wording but formula/numeric content differs"
        if sequence_ratio >= 0.95:
            return "weak_near_text_ocr_or_minor_text_review", "near text exists but exact deterministic rule is absent"
        if has_different_numbers(clean_text, source_text):
            return "weak_false_positive_different_numbers", "similar wording but formula/numeric content differs"
        if "short_formula" in text_shape:
            return "weak_short_formula_not_safe", "short formula lacks enough context for automatic source selection"
        return "weak_false_positive_or_context_gap", "weak match is insufficient for automatic source-location evidence"

    return "unclassified", "unexpected raw context bucket"


def build_audit(standard_dir: Path) -> dict[str, Any]:
    raw_context = read_json(standard_dir / "raw_context_bbox_candidate_audit.json")
    items: list[dict[str, Any]] = []
    for item in raw_context.get("items") or []:
        bucket = str(item.get("bucket") or "")
        if bucket not in {"context_window_candidate_review", "context_window_candidate_weak", "no_context_candidate"}:
            continue
        stop_bucket, reason = classify_item(item)
        best = item.get("best_candidate") if isinstance(item.get("best_candidate"), dict) else {}
        items.append(
            {
                "outcome_id": item.get("outcome_id"),
                "block_id": item.get("block_id"),
                "raw_context_bucket": bucket,
                "stop_bucket": stop_bucket,
                "reason": reason,
                "text_shape": item.get("text_shape") or [],
                "heading_path": item.get("heading_path") or [],
                "score": best.get("score"),
                "sequence_ratio": best.get("sequence_ratio"),
                "token_overlap": best.get("token_overlap"),
                "source_page_number": best.get("source_page_number"),
                "clean_text_preview": str(item.get("clean_text_preview") or "")[:500],
                "source_content_preview": str(best.get("source_content_preview") or "")[:500],
            }
        )
    bucket_counts = Counter(str(item.get("stop_bucket") or "") for item in items)
    raw_bucket_counts = Counter(str(item.get("raw_context_bucket") or "") for item in items)
    return {
        "schema": "luceon-standard-raw-context-rule-stop-audit/v1",
        "standard_dir": str(standard_dir),
        "policy": "audit_only_no_backfill_no_closure_stop_rule_expansion_for_weak_or_missing_context",
        "decision_boundary": (
            "Remaining weak/no-candidate Raw context items must not be closed or backfilled by lowering "
            "similarity thresholds. Only new deterministic rules with exact source evidence may move items "
            "out of this audit."
        ),
        "count": len(items),
        "raw_context_bucket_counts": dict(raw_bucket_counts),
        "stop_bucket_counts": dict(bucket_counts),
        "items": items,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "items"}, ensure_ascii=False, indent=2)
    rows = []
    for item in report.get("items") or []:
        rows.append(
            "<article>"
            f"<h2>{html.escape(str(item.get('block_id') or item.get('outcome_id') or ''))}</h2>"
            f"<p><strong>{html.escape(str(item.get('stop_bucket') or ''))}</strong> - "
            f"{html.escape(str(item.get('reason') or ''))}</p>"
            f"<p>{html.escape(' > '.join(item.get('heading_path') or []))}</p>"
            "<div class=\"pair\">"
            f"<pre>{html.escape(str(item.get('clean_text_preview') or ''))}</pre>"
            f"<pre>{html.escape(str(item.get('source_content_preview') or ''))}</pre>"
            "</div>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Raw Context Rule Stop Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    article {{ border-top: 1px solid #ddd; padding: 16px 0; }}
    .pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    pre {{ white-space: pre-wrap; background: #f6f6f6; padding: 10px; overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <h1>Raw Context Rule Stop Audit</h1>
  <pre>{html.escape(summary)}</pre>
  {''.join(rows)}
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
    write_json(args.standard_dir / "raw_context_rule_stop_audit.json", report)
    (args.standard_dir / "raw_context_rule_stop_audit.html").write_text(build_html(report), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
