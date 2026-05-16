# P1 MinerU Progress Semantics Fresh Pressure Revalidation Final Report

- Task ID: `TASK-20260516-084828-P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation`
- Role: TestAcceptanceEngineer
- Based on Director task brief: `TaskAndReport/2026-05-16T08-48-28+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Development HEAD before final report: `544217b`
- Production HEAD observed: `0598ca5`
- Final observation time: 2026-05-16 14:20-14:21 +0800

## Final Classification

`PASS_FOR_PROGRESS_SEMANTICS_BOUNDARY_WITH_RESIDUAL_AI_FAILURE`

The fresh user-started 24-PDF pressure run reached terminal backend state by the 14:20 snapshot:

- 24/24 tasks reached terminal states.
- 24/24 MinerU parses completed.
- 23/24 tasks reached `review-pending` / `review`.
- 1/24 task failed in AI stage after MinerU completion.
- No active MinerU task, queued MinerU task, result-ingestion lag, drift task, submit-retryable task, or takeover-required task remained.

This is not a production-readiness, L3, release-readiness, go-live, or overall pressure PASS claim. It is a TestAcceptanceEngineer recommendation that the Task 205 monitoring objective passed for MinerU progress semantics and terminal-state attribution, with a residual single AI-stage failure for Director decision.

## Monitoring Timeline

| Snapshot | Fresh task state summary | Key progress evidence |
| --- | --- | --- |
| 08:52 | No fresh run observed yet | Initial report recorded blocked baseline before user upload was visible. |
| 08:55 | 1 `running` / `mineru-processing`, 23 `pending` / `upload` | Active `task-1778892864544`; direct MinerU `processing`; host logs fresh. |
| 09:02 | 1 `running` / `mineru-processing`, 23 `pending` / `upload` | Direct MinerU still `processing`; host logs showed MFR/Table OCR progress. |
| 11:07 | 4 `review-pending`, 1 `running`, 19 `pending` | Direct MinerU and logs confirmed continued forward progress. |
| 13:07 | 11 `review-pending`, 1 `running`, 12 `pending` | `progressSnapshot.source=direct-mineru`; host logs fresh; no hung condition. |
| 14:20 | 23 `review-pending`, 1 `failed` in AI | Active-task empty; direct MinerU queued 0 / processing 0 / completed 96 / failed 0. |

Supplemental evidence files:

- `TaskAndReport/2026-05-16T08-55-06+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_SUPPLEMENTAL_REPORT.md`
- `TaskAndReport/2026-05-16T09-02-28+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_SUPPLEMENTAL_REPORT.md`
- `TaskAndReport/2026-05-16T11-07-20+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_SUPPLEMENTAL_REPORT.md`
- `TaskAndReport/2026-05-16T13-07-20+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_SUPPLEMENTAL_REPORT.md`

## Final Runtime Evidence

### Fresh Run Counts

Read-only DB summary for records created after Task 205 issue time:

| Dataset | Fresh records | Final summary |
| --- | ---: | --- |
| tasks | 24 | 23 `review-pending` / `review`, 1 `failed` / `ai` |
| materials | 24 | 23 `reviewing`, 1 `failed` |
| AI metadata jobs | 24 | 23 `review-pending`, 1 `failed` |

The failed item was:

- Task: `task-1778892903338`
- Material: `2077680543704196`
- File: `蓝月、血月、橙月？月亮为啥还会变色？.pdf`
- MinerU task: `95bd0e34-f602-4990-9546-cb25c2281bef`
- MinerU status: `completed`
- Task state/stage: `failed` / `ai`
- AI job: `ai-job-1778908848756-4ef4`, `failed`, progress 25

### Active Task And MinerU Evidence

`/ops/mineru/active-task` at 14:20 reported:

- `activeTask=null`
- `currentProcessingTask=null`
- `queuedTasks=[]`
- `completedButNotIngestedTasks=[]`
- `driftTasks=[]`
- `submitRetryableTasks=[]`
- `takeoverRequiredTasks=[]`
- `resultIngestionLagTasks=[]`
- `historicalAiFailureTasks` included the fresh AI-stage failed task `task-1778892903338`
- diagnostic mode used DB-derived task source with direct MinerU checked

Direct MinerU `/health` at 14:20 reported:

- `status=healthy`
- `queued_tasks=0`
- `processing_tasks=0`
- `completed_tasks=96`
- `failed_tasks=0`

The final state therefore does not indicate MinerU parse failure or stuck processing. The remaining defect is AI-stage handling for one completed parse.

### Dependency And Admission

`dependency-health?mineruSubmitProbe=false`:

- `ok=true`
- `blocking=false`
- `progressSnapshot.version=progress-snapshot-v0.1`
- `phase=unknown`
- `lagKind=dependency-health-readiness-only`
- operator message: dependency health is readiness-only and not single-task progress
- Ollama `qwen3.5:9b` readiness succeeded and model was resident

Admission circuit:

- state `closed`
- `parsePending=0`
- `parseRunning=0`
- `aiPending=0`
- `aiRunning=0`
- `activeTaskClean=true`

### UI Accessibility

`/cms/tasks` HTTP check returned `200 450`. Page accessibility was available for operator review, but this report does not claim visual UI acceptance beyond HTTP reachability.

### Log Evidence

Host MinerU logs remained materially useful for progress attribution during the run:

- `/Users/concm/ops/logs/mineru-api.log`: mtime `2026-05-16 14:21:56 +0800`
- `/Users/concm/ops/logs/mineru-api.err.log`: mtime `2026-05-16 14:16:49 +0800`
- Tail evidence around the final file showed OCR recognition progressing to `846/846` and page processing reaching `62/62`.

Across the 08:55, 09:02, 11:07, and 13:07 snapshots, direct MinerU API plus host logs consistently showed forward progress. This avoided false failure classification when container log-channel diagnostics were stale.

## Operator Semantics Assessment

The deployed progress semantics were materially better than the earlier failure mode:

- During active parse, `/ops/mineru/active-task` exposed `progressSnapshot.source=direct-mineru`.
- The operator message used direct MinerU truth when logs were stale: `MinerU API 仍在处理`.
- Dependency health remained clearly readiness-only instead of being treated as task progress.
- Final active-task state correctly became empty after all tasks reached terminal backend states.

Residual observability gap:

- Container log-channel ownership can still be stale or less informative than host MinerU logs.
- Human operators still need backend/direct-MinerU evidence, or an improved log-channel owner, to explain detailed page/batch movement.

## Commands Run

| Workspace | Command / endpoint | Exit code | Key output |
| --- | --- | ---: | --- |
| Dev | `git status --short --branch` | 0 | `## main...origin/main` |
| Dev | read `TaskAndReport/TASK_TRACKING_LIST.md` and Task 205 brief | 0 | Task 205 was `执行中` / `TestAcceptanceEngineer` |
| Prod | `date`, `git status --short --branch`, `git rev-parse --short HEAD` | 0 | `2026-05-16 14:20:43 +0800`; production HEAD `0598ca5` |
| Prod | `curl -fsS http://localhost:8081/__proxy/upload/health` | 0 | upload-server ok |
| Prod | `curl .../ops/dependency-health?mineruSubmitProbe=false` | 0 | readiness ok; no submit-probe; readiness-only progress snapshot |
| Prod | `curl .../ops/mineru/admission-circuit` | 0 | circuit closed; no parse/AI pending or running counts |
| Prod | `curl .../ops/mineru/active-task` | 0 | no active/queued/drift/lag/takeover work remained |
| Prod | `curl http://127.0.0.1:8083/health` | 0 | queued 0, processing 0, completed 96, failed 0 |
| Prod | DB summaries through `/__proxy/db/*` | 0 | 23 review-pending, 1 AI failed |
| Prod | `stat` and `tail` host MinerU logs | 0 | final logs showed OCR/page processing completion evidence |
| Prod | `/cms/tasks` HTTP check | 0 | HTTP 200, 450 bytes |

## Forbidden Actions Confirmation

No upload, cleanup/reset, manual/extra submit-probe, retry, reparse, re-AI, repair, cancel, restart, rebuild, redeploy, DB/MinIO/Docker/config/secret/model/sample mutation, pressure PASS, L3, release-readiness, production-readiness, or go-live claim was performed.

## Skipped Checks And Reasons

- No direct active MinerU task API was called in the final snapshot because active-task was already empty and direct MinerU health showed no processing.
- No screenshot/browser interaction was performed; `/cms/tasks` HTTP reachability was sufficient for this monitoring boundary.
- No retry/reparse/re-AI was performed for the failed AI item because the task brief forbids mutation and repair.

## Risks And Residual Issues

- One small file reached AI-stage failure despite successful MinerU parse. Director should decide whether this is acceptable pressure-run residual, a retry candidate, or a follow-up AI error handling task.
- Detailed human-readable progress still depends partly on host MinerU logs when the container log-channel is stale.
- This task validates monitoring/progress semantics for the run; it does not certify release readiness or production go-live.

## Recommendation To Director

Recommend `PASS_FOR_TASK_205_MONITORING_BOUNDARY_WITH_RESIDUAL_AI_FAILURE`.

Director review is required to decide:

- whether the 23/24 review-pending result plus 1 AI-stage failure is acceptable for this pressure validation boundary,
- whether to issue a follow-up task for the single AI failed PDF,
- whether to issue a follow-up task for log-channel ownership improvement,
- whether any broader pressure, UAT, L3, release, or production-readiness decision is allowed.
