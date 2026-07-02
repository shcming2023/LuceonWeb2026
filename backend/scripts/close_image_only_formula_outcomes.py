#!/usr/bin/env python3
"""Close duplicate formula outcomes for image-only blocks covered by image review."""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from close_standard_review_outcomes import build_closure_html, build_closure_report, update_acceptance_and_manifest
from standard_from_clean import (
    build_review_outcomes_html,
    is_image_only_markdown,
    refresh_visual_outcome_review_artifacts,
    refresh_workbook_profile_artifacts,
    write_json,
)


FORMULA_PACKET_TYPE = "formula_visual_review"
IMAGE_PACKET_TYPE = "image_source_visual_confirmation"
READY_CROP_STATUSES = {"created", "reused"}
RECLASSIFIED_STATUS = "not_required_image_only_formula_reclassified"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def summarize_review_outcomes(review_outcomes: dict[str, Any]) -> None:
    items = review_outcomes.get("items") or []
    review_outcomes["count"] = len(items)
    review_outcomes["decision_counts"] = dict(Counter(str(item.get("decision") or "") for item in items))
    review_outcomes["open_blocking_count"] = sum(
        1 for item in items if item.get("status") == "open" and item.get("basic_print_blocking")
    )
    review_outcomes["closed_count"] = sum(1 for item in items if item.get("status") == "closed")


def recompute_visual_crop_summary(visual_packets: dict[str, Any]) -> dict[str, Any]:
    items = visual_packets.get("items") or []
    status_counts = Counter(str(item.get("source_crop_status") or "") for item in items)
    not_required_count = int(status_counts.get(RECLASSIFIED_STATUS, 0))
    crop_count = sum(1 for item in items if item.get("source_crop_status") in READY_CROP_STATUSES)
    required_count = max(len(items) - not_required_count, 0)
    summary = dict(visual_packets.get("source_crop_summary") or {})
    summary.update(
        {
            "source_crop_generation": "generated" if crop_count == required_count else "attempted",
            "source_crop_count": crop_count,
            "source_crop_required_count": required_count,
            "source_crop_status_counts": dict(status_counts),
            "not_required_count": not_required_count,
            "not_required_rule": "image_only_formula_packet_covered_by_image_visual_confirmation",
        }
    )
    visual_packets["source_crop_summary"] = summary
    return summary


def update_visual_crop_audit(standard_dir: Path, summary: dict[str, Any]) -> None:
    audit_path = standard_dir / "visual_source_crop_audit.json"
    audit = read_json(audit_path)
    if not audit:
        return
    audit["summary"] = {**(audit.get("summary") or {}), **summary}
    sync_summary = audit.get("sync_summary") if isinstance(audit.get("sync_summary"), dict) else {}
    if sync_summary:
        sync_summary["outcome_source_crop_status_counts"] = summary.get("source_crop_status_counts") or {}
        audit["sync_summary"] = sync_summary
    write_json(audit_path, audit)
    html_path = standard_dir / "visual_source_crop_audit.html"
    html_path.write_text(
        "<!doctype html><meta charset=\"utf-8\"><title>Visual Source Crop Audit</title>"
        f"<pre>{html.escape(json.dumps(audit, ensure_ascii=False, indent=2))}</pre>",
        encoding="utf-8",
    )


def build_html(report: dict[str, Any]) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Image-only Formula Reclassification</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    pre {{ background: #f6f6f6; padding: 12px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Image-only Formula Reclassification</h1>
  <pre>{html.escape(json.dumps(report, ensure_ascii=False, indent=2))}</pre>
</body>
</html>
"""


def close_image_only_formula_outcomes(standard_dir: Path, *, apply: bool) -> dict[str, Any]:
    document = read_json(standard_dir / "standard_document.json")
    visual_packets = read_json(standard_dir / "standard_visual_review_packets.json")
    review_outcomes = read_json(standard_dir / "standard_review_outcomes.json")
    blocks = {str(block.get("id") or ""): block for block in document.get("blocks") or []}
    visual_packets_by_outcome = {
        f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}": packet
        for packet in visual_packets.get("items") or []
        if isinstance(packet, dict)
    }
    outcomes_by_block: dict[str, list[dict[str, Any]]] = {}
    for item in review_outcomes.get("items") or []:
        outcomes_by_block.setdefault(str(item.get("block_id") or ""), []).append(item)

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    candidates: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for item in review_outcomes.get("items") or []:
        if item.get("packet_type") != FORMULA_PACKET_TYPE:
            continue
        if item.get("status") != "open" or not item.get("basic_print_blocking"):
            continue
        block_id = str(item.get("block_id") or "")
        block = blocks.get(block_id) or {}
        markdown = str(block.get("markdown") or "")
        image_outcomes = [
            outcome
            for outcome in outcomes_by_block.get(block_id, [])
            if outcome.get("packet_type") == IMAGE_PACKET_TYPE
            and outcome.get("status") == "closed"
            and outcome.get("decision") == "accepted_by_rule"
            and outcome.get("source_crop_status") in READY_CROP_STATUSES
            and outcome.get("source_crop")
        ]
        if not is_image_only_markdown(markdown):
            continue
        if str(block.get("text") or "").strip():
            skipped.append({"outcome_id": item.get("outcome_id"), "block_id": block_id, "reason": "block_text_not_empty"})
            continue
        if not image_outcomes:
            skipped.append({"outcome_id": item.get("outcome_id"), "block_id": block_id, "reason": "closed_image_outcome_missing"})
            continue
        image_outcome = image_outcomes[0]
        candidates.append(
            {
                "outcome_id": item.get("outcome_id"),
                "block_id": block_id,
                "image_outcome_id": image_outcome.get("outcome_id"),
                "image_source_crop": image_outcome.get("source_crop"),
                "image_source_crop_status": image_outcome.get("source_crop_status"),
                "heading_path": item.get("heading_path") or [],
            }
        )
        if apply:
            item.update(
                {
                    "decision": "non_blocking",
                    "status": "closed",
                    "basic_print_blocking": False,
                    "source_evidence_ready": True,
                    "source_page_number": image_outcome.get("source_page_number"),
                    "source_bbox": image_outcome.get("source_bbox") or [],
                    "source_crop": image_outcome.get("source_crop") or "",
                    "source_crop_status": RECLASSIFIED_STATUS,
                    "reviewer": "system:image_only_formula_reclassification",
                    "reviewed_at": now,
                    "notes": "Closed as non_blocking because this is an image-only block already covered by a closed image_source_visual_confirmation outcome.",
                    "evidence": [
                        "standard_document.json",
                        "standard_review_outcomes.json",
                        str(image_outcome.get("outcome_id") or ""),
                        str(image_outcome.get("source_crop") or ""),
                        "image_only_formula_packet_covered_by_image_visual_confirmation",
                    ],
                    "next_action": "none",
                }
            )
            packet = visual_packets_by_outcome.get(str(item.get("outcome_id") or ""))
            if packet:
                packet["source_page_number"] = image_outcome.get("source_page_number")
                packet["source_bbox"] = image_outcome.get("source_bbox") or []
                packet["source_crop"] = image_outcome.get("source_crop") or ""
                packet["source_crop_status"] = RECLASSIFIED_STATUS
                packet["source_match_rule"] = "image_only_formula_packet_covered_by_image_visual_confirmation"

    crop_summary = recompute_visual_crop_summary(visual_packets)
    if apply:
        summarize_review_outcomes(review_outcomes)
        review_outcomes["updated_at"] = now
        review_outcomes["image_only_formula_reclassification_summary"] = {
            "closed_count": len(candidates),
            "status": "applied",
        }
        review_outcomes["source_crop_summary"] = crop_summary
        write_json(standard_dir / "standard_visual_review_packets.json", visual_packets)
        write_json(standard_dir / "standard_review_outcomes.json", review_outcomes)
        (standard_dir / "review_outcomes.html").write_text(build_review_outcomes_html(review_outcomes), encoding="utf-8")
        refresh_visual_outcome_review_artifacts(standard_dir)
        refresh_workbook_profile_artifacts(standard_dir)
        update_visual_crop_audit(standard_dir, crop_summary)

    report = {
        "schema": "luceon-standard-image-only-formula-reclassification/v1",
        "standard_dir": str(standard_dir),
        "mode": "apply" if apply else "dry_run",
        "policy": "close_only_image_only_formula_packets_with_closed_image_visual_confirmation",
        "status_counts": {"closed_non_blocking": len(candidates)} if apply else {"candidate": len(candidates)},
        "candidate_count": len(candidates),
        "skipped_count": len(skipped),
        "items": candidates,
        "skipped_items": skipped[:100],
        "notes": [
            "This does not close mixed text+image formula blocks.",
            "This does not treat image alt text as separately verified formula text.",
            "The paired image outcome must already be closed accepted_by_rule with a generated or reused source crop.",
        ],
    }
    if apply:
        write_json(standard_dir / "image_only_formula_reclassification_report.json", report)
        (standard_dir / "image_only_formula_reclassification.html").write_text(build_html(report), encoding="utf-8")
        acceptance = update_acceptance_and_manifest(standard_dir, review_outcomes, crop_summary)
        closure = build_closure_report(standard_dir, acceptance, review_outcomes, crop_summary)
        write_json(standard_dir / "basic_print_closure_report.json", closure)
        (standard_dir / "basic_print_closure.html").write_text(build_closure_html(closure), encoding="utf-8")
    return report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Close image-only formula review outcomes covered by image review.")
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = close_image_only_formula_outcomes(args.standard_dir, apply=args.apply)
    print(json.dumps({"mode": report["mode"], "candidate_count": report["candidate_count"], "status_counts": report["status_counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
