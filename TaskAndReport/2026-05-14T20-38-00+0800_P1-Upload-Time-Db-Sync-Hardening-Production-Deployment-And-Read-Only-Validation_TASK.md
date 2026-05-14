# Task Brief: P1 Upload-Time Db-Sync Hardening Production Deployment And Read-Only Validation

- Task ID: `TASK-20260514-203800-P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-And-Read-Only-Validation`
- Created: 2026-05-14T20:38:00+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-14T20-38-00+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-And-Read-Only-Validation_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-14T19-54-24+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-Decision_DECISION.md`
- Based on Director review: `TaskAndReport/2026-05-14T19-54-24+0800_P1-Upload-Time-Db-Sync-Console-Noise-Diagnosis-And-Hardening_DIRECTOR_REVIEW.md`

## Context

Task 146 was accepted at code/test level and integrated to GitHub main:

- `src/store/appContext.tsx` now treats transient fetch cancellation during `pagehide` / `beforeunload` as debug-level lifecycle cancellation rather than real db-sync warning/failure count;
- real db-sync warning paths remain visible;
- focused smoke `server/tests/db-sync-page-lifecycle-noise-smoke.mjs` was added;
- Director replayed the patch in a clean sync clone and verified focused smoke, syntax check, `git diff --check`, and `tsc --noEmit`.

User approved Option A at `2026-05-14T20:38:00+0800`: scoped production deployment and validation. Director is splitting the approved route into two role-safe steps:

1. This DevelopmentEngineer task deploys the accepted frontend hardening and performs read-only post-deploy checks.
2. If accepted, Director may dispatch TestAcceptanceEngineer for exactly one controlled fresh upload validation under the same user approval.

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
12. `TaskAndReport/2026-05-14T19-39-27+0800_P1-Upload-Time-Db-Sync-Console-Noise-Diagnosis-And-Hardening_REPORT.md`
13. `TaskAndReport/2026-05-14T19-54-24+0800_P1-Upload-Time-Db-Sync-Console-Noise-Diagnosis-And-Hardening_DIRECTOR_REVIEW.md`

If `docs/codex/roles/development-engineer.md` or this task row is missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`. Do not improvise from partial role context.

## Workspaces And Runtime Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production UI: `http://localhost:8081/cms/`
- Upload proxy base: `http://localhost:8081/__proxy/upload`
- MinerU endpoint: `http://127.0.0.1:8083`

## Objective

Deploy the accepted Task 146 frontend db-sync lifecycle hardening to production with the minimum necessary frontend deployment operation, then perform non-destructive read-only validation that production is healthy and serving the accepted code path.

This task does not perform the fresh upload validation. That will be a separate TestAcceptanceEngineer task after Director review if this deployment evidence is accepted.

## Mandatory Preflight

Before any production deployment, run and record:

- development workspace `git status --short --branch`;
- production `git status --short --branch`;
- production `git log -1 --oneline`;
- production `docker compose ps`;
- frontend `/cms/` HTTP status;
- upload health;
- dependency-health with Ollama chat probe, and MinerU submit probe only if safe;
- MinerU admission circuit;
- active task through `/__proxy/upload/ops/mineru/active-task`;
- direct MinerU `/health`.

Stop and write a blocked report if:

- active parse/AI work exists;
- MinerU admission circuit is open;
- dependency-health is blocking;
- Docker core services are unhealthy;
- direct MinerU is unhealthy or not idle after safe probe settlement;
- deployment would require broad restart/rollback, destructive mutation, cleanup/repair/reparse/re-AI, or any operation outside this brief.

## Allowed Operations

Allowed:

- in production deployment path, fast-forward to current GitHub `origin/main` containing accepted Task 146;
- rebuild/restart only the minimum frontend service needed to serve the accepted `src/store/appContext.tsx` change, expected command shape: `docker compose up -d --build cms-frontend`;
- run non-destructive health/read-only browser checks after deployment;
- verify the accepted code marker is present in production source:
  - `dbSyncPageLifecycleEnding`
  - `cancelled during page lifecycle change`
  - `db-sync-page-lifecycle-noise-smoke`
- write the report and update the task row locally.

Forbidden:

- PDF upload or any fresh upload validation;
- second upload, batch/intake/pressure/soak/broader serial validation;
- cleanup/repair/reparse/re-AI;
- destructive DB/MinIO/Docker volume/data mutation;
- `docker compose down`, `docker compose down -v`, Docker volume/data cleanup;
- MinerU/Ollama/supervisor start/stop/restart/kill/attach/mutation;
- settings/secrets/config/model/sample mutation;
- broad warning suppression;
- PRD truth, role contract, project state, or handoff changes;
- declaring production readiness, release-readiness, L3, pressure PASS, or go-live readiness.

## Post-Deploy Read-Only Validation

After deployment, record:

- production HEAD and branch status;
- `docker compose ps`;
- upload health;
- dependency-health, non-blocking;
- MinerU admission circuit closed;
- active-task idle;
- direct MinerU health idle;
- frontend `/cms/` HTTP 200;
- at least one browser read-only pass over `/cms/tasks` with console/network observation:
  - record relevant `[db-sync]`, `/settings`, `/secrets`, `Failed to fetch`, HTTP 5xx, and non-stream request-failed counts;
  - do not upload.

## GitHub / Repository Rules

Do not run `git fetch`, `git pull`, or `git push` in the development workspace unless Director separately instructs you.

Production workspace may run the GitHub sync commands necessary to fast-forward production to the accepted main commit. Do not overwrite unrelated production local modifications; report them and proceed only if fast-forward deployment can be done without reverting them.

Write the report and update `TaskAndReport/TASK_TRACKING_LIST.md` locally. Director will handle GitHub synchronization after review if needed.

## Required Report

Write:

`TaskAndReport/2026-05-14T20-38-00+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-And-Read-Only-Validation_REPORT.md`

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
- explicit statement that no upload, pressure/batch/soak, cleanup/repair/reparse/re-AI, destructive mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, settings/secrets/config/model/sample mutation, broad warning suppression, or readiness/go-live claim was made.

Update row 148 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or precise blocked status;
- Next Actor: `Director`;
- Report path populated.
