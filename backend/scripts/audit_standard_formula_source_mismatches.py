#!/usr/bin/env python3
"""Audit open formula source mismatches with a conservative semantic key."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


READY_CROP_STATUSES = {"created", "reused"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def outcome_id_for_packet(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


def packet_items(doc: dict[str, Any]) -> list[dict[str, Any]]:
    items = doc.get("items")
    return items if isinstance(items, list) else []


def formula_semantic_key(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"(?<!\\)\*\*([^*\n]+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\\)__([^_\n]+?)__", r"\1", text)
    replacements = {
        r"\\cdot": "*",
        r"\\times": "*",
        r"\\div": "/",
        r"\\pm": "+-",
        r"\\leq": "<=",
        r"\\geq": ">=",
        r"\\neq": "!=",
        r"\\lt": "<",
        r"\\gt": ">",
        r"\\left": "",
        r"\\right": "",
        r"\\quad": "",
        r"\\,": "",
        r"\\;": "",
        r"\\:": "",
        r"\\!": "",
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"\\begin\{([^}]+)\}", r" begin\1 ", text)
    text = re.sub(r"\\end\{([^}]+)\}", r" end\1 ", text)
    text = re.sub(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"frac(\1)/(\2)", text)
    text = re.sub(r"\\sqrt\s*\[([^{}]+)\]\s*\{([^{}]+)\}", r"sqrtroot(\1)(\2)", text)
    text = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", text)
    text = re.sub(r"\\text\s*\{([^{}]+)\}", r"text(\1)", text)
    text = re.sub(r"\\([a-zA-Z]+)", r"\1", text)
    text = text.replace("$", "")
    return re.sub(r"[^a-zA-Z0-9+\-*/=<>!%.^_()]+", "", text).lower()


def classify(outcome: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    clean_text = str(packet.get("clean_text") or "")
    source_content = str(packet.get("source_content") or "")
    clean_key = formula_semantic_key(clean_text)
    source_key = formula_semantic_key(source_content)
    ratio = SequenceMatcher(None, clean_key, source_key).ratio() if clean_key or source_key else 0.0
    crop_status = str(outcome.get("source_crop_status") or packet.get("source_crop_status") or "")
    has_crop = crop_status in READY_CROP_STATUSES
    has_bbox = bool(outcome.get("source_page_number") and outcome.get("source_bbox"))

    if not has_bbox:
        bucket = "needs_page_bbox"
    elif not has_crop:
        bucket = "needs_source_crop"
    elif clean_key and clean_key == source_key:
        bucket = "deterministic_formula_semantic_equivalent"
    elif ratio >= 0.98:
        bucket = "near_equivalent_needs_manual_review"
    else:
        bucket = "semantic_mismatch_needs_manual_review"

    return {
        "outcome_id": outcome.get("outcome_id"),
        "block_id": outcome.get("block_id"),
        "status": outcome.get("status"),
        "decision": outcome.get("decision"),
        "bucket": bucket,
        "source_page_number": outcome.get("source_page_number"),
        "source_bbox": outcome.get("source_bbox") or [],
        "source_crop": outcome.get("source_crop") or packet.get("source_crop") or "",
        "source_crop_status": crop_status,
        "semantic_key_equal": clean_key == source_key and bool(clean_key),
        "semantic_key_similarity": round(ratio, 6),
        "clean_semantic_key_preview": clean_key[:500],
        "source_semantic_key_preview": source_key[:500],
        "clean_text_preview": clean_text[:500],
        "source_content_preview": source_content[:500],
        "source_match_rule": packet.get("source_match_rule") or "",
    }


def build_audit(standard_dir: Path) -> dict[str, Any]:
    outcomes = read_json(standard_dir / "standard_review_outcomes.json")
    packets = read_json(standard_dir / "standard_visual_review_packets.json")
    packets_by_outcome = {outcome_id_for_packet(packet): packet for packet in packet_items(packets)}
    items: list[dict[str, Any]] = []
    for outcome in packet_items(outcomes):
        if outcome.get("packet_type") != "formula_visual_review":
            continue
        if outcome.get("status") != "open" or not outcome.get("basic_print_blocking"):
            continue
        if outcome.get("decision") != "needs_layout_fix":
            continue
        packet = packets_by_outcome.get(str(outcome.get("outcome_id") or ""), {})
        items.append(classify(outcome, packet))

    bucket_counts = Counter(str(item.get("bucket") or "") for item in items)
    closable_count = bucket_counts.get("deterministic_formula_semantic_equivalent", 0)
    return {
        "schema": "luceon-standard-formula-source-mismatch-audit/v1",
        "standard_dir": str(standard_dir),
        "policy": "audit_only_formula_semantic_equivalent_requires_explicit_closure",
        "decision_boundary": (
            "A formula semantic-equivalent outcome preserves operators, exponents, digits, "
            "formula commands, source page/bbox, and generated/reused source crop evidence. "
            "Near-equivalent or mismatched keys remain manual review."
        ),
        "count": len(items),
        "bucket_counts": dict(bucket_counts),
        "deterministic_formula_semantic_equivalent_count": closable_count,
        "manual_review_count": len(items) - closable_count,
        "items": items,
    }


def build_html(audit: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in audit.items() if k != "items"}, ensure_ascii=False, indent=2)
    rows = []
    for item in audit.get("items", [])[:500]:
        crop = str(item.get("source_crop") or "")
        crop_html = f'<img src="{html.escape(crop)}" alt="source crop">' if crop else ""
        rows.append(
            "<article>"
            f"<h2>{html.escape(str(item.get('outcome_id') or ''))}</h2>"
            f"<p><strong>Bucket:</strong> {html.escape(str(item.get('bucket') or ''))} | "
            f"<strong>Similarity:</strong> {html.escape(str(item.get('semantic_key_similarity') or ''))}</p>"
            f"{crop_html}"
            "<div class=\"pair\">"
            f"<pre>{html.escape(str(item.get('clean_text_preview') or ''))}</pre>"
            f"<pre>{html.escape(str(item.get('source_content_preview') or ''))}</pre>"
            "</div>"
            "<div class=\"pair\">"
            f"<pre>{html.escape(str(item.get('clean_semantic_key_preview') or ''))}</pre>"
            f"<pre>{html.escape(str(item.get('source_semantic_key_preview') or ''))}</pre>"
            "</div>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Formula Source Mismatch Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    article {{ border-top: 1px solid #ddd; padding: 16px 0; }}
    img {{ max-width: 520px; border: 1px solid #ddd; display: block; margin: 8px 0; }}
    .pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    pre {{ white-space: pre-wrap; background: #f6f6f6; padding: 10px; overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <h1>Formula Source Mismatch Audit</h1>
  <pre>{html.escape(summary)}</pre>
  {''.join(rows)}
</body>
</html>
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit open formula source mismatches with a conservative semantic key.")
    parser.add_argument("--standard-dir", required=True, type=Path, help="Existing standard-final directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    audit = build_audit(args.standard_dir)
    write_json(args.standard_dir / "formula_source_mismatch_audit.json", audit)
    (args.standard_dir / "formula_source_mismatch_audit.html").write_text(build_html(audit), encoding="utf-8")
    print(json.dumps({k: v for k, v in audit.items() if k != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
