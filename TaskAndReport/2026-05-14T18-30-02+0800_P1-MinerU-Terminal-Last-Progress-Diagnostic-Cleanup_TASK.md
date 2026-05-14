# Task Brief: P1 MinerU Terminal Last Progress Diagnostic Cleanup

- Task ID: `TASK-20260514-183002-P1-MinerU-Terminal-Last-Progress-Diagnostic-Cleanup`
- Created: 2026-05-14T18:30:02+0800
- Created by: Director
- Assigned role: DevelopmentEngineer
- Priority: P1
- Expected report: `TaskAndReport/2026-05-14T18-30-02+0800_P1-MinerU-Terminal-Last-Progress-Diagnostic-Cleanup_REPORT.md`

## Context

Task 140 successfully deployed and read-only validated the Task 138 terminal progress hardening in production.

The deployed UI now starts successful terminal MinerU rows with completion-oriented wording such as:

- `MinerU 已完成，解析产物 82 个`
- `MinerU 已完成，解析产物 9 个`

Residual issue: historical no-attributed-log tasks can still show the old diagnostic sentence appended as `最后可见进度` in the same primary line:

`MinerU 已完成，解析产物 9 个；最后可见进度：MinerU 已完成，但本次未捕获可归因业务进度日志`

This is not a runtime failure, but it weakens the operator-facing progress semantics that this P1 thread is meant to improve.

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
11. `TaskAndReport/2026-05-14T17-55-21+0800_P1-MinerU-Terminal-Progress-Hardening-Production-Deployment-And-Read-Only-Validation_REPORT.md`
12. `TaskAndReport/2026-05-14T18-30-02+0800_P1-MinerU-Terminal-Progress-Hardening-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`

If a required role document is unavailable in the current checkout, record that as a blocker detail in the report, then continue only if `AGENTS.md` and this task brief provide sufficient execution boundaries.

## Scope

Make a narrow code/test change so successful terminal primary progress lines do not append the old no-attributed-log diagnostic sentence as `最后可见进度`.

Expected technical direction:

- Treat `MinerU 已完成，但本次未捕获可归因业务进度日志` as diagnostic metadata, not as a valid last business-progress phrase to append to terminal success primary lines.
- For successful terminal tasks with MinerU completed state and parsed artifact evidence, prefer:
  - `MinerU 已完成，解析产物 N 个`
  - or `MinerU 已完成，解析产物 N 个；最后可见进度：<real business progress>`
- Preserve real last business progress such as backend/pipeline phase/page information.
- Preserve failure, no-artifact, dependency-blocking, stale, in-flight, and diagnostic semantics. Do not convert missing artifacts or failures into success.
- Keep the no-attributed-log condition inspectable as secondary diagnostic metadata/warning where the current data model supports it.

Likely files:

- `src/app/utils/taskView.ts`
- `server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs`
- another focused existing smoke only if required by the actual surface

Keep the patch as small as possible.

## Acceptance Criteria

Code/test-level acceptance requires:

1. Successful terminal tasks with parsed artifacts do not include `MinerU 已完成，但本次未捕获可归因业务进度日志` inside the primary progress line.
2. Successful terminal tasks with real last business progress still include that progress after `最后可见进度`.
3. The diagnostic no-attributed-log condition remains available as diagnostic data when applicable.
4. Failure/no-artifact/in-flight semantics are not regressed.
5. No queue/admission/Ollama/MinIO/db-sync behavior is changed.
6. Focused smoke/regression coverage proves both the filtered diagnostic case and the real-last-progress preservation case.

## Required Checks

Run and record exit codes:

- `git diff --check`
- `node --check` on changed `.mjs` files
- focused MinerU terminal diagnostic/progress smoke tests
- `npx pnpm@10.4.1 exec tsc --noEmit` if frontend TypeScript files are changed

If a check is unavailable or skipped, record the exact reason.

## Forbidden

This task does not authorize:

- production deployment
- uploads or runtime validation
- batch/intake, pressure, soak, L3, pressure PASS, release-readiness, production-readiness, or go-live claims
- cleanup, repair, reparse, re-AI, failed-task mutation, or manual status mutation
- destructive DB, MinIO, Docker volume, Docker down, data, sample, model, secret, settings, or config mutation
- MinerU, Ollama, supervisor, or sidecar start/stop/restart/kill/ownership changes
- broad UI rewrite or unrelated page redesign
- PRD truth, role-contract, release-state, or readiness-state changes

## Deliverable

Implement the scoped patch, write `TaskAndReport/2026-05-14T18-30-02+0800_P1-MinerU-Terminal-Last-Progress-Diagnostic-Cleanup_REPORT.md`, and update this task ledger row to `已回报待 Director 审查` with `Next Actor=Director`.

The report must include:

- confirmation that work was based on this Director task brief
- branch and HEAD
- files changed
- implementation summary
- exact commands and exit codes
- focused test evidence
- skipped checks with exact reasons
- residual risks
- whether production deployment/read-only validation is still required afterward
