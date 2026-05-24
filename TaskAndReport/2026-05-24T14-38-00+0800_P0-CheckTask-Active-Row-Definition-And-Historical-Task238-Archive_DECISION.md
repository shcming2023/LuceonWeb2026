# P0 CheckTask Active Row Definition And Historical Task238 Archive Decision

Time: 2026-05-24T14:38:00+0800

## Context

The Director observed that both Luceon and Lucode returned no-task responses
after `check task`.

Current shared control-plane audit:

- Luceon workspace: `/Users/concm/prod_workspace/Luceon2026`
- Lucode workspace: `/Users/concm/Dev_workspace/Luceon2026`
- `origin/main`: `c229a4add29baa0fe35ae97ee3b82a5fab8def44`
- Latest main rows through Task 261 are closed with `Next Actor=None`.
- Task 256 is already closed by Luceon Review v3.
- Task 259, Task 260, and Task 261 are also closed on main.
- Historical Task 238 still used legacy status `未接受已退回` with
  `Next Actor=Lucode`, even though its row instructed not to continue runtime
  action and its recovery path was superseded by Task 239.
- No remote `lucode/TASK-20260522-063003*` or `lucode/task-238*` branch exists.

## Decision

For `check task`, an active/open row requires both a current active `Status` and
a matching `Next Actor`.

`Next Actor` alone is not sufficient.

Active Lucode statuses:

- `下达待 Lucode 执行`
- `Lucode 执行中`
- `退回待 Lucode 修正`

Active Luceon statuses:

- `Lucode 已回报待 Luceon 审查`
- `Luceon 规划中`
- `Luceon 验收中`

Active User status:

- `挂起待 User`

Legacy returned, withdrawn, failed, canceled, paused, and closed rows are
historical/non-executable for `check task` unless a later task or decision row
explicitly reactivates them.

Task 238 is archived as a historical returned/failed row with `Next Actor=None`.
It must not be picked up by Lucode `check task`.

## Boundaries

- No production/runtime/data mutation.
- No Docker, DB, MinIO, LLM, model, credential, sample, or job-store operation.
- No heartbeat automation created.
- No UAT, L3, pressure PASS, release readiness, production readiness, or
  go-live claim.
