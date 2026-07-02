#!/usr/bin/env python3
"""Refresh a Standard package PDF and print evidence after artifact changes."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from standard_from_clean import (
    acceptance_status,
    compute_quality_score,
    detect_visible_artifacts,
    pdf_page_count,
    read_json,
    render_pdf,
    write_json,
)


IMG_SRC_RE = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", re.I)


def local_image_refs(html_text: str) -> list[str]:
    refs: list[str] = []
    for match in IMG_SRC_RE.finditer(html_text):
        ref = match.group(1).strip()
        if not ref or ref.startswith(("http://", "https://", "data:", "#")):
            continue
        refs.append(ref)
    return sorted(set(refs))


def source_clean_dir(standard_dir: Path) -> Path | None:
    manifest = read_json(standard_dir / "manifest.json")
    source_clean_manifest = str(manifest.get("source_clean_manifest") or "")
    if not source_clean_manifest:
        return None
    path = Path(source_clean_manifest)
    if path.exists():
        return path.parent
    return None


def restore_missing_images(standard_dir: Path, refs: list[str]) -> dict[str, Any]:
    clean_dir = source_clean_dir(standard_dir)
    restored: list[str] = []
    missing: list[str] = []
    for ref in refs:
        target = standard_dir / ref
        if target.exists():
            continue
        sources = []
        if clean_dir:
            sources.extend(
                [
                    clean_dir / ref,
                    clean_dir / "raw_input" / ref,
                    clean_dir.parent / "raw_input" / ref,
                ]
            )
        source = next((candidate for candidate in sources if candidate.exists()), None)
        if source:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            restored.append(ref)
        else:
            missing.append(ref)
    report = {
        "schema": "luceon-standard-media-ref-refresh/v1",
        "standard_dir": str(standard_dir),
        "source_clean_dir": str(clean_dir) if clean_dir else "",
        "image_ref_count": len(refs),
        "restored_count": len(restored),
        "missing_count": len(missing),
        "restored": restored,
        "missing": missing,
    }
    write_json(standard_dir / "standard_media_ref_refresh_report.json", report)
    return report


def recompute_quality(standard_dir: Path, print_qa: dict[str, Any]) -> dict[str, Any] | None:
    acceptance = read_json(standard_dir / "standard_acceptance_report.json")
    gates = acceptance.get("gates") if isinstance(acceptance.get("gates"), dict) else {}
    if not gates:
        return None
    quality = compute_quality_score(
        gates,
        read_json(standard_dir / "layout_report.json"),
        read_json(standard_dir / "standard_issue_candidates.json") if (standard_dir / "standard_issue_candidates.json").exists() else [],
        read_json(standard_dir / "standard_visual_review_packets.json"),
        print_qa,
        read_json(standard_dir / "correction_log.json") if (standard_dir / "correction_log.json").exists() else [],
        read_json(standard_dir / "issue_candidate_disposition_audit.json"),
    )
    write_json(standard_dir / "standard_quality_score.json", quality)
    acceptance["quality_score"] = {"score": quality.get("score"), "status": quality.get("status")}
    write_json(standard_dir / "standard_acceptance_report.json", acceptance)
    return quality


def refresh_print_pdf(standard_dir: Path, chrome_path: str | None = None) -> dict[str, Any]:
    html_path = standard_dir / "standard.html"
    pdf_path = standard_dir / "standard.pdf"
    if not html_path.exists():
        raise FileNotFoundError(f"Missing Standard HTML: {html_path}")
    html_text = html_path.read_text(encoding="utf-8")
    refs = local_image_refs(html_text)
    media_refresh = restore_missing_images(standard_dir, refs)
    missing_images = list(media_refresh.get("missing") or [])
    visible_artifacts = detect_visible_artifacts(html_text)
    pdf_ok, pdf_message = render_pdf(html_path, pdf_path, chrome_path)
    print_qa = {
        "schema": "luceon-standard-print-qa/v1",
        "html": str(html_path.resolve()),
        "pdf": str(pdf_path.resolve()),
        "pdf_ok": pdf_ok,
        "pdf_message": pdf_message,
        "pdf_bytes": pdf_path.stat().st_size if pdf_path.exists() else 0,
        "pdf_page_count": pdf_page_count(pdf_path) if pdf_ok else None,
        "image_refs": len(refs),
        "missing_images": missing_images,
        "visible_artifacts": visible_artifacts,
    }
    write_json(standard_dir / "print_qa_report.json", print_qa)

    acceptance_path = standard_dir / "standard_acceptance_report.json"
    acceptance = read_json(acceptance_path)
    gates = acceptance.get("gates") if isinstance(acceptance.get("gates"), dict) else {}
    if gates:
        print_gate = gates.get("print_render") if isinstance(gates.get("print_render"), dict) else {}
        print_gate.update(
            {
                "status": "pass" if pdf_ok and print_qa["pdf_page_count"] is not None else "fail",
                "pdf_ok": pdf_ok,
                "pdf_message": pdf_message,
                "pdf_bytes": print_qa["pdf_bytes"],
                "pdf_page_count": print_qa["pdf_page_count"],
            }
        )
        gates["print_render"] = print_gate
        media_gate = gates.get("media_integrity") if isinstance(gates.get("media_integrity"), dict) else {}
        media_gate["image_refs"] = len(refs)
        media_gate["missing_images"] = missing_images
        dropped_without_evidence = media_gate.get("dropped_without_evidence") or []
        media_gate["status"] = "fail" if missing_images or dropped_without_evidence else "pass"
        gates["media_integrity"] = media_gate
        visible_gate = gates.get("visible_artifacts") if isinstance(gates.get("visible_artifacts"), dict) else {}
        visible_gate.update(
            {
                "status": "fail" if visible_artifacts["count"] else "pass",
                "count": visible_artifacts["count"],
                "items": visible_artifacts["items"],
            }
        )
        gates["visible_artifacts"] = visible_gate
        acceptance["gates"] = gates
        acceptance["status"] = acceptance_status(gates)
        summary = acceptance.get("summary") if isinstance(acceptance.get("summary"), dict) else {}
        summary["image_refs"] = len(refs)
        summary["missing_images"] = len(missing_images)
        summary["visible_artifact_count"] = visible_artifacts["count"]
        acceptance["summary"] = summary
        write_json(acceptance_path, acceptance)

    quality = recompute_quality(standard_dir, print_qa)
    acceptance = read_json(acceptance_path)
    manifest_path = standard_dir / "manifest.json"
    manifest = read_json(manifest_path)
    if isinstance(manifest, dict):
        outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), dict) else {}
        outputs["print_qa_report"] = "print_qa_report.json"
        outputs["standard_pdf"] = "standard.pdf"
        outputs["standard_media_ref_refresh_report"] = "standard_media_ref_refresh_report.json"
        outputs["image_refs"] = len(refs)
        manifest["outputs"] = outputs
        if quality:
            manifest["quality_score"] = {"score": quality.get("score"), "status": quality.get("status")}
        manifest["acceptance"] = {
            "status": acceptance.get("status"),
            "gates": {
                name: gate.get("status")
                for name, gate in (acceptance.get("gates") or {}).items()
                if isinstance(gate, dict)
            },
        }
        write_json(manifest_path, manifest)

    return {
        "standard_dir": str(standard_dir),
        "pdf_ok": pdf_ok,
        "pdf_message": pdf_message,
        "pdf_bytes": print_qa["pdf_bytes"],
        "pdf_page_count": print_qa["pdf_page_count"],
        "image_refs": len(refs),
        "missing_images": len(missing_images),
        "restored_images": int(media_refresh.get("restored_count") or 0),
        "visible_artifact_count": visible_artifacts["count"],
        "acceptance_status": acceptance.get("status"),
        "quality_score": (quality or {}).get("score"),
        "quality_status": (quality or {}).get("status"),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--chrome", default=None, help="Optional Chrome executable path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = refresh_print_pdf(args.standard_dir, args.chrome)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["pdf_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
