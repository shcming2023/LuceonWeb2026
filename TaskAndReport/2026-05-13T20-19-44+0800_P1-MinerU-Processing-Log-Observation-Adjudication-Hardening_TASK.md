# TASK-20260513-201944-P1-MinerU-Processing-Log-Observation-Adjudication-Hardening

Task:
P1 MinerU Processing Log Observation Adjudication Hardening

Assignee:
DevelopmentEngineer

Issued by:
Director

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-13T20-19-44+0800_P1-MinerU-Processing-Log-Observation-Adjudication-Hardening_TASK.md`

Expected completion report:
`TaskAndReport/2026-05-13T20-19-44+0800_P1-MinerU-Processing-Log-Observation-Adjudication-Hardening_REPORT.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- This task brief
- Task 100 corrected report and Director review:
  - `TaskAndReport/2026-05-13T19-50-02+0800_P0-Small-Stage-Queued-Validation-After-AI-JSON-Repair_REPORT.md`
  - `TaskAndReport/2026-05-13T20-19-44+0800_P0-Small-Stage-Queued-Validation-After-AI-JSON-Repair_DIRECTOR_REVIEW.md`

## Background

Task 100 accepted a small serial validation boundary: 3 authorized production uploads, one at a time, all ultimately reached `review-pending`.

However, all 3 samples exposed the same defect before success:

- Luceon temporarily marked the task `failed` because the MinerU log observer reported `log-observation-unreadable`;
- direct MinerU still reported the internal task as `processing`;
- the worker later self-corrected and completed the task;
- the task page and task history showed confusing failed/corrected noise.

Director code-reading found the likely hot path:

- `server/services/mineru/local-adapter.mjs`
- `server/services/mineru/v4-online-adapter.mjs` if it shares the same adjudication pattern
- `server/services/queue/task-worker.mjs`
- `server/lib/ops-mineru-diagnostics.mjs`
- `server/lib/ops-mineru-log-parser.mjs`
- frontend display helpers such as `src/app/utils/taskView.ts` only if needed for truthful display

The key wrong behavior is that an unreadable, unavailable, or stale log channel is being treated as a terminal MinerU failure even when the authoritative MinerU task API still says the task is `processing`.

## Objective

Prevent false terminal failures while MinerU API status is still `queued`, `pending`, `processing`, or `running`.

Log observation problems should be recorded as diagnostic warnings and operator-visible caveats, not as task-terminal `failed`, unless another authoritative failure, timeout, or explicit cancellation condition exists.

## Non-Goals

- Do not weaken strict no-skeleton AI behavior.
- Do not hide real MinerU API failures.
- Do not remove diagnostic visibility.
- Do not change PRD truth, role contracts, release judgments, or production readiness facts.
- Do not run production uploads, pressure tests, repairs, cleanup, destructive commands, restarts, rebuilds, model operations, or sample mutations.

## Suggested Direction

1. In the MinerU polling and takeover paths, distinguish:
   - authoritative MinerU states: queued/pending/processing/running/completed/failed;
   - observation channel health: active/stale/unreadable/unavailable.
2. If MinerU API reports still-processing, do not throw or transition to terminal failed solely because the log channel is unreadable or stale.
3. Preserve a clear diagnostic in metadata and task events, such as "log observation unavailable; MinerU API still processing".
4. Avoid repeated noisy `worker-failed` / `misjudged-failed-corrected` cycles for the same still-processing task.
5. Ensure active-task/admission diagnostics continue to count in-flight parse/AI work accurately while a MinerU task is still processing.
6. Keep true failure handling intact when MinerU API itself reports failed/error, the local timeout is exceeded, result fetch fails after completion, cancellation occurs, or a real transport/worker failure occurs.

## Allowed Files / Modules

You may modify only files required for this scoped fix, likely including:

- `server/services/mineru/local-adapter.mjs`
- `server/services/mineru/v4-online-adapter.mjs`
- `server/services/queue/task-worker.mjs`
- `server/lib/ops-mineru-diagnostics.mjs`
- `server/lib/ops-mineru-log-parser.mjs`
- `src/app/utils/taskView.ts` if display semantics need a narrow truth-preserving adjustment
- focused tests under `server/tests/`

If another file is necessary, explain why in the report.

## Forbidden Changes

- Do not change unrelated files.
- Do not broaden the upload pipeline or task model.
- Do not remove raw diagnostics or suppress evidence.
- Do not treat skeleton fallback as valid metadata.
- Do not change AI JSON repair behavior except as absolutely required by tests, which is not expected.
- Do not perform production deployment or production validation upload.
- Do not mutate DB/MinIO/Docker volumes/data, sample files, secrets, model settings, PRD truth, release docs, or role contracts.

## Required Checks

At minimum, run:

- `git diff --check`
- syntax checks for changed `.mjs` files with `node --check`
- a new or updated focused smoke proving that `log-observation-unreadable` while MinerU API is still `processing` does not terminally fail the task
- a focused smoke proving true MinerU API failure still fails explicitly
- relevant existing MinerU tests, including:
  - `node server/tests/mineru-log-progress-smoke.mjs`
  - `node server/tests/mineru-diagnostics-smoke.mjs`
  - `node server/tests/ops-mineru-active-task-classification-smoke.mjs`
  - `node server/tests/mineru-timeout-adjudication-smoke.mjs`
  - `node server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs`
- `node server/tests/dependency-health-smoke.mjs`
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`

If any check is skipped, state the exact reason.

## Completion Report Requirements

Write the report to:

`TaskAndReport/2026-05-13T20-19-44+0800_P1-MinerU-Processing-Log-Observation-Adjudication-Hardening_REPORT.md`

Update only Task 101 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- `Status=已回报待 Director 审查`
- `Next Actor=Director`
- include branch/HEAD, files changed, checks run, and remaining risk.

Do not push to GitHub unless this task's role contract and current branch policy require it. If you push, report branch and commit exactly. Director will decide merge/main synchronization.

## Acceptance Criteria

Task 101 can be accepted at code/test level if:

- still-processing MinerU API state plus unreadable/stale log observation no longer produces terminal failed state by itself;
- true MinerU failure/timeout/cancel/result-fetch failure semantics remain explicit;
- task events and UI semantics remain truthful about log-observation limitations;
- focused and relevant regression checks pass;
- no production readiness, L3, pressure PASS, release readiness, or go-live claim is made.
