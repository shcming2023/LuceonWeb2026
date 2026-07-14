from __future__ import annotations

import hashlib
import json
import os

import httpx


ALLOWED_ACTIONS = {
    "route_upstream_findings",
    "require_independent_visual_qa",
}

REPAIR_PLAN_PROMPT_VERSION = "bounded-repair-plan-v3"
BOUNDED_AMBIGUITY_PROMPT_VERSION = "bounded-ambiguity-choice-v1"
BOUNDED_TASK_TYPES = {
    "ocr_choice",
    "heading_classification",
    "segment_relation",
    "component_relation",
}


class LlmGatewayError(RuntimeError):
    pass


def resolve_bounded_ambiguities(*, tasks: list[dict]) -> dict:
    normalized = _validate_bounded_tasks(tasks)
    if not normalized:
        return {
            "decisions": [],
            "audit": {
                "provider": "deepseek",
                "model": "",
                "response_id": "",
                "usage": {},
                "estimated_cost": 0,
                "input_evidence_sha256": hashlib.sha256(b"[]").hexdigest(),
                "call_count": 0,
                "prompt_version": BOUNDED_AMBIGUITY_PROMPT_VERSION,
            },
        }
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise LlmGatewayError("DEEPSEEK_API_KEY is unavailable")
    model = os.getenv("DEEPSEEK_FLASH_MODEL") or os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"
    evidence_bytes = json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode("utf-8")
    system = (
        "Choose exactly one supplied option for every bounded ambiguity task. Return one JSON object only. "
        "Never rewrite source content, invent an option, omit a task, decide publication, or claim a quality gate passed. "
        "Schema: {decisions:[{task_id:string,selected_option_id:string,confidence:number,reason:string}]}."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps({"tasks": normalized}, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 4000,
    }
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    with httpx.Client(timeout=180) as client:
        response = client.post(f"{base_url}/chat/completions", headers={"Authorization": f"Bearer {api_key}"}, json=payload)
    if response.status_code >= 400:
        raise LlmGatewayError(f"LLM gateway returned {response.status_code}: {response.text[-1000:]}")
    raw = response.json()
    try:
        result = json.loads(raw["choices"][0]["message"]["content"])
    except Exception as exc:
        raise LlmGatewayError("LLM response was not valid JSON") from exc
    decisions = _validate_bounded_decisions(normalized, result.get("decisions"))
    usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    return {
        "decisions": decisions,
        "audit": {
            "provider": "deepseek",
            "model": model,
            "response_id": str(raw.get("id") or ""),
            "usage": usage,
            "estimated_cost": round(prompt_tokens * 0.27 / 1_000_000 + completion_tokens * 1.10 / 1_000_000, 6),
            "input_evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "call_count": 1,
            "prompt_version": BOUNDED_AMBIGUITY_PROMPT_VERSION,
        },
    }


def _validate_bounded_tasks(tasks: list[dict]) -> list[dict]:
    if not isinstance(tasks, list):
        raise LlmGatewayError("bounded tasks must be an array")
    normalized = []
    seen = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise LlmGatewayError("each bounded task must be an object")
        task_id = str(task.get("task_id") or "").strip()
        task_type = str(task.get("task_type") or "").strip()
        evidence = task.get("evidence")
        options = task.get("options")
        if not task_id or task_id in seen:
            raise LlmGatewayError("bounded task ids must be non-empty and unique")
        if task_type not in BOUNDED_TASK_TYPES:
            raise LlmGatewayError(f"unsupported bounded task type: {task_type}")
        if not isinstance(evidence, list) or not evidence or not all(isinstance(row, dict) for row in evidence):
            raise LlmGatewayError(f"bounded task {task_id} requires structured evidence")
        if not isinstance(options, list) or not 2 <= len(options) <= 5:
            raise LlmGatewayError(f"bounded task {task_id} requires two to five options")
        option_ids = [str(row.get("option_id") or "").strip() for row in options if isinstance(row, dict)]
        if len(option_ids) != len(options) or any(not value for value in option_ids) or len(set(option_ids)) != len(option_ids):
            raise LlmGatewayError(f"bounded task {task_id} option ids must be non-empty and unique")
        seen.add(task_id)
        normalized.append({
            "task_id": task_id,
            "task_type": task_type,
            "question": str(task.get("question") or "").strip(),
            "evidence": evidence,
            "options": options,
        })
    return normalized


def _validate_bounded_decisions(tasks: list[dict], decisions) -> list[dict]:
    if not isinstance(decisions, list):
        raise LlmGatewayError("LLM decisions must be an array")
    task_by_id = {task["task_id"]: task for task in tasks}
    rows = {}
    for decision in decisions:
        if not isinstance(decision, dict):
            raise LlmGatewayError("each LLM decision must be an object")
        task_id = str(decision.get("task_id") or "")
        if task_id not in task_by_id or task_id in rows:
            raise LlmGatewayError("LLM returned an unknown or duplicate task id")
        option_id = str(decision.get("selected_option_id") or "")
        allowed = {str(row["option_id"]) for row in task_by_id[task_id]["options"]}
        if option_id not in allowed:
            raise LlmGatewayError(f"LLM selected an unknown option for task {task_id}")
        try:
            confidence = float(decision.get("confidence"))
        except (TypeError, ValueError) as exc:
            raise LlmGatewayError(f"LLM confidence is invalid for task {task_id}") from exc
        if not 0 <= confidence <= 1:
            raise LlmGatewayError(f"LLM confidence is out of range for task {task_id}")
        rows[task_id] = {
            "task_id": task_id,
            "selected_option_id": option_id,
            "confidence": confidence,
            "reason": str(decision.get("reason") or ""),
        }
    if set(rows) != set(task_by_id):
        raise LlmGatewayError("LLM did not decide every bounded task")
    return [rows[task["task_id"]] for task in tasks]


def plan_latex_repairs(*, findings: list[dict], metrics: dict) -> dict:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise LlmGatewayError("DEEPSEEK_API_KEY is unavailable")
    model = os.getenv("DEEPSEEK_FLASH_MODEL") or os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"
    evidence = {"findings": findings, "metrics": metrics}
    evidence_bytes = json.dumps(evidence, ensure_ascii=False, sort_keys=True).encode("utf-8")
    known_codes = {str(row.get("code") or "") for row in findings}
    system = (
        "You are a bounded LaTeX repair planner. Return one JSON object only. "
        "You cannot rewrite source content, accept QA, publish artifacts, or invent missing text. "
        "Allowed actions are: route_upstream_findings, require_independent_visual_qa. "
        "Do not request whole-project rewriting or broad deterministic workbook repair. Content patches are handled only by the later page-scoped repair sidecar. "
        "Schema: {actions:[string], dispositions:[{finding_code:string,owner:deterministic_repair|upstream|independent_qa,reason:string}], rationale:string}. "
        f"Known finding_code values are exactly: {sorted(known_codes)}. If this list is empty, dispositions must be empty."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(evidence, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 4000,
    }
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    with httpx.Client(timeout=180) as client:
        response = client.post(f"{base_url}/chat/completions", headers={"Authorization": f"Bearer {api_key}"}, json=payload)
    if response.status_code >= 400:
        raise LlmGatewayError(f"LLM gateway returned {response.status_code}: {response.text[-1000:]}")
    raw = response.json()
    try:
        plan = json.loads(raw["choices"][0]["message"]["content"])
    except Exception as exc:
        raise LlmGatewayError("LLM response was not valid JSON") from exc
    actions = plan.get("actions") if isinstance(plan.get("actions"), list) else []
    unknown = sorted(set(map(str, actions)) - ALLOWED_ACTIONS)
    if unknown:
        raise LlmGatewayError(f"LLM requested disallowed actions: {', '.join(unknown)}")
    dispositions = plan.get("dispositions") if isinstance(plan.get("dispositions"), list) else []
    valid_dispositions = []
    discarded_dispositions = []
    for row in dispositions:
        if not isinstance(row, dict) or row.get("finding_code") not in known_codes:
            discarded_dispositions.append(row)
            continue
        if row.get("owner") not in {"deterministic_repair", "upstream", "independent_qa"}:
            discarded_dispositions.append(row)
            continue
        valid_dispositions.append(row)
    usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    return {
        "plan": {"actions": actions, "dispositions": valid_dispositions, "rationale": str(plan.get("rationale") or "")},
        "audit": {
            "provider": "deepseek",
            "model": model,
            "response_id": str(raw.get("id") or ""),
            "usage": usage,
            "estimated_cost": round(prompt_tokens * 0.27 / 1_000_000 + completion_tokens * 1.10 / 1_000_000, 6),
            "input_evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "discarded_dispositions": discarded_dispositions,
        },
    }
