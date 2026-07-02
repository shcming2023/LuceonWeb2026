#!/usr/bin/env python3
"""Generate table/formula source crops for Standard visual review outcomes."""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from standard_from_clean import (
    build_review_outcomes_html,
    refresh_visual_outcome_review_artifacts,
    refresh_workbook_profile_artifacts,
    safe_slug,
    write_json,
)

VISUAL_PACKET_TYPES = {"table_visual_review", "formula_visual_review"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def render_page(source_pdf: Path, page_number: int, temp_dir: Path, dpi: int) -> Path | None:
    prefix = temp_dir / f"source_page_{page_number}"
    completed = subprocess.run(
        [
            "pdftoppm",
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-r",
            str(dpi),
            "-png",
            str(source_pdf),
            str(prefix),
        ],
        text=True,
        capture_output=True,
        timeout=120,
    )
    if completed.returncode != 0:
        return None
    rendered = sorted(temp_dir.glob(f"{prefix.name}*.png"))
    return rendered[0] if rendered else None


def outcome_id_for_packet(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


def item_list(packet_or_outcome_doc: dict[str, Any]) -> list[dict[str, Any]]:
    items = packet_or_outcome_doc.get("items")
    return items if isinstance(items, list) else []


def crop_visual_packets(
    visual_packets: dict[str, Any],
    standard_dir: Path,
    source_pdf: Path,
    *,
    dpi: int,
    max_pages: int | None,
    only_ready_for_source_crop: bool = False,
) -> dict[str, Any]:
    if not shutil.which("pdftoppm"):
        raise RuntimeError("pdftoppm is required")
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency checked at runtime
        raise RuntimeError("Pillow is required") from exc

    crop_dir_name = "visual_source_crops"
    crop_dir = standard_dir / crop_dir_name
    crop_dir.mkdir(parents=True, exist_ok=True)
    crop_dir_ref = f"{crop_dir_name}/"
    packets = [
        (index, packet)
        for index, packet in enumerate(item_list(visual_packets), start=1)
        if isinstance(packet, dict) and packet.get("type") in VISUAL_PACKET_TYPES
    ]
    by_page: dict[int, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    status_counts: Counter[str] = Counter()
    packet_type_counts: Counter[str] = Counter()
    crop_count = 0
    page_numbers: set[int] = set()

    for index, packet in packets:
        packet_type = str(packet.get("type") or "")
        packet_type_counts[packet_type] += 1
        if only_ready_for_source_crop and packet.get("source_crop_status") != "ready_for_source_crop":
            status = str(packet.get("source_crop_status") or "not_generated")
            status_counts[status] += 1
            if status in {"created", "reused"} and packet.get("source_crop"):
                crop_count += 1
            continue
        page_number = packet.get("source_page_number")
        bbox = packet.get("source_bbox") or []
        if not isinstance(page_number, int) or len(bbox) != 4:
            packet["source_crop_status"] = "needs_page_bbox"
            status_counts["needs_page_bbox"] += 1
            continue
        block_id = safe_slug(str(packet.get("block_id") or f"packet_{index}"))
        crop_name = f"{index:04d}-{block_id}-{safe_slug(packet_type)}.png"
        crop_path = crop_dir / crop_name
        crop_ref = f"{crop_dir_ref}{crop_name}"
        if crop_path.exists():
            packet["source_crop"] = crop_ref
            packet["source_crop_status"] = "reused"
            packet["source_crop_method"] = f"pdftoppm_{dpi}dpi_normalized_bbox_0_1000_page_grouped"
            if not only_ready_for_source_crop:
                try:
                    with Image.open(crop_path) as existing_crop:
                        packet["source_crop_size"] = [existing_crop.size[0], existing_crop.size[1]]
                except Exception:
                    pass
            crop_count += 1
            status_counts["reused"] += 1
            continue
        by_page[page_number].append((index, packet))

    pages = sorted(by_page)
    if max_pages is not None:
        skipped_pages = pages[max_pages:]
        pages = pages[:max_pages]
        for page in skipped_pages:
            for _index, packet in by_page[page]:
                packet["source_crop_status"] = "deferred_by_max_pages"
                status_counts["deferred_by_max_pages"] += 1

    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="luceon-visual-crops-fast-") as temp_name:
        temp_dir = Path(temp_name)
        for page_number in pages:
            page_numbers.add(page_number)
            page_image_path = render_page(source_pdf, page_number, temp_dir, dpi)
            if not page_image_path:
                for _index, packet in by_page[page_number]:
                    packet["source_crop_status"] = "page_render_failed"
                    status_counts["page_render_failed"] += 1
                continue
            try:
                with Image.open(page_image_path) as page_image:
                    width, height = page_image.size
                    for index, packet in by_page[page_number]:
                        bbox = packet.get("source_bbox") or []
                        packet_type = str(packet.get("type") or "")
                        block_id = safe_slug(str(packet.get("block_id") or f"packet_{index}"))
                        crop_name = f"{index:04d}-{block_id}-{safe_slug(packet_type)}.png"
                        crop_path = crop_dir / crop_name
                        crop_ref = f"{crop_dir_ref}{crop_name}"
                        x0, y0, x1, y1 = [float(value) for value in bbox]
                        left = int(round(x0 / 1000.0 * width))
                        top = int(round(y0 / 1000.0 * height))
                        right = int(round(x1 / 1000.0 * width))
                        bottom = int(round(y1 / 1000.0 * height))
                        margin = max(4, int(round(min(width, height) * 0.006)))
                        left = max(0, left - margin)
                        top = max(0, top - margin)
                        right = min(width, right + margin)
                        bottom = min(height, bottom + margin)
                        if right <= left or bottom <= top:
                            packet["source_crop_status"] = "invalid_bbox"
                            status_counts["invalid_bbox"] += 1
                            continue
                        crop = page_image.crop((left, top, right, bottom))
                        crop.save(crop_path)
                        packet["source_crop"] = crop_ref
                        packet["source_crop_status"] = "created"
                        packet["source_crop_bbox_px"] = [left, top, right, bottom]
                        packet["source_crop_size"] = [right - left, bottom - top]
                        packet["source_crop_method"] = f"pdftoppm_{dpi}dpi_normalized_bbox_0_1000_page_grouped"
                        crop_count += 1
                        status_counts["created"] += 1
            except Exception as exc:
                for _index, packet in by_page[page_number]:
                    packet["source_crop_status"] = "crop_failed"
                    packet["source_crop_error"] = str(exc)[:300]
                    status_counts["crop_failed"] += 1

    for _index, packet in packets:
        if not packet.get("source_crop_status"):
            packet["source_crop_status"] = "not_generated"
            status_counts["not_generated"] += 1

    not_required_count = sum(count for status, count in status_counts.items() if status.startswith("not_required"))
    required_count = max(len(packets) - not_required_count, 0)
    summary = {
        "source_crop_generation": "generated" if crop_count == required_count else "attempted",
        "source_crop_count": crop_count,
        "source_crop_required_count": required_count,
        "source_crop_status_counts": dict(status_counts),
        "not_required_count": not_required_count,
        "packet_type_counts": dict(packet_type_counts),
        "source_crop_dir": crop_dir_ref,
        "source_crop_method": f"pdftoppm_{dpi}dpi_page_grouped_table_formula",
        "rendered_page_count": len(page_numbers),
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "max_pages": max_pages,
    }
    visual_packets["source_crop_summary"] = summary
    return summary


def sync_packets_to_outcomes(visual_packets: dict[str, Any], review_outcomes: dict[str, Any]) -> dict[str, Any]:
    packets_by_outcome = {outcome_id_for_packet(packet): packet for packet in item_list(visual_packets)}
    status_counts: Counter[str] = Counter()
    synced = 0
    for outcome in item_list(review_outcomes):
        if outcome.get("packet_type") not in VISUAL_PACKET_TYPES:
            continue
        packet = packets_by_outcome.get(str(outcome.get("outcome_id") or ""))
        if not packet:
            continue
        outcome["source_page_number"] = packet.get("source_page_number")
        outcome["source_bbox"] = packet.get("source_bbox") or []
        outcome["source_crop"] = packet.get("source_crop") or ""
        outcome["source_crop_status"] = packet.get("source_crop_status") or ""
        outcome["source_crop_size"] = packet.get("source_crop_size") or []
        outcome["source_crop_method"] = packet.get("source_crop_method") or ""
        crop_ready = packet.get("source_crop_status") in {"created", "reused"}
        bbox_ready = bool(packet.get("source_page_number") and packet.get("source_bbox"))
        outcome["source_evidence_ready"] = bool(crop_ready and bbox_ready)
        if outcome.get("status") == "closed" or outcome.get("basic_print_blocking") is False:
            pass
        elif outcome.get("decision") == "needs_reconstruction":
            pass
        elif crop_ready:
            outcome["decision"] = "needs_layout_fix"
            outcome["next_action"] = "manual_table_formula_visual_review"
            outcome["notes"] = "Source crop generated for manual visual review; outcome intentionally remains open."
        elif not bbox_ready and outcome.get("decision") == "pending":
            outcome["decision"] = "needs_page_bbox"
            outcome["next_action"] = "locate_source_page_bbox"
        elif not crop_ready and outcome.get("decision") == "pending":
            outcome["decision"] = "needs_source_crop"
            outcome["next_action"] = "generate_source_crop"
        status_counts[str(outcome.get("source_crop_status") or "")] += 1
        synced += 1
    return {"synced_outcome_count": synced, "outcome_source_crop_status_counts": dict(status_counts)}


def update_reports(standard_dir: Path, summary: dict[str, Any], sync_summary: dict[str, Any]) -> None:
    acceptance_path = standard_dir / "standard_acceptance_report.json"
    if acceptance_path.exists():
        acceptance = read_json(acceptance_path)
        gates = acceptance.get("gates") if isinstance(acceptance.get("gates"), dict) else {}
        review_gate = gates.get("review_outcomes") if isinstance(gates.get("review_outcomes"), dict) else {}
        review_gate["visual_source_crop_summary"] = summary
        review_gate["visual_source_crop_sync_summary"] = sync_summary
        gates["review_outcomes"] = review_gate
        formula_table_gate = gates.get("formula_table_integrity") if isinstance(gates.get("formula_table_integrity"), dict) else {}
        formula_table_gate["visual_source_crop_summary"] = summary
        formula_table_gate["note"] = "Source crops are review evidence only and do not close table/formula outcomes."
        gates["formula_table_integrity"] = formula_table_gate
        acceptance["gates"] = gates
        report_summary = acceptance.get("summary") if isinstance(acceptance.get("summary"), dict) else {}
        report_summary["visual_review_source_crop_count"] = summary.get("source_crop_count", 0)
        report_summary["visual_review_source_crop_required_count"] = summary.get("source_crop_required_count", 0)
        acceptance["summary"] = report_summary
        write_json(acceptance_path, acceptance)

    manifest_path = standard_dir / "manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), dict) else {}
        outputs["visual_source_crops"] = "visual_source_crops/"
        outputs["visual_source_crop_audit"] = "visual_source_crop_audit.json"
        outputs["visual_source_crop_audit_html"] = "visual_source_crop_audit.html"
        manifest["outputs"] = outputs
        review_artifacts = manifest.get("review_artifacts") if isinstance(manifest.get("review_artifacts"), dict) else {}
        review_artifacts["visual_source_crops"] = summary
        manifest["review_artifacts"] = review_artifacts
        write_json(manifest_path, manifest)


def build_audit_html(audit: dict[str, Any]) -> str:
    rows = []
    for item in (audit.get("sample_items") or [])[:300]:
        crop = str(item.get("source_crop") or "")
        crop_html = f'<img src="{html.escape(crop)}" alt="source crop">' if crop else ""
        rows.append(
            "<article>"
            f"<h2>{html.escape(str(item.get('outcome_id') or ''))}</h2>"
            f"<p><strong>Type:</strong> {html.escape(str(item.get('packet_type') or ''))} | "
            f"<strong>Status:</strong> {html.escape(str(item.get('source_crop_status') or ''))} | "
            f"<strong>Page:</strong> {html.escape(str(item.get('source_page_number') or ''))}</p>"
            f"{crop_html}"
            "</article>"
        )
    summary = json.dumps({k: v for k, v in audit.items() if k != "sample_items"}, ensure_ascii=False, indent=2)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Visual Source Crop Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    pre {{ white-space: pre-wrap; border: 1px solid #bbb; padding: 12px; }}
    article {{ break-inside: avoid; border-top: 1px solid #bbb; padding: 14px 0; }}
    img {{ max-width: 100%; border: 1px solid #ccc; background: #fff; }}
  </style>
</head>
<body>
  <h1>Visual Source Crop Audit</h1>
  <pre>{html.escape(summary)}</pre>
  {''.join(rows)}
</body>
</html>"""


def write_audit(standard_dir: Path, summary: dict[str, Any], sync_summary: dict[str, Any], review_outcomes: dict[str, Any]) -> None:
    sample_items = []
    for outcome in item_list(review_outcomes):
        if outcome.get("packet_type") in VISUAL_PACKET_TYPES:
            sample_items.append(
                {
                    "outcome_id": outcome.get("outcome_id"),
                    "packet_type": outcome.get("packet_type"),
                    "source_page_number": outcome.get("source_page_number"),
                    "source_bbox": outcome.get("source_bbox") or [],
                    "source_crop": outcome.get("source_crop") or "",
                    "source_crop_status": outcome.get("source_crop_status") or "",
                    "decision": outcome.get("decision"),
                    "status": outcome.get("status"),
                    "basic_print_blocking": outcome.get("basic_print_blocking"),
                }
            )
    audit = {
        "schema": "luceon-standard-visual-source-crop-audit/v1",
        "standard_dir": str(standard_dir),
        "policy": "source_crops_are_review_evidence_only_no_automatic_acceptance",
        "summary": summary,
        "sync_summary": sync_summary,
        "sample_items": sample_items,
    }
    write_json(standard_dir / "visual_source_crop_audit.json", audit)
    (standard_dir / "visual_source_crop_audit.html").write_text(build_audit_html(audit), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--source-pdf", required=True, type=Path)
    parser.add_argument("--dpi", type=int, default=180)
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--only-ready-for-source-crop", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    standard_dir = args.standard_dir
    visual_path = standard_dir / "standard_visual_review_packets.json"
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    if not visual_path.exists():
        print(f"Missing standard visual review packets: {visual_path}", file=sys.stderr)
        return 1
    if not outcomes_path.exists():
        print(f"Missing standard review outcomes: {outcomes_path}", file=sys.stderr)
        return 1
    source_pdf = args.source_pdf.resolve()
    visual_packets = read_json(visual_path)
    review_outcomes = read_json(outcomes_path)
    visual_packets["source_pdf"] = str(source_pdf)
    visual_packets["source_pdf_available"] = source_pdf.exists()
    for packet in item_list(visual_packets):
        if packet.get("type") in VISUAL_PACKET_TYPES:
            packet["source_pdf"] = str(source_pdf)
            packet["source_pdf_available"] = source_pdf.exists()
    summary = crop_visual_packets(
        visual_packets,
        standard_dir,
        source_pdf,
        dpi=args.dpi,
        max_pages=args.max_pages,
        only_ready_for_source_crop=args.only_ready_for_source_crop,
    )
    sync_summary = sync_packets_to_outcomes(visual_packets, review_outcomes)
    write_json(visual_path, visual_packets)
    write_json(outcomes_path, review_outcomes)
    (standard_dir / "review_outcomes.html").write_text(build_review_outcomes_html(review_outcomes), encoding="utf-8")
    refresh_visual_outcome_review_artifacts(standard_dir)
    refresh_workbook_profile_artifacts(standard_dir)
    update_reports(standard_dir, summary, sync_summary)
    write_audit(standard_dir, summary, sync_summary, review_outcomes)
    print(json.dumps({"standard_dir": str(standard_dir), **summary, **sync_summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
