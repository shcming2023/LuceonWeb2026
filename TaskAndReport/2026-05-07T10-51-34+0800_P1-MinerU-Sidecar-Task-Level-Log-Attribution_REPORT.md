# Lucode Analysis Report: P1 MinerU Sidecar Task-Level Log Attribution

Report time: 2026-05-07T10:51:34+0800

## Basis

This analysis was based on Lucia task brief:

- `TaskAndReport/2026-05-07T10-41-51+0800_P1-MinerU-Sidecar-Task-Level-Log-Attribution_TASK.md`

Lucode performed read-only code/runtime analysis only. No code, task state, logs, services, Docker containers, MinerU process, Ollama process, DB data, or MinIO objects were changed.

## Current Runtime Evidence

Task checked:

```json
{
  "id": "task-1778120784621",
  "fileName": "走向成功_英语_二模卷16篇.pdf",
  "state": "failed",
  "stage": "ai",
  "mineruStatus": "completed",
  "parsedFilesCount": 25,
  "mineruStartedAt": "2026-05-07T02:26:26.472159+00:00",
  "mineruLastStatusAt": "2026-05-07T02:28:07.916Z",
  "parsedAt": "2026-05-07T02:28:09.756Z"
}
```

Task-level observation retained on the task:

```json
{
  "activityLevel": "log-observation-no-business-signal",
  "signalSummary": {
    "progressCount": 0,
    "businessLogCount": 0
  },
  "observerCheckedAt": "2026-05-07T02:28:09.202Z"
}
```

Host raw MinerU logs did contain useful business progress for this same 24-page run:

```text
2026-05-07 10:26:26.513 ... total_pages=24
Layout Predict: 100% ... 24/24
Table-ocr det: 100% ... 13/13
Table-ocr rec ch: 100% ... 148/148
OCR-det ch: 100% ... 32/32
OCR-rec Predict: 100% ... 451/451
Processing pages: 100% ... 24/24
```

Current active-task endpoint:

```json
{
  "activeTask": null,
  "currentProcessingTask": null,
  "queuedTasks": [],
  "takeoverRequiredTasks": [
    { "id": "task-1778120784621", "state": "failed", "stage": "ai" },
    { "id": "task-1778118934116", "state": "failed", "stage": "ai" }
  ]
}
```

Current global observation is non-null but unattributed:

```json
{
  "observer": "host-mineru-log-observer",
  "activityLevel": "active-progress",
  "attribution": "unattributed",
  "unattributedReason": "not exactly 1 active task"
}
```

## Attribution Flow

Sidecar:

- [ops/mineru-log-observer.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/ops/mineru-log-observer.mjs:4): polls every 2000ms by default.
- [ops/mineru-log-observer.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/ops/mineru-log-observer.mjs:17): reads `/ops/mineru/active-task`.
- [ops/mineru-log-observer.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/ops/mineru-log-observer.mjs:20): only uses `taskData.activeTask` for `minObservedAt`, previous observation, and execution profile.
- [ops/mineru-log-observer.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/ops/mineru-log-observer.mjs:30): parses latest host logs with that single active-task context.
- [ops/mineru-log-observer.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/ops/mineru-log-observer.mjs:38): posts the snapshot back to `/ops/mineru-log-observation`.

Upload-server active-task context:

- [server/upload-server.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/upload-server.mjs:1001): normal active candidates require `state=running`, `metadata.mineruTaskId`, and stage in `mineru-processing`, `mineru-queued`, or `result-fetching`.
- [server/upload-server.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/upload-server.mjs:1050): `activeTask` is set only when exactly one `runningWithMineru` task exists, or exactly one drift task exists.

Upload-server attribution:

- [server/upload-server.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/upload-server.mjs:1141): POST `/ops/mineru-log-observation` recomputes eligible tasks from DB.
- [server/upload-server.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/upload-server.mjs:1148): if eligible task count is not exactly 1, the snapshot is saved only as global and returned as `attributed:false`, `reason:not exactly 1 active task`.
- [server/upload-server.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/upload-server.mjs:1157): snapshots older than the task start are rejected as stale.
- [server/upload-server.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/upload-server.mjs:1192): only an attributed snapshot is patched into `task.metadata.mineruObservedProgress`.

UI:

- [src/app/pages/TaskDetailPage.tsx](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/src/app/pages/TaskDetailPage.tsx:813): task detail reads only `task.metadata.mineruObservedProgress`.
- [src/app/pages/TaskManagementPage.tsx](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/src/app/pages/TaskManagementPage.tsx:661): task list also reads only `t.metadata?.mineruObservedProgress`.

## Why Fast-Completing Tasks Lose Useful Logs

For `task-1778120784621`, the timing was:

- `02:26:26.472Z`: MinerU started.
- `02:28:09.202Z`: sidecar produced/posted a low-signal task-level observation.
- `02:28:09.756Z`: MinerU parse completed and task moved out of the eligible MinerU states.
- Later host log parsing could see useful business progress lines, but the task was no longer exactly one eligible active task.

The bottleneck is the double exact-one-active gate:

1. The sidecar only obtains task context from `activeTask`. If `/active-task` is null or ambiguous, the parser runs without a task-specific `minObservedAt` and previous observation.
2. The upload-server attribution endpoint independently requires exactly one currently eligible task at POST time. Once the task has moved to `result-store`, `ai-pending`, `ai-running`, or `failed`, later snapshots cannot be patched back into that task even if the log timestamps fit the task's MinerU execution window.

This means a valid host log can exist but still not appear on task detail if the useful log signal is parsed after the task leaves `state=running` plus MinerU stage.

## Problem Classification

This is primarily a **timing/attribution problem**, with a **UI fallback gap**.

It is not raw log loss:

- Host logs contained the 24-page business progress.
- Global observation was non-null after sidecar recovery.

It is not primarily a parser capability problem:

- The parser can extract phases and activity levels from host logs when given suitable context.

It is not a parse state semantics failure:

- MinerU completed and artifacts were saved.

The user-facing symptom is a UI/task-metadata visibility gap because the UI only shows task-level `mineruObservedProgress`, and the backend refuses to backfill once no exactly-one active task exists.

## Likely Fix Location

Smallest safe fix should be in **upload-server attribution logic plus focused tests**, with optional small sidecar context support.

Recommended implementation direction:

- Keep the current exact-one-active rule for live attribution to avoid cross-task contamination.
- Add a narrow backfill candidate path for recently completed local MinerU tasks where:
  - task has `metadata.mineruTaskId`;
  - task has `metadata.mineruStartedAt`;
  - task has `metadata.mineruLastStatusAt` or `metadata.parsedAt`;
  - snapshot `contextTime`/`observedAt` falls within `[mineruStartedAt, parsedAt + small grace]`;
  - candidate set is exactly one after time-window filtering.
- Prefer updating only `mineruObservedProgress` and a clear `attribution` field; do not change parse state.
- Avoid using stale global observations with no timestamp match.
- Keep existing global observation behavior for ambiguous cases.

Secondary optional improvement:

- Include `takeoverRequiredTasks` or a recently completed task window in `/ops/mineru/active-task` for sidecar context, but only if the sidecar can still avoid ambiguous attribution.

UI fallback alone is not sufficient because it would still be global/unattributed and could show another task's log on a task detail page.

## Test Coverage Needed

Before implementation acceptance, add focused tests covering:

1. One running MinerU task receives live sidecar observation as today.
2. Zero active tasks plus exactly one recently completed task whose time window matches the snapshot receives backfilled `mineruObservedProgress`.
3. Two recently completed candidates with overlapping windows keep the snapshot global/unattributed.
4. Snapshot timestamp before task start is rejected.
5. Snapshot timestamp after the grace window is rejected.
6. Task detail/list UI continues to show only task-attributed progress, not arbitrary global observation.

Likely existing test surface:

- `server/tests` sidecar/dependency smoke or a new focused upload-server route smoke.
- Frontend unit/smoke only if UI text changes.

## Recommended Implementation Task

Recommended task:

`P1 MinerU Sidecar Completed-Window Log Backfill`

Allowed files:

- `server/upload-server.mjs`
- `server/tests/*mineru*log*smoke*.mjs` or a new focused server test file
- `ops/mineru-log-observer.mjs` only if sidecar context must include completed-window candidates
- `src/app/pages/TaskDetailPage.tsx` and `src/app/pages/TaskManagementPage.tsx` only if display wording needs to distinguish live vs backfilled observation
- `TaskAndReport/` report files

Acceptance criteria:

- Fast-completing MinerU tasks with valid host log timestamps show useful task-level `mineruObservedProgress`.
- Ambiguous multi-task windows remain unattributed.
- No task state, parse semantics, retry behavior, or AI behavior changes.
- No silent degradation or misleading cross-task log display.

## Review Required

Lucia review is required. Implementation should wait for a separate Lucia task brief.
