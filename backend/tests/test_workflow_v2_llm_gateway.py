import json

import pytest

from app.workflow_v2.llm_gateway import LlmGatewayError, plan_latex_repairs, resolve_bounded_ambiguities


class FakeResponse:
    status_code = 200
    text = ""

    def __init__(self, content):
        self.content = content

    def json(self):
        return {
            "id": "response-1",
            "choices": [{"message": {"content": json.dumps(self.content)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
        }


class FakeClient:
    response = None

    def __init__(self, **_kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def post(self, *_args, **_kwargs):
        return FakeResponse(self.response)


def test_gateway_accepts_only_allowlisted_plan(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    FakeClient.response = {
        "actions": ["route_upstream_findings", "require_independent_visual_qa"],
        "dispositions": [{"finding_code": "orphan", "owner": "deterministic_repair", "reason": "bounded"}],
        "rationale": "Use project code.",
    }
    monkeypatch.setattr("app.workflow_v2.llm_gateway.httpx.Client", FakeClient)
    result = plan_latex_repairs(findings=[{"code": "orphan"}], metrics={"output_pages": 3})
    assert result["plan"]["actions"] == ["route_upstream_findings", "require_independent_visual_qa"]
    assert result["audit"]["response_id"] == "response-1"
    assert result["audit"]["usage"]["total_tokens"] == 120


def test_gateway_rejects_disallowed_action(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    FakeClient.response = {"actions": ["publish_to_minio"], "dispositions": [], "rationale": "unsafe"}
    monkeypatch.setattr("app.workflow_v2.llm_gateway.httpx.Client", FakeClient)
    with pytest.raises(LlmGatewayError, match="disallowed"):
        plan_latex_repairs(findings=[{"code": "orphan"}], metrics={})


def test_gateway_discards_dispositions_for_unknown_findings(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    unknown = {"finding_code": "invented", "owner": "upstream", "reason": "not in evidence"}
    FakeClient.response = {
        "actions": ["require_independent_visual_qa"],
        "dispositions": [unknown],
        "rationale": "Continue to independent QA.",
    }
    monkeypatch.setattr("app.workflow_v2.llm_gateway.httpx.Client", FakeClient)

    result = plan_latex_repairs(findings=[], metrics={"output_pages": 3})

    assert result["plan"]["dispositions"] == []
    assert result["audit"]["discarded_dispositions"] == [unknown]


def test_gateway_rejects_whole_project_refiner(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    FakeClient.response = {"actions": ["apply_artifact_refiner"], "dispositions": [], "rationale": "too broad"}
    monkeypatch.setattr("app.workflow_v2.llm_gateway.httpx.Client", FakeClient)
    with pytest.raises(LlmGatewayError, match="disallowed"):
        plan_latex_repairs(findings=[{"code": "orphan"}], metrics={})


def test_gateway_rejects_broad_workbook_repair(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    FakeClient.response = {"actions": ["apply_workbook_repairs"], "dispositions": [], "rationale": "too broad"}
    monkeypatch.setattr("app.workflow_v2.llm_gateway.httpx.Client", FakeClient)
    with pytest.raises(LlmGatewayError, match="disallowed"):
        plan_latex_repairs(findings=[{"code": "orphan"}], metrics={})


def _bounded_task():
    return {
        "task_id": "heading-1",
        "task_type": "heading_classification",
        "question": "Is this a heading or body text?",
        "evidence": [{"page_idx": 4, "source_block_id": "content-list-000010"}],
        "options": [
            {"option_id": "heading", "value": "heading"},
            {"option_id": "body", "value": "body"},
        ],
    }


def test_bounded_gateway_skips_api_when_there_are_no_tasks(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    result = resolve_bounded_ambiguities(tasks=[])

    assert result["decisions"] == []
    assert result["audit"]["call_count"] == 0


def test_bounded_gateway_can_only_select_a_supplied_option(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    FakeClient.response = {
        "decisions": [{
            "task_id": "heading-1",
            "selected_option_id": "heading",
            "confidence": 0.92,
            "reason": "Matches the supplied layout evidence.",
        }],
    }
    monkeypatch.setattr("app.workflow_v2.llm_gateway.httpx.Client", FakeClient)

    result = resolve_bounded_ambiguities(tasks=[_bounded_task()])

    assert result["decisions"][0]["selected_option_id"] == "heading"
    assert result["audit"]["call_count"] == 1


def test_bounded_gateway_rejects_invented_option(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    FakeClient.response = {
        "decisions": [{
            "task_id": "heading-1",
            "selected_option_id": "rewrite_everything",
            "confidence": 1,
            "reason": "invented",
        }],
    }
    monkeypatch.setattr("app.workflow_v2.llm_gateway.httpx.Client", FakeClient)

    with pytest.raises(LlmGatewayError, match="unknown option"):
        resolve_bounded_ambiguities(tasks=[_bounded_task()])


def test_bounded_gateway_requires_evidence_and_finite_options():
    task = _bounded_task()
    task["evidence"] = []

    with pytest.raises(LlmGatewayError, match="structured evidence"):
        resolve_bounded_ambiguities(tasks=[task])
