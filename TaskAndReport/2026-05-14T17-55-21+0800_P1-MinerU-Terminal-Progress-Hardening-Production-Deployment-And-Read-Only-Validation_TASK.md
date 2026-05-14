# Task Brief: P1 MinerU Terminal Progress Hardening Production Deployment And Read-Only Validation

- Task ID: `TASK-20260514-175521-P1-MinerU-Terminal-Progress-Hardening-Production-Deployment-And-Read-Only-Validation`
- Created: 2026-05-14T17:55:21+0800
- Created by: Director
- Assigned role: DevelopmentEngineer
- Priority: P1
- Expected report: `TaskAndReport/2026-05-14T17-55-21+0800_P1-MinerU-Terminal-Progress-Hardening-Production-Deployment-And-Read-Only-Validation_REPORT.md`

## Context

Task 138 was accepted at code/test level and integrated to GitHub `main`.

The accepted code path hardens MinerU terminal progress display semantics so that successful terminal tasks with MinerU completed state and parsed artifact evidence prefer a completion-oriented primary line instead of making `未捕获可归因业务进度日志` the dominant operator-facing message.

Task 139 asked the user whether to authorize production deployment and read-only runtime/browser validation. Director recommended Option A. Two heartbeat checks found the decision still pending with no user reply:

- wait evidence 1: 2026-05-14T17:25:21+0800
- wait evidence 2: 2026-05-14T17:55:21+0800

Director applied the conservative autonomous rule and selected only Option A: minimum necessary production deployment plus non-destructive read-only validation. This task does not authorize uploads or any pressure/batch validation.

## Required Reading

Read before acting:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/development-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/codex/TEST_POLICY.md`
7. `docs/prd/Luceon2026-PRD-v0.4.md`
8. `TaskAndReport/README.md`
9. `TaskAndReport/TASK_TRACKING_LIST.md`
10. This task brief
11. `TaskAndReport/2026-05-14T16-23-11+0800_P1-MinerU-Terminal-Progress-Attribution-Hardening_REPORT.md`
12. `TaskAndReport/2026-05-14T16-56-48+0800_P1-MinerU-Terminal-Progress-Attribution-Hardening_DIRECTOR_REVIEW.md`
13. `TaskAndReport/2026-05-14T16-56-48+0800_P1-MinerU-Terminal-Progress-Hardening-Production-Deployment-Decision_DECISION.md`

If a required role document is unavailable in the current checkout, record that as a blocker detail in the report, then continue only if `AGENTS.md` and this task brief provide sufficient execution boundaries.

## Scope

Deploy the accepted Task 138 code path to `/Users/concm/prod_workspace/Luceon2026` and perform non-mutating runtime/browser validation.

Allowed production actions:

- inspect development and production git status
- synchronize the production worktree to GitHub `main` containing the accepted Task 138 code path
- run the minimum required frontend deployment command, preferably scoped to `cms-frontend`
- read health/status endpoints
- open existing CMS pages in a browser or scripted browser session
- inspect existing task/detail pages already present in production

Preflight requirements:

- run `git status --short --branch` in the development workspace
- run `git status --short --branch` in the production deployment path
- check active parse/AI work before any deployment command
- if parse/AI work is active or unclear, stop and write a blocked report
- record production HEAD before deployment

Validation requirements:

- record production HEAD after deployment
- confirm production contains the accepted Task 138 code path, either by commit ancestry or file content evidence
- run health/status checks for upload health, dependency-health, intake/admission circuit, active task state, and direct MinerU health
- load existing `/cms/tasks` and at least one existing task/detail route if available
- verify read-only UI/runtime semantics for existing successful terminal task pages where evidence exists
- explicitly record whether the old dominant terminal wording still appears as the primary line, and whether the attribution residual remains only as diagnostic/secondary metadata
- record browser console/network observations for relevant errors, including `[db-sync]`, `/settings`, `/secrets`, `Failed to fetch`, HTTP 5xx, and task-detail request failures

## Acceptance Criteria

1. Production runs GitHub `main` containing the accepted Task 138 code path.
2. No PDF upload is performed.
3. No destructive data, model, sample, secret, settings, config, or service ownership mutation is performed.
4. Existing task/detail pages load after deployment.
5. Successful terminal MinerU tasks with parsed artifact evidence do not use `MinerU 已完成，但本次未捕获可归因业务进度日志` as the dominant primary progress line after deployment.
6. If no suitable existing terminal task is available for read-only semantic proof, report the evidence gap exactly and recommend whether a separately authorized controlled upload validation is needed.
7. No readiness, L3, pressure PASS, release-readiness, production-readiness, or go-live claim is made.

## Required Checks

Record commands and exit codes:

- `git status --short --branch` in development workspace
- `git status --short --branch` and `git rev-parse --short HEAD` in production deployment path before and after deployment
- production sync/deployment command(s)
- health/status endpoint checks used
- browser or scripted-browser validation command(s), if any

If a browser tool or scripted browser cannot be used, state the exact blocker and provide the strongest read-only fallback evidence available.

## Forbidden

This task does not authorize:

- PDF upload validation
- second-stage validation, batch/intake, pressure, soak, L3, release-readiness, pressure PASS, production-readiness, or go-live claims
- cleanup, repair, reparse, re-AI, failed-task mutation, or manual status mutation
- destructive DB, MinIO, Docker volume, Docker down, data, sample, model, secret, settings, or config mutation
- MinerU, Ollama, supervisor, or sidecar start/stop/restart/kill/ownership changes beyond the minimum service rebuild/restart needed for accepted frontend deployment
- changing settings/secrets through UI or API
- broad production deploy beyond the minimum needed for accepted Task 138 frontend code
- unrelated code changes

## Deliverable

Write `TaskAndReport/2026-05-14T17-55-21+0800_P1-MinerU-Terminal-Progress-Hardening-Production-Deployment-And-Read-Only-Validation_REPORT.md` and update this task ledger row to `已回报待 Director 审查` with `Next Actor=Director`.

The report must include:

- confirmation that work was based on this Director task brief
- branch and HEAD for development and production workspaces
- deployment command(s) and exit codes
- files changed, if any
- runtime/browser validation summary
- exact health/status endpoint evidence
- console/network observations
- skipped checks with exact reasons
- risks, blockers, or residual debt
- whether separate user-authorized controlled upload validation is still needed
