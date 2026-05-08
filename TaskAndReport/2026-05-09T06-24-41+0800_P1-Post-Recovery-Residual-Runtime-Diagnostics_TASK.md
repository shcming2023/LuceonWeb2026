# Lucia Task Brief: P1 Post-Recovery Residual Runtime Diagnostics

Task:
P1 Post-Recovery Residual Runtime Diagnostics

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
TaskAndReport/2026-05-09T06-24-41+0800_P1-Post-Recovery-Residual-Runtime-Diagnostics_TASK.md

Required reading before execution:
- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/lucode.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-09T06-24-41+0800_P0-Sample3-Controlled-Production-Recovery_LUCIA_REVIEW.md

Background:
Task 48 recovered sample 3 to human review state. Lucia accepted the recovery, but two residual runtime diagnostics remain: dependency-health still observed an Ollama smoke timeout at about 15s with `blocking=false`, and `/__proxy/upload/ops/mineru/active-task` still reports three unrelated historical `takeoverRequiredTasks`.

Current known facts:
- Target sample 3 task `task-1778249434820` is recovered to `review-pending`.
- Target material `mat-1778249419780` is `reviewing`.
- Target AI job `ai-job-1778278172782-303b` is `review-pending`.
- Dependency-health after recovery can report Ollama smoke timeout while parse dependencies are non-blocking.
- Three unrelated historical takeover-required tasks remain outside Task 48 scope.

Objective:
Produce a read-only residual runtime diagnostic report that identifies the three unrelated takeover-required tasks, summarizes their current states and risk, and characterizes the Ollama dependency-health timeout behavior after recovery.

Non-goals:
- Do not repair, mutate, delete, retry, requeue, restart, rebuild, or recover any production task.
- Do not change DB, MinIO, Docker, model, timeout, secret, override, prompt, provider, or source code.
- Do not create uploads or validation artifacts.
- Do not declare production release readiness, UAT, L3, or full-site acceptance.

Allowed files, modules, or operations:
- Read-only Git sync and status checks.
- Read-only production API checks:
  - CMS/upload health.
  - DB health.
  - dependency-health.
  - MinerU active-task endpoint.
  - task/material/AI-job reads for the three unrelated takeover-required tasks if IDs are exposed.
- Read-only local log inspection if needed and non-destructive.
- Write only the Lucode completion report and update `TaskAndReport/TASK_TRACKING_LIST.md`.

Forbidden changes:
- No production service restart, rebuild, recreate, rollback, fast-forward, or Docker mutation.
- No DB row edit/delete, MinIO object edit/delete, Docker volume/image/log deletion, or sample mutation.
- No manual recovery of the three unrelated tasks.
- No second MinerU submission, no new upload, no reparse, no AI job retry.
- No secret/model/config/override/timeout changes.
- No source-code implementation unless Lucia issues a separate task.

Suggested direction:
1. Confirm development workspace and production workspace git state.
2. Capture read-only dependency-health at least twice, separated enough to distinguish cold vs immediate repeat behavior. Do not warm up or mutate services.
3. Capture `/__proxy/upload/ops/mineru/active-task` and enumerate the three unrelated `takeoverRequiredTasks`.
4. For each unrelated task, if IDs are available, read task/material state and classify whether it appears stale historical, already terminal, or an active risk.
5. Report whether a future repair task is needed, and if yes, propose a scoped non-destructive planning task or Director decision boundary.

Required checks:
- `git status --short --branch`
- `git fetch origin`
- Read-only CMS/upload health.
- Read-only DB health.
- Read-only dependency-health evidence.
- Read-only MinerU active-task evidence.
- `git diff --check` if repository files are changed.

Required evidence:
- Exact commands and exit codes.
- Raw or summarized JSON fields for dependency-health and active-task.
- IDs and current states of unrelated takeover-required tasks, if exposed.
- Explicit confirmation that no production mutation, restart, rebuild, cleanup, upload, reparse, or retry was performed.

Completion report storage requirements:
- Write the completion report into `TaskAndReport/` using this naming rule: `YYYY-MM-DDTHH-MM-SS+0800_P1-Post-Recovery-Residual-Runtime-Diagnostics_REPORT.md`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch, HEAD, current status, next actor, next action, and required output.

Acceptance criteria:
- Lucia can decide from the report whether the residuals are informational debt, require a future scoped repair task, or require a Director decision.
- No production state is changed by this diagnostic task.

