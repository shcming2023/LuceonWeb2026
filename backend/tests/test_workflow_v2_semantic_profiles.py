import json
from pathlib import Path

from app.workflow_v2.runtime.semantic.scripts.annotate_material import (
    annotate_assets,
    build_sections,
    detect_profile,
    load_profile,
    parse_markdown,
)


def test_all_detectable_semantic_profiles_are_vendored() -> None:
    profile_dir = Path(__file__).parents[1] / "app" / "workflow_v2" / "runtime" / "semantic" / "profiles"
    names = {path.stem for path in profile_dir.glob("*.json")}
    assert names == {"english_grammar_workbook", "general_textbook", "math_workbook"}
    for name in names:
        profile = load_profile(name)
        assert profile["id"] == name
        assert profile["section_role_rules"]
        assert profile["asset_role_rules"]
        json.dumps(profile)


def test_profile_detection_covers_golden_material_families() -> None:
    assert detect_profile("# Chapter 1\nReading and Writing\nQuestions") == "general_textbook"
    assert detect_profile("# Unit 1\n## Grammar Point 1\n## Grammar Practice 1") == "english_grammar_workbook"
    assert detect_profile("# 第1章 数与代数\n## 要点归纳\n## 基础训练\n## 例1") == "math_workbook"


def test_parent_content_around_children_is_assigned_without_overlap() -> None:
    markdown = """# Chapter 1
Chapter introduction
![cover](images/cover.png)
## Lesson 1
Lesson body
Parent transition
## Lesson 2
Second body
Parent conclusion
"""
    blocks = parse_markdown(markdown)
    profile = load_profile("general_textbook")
    sections = build_sections(blocks, profile)

    assets = annotate_assets(blocks, sections, profile)

    covered = [
        line
        for asset in assets
        for line in range(asset["source_span"]["start_line"], asset["source_span"]["end_line"] + 1)
        if any(block["line"] == line and block["type"] in {"text", "image", "table"} for block in blocks)
    ]
    expected = [block["line"] for block in blocks if block["type"] in {"text", "image", "table"}]
    assert sorted(covered) == expected
    assert len(covered) == len(set(covered))
    assert any(asset["section_id"] == sections[0]["id"] for asset in assets)


def test_image_only_parent_preamble_is_preserved_as_asset() -> None:
    markdown = """# Chapter 1
![opening](images/opening.png)
## Lesson 1
Lesson body
"""
    blocks = parse_markdown(markdown)
    profile = load_profile("general_textbook")
    sections = build_sections(blocks, profile)

    assets = annotate_assets(blocks, sections, profile)

    parent_assets = [asset for asset in assets if asset["section_id"] == sections[0]["id"]]
    assert len(parent_assets) == 1
    assert parent_assets[0]["source_span"]["start_line"] == 2
    assert parent_assets[0]["source_span"]["end_line"] == 2


def test_image_alt_can_contain_bracketed_geometry_labels() -> None:
    blocks = parse_markdown("![Join edges [AB] and [CB]](images/net.jpg)\n")

    assert blocks == [{
        "type": "image",
        "line": 1,
        "alt": "Join edges [AB] and [CB]",
        "src": "images/net.jpg",
        "text": "![Join edges [AB] and [CB]](images/net.jpg)",
        "page_idx": None,
    }]


def test_content_before_first_heading_is_assigned_to_document_preamble() -> None:
    markdown = """<!-- page_idx: 1 -->
![cover](images/cover.png)
Printed page number
# Chapter 1
Body
"""
    blocks = parse_markdown(markdown)
    profile = load_profile("general_textbook")
    sections = build_sections(blocks, profile)

    assets = annotate_assets(blocks, sections, profile)

    preamble = [asset for asset in assets if asset["role"] == "document_preamble"]
    assert len(preamble) == 1
    assert preamble[0]["section_id"] == sections[0]["id"]
    assert preamble[0]["source_span"]["start_line"] == 1
    assert preamble[0]["source_span"]["end_line"] == 3
