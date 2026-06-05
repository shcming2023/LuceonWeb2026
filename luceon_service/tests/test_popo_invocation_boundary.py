from __future__ import annotations

import json
import os
import http.server
import sys
import tempfile
import threading
import time
import types
from pathlib import Path

sys.modules.setdefault("boto3", types.SimpleNamespace(client=lambda *args, **kwargs: None))

from luceon_service import service


def make_pages(count: int) -> dict[str, list[dict]]:
    return {
        str(page): [
            {"type": "text", "content": f"page {page} text", "bbox": [0.1, 0.1, 0.2, 0.2]},
            {"type": "title", "content": f"heading {page}", "bbox": [0.1, 0.2, 0.2, 0.3]},
        ]
        for page in range(1, count + 1)
    }


def test_wrapped_normalized_label_counts_pages_and_chunks():
    payload = {
        "model": "mineru",
        "doc_id": "4134323036518274",
        "input_label": "4134323036518274",
        "pages": make_pages(891),
    }

    estimate = service._estimate_toc_rebuild(payload, chunk_size=10)

    assert estimate["normalized_pages"] == 891
    assert estimate["normalized_blocks"] == 1782
    assert estimate["inference_chunks_total"] > 250
    assert estimate["inference_chunks_total"] < 320
    assert estimate["chunks_by_task"]["contd"] > 80
    assert estimate["chunks_by_task"]["title"] > 80
    assert estimate["chunks_by_task"]["image"] > 80


def test_bounded_payload_keeps_large_original_estimate_but_limits_selected_work():
    payload = {
        "model": "mineru",
        "doc_id": "4134323036518274",
        "input_label": "4134323036518274",
        "pages": make_pages(891),
    }

    bounded_payload, plan = service._build_bounded_payload(payload, chunk_size=10)

    assert plan["mode"] == "bounded-preview"
    assert plan["original"]["normalized_pages"] == 891
    assert plan["selected"]["normalized_pages"] <= service.BOUNDED_PAGE_LIMIT
    assert plan["selected"]["inference_chunks_total"] <= service.BOUNDED_CHUNK_LIMIT
    assert len(bounded_payload["pages"]) == plan["selected"]["normalized_pages"]
    assert bounded_payload["luceon_invocation"]["mode"] == "bounded-preview"
    assert bounded_payload["luceon_invocation"]["source_pages"] == 891


def test_live_progress_reads_real_pages_and_raw_chunk_metadata():
    payload = {
        "model": "mineru",
        "doc_id": "4134323036518274",
        "input_label": "4134323036518274",
        "pages": make_pages(891),
    }

    with tempfile.TemporaryDirectory() as tmp:
        old_work_root = service.WORK_ROOT
        try:
            service.WORK_ROOT = Path(tmp)
            job_id = "luceon-task-1780291805535-toc-rebuild-v2-1780298498453"
            outputs = service.WORK_ROOT / job_id / "outputs"
            label_dir = outputs / "label_normalization" / "mineru"
            raw_dir = outputs / "inference_raw" / "mineru" / "4134323036518274"
            label_dir.mkdir(parents=True)
            raw_dir.mkdir(parents=True)
            archive_dir = raw_dir / "profile_archive" / "chunk-size-4-legacy"
            archive_dir.mkdir(parents=True)
            (label_dir / "4134323036518274.json").write_text(json.dumps(payload), encoding="utf-8")
            (raw_dir / "contd_chunk_0000.json").write_text(json.dumps({
                "task": "contd",
                "chunk_index": 0,
                "range": [1, 16],
                "pages": [1, 2, 3, 4, 5, 12, 13, 14, 15, 16],
                "parsed": [[{"src_id": 1, "tgt_id": 2}]],
            }), encoding="utf-8")
            (archive_dir / "contd_chunk_0009.json").write_text(json.dumps({
                "task": "contd",
                "chunk_index": 9,
                "range": [90, 99],
                "pages": [90],
                "parsed": [[{"src_id": 9, "tgt_id": 10}]],
            }), encoding="utf-8")

            progress = service._get_live_progress({
                "payload": {"job_id": job_id, "material_id": "4134323036518274"},
                "start_time": time.time(),
                "current_step": "running_inference",
            })
        finally:
            service.WORK_ROOT = old_work_root

    assert progress["normalized_pages"] == 891
    assert progress["inference_chunks_total"] > 250
    assert progress["inference_chunks_completed"] == 1
    assert progress["chunks_by_task"] == {"contd": 1}
    assert progress["last_completed_chunk"] == "contd_chunk_0000.json"
    assert progress["active_chunk"] == "contd_chunk_0001.json"
    assert progress["inference_blocks_validated"] == 1


def test_toc_review_filter_keeps_outline_and_hides_full_document_noise():
    raw_tree = {
        "type": "root",
        "title": "",
        "content": "",
        "children": [
            {
                "type": "title",
                "title": "Default Title",
                "content": "cover and copyright text that should not reach review",
                "children": [
                    {"type": "title", "title": "> Contents", "content": "duplicated table of contents", "children": []},
                    {
                        "type": "title",
                        "title": "> Acknowledgements",
                        "content": "front matter wrapper",
                        "children": [
                            {
                                "type": "title",
                                "title": "Unit 1",
                                "content": "Review of number concepts",
                                "children": [
                                    {
                                        "type": "title",
                                        "title": "1.1 Different types of numbers",
                                        "content": "full section body should not be copied",
                                        "block_ids": ["b-1"],
                                        "children": [
                                            {"type": "title", "title": "TIP", "content": "hide tip body", "children": []},
                                            {"type": "title", "title": "Exercise 1.1", "content": "question text should not flood review", "children": []},
                                            {"type": "footer", "title": "12", "content": "", "children": []},
                                        ],
                                    },
                                    {"type": "title", "title": "WORKED EXAMPLE1", "content": "hide example", "children": []},
                                ],
                            },
                            {"type": "title", "title": "> Glossary", "content": "terms", "children": []},
                            {"type": "title", "title": "> Index", "content": "index terms", "children": []},
                        ],
                    },
                ],
            }
        ],
    }

    review_tree = service._filter_toc_view_tree(raw_tree)
    readable = service._render_tree_preview(review_tree)
    flattened = service._flatten_tree(review_tree)

    assert review_tree["schema"] == "luceon-toc-review-tree/v1"
    assert "Default Title" not in readable
    assert "> Contents" not in readable
    assert "Acknowledgements" not in readable
    assert "TIP" not in readable
    assert "WORKED EXAMPLE" not in readable
    assert "Unit 1" in readable
    assert "1.1 Different types of numbers" in readable
    assert "Exercise 1.1" in readable
    assert "> Glossary" in readable
    assert "> Index" in readable
    assert all(row["content"] == "" for row in flattened)
    assert any(row["block_ids"] == ["b-1"] for row in flattened)


def test_canonical_toc_compiler_builds_traceable_chapter_scaffold_without_llm_structure():
    raw_tree = {
        "type": "root",
        "title": "",
        "content": "",
        "children": [
            {
                "type": "title",
                "title": "Default Title",
                "content": "cover text must not leak",
                "children": [
                    {
                        "type": "title",
                        "title": "Unit 1",
                        "content": "unit body must not leak",
                        "id": "b-unit-1",
                        "page": 3,
                        "children": [
                            {
                                "type": "title",
                                "title": "1.1 Different types of numbers",
                                "content": "section body must not leak",
                                "block_ids": ["b-sec-1"],
                                "page": 4,
                                "children": [
                                    {
                                        "type": "title",
                                        "title": "Exercise 1.1",
                                        "content": "questions must not leak",
                                        "block_ids": ["b-ex-1"],
                                        "page": 6,
                                        "children": [],
                                    },
                                    {
                                        "type": "title",
                                        "title": "TIP",
                                        "content": "noise",
                                        "block_ids": ["b-tip"],
                                        "page": 6,
                                        "children": [],
                                    },
                                ],
                            },
                            {
                                "type": "title",
                                "title": "Practice questions",
                                "content": "practice body must not leak",
                                "block_ids": ["b-practice"],
                                "page": 9,
                                "children": [],
                            },
                        ],
                    },
                    {
                        "type": "title",
                        "title": "> Glossary",
                        "content": "glossary body must not leak",
                        "block_ids": ["b-glossary"],
                        "page": 100,
                        "children": [],
                    },
                    {
                        "type": "title",
                        "title": "> Index",
                        "content": "index body must not leak",
                        "block_ids": ["b-index"],
                        "page": 110,
                        "children": [],
                    },
                ],
            },
        ],
    }

    review_tree = service._filter_toc_view_tree(raw_tree)
    canonical_toc = service._compile_canonical_toc(review_tree)
    chapter_spans = service._compile_chapter_spans(canonical_toc)
    rawlatex_scaffold = service._compile_rawlatex_scaffold(canonical_toc, chapter_spans)

    assert canonical_toc["schema"] == "luceon-canonical-toc/v1"
    assert chapter_spans["schema"] == "luceon-chapter-spans/v1"
    assert rawlatex_scaffold["schema"] == "luceon-rawlatex-scaffold/v1"
    assert canonical_toc["stats"]["kind_counts"]["unit"] == 1
    assert canonical_toc["stats"]["kind_counts"]["section"] == 1
    assert canonical_toc["stats"]["kind_counts"]["exercise"] == 1
    assert canonical_toc["stats"]["kind_counts"]["practice"] == 1
    assert canonical_toc["stats"]["kind_counts"]["glossary"] == 1
    assert canonical_toc["stats"]["kind_counts"]["index"] == 1

    spans = {span["title"]: span for span in chapter_spans["spans"]}
    assert set(spans["1.1 Different types of numbers"]["source_block_ids"]) == {"b-sec-1", "b-ex-1", "b-practice"}
    assert spans["Exercise 1.1"]["source_block_ids"] == ["b-ex-1"]
    assert spans["Exercise 1.1"]["source_page_range"] == [6, 6]
    assert spans["> Glossary"]["source_block_ids"] == ["b-glossary"]
    assert spans["> Index"]["source_block_ids"] == ["b-index"]

    assert rawlatex_scaffold["manifest"]["file_count"] >= 6
    exercise_file = next(file for file in rawlatex_scaffold["files"] if file["title"] == "Exercise 1.1")
    assert "source_block_ids: ['b-ex-1']" in exercise_file["content"]
    assert "TODO(cleanlatex)" in exercise_file["content"]
    assert "questions must not leak" not in json.dumps(rawlatex_scaffold, ensure_ascii=False)
    assert "No LLM call was used to decide whole-book structure." in rawlatex_scaffold["rules"]


def test_contents_first_canonical_toc_uses_book_contents_as_global_spine():
    markdown = """
## > Contents

## Unit 1

Review of number concepts
1.1 Different types of numbers 4
1.5 Powers,rootsand laws of indices 17
Past paper questions for Unit1 145
Unit1Project 148

## Unit 3

12Averagesandmeasuresof
spread 366
12.1 Differenttypesof averages 367
12.2 Making comparisonsusingaverages
andranges 371

Unit 4
15Scaledrawings,bearings and
trigonometry 471
15.3 Understanding thetangent,cosineand
sineratios 479
15.4 Exact trigonometric ratios 495
Glossary 867
Index 872

## > Introduction
"""
    review_tree = {
        "schema": "luceon-toc-review-tree/v1",
        "type": "root",
        "title": "TOC Review View",
        "children": [
            {"type": "text", "title": "Unit 1", "id": "b-unit-1", "page": 3, "children": [
                {"type": "text", "title": "1.1 Different types of numbers", "block_ids": ["b-1-1"], "page": 4, "children": []},
                {"type": "text", "title": "Exercise 1.1", "block_ids": ["b-ex-1-1"], "page": 6, "children": []},
            ]},
            {"type": "text", "title": "12.1Different types of average", "block_ids": ["b-12-1"], "page": 367, "children": []},
            {"type": "text", "title": "15.4 Exact trigonometric ratios", "block_ids": ["b-15-4"], "page": 495, "children": []},
        ],
    }

    outline = service._parse_contents_outline(markdown)
    canonical_toc = service._compile_canonical_toc(review_tree, markdown)
    spans = service._compile_chapter_spans(canonical_toc)

    assert len([entry for entry in outline if entry["kind"] == "unit"]) == 3
    assert not any(entry["kind"] == "unit" and "Project" in entry["title"] for entry in outline)
    assert canonical_toc["compiler"].endswith("contents-first")
    assert canonical_toc["stats"]["kind_counts"]["unit"] == 3

    nodes = []
    def walk(node):
        if node.get("node_id") != "toc-root":
            nodes.append(node)
        for child in node.get("children") or []:
            walk(child)
    walk(canonical_toc["root"])
    titles = [node["title"] for node in nodes]
    assert "1.5 Powers,rootsand laws of indices" in titles
    assert "12.1 Differenttypesof averages" in titles
    assert "12.2 Making comparisonsusingaverages andranges" in titles
    assert "15.4 Exact trigonometric ratios" in titles
    assert "Unit 1 Project" in titles

    by_title = {span["title"]: span for span in spans["spans"]}
    assert by_title["12.1 Differenttypesof averages"]["source_block_ids"] == ["b-12-1"]
    assert by_title["15.4 Exact trigonometric ratios"]["source_block_ids"] == ["b-15-4"]
    assert "missing-body-tree-match" in by_title["1.5 Powers,rootsand laws of indices"]["warnings"]


def test_contents_first_recovers_implicit_chapters_and_reparents_orphan_exercises():
    markdown = """
## > Contents

## Unit 1

Review of number concepts
1.1 Different types of numbers 4
1.2 Multiplesand factors 6
Collectingorganisingand
displayingdata 107
4.1 Colectingand classifyingdata 110
4.2 Organisingdata 113
Past paper questions for Unit1 145

## Unit 2

5 Fractions,percentagesand
standardform 149
5.1 Revisiting fractions 151
"""
    review_tree = {
        "schema": "luceon-toc-review-tree/v1",
        "type": "root",
        "title": "TOC Review View",
        "children": [
            {"type": "text", "title": "Unit 1", "id": "b-unit-1", "page": 3, "children": []},
            {"type": "text", "title": "1.1 Different types of numbers", "block_ids": ["b-1-1"], "page": 4, "children": []},
            {"type": "text", "title": "Exercise 1.8", "block_ids": ["b-ex-1-8"], "page": 31, "children": []},
            {"type": "text", "title": "4.1 Colectingand classifyingdata", "block_ids": ["b-4-1"], "page": 110, "children": []},
            {"type": "text", "title": "Exercise 4.4", "block_ids": ["b-ex-4-4"], "page": 125, "children": []},
        ],
    }

    canonical_toc = service._compile_canonical_toc(review_tree, markdown)

    nodes = []
    by_title = {}

    def walk(node):
        if node.get("node_id") != "toc-root":
            nodes.append(node)
            by_title[node["title"]] = node
        for child in node.get("children") or []:
            walk(child)

    walk(canonical_toc["root"])

    chapter_1 = by_title["1 Review of number concepts"]
    chapter_4 = by_title["4 Collectingorganisingand displayingdata"]
    assert "inferred_chapter_from_following_section" in chapter_1["warnings"]
    assert "inferred_chapter_from_following_section" in chapter_4["warnings"]
    assert by_title["1.1 Different types of numbers"]["parent_id"] == chapter_1["node_id"]
    assert by_title["1.2 Multiplesand factors"]["parent_id"] == chapter_1["node_id"]
    assert by_title["4.1 Colectingand classifyingdata"]["parent_id"] == chapter_4["node_id"]
    assert by_title["4.2 Organisingdata"]["parent_id"] == chapter_4["node_id"]
    assert by_title["Exercise 1.8"]["parent_id"] == chapter_1["node_id"]
    assert by_title["Exercise 4.4"]["parent_id"] == chapter_4["node_id"]
    assert by_title["Exercise 1.8"]["parent_id"] != by_title["Unit 2"]["node_id"]
    assert by_title["Exercise 4.4"]["parent_id"] != by_title["Unit 2"]["node_id"]


def test_cleanlatex_pilot_packs_are_structure_level_and_source_bound():
    markdown = """
## > Contents

## Unit 1

Review of number concepts
1.1 Different types of numbers 4
Collectingorganisingand
displayingdata 107
4.1 Colectingand classifyingdata 110
4.2 Organisingdata 113
"""
    review_tree = {
        "schema": "luceon-toc-review-tree/v1",
        "type": "root",
        "title": "TOC Review View",
        "children": [
            {"type": "text", "title": "Unit 1", "id": "b-unit-1", "page": 3, "children": [
                {"type": "text", "title": "1 Review of number concepts", "block_ids": ["b-ch-1"], "page": 4, "children": [
                    {"type": "text", "title": "1.1 Different types of numbers", "block_ids": ["b-1-1"], "page": 4, "content": "Numbers content", "children": []},
                ]},
                {"type": "text", "title": "4 Collectingorganisingand displayingdata", "block_ids": ["b-ch-4"], "page": 107, "children": [
                    {
                        "type": "image",
                        "id": "img-4-1",
                        "source_id": "fixture:99",
                        "page": 110,
                        "image": "b-4-1",
                        "bbox": [0.2, 0.4, 0.3, 0.5],
                        "children": [],
                    },
                    {
                        "type": "text",
                        "title": "4.1 Colectingand classifyingdata",
                        "block_ids": ["b-4-1"],
                        "page": 110,
                        "content": "The flow diagram shows data content",
                        "children": [],
                    },
                    {
                        "type": "text",
                        "title": "Exercise4.1",
                        "block_ids": ["b-ex-4-1-title"],
                        "page": 111,
                        "content": "",
                        "children": [
                            {
                                "type": "text",
                                "block_ids": ["b-ex-4-1-body-a"],
                                "page": 111,
                                "content": "Draw a table like this one.",
                                "children": [],
                            },
                            {
                                "type": "text",
                                "block_ids": ["b-ex-4-1-body-b"],
                                "page": 111,
                                "content": "Add five examples of categorical data.",
                                "children": [],
                            },
                        ],
                    },
                    {
                        "type": "text",
                        "title": "4.2 Organisingdata",
                        "block_ids": ["b-4-2"],
                        "page": 113,
                        "content": "This next section must not leak into 4.1.",
                        "children": [],
                    },
                ]},
            ]},
        ],
    }
    asset_hash_name = "71ef028a11659ad184c2c55a77eec9c6447b1168a81d59e273fb945c43d6929f.jpg"
    asset_index = {
        "images": [{
            "kind": "image",
            "asset_hash_name": asset_hash_name,
            "raw_ref": f"images/{asset_hash_name}",
            "source_index": 10,
            "source_order": 11,
            "page": 110,
            "bbox": [200, 400, 300, 500],
        }],
        "tables": [],
    }

    canonical_toc = service._compile_canonical_toc(review_tree, markdown)
    chapter_spans = service._compile_chapter_spans(canonical_toc)
    packs_manifest = service._compile_cleanlatex_pilot_packs(
        canonical_toc,
        chapter_spans,
        review_tree,
        "4134323036518274",
        "v-test",
        asset_index,
    )

    assert packs_manifest["schema"] == "luceon-cleanlatex-pack-manifest/v1"
    assert packs_manifest["selection_policy"]["schema"] == "luceon-cleanlatex-pack-selection-policy/v1"
    assert packs_manifest["stats"]["pack_count"] == 2
    packs = {pack["node"]["number"]: pack for pack in packs_manifest["packs"]}
    assert set(packs) == {"1.1", "4.1"}
    pack_11 = packs["1.1"]
    pack_41 = packs["4.1"]
    assert pack_11["schema"] == "luceon-cleanlatex-cleaning-unit-pack/v1"
    assert pack_11["pack_boundary"]["boundary_basis"] == "structure-level"
    assert pack_11["pack_boundary"]["semantic_kind_is_boundary_driver"] is False
    assert pack_11["pack_boundary"]["pack_level"] >= 3
    assert pack_11["node"]["canonical_kind"] == "section"
    assert pack_11["node"]["parent_title"] == "1 Review of number concepts"
    assert pack_41["node"]["parent_title"] == "4 Collectingorganisingand displayingdata"
    assert "b-1-1" in pack_11["source_span"]["source_block_ids"]
    assert "b-4-1" in pack_41["source_span"]["source_block_ids"]
    assert "b-ex-4-1-title" in pack_41["source_span"]["source_block_ids"]
    assert "b-ex-4-1-body-a" in pack_41["source_span"]["source_block_ids"]
    assert "b-ex-4-1-body-b" in pack_41["source_span"]["source_block_ids"]
    assert "b-4-2" not in pack_41["source_span"]["source_block_ids"]
    assert pack_41["source_span"]["span_expansion"]["expanded"] is True
    assert pack_11["content_blocks"][0]["block_id"] == "b-1-1"
    text_blocks_41 = [block for block in pack_41["content_blocks"] if block["block_id"] == "b-4-1"]
    assert text_blocks_41[0]["raw_text"].endswith("The flow diagram shows data content")
    body_blocks_41 = [block for block in pack_41["content_blocks"] if block["block_id"] == "b-ex-4-1-body-a"]
    assert body_blocks_41[0]["raw_text"] == "Draw a table like this one."
    assert not any(block["block_id"] == "b-4-2" for block in pack_41["content_blocks"])
    assert pack_41["assets"]["images"][0]["asset_hash_name"] == asset_hash_name
    assert "img-4-1" in pack_41["assets"]["images"][0]["source_block_ids"]
    assert pack_41["visual_evidence_requirements"][0]["status"] == "asset-linked"
    assert pack_41["visual_evidence_requirements"][0]["linked_asset_hash_names"] == [asset_hash_name]
    assert packs_manifest["prompts"][pack_11["pack_id"]].startswith("# CleanLaTeX Cleaning Unit Pack")
    assert "semantic label is guidance only" in packs_manifest["prompts"][pack_11["pack_id"]]
    assert asset_hash_name in packs_manifest["prompts"][pack_41["pack_id"]]
    validation = {item["pack_id"]: item for item in packs_manifest["validation_manifests"]}
    assert validation[pack_11["pack_id"]]["input_counts"]["unresolved_source_blocks"] == 0
    assert validation[pack_41["pack_id"]]["input_counts"]["images"] == 1
    assert validation[pack_41["pack_id"]]["output_checks"]["structure_boundary"] == "pending"

    full_manifest = service._compile_cleanlatex_pilot_packs(
        canonical_toc,
        chapter_spans,
        review_tree,
        "4134323036518274",
        "v-test",
        asset_index,
        selection_mode="full-book",
    )
    full_titles = {pack["node"]["title"] for pack in full_manifest["packs"]}
    full_numbers = {pack["node"]["number"] for pack in full_manifest["packs"]}
    assert "1.1 Different types of numbers" in full_titles
    assert "4.1" in full_numbers
    assert "4.2" in full_numbers
    assert "Exercise4.1" not in full_titles
    assert full_manifest["selection_mode"] == "full-book"


def test_cleanlatex_pack_boundary_uses_unbound_chapter_intro_as_hard_stop():
    canonical_toc = {
        "root": {
            "node_id": "toc-root",
            "kind": "root",
            "title": "root",
            "children": [
                {
                    "node_id": "toc-unit-2",
                    "kind": "unit",
                    "title": "Unit 2",
                    "parent_id": "toc-root",
                    "metadata": {"number": "2"},
                    "source_block_ids": [],
                    "children": [
                        {
                            "node_id": "toc-0039",
                            "kind": "chapter",
                            "title": "7 Perimeter,areaandvolume",
                            "parent_id": "toc-unit-2",
                            "metadata": {"number": "7"},
                            "source_block_ids": [],
                            "children": [
                                {
                                    "node_id": "toc-0042",
                                    "kind": "section",
                                    "title": "7.3 Surface areas and volumes of solids",
                                    "parent_id": "toc-0039",
                                    "metadata": {"number": "7.3"},
                                    "source_block_ids": ["b-7-3-title"],
                                    "children": [],
                                },
                            ],
                        },
                        {
                            "node_id": "toc-0043",
                            "kind": "chapter",
                            "title": "8 Introductiontoprobability",
                            "parent_id": "toc-unit-2",
                            "metadata": {"number": "8"},
                            "source_block_ids": [],
                            "children": [
                                {
                                    "node_id": "toc-0044",
                                    "kind": "section",
                                    "title": "8.1 Understandingbasic probability",
                                    "parent_id": "toc-0043",
                                    "metadata": {"number": "8.1"},
                                    "source_block_ids": ["b-8-1-title"],
                                    "children": [],
                                },
                            ],
                        },
                    ],
                },
            ],
        }
    }
    source_tree = {
        "type": "root",
        "title": "root",
        "children": [
            {
                "type": "text",
                "title": "7.3 Surface areas and volumes of solids",
                "block_ids": ["b-7-3-title"],
                "page": 219,
                "content": "Surface area and volume content starts here.",
                "children": [],
            },
            {
                "type": "text",
                "title": "",
                "block_ids": ["b-7-3-body"],
                "page": 220,
                "content": "More 7.3 content before the next chapter.",
                "children": [],
            },
            {
                "type": "text",
                "title": "Introduction to probability",
                "block_ids": ["b-8-intro-title"],
                "page": 227,
                "content": "IN THIS CHAPTER YOU WILL: express probabilities mathematically.",
                "children": [],
            },
            {
                "type": "text",
                "title": "8.1 Understandingbasic probability",
                "block_ids": ["b-8-1-title"],
                "page": 228,
                "content": "Basic probability content starts here.",
                "children": [],
            },
        ],
    }

    packs_manifest = service._compile_cleanlatex_pilot_packs(
        canonical_toc,
        {"spans": []},
        source_tree,
        "4134323036518274",
        "v-test",
        {},
        selection_mode="full-book",
    )

    packs = {pack["node"]["node_id"]: pack for pack in packs_manifest["packs"]}
    pack_73 = packs["toc-0042"]
    ids_73 = set(pack_73["source_span"]["source_block_ids"])
    assert "b-7-3-title" in ids_73
    assert "b-7-3-body" in ids_73
    assert "b-8-intro-title" not in ids_73
    assert "b-8-1-title" not in ids_73
    assert pack_73["source_span"]["span_expansion"]["strategy"] == "canonical-structure-lock-mechanical-slice"
    text_73 = "\n".join(str(block.get("raw_text") or "") for block in pack_73["content_blocks"])
    assert "Introduction to probability" not in text_73
    assert "IN THIS CHAPTER YOU WILL" not in text_73

    pack_81 = packs["toc-0044"]
    assert "b-8-1-title" in set(pack_81["source_span"]["source_block_ids"])


def test_release_host_mps_worker_posts_force_release_payload():
    captured = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            captured["path"] = self.path
            captured["payload"] = json.loads(body.decode("utf-8"))
            response = {
                "ok": True,
                "status": "terminating",
                "active_generations": 1,
            }
            encoded = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format, *args):
            return

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    old_url = os.environ.get("POPO_GENERATE_URL")
    try:
        os.environ["POPO_GENERATE_URL"] = f"http://127.0.0.1:{server.server_port}"
        result = service._release_host_mps_worker("job-canceled", force_terminate_if_busy=True)
    finally:
        if old_url is None:
            os.environ.pop("POPO_GENERATE_URL", None)
        else:
            os.environ["POPO_GENERATE_URL"] = old_url
        server.shutdown()
        thread.join(timeout=2)

    assert captured["path"] == "/release"
    assert captured["payload"] == {
        "reason": "job-canceled",
        "force_terminate_if_busy": True,
    }
    assert result["ok"] is True
    assert result["status"] == "terminating"


def test_live_progress_preserves_mps_worker_release_evidence():
    progress = service._get_live_progress({
        "payload": {"job_id": "missing-workdir", "material_id": "m1"},
        "start_time": time.time(),
        "current_step": "canceled",
        "mps_worker_release": {
            "ok": True,
            "status": "terminating",
            "active_generations": 1,
        },
    })

    assert progress["mps_worker_release"]["status"] == "terminating"
    assert progress["mps_worker_release"]["active_generations"] == 1


def test_full_background_progress_aware_wait_ignores_whole_job_timeout():
    old_job_timeout = service.JOB_TIMEOUT_SECONDS
    old_poll = service.FULL_BACKGROUND_POLL_SECONDS
    old_single = service.FULL_BACKGROUND_SINGLE_GENERATION_TIMEOUT_SECONDS
    old_health = service._host_mps_worker_health
    try:
        service.JOB_TIMEOUT_SECONDS = 1
        service.FULL_BACKGROUND_POLL_SECONDS = 0.1
        service.FULL_BACKGROUND_SINGLE_GENERATION_TIMEOUT_SECONDS = 60
        service._host_mps_worker_health = lambda: {
            "ok": True,
            "active_generations": 1,
            "generation_count": 1,
        }
        job_state = {
            "payload": {"job_id": "progress-aware-sleep", "material_id": "m1"},
            "start_time": time.time(),
            "canceled": False,
            "invocation": {
                "mode": "full-background",
                "recoverable": True,
            },
        }
        stdout = service._run_with_state(
            [sys.executable, "-c", "import time; time.sleep(1.5); print('done')"],
            Path.cwd(),
            job_state,
            "running_inference",
        )
    finally:
        service.JOB_TIMEOUT_SECONDS = old_job_timeout
        service.FULL_BACKGROUND_POLL_SECONDS = old_poll
        service.FULL_BACKGROUND_SINGLE_GENERATION_TIMEOUT_SECONDS = old_single
        service._host_mps_worker_health = old_health

    assert "done" in stdout
    assert job_state["long_run_policy"]["mode"] == "progress-aware"


def test_bounded_path_still_uses_whole_job_timeout():
    old_job_timeout = service.JOB_TIMEOUT_SECONDS
    try:
        service.JOB_TIMEOUT_SECONDS = 1
        job_state = {
            "payload": {"job_id": "bounded-sleep", "material_id": "m1"},
            "start_time": time.time(),
            "canceled": False,
            "invocation": {
                "mode": "bounded-preview",
                "recoverable": False,
            },
        }
        try:
            service._run_with_state(
                [sys.executable, "-c", "import time; time.sleep(2)"],
                Path.cwd(),
                job_state,
                "running_inference",
            )
            assert False, "bounded-preview should have timed out"
        except service.AdapterError as exc:
            assert exc.code == "timeout"
    finally:
        service.JOB_TIMEOUT_SECONDS = old_job_timeout


if __name__ == "__main__":
    test_wrapped_normalized_label_counts_pages_and_chunks()
    test_bounded_payload_keeps_large_original_estimate_but_limits_selected_work()
    test_live_progress_reads_real_pages_and_raw_chunk_metadata()
    test_toc_review_filter_keeps_outline_and_hides_full_document_noise()
    test_canonical_toc_compiler_builds_traceable_chapter_scaffold_without_llm_structure()
    test_contents_first_canonical_toc_uses_book_contents_as_global_spine()
    test_contents_first_recovers_implicit_chapters_and_reparents_orphan_exercises()
    test_cleanlatex_pilot_packs_are_structure_level_and_source_bound()
    test_release_host_mps_worker_posts_force_release_payload()
    test_live_progress_preserves_mps_worker_release_evidence()
    test_full_background_progress_aware_wait_ignores_whole_job_timeout()
    test_bounded_path_still_uses_whole_job_timeout()
    print("PASS popo invocation boundary tests")
