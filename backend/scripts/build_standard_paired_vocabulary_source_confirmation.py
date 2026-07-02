#!/usr/bin/env python3
"""Build source visual confirmation packets for paired vocabulary table candidates."""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from audit_standard_workbook_relation_gap_patterns import block_text, read_json  # noqa: E402
from standard_from_clean import safe_slug, write_json


def item_list(doc: dict[str, Any]) -> list[dict[str, Any]]:
    items = doc.get("items")
    return items if isinstance(items, list) else []


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


def merge_bbox(*bboxes: list[Any]) -> list[float]:
    values = []
    for bbox in bboxes:
        if isinstance(bbox, list) and len(bbox) == 4:
            values.append([float(value) for value in bbox])
    if not values:
        return []
    return [
        min(value[0] for value in values),
        min(value[1] for value in values),
        max(value[2] for value in values),
        max(value[3] for value in values),
    ]


def expanded_context_bbox(item: dict[str, Any], current_packet: dict[str, Any], previous_packet: dict[str, Any] | None) -> list[float]:
    current = current_packet.get("source_bbox") or []
    if item.get("layout_bucket") == "two_table_vocabulary_definition_pair" and previous_packet:
        bbox = merge_bbox(previous_packet.get("source_bbox") or [], current)
        if bbox:
            bbox[0] = max(0.0, bbox[0] - 20.0)
            bbox[2] = min(1000.0, bbox[2] + 20.0)
            return bbox
    if isinstance(current, list) and len(current) == 4:
        x0, y0, x1, y1 = [float(value) for value in current]
        return [max(0.0, x0 - 20.0), max(0.0, y0 - 185.0), min(1000.0, x1 + 20.0), min(1000.0, y1 + 40.0)]
    return []


def crop_context(
    source_pdf: Path,
    page_number: int,
    bbox: list[float],
    output_path: Path,
    *,
    dpi: int,
) -> dict[str, Any]:
    if not shutil.which("pdftoppm"):
        return {"status": "render_tool_missing"}
    if len(bbox) != 4:
        return {"status": "missing_bbox"}
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency checked at runtime
        return {"status": "pillow_missing", "error": str(exc)}
    with tempfile.TemporaryDirectory(prefix="luceon-paired-vocab-source-") as temp_name:
        page_path = render_page(source_pdf, page_number, Path(temp_name), dpi)
        if not page_path:
            return {"status": "page_render_failed"}
        with Image.open(page_path) as page_image:
            width, height = page_image.size
            x0, y0, x1, y1 = bbox
            left = max(0, int(round(x0 / 1000.0 * width)))
            top = max(0, int(round(y0 / 1000.0 * height)))
            right = min(width, int(round(x1 / 1000.0 * width)))
            bottom = min(height, int(round(y1 / 1000.0 * height)))
            if right <= left or bottom <= top:
                return {"status": "invalid_bbox", "crop_bbox_px": [left, top, right, bottom]}
            output_path.parent.mkdir(parents=True, exist_ok=True)
            page_image.crop((left, top, right, bottom)).save(output_path)
            return {
                "status": "created",
                "crop_bbox_px": [left, top, right, bottom],
                "crop_size": [right - left, bottom - top],
                "method": f"pdftoppm_{dpi}dpi_expanded_context_bbox",
            }


def build_confirmation(standard_dir: Path, source_pdf: Path, *, dpi: int) -> dict[str, Any]:
    paired = read_json(standard_dir / "workbook_paired_vocabulary_table_layout_audit.json")
    packets = read_json(standard_dir / "standard_visual_review_packets.json")
    document = read_json(standard_dir / "standard_document.json")
    packet_by_block = {
        str(packet.get("block_id") or ""): packet
        for packet in item_list(packets)
        if packet.get("type") == "table_visual_review"
    }
    blocks = document.get("blocks") if isinstance(document.get("blocks"), list) else []
    block_by_id = {str(block.get("id") or ""): block for block in blocks}
    crop_dir = standard_dir / "paired_vocabulary_source_context_crops"
    crop_dir.mkdir(parents=True, exist_ok=True)

    records = []
    status_counts: dict[str, int] = {}
    layout_counts: dict[str, int] = {}
    for item in paired.get("items") or []:
        block_id = str(item.get("block_id") or "")
        current_packet = packet_by_block.get(block_id) or {}
        previous_block_id = str(((item.get("previous_block") or {}).get("id")) or "")
        previous_packet = packet_by_block.get(previous_block_id)
        source_page_number = current_packet.get("source_page_number")
        context_bbox = expanded_context_bbox(item, current_packet, previous_packet)
        crop_ref = ""
        crop_result = {"status": "missing_page_or_bbox"}
        if isinstance(source_page_number, int) and context_bbox:
            crop_name = f"{safe_slug(block_id)}-{safe_slug(str(item.get('layout_bucket') or 'layout'))}.png"
            crop_path = crop_dir / crop_name
            crop_ref = f"{crop_dir.name}/{crop_name}"
            if crop_path.exists():
                crop_result = {"status": "reused"}
            else:
                crop_result = crop_context(source_pdf, source_page_number, context_bbox, crop_path, dpi=dpi)
        status = str(crop_result.get("status") or "")
        status_counts[status] = status_counts.get(status, 0) + 1
        layout = str(item.get("layout_bucket") or "")
        layout_counts[layout] = layout_counts.get(layout, 0) + 1
        records.append(
            {
                "block_id": block_id,
                "layout_bucket": layout,
                "readiness": item.get("readiness"),
                "source_page_number": source_page_number,
                "current_table_source_bbox": current_packet.get("source_bbox") or [],
                "previous_table_block_id": previous_block_id if previous_packet else "",
                "previous_table_source_bbox": (previous_packet or {}).get("source_bbox") or [],
                "context_bbox": context_bbox,
                "source_context_crop": crop_ref if crop_result.get("status") in {"created", "reused"} else "",
                "source_context_crop_status": status,
                "source_context_crop_result": crop_result,
                "existing_table_source_crop": current_packet.get("source_crop") or "",
                "previous_table_source_crop": (previous_packet or {}).get("source_crop") or "",
                "heading_path": item.get("heading_path") or [],
                "word_bank_count": item.get("word_bank_count"),
                "word_bank_blocks": item.get("word_bank_blocks") or [],
                "standard_previous_text": block_text(block_by_id.get(previous_block_id))[:500],
                "standard_table_text": block_text(block_by_id.get(block_id))[:1200],
            }
        )

    source_crop_ready = sum(1 for record in records if record.get("source_context_crop_status") in {"created", "reused"})
    return {
        "schema": "luceon-standard-paired-vocabulary-source-confirmation/v1",
        "standard_dir": str(standard_dir),
        "source_pdf": str(source_pdf),
        "policy": "review_packet_only_no_gate_closure",
        "decision_boundary": (
            "This packet provides expanded source-PDF visual evidence for paired/vocabulary table layout candidates. "
            "It does not attach tables, close relation gaps, or change Standard acceptance."
        ),
        "source_layout_audit": "workbook_paired_vocabulary_table_layout_audit.json",
        "record_count": len(records),
        "layout_bucket_counts": layout_counts,
        "source_context_crop_ready_count": source_crop_ready,
        "source_context_crop_status_counts": status_counts,
        "candidate_rule_verdict": "source_visual_confirmation_ready_for_manual_review",
        "records": records,
    }


def build_html(report: dict[str, Any]) -> str:
    summary = json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2)
    rows = []
    for record in report.get("records") or []:
        context_crop = str(record.get("source_context_crop") or "")
        table_crop = str(record.get("existing_table_source_crop") or "")
        previous_crop = str(record.get("previous_table_source_crop") or "")
        word_bank = "; ".join(str(block.get("text") or "") for block in record.get("word_bank_blocks") or [])
        rows.append(
            "<article>"
            f"<h2>{html.escape(str(record.get('block_id') or ''))} - {html.escape(str(record.get('layout_bucket') or ''))}</h2>"
            f"<p><strong>Page:</strong> {html.escape(str(record.get('source_page_number') or ''))} | "
            f"<strong>Status:</strong> {html.escape(str(record.get('source_context_crop_status') or ''))}</p>"
            f"<p><strong>Heading:</strong> {html.escape(' > '.join(record.get('heading_path') or []))}</p>"
            f"<p><strong>Word bank:</strong> {html.escape(word_bank)}</p>"
            f"<div class=\"images\">"
            f"<section><h3>Expanded Source Context</h3>{'<img src=\"' + html.escape(context_crop) + '\" alt=\"expanded source context\">' if context_crop else '<p>No context crop.</p>'}</section>"
            f"<section><h3>Current Table Crop</h3>{'<img src=\"' + html.escape(table_crop) + '\" alt=\"table source crop\">' if table_crop else '<p>No table crop.</p>'}</section>"
            f"<section><h3>Previous Table Crop</h3>{'<img src=\"' + html.escape(previous_crop) + '\" alt=\"previous table source crop\">' if previous_crop else '<p>No previous table crop.</p>'}</section>"
            f"</div>"
            f"<details><summary>Standard table text</summary><pre>{html.escape(str(record.get('standard_table_text') or ''))}</pre></details>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paired Vocabulary Source Confirmation</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    pre {{ white-space: pre-wrap; border: 1px solid #bbb; padding: 12px; }}
    article {{ break-inside: avoid; border-top: 1px solid #bbb; padding: 18px 0; }}
    .images {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; align-items: start; }}
    img {{ max-width: 100%; border: 1px solid #ccc; background: #fff; }}
    h3 {{ font-size: 14px; margin: 8px 0; }}
  </style>
</head>
<body>
  <h1>Paired Vocabulary Source Confirmation</h1>
  <pre>{html.escape(summary)}</pre>
  {''.join(rows)}
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--source-pdf", required=True, type=Path)
    parser.add_argument("--dpi", type=int, default=180)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_confirmation(args.standard_dir, args.source_pdf, dpi=args.dpi)
    write_json(args.standard_dir / "paired_vocabulary_source_confirmation.json", report)
    (args.standard_dir / "paired_vocabulary_source_confirmation.html").write_text(build_html(report), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
