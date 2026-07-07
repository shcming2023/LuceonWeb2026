from types import SimpleNamespace

import pytest

from app.services.material_inventory import pipeline_result_counts
from app.services.material_inventory import assign_input_review_asset


def test_pipeline_result_counts_reads_done_popo_freezes():
    payload = {
        "status": "DONE",
        "selected_count": 1,
        "mineru_freezes": [{"manifest": {}}],
        "mineru_errors": [],
        "popo": {"freezes": [{"manifest": {}}], "errors": []},
    }

    assert pipeline_result_counts(payload) == {"total": 1, "processed": 1, "success": 1, "failed": 0}


def test_pipeline_result_counts_marks_unfinished_partial_items_failed():
    payload = {
        "status": "PARTIAL",
        "selected_count": 3,
        "popo": {"freezes": [{"manifest": {}}], "errors": [{"error": "boom"}]},
    }

    assert pipeline_result_counts(payload) == {"total": 3, "processed": 3, "success": 1, "failed": 2}


def test_pipeline_result_counts_handles_mineru_only_success():
    payload = {
        "status": "MINERU_DONE_FROZEN",
        "selected_count": 2,
        "mineru_freezes": [{"manifest": {}}, {"manifest": {}}],
        "mineru_errors": [],
    }

    assert pipeline_result_counts(payload) == {"total": 2, "processed": 2, "success": 2, "failed": 0}


def test_pipeline_result_counts_handles_mineru_only_partial():
    payload = {
        "status": "PARTIAL",
        "selected_count": 3,
        "mineru_freezes": [{"manifest": {}}],
        "mineru_errors": [{"error": "boom"}],
        "popo": {},
    }

    assert pipeline_result_counts(payload) == {"total": 3, "processed": 3, "success": 1, "failed": 2}


@pytest.mark.parametrize(
    "stage_field",
    [
        "mineru_manifest_object",
        "popo_manifest_object",
        "latex_manifest_object",
        "raw_manifest_object",
        "clean_manifest_object",
        "standard_manifest_object",
    ],
)
def test_assign_input_review_asset_preserves_any_downstream_review_asset(stage_field):
    material = SimpleNamespace(
        review_asset_id=20,
        mineru_manifest_object="",
        popo_manifest_object="",
        latex_manifest_object="",
        raw_manifest_object="",
        clean_manifest_object="",
        standard_manifest_object="",
    )
    setattr(material, stage_field, f"{stage_field}/manifest.json")
    asset = SimpleNamespace(id=10)

    assign_input_review_asset(material, asset)

    assert material.review_asset_id == 20


def test_assign_input_review_asset_sets_initial_input_asset():
    material = SimpleNamespace(
        review_asset_id=None,
        mineru_manifest_object="",
        popo_manifest_object="",
        latex_manifest_object="",
        raw_manifest_object="",
        clean_manifest_object="",
        standard_manifest_object="",
    )
    asset = SimpleNamespace(id=10)

    assign_input_review_asset(material, asset)

    assert material.review_asset_id == 10
