#!/usr/bin/env python3
"""Audit source-crop-backed replacements for Standard image blockers."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from standard_from_clean import write_json

READY_STATUSES = {"created", "reused"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def image_size(path: Path) -> list[int]:
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            return [image.size[0], image.size[1]]
    except Exception:
        return []


def build_audit(standard_dir: Path) -> dict[str, Any]:
    outcomes = read_json(standard_dir / "standard_review_outcomes.json")
    rule_audit = read_json(standard_dir / "image_outcome_rule_audit.json")
    audit_by_id = {str(item.get("outcome_id") or ""): item for item in rule_audit.get("items") or []}
    items: list[dict[str, Any]] = []
    for outcome in outcomes.get("items") or []:
        if outcome.get("packet_type") != "image_source_visual_confirmation":
            continue
        if outcome.get("decision") != "needs_reconstruction" or outcome.get("status") != "open":
            continue
        audit_item = audit_by_id.get(str(outcome.get("outcome_id") or ""), {})
        standard_image = str(audit_item.get("standard_image") or "")
        source_crop = str(outcome.get("source_crop") or audit_item.get("source_crop") or "")
        standard_path = standard_dir / standard_image
        crop_path = standard_dir / source_crop
        source_crop_status = str(outcome.get("source_crop_status") or audit_item.get("source_crop_status") or "")
        issues = audit_item.get("issues") or []
        can_replace = bool(
            standard_image
            and source_crop
            and standard_path.exists()
            and crop_path.exists()
            and source_crop_status in READY_STATUSES
            and issues
        )
        bucket = "replace_with_source_crop_candidate" if can_replace else "not_replaceable_missing_evidence"
        items.append(
            {
                "outcome_id": outcome.get("outcome_id"),
                "block_id": outcome.get("block_id"),
                "bucket": bucket,
                "standard_image": standard_image,
                "source_crop": source_crop,
                "source_crop_status": source_crop_status,
                "issues": issues,
                "standard_size": image_size(standard_path),
                "source_crop_size": image_size(crop_path),
                "source_page_number": outcome.get("source_page_number"),
                "source_bbox": outcome.get("source_bbox") or audit_item.get("source_bbox") or [],
                "category": audit_item.get("category") or "",
                "action": audit_item.get("action") or "",
                "context": audit_item.get("context") or "",
            }
        )
    bucket_counts = Counter(str(item.get("bucket") or "") for item in items)
    issue_counts = Counter(issue for item in items for issue in item.get("issues") or [])
    return {
        "schema": "luceon-standard-image-replacement-audit/v1",
        "standard_dir": str(standard_dir),
        "policy": "audit_only_source_crop_replacement_requires_explicit_apply",
        "count": len(items),
        "bucket_counts": dict(bucket_counts),
        "issue_counts": dict(issue_counts),
        "items": items,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit = build_audit(args.standard_dir)
    write_json(args.standard_dir / "image_replacement_audit.json", audit)
    print(json.dumps({k: v for k, v in audit.items() if k != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
