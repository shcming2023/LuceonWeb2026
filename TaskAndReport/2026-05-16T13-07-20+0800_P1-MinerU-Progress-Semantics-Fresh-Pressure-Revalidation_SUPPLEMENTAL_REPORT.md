# P1 MinerU Progress Semantics Fresh Pressure Revalidation Supplemental Snapshot 13:07

- Task ID: `TASK-20260516-084828-P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation`
- Role: TestAcceptanceEngineer
- Supplemental snapshot time: 2026-05-16 13:07 +0800
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Production HEAD observed: `0598ca5`

## Current Classification

`IN_PROGRESS_ACTIVE_PRESSURE_RUN`

The run is still active and still making forward progress. No terminal, no-progress, system-level failure, pressure PASS, L3, release-readiness, production-readiness, or go-live claim is made.

## Fresh Run Counts

Read-only DB summary for records created after Task 205 issue time:

| Dataset | Fresh records | State / stage summary |
| --- | ---: | --- |
| tasks | 24 | 11 `review-pending` / `review`, 1 `running` / `mineru-processing`, 12 `pending` / `upload` |
| materials | 24 | 11 `reviewing`, 13 `processing` |
| AI metadata jobs | 11 | 11 `review-pending` |

Since the 11:07 snapshot, the run advanced from 4 review-pending tasks to 11 review-pending tasks. No fresh failed task or failed AI job was observed.

## Active Task

| Field | Value |
| --- | --- |
| Task ID | `task-1778892896111` |
| Material ID | `500702303383307` |
| File | `Cambridge IGCSE(0580)  Core  Mathematics_2023(Hodder Education).pdf` |
| Size | 63,585,444 bytes |
| Task state / stage | `running` / `mineru-processing` |
| Progress | 50 |
| MinerU task ID | `d9fdc486-f362-4da8-82c2-3928e05cc785` |
| Direct MinerU status | `processing` |

Direct MinerU task API:

- status: `processing`
- completed_at: `null`
- error: `null`
- queued_ahead: 0
- started_at: `2026-05-16T05:04:45.811309+00:00`

Direct MinerU health:

- `queued_tasks=0`
- `processing_tasks=1`
- `completed_tasks=83`
- `failed_tasks=0`

## Progress Snapshot Semantics

`/ops/mineru/active-task` continued to prioritize direct MinerU evidence:

- `progressSnapshot.version=progress-snapshot-v0.1`
- `phase=parse`
- `source=direct-mineru`
- `sourcePriority=direct-mineru`
- `directMineruStatus=processing`
- `dbState=running`
- `dbStage=mineru-processing`
- `logState=stale`
- `lagKind=none`
- `operatorMessage=MinerU API 仍在处理`

The task message remains `MinerU 正在处理，但日志观测滞后：backend=pipeline`. This is not failure evidence while direct MinerU API and host logs show active processing.

## Log Evidence

Host log files were fresh:

- `/Users/concm/ops/logs/mineru-api.log`: mtime `2026-05-16 13:07:49 +0800`
- `/Users/concm/ops/logs/mineru-api.err.log`: mtime `2026-05-16 13:07:48 +0800`

Tail evidence showed continuing activity and transition into a later active file:

- A 714-page document reached `Processing pages: 714/714`.
- A 380-page document started with `total_batches=6`.
- Batch `1/6` reached `Layout Predict 64/64`.
- MFR progressed through `783/783`.
- Table OCR detection/recognition and table wireless/wired prediction progressed.
- OCR detection for the current window was still progressing at the tail.

This is continuing forward movement, not a hung condition.

## Readiness And Admission

`dependency-health?mineruSubmitProbe=false`:

- `ok=true`
- `blocking=false`
- `progressSnapshot.lagKind=dependency-health-readiness-only`
- Ollama `qwen3.5:9b` readiness succeeded in `2581ms`.

Admission circuit:

- state `closed`
- counts: `parsePending=12`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`
- `activeTaskClean=false` because active work is expected.

Dependency health remains readiness-only and is not used as task-progress truth.

## Operator Semantics Assessment

Current semantics remain usable for human progress judgment:

- `progressSnapshot` separates readiness from progress.
- During log staleness, active-task still uses direct MinerU status as the progress truth.
- The operator-facing message `MinerU API 仍在处理` prevents the stale-log warning from becoming a false failure judgment.

Residual risk persists:

- Log observation from the container-mounted channel remains stale relative to host logs. Host logs were required for detailed progress attribution.

## Commands Run

| Workspace | Command / endpoint | Exit code | Key output |
| --- | --- | ---: | --- |
| Dev | `git status --short --branch` | 0 | `## main...origin/main` |
| Dev | read `TaskAndReport/TASK_TRACKING_LIST.md` and Task 205 brief | 0 | Task 205 still `执行中` / `TestAcceptanceEngineer` |
| Prod | `date`, `git status --short --branch`, `git rev-parse --short HEAD` | 0 | `2026-05-16 13:07:20 +0800`; production HEAD `0598ca5` |
| Prod | `curl -fsS http://localhost:8081/__proxy/upload/health` | 0 | upload-server ok |
| Prod | `curl .../ops/dependency-health?mineruSubmitProbe=false` | 0 | readiness ok, no submit-probe |
| Prod | `curl .../ops/mineru/admission-circuit` | 0 | circuit closed; active pressure work present |
| Prod | `curl .../ops/mineru/active-task` | 0 | active task `task-1778892896111`, direct MinerU `processing` |
| Prod | `curl http://127.0.0.1:8083/health` | 0 | queued 0, processing 1, completed 83, failed 0 |
| Prod | DB summaries through `/__proxy/db/*` | 0 | 11 review-pending, 1 running, 12 pending |
| Prod | direct MinerU task API for `d9fdc486-f362-4da8-82c2-3928e05cc785` | 0 | direct MinerU `processing`, no error |
| Prod | `stat` and `tail` host MinerU logs | 0 | fresh log mtime and forward progress |
| Prod | `/cms/tasks` HTTP check | 0 | HTTP 200 |

## Forbidden Actions Confirmation

No upload, cleanup/reset, submit-probe, retry, reparse, re-AI, repair, cancel, restart, rebuild, redeploy, DB/MinIO/Docker/config/model/sample mutation, pressure PASS, L3, release-readiness, production-readiness, or go-live claim was performed.

## Next Monitoring Need

Continue heartbeat monitoring. The next useful snapshot should check whether the active 63.6 MB PDF reaches review-pending and whether the remaining 12 pending tasks advance into parse/AI stages.
