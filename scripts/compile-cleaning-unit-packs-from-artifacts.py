#!/usr/bin/env python3
"""Compile CleanLaTeX cleaning unit packs from existing Luceon artifacts.

This script is intentionally local-file only. It does not run MinerU,
MinerU-Popo, LLMs, DB writes, MinIO writes, or runtime workers.
"""

from __future__ import annotations

import argparse
import json
import sys
import types
from pathlib import Path
from typing import Any

sys.modules.setdefault("boto3", types.SimpleNamespace(client=lambda *args, **kwargs: None))

from luceon_service import service  # noqa: E402


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-toc", type=Path)
    parser.add_argument("--chapter-spans", type=Path)
    parser.add_argument("--review-tree", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--source-tree", required=True, type=Path)
    parser.add_argument("--content-list", type=Path)
    parser.add_argument("--material-id", required=True)
    parser.add_argument("--asset-version", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--selection-mode", choices=["pilot", "full-book"], default="full-book")
    parser.add_argument("--pilot-number", action="append", dest="pilot_numbers")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.canonical_toc:
        canonical_toc = read_json(args.canonical_toc)
    else:
        if not args.review_tree:
            raise SystemExit("--canonical-toc or --review-tree is required")
        markdown_text = args.markdown.read_text(encoding="utf-8", errors="replace") if args.markdown else None
        canonical_toc = service._compile_canonical_toc(read_json(args.review_tree), markdown_text)

    chapter_spans = read_json(args.chapter_spans) if args.chapter_spans else service._compile_chapter_spans(canonical_toc)
    source_tree = read_json(args.source_tree)
    content_bytes = args.content_list.read_bytes() if args.content_list else None
    asset_index = service._mineru_asset_index_from_content_bytes(content_bytes)

    packs_manifest = service._compile_cleanlatex_pilot_packs(
        canonical_toc,
        chapter_spans,
        source_tree,
        args.material_id,
        args.asset_version,
        asset_index,
        tuple(args.pilot_numbers or ("1.1", "4.1")),
        selection_mode=args.selection_mode,
    )

    output_dir = args.out
    write_json(output_dir / "cleaning_unit_packs.json", packs_manifest.get("packs") or [])
    write_json(output_dir / "cleaning_unit_prompts.json", packs_manifest.get("prompts") or {})
    write_json(output_dir / "cleanlatex_validation_manifests.json", packs_manifest.get("validation_manifests") or [])
    write_json(output_dir / "toc_output_coverage.json", packs_manifest.get("toc_output_coverage") or {})
    write_json(
        output_dir / "cleanlatex_pack_manifest.json",
        {key: value for key, value in packs_manifest.items() if key not in {"packs", "prompts", "validation_manifests"}},
    )
    write_json(output_dir / "canonical_toc.json", canonical_toc)
    write_json(output_dir / "chapter_spans.json", chapter_spans)
    write_json(
        output_dir / "summary.json",
        {
            "ok": True,
            "selection_mode": args.selection_mode,
            "material_id": args.material_id,
            "asset_version": args.asset_version,
            "stats": packs_manifest.get("stats") or {},
            "side_effects": {
                "mineru_runs": 0,
                "minerupopo_runs": 0,
                "llm_api_calls": 0,
                "db_writes": 0,
                "minio_writes": 0,
                "runtime_worker_posts": 0,
            },
        },
    )
    print(json.dumps(read_json(output_dir / "summary.json"), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
