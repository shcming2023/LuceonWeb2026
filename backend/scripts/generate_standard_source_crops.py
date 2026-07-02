#!/usr/bin/env python3
"""Generate optional source PDF crop artifacts for an existing Standard package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from standard_from_clean import (
    add_source_pdf_crops_to_packets,
    build_image_visual_confirmation_html,
    build_review_outcomes_html,
    refresh_visual_outcome_review_artifacts,
    refresh_workbook_profile_artifacts,
    sync_image_visual_crops_to_review_outcomes,
    write_json,
)


def update_manifest(standard_dir: Path, summary: dict[str, object]) -> None:
    manifest_path = standard_dir / "manifest.json"
    if not manifest_path.exists() or not summary.get("source_crop_count"):
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), dict) else {}
    outputs["source_crops"] = "source_crops/"
    outputs["visual_outcome_review"] = "visual_outcome_review.json"
    outputs["visual_outcome_review_html"] = "visual_outcome_review.html"
    manifest["outputs"] = outputs
    review_artifacts = manifest.get("review_artifacts") if isinstance(manifest.get("review_artifacts"), dict) else {}
    review_artifacts["source_crops"] = summary
    manifest["review_artifacts"] = review_artifacts
    write_json(manifest_path, manifest)


def update_reports(standard_dir: Path, summary: dict[str, object]) -> None:
    acceptance_path = standard_dir / "standard_acceptance_report.json"
    if acceptance_path.exists():
        acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
        gates = acceptance.get("gates") if isinstance(acceptance.get("gates"), dict) else {}
        image_gate = gates.get("image_visual_confirmation") if isinstance(gates.get("image_visual_confirmation"), dict) else {}
        image_gate["source_crop_summary"] = summary
        gates["image_visual_confirmation"] = image_gate
        acceptance["gates"] = gates
        report_summary = acceptance.get("summary") if isinstance(acceptance.get("summary"), dict) else {}
        report_summary["image_visual_confirmation_source_crop_count"] = summary.get("source_crop_count", 0)
        acceptance["summary"] = report_summary
        write_json(acceptance_path, acceptance)

    layout_path = standard_dir / "layout_report.json"
    if layout_path.exists():
        layout = json.loads(layout_path.read_text(encoding="utf-8"))
        image_summary = (
            layout.get("image_visual_confirmation_summary")
            if isinstance(layout.get("image_visual_confirmation_summary"), dict)
            else {}
        )
        image_summary["source_crop_summary"] = summary
        layout["image_visual_confirmation_summary"] = image_summary
        write_json(layout_path, layout)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate source PDF crops for a standard-final review package.")
    parser.add_argument("--standard-dir", required=True, type=Path, help="Existing standard-final directory.")
    parser.add_argument("--source-pdf", type=Path, help="Optional source PDF override.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    standard_dir = args.standard_dir
    packets_path = standard_dir / "image_visual_confirmation_packets.json"
    if not packets_path.exists():
        print(f"Missing image visual confirmation packets: {packets_path}", file=sys.stderr)
        return 1

    packets = json.loads(packets_path.read_text(encoding="utf-8"))
    if args.source_pdf:
        source_pdf = str(args.source_pdf.resolve())
        packets["source_pdf"] = source_pdf
        packets["source_pdf_available"] = args.source_pdf.exists()
        for item in packets.get("items") or []:
            item["source_pdf"] = source_pdf
            item["source_pdf_available"] = args.source_pdf.exists()

    summary = add_source_pdf_crops_to_packets(packets, standard_dir)
    write_json(packets_path, packets)
    (standard_dir / "image_visual_confirmation.html").write_text(build_image_visual_confirmation_html(packets), encoding="utf-8")
    outcomes_path = standard_dir / "standard_review_outcomes.json"
    if outcomes_path.exists():
        review_outcomes = json.loads(outcomes_path.read_text(encoding="utf-8"))
        sync_image_visual_crops_to_review_outcomes(packets, review_outcomes)
        write_json(outcomes_path, review_outcomes)
        (standard_dir / "review_outcomes.html").write_text(build_review_outcomes_html(review_outcomes), encoding="utf-8")
        refresh_visual_outcome_review_artifacts(standard_dir)
    update_manifest(standard_dir, summary)
    update_reports(standard_dir, summary)
    refresh_workbook_profile_artifacts(standard_dir)
    print(json.dumps({"standard_dir": str(standard_dir), **summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
