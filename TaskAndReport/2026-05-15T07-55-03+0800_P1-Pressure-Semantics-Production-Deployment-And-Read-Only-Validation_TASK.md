# Task Brief: P1 Pressure Semantics Production Deployment And Read-Only Validation

- Task ID: `TASK-20260515-075503-P1-Pressure-Semantics-Production-Deployment-And-Read-Only-Validation`
- Created: 2026-05-15T07:55:03+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-15T07-55-03+0800_P1-Pressure-Semantics-Production-Deployment-And-Read-Only-Validation_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-15T07-43-09+0800_P1-Pressure-Semantics-Production-Deployment-Decision_DECISION.md`
- Based on Director review: `TaskAndReport/2026-05-15T07-43-09+0800_P1-Pressure-Semantics-MinerU-Observability-And-AI-Failure-Contract_DIRECTOR_REVIEW.md`
- Accepted GitHub main commit to deploy: `2b59ef4 Accept pressure semantics and AI failure contract`

## Context

Task 157 was accepted at code/test level and integrated to GitHub main. It addresses the user-corrected pressure-test semantics:

- 24 PDFs were manually submitted by the user.
- Most tasks, including large files, succeeded or reached review state.
- A few AI recognition failures should be treated as manual-retry-eligible AI residuals, not as whole-run/systemic failure.
- MinerU active/success/failure judgment must respect direct MinerU API truth and raw MinerU logs. A task whose direct MinerU API remains `processing`, `error=null`, `completed_at=null`, and whose raw logs keep advancing must not be presented as terminal failure merely because a page/sidecar summary is stale.

The accepted code includes:

- AI timeout/transport failure classification and Material/ParseTask backfill.
- Task-page/list semantics for local timeout, remote MinerU `processing`, stale observation, and raw-log advancement.
- Pressure-result helper semantics for partial success with retryable AI residuals versus systemic failure.

Production still needs a scoped deployment and read-only validation before these semantics are available in the running system.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/development-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. This task brief
12. Task 157 report and Director review
13. Task 158 decision file

If the role file, this task row, Task 157 review, or Task 158 decision file is missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`. Do not improvise from partial context.

## Workspaces And Runtime Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production UI: `http://localhost:8081/cms/`
- Upload proxy base: `http://localhost:8081/__proxy/upload`
- MinerU endpoint: `http://127.0.0.1:8083`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`

## Objective

Deploy the accepted Task 157 code to production with the minimum necessary production operation, then perform non-destructive read-only validation that production is healthy and serving the accepted code path.

This task does not upload PDFs, restart pressure tests, repair historical failed tasks, retry AI jobs, or declare production readiness.

## Mandatory Preflight

Before any production deployment, run and record:

- development workspace `git status --short --branch`;
- production `git status --short --branch`;
- production `git log -1 --oneline`;
- production `docker compose ps`;
- frontend `/cms/` HTTP status;
- upload health: `http://localhost:8081/__proxy/upload/health`;
- dependency-health, preferably without submit probe first, and with MinerU submit probe only if active-task/admission evidence says it is safe;
- MinerU admission circuit: `http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit`;
- active task diagnostics: `http://localhost:8081/__proxy/upload/ops/mineru/active-task`;
- direct MinerU `/health`: `http://127.0.0.1:8083/health`.

Stop and write a blocked report if:

- active parse/AI/MinerU work exists and deployment would interrupt it;
- MinerU admission circuit is open;
- dependency-health is blocking;
- Docker core services are unhealthy;
- direct MinerU is unhealthy or not safely idle after any authorized submit-probe settlement;
- production workspace has unrelated local changes that prevent a clean fast-forward;
- deployment would require broad restart/rollback, destructive mutation, cleanup/repair/reparse/re-AI, or any operation outside this brief.

## Allowed Operations

Allowed:

- in the production deployment path, run the GitHub sync commands necessary to fast-forward production to current `origin/main` containing commit `2b59ef4` or a descendant containing it;
- rebuild/restart only the minimum services needed for Task 157 code to run:
  - `docker compose up -d --build upload-server cms-frontend`
- run non-destructive health/read-only browser checks after deployment;
- verify accepted code markers are present in production source:
  - `ai-failure-backfill`
  - `pressure-result-semantics`
  - `deriveMineruRuntimeProgressTruth`
  - `partial-success-with-retryable-ai-residuals`
  - `AI 识别失败，待人工判断是否手动重试`
- write the report and update the task row locally.

If `docker compose up -d --build upload-server cms-frontend` causes Compose to recreate dependent services automatically, record exactly what changed and verify service health afterward.

## Forbidden Operations

Forbidden:

- PDF upload or any fresh upload validation;
- pressure/batch/soak test or broader serial validation;
- cleanup, cancel, repair, retry, reparse, or re-AI for existing tasks;
- destructive DB, MinIO, Docker volume, Docker data, or local filesystem operations;
- `docker compose down`, `docker compose down -v`, Docker volume/data cleanup, prune;
- MinerU/Ollama/supervisor start/stop/restart/kill/attach/mutation;
- settings, secrets, config, model, or sample-library mutation;
- automatic retry/requeue;
- skeleton fallback weakening;
- PRD truth, role contract, project state, or handoff changes;
- declaring production readiness, release readiness, L3, pressure PASS, production上线, or go-live readiness.

## Post-Deploy Read-Only Validation

After deployment, record:

- production branch and HEAD before/after;
- `docker compose ps`;
- upload health OK;
- dependency-health non-blocking;
- MinerU admission circuit closed;
- active-task state and whether active parse/AI/MinerU work exists;
- direct MinerU `/health`;
- frontend `/cms/` and `/cms/tasks` HTTP 200;
- at least one read-only browser pass over `/cms/tasks` and one relevant task detail page if a suitable existing task exists, with console/network observation counts:
  - relevant `[db-sync]` warnings/errors;
  - `/settings`;
  - `/secrets`;
  - `Failed to fetch`;
  - HTTP 5xx;
  - non-stream request failures.

Do not upload or mutate runtime data during browser validation.

## Required Report

Write:

`TaskAndReport/2026-05-15T07-55-03+0800_P1-Pressure-Semantics-Production-Deployment-And-Read-Only-Validation_REPORT.md`

The report must include:

- confirmation this work was based on this Director task brief;
- required reading completed;
- development branch/HEAD and production before/after HEAD;
- production preflight evidence;
- deployment commands and exit codes;
- post-deploy read-only validation evidence;
- browser console/network observation counts;
- skipped checks and exact reasons;
- risks/blockers/residual debt;
- explicit statement that no upload, pressure/batch/soak, cleanup/repair/reparse/re-AI, destructive mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, settings/secrets/config/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, or readiness/go-live claim was made.

Update row 159 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or precise blocked status;
- Next Actor: `Director`;
- Report path populated.
