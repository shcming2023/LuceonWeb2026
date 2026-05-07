# Task: P1 MinerU Sidecar Completed-Window Log Backfill

```text
Task:
P1 MinerU Sidecar Completed-Window Log Backfill

Assignee:
Lucode

Issued by:
Lucia

Project:
Luceon2026

Date:
2026-05-07

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-07T10-56-16+0800_P1-MinerU-Sidecar-Completed-Window-Log-Backfill_TASK.md

Required reading before execution:
- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/lucode.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-07T10-51-34+0800_P1-MinerU-Sidecar-Task-Level-Log-Attribution_REPORT.md
- TaskAndReport/2026-05-07T10-56-16+0800_P1-MinerU-Sidecar-Task-Level-Log-Attribution_LUCIA_REVIEW.md

Background:
The sidecar is running and host MinerU logs contain useful progress, but fast-completing tasks can leave the eligible active MinerU window before the useful sidecar snapshot is attributed to task metadata. The UI reads task-level `metadata.mineruObservedProgress`, so users may see missing or low-signal parse logs even though host logs contain valid business progress.

Objective:
Implement a safe completed-window backfill path for MinerU sidecar observations so fast-completing tasks can receive task-level `mineruObservedProgress` when the snapshot timestamp clearly matches exactly one recently completed task.

Non-goals:
- Do not change parse state semantics.
- Do not change retry/reparse behavior.
- Do not restart services or mutate production data.
- Do not display arbitrary global observations on task detail pages.
- Do not accept ambiguous multi-task attribution.
- Do not claim production release readiness.

Allowed files:
- `server/upload-server.mjs`
- `ops/mineru-log-observer.mjs`, only if completed-window context must be passed to the parser
- `server/tests/*mineru*log*smoke*.mjs` or a new focused server test file
- `src/app/pages/TaskDetailPage.tsx` and `src/app/pages/TaskManagementPage.tsx`, only if display wording needs to distinguish live vs backfilled observation
- `TaskAndReport/*_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden changes:
- Do not edit AI metadata behavior.
- Do not edit production-only config.
- Do not edit PRD truth, project ledger, handoff, role contracts, or release judgments.
- Do not mutate production tasks.
- Do not relax attribution in a way that can show another task's logs on the wrong task.

Required implementation direction:
1. Preserve the existing exact-one-active attribution behavior for live MinerU tasks.
2. Add a narrow completed-window candidate path for local MinerU tasks where:
   - task has `metadata.mineruTaskId`;
   - task has `metadata.mineruStartedAt`;
   - task has `metadata.mineruLastStatusAt` or `metadata.parsedAt`;
   - task has moved out of live MinerU states recently;
   - snapshot `contextTime`, `observedAt`, or `logFileUpdatedAt` falls within `[mineruStartedAt, parsedAt + small grace]`;
   - exactly one candidate matches after time-window filtering.
3. If exactly one completed-window candidate matches, patch only task metadata fields needed for observation:
   - `metadata.mineruObservedProgress`
   - an explicit attribution marker such as `attribution: <taskId>` or `attributionMode: completed-window-backfill`
4. If zero or multiple candidates match, keep snapshot global/unattributed.
5. Reject snapshots before task start or after the grace window.
6. Do not alter task `state`, `stage`, parsed artifacts, retry state, or AI state.

Required tests:
- Existing live attribution still works.
- Zero active tasks plus exactly one recently completed matching task backfills observation.
- Two overlapping completed candidates remain unattributed.
- Snapshot before task start is rejected.
- Snapshot after grace window is rejected.
- UI does not show arbitrary global observation as task-level evidence.

Required checks:
- `git status --short --branch`
- focused new/updated sidecar attribution smoke test
- relevant existing MinerU log smoke tests
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`
- `git diff --check`

GitHub sync requirements:
- Start from GitHub `main`.
- Use a scoped branch, suggested:
  `lucode/p1-mineru-sidecar-completed-window-backfill`
- Commit and push the branch to GitHub.
- Do not merge to `main` before Lucia review.

Completion report storage requirements:
- Write the report into TaskAndReport/:
  `YYYY-MM-DDTHH-MM-SS+0800_P1-MinerU-Sidecar-Completed-Window-Log-Backfill_REPORT.md`
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch, HEAD, status, next actor, and evidence summary.

Completion report must include:
- implementation summary
- files changed
- exact commands and exit codes
- test evidence
- examples for attributed and unattributed cases
- risks and residual technical debt
- whether Lucia review is required

Acceptance criteria:
- Fast-completing MinerU tasks can receive useful task-level observation when time-window attribution is unambiguous.
- Ambiguous cases remain unattributed.
- No task state, parse semantics, retry behavior, or AI behavior changes.
- Tests, TypeScript, build, and diff check pass.
```
