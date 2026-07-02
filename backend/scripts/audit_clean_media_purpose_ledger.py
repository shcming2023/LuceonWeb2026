#!/usr/bin/env python3
"""Build a Clean media purpose/role closure ledger from Standard image evidence."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

from standard_from_clean import read_json, write_json


def load_items(path: Path) -> list[dict[str, Any]]:
    data = read_json(path)
    items = data.get("items") if isinstance(data.get("items"), list) else []
    return items


def path_key(value: Any) -> str:
    return str(value or "").strip()


def image_name(value: Any) -> str:
    return Path(path_key(value)).name


def relation_role(relation: dict[str, Any]) -> str:
    category = str(relation.get("category") or "")
    action = str(relation.get("action") or "")
    if category in {"exercise_key_figure", "explanation_key_figure"}:
        return "content_bearing_key_figure"
    if category == "helper_icon" or action == "compress_keep_near":
        return "helper_icon"
    if category == "decorative":
        return "decorative"
    return "unknown"


def disposition(
    clean_item: dict[str, Any],
    relation: dict[str, Any],
    image_outcome: dict[str, Any],
    review_outcome: dict[str, Any],
) -> tuple[str, list[str], list[str]]:
    role = relation_role(relation)
    evidence: list[str] = []
    blockers: list[str] = []
    if relation:
        evidence.append("image_relation_report")
    if image_outcome:
        evidence.append("image_outcome_rule_audit")
    if review_outcome:
        evidence.append("standard_review_outcomes")

    if role == "content_bearing_key_figure":
        ok = (
            image_outcome.get("proposed_decision") == "accepted_by_rule"
            and image_outcome.get("source_crop_status") in {"created", "reused"}
            and not image_outcome.get("issues")
        )
        if ok:
            return "content_bearing_source_confirmed", evidence, blockers
        blockers.append("content_bearing_image_missing_source_crop_rule_acceptance")
        return "needs_media_review", evidence, blockers

    if role == "helper_icon":
        return "helper_icon_compact_nearby_rendering", evidence, blockers

    if role == "decorative":
        return "decorative_non_blocking_retained", evidence, blockers

    blockers.append("missing_reusable_media_role")
    return "needs_media_review", evidence, blockers


def build_ledger(clean_dir: Path, standard_dir: Path) -> dict[str, Any]:
    media_items = load_items(clean_dir / "media_report.json")
    relation_items = load_items(standard_dir / "image_relation_report.json")
    outcome_items = load_items(standard_dir / "image_outcome_rule_audit.json")
    review_items = load_items(standard_dir / "standard_review_outcomes.json")

    relation_by_image = {path_key(item.get("image")): item for item in relation_items}
    relation_by_name = {image_name(item.get("image")): item for item in relation_items}
    outcome_by_image = {path_key(item.get("standard_image")): item for item in outcome_items}
    outcome_by_block = {str(item.get("block_id") or ""): item for item in outcome_items}
    review_by_block = {str(item.get("block_id") or ""): item for item in review_items if item.get("packet_type") == "image_source_visual_confirmation"}

    ledger_items: list[dict[str, Any]] = []
    for media in media_items:
        media_path = path_key(media.get("path"))
        relation = relation_by_image.get(media_path) or relation_by_name.get(image_name(media_path)) or {}
        block_id = str(relation.get("block_id") or "")
        image_outcome = outcome_by_image.get(media_path) or outcome_by_block.get(block_id) or {}
        review_outcome = review_by_block.get(block_id) or {}
        item_disposition, evidence, blockers = disposition(media, relation, image_outcome, review_outcome)
        ledger_items.append(
            {
                "media_path": media_path,
                "clean_decision": media.get("decision"),
                "clean_reasons": media.get("reasons") or [],
                "line": media.get("line"),
                "alt": media.get("alt"),
                "dimensions": {"width": media.get("width"), "height": media.get("height")},
                "raw_semantics_available": bool((media.get("raw_semantics") or {}).get("available")),
                "standard_block_id": block_id,
                "standard_category": relation.get("category"),
                "standard_action": relation.get("action"),
                "role": relation_role(relation),
                "disposition": item_disposition,
                "source_page_number": image_outcome.get("source_page_number") or review_outcome.get("source_page_number"),
                "source_crop": image_outcome.get("source_crop") or review_outcome.get("source_crop"),
                "source_crop_status": image_outcome.get("source_crop_status") or review_outcome.get("source_crop_status"),
                "rule_decision": image_outcome.get("proposed_decision") or review_outcome.get("decision"),
                "evidence": evidence,
                "blockers": blockers,
                "context_excerpt": media.get("context_excerpt"),
            }
        )

    role_counts = Counter(item["role"] for item in ledger_items)
    disposition_counts = Counter(item["disposition"] for item in ledger_items)
    clean_decision_counts = Counter(str(item["clean_decision"] or "") for item in ledger_items)
    review_items_only = [item for item in ledger_items if item["clean_decision"] == "review"]
    open_blockers = [item for item in review_items_only if item["blockers"]]
    review_role_counts = Counter(item["role"] for item in review_items_only)
    review_disposition_counts = Counter(item["disposition"] for item in review_items_only)
    verdict = "media_purpose_ledger_pass" if not open_blockers else "media_purpose_ledger_review"
    return {
        "schema": "luceon-clean-media-purpose-ledger/v1",
        "policy": "audit_only_no_clean_status_mutation",
        "clean_dir": str(clean_dir),
        "standard_dir": str(standard_dir),
        "verdict": verdict,
        "promotion_gate_candidate": verdict == "media_purpose_ledger_pass",
        "summary": {
            "media_item_count": len(ledger_items),
            "clean_decision_counts": dict(clean_decision_counts),
            "role_counts": dict(role_counts),
            "disposition_counts": dict(disposition_counts),
            "review_item_count": len(review_items_only),
            "review_role_counts": dict(review_role_counts),
            "review_disposition_counts": dict(review_disposition_counts),
            "open_blocking_review_item_count": len(open_blockers),
        },
        "closure_rule": (
            "Clean media review items may close when every retained review item maps to a Standard image role and "
            "has either source-crop-backed accepted key-figure evidence or helper/decorative retained-nearby disposition."
        ),
        "items": ledger_items,
        "open_blocking_items": open_blockers,
        "evidence_paths": {
            "clean_media_report": str(clean_dir / "media_report.json"),
            "standard_image_relation_report": str(standard_dir / "image_relation_report.json"),
            "standard_image_outcome_rule_audit": str(standard_dir / "image_outcome_rule_audit.json"),
            "standard_review_outcomes": str(standard_dir / "standard_review_outcomes.json"),
        },
    }


def render_html(report: dict[str, Any]) -> str:
    rows = []
    for item in report["items"]:
        cls = "bad" if item["blockers"] else "ok"
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item['media_path']))}</td>"
            f"<td>{html.escape(str(item['clean_decision']))}</td>"
            f"<td>{html.escape(str(item['role']))}</td>"
            f"<td>{html.escape(str(item['disposition']))}</td>"
            f"<td>{html.escape(str(item['standard_block_id']))}</td>"
            f"<td>{html.escape(str(item['source_crop_status']))}</td>"
            f"<td class=\"{cls}\">{html.escape(', '.join(item['blockers']))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Clean Media Purpose Ledger</title>
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
<h1>Clean Media Purpose Ledger</h1>
<p><strong>Verdict:</strong> {html.escape(report['verdict'])}</p>
<pre>{html.escape(json.dumps(report['summary'], ensure_ascii=False, indent=2))}</pre>
<table>
<thead><tr><th>Media</th><th>Clean</th><th>Role</th><th>Disposition</th><th>Block</th><th>Crop</th><th>Blockers</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</body>
</html>
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-dir", required=True, type=Path)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_ledger(args.clean_dir, args.standard_dir)
    write_json(args.out_dir / "clean_media_purpose_ledger.json", report)
    (args.out_dir / "clean_media_purpose_ledger.html").write_text(render_html(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(args.out_dir / "clean_media_purpose_ledger.json"),
                "html": str(args.out_dir / "clean_media_purpose_ledger.html"),
                "verdict": report["verdict"],
                "summary": report["summary"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
