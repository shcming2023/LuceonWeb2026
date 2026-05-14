# Task Brief: P1 MinerU Terminal Progress Attribution Hardening

- Task ID: `TASK-20260514-162311-P1-MinerU-Terminal-Progress-Attribution-Hardening`
- Created: 2026-05-14T16:23:11+0800
- Created by: Director
- Assigned role: DevelopmentEngineer
- Priority: P1
- Expected report: `TaskAndReport/2026-05-14T16-23-11+0800_P1-MinerU-Terminal-Progress-Attribution-Hardening_REPORT.md`

## Context

Fresh-upload validation after db-sync hardening has passed under strict serial boundaries:

- Task 132: exactly one fresh upload passed
- Task 134: three additional strict-serial uploads passed
- Task 136: six additional strict-serial uploads passed, including a larger sample with `82` parsed files

Across Task 136:

- all six tasks reached `review-pending`
- all six materials reached `reviewing`
- all six MinerU parses reached `completed`
- all six AI jobs reached `review-pending`
- db-sync/settings/secrets/Failed-to-fetch/HTTP-503/PUT-settings/PUT-secrets recurrence was `0`
- runtime returned idle after every upload

However, MinerU terminal progress attribution remains imperfect. Successful terminal rows can still show:

`MinerU 已完成，但本次未捕获可归因业务进度日志`

This wording is acceptable as a secondary diagnostic, but it should not dominate successful terminal UI semantics when the task has coherent terminal state and parsed artifacts. Operator trust matters before moving to batch/intake or pressure-style validation.

Task 137 asked the user to choose the next step. After two unanswered heartbeat checks, Director applied the conservative auto-advance rule and selected Option A: code/test-level hardening of MinerU terminal progress-attribution semantics.

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
11. `TaskAndReport/2026-05-14T14-45-50+0800_P1-Extended-Strict-Serial-Validation-After-Small-Serial-Pass_REPORT.md`
12. `TaskAndReport/2026-05-14T15-22-11+0800_P1-Extended-Strict-Serial-Validation-After-Small-Serial-Pass_DIRECTOR_REVIEW.md`
13. `TaskAndReport/2026-05-14T15-22-11+0800_P1-Next-Step-After-Extended-Serial-Pass_DECISION.md`

## Scope

Implement a focused code/test hardening so that successful terminal MinerU states present trustworthy operator-facing progress semantics.

Expected technical direction:

- Preserve or derive the last valid task-attributed MinerU business-progress snapshot for terminal successful rows when available.
- When a task is terminal-successful (`review-pending` or otherwise clearly successful), MinerU is `completed`, and parsed artifacts/files exist, prefer a primary terminal message such as MinerU completed with parsed artifact count or last known phase, instead of making `未捕获可归因业务进度日志` the dominant row/detail message.
- Keep the no-attributed-log condition visible as secondary diagnostic metadata/warning when true.
- Do not hide real warning/error states. If MinerU failed, active parsing is stuck, dependency health is blocking, or artifacts are absent when required, keep explicit failure/diagnostic semantics.
- Do not reintroduce heuristic chapter preprocessing, skeleton fallback, silent parse/AI degradation, or any hidden success path.

Likely code areas to inspect and adjust, but keep the actual patch narrow:

- `server/lib/ops-mineru-log-parser.mjs`
- `server/services/queue/task-worker.mjs`
- `src/app/pages/TaskDetailPage.tsx`
- `src/app/pages/TaskManagementPage.tsx`
- `src/app/utils/taskView.ts`
- focused tests under `server/tests/` or the existing test structure

If the actual implementation surface is smaller, change only the smaller surface.

## Acceptance Criteria

Code/test-level acceptance requires:

- Successful terminal tasks with MinerU completed and parsed artifacts/counts no longer use `MinerU 已完成，但本次未捕获可归因业务进度日志` as the dominant primary progress message.
- The attribution residual remains inspectable as diagnostic data when applicable.
- In-flight progress semantics are not regressed.
- Failure, stale, unattributed, dependency-blocking, and no-artifact states remain explicit and are not silently converted to success.
- Existing db-sync/settings/secrets behavior is not changed.
- Existing queue/admission/Ollama/MinIO behavior is not changed.
- Focused smoke/regression coverage is added or updated for the terminal-success case and at least one diagnostic/failure-like case.

## Required Checks

Run the narrowest relevant checks plus any affected existing checks. At minimum:

- `git diff --check`
- `node --check` on changed `.mjs` files
- focused smoke/regression tests touching MinerU progress semantics
- `npx pnpm@10.4.1 exec tsc --noEmit` if frontend TypeScript files are changed

If a check is unavailable or skipped, record the exact reason in the report.

## Forbidden

This task does not authorize:

- production deployment
- uploads or validation runs
- batch/intake, pressure, soak, L3, pressure PASS, release-readiness, or go-live claims
- cleanup, repair, reparse, re-AI, failed-task mutation, or manual status mutation
- destructive DB, MinIO, Docker volume, Docker down, data, sample, model, secret, settings, or config mutation
- MinerU, Ollama, supervisor, or sidecar start/stop/restart/kill/ownership changes
- broad architecture rewrite
- PRD truth, role-contract, release-state, or readiness-state changes

## Deliverable

Implement the scoped patch on a DevelopmentEngineer branch, write `TaskAndReport/2026-05-14T16-23-11+0800_P1-MinerU-Terminal-Progress-Attribution-Hardening_REPORT.md`, and update the task ledger row to `已回报待 Director 审查` with `Next Actor=Director`.

The report must include:

- files changed
- implementation summary
- exact commands and exit codes
- focused evidence for terminal-success semantics
- skipped checks with exact reasons
- residual risks
- whether production deployment/runtime validation is still required
