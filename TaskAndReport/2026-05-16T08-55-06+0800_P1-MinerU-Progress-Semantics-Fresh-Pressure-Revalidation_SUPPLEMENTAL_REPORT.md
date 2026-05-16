# P1 MinerU Progress Semantics Fresh Pressure Revalidation Supplemental Snapshot

- Task ID: `TASK-20260516-084828-P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation`
- Role: TestAcceptanceEngineer
- Supplemental snapshot time: 2026-05-16 08:55 +0800
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Development status before snapshot: `## main...origin/main`
- Production HEAD observed: `0598ca5`

## Correction To Prior Blocked Snapshot

The earlier 08:52 blocked report was accurate for that instant, but it is now superseded by fresh runtime evidence: a user-started 24-PDF pressure run appeared immediately afterward.

This supplemental snapshot reopens Task 205 monitoring as active/in progress. It does not claim pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

## Current Classification

`IN_PROGRESS_ACTIVE_PRESSURE_RUN`

No terminal classification yet. The run is active and should continue to be observed at a 5-10 minute cadence while MinerU processing is moving.

## Fresh Run Evidence

Read-only DB summaries since Task 205 issue time (`2026-05-16T08:48:28+0800`) show exactly 24 fresh uploaded tasks/materials:

| Dataset | Fresh records | State / stage summary |
| --- | ---: | --- |
| tasks | 24 | 1 `running` / `mineru-processing`, 23 `pending` / `upload` |
| materials | 24 | 24 `processing` |
| AI metadata jobs | 0 | AI stage has not started for this fresh run |

Active task:

| Field | Value |
| --- | --- |
| Task ID | `task-1778892864544` |
| Material ID | `2276905321424867` |
| File | `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express).pdf` |
| Size | 52,964,792 bytes |
| Task state / stage | `running` / `mineru-processing` |
| Progress | 50 |
| MinerU task ID | `cd19b2fd-8a68-4627-8966-cbe1f90e4e5e` |
| Direct MinerU status | `processing` |

## Progress Semantics Snapshot

`/ops/mineru/active-task` shows the deployed `progressSnapshot` contract working for the active task:

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

The task message still says:

- `MinerU 正在处理，但日志观测滞后：backend=pipeline`

Interpretation: page/backend semantics correctly distinguish stale log observation from real MinerU processing. This must not be treated as failure while direct MinerU API reports `processing` and logs show progress.

## Direct MinerU Evidence

Direct MinerU task API:

- endpoint: `http://127.0.0.1:8083/tasks/cd19b2fd-8a68-4627-8966-cbe1f90e4e5e`
- status: `processing`
- backend: `pipeline`
- created_at: `2026-05-16T00:54:35.953208+00:00`
- started_at: `2026-05-16T00:54:35.953868+00:00`
- completed_at: `null`
- error: `null`
- queued_ahead: 0

Direct MinerU health:

- `queued_tasks=19`
- `processing_tasks=1`
- `completed_tasks=53`
- `failed_tasks=0`

## Log Evidence

MinerU logs were fresh at observation time:

- `/Users/concm/ops/logs/mineru-api.log`: mtime `2026-05-16 08:55:34 +0800`
- `/Users/concm/ops/logs/mineru-api.err.log`: mtime `2026-05-16 08:55:32 +0800`

Tail evidence showed active large-document progress for the active 632-page file:

- `total_pages=632`, `total_batches=10`
- processing window `batch 1/10: 64/632 pages`
- `Layout Predict` reached `64/64`
- `MFR Predict` was progressing, observed through at least `176/467`

This is forward movement. No no-progress or failure condition is met.

## Readiness Versus Progress

`dependency-health?mineruSubmitProbe=false` is still readiness-only. It showed:

- `ok=true`
- `blocking=false`
- `progressSnapshot.lagKind=dependency-health-readiness-only`
- operator message: `依赖健康检查仅代表就绪性，不代表单个任务进度`

This endpoint should not be used as task progress truth.

## Commands Run

| Workspace | Command / endpoint | Exit code | Key output |
| --- | --- | ---: | --- |
| Dev | `git status --short --branch` | 0 | `## main...origin/main` |
| Prod | `date`, `git status --short --branch`, `git rev-parse --short HEAD` | 0 | `2026-05-16 08:55:06 +0800`; production HEAD `0598ca5` |
| Prod | `curl .../ops/mineru/active-task` | 0 | active task `task-1778892864544`; progressSnapshot source `direct-mineru`; direct status `processing` |
| Prod | `curl .../ops/dependency-health?mineruSubmitProbe=false` | 0 | readiness ok, readiness-only progressSnapshot |
| Prod | read-only DB summaries | 0 | 24 fresh tasks/materials, 0 AI jobs |
| Prod | `curl http://127.0.0.1:8083/tasks/cd19b2fd-8a68-4627-8966-cbe1f90e4e5e` | 0 | direct MinerU `processing`, no error |
| Prod | `stat` and `tail` MinerU logs | 0 | fresh logs; large-file active progress |
| Prod | `curl http://127.0.0.1:8083/health` | 0 | queued 19, processing 1, failed 0 |

## Forbidden Actions Confirmation

No upload, cleanup/reset, submit-probe, retry, reparse, re-AI, repair, cancel, restart, rebuild, redeploy, DB/MinIO/Docker/config/model/sample mutation, pressure PASS, L3, release-readiness, production-readiness, or go-live claim was performed.

## Next Monitoring Need

Continue read-only monitoring while the fresh run is active. The next useful snapshot should compare:

- active task page/backend message,
- `progressSnapshot`,
- direct MinerU task API,
- fresh log progress,
- DB task/material state,
- AI job creation once parse completes.
