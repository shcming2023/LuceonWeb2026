#!/usr/bin/env python3
"""Audit raw-assignment exact formula semantic matches before closure."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


TARGET_BUCKET = "deterministic_formula_semantic_equivalent"
TARGET_SOURCE_RULE = "raw_assignment.located_exact"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def strip_markup(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("$", " ")
    return text


def compact_text(value: str) -> str:
    text = strip_markup(value)
    text = re.sub(r"(?<!\\)\*\*([^*\n]+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\\)__([^_\n]+?)__", r"\1", text)
    replacements = {
        "（": "(",
        "）": ")",
        "；": ";",
        "，": ",",
        "。": ".",
        "：": ":",
        "、": ",",
        "－": "-",
        "—": "-",
        "＝": "=",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", "", text).lower()


def punctuationless_text(value: str) -> str:
    text = compact_text(value)
    return re.sub(r"[^\w\\{}[\]^_+\-*/=<>.!?]+", "", text)


def has_digit_spacing_risk(source_text: str) -> bool:
    plain = strip_markup(source_text)
    return bool(re.search(r"(?<![a-zA-Z])\d(?:\s+\d){1,}(?![a-zA-Z])", plain))


def classify(item: dict[str, Any]) -> tuple[str, list[str]]:
    clean_text = str(item.get("clean_text_preview") or "")
    source_text = str(item.get("source_content_preview") or "")
    reasons: list[str] = []
    if has_digit_spacing_risk(source_text):
        reasons.append("source_has_digit_spacing")
    clean_compact = compact_text(clean_text)
    source_compact = compact_text(source_text)
    clean_punctless = punctuationless_text(clean_text)
    source_punctless = punctuationless_text(source_text)
    if clean_compact == source_compact:
        reasons.append("compact_text_equal")
    elif clean_punctless == source_punctless:
        reasons.append("punctuation_or_spacing_only")
    else:
        reasons.append("semantic_equal_but_surface_differs")

    stripped = clean_text.strip()
    if re.match(r"^\([A-DＡ-Ｄ]\)", stripped):
        reasons.append("short_option_choice")
    if len(str(item.get("clean_semantic_key_preview") or "")) < 30:
        reasons.append("short_semantic_key")
    if len(clean_text) > 180:
        reasons.append("long_mixed_text")

    if "source_has_digit_spacing" in reasons:
        return "digit_spacing_review", reasons
    if "semantic_equal_but_surface_differs" in reasons:
        return "surface_diff_review", reasons
    if "long_mixed_text" in reasons and "compact_text_equal" not in reasons:
        return "long_mixed_review", reasons
    if "short_option_choice" in reasons and ("compact_text_equal" in reasons or "punctuation_or_spacing_only" in reasons):
        return "short_option_surface_safe", reasons
    if "compact_text_equal" in reasons:
        return "compact_surface_safe", reasons
    if "punctuation_or_spacing_only" in reasons:
        return "punctuation_spacing_safe", reasons
    return "manual_review", reasons


def build_audit(standard_dir: Path) -> dict[str, Any]:
    formula_audit = read_json(standard_dir / "formula_source_mismatch_audit.json")
    records: list[dict[str, Any]] = []
    for item in formula_audit.get("items") or []:
        if item.get("bucket") != TARGET_BUCKET:
            continue
        if item.get("source_match_rule") != TARGET_SOURCE_RULE:
            continue
        risk_bucket, reasons = classify(item)
        records.append(
            {
                "outcome_id": item.get("outcome_id"),
                "block_id": item.get("block_id"),
                "risk_bucket": risk_bucket,
                "reasons": reasons,
                "source_page_number": item.get("source_page_number"),
                "source_bbox": item.get("source_bbox") or [],
                "source_crop": item.get("source_crop") or "",
                "source_crop_status": item.get("source_crop_status") or "",
                "semantic_key_similarity": item.get("semantic_key_similarity"),
                "clean_text_preview": item.get("clean_text_preview") or "",
                "source_content_preview": item.get("source_content_preview") or "",
                "clean_semantic_key_preview": item.get("clean_semantic_key_preview") or "",
                "source_semantic_key_preview": item.get("source_semantic_key_preview") or "",
            }
        )
    risk_counts = Counter(record["risk_bucket"] for record in records)
    closure_candidate_buckets = {
        "short_option_surface_safe",
        "compact_surface_safe",
        "punctuation_spacing_safe",
    }
    closure_candidate_count = sum(count for bucket, count in risk_counts.items() if bucket in closure_candidate_buckets)
    review_count = len(records) - closure_candidate_count
    return {
        "schema": "luceon-standard-math-raw-assignment-exact-closure-risk/v1",
        "standard_dir": str(standard_dir),
        "policy": "audit_only_no_outcome_closure",
        "decision_boundary": (
            "raw_assignment.located_exact formula semantic matches require surface-risk classification before any "
            "closure rule can be accepted. Digit-spacing and semantic-equal-but-surface-different records remain review."
        ),
        "source_rule": TARGET_SOURCE_RULE,
        "input_bucket": TARGET_BUCKET,
        "count": len(records),
        "risk_bucket_counts": dict(risk_counts),
        "closure_candidate_buckets": sorted(closure_candidate_buckets),
        "closure_candidate_count": closure_candidate_count,
        "review_count": review_count,
        "gate_implications": {
            "can_close_formula_outcomes": False,
            "can_promote_math_textbook_profile": False,
            "next_action": "spot_check_closure_candidate_buckets_before_optional_narrow_closure_rule",
        },
        "items": records,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "items"}, ensure_ascii=False, indent=2)
    rows = []
    for item in report.get("items") or []:
        crop = str(item.get("source_crop") or "")
        crop_html = f'<img src="{html.escape(crop)}" alt="source crop">' if crop else ""
        rows.append(
            "<article>"
            f"<h2>{html.escape(str(item.get('outcome_id') or ''))}</h2>"
            f"<p><strong>Bucket:</strong> {html.escape(str(item.get('risk_bucket') or ''))} | "
            f"<strong>Reasons:</strong> {html.escape(', '.join(str(x) for x in item.get('reasons') or []))}</p>"
            f"{crop_html}"
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
  <title>Math Raw Assignment Exact Closure Risk</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    article {{ border-top: 1px solid #ddd; padding: 16px 0; }}
    img {{ max-width: 520px; border: 1px solid #ddd; display: block; margin: 8px 0; }}
    .pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    pre {{ white-space: pre-wrap; background: #f6f6f6; padding: 10px; overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <h1>Math Raw Assignment Exact Closure Risk</h1>
  <pre>{html.escape(summary)}</pre>
  {''.join(rows)}
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_audit(args.standard_dir)
    out_dir = args.out_dir or args.standard_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "math_raw_assignment_exact_closure_risk_audit.json", report)
    (out_dir / "math_raw_assignment_exact_closure_risk_audit.html").write_text(build_html(report), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
