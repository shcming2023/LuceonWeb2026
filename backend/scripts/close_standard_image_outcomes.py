#!/usr/bin/env python3
"""Classify and optionally close Standard image review outcomes by deterministic evidence."""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from standard_from_clean import (
    acceptance_status,
    apply_issue_candidate_gates_to_acceptance,
    build_review_outcomes_html,
    refresh_visual_outcome_review_artifacts,
    refresh_workbook_profile_artifacts,
    refresh_issue_candidate_disposition_audit_artifacts,
    read_json,
    write_json,
)
from close_standard_review_outcomes import build_closure_html, build_closure_report

IMAGE_PACKET_TYPE = "image_source_visual_confirmation"
KEY_IMAGE_CATEGORIES = {"exercise_key_figure", "explanation_key_figure"}
SOURCE_CROP_READY = {"created", "reused"}
QUESTION_CONTEXT_TYPES = {"question", "question_group"}
EXPLANATION_CONTEXT_TYPES = {"paragraph", "captioned_figure", "section", "question", "question_group"}


def image_outcome_id(packet: dict[str, Any]) -> str:
    category = str(packet.get("category") or "image")
    block_id = str(packet.get("block_id") or "")
    return f"image:{category}:{block_id}"


def image_probe(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "exists": path.exists(),
        "path": str(path),
        "bytes": path.stat().st_size if path.exists() else 0,
    }
    if not path.exists():
        return result
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            result["size"] = [image.size[0], image.size[1]]
            result["area"] = image.size[0] * image.size[1]
    except Exception as exc:
        result["error"] = str(exc)[:240]
    return result


def aspect_ratio_delta(standard_info: dict[str, Any], crop_info: dict[str, Any]) -> float | None:
    standard_size = standard_info.get("size") if isinstance(standard_info.get("size"), list) else []
    crop_size = crop_info.get("size") if isinstance(crop_info.get("size"), list) else []
    if len(standard_size) != 2 or len(crop_size) != 2:
        return None
    sw, sh = float(standard_size[0]), float(standard_size[1])
    cw, ch = float(crop_size[0]), float(crop_size[1])
    if sw <= 0 or sh <= 0 or cw <= 0 or ch <= 0:
        return None
    return abs(math.log((sw / sh) / (cw / ch)))


def context_label(packet: dict[str, Any]) -> str:
    parent_id = str(packet.get("parent_id") or "")
    parent_type = str(packet.get("parent_type") or "")
    previous_type = str((packet.get("previous_block") or {}).get("type") or "")
    next_type = str((packet.get("next_block") or {}).get("type") or "")
    category = str(packet.get("category") or "")
    if parent_id and parent_type in QUESTION_CONTEXT_TYPES:
        return "parented_question_context"
    if parent_id:
        return "parented_other_context"
    if category == "explanation_key_figure" and (previous_type in EXPLANATION_CONTEXT_TYPES or next_type in EXPLANATION_CONTEXT_TYPES):
        return "neighbor_explanation_context"
    if previous_type or next_type:
        return "neighbor_only_context"
    return "no_context"


def next_action_for_decision(decision: str) -> str:
    return {
        "accepted_by_rule": "none",
        "non_blocking": "none",
        "needs_page_bbox": "locate_source_page_bbox",
        "needs_source_crop": "generate_source_crop",
        "needs_reconstruction": "reconstruct_or_replace_standard_image_from_source_crop",
    }.get(decision, "manual_image_visual_review")


def classify_image_packet(packet: dict[str, Any], standard_dir: Path) -> dict[str, Any]:
    standard_ref = str(packet.get("image") or "")
    crop_ref = str(packet.get("source_crop") or "")
    standard_info = image_probe(standard_dir / standard_ref) if standard_ref else {"exists": False, "path": ""}
    crop_info = image_probe(standard_dir / crop_ref) if crop_ref else {"exists": False, "path": ""}
    ratio_delta = aspect_ratio_delta(standard_info, crop_info)
    category = str(packet.get("category") or "")
    action = str(packet.get("action") or "")
    context = context_label(packet)
    source_bbox = packet.get("source_bbox") or []
    source_crop_status = str(packet.get("source_crop_status") or "")
    issues: list[str] = []
    rule_id = ""
    confidence = "low"

    if category not in KEY_IMAGE_CATEGORIES:
        decision = "non_blocking"
        rule_id = "image_non_key_category_excluded"
        confidence = "high"
    elif not standard_info.get("exists"):
        decision = "needs_reconstruction"
        issues.append("standard_image_missing")
    elif not crop_info.get("exists") or source_crop_status not in SOURCE_CROP_READY:
        decision = "needs_source_crop"
        issues.append("source_crop_missing_or_not_ready")
    elif not packet.get("source_page_number") or len(source_bbox) != 4:
        decision = "needs_page_bbox"
        issues.append("source_page_bbox_missing")
    elif not standard_info.get("size") or not crop_info.get("size"):
        decision = "needs_reconstruction"
        issues.append("image_dimensions_unreadable")
    elif ratio_delta is None or ratio_delta > 0.10:
        decision = "needs_reconstruction"
        issues.append("standard_source_aspect_ratio_mismatch")
    elif int(standard_info.get("area") or 0) < 25000:
        decision = "needs_reconstruction"
        issues.append("standard_image_too_small_for_basic_print")
    elif min(standard_info.get("size") or [0, 0]) < 120:
        decision = "needs_reconstruction"
        issues.append("standard_image_min_dimension_too_small")
    else:
        decision = "accepted_by_rule"
        rule_id = "raw_image_ref_source_crop_aspect_context"
        if context in {"parented_question_context", "neighbor_explanation_context"} and ratio_delta <= 0.08:
            confidence = "high"
        else:
            confidence = "medium"

    if decision != "accepted_by_rule" and not rule_id:
        rule_id = "image_requires_manual_or_reconstruction_work"

    return {
        "outcome_id": image_outcome_id(packet),
        "block_id": packet.get("block_id") or "",
        "category": category,
        "action": action,
        "source_page_number": packet.get("source_page_number"),
        "heading_path": packet.get("heading_path") or [],
        "parent_id": packet.get("parent_id") or "",
        "parent_type": packet.get("parent_type") or "",
        "context": context,
        "previous_block": packet.get("previous_block") or {},
        "next_block": packet.get("next_block") or {},
        "standard_image": standard_ref,
        "source_crop": crop_ref,
        "source_crop_status": source_crop_status,
        "source_bbox": source_bbox,
        "source_sub_type": packet.get("source_sub_type") or "",
        "source_content": str(packet.get("source_content") or "")[:1000],
        "standard_image_info": standard_info,
        "source_crop_info": crop_info,
        "aspect_ratio_delta": round(ratio_delta, 6) if ratio_delta is not None else None,
        "proposed_decision": decision,
        "confidence": confidence,
        "rule_id": rule_id,
        "issues": issues,
        "next_action": next_action_for_decision(decision),
    }


def build_batches(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    batches: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
    for item in items:
        page = item.get("source_page_number")
        page_number = int(page) if isinstance(page, int) else -1
        key = (str(item.get("category") or ""), str(item.get("action") or ""), page_number)
        batches.setdefault(key, []).append(item)
    rows: list[dict[str, Any]] = []
    for (category, action, page_number), batch_items in sorted(batches.items(), key=lambda row: (row[0][0], row[0][1], row[0][2])):
        rows.append(
            {
                "category": category,
                "action": action,
                "source_page_number": page_number if page_number > 0 else None,
                "count": len(batch_items),
                "decision_counts": dict(Counter(str(item.get("proposed_decision") or "") for item in batch_items)),
                "confidence_counts": dict(Counter(str(item.get("confidence") or "") for item in batch_items)),
                "context_counts": dict(Counter(str(item.get("context") or "") for item in batch_items)),
                "block_ids": [str(item.get("block_id") or "") for item in batch_items],
            }
        )
    return rows


def build_image_outcome_rule_audit(standard_dir: Path) -> dict[str, Any]:
    packets = read_json(standard_dir / "image_visual_confirmation_packets.json")
    items = [
        classify_image_packet(packet, standard_dir)
        for packet in packets.get("items") or []
        if isinstance(packet, dict)
    ]
    return {
        "schema": "luceon-standard-image-outcome-rule-audit/v1",
        "policy": "deterministic_image_ref_source_crop_aspect_context_rules",
        "standard_dir": str(standard_dir),
        "applied": False,
        "rules": [
            {
                "decision": "accepted_by_rule",
                "requires": [
                    "image outcome category is exercise_key_figure or explanation_key_figure",
                    "Standard image file exists and is readable",
                    "source PDF crop exists and was generated/reused from Raw content_list page/bbox",
                    "source page/bbox is present",
                    "Standard/source aspect-ratio delta <= 0.10",
                    "Standard image area >= 25000 px and min dimension >= 120 px",
                    "question or explanation context exists",
                ],
            },
            {
                "decision": "needs_reconstruction",
                "requires_any": [
                    "Standard image missing",
                    "image dimensions unreadable",
                    "Standard/source aspect ratio mismatch",
                    "Standard image too small for Basic Print",
                ],
            },
            {
                "decision": "non_blocking",
                "requires": ["image is not a key figure category"],
            },
        ],
        "items": items,
        "count": len(items),
        "decision_counts": dict(Counter(str(item.get("proposed_decision") or "") for item in items)),
        "category_counts": dict(Counter(str(item.get("category") or "") for item in items)),
        "action_counts": dict(Counter(str(item.get("action") or "") for item in items)),
        "context_counts": dict(Counter(str(item.get("context") or "") for item in items)),
        "confidence_counts": dict(Counter(str(item.get("confidence") or "") for item in items)),
        "issue_counts": dict(Counter(issue for item in items for issue in item.get("issues") or [])),
        "batches": build_batches(items),
    }


def build_image_outcome_rule_audit_html(report: dict[str, Any]) -> str:
    summary = {
        key: report.get(key)
        for key in ["count", "decision_counts", "category_counts", "action_counts", "context_counts", "confidence_counts", "issue_counts"]
    }
    batch_rows = []
    for batch in report.get("batches") or []:
        batch_rows.append(
            "<tr>"
            f"<td>{html.escape(str(batch.get('category') or ''))}</td>"
            f"<td>{html.escape(str(batch.get('action') or ''))}</td>"
            f"<td>{html.escape(str(batch.get('source_page_number') or ''))}</td>"
            f"<td>{html.escape(str(batch.get('count') or 0))}</td>"
            f"<td>{html.escape(json.dumps(batch.get('decision_counts') or {}, ensure_ascii=False))}</td>"
            f"<td>{html.escape(json.dumps(batch.get('context_counts') or {}, ensure_ascii=False))}</td>"
            f"<td>{html.escape(', '.join(batch.get('block_ids') or []))}</td>"
            "</tr>"
        )
    cards = []
    for item in report.get("items") or []:
        heading = " > ".join(item.get("heading_path") or [])
        cards.append(
            "<article class=\"item\">"
            f"<h2>{html.escape(str(item.get('outcome_id') or ''))}</h2>"
            f"<p><strong>Decision:</strong> {html.escape(str(item.get('proposed_decision') or ''))} | "
            f"<strong>Confidence:</strong> {html.escape(str(item.get('confidence') or ''))} | "
            f"<strong>Rule:</strong> {html.escape(str(item.get('rule_id') or ''))}</p>"
            f"<p><strong>Category:</strong> {html.escape(str(item.get('category') or ''))} | "
            f"<strong>Action:</strong> {html.escape(str(item.get('action') or ''))} | "
            f"<strong>Page:</strong> {html.escape(str(item.get('source_page_number') or ''))} | "
            f"<strong>Context:</strong> {html.escape(str(item.get('context') or ''))}</p>"
            f"<p><strong>Heading:</strong> {html.escape(heading)}</p>"
            "<div class=\"pair\">"
            f"<section><h3>Standard</h3><img src=\"{html.escape(str(item.get('standard_image') or ''))}\" alt=\"standard image\"></section>"
            f"<section><h3>Source Crop</h3><img src=\"{html.escape(str(item.get('source_crop') or ''))}\" alt=\"source crop\"></section>"
            "</div>"
            f"<pre>{html.escape(json.dumps({key: item.get(key) for key in ['standard_image_info', 'source_crop_info', 'aspect_ratio_delta', 'source_bbox', 'issues', 'next_action', 'source_content']}, ensure_ascii=False, indent=2))}</pre>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Image Outcome Rule Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 14px 0 24px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    .summary {{ padding: 12px 14px; border: 1px solid #bbb; margin-bottom: 18px; }}
    .item {{ break-inside: avoid; border-top: 1px solid #bbb; padding: 16px 0; }}
    h1, h2 {{ margin: 0 0 8px; }}
    h2 {{ font-size: 16px; }}
    h3 {{ font-size: 13px; margin: 0 0 6px; }}
    .pair {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; align-items: start; }}
    img {{ max-width: 100%; max-height: 300px; object-fit: contain; border: 1px solid #ccc; background: #fff; }}
    pre {{ white-space: pre-wrap; background: #f6f6f6; padding: 8px; max-height: 280px; overflow: auto; }}
  </style>
</head>
<body>
  <h1>Image Outcome Rule Audit</h1>
  <section class="summary"><pre>{html.escape(json.dumps(summary, ensure_ascii=False, indent=2))}</pre></section>
  <h2>Batches</h2>
  <table><thead><tr><th>Category</th><th>Action</th><th>Page</th><th>Count</th><th>Decisions</th><th>Contexts</th><th>Blocks</th></tr></thead><tbody>{''.join(batch_rows)}</tbody></table>
  <h2>Items</h2>
  {''.join(cards)}
</body>
</html>
"""


def outcome_packet_type_summary(review_outcomes: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, dict[str, Any]] = {}
    for item in review_outcomes.get("items") or []:
        packet_type = str(item.get("packet_type") or "")
        if not packet_type:
            continue
        row = summary.setdefault(packet_type, {"count": 0, "closed_count": 0, "open_blocking_count": 0, "decision_counts": {}})
        row["count"] += 1
        if item.get("status") == "closed":
            row["closed_count"] += 1
        if item.get("status") == "open" and item.get("basic_print_blocking"):
            row["open_blocking_count"] += 1
        decision = str(item.get("decision") or "")
        row["decision_counts"][decision] = row["decision_counts"].get(decision, 0) + 1
    return summary


def recompute_review_outcome_counts(review_outcomes: dict[str, Any]) -> None:
    decision_counts = Counter(str(item.get("decision") or "") for item in review_outcomes.get("items") or [])
    review_outcomes["decision_counts"] = dict(decision_counts)
    review_outcomes["open_blocking_count"] = sum(
        1 for item in review_outcomes.get("items") or [] if item.get("status") == "open" and item.get("basic_print_blocking")
    )
    review_outcomes["closed_count"] = sum(1 for item in review_outcomes.get("items") or [] if item.get("status") == "closed")


def apply_image_decisions(standard_dir: Path, audit: dict[str, Any]) -> dict[str, Any]:
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    review_outcomes = read_json(outcomes_path)
    outcomes_by_id = {
        str(item.get("outcome_id") or ""): item
        for item in review_outcomes.get("items") or []
        if isinstance(item, dict)
    }
    now = datetime.utcnow().isoformat() + "Z"
    applied_count = 0
    for audit_item in audit.get("items") or []:
        outcome = outcomes_by_id.get(str(audit_item.get("outcome_id") or ""))
        if not outcome or outcome.get("packet_type") != IMAGE_PACKET_TYPE:
            continue
        decision = str(audit_item.get("proposed_decision") or "needs_reconstruction")
        closed = decision in {"accepted_by_rule", "non_blocking"}
        outcome.update(
            {
                "decision": decision,
                "status": "closed" if closed else "open",
                "basic_print_blocking": not closed,
                "source_evidence_ready": bool(audit_item.get("source_crop") and audit_item.get("source_bbox")),
                "source_crop": audit_item.get("source_crop") or outcome.get("source_crop") or "",
                "source_crop_status": audit_item.get("source_crop_status") or outcome.get("source_crop_status") or "",
                "reviewer": "system:image_outcome_rule_audit",
                "reviewed_at": now,
                "notes": (
                    "Closed by Raw image_ref + source PDF crop + aspect/context rule."
                    if closed
                    else "Requires additional image reconstruction or source evidence work."
                ),
                "evidence": [
                    "image_outcome_rule_audit.json",
                    "image_visual_confirmation_packets.json",
                    audit_item.get("source_crop") or "",
                    audit_item.get("rule_id") or "",
                ],
                "next_action": audit_item.get("next_action") or next_action_for_decision(decision),
                "image_rule_audit": {
                    "rule_id": audit_item.get("rule_id"),
                    "confidence": audit_item.get("confidence"),
                    "aspect_ratio_delta": audit_item.get("aspect_ratio_delta"),
                    "context": audit_item.get("context"),
                    "issues": audit_item.get("issues") or [],
                    "standard_image_info": audit_item.get("standard_image_info") or {},
                    "source_crop_info": audit_item.get("source_crop_info") or {},
                },
            }
        )
        applied_count += 1
    recompute_review_outcome_counts(review_outcomes)
    review_outcomes["updated_at"] = now
    write_json(outcomes_path, review_outcomes)
    (standard_dir / "review_outcomes.html").write_text(build_review_outcomes_html(review_outcomes), encoding="utf-8")
    refresh_visual_outcome_review_artifacts(standard_dir)
    refresh_workbook_profile_artifacts(standard_dir)
    audit["applied"] = True
    audit["applied_at"] = now
    audit["applied_count"] = applied_count
    return review_outcomes


def update_acceptance_and_manifest(standard_dir: Path, audit: dict[str, Any], review_outcomes: dict[str, Any] | None) -> dict[str, Any]:
    acceptance_path = standard_dir / "standard_acceptance_report.json"
    manifest_path = standard_dir / "manifest.json"
    quality_path = standard_dir / "standard_quality_score.json"
    acceptance = read_json(acceptance_path)
    gates = acceptance.get("gates") if isinstance(acceptance.get("gates"), dict) else {}
    if review_outcomes:
        packet_summary = outcome_packet_type_summary(review_outcomes)
        image_summary = packet_summary.get(IMAGE_PACKET_TYPE, {})
        open_blocking_count = int(review_outcomes.get("open_blocking_count") or 0)
        open_image_count = int(image_summary.get("open_blocking_count") or 0)
        correction_log = read_json(standard_dir / "correction_log.json")
        corrections = correction_log if isinstance(correction_log, list) else []
        corrections_without_evidence = sum(1 for item in corrections if isinstance(item, dict) and not item.get("evidence"))
        gates["review_outcomes"] = {
            "status": "review" if open_blocking_count else "pass",
            "outcome_count": int(review_outcomes.get("count") or 0),
            "open_blocking_count": open_blocking_count,
            "decision_counts": review_outcomes.get("decision_counts") or {},
            "packet_type_summary": packet_summary,
        }
        image_gate = gates.get("image_visual_confirmation") if isinstance(gates.get("image_visual_confirmation"), dict) else {}
        image_gate.update(
            {
                "status": "review" if open_image_count else "pass",
                "resolved_by_review_outcomes": open_image_count == 0,
                "open_blocking_count": open_image_count,
                "decision_counts": image_summary.get("decision_counts") or {},
                "rule_audit": {
                    "decision_counts": audit.get("decision_counts") or {},
                    "confidence_counts": audit.get("confidence_counts") or {},
                },
            }
        )
        gates["image_visual_confirmation"] = image_gate
        image_relation_gate = gates.get("image_relation_integrity") if isinstance(gates.get("image_relation_integrity"), dict) else {}
        relation_blockers = image_relation_gate.get("blockers") or []
        relation_review_reasons = [
            reason
            for reason in image_relation_gate.get("review_reasons") or []
            if reason != "source_visual_check_required"
        ]
        image_relation_gate["open_image_review_outcome_count"] = open_image_count
        image_relation_gate["resolved_by_review_outcomes"] = open_image_count == 0
        image_relation_gate["review_reasons"] = relation_review_reasons
        image_relation_gate["status"] = "fail" if relation_blockers else "review" if relation_review_reasons or open_image_count else "pass"
        gates["image_relation_integrity"] = image_relation_gate
        correction_gate = gates.get("correction_evidence") if isinstance(gates.get("correction_evidence"), dict) else {}
        correction_gate["status"] = "fail" if corrections_without_evidence else "pass"
        correction_gate["correction_count"] = len(corrections)
        correction_gate["corrections_without_evidence"] = corrections_without_evidence
        gates["correction_evidence"] = correction_gate
        acceptance["gates"] = gates
        acceptance["status"] = acceptance_status(gates)
        summary = acceptance.get("summary") if isinstance(acceptance.get("summary"), dict) else {}
        summary["review_outcome_open_blocking_count"] = open_blocking_count
        summary["review_outcome_closed_count"] = int(review_outcomes.get("closed_count") or 0)
        summary["image_review_outcome_open_blocking_count"] = open_image_count
        summary["image_review_outcome_closed_count"] = int(image_summary.get("closed_count") or 0)
        summary["correction_count"] = len(corrections)
        acceptance["summary"] = summary
        quality = read_json(quality_path)
        if acceptance["status"] == "pass" and int(quality.get("score") or 0) >= 90:
            quality["status"] = "pass"
            write_json(quality_path, quality)
            acceptance["quality_score"] = {"score": quality.get("score"), "status": quality.get("status")}
    write_json(acceptance_path, acceptance)

    manifest = read_json(manifest_path)
    outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), dict) else {}
    outputs["image_outcome_rule_audit"] = "image_outcome_rule_audit.json"
    outputs["image_outcome_rule_audit_html"] = "image_outcome_rule_audit.html"
    outputs["visual_outcome_review"] = "visual_outcome_review.json"
    outputs["visual_outcome_review_html"] = "visual_outcome_review.html"
    manifest["outputs"] = outputs
    if gates:
        manifest["acceptance"] = {
            "status": acceptance.get("status"),
            "gates": {name: gate.get("status") for name, gate in gates.items() if isinstance(gate, dict)},
        }
    write_json(manifest_path, manifest)
    if (standard_dir / "standard_issue_candidates.json").exists():
        issue_audit = refresh_issue_candidate_disposition_audit_artifacts(standard_dir)
        acceptance = apply_issue_candidate_gates_to_acceptance(standard_dir, issue_audit)
    if review_outcomes:
        refreshed_manifest = read_json(manifest_path)
        crop_summary = ((refreshed_manifest.get("review_artifacts") or {}).get("visual_source_crops") or {})
        report = build_closure_report(standard_dir, acceptance, review_outcomes, crop_summary)
        write_json(standard_dir / "basic_print_closure_report.json", report)
        (standard_dir / "basic_print_closure.html").write_text(build_closure_html(report), encoding="utf-8")
    return acceptance


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify and optionally close Standard image review outcomes.")
    parser.add_argument("--standard-dir", required=True, type=Path, help="Existing standard-final directory.")
    parser.add_argument("--apply", action="store_true", help="Write proposed image decisions into standard_review_outcomes.json.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    standard_dir = args.standard_dir
    audit = build_image_outcome_rule_audit(standard_dir)
    review_outcomes = apply_image_decisions(standard_dir, audit) if args.apply else None
    write_json(standard_dir / "image_outcome_rule_audit.json", audit)
    (standard_dir / "image_outcome_rule_audit.html").write_text(build_image_outcome_rule_audit_html(audit), encoding="utf-8")
    acceptance = update_acceptance_and_manifest(standard_dir, audit, review_outcomes)
    print(
        json.dumps(
            {
                "standard_dir": str(standard_dir),
                "applied": bool(args.apply),
                "decision_counts": audit.get("decision_counts"),
                "confidence_counts": audit.get("confidence_counts"),
                "acceptance_status": acceptance.get("status"),
                "open_blocking_count": review_outcomes.get("open_blocking_count") if review_outcomes else None,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
