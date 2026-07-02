#!/usr/bin/env python3
"""Generate image source crops with page-grouped rendering for large workbooks."""

from __future__ import annotations

import argparse
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
    build_image_visual_confirmation_html,
    build_review_outcomes_html,
    refresh_visual_outcome_review_artifacts,
    refresh_workbook_profile_artifacts,
    safe_slug,
    sync_image_visual_crops_to_review_outcomes,
    write_json,
)


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


def update_manifest(standard_dir: Path, summary: dict[str, Any]) -> None:
    manifest_path = standard_dir / "manifest.json"
    manifest = read_json(manifest_path)
    if not manifest:
        return
    outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), dict) else {}
    outputs["source_crops"] = "source_crops/"
    outputs["image_visual_confirmation_packets"] = "image_visual_confirmation_packets.json"
    outputs["visual_outcome_review"] = "visual_outcome_review.json"
    outputs["visual_outcome_review_html"] = "visual_outcome_review.html"
    manifest["outputs"] = outputs
    review_artifacts = manifest.get("review_artifacts") if isinstance(manifest.get("review_artifacts"), dict) else {}
    review_artifacts["source_crops"] = summary
    manifest["review_artifacts"] = review_artifacts
    write_json(manifest_path, manifest)


def update_reports(standard_dir: Path, summary: dict[str, Any], packets: dict[str, Any]) -> None:
    acceptance_path = standard_dir / "standard_acceptance_report.json"
    if acceptance_path.exists():
        acceptance = read_json(acceptance_path)
        gates = acceptance.get("gates") if isinstance(acceptance.get("gates"), dict) else {}
        image_gate = gates.get("image_visual_confirmation") if isinstance(gates.get("image_visual_confirmation"), dict) else {}
        image_gate["source_crop_summary"] = summary
        image_gate["crop_status_counts"] = packets.get("crop_status_counts") or summary.get("source_crop_status_counts") or {}
        gates["image_visual_confirmation"] = image_gate
        acceptance["gates"] = gates
        report_summary = acceptance.get("summary") if isinstance(acceptance.get("summary"), dict) else {}
        report_summary["image_visual_confirmation_source_crop_count"] = summary.get("source_crop_count", 0)
        acceptance["summary"] = report_summary
        write_json(acceptance_path, acceptance)

    layout_path = standard_dir / "layout_report.json"
    if layout_path.exists():
        layout = read_json(layout_path)
        image_summary = (
            layout.get("image_visual_confirmation_summary")
            if isinstance(layout.get("image_visual_confirmation_summary"), dict)
            else {}
        )
        image_summary["source_crop_summary"] = summary
        layout["image_visual_confirmation_summary"] = image_summary
        write_json(layout_path, layout)


def crop_packets(
    packets: dict[str, Any],
    standard_dir: Path,
    source_pdf: Path,
    *,
    dpi: int,
    max_pages: int | None,
) -> dict[str, Any]:
    if not shutil.which("pdftoppm"):
        raise RuntimeError("pdftoppm is required")
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency checked at runtime
        raise RuntimeError("Pillow is required") from exc

    items = packets.get("items") if isinstance(packets.get("items"), list) else []
    crop_dir_name = "source_crops"
    crop_dir = standard_dir / crop_dir_name
    crop_dir.mkdir(parents=True, exist_ok=True)
    crop_dir_ref = f"{crop_dir_name}/"
    by_page: dict[int, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    status_counts: Counter[str] = Counter()
    crop_count = 0
    page_numbers: set[int] = set()

    for index, item in enumerate(items, start=1):
        page_number = item.get("source_page_number")
        bbox = item.get("source_bbox") or []
        if not isinstance(page_number, int) or len(bbox) != 4:
            item["source_crop_status"] = "needs_page_bbox"
            status_counts["needs_page_bbox"] += 1
            continue
        block_id = safe_slug(str(item.get("block_id") or f"packet_{index}"))
        category = safe_slug(str(item.get("category") or "image"))
        crop_name = f"{index:04d}-{block_id}-{category}.png"
        crop_path = crop_dir / crop_name
        crop_ref = f"{crop_dir_ref}{crop_name}"
        if crop_path.exists():
            item["source_crop"] = crop_ref
            item["source_crop_status"] = "reused"
            item["source_crop_method"] = f"pdftoppm_{dpi}dpi_normalized_bbox_0_1000_page_grouped"
            try:
                with Image.open(crop_path) as existing_crop:
                    item["source_crop_size"] = [existing_crop.size[0], existing_crop.size[1]]
            except Exception:
                pass
            crop_count += 1
            status_counts["reused"] += 1
            continue
        by_page[page_number].append((index, item))

    pages = sorted(by_page)
    if max_pages is not None:
        skipped_pages = pages[max_pages:]
        pages = pages[:max_pages]
        skipped_items = sum(len(by_page[page]) for page in skipped_pages)
        status_counts["deferred_by_max_pages"] += skipped_items
        for page in skipped_pages:
            for _index, item in by_page[page]:
                item["source_crop_status"] = "deferred_by_max_pages"

    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="luceon-image-crops-fast-") as temp_name:
        temp_dir = Path(temp_name)
        for page_number in pages:
            page_numbers.add(page_number)
            page_image_path = render_page(source_pdf, page_number, temp_dir, dpi)
            if not page_image_path:
                for _index, item in by_page[page_number]:
                    item["source_crop_status"] = "page_render_failed"
                    status_counts["page_render_failed"] += 1
                continue
            try:
                with Image.open(page_image_path) as page_image:
                    width, height = page_image.size
                    for index, item in by_page[page_number]:
                        bbox = item.get("source_bbox") or []
                        block_id = safe_slug(str(item.get("block_id") or f"packet_{index}"))
                        category = safe_slug(str(item.get("category") or "image"))
                        crop_name = f"{index:04d}-{block_id}-{category}.png"
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
                            item["source_crop_status"] = "invalid_bbox"
                            status_counts["invalid_bbox"] += 1
                            continue
                        crop = page_image.crop((left, top, right, bottom))
                        crop.save(crop_path)
                        item["source_crop"] = crop_ref
                        item["source_crop_status"] = "created"
                        item["source_crop_bbox_px"] = [left, top, right, bottom]
                        item["source_crop_size"] = [right - left, bottom - top]
                        item["source_crop_method"] = f"pdftoppm_{dpi}dpi_normalized_bbox_0_1000_page_grouped"
                        crop_count += 1
                        status_counts["created"] += 1
            except Exception as exc:
                for _index, item in by_page[page_number]:
                    item["source_crop_status"] = "crop_failed"
                    item["source_crop_error"] = str(exc)[:300]
                    status_counts["crop_failed"] += 1

    for item in items:
        if not item.get("source_crop_status"):
            item["source_crop_status"] = "not_generated"
            status_counts["not_generated"] += 1

    summary = {
        "source_crop_generation": "generated" if crop_count == len(items) else "attempted",
        "source_crop_count": crop_count,
        "source_crop_status_counts": dict(status_counts),
        "source_crop_dir": crop_dir_ref,
        "source_crop_method": f"pdftoppm_{dpi}dpi_page_grouped_image_only",
        "rendered_page_count": len(page_numbers),
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "max_pages": max_pages,
    }
    packets["source_crop_summary"] = summary
    packets["crop_status_counts"] = dict(Counter(str(item.get("source_crop_status") or "") for item in items))
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--source-pdf", required=True, type=Path)
    parser.add_argument("--dpi", type=int, default=180)
    parser.add_argument("--max-pages", type=int)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    standard_dir = args.standard_dir
    packets_path = standard_dir / "image_visual_confirmation_packets.json"
    if not packets_path.exists():
        print(f"Missing image visual confirmation packets: {packets_path}", file=sys.stderr)
        return 1
    packets = read_json(packets_path)
    source_pdf = args.source_pdf.resolve()
    packets["source_pdf"] = str(source_pdf)
    packets["source_pdf_available"] = source_pdf.exists()
    for item in packets.get("items") or []:
        item["source_pdf"] = str(source_pdf)
        item["source_pdf_available"] = source_pdf.exists()
    summary = crop_packets(packets, standard_dir, source_pdf, dpi=args.dpi, max_pages=args.max_pages)
    write_json(packets_path, packets)
    (standard_dir / "image_visual_confirmation.html").write_text(build_image_visual_confirmation_html(packets), encoding="utf-8")

    outcomes_path = standard_dir / "standard_review_outcomes.json"
    if outcomes_path.exists():
        review_outcomes = read_json(outcomes_path)
        sync_image_visual_crops_to_review_outcomes(packets, review_outcomes)
        write_json(outcomes_path, review_outcomes)
        (standard_dir / "review_outcomes.html").write_text(build_review_outcomes_html(review_outcomes), encoding="utf-8")
        refresh_visual_outcome_review_artifacts(standard_dir)

    update_manifest(standard_dir, summary)
    update_reports(standard_dir, summary, packets)
    refresh_workbook_profile_artifacts(standard_dir)
    print(json.dumps({"standard_dir": str(standard_dir), **summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
