# Task: P0 Production AI JSON Repair Ollama Timeout Diagnosis

```text
Task:
P0 Production AI JSON Repair Ollama Timeout Diagnosis

Assignee:
Lucode

Issued by:
Lucia

Project:
Luceon2026

Date:
2026-05-07

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-07T10-41-51+0800_P0-Production-AI-JSON-Repair-Ollama-Timeout-Diagnosis_TASK.md

Required reading before execution:
- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/lucode.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/codex/TEST_POLICY.md
- docs/prd/Luceon2026-PRD-v0.4.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-07T10-34-23+0800_P0-Production-Ops-Sidecar-Supervisor-Recovery_SUPPLEMENTAL_REPORT.md

Background:
Production manual review shows that MinerU parsing can complete while the AI metadata stage blocks or fails under Ollama `qwen3.5:9b`.

Known evidence:
- `task-1778118934116` failed after MinerU completed because Ollama metadata recognition timed out at about `299998ms` with a `300000ms` timeout.
- `task-1778120784621` reached `stage=ai`, `state=ai-running`, message `AI: 正在进行 JSON Repair...`.
- AI job `ai-job-1778120889758-8cab` was in `repair-pass-running`.
- Direct Ollama `/api/tags` returned, but `/api/chat` with `qwen3.5:9b` timed out after 20s.
- Dependency-health reported `ollama.ok=false`, `chatOk=false`, `durationMs=15002`, `Smoke test failed: The operation was aborted due to timeout`.
- Strict no-skeleton semantics must be preserved.

Objective:
Diagnose why Ollama `qwen3.5:9b` blocks during AI JSON Repair and recommend the smallest safe remediation path. Execute only read-only diagnostics unless the task finds an explicitly safe non-code operational check.

Non-goals:
- Do not implement code changes.
- Do not restart Ollama unless Lucia explicitly authorizes in a separate task.
- Do not retry or mutate `task-1778118934116` or `task-1778120784621`.
- Do not change timeout policy, prompt policy, model policy, or fallback semantics.
- Do not claim production release readiness.
- Do not enable skeleton fallback.

Required investigation:
1. Confirm current production URL and production HEAD.
2. Inspect current dependency-health with `mineruSubmitProbe=true`.
3. Inspect direct Ollama health:
   - `/api/tags`
   - a minimal `/api/chat` request with short timeout
   - process list and resource state where available
4. Inspect AI job state and task state for:
   - `task-1778118934116`
   - `ai-job-1778119321533-4dce`
   - `task-1778120784621`
   - `ai-job-1778120889758-8cab`
5. Inspect upload-server logs around:
   - provider request start
   - first pass failure
   - repair pass start
   - timeout or abort events
6. Inspect `server/services/ai/metadata-worker.mjs` and provider configuration to identify:
   - repair pass timeout source
   - repair pass `num_predict`
   - prompt/input size behavior
   - stale running job recovery behavior
   - whether the worker can leave an AI job in `running` longer than expected
7. Classify the likely root cause as one or more of:
   - Ollama process/model performance issue
   - repair prompt/input size issue
   - timeout policy mismatch
   - AI job stale-state handling issue
   - malformed output repair loop issue
   - unknown, with missing evidence listed
8. Recommend one next task only if remediation is needed. The recommendation must preserve strict no-skeleton semantics.

Allowed commands:
- `curl` read-only HTTP checks
- `docker compose logs --tail=... upload-server`
- `ps`, `top`, `vm_stat`, or equivalent read-only system inspection
- `sed`, `rg`, `git show`, `git diff` read-only code inspection
- direct Ollama read-only test prompts with explicit timeout

Forbidden operations:
- Do not restart Ollama.
- Do not restart containers.
- Do not restart MinerU.
- Do not mutate AI jobs, parse tasks, DB files, MinIO objects, or logs.
- Do not run Re-AI, Retry, Reparse, or repair actions.
- Do not change code or config.
- Do not delete data or run destructive cleanup.

Required report evidence:
- Exact commands and exit codes.
- Current dependency-health result.
- Direct Ollama `/api/tags` and `/api/chat` results.
- Current task/job states for the two affected tasks.
- Relevant upload-server log excerpts.
- Code/config observations with file paths and line references.
- Root-cause classification.
- Recommended next remediation task, or statement that no remediation task is justified.

Completion report storage requirements:
- Write the report into TaskAndReport/:
  `YYYY-MM-DDTHH-MM-SS+0800_P0-Production-AI-JSON-Repair-Ollama-Timeout-Diagnosis_REPORT.md`
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, status, next actor, and evidence summary.
- Commit and push only task/report tracking changes to GitHub `main`.

Acceptance criteria:
- Lucia can determine whether the AI blockage is operational, code/prompt-level, timeout-policy-level, or still unknown.
- Existing tasks are not mutated.
- Strict no-skeleton semantics remain unchanged.
```
