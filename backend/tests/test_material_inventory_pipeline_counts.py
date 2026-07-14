from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.material import Material, MaterialOutput
from app.services.material_inventory import pipeline_result_counts, pipeline_run_outcome
from app.services.material_inventory import assign_input_review_asset
from app.services.material_inventory import material_summary
from app.services.material_outputs import _ensure_single_current


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


def test_pipeline_run_outcome_does_not_project_partial_as_success():
    assert pipeline_run_outcome({"status": "DONE"}, returncode=0, apply=True) == "succeeded"
    assert pipeline_run_outcome({"status": "PARTIAL"}, returncode=0, apply=True) == "partial"
    assert pipeline_run_outcome({"status": "PARTIAL"}, returncode=3, apply=True) == "partial"
    assert pipeline_run_outcome({"status": "MINERU_WAIT_INCOMPLETE"}, returncode=3, apply=True) == "failed"


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


def test_material_summary_excludes_ignored_rows():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all(
        [
            Material(user_id="u1", title="Visible", filename="visible.pdf", stage_status="popo_done", ignored=False),
            Material(user_id="u1", title="Archived", filename="archived.pdf", stage_status="latex_done", ignored=True),
        ]
    )
    db.commit()

    summary = material_summary(db, "u1")

    assert summary["total"] == 1
    assert summary["stages"]["popo_done"] == 1
    assert summary["stages"]["latex_done"] == 0


def test_output_registry_projects_existing_winner_back_to_material():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    material = Material(
        user_id="u1", material_id="pdf-1", title="Book", filename="book.pdf",
        stage_status="popo_done", popo_manifest_bucket="popo", popo_manifest_object="popo/manifest.json",
    )
    db.add(material)
    db.flush()
    winner = MaterialOutput(
        user_id="u1", material_pk=material.id, material_id=material.material_id,
        output_type="elegantbook", origin="legacy_selfloop", status="promoted",
        quality_status="passed", is_current=False, manifest_bucket="elegant",
        manifest_object="elegant/pdf-1/manifest.json", output_run_id="legacy-1",
    )
    db.add(winner)
    db.flush()

    _ensure_single_current(db, "u1", material, [])

    assert winner.is_current is True
    assert material.stage_status == "latex_done"
    assert material.latex_manifest_object == winner.manifest_object
