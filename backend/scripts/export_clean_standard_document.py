#!/usr/bin/env python3
"""Export a Clean package as Luceon Clean Standard Document v1."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import standard_from_clean as standard


BLOCK_TYPE_MAP = {
    "unit_opener": "unit",
    "question_group": "exercise_group",
    "captioned_figure": "figure",
    "before_you_read": "section",
    "comprehension_questions": "section",
    "vocabulary_practice": "section",
    "vocabulary_box": "section",
    "did_you_know": "note",
    "explore_more": "section",
    "review_unit": "section",
    "label_marker": "metadata",
    "unknown": "paragraph",
}

ASSET_ROLE_BY_DECISION = {
    "drop": "decorative",
}

STANDARD_BLOCK_TYPES = {
    "document_title",
    "front_matter",
    "unit",
    "chapter",
    "lesson",
    "section",
    "reading_passage",
    "paragraph",
    "explanation",
    "key_concept",
    "grammar_box",
    "worked_example",
    "example",
    "exercise_group",
    "question",
    "option",
    "answer_blank",
    "word_bank",
    "vocabulary_item",
    "table",
    "formula",
    "figure",
    "caption",
    "diagram",
    "note",
    "sidebar",
    "icon",
    "answer_key",
    "metadata",
}


def read_json(path: Path) -> Any:
    if not path.exists():
        return {} if path.suffix == ".json" else None
    return json.loads(path.read_text(encoding="utf-8"))


def object_ref(kind: str, uri: str, path: Path | None = None) -> dict[str, Any]:
    ref: dict[str, Any] = {"kind": kind, "uri": uri}
    if path and path.exists() and path.is_file():
        ref["size_bytes"] = path.stat().st_size
    return ref


def map_block_type(block_type: str, subtype: str) -> str:
    if block_type in STANDARD_BLOCK_TYPES:
        return block_type
    if block_type == "section" and subtype == "lesson_heading":
        return "lesson"
    return BLOCK_TYPE_MAP.get(block_type, "paragraph")


def source_entries_for_blocks(blocks: list[dict[str, Any]], source_map: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    sorted_source = sorted(
        [item for item in source_map if isinstance(item, dict) and item.get("source_line") is not None],
        key=lambda item: int(item.get("source_line") or 0),
    )
    refs: list[dict[str, Any]] = []
    refs_by_block: dict[str, list[str]] = {}
    cursor = 0
    for index, block in enumerate(blocks, start=1):
        line_start = int(block.get("line_start") or 0)
        while cursor + 1 < len(sorted_source) and int(sorted_source[cursor + 1].get("source_line") or 0) <= line_start:
            cursor += 1
        source = sorted_source[cursor] if sorted_source else {}
        ref_id = f"src-{index:05d}"
        refs_by_block[str(block["id"])] = [ref_id]
        entry: dict[str, Any] = {
            "id": ref_id,
            "block_id": block["id"],
            "stage": "raw",
            "source_block_id": str(source.get("block_ref") or ""),
            "source_text": block.get("text") or "",
            "match": {
                "method": "unknown" if not source else "manual",
                "status": "candidate" if source else "missing",
                "confidence": 0.5 if source else 0,
            },
            "review_flags": [] if source else ["missing_source_ref"],
        }
        if source.get("page_idx") is not None:
            page_index = int(source["page_idx"])
            entry["page_index"] = page_index
            entry["page_number"] = page_index + 1
        refs.append(entry)
    return refs, refs_by_block


def build_assets(blocks: list[dict[str, Any]], media_report: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    media_by_path = {
        str(item.get("path") or ""): item
        for item in media_report.get("items") or []
        if isinstance(item, dict)
    }
    asset_by_path: dict[str, str] = {}
    assets: list[dict[str, Any]] = []
    for block in blocks:
        for image in block.get("image_refs") or []:
            if image in asset_by_path:
                continue
            item = media_by_path.get(image) or {}
            asset_id = f"asset-{len(assets) + 1:05d}"
            decision = str(item.get("decision") or "")
            role = ASSET_ROLE_BY_DECISION.get(decision) or "educational"
            if "helper" in " ".join(item.get("reasons") or []).lower():
                role = "helper_icon"
            asset: dict[str, Any] = {
                "id": asset_id,
                "kind": "image",
                "path": image,
                "role": role,
                "review_flags": ["decorative_media_decision"] if role == "decorative" else [],
            }
            if item.get("width") is not None:
                asset["width"] = int(item["width"])
            if item.get("height") is not None:
                asset["height"] = int(item["height"])
            assets.append(asset)
            asset_by_path[image] = asset_id
    return assets, asset_by_path


def profile_candidate(profile: str, blocks: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(block.get("type") for block in blocks)
    evidence = [
        {"signal": "reading_passage_count", "value": int(counts.get("reading_passage") or 0)},
        {"signal": "question_count", "value": int(counts.get("question") or 0)},
        {"signal": "table_count", "value": int(counts.get("table") or 0)},
        {"signal": "figure_count", "value": int(counts.get("captioned_figure") or 0)},
    ]
    return {"profile": profile, "confidence": 0.9, "evidence": evidence, "review_flags": []}


def build_clean_standard(clean_dir: Path, raw_dir: Path | None, source_pdf: Path | None, profile: str) -> dict[str, Any]:
    clean_md = clean_dir / "clean.md"
    markdown = clean_md.read_text(encoding="utf-8")
    lines = standard.coalesce_html_table_lines(
        standard.coalesce_display_math_lines(
            [standard.Line(idx, text) for idx, text in enumerate(markdown.splitlines(), start=1)]
        )
    )
    clean_manifest = read_json(clean_dir / "manifest.json")
    media_report = read_json(clean_dir / "media_report.json")
    acceptance_report = read_json(clean_dir / "acceptance_report.json")
    source_map = read_json(clean_dir / "source_map.json")
    if not isinstance(source_map, list):
        source_map = []
    image_semantics = standard.load_image_semantics(raw_dir)

    selected_profile = standard.infer_standard_profile(markdown, clean_manifest, profile)
    outline = standard.extract_outline(lines)
    blocks, relations, issue_candidates = standard.build_blocks(lines, image_semantics, selected_profile)
    blocks, short_marker_transforms = standard.merge_short_marker_blocks(blocks)
    relation_summary = standard.annotate_question_relations(blocks, relations)
    source_refs, refs_by_block = source_entries_for_blocks(blocks, source_map)
    assets, asset_by_path = build_assets(blocks, media_report)

    clean_blocks: list[dict[str, Any]] = []
    review_flag_count = 0
    for order, block in enumerate(blocks, start=1):
        mapped_type = map_block_type(str(block.get("type") or ""), str(block.get("subtype") or ""))
        review_flags: list[str] = []
        if not refs_by_block.get(str(block["id"])):
            review_flags.append("missing_source_ref")
        if block.get("status") == "needs_review":
            review_flags.append("uncertain_block_type")
        asset_refs = [asset_by_path[path] for path in block.get("image_refs") or [] if path in asset_by_path]
        review_flag_count += len(review_flags)
        clean_blocks.append(
            {
                "id": block["id"],
                "type": mapped_type,
                "subtype": str(block.get("subtype") or ""),
                "text": str(block.get("text") or ""),
                "markdown": str(block.get("markdown") or ""),
                "outline_path": block.get("heading_path") or [],
                "source_refs": refs_by_block.get(str(block["id"]), []),
                "asset_refs": asset_refs,
                "review_flags": sorted(set(review_flags)),
                "blockers": [],
                "confidence": 0.9 if not review_flags else 0.6,
                "order": order,
            }
        )

    clean_relations: list[dict[str, Any]] = []
    for index, relation in enumerate(relations, start=1):
        relation_type = str(relation.get("type") or "contains")
        mapped = relation_type if relation_type in {"contains", "continues"} else "contains"
        clean_relations.append(
            {
                "id": f"r-{index:05d}",
                "type": mapped,
                "from": str(relation.get("from") or ""),
                "to": str(relation.get("to") or ""),
                "confidence": 0.8,
                "evidence_refs": [],
                "review_flags": [],
                "blockers": [],
            }
        )

    outline_items = [
        {
            "id": f"o-{index:05d}",
            "title": item["title"],
            "level": int(item["level"]),
            "block_id": next((block["id"] for block in blocks if int(block.get("line_start") or 0) == int(item["line"])), ""),
            "path": item.get("path") or [],
        }
        for index, item in enumerate(outline, start=1)
    ]

    status = acceptance_report.get("status") or acceptance_report.get("acceptance", {}).get("status") or "review"
    return {
        "schema": "luceon-clean-standard-document/v1",
        "material_id": clean_manifest.get("material_id") or "",
        "source": {
            "pipeline_stage": "clean",
            "input_refs": [object_ref("local_path", str(clean_md.resolve()), clean_md)],
            "raw_manifest_ref": object_ref("local_path", str((raw_dir / "manifest.json").resolve()), raw_dir / "manifest.json") if raw_dir else {"kind": "unknown", "uri": ""},
            "source_pdf_ref": object_ref("local_path", str(source_pdf.resolve()), source_pdf) if source_pdf else {"kind": "unknown", "uri": ""},
        },
        "document": {
            "title": clean_manifest.get("title") or clean_manifest.get("source_pdf_name") or "Clean Standard Document",
            "languages": ["en"],
            "document_kind_hint": "textbook" if selected_profile.endswith("textbook") else "workbook",
        },
        "profile_candidates": [profile_candidate(selected_profile, blocks)],
        "outline": outline_items,
        "blocks": clean_blocks,
        "relations": clean_relations,
        "assets": assets,
        "source_map": source_refs,
        "contract": {
            "status": "pass" if status == "pass" else "review",
            "version": "v1",
            "required_artifacts": {
                "clean_md": "pass",
                "clean_standard_json": "pass",
                "manifest": "pass" if (clean_dir / "manifest.json").exists() else "fail",
                "media_report": "pass" if (clean_dir / "media_report.json").exists() else "review",
                "structure_report": "pass" if (clean_dir / "structure_report.json").exists() else "review",
                "images": "pass" if (clean_dir / "images").exists() else "review",
                "source_map": "pass" if source_map else "review",
            },
            "blocker_count": 0,
            "review_flag_count": review_flag_count,
            "review_flags": [],
            "blockers": [],
        },
        "metadata": {
            "generated_by": "backend/scripts/export_clean_standard_document.py",
            "source_clean_acceptance": status,
            "requested_profile": profile,
            "selected_profile": selected_profile,
            "compiler_note": "Standard compiler must consume canonical blocks/relations/assets/source_map, not compatibility payloads.",
        },
    }


def build_contract_report(document: dict[str, Any]) -> dict[str, Any]:
    block_counts = Counter(block["type"] for block in document.get("blocks") or [])
    relation_counts = Counter(relation["type"] for relation in document.get("relations") or [])
    return {
        "schema": "luceon-clean-standard-contract-report/v1",
        "status": document.get("contract", {}).get("status"),
        "profile": document.get("metadata", {}).get("selected_profile") or "",
        "requested_profile": document.get("metadata", {}).get("requested_profile") or "",
        "profile_candidates": document.get("profile_candidates") or [],
        "block_count": len(document.get("blocks") or []),
        "relation_count": len(document.get("relations") or []),
        "asset_count": len(document.get("assets") or []),
        "source_ref_count": len(document.get("source_map") or []),
        "block_type_counts": dict(block_counts),
        "relation_type_counts": dict(relation_counts),
        "review_flag_count": document.get("contract", {}).get("review_flag_count"),
        "blocker_count": document.get("contract", {}).get("blocker_count"),
        "notes": [
            "This report validates contract shape and coverage only.",
            "It does not promote a Standard artifact to candidate or accepted golden.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-dir", required=True, type=Path)
    parser.add_argument("--raw-dir", type=Path)
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--profile", default="auto")
    parser.add_argument("--out-dir", type=Path, help="Directory to receive clean_standard.json and clean_contract_report.json. Defaults to clean-dir.")
    parser.add_argument("--copy-clean", action="store_true", help="Copy clean package files into out-dir before writing contract artifacts.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir or args.clean_dir
    if args.copy_clean and out_dir != args.clean_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        for child in args.clean_dir.iterdir():
            target = out_dir / child.name
            if child.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(child, target)
            elif child.is_file():
                shutil.copy2(child, target)
    else:
        out_dir.mkdir(parents=True, exist_ok=True)

    clean_dir = out_dir if args.copy_clean else args.clean_dir
    document = build_clean_standard(clean_dir, args.raw_dir, args.source_pdf, args.profile)
    report = build_contract_report(document)
    standard.write_json(out_dir / "clean_standard.json", document)
    standard.write_json(out_dir / "clean_contract_report.json", report)
    print(
        json.dumps(
            {
                "clean_standard": str((out_dir / "clean_standard.json").resolve()),
                "status": report["status"],
                "profile": (document.get("profile_candidates") or [{}])[0].get("profile"),
                "block_count": report["block_count"],
                "relation_count": report["relation_count"],
                "asset_count": report["asset_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
