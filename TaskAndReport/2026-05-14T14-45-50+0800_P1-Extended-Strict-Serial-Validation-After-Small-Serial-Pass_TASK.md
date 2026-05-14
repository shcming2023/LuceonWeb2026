# Task Brief: P1 Extended Strict Serial Validation After Small Serial Pass

- Task ID: `TASK-20260514-144550-P1-Extended-Strict-Serial-Validation-After-Small-Serial-Pass`
- Created: 2026-05-14T14:45:50+0800
- Created by: Director
- Assigned role: TestAcceptanceEngineer
- Priority: P1
- Expected report: `TaskAndReport/2026-05-14T14-45-50+0800_P1-Extended-Strict-Serial-Validation-After-Small-Serial-Pass_REPORT.md`

## Context

Task 132 proved exactly one fresh upload after db-sync hardening.

Task 134 proved three additional strict-serial UI uploads after db-sync hardening:

- `task-1778740127704`
- `task-1778740183408`
- `task-1778740275811`

All three reached coherent terminal states:

- task `review-pending`
- material `reviewing`
- MinerU `completed`
- AI `analyzed`
- AI job `review-pending`
- parsed files counts `9/8/8`

Director review for Task 134 accepted the bounded small-serial validation as:

`ACCEPTED_SMALL_SERIAL_VALIDATION_PASS_WITH_PROGRESS_ATTRIBUTION_RESIDUAL`

The remaining known residual is MinerU terminal progress attribution for fast/short tasks: a task may complete successfully while the UI reports that no attributable business-progress log was captured.

User approved Option A from Task 135 at 2026-05-14T14:45:50+0800: run an extended strict-serial validation of up to 6 additional PDFs, one completed before the next, with no pressure test.

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
11. `TaskAndReport/2026-05-14T14-24-48+0800_P1-Post-Db-Sync-Hardening-Small-Serial-Validation_REPORT.md`
12. `TaskAndReport/2026-05-14T14-42-24+0800_P1-Post-Db-Sync-Hardening-Small-Serial-Validation_DIRECTOR_REVIEW.md`
13. `TaskAndReport/2026-05-14T14-42-24+0800_P1-Next-Validation-Scope-After-Small-Serial-Pass_DECISION.md`

## Scope

Run an extended strict-serial validation in the production-like runtime:

- upload at most 6 PDFs
- source directory: `/Users/concm/prod_workspace/Luceon2026/testpdf`
- upload through the UI only
- strictly one at a time
- wait for a coherent terminal state before starting the next upload
- stop immediately on unsafe preflight, systemic failure, db-sync/settings/secrets warning recurrence, dependency/admission/active-task inconsistency, or unexpected runtime mutation need

The sample directory is read-only. Do not copy, delete, rename, edit, move, truncate, or commit sample files.

Prefer PDFs not already used in Tasks 132 and 134 when enough unused files are available. If fewer unused PDFs are available, use the available files within the same maximum of 6 and record the exact selection rationale.

## Required Preflight

Before the first upload, and again before every subsequent upload:

1. `git status --short --branch` in the development workspace.
2. `git status --short --branch` and HEAD in `/Users/concm/prod_workspace/Luceon2026`.
3. Confirm production HEAD includes code commit `4eb2e3b` or a later deployed code commit that includes the db-sync hardening.
4. Check Docker services are healthy.
5. Check `/__proxy/upload/health`.
6. Check `/__proxy/upload/ops/dependency-health?ollamaChatProbe=true`.
7. Check `/__proxy/upload/ops/mineru/admission-circuit`.
8. Check `/__proxy/upload/ops/mineru/active-task`.
9. Check direct MinerU `/health`.

If parse/AI work is active, admission is open, dependency-health is blocking, Docker services are unhealthy, or MinerU is not healthy, stop and write a blocked report.

## Required Observations Per Upload

For each attempted upload, capture:

- sample path, size, SHA-256 hash, and whether it was previously used in Tasks 132/134
- upload status
- task ID, material ID, MinerU task ID, and AI job ID when available
- task state/stage sequence
- task list/detail progress semantics, especially whether operator-visible progress is meaningful during MinerU processing
- terminal progress attribution text, including any `MinerU 已完成，但本次未捕获可归因业务进度日志` residual
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
- request failures and whether they are only expected SSE aborts
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
- active-task shows unexpected queued/running/takeover/drift work after a terminal state
- MinerU, Ollama, supervisor, sidecar, Docker, DB, MinIO, settings, secrets, model, or sample mutation appears necessary
- a next upload would violate the strict "terminal before next" rule

If stopped, write a blocked report with the exact stopping point, evidence, and recommendation. Do not attempt repair unless a later Director task explicitly authorizes it.

## Acceptance Boundary

This task may recommend pass/fail with residual risks, but Director records final acceptance.

This task is extended strict-serial validation only. Even if it passes, it does not authorize pressure, batch concurrency, soak, L3, pressure PASS, release-readiness, or go-live.

## Forbidden

This task does not authorize:

- more than 6 uploads
- concurrent uploads
- pressure, batch-concurrent, soak, L3, pressure PASS, release-readiness, or go-live claims
- cleanup, repair, reparse, re-AI, failed-task repair, or manual status mutation
- destructive DB, MinIO, Docker volume, Docker down, data, sample, model, secret, settings, or config mutation
- MinerU, Ollama, supervisor, sidecar start/stop/restart/kill/ownership changes
- broad production deployment, rebuild, rollback, or source-code change

## Deliverable

Write `TaskAndReport/2026-05-14T14-45-50+0800_P1-Extended-Strict-Serial-Validation-After-Small-Serial-Pass_REPORT.md` and update the task ledger row to `已回报待 Director 审查` with `Next Actor=Director`.
