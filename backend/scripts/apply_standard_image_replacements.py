#!/usr/bin/env python3
"""Apply source-crop-backed replacements for Standard image blockers."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_crop_to_target(source: Path, target: Path) -> None:
    try:
        from PIL import Image  # type: ignore

        with Image.open(source) as image:
            if target.suffix.lower() in {".jpg", ".jpeg"} and image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            image.save(target)
    except Exception:
        shutil.copy2(source, target)


def apply_replacements(standard_dir: Path) -> dict[str, Any]:
    audit_path = standard_dir / "image_replacement_audit.json"
    if not audit_path.exists():
        raise FileNotFoundError(f"Missing image replacement audit: {audit_path}")
    audit = read_json(audit_path)
    items = [item for item in audit.get("items") or [] if item.get("bucket") == "replace_with_source_crop_candidate"]
    backup_dir = standard_dir / "image_replacement_originals"
    backup_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.utcnow().isoformat() + "Z"
    correction_log_path = standard_dir / "correction_log.json"
    corrections = read_json(correction_log_path)
    if not isinstance(corrections, list):
        corrections = []
    existing = {
        (item.get("type"), item.get("outcome_id"), item.get("target_image"))
        for item in corrections
        if isinstance(item, dict)
    }
    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for item in items:
        target_ref = str(item.get("standard_image") or "")
        source_ref = str(item.get("source_crop") or "")
        target = standard_dir / target_ref
        source = standard_dir / source_ref
        if not target.exists() or not source.exists():
            skipped.append({"outcome_id": item.get("outcome_id"), "reason": "missing_target_or_source"})
            continue
        backup = backup_dir / target.name
        if not backup.exists():
            shutil.copy2(target, backup)
        save_crop_to_target(source, target)
        correction = {
            "type": "image_replaced_from_source_crop",
            "block_id": item.get("block_id"),
            "outcome_id": item.get("outcome_id"),
            "target_image": target_ref,
            "source_crop": source_ref,
            "source_page_number": item.get("source_page_number"),
            "source_bbox": item.get("source_bbox") or [],
            "reason": "Standard extracted image failed Basic Print image visual rule; replaced with source PDF crop evidence preserving source visual content.",
            "method": "source_pdf_crop_saved_to_existing_image_ref",
            "created_at": now,
            "evidence": [
                "standard_review_outcomes.json",
                "image_outcome_rule_audit.json",
                "image_replacement_audit.json",
                source_ref,
                target_ref,
            ],
        }
        key = (correction["type"], correction["outcome_id"], correction["target_image"])
        if key not in existing:
            corrections.append(correction)
            existing.add(key)
        applied.append(correction)
    write_json(correction_log_path, corrections)
    report = {
        "schema": "luceon-standard-image-replacement-apply/v1",
        "standard_dir": str(standard_dir),
        "applied_at": now,
        "applied_count": len(applied),
        "skipped_count": len(skipped),
        "backup_dir": "image_replacement_originals/",
        "applied": applied,
        "skipped": skipped,
    }
    write_json(standard_dir / "image_replacement_apply_report.json", report)
    manifest_path = standard_dir / "manifest.json"
    manifest = read_json(manifest_path)
    if isinstance(manifest, dict):
        outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), dict) else {}
        outputs["image_replacement_audit"] = "image_replacement_audit.json"
        outputs["image_replacement_apply_report"] = "image_replacement_apply_report.json"
        manifest["outputs"] = outputs
        review_artifacts = manifest.get("review_artifacts") if isinstance(manifest.get("review_artifacts"), dict) else {}
        review_artifacts["image_replacement_apply_report"] = {
            "applied_count": len(applied),
            "skipped_count": len(skipped),
        }
        manifest["review_artifacts"] = review_artifacts
        write_json(manifest_path, manifest)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = apply_replacements(args.standard_dir)
    print(json.dumps({k: v for k, v in report.items() if k not in {"applied", "skipped"}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
