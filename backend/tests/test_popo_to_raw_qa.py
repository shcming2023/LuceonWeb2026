import pytest

from app.services.popo_to_raw import heading_order_report, validate_outline_mechanical_qa


def base_outline_summary(**overrides):
    summary = {
        "outline_decision": {
            "available": True,
            "decision_method": "llm_global_candidate_outline",
            "final_outline_count": 3,
            "selected_count": 3,
            "llm": {"call_count": 1},
        },
        "outline_candidates_summary": {"candidate_type_counts": {}},
        "visual_decisions": {"enabled": False, "error_count": 0},
        "outline_apply_report": {
            "unit_count": 3,
            "unassigned_block_count": 0,
            "leaf_units_without_blocks_count": 0,
            "container_units_without_direct_blocks_count": 0,
        },
        "image_closure_report": {"missing_image_count": 0, "markdown_refs_not_copied_count": 0},
        "chunk_boundary_report": {
            "unit_count": 3,
            "empty_leaf_count": 0,
            "source_empty_chunk_count": 0,
            "max_heading_level": 2,
        },
        "heading_order_report": {
            "available": True,
            "parent_order_violation_count": 0,
            "parent_level_violation_count": 0,
            "duplicate_same_parent_count": 0,
        },
    }
    summary.update(overrides)
    return summary


def test_heading_order_report_flags_duplicate_root_headings(tmp_path):
    clean_md = tmp_path / "clean.md"
    clean_md.write_text(
        "\n".join(
            [
                "# Review 1",
                "first chunk",
                "# Review 1",
                "second chunk",
            ]
        ),
        encoding="utf-8",
    )

    report = heading_order_report(clean_md)

    assert report["duplicate_same_parent_count"] == 1
    assert report["duplicate_same_parent_headings"][0]["title"] == "Review 1"
    assert report["duplicate_same_parent_headings"][0]["lines"] == [1, 3]


def test_heading_order_report_allows_same_topic_under_different_parents(tmp_path):
    clean_md = tmp_path / "clean.md"
    clean_md.write_text(
        "\n".join(
            [
                "# Unit 1",
                "## Practice",
                "one",
                "# Unit 2",
                "## Practice",
                "two",
            ]
        ),
        encoding="utf-8",
    )

    report = heading_order_report(clean_md)

    assert report["duplicate_same_parent_count"] == 0


def test_heading_order_report_flags_numbered_units_nested_under_non_structural_parent(tmp_path):
    clean_md = tmp_path / "clean.md"
    clean_md.write_text(
        "\n".join(
            [
                "# Starter",
                "## 1 First prize!",
                "## 2 Will we have any homework?",
                "## 3 A celebration",
            ]
        ),
        encoding="utf-8",
    )

    report = heading_order_report(clean_md)

    assert report["nested_numbered_major_heading_count"] == 1
    assert report["nested_numbered_major_headings"][0]["parent_path"] == "Starter"


def test_heading_order_report_allows_numbered_units_under_structural_parent(tmp_path):
    clean_md = tmp_path / "clean.md"
    clean_md.write_text(
        "\n".join(
            [
                "# Part 1 Grammar",
                "## 1 First prize!",
                "## 2 Will we have any homework?",
                "## 3 A celebration",
            ]
        ),
        encoding="utf-8",
    )

    report = heading_order_report(clean_md)

    assert report["nested_numbered_major_heading_count"] == 0


def test_validate_outline_mechanical_qa_blocks_duplicate_same_parent_headings():
    summary = base_outline_summary(
        heading_order_report={
            "available": True,
            "parent_order_violation_count": 0,
            "parent_level_violation_count": 0,
            "duplicate_same_parent_count": 1,
        }
    )

    with pytest.raises(RuntimeError, match="duplicate_same_parent_headings:1"):
        validate_outline_mechanical_qa(summary)


def test_validate_outline_mechanical_qa_blocks_nested_numbered_major_headings():
    summary = base_outline_summary(
        heading_order_report={
            "available": True,
            "parent_order_violation_count": 0,
            "parent_level_violation_count": 0,
            "duplicate_same_parent_count": 0,
            "nested_numbered_major_heading_count": 1,
        }
    )

    with pytest.raises(RuntimeError, match="nested_numbered_major_headings:1"):
        validate_outline_mechanical_qa(summary)


def test_validate_outline_mechanical_qa_blocks_extra_units_after_llm_outline():
    summary = base_outline_summary(
        outline_apply_report={"unit_count": 4, "unassigned_block_count": 0},
        chunk_boundary_report={
            "unit_count": 4,
            "empty_leaf_count": 0,
            "source_empty_chunk_count": 0,
            "max_heading_level": 2,
        },
    )

    with pytest.raises(RuntimeError, match="raw_units_exceed_final_outline:4>3"):
        validate_outline_mechanical_qa(summary)
