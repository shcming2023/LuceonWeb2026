# Task Brief: P1 Pressure Semantics Production Read-Only Acceptance Review

- Task ID: `TASK-20260515-080916-P1-Pressure-Semantics-Production-Read-Only-Acceptance-Review`
- Created: 2026-05-15T08:09:16+0800
- Created by: Director
- Assigned role: `TestAcceptanceEngineer`
- Expected report: `TaskAndReport/2026-05-15T08-09-16+0800_P1-Pressure-Semantics-Production-Read-Only-Acceptance-Review_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-15T08-09-16+0800_P1-Pressure-Semantics-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`
- Based on deployed production HEAD: `91c1352 Authorize pressure semantics production deployment`

## Context

Task 157 changed the pressure-result and task-page semantics so that a mixed pressure run with many successful tasks and a small number of retryable AI residual failures is not flattened into a whole-run/systemic failure. It also tightened MinerU runtime progress truth so stale page/sidecar summaries do not overrule direct MinerU API state and advancing raw MinerU logs.

Task 159 deployed those code changes to production and passed DevelopmentEngineer read-only validation. This task asks TestAcceptanceEngineer to perform an independent read-only acceptance review of the deployed operator-facing semantics using existing production tasks only.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/test-acceptance-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. Task 157 task/report/Director review
12. Task 159 task/report/Director review
13. This task brief

If the task row, role file, Task 159 report, or Task 159 Director review is missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`.

## Workspaces And Runtime Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production UI: `http://localhost:8081/cms/`
- Upload proxy base: `http://localhost:8081/__proxy/upload`
- MinerU endpoint: `http://127.0.0.1:8083`

## Objective

Independently verify, read-only, that production now exposes understandable operator-facing semantics for:

- pressure-batch outcomes with mixed success and retryable AI residuals;
- AI failed tasks that should be visible as AI-stage residuals/manual-review candidates rather than whole-system failure;
- MinerU progress truth where the runtime is idle now and existing task details do not misrepresent stale observations as terminal system failure.

This is an acceptance review of deployed behavior on existing tasks only.

## Allowed Operations

Allowed:

- read-only Git status/HEAD checks in development and production;
- read-only Docker status checks;
- read-only HTTP checks for upload health, dependency-health, admission circuit, active-task diagnostics, direct MinerU `/health`, `/cms/`, and `/cms/tasks`;
- read-only browser inspection of `/cms/tasks` and representative existing task detail pages;
- read-only console/network observation counts;
- write the TestAcceptanceEngineer report and update row 160 locally.

Representative pages should include, if visible:

- at least one existing `failed/ai` task from the historical AI-failure list, such as `task-1778765415701`;
- at least one existing `review-pending` task from the same recent pressure-test window if a suitable one is visible;
- task list/filter/search/summary surfaces that show pressure semantics or stage labels.

## Forbidden Operations

Forbidden:

- PDF upload, pressure/batch/soak, fresh serial validation, or any new validation artifact creation;
- cleanup, cancel, repair, retry, reparse, or re-AI for existing tasks;
- destructive DB, MinIO, Docker volume, Docker data, or local filesystem operations;
- `docker compose down`, `docker compose down -v`, Docker volume/data cleanup, prune;
- service start/stop/restart/rebuild, including MinerU/Ollama/supervisor mutation;
- settings, secrets, config, model, or sample-library mutation;
- automatic retry/requeue;
- skeleton fallback weakening;
- PRD truth, role contract, project state, or handoff changes;
- declaring production readiness, release readiness, L3, pressure PASS, production上线, or go-live readiness.

## Required Evidence

Record:

- development and production `git status --short --branch`;
- production HEAD;
- production service health/read-only endpoint status;
- task-list counts and visible statuses/stages relevant to the pressure test;
- screenshots or DOM/text summaries sufficient to judge whether the page semantics are understandable;
- console/network counts for:
  - relevant `[db-sync]` warnings/errors;
  - `/settings`;
  - `/secrets`;
  - `Failed to fetch`;
  - HTTP 5xx;
  - non-stream request failures;
- whether the UI clearly distinguishes:
  - successful/review-pending tasks;
  - AI-stage failures/manual-retry residuals;
  - MinerU active/idle/current processing truth;
  - whole-run/systemic failure versus partial success with residuals.

## Stop / Block Conditions

Stop and write a blocked report if:

- production UI or upload health is unreachable;
- dependency-health is blocking in a way that prevents read-only acceptance;
- the task list/detail pages cannot be observed read-only;
- browser automation would require login, mutation, upload, data repair, or service changes;
- the observed semantics are misleading enough that TestAcceptanceEngineer cannot recommend acceptance.

## Required Report

Write:

`TaskAndReport/2026-05-15T08-09-16+0800_P1-Pressure-Semantics-Production-Read-Only-Acceptance-Review_REPORT.md`

The report must include:

- confirmation this work was based on this Director task brief;
- required reading completed;
- exact task pages observed;
- evidence table for each observed page/surface;
- console/network counts;
- pass/fail/recommendation boundary;
- skipped checks and exact reasons;
- risks/blockers/residual debt;
- explicit statement that no upload, pressure/batch/soak/fresh serial validation, cleanup/repair/reparse/re-AI, destructive mutation, service/config/secret/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, or readiness/go-live claim was made.

Update row 160 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or precise blocked status;
- Next Actor: `Director`;
- Report path populated.
