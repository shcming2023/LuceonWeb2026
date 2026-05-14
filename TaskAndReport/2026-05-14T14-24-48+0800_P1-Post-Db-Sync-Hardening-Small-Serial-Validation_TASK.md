# Task Brief: P1 Post Db-Sync Hardening Small Serial Validation

- Task ID: `TASK-20260514-142448-P1-Post-Db-Sync-Hardening-Small-Serial-Validation`
- Created: 2026-05-14T14:24:48+0800
- Created by: Director
- Assigned role: TestAcceptanceEngineer
- Priority: P1
- Expected report: `TaskAndReport/2026-05-14T14-24-48+0800_P1-Post-Db-Sync-Hardening-Small-Serial-Validation_REPORT.md`

## Context

Task 132 accepted exactly one fresh-upload validation after db-sync hardening:

- `task-1778739091603` reached `review-pending`
- material `4487185779409524` reached `reviewing`
- MinerU completed
- AI analyzed with `qwen3.5:9b`
- fresh-upload console/network counts for `[db-sync]`, `/settings/`, `/secrets`, `Failed to fetch`, HTTP 503, and PUT settings/secrets were all `0`
- runtime returned idle and nonblocking

The remaining evidence gap is whether this remains stable across a few more strictly serial documents. User approved Option A from Task 133 at 2026-05-14T14:24:48+0800.

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
11. `TaskAndReport/2026-05-14T14-05-03+0800_P1-Post-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`
12. `TaskAndReport/2026-05-14T14-22-01+0800_P1-Post-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`
13. `TaskAndReport/2026-05-14T14-22-01+0800_P1-Next-Validation-Scope-After-Db-Sync-Fresh-Upload-Pass_DECISION.md`

## Scope

Run a small serial validation in the production-like runtime:

- Upload at most 3 PDFs.
- Source directory: `/Users/concm/prod_workspace/Luceon2026/testpdf`.
- Upload through the UI only.
- Strictly one at a time.
- Wait for a terminal state before starting the next upload.
- Stop immediately on unsafe preflight, systemic failure, repeated db-sync/settings/secrets warning recurrence, active-task/admission inconsistency, dependency blocking, or any unexpected runtime mutation need.

The sample directory is read-only. Do not copy, delete, rename, edit, move, truncate, or commit sample files.

## Required Preflight

Before the first upload, and again before each subsequent upload:

1. `git status --short --branch` in the development workspace.
2. `git status --short --branch` and HEAD in `/Users/concm/prod_workspace/Luceon2026`.
3. Confirm production HEAD is on or includes `4eb2e3b`.
4. Check Docker services are healthy.
5. Check `/__proxy/upload/health`.
6. Check `/__proxy/upload/ops/dependency-health?ollamaChatProbe=true`.
7. Check `/__proxy/upload/ops/mineru/admission-circuit`.
8. Check `/__proxy/upload/ops/mineru/active-task`.
9. Check direct MinerU `/health`.

If parse/AI work is active, admission is open, dependency-health is blocking, Docker services are unhealthy, or MinerU is not healthy, stop and write a blocked report.

## Required Observations Per Upload

For each attempted upload, capture:

- sample path, size, and SHA-256 hash
- upload status
- task ID, material ID, MinerU task ID, and AI job ID when available
- task state/stage sequence
- task list/detail progress semantics, especially `当前进展`
- browser console counts:
  - `[db-sync]`
  - `/settings/`
  - `/secrets`
  - `Failed to fetch`
  - HTTP 503
- network counts:
  - HTTP 503 responses
  - PUT `/settings/*`
  - PUT `/secrets`
- final task state and stage
- final material status, `mineruStatus`, `aiStatus`, parsed files/counts if available
- final AI job state/model if available
- post-terminal admission/active-task/dependency/MinerU health

## Stop Conditions

Stop immediately if any of these occur:

- any upload does not reach a coherent terminal state within the task's observation window
- Task 128-style db-sync warning pattern recurs
- HTTP 503 recurs on relevant operational paths
- dependency-health becomes blocking
- admission circuit opens
- active-task shows unexpected queued/running/takeover/drift work after terminal state
- MinerU or Ollama ownership/service mutation appears necessary
- a second upload would violate the "terminal before next" rule

## Acceptance Boundary

This task may recommend pass/fail with residual risks, but Director records final acceptance.

This task is a small serial validation only. Even if it passes, it does not by itself authorize pressure, batch, soak, L3, release-readiness, or go-live.

## Forbidden

This task does not authorize:

- more than 3 uploads
- concurrent uploads
- pressure, batch-concurrent, soak, L3, release-readiness, pressure PASS, or go-live claims
- cleanup, repair, reparse, re-AI, failed-task repair, or manual status mutation
- destructive DB, MinIO, Docker volume, Docker down, data, sample, model, secret, settings, or config mutation
- MinerU, Ollama, supervisor, or sidecar start/stop/restart/kill/ownership changes
- broad production deployment, rebuild, rollback, or source-code change

## Deliverable

Write `TaskAndReport/2026-05-14T14-24-48+0800_P1-Post-Db-Sync-Hardening-Small-Serial-Validation_REPORT.md` and update the task ledger row to `已回报待 Director 审查` with `Next Actor=Director`.

