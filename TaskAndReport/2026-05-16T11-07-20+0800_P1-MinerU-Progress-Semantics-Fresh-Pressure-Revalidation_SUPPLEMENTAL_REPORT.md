# P1 MinerU Progress Semantics Fresh Pressure Revalidation Supplemental Snapshot 11:07

- Task ID: `TASK-20260516-084828-P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation`
- Role: TestAcceptanceEngineer
- Supplemental snapshot time: 2026-05-16 11:07 +0800
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
| tasks | 24 | 4 `review-pending` / `review`, 1 `running` / `mineru-processing`, 19 `pending` / `upload` |
| materials | 24 | 4 `reviewing`, 20 `processing` |
| AI metadata jobs | 4 | 4 `review-pending` |

Since the 09:02 snapshot, the first four large PDFs reached review-pending with AI metadata jobs completed to review-pending. The current active parse is the fifth large PDF.

## Active Task

| Field | Value |
| --- | --- |
| Task ID | `task-1778892873718` |
| Material ID | `3932737649212363` |
| File | `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics _2018(Haese Mathematics).pdf` |
| Size | 91,501,329 bytes |
| Task state / stage | `running` / `mineru-processing` |
| Progress | 50 |
| MinerU task ID | `a433fbd5-ae70-4221-8a07-39a43599c655` |
| Direct MinerU status | `processing` |

Direct MinerU task API:

- status: `processing`
- completed_at: `null`
- error: `null`
- queued_ahead: 0
- started_at: `2026-05-16T02:41:57.140104+00:00`

Direct MinerU health:

- `queued_tasks=0`
- `processing_tasks=1`
- `completed_tasks=76`
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

The task message remains `MinerU 正在处理，但日志观测滞后：backend=pipeline`. This is acceptable during this snapshot because the operator-facing progress snapshot explicitly says the MinerU API is still processing and direct MinerU/log evidence confirms forward movement.

## Log Evidence

Host log files were fresh:

- `/Users/concm/ops/logs/mineru-api.log`: mtime `2026-05-16 11:08:04 +0800`
- `/Users/concm/ops/logs/mineru-api.err.log`: mtime `2026-05-16 11:08:04 +0800`

Tail evidence showed active progress on the current large PDF:

- `Processing pages` reached `448/500`.
- `Layout Predict` completed `52/52`.
- `MFR Predict` progressed to at least `1216/2633`.

This is continuing progress, not a hung condition.

## Readiness And Admission

`dependency-health?mineruSubmitProbe=false`:

- `ok=true`
- `blocking=false`
- `progressSnapshot.lagKind=dependency-health-readiness-only`
- Ollama `qwen3.5:9b` responded, but with high duration `14156ms` near the 15s probe limit.

Admission circuit:

- state `closed`
- counts: `parsePending=19`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`
- `activeTaskClean=false` because active work is expected.

Dependency health remains readiness-only and is not used as task-progress truth.

## Operator Semantics Assessment

Current semantics are improved for active progress judgment:

- Active-task/progressSnapshot correctly separates stale log observation from direct MinerU processing.
- Direct MinerU API is correctly treated as authoritative for active parse progress.
- The stale-log wording should not be interpreted as task failure.

Residual observability issue persists:

- Container-mounted log-channel diagnostics report log staleness while host logs are fresh and moving. This mismatch remains a Director-visible follow-up risk, but it did not cause the active-task progressSnapshot to misclassify the run.

## Commands Run

| Workspace | Command / endpoint | Exit code | Key output |
| --- | --- | ---: | --- |
| Dev | `git status --short --branch` | 0 | `## main...origin/main` |
| Dev | read `TaskAndReport/TASK_TRACKING_LIST.md` and Task 205 brief | 0 | Task 205 still `执行中` / `TestAcceptanceEngineer` |
| Prod | `date`, `git status --short --branch`, `git rev-parse --short HEAD` | 0 | `2026-05-16 11:07:20 +0800`; production HEAD `0598ca5` |
| Prod | `curl -fsS http://localhost:8081/__proxy/upload/health` | 0 | upload-server ok |
| Prod | `curl .../ops/dependency-health?mineruSubmitProbe=false` | 0 | readiness ok, no submit-probe, Ollama chat ok |
| Prod | `curl .../ops/mineru/admission-circuit` | 0 | circuit closed; active pressure work present |
| Prod | `curl .../ops/mineru/active-task` | 0 | active task `task-1778892873718`, direct MinerU `processing` |
| Prod | `curl http://127.0.0.1:8083/health` | 0 | queued 0, processing 1, completed 76, failed 0 |
| Prod | DB summaries through `/__proxy/db/*` | 0 | 4 review-pending, 1 running, 19 pending |
| Prod | direct MinerU task API for `a433fbd5-ae70-4221-8a07-39a43599c655` | 0 | direct MinerU `processing`, no error |
| Prod | `stat` and `tail` host MinerU logs | 0 | fresh log mtime and forward MFR progress |
| Prod | `/cms/tasks` HTTP check | 0 | HTTP 200 |

## Forbidden Actions Confirmation

No upload, cleanup/reset, submit-probe, retry, reparse, re-AI, repair, cancel, restart, rebuild, redeploy, DB/MinIO/Docker/config/model/sample mutation, pressure PASS, L3, release-readiness, production-readiness, or go-live claim was performed.

## Next Monitoring Need

Continue heartbeat monitoring. The next useful snapshot should check whether the current 91.5 MB PDF reaches review-pending and whether later pending tasks advance into parse/AI stages.
