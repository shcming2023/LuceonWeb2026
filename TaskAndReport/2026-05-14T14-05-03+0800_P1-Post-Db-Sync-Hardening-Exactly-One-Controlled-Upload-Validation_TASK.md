# Task Brief: P1 Post Db-Sync Hardening Exactly One Controlled Upload Validation

- Task ID: `TASK-20260514-140503-P1-Post-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation`
- Created: 2026-05-14T14:05:03+0800
- Created by: Director
- Assigned role: TestAcceptanceEngineer
- Priority: P1
- Expected report: `TaskAndReport/2026-05-14T14-05-03+0800_P1-Post-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`

## Context

Task 130 accepted scoped production deployment and read-only browser validation for the Task 129 db-sync console-warning hardening:

- Production is on `4eb2e3b Accept db-sync warning hardening`.
- Read-only browser navigation did not emit the Task 128 no-op `[db-sync] PUT /settings/*` plus `/secrets` warning pattern.
- Fresh upload lifecycle behavior remains unproven because Task 130 did not authorize a PDF upload.

User approved Option A from Task 131 at 2026-05-14T14:05:03+0800.

## Required Reading

Read before acting:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/test-acceptance-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/codex/TEST_POLICY.md`
7. `docs/prd/Luceon2026-PRD-v0.4.md`
8. `TaskAndReport/README.md`
9. `TaskAndReport/TASK_TRACKING_LIST.md`
10. This task brief
11. `TaskAndReport/2026-05-14T13-48-08+0800_P1-Db-Sync-Console-Warning-Hardening-Production-Deployment-And-Read-Only-Browser-Validation_REPORT.md`
12. `TaskAndReport/2026-05-14T14-02-00+0800_P1-Db-Sync-Console-Warning-Hardening-Production-Deployment-And-Read-Only-Browser-Validation_DIRECTOR_REVIEW.md`
13. `TaskAndReport/2026-05-14T14-02-00+0800_P1-Post-Db-Sync-Hardening-One-Upload-Validation-Authorization_DECISION.md`

## Scope

Run exactly one controlled upload validation in production-like runtime.

Allowed:

- Select exactly one small/medium PDF from `/Users/concm/prod_workspace/Luceon2026/testpdf`.
- Upload it through the UI.
- Observe task list/detail progress, browser console/network events, and terminal task/material/MinerU/AI state.
- Stop after the first terminal state or first systemic failure.

The sample directory is read-only. Do not copy, delete, rename, edit, or move sample files.

## Required Preflight

Before upload:

1. `git status --short --branch` in the development workspace.
2. `git status --short --branch` and HEAD in `/Users/concm/prod_workspace/Luceon2026`.
3. Confirm production HEAD is on or includes `4eb2e3b`.
4. Check Docker services are healthy.
5. Check `/__proxy/upload/health`.
6. Check `/__proxy/upload/ops/dependency-health?ollamaChatProbe=true`.
7. Check `/__proxy/upload/ops/mineru/admission-circuit`.
8. Check `/__proxy/upload/ops/mineru/active-task`.
9. Check direct MinerU `/health`.

If parse/AI work is active, admission is open, dependency-health is blocking, Docker services are unhealthy, or MinerU is not healthy, do not upload. Write a blocked report.

## Required Observations

During and after the upload, capture:

- selected sample path, size, and SHA-256 hash
- created task ID, material ID, MinerU task ID, and AI job ID when available
- task list/detail progress semantics, especially `当前进展`
- browser console counts for:
  - `[db-sync]`
  - `/settings/`
  - `/secrets`
  - `Failed to fetch`
  - HTTP 503
- network counts for:
  - HTTP 503 responses
  - PUT `/settings/*`
  - PUT `/secrets`
- final task state and stage
- final material status, `mineruStatus`, `aiStatus`, parsed files/counts if available
- final AI job state/model if available
- post-terminal admission/active-task/dependency/MinerU health

## Acceptance Boundary

This task may recommend whether the one-upload validation passed or failed, but Director will make the final acceptance decision.

A pass for this task requires:

- exactly one upload
- no concurrent/batch upload
- no recurrence of the Task 128 no-op db-sync settings/secrets warning pattern during the upload lifecycle
- coherent terminal state, or a clear blocked/failure diagnosis if the upload fails
- no unapproved mutation beyond the single upload's ordinary artifacts

## Forbidden

This task does not authorize:

- second upload
- pressure, batch-concurrent, soak, L3, release-readiness, pressure PASS, or go-live claims
- cleanup, repair, reparse, re-AI, failed-task repair, or manual status mutation
- destructive DB, MinIO, Docker volume, Docker down, data, sample, model, secret, settings, or config mutation
- MinerU, Ollama, supervisor, or sidecar start/stop/restart/kill/ownership changes
- broad production deployment, rebuild, rollback, or source-code change

## Deliverable

Write `TaskAndReport/2026-05-14T14-05-03+0800_P1-Post-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md` and update the task ledger row to `已回报待 Director 审查` with `Next Actor=Director`.

