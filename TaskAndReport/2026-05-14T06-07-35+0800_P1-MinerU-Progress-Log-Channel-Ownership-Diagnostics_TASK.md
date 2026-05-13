# TASK-20260514-060735-P1-MinerU-Progress-Log-Channel-Ownership-Diagnostics

Task:
P1 MinerU Progress Log Channel Ownership Diagnostics

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
`TaskAndReport/2026-05-14T06-07-35+0800_P1-MinerU-Progress-Log-Channel-Ownership-Diagnostics_TASK.md`

Expected completion report:
`TaskAndReport/2026-05-14T06-07-35+0800_P1-MinerU-Progress-Log-Channel-Ownership-Diagnostics_REPORT.md`

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
- Task 106 report and Director review:
  - `TaskAndReport/2026-05-14T05-42-35+0800_P1-MinerU-Progress-Observability-Ownership-Review_REPORT.md`
  - `TaskAndReport/2026-05-14T06-07-35+0800_P1-MinerU-Progress-Observability-Ownership-Review_DIRECTOR_REVIEW.md`

## Background

Task 104 proved that the false-failed MinerU log-observation defect did not recur for one controlled upload. However, the same task still showed diagnostic-only progress: `MinerU 已完成，但本次未捕获可归因业务进度日志`.

Task 106 confirmed the architecture gap: lifecycle truth is healthy via MinerU API and Luceon task state, but progress-rich observability depends on a MinerU log channel that is not currently live/attributable. Production read-only evidence showed expected log files were present but empty, global observation was null, and the `mineru-log-observer` sidecar was not running.

The user explicitly chose to govern MinerU progress observability before broader validation or pressure testing.

## Objective

Implement and/or document a scoped ownership diagnostics layer so Luceon can distinguish these cases before any broader validation:

- MinerU log file missing;
- MinerU log file present but empty;
- MinerU log file present but stale;
- MinerU log file present with valid business-progress lines;
- sidecar observer expected but not running;
- active-task attribution unavailable or ambiguous;
- fast-complete task with no business signal;
- true MinerU API failure.

This task should make the log-channel ownership state explicit and testable. It must not fabricate page/batch progress.

## Scope

Allowed source/docs areas, if needed:

- `server/lib/ops-mineru-log-parser.mjs`
- `server/services/mineru/local-adapter.mjs`
- `server/upload-server.mjs`
- `ops/mineru-log-observer.mjs`
- `ops/runtime-ownership-status.sh`
- deployment/runbook docs that describe MinerU API/log/sidecar ownership
- focused smoke tests under `server/tests/`
- TaskAndReport report and task ledger

Prefer the smallest change that gives reliable operator/Director evidence. A good solution may be a diagnostic endpoint, richer runtime-ownership status output, focused parser/diagnostic helpers, or a combination.

## Allowed Operations

In the development workspace:

- inspect source and tests;
- implement scoped code/docs/test changes within the allowed areas;
- add focused smoke tests for log-channel diagnostics;
- run relevant checks such as `git diff --check`, changed-file `node --check`, focused smoke tests, and broader static checks if the change touches shared server code;
- write the completion report;
- update only Task 107 in `TaskAndReport/TASK_TRACKING_LIST.md`.

In the production deployment path:

- read-only inspection only:
  - `git status --short --branch`;
  - `git log -1 --oneline`;
  - `docker compose ps`;
  - read-only `curl` health/admission/active-task/global-observation checks;
  - read-only log path/process ownership inspection;
  - no mutation.

## Forbidden Operations

- Do not upload any PDF.
- Do not run pressure, batch-concurrent, soak, broad stress, or long-run tests.
- Do not deploy to production.
- Do not restart/rebuild/rollback services.
- Do not run `docker compose up`, `docker compose down`, `docker compose down -v`, DB reset, MinIO cleanup, volume deletion, model pull/delete/replace, or destructive commands.
- Do not modify production data, DB, MinIO, Docker volumes, sample files, secrets, model settings, or local environment configuration.
- Do not repair, reparse, re-AI, retry, clean up, delete, rename, or mutate historical tasks/materials/artifacts.
- Do not reintroduce heuristic/fabricated page/batch progress.
- Do not weaken strict no-skeleton or false-failure semantics.
- Do not change PRD truth, release-readiness docs, role contracts, or public workflow scope unless explicitly required by the allowed runbook update.
- Do not declare L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.

## Required Implementation / Analysis Points

Your completion report must answer:

1. What is the chosen log-channel ownership diagnostic surface?
2. How does it distinguish missing/empty/stale/valid log states?
3. How does it report sidecar expected/running/unknown state without requiring destructive process management?
4. How does it preserve the rule that MinerU API lifecycle state is authoritative for terminal failure?
5. How does it avoid exposing private host paths in operator-facing UI?
6. What remains production-ops-only and requires a separate Director/user-authorized task?

## Required Tests / Checks

At minimum, add or run focused checks that prove:

- missing log file is classified distinctly;
- empty log file is classified distinctly;
- stale log file is classified distinctly;
- valid progress line is classified as business progress;
- fast-complete/no-business-signal is not fabricated into progress;
- in-flight MinerU API states do not become terminal failure solely because the log channel is missing/empty/stale.

If broader checks are skipped, record exact reasons.

## Completion Report Requirements

Write the report to:

`TaskAndReport/2026-05-14T06-07-35+0800_P1-MinerU-Progress-Log-Channel-Ownership-Diagnostics_REPORT.md`

Then update only Task 107 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- `Status=已回报待 Director 审查` if completed;
- `Status=挂起` if blocked;
- `Next Actor=Director`;
- include branch/HEAD, files changed, implementation summary, commands and exit codes, skipped checks, residual risks, and recommended next actor.

Do not push to GitHub unless the DevelopmentEngineer role instructions explicitly require it for the completion report branch. Director will own final main synchronization in this thread.

## Acceptance Criteria

Director can accept this task if:

- the change is scoped to log-channel ownership diagnostics/observability;
- focused tests cover missing/empty/stale/valid/fast-complete and in-flight no-false-failure semantics;
- production was only inspected read-only, if inspected at all;
- no forbidden operation or readiness claim occurred;
- the report clearly states whether a follow-up production deployment or ops sidecar-start task is needed before another controlled upload validation.
