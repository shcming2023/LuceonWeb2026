import pytest
from fastapi import HTTPException

from app.api.workflow_v2 import _merge_review_blockers, _review_restart_stage, revalidate_review_candidate
from app.workflow_v2.service import create_workflow_job
from test_workflow_v2 import make_sessions


def test_review_evidence_merges_current_and_candidate_blockers_without_duplicates():
    current = {"blockers": [{"code": "latex_project_structure_invalid", "detail": "missing images/"}]}
    candidate = {"blockers": [{"code": "latex_missing_glyphs", "count": 2}]}

    assert _merge_review_blockers(current, candidate, candidate) == [
        {"code": "latex_project_structure_invalid", "detail": "missing images/"},
        {"code": "latex_missing_glyphs", "count": 2},
    ]


def test_review_restarts_earliest_layout_stage_only_for_candidate_structure_repairs():
    structure = [{"code": "latex_project_structure_invalid", "detail": "missing images/"}]
    legacy_structure = [
        {
            "code": "latex_project_zip_too_large",
            "detail": "LaTeX delivery is missing required paths: images/",
        }
    ]

    assert _review_restart_stage("bounded_deepseek_polish_qa", structure) == "deterministic_elegantbook"
    assert _review_restart_stage("bounded_deepseek_polish_qa", legacy_structure) == "deterministic_elegantbook"
    assert _review_restart_stage("bounded_deepseek_polish_qa", [{"code": "outline_gate_not_passed"}]) == "bounded_deepseek_polish_qa"
    assert _review_restart_stage("deterministic_elegantbook", structure) == "deterministic_elegantbook"


def test_revalidate_rejects_needs_review_job_without_manual_handoff():
    _old_db, workflow_db, material = make_sessions()
    job, _ = create_workflow_job(workflow_db, user_id="u1", material=material)
    job.status = "needs_review"
    workflow_db.commit()

    with pytest.raises(HTTPException) as exc_info:
        revalidate_review_candidate(job.public_id, user_id="u1", workflow_db=workflow_db)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "请先登记转人工处理，再重新验证候选件"
