# Task Brief: P1 MinerU Terminal Diagnostic Cleanup Production Deployment And Read-Only Validation

- Task ID: `TASK-20260514-190858-P1-MinerU-Terminal-Diagnostic-Cleanup-Production-Deployment-And-Read-Only-Validation`
- Created: 2026-05-14T19:08:58+0800
- Created by: Director
- Assigned role: DevelopmentEngineer
- Priority: P1
- Expected report: `TaskAndReport/2026-05-14T19-08-58+0800_P1-MinerU-Terminal-Diagnostic-Cleanup-Production-Deployment-And-Read-Only-Validation_REPORT.md`

## Context

Task 141 was accepted at code/test level and integrated to GitHub `main`.

The accepted cleanup prevents the old no-attributed-log diagnostic sentence from being appended as `最后可见进度` inside successful terminal primary progress lines:

`MinerU 已完成，但本次未捕获可归因业务进度日志`

The cleanup preserves real backend/pipeline/page progress as valid `最后可见进度`, and keeps the no-attributed-log condition inspectable as diagnostic metadata.

Task 142 asked the user whether to authorize production deployment and read-only validation. User approved Option A at 2026-05-14T19:08:58+0800.

This task authorizes only the minimum necessary production deployment plus non-destructive read-only validation. It does not authorize uploads or pressure/batch validation.

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
11. `TaskAndReport/2026-05-14T18-30-02+0800_P1-MinerU-Terminal-Last-Progress-Diagnostic-Cleanup_REPORT.md`
12. `TaskAndReport/2026-05-14T18-59-27+0800_P1-MinerU-Terminal-Last-Progress-Diagnostic-Cleanup_DIRECTOR_REVIEW.md`
13. `TaskAndReport/2026-05-14T18-59-27+0800_P1-MinerU-Terminal-Diagnostic-Cleanup-Production-Deployment-Decision_DECISION.md`

If a required role document is unavailable in the current checkout, record that as a blocker detail in the report, then continue only if `AGENTS.md` and this task brief provide sufficient execution boundaries.

## Scope

Deploy the accepted Task 141 cleanup code path to `/Users/concm/prod_workspace/Luceon2026` and perform non-mutating runtime/browser validation.

Allowed production actions:

- inspect development and production git status
- synchronize the production worktree to GitHub `main` containing the accepted Task 141 cleanup
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
- confirm production contains the accepted Task 141 cleanup code path, either by commit ancestry or file content evidence
- run health/status checks for upload health, dependency-health, intake/admission circuit, active task state, and direct MinerU health
- load existing `/cms/tasks` and at least one existing task/detail route if available
- verify read-only UI/runtime semantics for existing successful terminal task pages where evidence exists
- explicitly record whether the old no-attributed-log diagnostic sentence still appears inside successful terminal primary progress lines after deployment
- verify real backend/pipeline/page progress remains visible when present
- record browser console/network observations for relevant errors, including `[db-sync]`, `/settings`, `/secrets`, `Failed to fetch`, HTTP 5xx, and task-detail request failures

## Acceptance Criteria

1. Production runs GitHub `main` containing the accepted Task 141 cleanup.
2. No PDF upload is performed.
3. No destructive data, model, sample, secret, settings, config, or service ownership mutation is performed.
4. Existing task/detail pages load after deployment.
5. Successful terminal MinerU tasks with parsed artifact evidence do not append `MinerU 已完成，但本次未捕获可归因业务进度日志` as `最后可见进度` in the primary progress line.
6. Existing tasks with real backend/pipeline/page progress still show that progress as `最后可见进度`.
7. If no suitable existing terminal task is available for read-only semantic proof, report the evidence gap exactly and recommend whether a separately authorized controlled upload validation is needed.
8. No readiness, L3, pressure PASS, release-readiness, production-readiness, or go-live claim is made.

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
- broad production deploy beyond the minimum needed for accepted Task 141 frontend code
- unrelated code changes

## Deliverable

Write `TaskAndReport/2026-05-14T19-08-58+0800_P1-MinerU-Terminal-Diagnostic-Cleanup-Production-Deployment-And-Read-Only-Validation_REPORT.md` and update this task ledger row to `已回报待 Director 审查` with `Next Actor=Director`.

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
