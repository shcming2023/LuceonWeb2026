#!/usr/bin/env python3
"""Backfill source page/bbox for table review outcomes from Raw table bodies."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from standard_from_clean import (
    normalize_review_compact_text,
    refresh_visual_outcome_review_artifacts,
    refresh_workbook_profile_artifacts,
    resolve_local_source_root,
    write_json,
)


TABLE_PACKET_TYPE = "table_visual_review"
TABLE_RE = re.compile(r"<table\b.*?</table>", re.I | re.S)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def raw_row_text(row: dict[str, Any]) -> str:
    return str(row.get("table_body") or row.get("text") or row.get("content") or "")


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
    rows = json.loads(content_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if isinstance(row, dict):
            copied = dict(row)
            copied["_raw_index"] = index
            normalized.append(copied)
    return normalized


def table_compact_candidates(clean_text: str) -> list[str]:
    tables = TABLE_RE.findall(clean_text)
    values = tables or [clean_text]
    candidates: list[str] = []
    for value in values:
        compact = normalize_review_compact_text(value)
        if compact and compact not in candidates:
            candidates.append(compact)
    return candidates


def build_raw_table_index(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        if row.get("type") != "table" or row.get("page_idx") is None or not row.get("bbox"):
            continue
        text = raw_row_text(row)
        compact = normalize_review_compact_text(text)
        if not compact:
            continue
        rows.append(
            {
                "raw_index": row.get("_raw_index"),
                "page_idx": row.get("page_idx"),
                "page_number": int(row["page_idx"]) + 1,
                "bbox": row.get("bbox") or [],
                "content": text,
                "compact": compact,
                "raw_type": row.get("type"),
                "img_path": row.get("img_path") or "",
            }
        )
    return rows


def find_table_source_candidate(clean_text: str, raw_tables: list[dict[str, Any]]) -> dict[str, Any]:
    clean_candidates = table_compact_candidates(clean_text)
    if not clean_candidates:
        return {}
    matches: list[dict[str, Any]] = []
    for clean_compact in clean_candidates:
        for raw in raw_tables:
            raw_compact = str(raw.get("compact") or "")
            if raw_compact == clean_compact:
                matches.append({**raw, "match_rule": "raw_content_list.table_body_compact_exact_for_manual_review", "match_score": 1.0})
            elif len(clean_compact) >= 20 and raw_compact and raw_compact in clean_compact:
                coverage = len(raw_compact) / max(len(clean_compact), 1)
                if coverage >= 0.85:
                    matches.append(
                        {
                            **raw,
                            "match_rule": "raw_content_list.table_body_compact_contained_for_manual_review",
                            "match_score": round(coverage, 4),
                        }
                    )
    if not matches:
        return {}
    matches.sort(key=lambda item: (float(item.get("match_score") or 0), -int(item.get("raw_index") or 0)), reverse=True)
    best = matches[0]
    return {
        "page_idx": best.get("page_idx"),
        "page_number": best.get("page_number"),
        "bbox": best.get("bbox") or [],
        "content": best.get("content") or "",
        "raw_type": best.get("raw_type") or "table",
        "img_path": best.get("img_path") or "",
        "match_rule": best.get("match_rule"),
        "match_score": best.get("match_score"),
        "raw_index": best.get("raw_index"),
        "candidate_count": len(matches),
    }


def summarize_review_outcomes(review_outcomes: dict[str, Any]) -> None:
    items = review_outcomes.get("items") or []
    review_outcomes["decision_counts"] = dict(Counter(str(item.get("decision") or "") for item in items))
    review_outcomes["open_blocking_count"] = sum(
        1 for item in items if item.get("status") == "open" and item.get("basic_print_blocking")
    )
    review_outcomes["closed_count"] = sum(1 for item in items if item.get("status") == "closed")


def backfill_table_sources(standard_dir: Path, *, apply: bool) -> dict[str, Any]:
    raw_tables = build_raw_table_index(load_raw_content_rows(standard_raw_dir(standard_dir)))
    visual_packets = read_json(standard_dir / "standard_visual_review_packets.json")
    review_outcomes = read_json(standard_dir / "standard_review_outcomes.json")
    packets_by_id = {
        f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}": packet
        for packet in visual_packets.get("items") or []
        if isinstance(packet, dict)
    }
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    items: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for outcome in review_outcomes.get("items") or []:
        if outcome.get("packet_type") != TABLE_PACKET_TYPE:
            continue
        if outcome.get("status") != "open" or outcome.get("decision") not in {"needs_page_bbox", "needs_source_crop"}:
            continue
        oid = str(outcome.get("outcome_id") or "")
        packet = packets_by_id.get(oid) or {}
        if outcome.get("source_page_number") and outcome.get("source_bbox"):
            evidence = {
                "page_idx": outcome.get("source_page_idx"),
                "page_number": outcome.get("source_page_number"),
                "bbox": outcome.get("source_bbox") or [],
                "content": outcome.get("source_content") or packet.get("source_content") or "",
                "raw_type": outcome.get("source_raw_type") or packet.get("source_raw_type") or "table",
                "img_path": outcome.get("source_image") or packet.get("source_image") or "",
                "match_rule": outcome.get("source_match_rule") or packet.get("source_match_rule") or "raw_content_list.table_body_compact_match_for_manual_review",
                "match_score": outcome.get("source_match_score") or packet.get("source_match_score"),
                "raw_index": None,
                "candidate_count": 1,
            }
        else:
            evidence = find_table_source_candidate(str(packet.get("clean_text") or ""), raw_tables)
        if not evidence:
            skipped.append({"outcome_id": oid, "block_id": outcome.get("block_id"), "reason": "no_raw_table_body_match"})
            continue
        item = {
            "outcome_id": oid,
            "block_id": outcome.get("block_id"),
            "source_page_number": evidence.get("page_number"),
            "source_bbox": evidence.get("bbox") or [],
            "source_match_rule": evidence.get("match_rule"),
            "source_match_score": evidence.get("match_score"),
            "raw_index": evidence.get("raw_index"),
            "candidate_count": evidence.get("candidate_count"),
        }
        items.append(item)
        if apply:
            for target in (packet, outcome):
                target["source_page_idx"] = evidence.get("page_idx")
                target["source_page_number"] = evidence.get("page_number")
                target["source_bbox"] = evidence.get("bbox") or []
                target["source_content"] = str(evidence.get("content") or "")
                target["source_raw_type"] = evidence.get("raw_type") or ""
                target["source_image"] = evidence.get("img_path") or ""
                target["source_match_rule"] = evidence.get("match_rule") or ""
                target["source_match_score"] = evidence.get("match_score")
            packet["crop_status"] = "ready_for_source_crop"
            packet["source_crop_status"] = "ready_for_source_crop"
            packet["source_crop"] = ""
            outcome.update(
                {
                    "decision": "needs_source_crop",
                    "status": "open",
                    "basic_print_blocking": True,
                    "source_crop_status": "ready_for_source_crop",
                    "source_evidence_ready": False,
                    "reviewer": "system:table_source_locator",
                    "reviewed_at": now,
                    "notes": "Raw table source page/bbox located; source crop generation and manual visual review still required.",
                    "evidence": [
                        "standard_visual_review_packets.json",
                        evidence.get("match_rule") or "",
                    ],
                    "next_action": "generate_source_crop",
                }
            )
    if apply:
        summarize_review_outcomes(review_outcomes)
        review_outcomes["updated_at"] = now
        review_outcomes["table_source_backfill_summary"] = {"backfilled_count": len(items), "status": "applied"}
        write_json(standard_dir / "standard_visual_review_packets.json", visual_packets)
        write_json(standard_dir / "standard_review_outcomes.json", review_outcomes)
        refresh_visual_outcome_review_artifacts(standard_dir)
        refresh_workbook_profile_artifacts(standard_dir)
    report = {
        "schema": "luceon-standard-table-source-candidate-backfill/v1",
        "standard_dir": str(standard_dir),
        "mode": "apply" if apply else "dry_run",
        "policy": "backfill_raw_table_body_compact_match_for_manual_review_only",
        "status_counts": {"backfilled": len(items)} if apply else {"candidate": len(items)},
        "candidate_count": len(items),
        "skipped_count": len(skipped),
        "items": items,
        "skipped_items": skipped,
        "notes": [
            "This locates table source page/bbox only.",
            "It does not close table outcomes as accepted_by_rule.",
            "Generated source crops and manual visual review remain required.",
        ],
    }
    if apply:
        write_json(standard_dir / "table_source_candidate_backfill_report.json", report)
        (standard_dir / "table_source_candidate_backfill.html").write_text(build_html(report), encoding="utf-8")
    return report


def build_html(report: dict[str, Any]) -> str:
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Table Source Candidate Backfill</title></head>
<body><pre>{html.escape(json.dumps(report, ensure_ascii=False, indent=2))}</pre></body>
</html>
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill table visual review source candidates.")
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = backfill_table_sources(args.standard_dir, apply=args.apply)
    print(json.dumps({"mode": report["mode"], "candidate_count": report["candidate_count"], "status_counts": report["status_counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
