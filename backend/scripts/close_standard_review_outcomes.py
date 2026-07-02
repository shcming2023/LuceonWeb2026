#!/usr/bin/env python3
"""Close Standard review outcomes when deterministic source evidence is sufficient."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from standard_from_clean import (
    acceptance_status,
    add_source_pdf_crops_to_packets,
    apply_issue_candidate_gates_to_acceptance,
    build_standard_product_status,
    build_review_outcomes_html,
    load_content_table_evidence,
    load_content_text_evidence,
    normalize_review_compact_text,
    normalize_review_text,
    refresh_issue_candidate_disposition_audit_artifacts,
    refresh_visual_outcome_review_artifacts,
    refresh_workbook_profile_artifacts,
    resolve_local_source_root,
    write_json,
)

TABLE_FORMULA_PACKET_TYPES = {"table_visual_review", "formula_visual_review"}
RAW_TEXT_SEQUENCE_TYPES = {"text", "list", "aside_text"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def outcome_id_for_packet(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


def standard_raw_dir(standard_dir: Path) -> Path | None:
    manifest = read_json(standard_dir / "manifest.json")
    raw_manifest = str(manifest.get("source_raw_manifest") or "")
    if raw_manifest and Path(raw_manifest).exists():
        return Path(raw_manifest).parent
    return None


def load_raw_content_rows(raw_dir: Path | None) -> list[dict[str, Any]]:
    if not raw_dir:
        return []
    manifest = read_json(raw_dir / "manifest.json")
    content_file = str(manifest.get("content_file") or "").strip()
    source_root = resolve_local_source_root(raw_dir, str(manifest.get("source_root") or ""))
    if not content_file or not source_root:
        return []
    content_path = source_root / content_file
    if not content_path.exists():
        return []
    try:
        rows = json.loads(content_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(rows, list):
        return []
    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if isinstance(row, dict):
            copied = dict(row)
            copied["_raw_index"] = index
            normalized_rows.append(copied)
    return normalized_rows


def review_token_counter(value: str) -> Counter[str]:
    return Counter(re.findall(r"[a-z0-9]+", normalize_review_text(value)))


def counter_coverage(clean_counter: Counter[str], candidate_counter: Counter[str]) -> tuple[float, float]:
    clean_total = sum(clean_counter.values())
    candidate_total = sum(candidate_counter.values())
    if not clean_total or not candidate_total:
        return 0.0, 1.0
    covered = sum(min(count, candidate_counter.get(token, 0)) for token, count in clean_counter.items())
    extra = sum(max(count - clean_counter.get(token, 0), 0) for token, count in candidate_counter.items())
    return covered / clean_total, extra / candidate_total


def union_bbox(items: list[dict[str, Any]]) -> list[Any]:
    bboxes = [item.get("bbox") for item in items if isinstance(item.get("bbox"), list) and len(item.get("bbox")) == 4]
    if not bboxes:
        return []
    return [
        min(bbox[0] for bbox in bboxes),
        min(bbox[1] for bbox in bboxes),
        max(bbox[2] for bbox in bboxes),
        max(bbox[3] for bbox in bboxes),
    ]


def raw_row_text(row: dict[str, Any]) -> str:
    return str(row.get("table_body") or row.get("text") or row.get("content") or "")


def table_cell_compact_texts(markdown: str) -> list[str]:
    cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", markdown, flags=re.I | re.S)
    compact_cells: list[str] = []
    for cell in cells:
        compact = normalize_review_compact_text(cell)
        if compact:
            compact_cells.append(compact)
    return compact_cells


def find_text_cell_coverage_bbox_union(clean_text: str, raw_rows: list[dict[str, Any]]) -> dict[str, Any]:
    clean_cells = table_cell_compact_texts(clean_text)
    if len(clean_cells) < 6:
        return {}
    rows_by_page: dict[int, list[dict[str, Any]]] = {}
    for row in raw_rows:
        if row.get("type") not in RAW_TEXT_SEQUENCE_TYPES or row.get("page_idx") is None or not row.get("bbox"):
            continue
        compact = normalize_review_compact_text(raw_row_text(row))
        if not compact:
            continue
        copied = dict(row)
        copied["_compact_text"] = compact
        rows_by_page.setdefault(int(row["page_idx"]), []).append(copied)

    best: dict[str, Any] = {}
    best_score = -1.0
    for page_idx, page_rows in rows_by_page.items():
        page_rows = sorted(page_rows, key=lambda item: int(item.get("_raw_index") or 0))
        for start in range(len(page_rows)):
            for end in range(start, min(len(page_rows), start + 18)):
                window = page_rows[start : end + 1]
                matched_rows: list[dict[str, Any]] = []
                matched_chars = 0
                used_raw_indexes: set[int] = set()
                for cell in clean_cells:
                    row_match = next(
                        (
                            row
                            for row in window
                            if row.get("_compact_text") == cell and int(row.get("_raw_index") or -1) not in used_raw_indexes
                        ),
                        None,
                    )
                    if row_match:
                        used_raw_indexes.add(int(row_match.get("_raw_index") or -1))
                        matched_rows.append(row_match)
                        matched_chars += len(cell)
                cell_coverage = len(matched_rows) / len(clean_cells)
                char_coverage = matched_chars / max(sum(len(cell) for cell in clean_cells), 1)
                if cell_coverage < 0.9 or char_coverage < 0.9:
                    continue
                bbox = union_bbox(matched_rows)
                if not bbox:
                    continue
                bbox_area = max((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]), 1)
                score = ((cell_coverage + char_coverage) / 2) - (len(window) * 0.001) - (bbox_area * 0.00000001)
                if score > best_score:
                    best_score = score
                    best = {
                        "page_idx": page_idx,
                        "page_number": page_idx + 1,
                        "bbox": bbox,
                        "content": "\n".join(raw_row_text(row) for row in sorted(matched_rows, key=lambda item: int(item.get("_raw_index") or 0))),
                        "raw_type": "text_cell_coverage_bbox_union",
                        "img_path": "",
                        "match_rule": "raw_content_list.text_cell_coverage_bbox_union_for_manual_review",
                        "match_score": round((cell_coverage + char_coverage) / 2, 4),
                    }
    return best


def find_table_source_fallback(clean_text: str, raw_rows: list[dict[str, Any]]) -> dict[str, Any]:
    clean_compact = normalize_review_compact_text(clean_text)
    if len(clean_compact) < 80:
        return {}

    best_table: dict[str, Any] = {}
    best_table_score = 0.0
    for row in raw_rows:
        if row.get("type") != "table" or not row.get("bbox") or row.get("page_idx") is None:
            continue
        source_text = raw_row_text(row)
        source_compact = normalize_review_compact_text(source_text)
        if not source_compact:
            continue
        score = SequenceMatcher(None, clean_compact, source_compact).ratio()
        if score > best_table_score:
            best_table_score = score
            best_table = row
    if best_table and best_table_score >= 0.82:
        return {
            "page_idx": best_table.get("page_idx"),
            "page_number": int(best_table["page_idx"]) + 1,
            "bbox": best_table.get("bbox") or [],
            "content": raw_row_text(best_table),
            "raw_type": "table_near_match",
            "img_path": best_table.get("img_path") or "",
            "match_rule": "raw_content_list.table_near_match_for_manual_review",
            "match_score": round(best_table_score, 4),
        }

    cell_coverage = find_text_cell_coverage_bbox_union(clean_text, raw_rows)
    if cell_coverage:
        return cell_coverage

    clean_counter = review_token_counter(clean_text)
    if sum(clean_counter.values()) < 20:
        return {}
    rows_by_page: dict[int, list[dict[str, Any]]] = {}
    for row in raw_rows:
        if row.get("type") not in RAW_TEXT_SEQUENCE_TYPES or row.get("page_idx") is None or not row.get("bbox"):
            continue
        text = raw_row_text(row)
        if not text.strip():
            continue
        rows_by_page.setdefault(int(row["page_idx"]), []).append(row)

    best_sequence: dict[str, Any] = {}
    best_sequence_score = 0.0
    for page_idx, page_rows in rows_by_page.items():
        page_rows = sorted(page_rows, key=lambda item: int(item.get("_raw_index") or 0))
        for start in range(len(page_rows)):
            candidate_rows: list[dict[str, Any]] = []
            candidate_text_parts: list[str] = []
            for end in range(start, min(len(page_rows), start + 14)):
                candidate_rows.append(page_rows[end])
                candidate_text_parts.append(raw_row_text(page_rows[end]))
                candidate_text = "\n".join(candidate_text_parts)
                candidate_counter = review_token_counter(candidate_text)
                coverage, extra_ratio = counter_coverage(clean_counter, candidate_counter)
                if coverage >= 0.98 and extra_ratio <= 0.08:
                    score = coverage - extra_ratio - (0.001 * len(candidate_rows))
                    if score > best_sequence_score:
                        bbox = union_bbox(candidate_rows)
                        if bbox:
                            best_sequence_score = score
                            best_sequence = {
                                "page_idx": page_idx,
                                "page_number": page_idx + 1,
                                "bbox": bbox,
                                "content": candidate_text,
                                "raw_type": "text_sequence_bbox_union",
                                "img_path": "",
                                "match_rule": "raw_content_list.text_sequence_bbox_union_for_manual_review",
                                "match_score": round(score, 4),
                            }
    return best_sequence


def backfill_missing_visual_packet_source_evidence(standard_dir: Path, visual_packets: dict[str, Any]) -> dict[str, Any]:
    raw_dir = standard_raw_dir(standard_dir)
    if not raw_dir:
        return {"backfilled_count": 0, "source": "raw_manifest_missing"}
    table_evidence = load_content_table_evidence(raw_dir)
    text_evidence = load_content_text_evidence(raw_dir)
    raw_rows = load_raw_content_rows(raw_dir)
    backfilled: list[dict[str, Any]] = []
    for packet in visual_packets.get("items") or []:
        existing_manual_review_rule = str(packet.get("source_match_rule") or "").endswith("_for_manual_review")
        if packet.get("source_page_number") and packet.get("source_bbox") and not existing_manual_review_rule:
            continue
        packet_type = str(packet.get("type") or "")
        key = normalize_review_text(str(packet.get("clean_text") or ""))
        if not key:
            continue
        matches = []
        evidence: dict[str, Any] = {}
        if packet_type == "table_visual_review":
            compact_key = normalize_review_compact_text(str(packet.get("clean_text") or ""))
            matches = table_evidence.get(key) or table_evidence.get(f"compact:{compact_key}") or []
            if not matches:
                evidence = find_table_source_fallback(str(packet.get("clean_text") or ""), raw_rows)
        elif packet_type == "formula_visual_review":
            matches = text_evidence.get(key) or []
        if matches:
            evidence = matches[0]
        if not evidence:
            continue
        if evidence.get("page_number") and evidence.get("bbox"):
            packet["source_page_idx"] = evidence.get("page_idx")
            packet["source_page_number"] = evidence.get("page_number")
            packet["source_bbox"] = evidence.get("bbox") or []
            packet["source_content"] = str(evidence.get("content") or "")
            packet["source_raw_type"] = evidence.get("raw_type") or ""
            packet["source_image"] = evidence.get("img_path") or ""
            packet["source_match_rule"] = evidence.get("match_rule") or ""
            packet["source_match_score"] = evidence.get("match_score")
            packet["crop_status"] = "ready_for_source_crop" if visual_packets.get("source_pdf") else "source_pdf_missing"
            backfilled.append(
                {
                    "block_id": packet.get("block_id"),
                    "type": packet_type,
                    "source_page_number": evidence.get("page_number"),
                    "source_bbox": evidence.get("bbox") or [],
                    "source_match_rule": evidence.get("match_rule") or "raw_content_list.exact_or_compact_table_match",
                    "source_match_score": evidence.get("match_score"),
                }
            )
    return {"backfilled_count": len(backfilled), "items": backfilled}


def existing_visual_source_crop_summary(standard_dir: Path, visual_packets: dict[str, Any]) -> dict[str, Any]:
    audit = read_json(standard_dir / "visual_source_crop_audit.json")
    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else None
    if summary:
        return summary
    summary = visual_packets.get("source_crop_summary") if isinstance(visual_packets.get("source_crop_summary"), dict) else None
    return summary or {}


def close_outcomes(standard_dir: Path, *, refresh_source_crops: bool = True) -> dict[str, Any]:
    visual_path = standard_dir / "standard_visual_review_packets.json"
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    if not visual_path.exists():
        raise FileNotFoundError(f"Missing standard visual review packets: {visual_path}")
    if not outcomes_path.exists():
        raise FileNotFoundError(f"Missing standard review outcomes: {outcomes_path}")

    visual_packets = read_json(visual_path)
    review_outcomes = read_json(outcomes_path)
    if refresh_source_crops:
        backfill_summary = backfill_missing_visual_packet_source_evidence(standard_dir, visual_packets)
        crop_summary = add_source_pdf_crops_to_packets(visual_packets, standard_dir, crop_dir_name="visual_source_crops")
    else:
        backfill_summary = review_outcomes.get("source_evidence_backfill_summary") or {}
        crop_summary = existing_visual_source_crop_summary(standard_dir, visual_packets)
    packets_by_id = {outcome_id_for_packet(packet): packet for packet in visual_packets.get("items") or []}

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for item in review_outcomes.get("items") or []:
        packet = packets_by_id.get(str(item.get("outcome_id") or ""))
        if not packet or packet.get("type") not in TABLE_FORMULA_PACKET_TYPES:
            continue
        item["source_page_number"] = packet.get("source_page_number")
        item["source_bbox"] = packet.get("source_bbox") or []
        item["source_crop"] = packet.get("source_crop") or ""
        item["source_crop_status"] = packet.get("source_crop_status") or ""
        clean_text = str(packet.get("clean_text") or "")
        source_content = str(packet.get("source_content") or "")
        exact_source_match = bool(source_content) and normalize_review_text(clean_text) == normalize_review_text(source_content)
        clean_compact_text = normalize_review_compact_text(clean_text)
        source_compact_text = normalize_review_compact_text(source_content)
        compact_source_match = bool(source_content) and len(clean_compact_text) >= 40 and clean_compact_text == source_compact_text
        fallback_rule = str(packet.get("source_match_rule") or "")
        manual_review_source = fallback_rule.endswith("_for_manual_review")
        source_match = (exact_source_match or compact_source_match) and not manual_review_source
        source_match_rule = "raw_content_list.exact_normalized_match" if exact_source_match else "raw_content_list.compact_exact_match"
        crop_ready = packet.get("source_crop_status") in {"created", "reused"}
        bbox_ready = bool(packet.get("source_page_number") and packet.get("source_bbox"))
        item["source_evidence_ready"] = bool(crop_ready and bbox_ready)
        if item.get("status") == "closed" or item.get("basic_print_blocking") is False:
            continue
        if item.get("decision") == "needs_reconstruction":
            continue
        if packet.get("type") in TABLE_FORMULA_PACKET_TYPES and source_match and crop_ready and bbox_ready:
            item.update(
                {
                    "decision": "accepted_by_rule",
                    "status": "closed",
                    "basic_print_blocking": False,
                    "source_evidence_ready": True,
                    "source_page_number": packet.get("source_page_number"),
                    "source_bbox": packet.get("source_bbox") or [],
                    "source_crop": packet.get("source_crop") or "",
                    "reviewer": "system:deterministic_visual_source_match",
                    "reviewed_at": now,
                    "notes": f"Closed by {source_match_rule} plus generated source PDF crop.",
                    "evidence": [
                        "standard_visual_review_packets.json",
                        packet.get("source_crop") or "",
                        source_match_rule,
                    ],
                    "next_action": "none",
                }
            )
        elif not bbox_ready:
            item.update({"decision": "needs_page_bbox", "status": "open", "basic_print_blocking": True, "next_action": "locate_source_page_bbox"})
        elif not crop_ready:
            item.update({"decision": "needs_source_crop", "status": "open", "basic_print_blocking": True, "next_action": "generate_source_crop"})
        else:
            notes = (
                f"Source crop ready from {fallback_rule}; manual visual review required because Raw source is not an exact table match."
                if fallback_rule
                else "Source crop ready, but Raw source is not an exact table match; manual visual review required."
            )
            item.update(
                {
                    "decision": "needs_layout_fix",
                    "status": "open",
                    "basic_print_blocking": True,
                    "next_action": "manual_table_visual_review",
                    "notes": notes,
                }
            )

    decision_counts: dict[str, int] = {}
    for item in review_outcomes.get("items") or []:
        decision = str(item.get("decision") or "")
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
    review_outcomes["decision_counts"] = decision_counts
    review_outcomes["open_blocking_count"] = sum(
        1 for item in review_outcomes.get("items") or [] if item.get("status") == "open" and item.get("basic_print_blocking")
    )
    review_outcomes["closed_count"] = sum(1 for item in review_outcomes.get("items") or [] if item.get("status") == "closed")
    review_outcomes["updated_at"] = now
    review_outcomes["source_crop_summary"] = crop_summary
    review_outcomes["source_evidence_backfill_summary"] = backfill_summary

    write_json(visual_path, visual_packets)
    write_json(outcomes_path, review_outcomes)
    (standard_dir / "review_outcomes.html").write_text(build_review_outcomes_html(review_outcomes), encoding="utf-8")
    refresh_visual_outcome_review_artifacts(standard_dir)
    refresh_workbook_profile_artifacts(standard_dir)
    return {"visual_packets": visual_packets, "review_outcomes": review_outcomes, "crop_summary": crop_summary, "backfill_summary": backfill_summary}


def open_blocking_count_for_packet_types(review_outcomes: dict[str, Any], packet_types: set[str]) -> int:
    return sum(
        1
        for item in review_outcomes.get("items") or []
        if item.get("packet_type") in packet_types and item.get("status") == "open" and item.get("basic_print_blocking")
    )


def packet_type_summary(review_outcomes: dict[str, Any]) -> dict[str, Any]:
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


def update_acceptance_and_manifest(standard_dir: Path, review_outcomes: dict[str, Any], crop_summary: dict[str, Any]) -> dict[str, Any]:
    acceptance_path = standard_dir / "standard_acceptance_report.json"
    manifest_path = standard_dir / "manifest.json"
    quality_path = standard_dir / "standard_quality_score.json"
    acceptance = read_json(acceptance_path)
    gates = acceptance.get("gates") if isinstance(acceptance.get("gates"), dict) else {}
    correction_log = read_json(standard_dir / "correction_log.json")
    corrections = correction_log if isinstance(correction_log, list) else []
    corrections_without_evidence = sum(1 for item in corrections if isinstance(item, dict) and not item.get("evidence"))
    open_blocking_count = int(review_outcomes.get("open_blocking_count") or 0)
    table_formula_open_blocking_count = open_blocking_count_for_packet_types(review_outcomes, TABLE_FORMULA_PACKET_TYPES)
    packet_summary = packet_type_summary(review_outcomes)
    outcomes_gate = {
        "status": "review" if open_blocking_count else "pass",
        "outcome_count": int(review_outcomes.get("count") or 0),
        "open_blocking_count": open_blocking_count,
        "decision_counts": review_outcomes.get("decision_counts") or {},
        "packet_type_summary": packet_summary,
        "table_formula_open_blocking_count": table_formula_open_blocking_count,
        "source_crop_summary": crop_summary,
    }
    gates["review_outcomes"] = outcomes_gate
    table_formula_gate = gates.get("formula_table_integrity") if isinstance(gates.get("formula_table_integrity"), dict) else {}
    if table_formula_open_blocking_count == 0 and any(packet_type in packet_summary for packet_type in TABLE_FORMULA_PACKET_TYPES):
        table_formula_gate["status"] = "pass"
        table_formula_gate["resolved_by_review_outcomes"] = True
        table_formula_gate["open_blocking_count"] = 0
    elif any(packet_type in packet_summary for packet_type in TABLE_FORMULA_PACKET_TYPES):
        table_formula_gate["status"] = "review"
        table_formula_gate["resolved_by_review_outcomes"] = False
        table_formula_gate["open_blocking_count"] = table_formula_open_blocking_count
    gates["formula_table_integrity"] = table_formula_gate
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
    summary["table_formula_review_outcome_open_blocking_count"] = table_formula_open_blocking_count
    summary["visual_review_source_crop_count"] = int(crop_summary.get("source_crop_count") or 0)
    if "source_crop_required_count" in crop_summary:
        summary["visual_review_source_crop_required_count"] = int(crop_summary.get("source_crop_required_count") or 0)
    summary["correction_count"] = len(corrections)
    acceptance["summary"] = summary
    write_json(acceptance_path, acceptance)

    quality = read_json(quality_path)
    if acceptance["status"] == "pass" and int(quality.get("score") or 0) >= 90:
        quality["status"] = "pass"
        write_json(quality_path, quality)
        acceptance["quality_score"] = {"score": quality.get("score"), "status": quality.get("status")}
        write_json(acceptance_path, acceptance)

    manifest = read_json(manifest_path)
    outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), dict) else {}
    outputs["standard_review_outcomes"] = "standard_review_outcomes.json"
    outputs["review_outcomes_html"] = "review_outcomes.html"
    outputs["visual_outcome_review"] = "visual_outcome_review.json"
    outputs["visual_outcome_review_html"] = "visual_outcome_review.html"
    if int(crop_summary.get("source_crop_count") or 0):
        outputs["visual_source_crops"] = "visual_source_crops/"
    if (standard_dir / "formula_bbox_backfill_report.json").exists():
        outputs["formula_bbox_backfill_report"] = "formula_bbox_backfill_report.json"
    if (standard_dir / "formula_bbox_global_backfill_report.json").exists():
        outputs["formula_bbox_global_backfill_report"] = "formula_bbox_global_backfill_report.json"
    if (standard_dir / "formula_source_mismatch_audit.json").exists():
        outputs["formula_source_mismatch_audit"] = "formula_source_mismatch_audit.json"
        outputs["formula_source_mismatch_audit_html"] = "formula_source_mismatch_audit.html"
    if (standard_dir / "formula_semantic_equivalent_closure_report.json").exists():
        outputs["formula_semantic_equivalent_closure_report"] = "formula_semantic_equivalent_closure_report.json"
    if (standard_dir / "remaining_bbox_blocker_audit.json").exists():
        outputs["remaining_bbox_blocker_audit"] = "remaining_bbox_blocker_audit.json"
        outputs["remaining_bbox_blocker_audit_html"] = "remaining_bbox_blocker_audit.html"
    if (standard_dir / "raw_context_bbox_candidate_audit.json").exists():
        outputs["raw_context_bbox_candidate_audit"] = "raw_context_bbox_candidate_audit.json"
        outputs["raw_context_bbox_candidate_audit_html"] = "raw_context_bbox_candidate_audit.html"
    if (standard_dir / "raw_context_bbox_backfill_report.json").exists():
        outputs["raw_context_bbox_backfill_report"] = "raw_context_bbox_backfill_report.json"
    if (standard_dir / "image_only_formula_reclassification_report.json").exists():
        outputs["image_only_formula_reclassification_report"] = "image_only_formula_reclassification_report.json"
        outputs["image_only_formula_reclassification_html"] = "image_only_formula_reclassification.html"
    if (standard_dir / "table_source_candidate_backfill_report.json").exists():
        outputs["table_source_candidate_backfill_report"] = "table_source_candidate_backfill_report.json"
        outputs["table_source_candidate_backfill_html"] = "table_source_candidate_backfill.html"
    outputs["basic_print_closure_report"] = "basic_print_closure_report.json"
    outputs["basic_print_closure_html"] = "basic_print_closure.html"
    manifest["outputs"] = outputs
    review_artifacts = manifest.get("review_artifacts") if isinstance(manifest.get("review_artifacts"), dict) else {}
    if crop_summary:
        review_artifacts["visual_source_crops"] = crop_summary
    backfill_report = read_json(standard_dir / "formula_bbox_backfill_report.json")
    if backfill_report:
        review_artifacts["formula_bbox_backfill_report"] = {
            "mode": backfill_report.get("mode"),
            "status_counts": backfill_report.get("status_counts") or {},
            "policy": backfill_report.get("policy"),
            "audit_report": backfill_report.get("audit_report"),
        }
    global_backfill_report = read_json(standard_dir / "formula_bbox_global_backfill_report.json")
    if global_backfill_report:
        review_artifacts["formula_bbox_global_backfill_report"] = {
            "mode": global_backfill_report.get("mode"),
            "candidate_bucket": global_backfill_report.get("candidate_bucket"),
            "status_counts": global_backfill_report.get("status_counts") or {},
            "policy": global_backfill_report.get("policy"),
        }
    formula_mismatch_audit = read_json(standard_dir / "formula_source_mismatch_audit.json")
    if formula_mismatch_audit:
        review_artifacts["formula_source_mismatch_audit"] = {
            "count": formula_mismatch_audit.get("count"),
            "bucket_counts": formula_mismatch_audit.get("bucket_counts") or {},
            "deterministic_formula_semantic_equivalent_count": formula_mismatch_audit.get(
                "deterministic_formula_semantic_equivalent_count"
            ),
            "manual_review_count": formula_mismatch_audit.get("manual_review_count"),
            "policy": formula_mismatch_audit.get("policy"),
        }
    formula_semantic_closure = read_json(standard_dir / "formula_semantic_equivalent_closure_report.json")
    if formula_semantic_closure:
        review_artifacts["formula_semantic_equivalent_closure"] = {
            "mode": formula_semantic_closure.get("mode"),
            "candidate_count": formula_semantic_closure.get("candidate_count"),
            "newly_closed": formula_semantic_closure.get("newly_closed"),
            "already_closed": formula_semantic_closure.get("already_closed"),
            "policy": formula_semantic_closure.get("policy"),
            "allowed_source_rules": formula_semantic_closure.get("allowed_source_rules") or [],
        }
    remaining_bbox_audit = read_json(standard_dir / "remaining_bbox_blocker_audit.json")
    if remaining_bbox_audit:
        review_artifacts["remaining_bbox_blocker_audit"] = {
            "count": remaining_bbox_audit.get("count"),
            "packet_type_counts": remaining_bbox_audit.get("packet_type_counts") or {},
            "bucket_counts": remaining_bbox_audit.get("bucket_counts") or {},
            "recommended_action_counts": remaining_bbox_audit.get("recommended_action_counts") or {},
            "policy": remaining_bbox_audit.get("policy"),
        }
    raw_context_audit = read_json(standard_dir / "raw_context_bbox_candidate_audit.json")
    if raw_context_audit:
        review_artifacts["raw_context_bbox_candidate_audit"] = {
            "count": raw_context_audit.get("count"),
            "bucket_counts": raw_context_audit.get("bucket_counts") or {},
            "target_action": raw_context_audit.get("target_action"),
            "policy": raw_context_audit.get("policy"),
        }
    raw_context_backfill = read_json(standard_dir / "raw_context_bbox_backfill_report.json")
    if raw_context_backfill:
        review_artifacts["raw_context_bbox_backfill_report"] = {
            "mode": raw_context_backfill.get("mode"),
            "candidate_bucket": raw_context_backfill.get("candidate_bucket"),
            "source_match_rule": raw_context_backfill.get("source_match_rule"),
            "status_counts": raw_context_backfill.get("status_counts") or {},
            "policy": raw_context_backfill.get("policy"),
        }
    image_only_reclassification = read_json(standard_dir / "image_only_formula_reclassification_report.json")
    if image_only_reclassification:
        review_artifacts["image_only_formula_reclassification"] = {
            "mode": image_only_reclassification.get("mode"),
            "status_counts": image_only_reclassification.get("status_counts") or {},
            "policy": image_only_reclassification.get("policy"),
        }
    table_source_backfill = read_json(standard_dir / "table_source_candidate_backfill_report.json")
    if table_source_backfill:
        review_artifacts["table_source_candidate_backfill"] = {
            "mode": table_source_backfill.get("mode"),
            "candidate_count": table_source_backfill.get("candidate_count"),
            "status_counts": table_source_backfill.get("status_counts") or {},
            "policy": table_source_backfill.get("policy"),
        }
    manifest["review_artifacts"] = review_artifacts
    manifest["acceptance"] = {
        "status": acceptance["status"],
        "gates": {name: gate.get("status") for name, gate in gates.items() if isinstance(gate, dict)},
    }
    write_json(manifest_path, manifest)
    if (standard_dir / "standard_issue_candidates.json").exists():
        issue_audit = refresh_issue_candidate_disposition_audit_artifacts(standard_dir)
        acceptance = apply_issue_candidate_gates_to_acceptance(standard_dir, issue_audit)
    document = read_json(standard_dir / "standard_document.json")
    if document:
        product_status = build_standard_product_status(
            acceptance,
            document,
            read_json(standard_dir / "workbook_profile_report.json"),
            review_outcomes,
            read_json(standard_dir / "standard_visual_review_packets.json"),
            read_json(standard_dir / "image_visual_confirmation_packets.json"),
            crop_summary,
        )
        write_json(standard_dir / "standard_product_status.json", product_status)
        manifest = read_json(manifest_path)
        manifest["acceptance"] = {
            "status": acceptance["status"],
            "gates": {
                name: gate.get("status")
                for name, gate in (acceptance.get("gates") or {}).items()
                if isinstance(gate, dict)
            },
        }
        manifest["product_status"] = {
            "product_layer": product_status["product_layer"],
            "deliverable_use": product_status["deliverable_use"],
            "corpus_promotion_status": product_status["corpus_promotion"]["status"],
        }
        outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), dict) else {}
        outputs["standard_product_status"] = "standard_product_status.json"
        manifest["outputs"] = outputs
        write_json(manifest_path, manifest)
    return acceptance


def build_closure_report(
    standard_dir: Path,
    acceptance: dict[str, Any],
    review_outcomes: dict[str, Any],
    crop_summary: dict[str, Any],
    backfill_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fail_gates = [name for name, gate in (acceptance.get("gates") or {}).items() if isinstance(gate, dict) and gate.get("status") == "fail"]
    review_gates = [name for name, gate in (acceptance.get("gates") or {}).items() if isinstance(gate, dict) and gate.get("status") == "review"]
    basic_print_candidate = not fail_gates and not review_gates and int(review_outcomes.get("open_blocking_count") or 0) == 0
    packet_summary = packet_type_summary(review_outcomes)
    open_table_formula_items = [
        {
            "outcome_id": item.get("outcome_id"),
            "packet_type": item.get("packet_type"),
            "block_id": item.get("block_id"),
            "decision": item.get("decision"),
            "next_action": item.get("next_action"),
            "source_page_number": item.get("source_page_number"),
            "source_bbox": item.get("source_bbox") or [],
            "source_crop_status": item.get("source_crop_status") or "",
        }
        for item in review_outcomes.get("items") or []
        if item.get("packet_type") in TABLE_FORMULA_PACKET_TYPES and item.get("status") == "open" and item.get("basic_print_blocking")
    ]
    return {
        "schema": "luceon-standard-basic-print-closure/v1",
        "standard_dir": str(standard_dir),
        "status": "basic_print_candidate" if basic_print_candidate else "review",
        "basic_print_candidate": basic_print_candidate,
        "acceptance_status": acceptance.get("status"),
        "quality_score": acceptance.get("quality_score"),
        "fail_gates": fail_gates,
        "review_gates": review_gates,
        "review_outcomes": {
            "count": review_outcomes.get("count"),
            "closed_count": review_outcomes.get("closed_count"),
            "open_blocking_count": review_outcomes.get("open_blocking_count"),
            "decision_counts": review_outcomes.get("decision_counts"),
            "packet_type_summary": packet_summary,
        },
        "open_table_formula_items": open_table_formula_items,
        "source_crop_summary": crop_summary,
        "source_evidence_backfill_summary": backfill_summary or review_outcomes.get("source_evidence_backfill_summary") or {},
        "closure_rules": [
            "table accepted_by_rule requires exact normalized table match or length-gated compact exact table match against Raw content_list, source page/bbox, and generated or reused source PDF crop.",
            "Raw table near-match and Raw text-cell coverage bbox-union may backfill source page/bbox and crop for manual review, but they do not close outcomes as accepted_by_rule.",
            "formula/text accepted_by_rule requires exact normalized Raw content_list text match, source page/bbox, and generated or reused source PDF crop.",
            "table/formula packets without source page/bbox remain open as needs_page_bbox.",
            "table packets with source crop but non-matching text remain open as needs_layout_fix for manual visual review.",
            "image_source_visual_confirmation outcomes are not closed by this table/formula closure script.",
        ],
        "notes": [
            "Closure does not edit Standard content.",
            "accepted_by_rule means deterministic Raw source match plus generated/reused source crop evidence.",
        ],
    }


def build_closure_html(report: dict[str, Any]) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Basic Print Closure</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    pre {{ background: #f6f6f6; padding: 12px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Basic Print Closure</h1>
  <pre>{html.escape(json.dumps(report, ensure_ascii=False, indent=2))}</pre>
</body>
</html>
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Close Standard review outcomes using deterministic source evidence.")
    parser.add_argument("--standard-dir", required=True, type=Path, help="Existing standard-final directory.")
    parser.add_argument(
        "--skip-source-crop-refresh",
        action="store_true",
        help="Refresh outcome/acceptance/closure reports from existing crop artifacts without rendering source PDF crops.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    standard_dir = args.standard_dir
    result = close_outcomes(standard_dir, refresh_source_crops=not args.skip_source_crop_refresh)
    acceptance = update_acceptance_and_manifest(standard_dir, result["review_outcomes"], result["crop_summary"])
    report = build_closure_report(standard_dir, acceptance, result["review_outcomes"], result["crop_summary"], result["backfill_summary"])
    write_json(standard_dir / "basic_print_closure_report.json", report)
    (standard_dir / "basic_print_closure.html").write_text(build_closure_html(report), encoding="utf-8")
    print(json.dumps({"standard_dir": str(standard_dir), "status": report["status"], "open_blocking_count": result["review_outcomes"]["open_blocking_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
