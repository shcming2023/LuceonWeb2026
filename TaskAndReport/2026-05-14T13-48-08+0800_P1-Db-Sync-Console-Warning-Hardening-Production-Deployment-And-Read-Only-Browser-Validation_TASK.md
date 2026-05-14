# Task Brief: P1 Db Sync Console Warning Hardening Production Deployment And Read-Only Browser Validation

- Task ID: `TASK-20260514-134808-P1-Db-Sync-Console-Warning-Hardening-Production-Deployment-And-Read-Only-Browser-Validation`
- Created: 2026-05-14T13:48:08+0800
- Created by: Director
- Assigned role: DevelopmentEngineer
- Priority: P1
- Expected report: `TaskAndReport/2026-05-14T13-48-08+0800_P1-Db-Sync-Console-Warning-Hardening-Production-Deployment-And-Read-Only-Browser-Validation_REPORT.md`

## Context

Task 129 accepted the db-sync console-warning hardening at code/test level. The accepted change prevents no-op background writes for sanitized settings and combined secrets after DB hydration while preserving visible warnings for real changed-payload save failures.

The remaining gap is production deployment plus read-only browser/runtime validation. Do not upload a PDF in this task.

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
11. `TaskAndReport/2026-05-14T13-17-23+0800_P1-Db-Sync-Console-Warning-Diagnostics-And-Hardening_REPORT.md`
12. `TaskAndReport/2026-05-14T13-48-08+0800_P1-Db-Sync-Console-Warning-Diagnostics-And-Hardening_DIRECTOR_REVIEW.md`

## Scope

Deploy the accepted Task 129 code to `/Users/concm/prod_workspace/Luceon2026` and perform non-mutating runtime/browser validation.

Allowed production actions:

- synchronize the production worktree to the accepted main commit
- run the minimum required frontend deployment command, preferably scoped to `cms-frontend`
- read health and status endpoints
- open existing pages in a browser or scripted browser session to observe console output

Validation must include:

- preflight: `git status --short --branch` in development and production workspaces
- preflight: admission circuit and active-task checks; if parse/AI work is active, stop and write a blocked report
- production HEAD before and after deployment
- exact deployment command and exit code
- frontend/app load check
- read-only checks for upload health, dependency-health, admission circuit, active-task, and direct MinerU health
- browser console observation while loading/navigating existing CMS pages, including at least one recent task/detail route if available
- explicit count of `[db-sync]`, `/settings/*`, `/secrets`, `Failed to fetch`, and HTTP 503 console or network events observed during the read-only browser session

## Acceptance Criteria

1. Production runs the accepted Task 129 code.
2. No PDF upload is performed.
3. No destructive data or service ownership operation is performed.
4. Browser/app boot and navigation do not emit the Task 128 no-op `[db-sync] PUT /settings/*` plus `/secrets` warning pattern.
5. If warnings still appear, report exact routes, console text, timing, and whether the warning is background/no-op or user-action-triggered.
6. Report whether a separate user-authorized controlled upload validation is recommended next.

## Required Checks

Record commands and exit codes:

- `git status --short --branch`
- production sync/deployment command(s)
- health/status endpoint checks used
- browser or scripted-browser validation command(s), if any

If a browser tool or scripted browser cannot be used, state the exact blocker and provide the strongest read-only fallback evidence available.

## Forbidden

This task does not authorize:

- PDF upload validation
- pressure, batch-concurrent, soak, L3, release-readiness, pressure PASS, or go-live claims
- cleanup, repair, reparse, re-AI, or failed-task mutation
- destructive DB, MinIO, Docker volume, Docker down, sample, model, secret, or config mutation
- MinerU, Ollama, supervisor, or sidecar start/stop/restart/kill/ownership changes
- broad production deploy beyond the minimum needed for accepted frontend code
- changing settings/secrets through the UI or API

## Deliverable

Write `TaskAndReport/2026-05-14T13-48-08+0800_P1-Db-Sync-Console-Warning-Hardening-Production-Deployment-And-Read-Only-Browser-Validation_REPORT.md` and update the task ledger row to `已回报待 Director 审查` with `Next Actor=Director`.

