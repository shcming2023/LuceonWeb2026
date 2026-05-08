# Lucia Task Brief: P1 Active-Task Historical AI Failure Classification Fix

Task:
P1 Active-Task Historical AI Failure Classification Fix

Assignee:
Lucode

Issued by:
Lucia

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-09T06-37-09+0800_P1-Active-Task-Historical-AI-Failure-Classification-Fix_TASK.md

Required reading before execution:
- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/lucode.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-09T06-33-34+0800_P1-Post-Recovery-Residual-Runtime-Diagnostics_REPORT.md
- TaskAndReport/2026-05-09T06-37-09+0800_P1-Post-Recovery-Residual-Runtime-Diagnostics_LUCIA_REVIEW.md

Background:
Task 49 confirmed that `/__proxy/upload/ops/mineru/active-task` still reports three `takeoverRequiredTasks`, but those tasks are historical terminal AI failures rather than active MinerU ingestion/recovery work. The current diagnostic label can confuse readiness reporting by suggesting that MinerU takeover remains required.

Current known facts:
- Affected historical task IDs:
  - `task-1778222027064`
  - `task-1778120784621`
  - `task-1778118934116`
- They are `state=failed`, `stage=ai` historical AI failures with MinerU completion/artifacts.
- There is no active/current/queued/completed-but-not-ingested/drift/submit-retryable MinerU work at the time of Task 49.
- Strict no-skeleton semantics must remain unchanged.

Objective:
Adjust active-task diagnostics so historical terminal AI failures are not mislabeled as `takeoverRequiredTasks`. They should either be excluded from takeover-required output or surfaced under a clearer non-actionable/historical AI-failure diagnostic bucket, with tests covering the classification.

Non-goals:
- Do not repair, retry, reparse, requeue, or mutate any production task.
- Do not change production data or production runtime.
- Do not change AI failure semantics, skeleton fallback behavior, model config, timeout config, or readiness policy.
- Do not delete or archive historical tasks/materials.
- Do not declare production release readiness, UAT, L3, or full-site acceptance.

Allowed files, modules, or operations:
- `server/upload-server.mjs`
- `server/lib/ops-mineru-diagnostics.mjs` if relevant
- Focused tests under `server/tests/`
- Task/report files under `TaskAndReport/`
- Minimal docs/state updates only if needed for confirmed facts

Forbidden changes:
- No production deploy, fast-forward, restart, rebuild, Docker/Compose mutation, or production write operation.
- No DB row edit/delete, MinIO object edit/delete, Docker volume/image/log deletion, or sample mutation.
- No task retry/recovery/reparse/requeue.
- No secret/model/config/override/timeout changes.
- No weakening strict no-skeleton failure semantics.
- No broad refactor of upload/task worker logic.

Suggested direction:
1. Inspect the active-task diagnostic logic that computes `takeoverRequiredTasks`.
2. Define classification so only tasks requiring MinerU result takeover/recovery are included in `takeoverRequiredTasks`.
3. Treat terminal AI-stage failures with MinerU artifacts as non-active historical AI failures, either excluded from takeover-required output or exposed in a separately named diagnostic array.
4. Add focused tests for:
   - A real completed-but-not-ingested / takeover-needed parse task still appears as actionable.
   - A failed AI-stage task with MinerU completed/artifacts does not appear as takeover-required.
   - Active/current/queued parse work classification remains unchanged.
5. Keep output backward-compatible where feasible; if adding a new diagnostic field, document it in the report and avoid breaking existing consumers.

Required checks:
- `git status --short --branch`
- `git fetch origin`
- `git pull --ff-only origin main`
- Focused server test(s) covering active-task diagnostic classification
- Existing relevant MinerU diagnostic smoke test(s), if present
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`
- `git diff --check`

Required evidence:
- Exact code paths changed.
- Exact before/after classification behavior for the three historical task shapes.
- Commands run with exit codes.
- Tests added/updated and their pass output.
- Explicit confirmation that no production mutation or runtime operation was performed.

Completion report storage requirements:
- Write the completion report into `TaskAndReport/` using this naming rule: `YYYY-MM-DDTHH-MM-SS+0800_P1-Active-Task-Historical-AI-Failure-Classification-Fix_REPORT.md`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch, HEAD, current status, next actor, next action, and required output.

Acceptance criteria:
- Historical terminal AI failures are no longer labeled as `takeoverRequiredTasks`.
- Actionable MinerU takeover/recovery cases remain visible.
- Strict AI failure semantics are preserved.
- No production state is changed by this task.

