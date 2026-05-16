# P1 MinerU Progress Semantics Fresh Pressure Revalidation Report

- Task ID: `TASK-20260516-084828-P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation`
- Role: TestAcceptanceEngineer
- Based on Director task brief: `TaskAndReport/2026-05-16T08-48-28+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Development HEAD before report: `77a6dbf`
- Production HEAD observed: `0598ca5`
- Observation time: 2026-05-16 08:52 +0800

## Final Classification

`BLOCKED_WAITING_FOR_USER_MANUAL_UPLOAD`

No fresh user-started active or queued pressure run was available at observation time. Per the task brief, TestAcceptanceEngineer did not upload files, clear/reset data, run submit-probe, retry/reparse/re-AI, repair, cancel, restart, redeploy, rebuild, or mutate production state.

## Scope Performed

Performed read-only baseline checks only:

- Development branch/status check.
- Production upload health.
- Production dependency-health with `mineruSubmitProbe=false`.
- Production admission circuit.
- Production active-task diagnostics.
- Direct MinerU `/health`.
- Log-channel ownership diagnostics.
- `/cms/tasks` HTTP reachability.
- Read-only DB summaries for tasks/materials/AI metadata jobs.

No code checks were required because this task made no code changes.

## Command Evidence

| Workspace | Command / endpoint | Exit code | Key output |
| --- | --- | ---: | --- |
| Dev | `git status --short --branch` | 0 | `## main...origin/main` |
| Dev | `git rev-parse --short HEAD` | 0 | `77a6dbf` |
| Prod | `date '+%Y-%m-%d %H:%M:%S %z'` | 0 | `2026-05-16 08:52:45 +0800` |
| Prod | `git status --short --branch` | 0 | `## main...origin/main` |
| Prod | `git rev-parse --short HEAD` | 0 | `0598ca5` |
| Prod | `curl -fsS http://localhost:8081/__proxy/upload/health` | 0 | `{"ok":true,"service":"upload-server"}` |
| Prod | `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=false'` | 0 | `ok=true`, `blocking=false`; `progressSnapshot.version=progress-snapshot-v0.1`; phase `unknown`; `lagKind=dependency-health-readiness-only`; operator message says dependency health is readiness, not single-task progress. |
| Prod | `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'` | 0 | circuit `closed`; counts parsePending 0, parseRunning 0, aiPending 0, aiRunning 0; `activeTaskClean=true`. |
| Prod | `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'` | 0 | `activeTask=null`, `currentProcessingTask=null`, `queuedTasks=[]`, `resultIngestionLagTasks=[]`; one historical AI failure retained. |
| Prod | `curl -sS --max-time 10 http://127.0.0.1:8083/health` | 0 | MinerU healthy; queued 0, processing 0, completed 48, failed 0. |
| Prod | `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership'` | 0 | selected stdout source `api-noise-only`; stderr stale but has historical business signals; sidecar `not-observed`; no active task to attribute. |
| Prod | `curl -sS -o /tmp/luceon_cms_tasks_check.html -w '%{http_code} %{size_download}\\n' --max-time 10 http://localhost:8081/cms/tasks` | 0 | HTTP `200`, 450 bytes. |
| Prod | read-only DB summaries via `/__proxy/db/tasks`, `/materials`, `/ai-metadata-jobs` | 0 | 24 tasks/materials/AI jobs total, all from prior pressure window; 0 records created since Task 205 issue time. |

## Baseline Runtime Evidence

### Progress Snapshot Surface

Production exposes the deployed progress snapshot contract:

- `progressSnapshot.version=progress-snapshot-v0.1`
- `phase=unknown`
- `source=mixed`
- `sourcePriority=db`
- `freshness=unknown`
- `confidence=medium`
- `lagKind=dependency-health-readiness-only`
- `directMineruStatus=null`
- `dbState=null`
- `dbStage=null`
- `logState=missing`
- operator message: `依赖健康检查仅代表就绪性，不代表单个任务进度`

This confirms the required surface exists, but there was no active task for validating real progress semantics.

### Active And Queued Work

`/ops/mineru/active-task` reported:

- `activeTask=null`
- `currentProcessingTask=null`
- `queuedTasks=[]`
- `completedButNotIngestedTasks=[]`
- `driftTasks=[]`
- `submitRetryableTasks=[]`
- `takeoverRequiredTasks=[]`
- `resultIngestionLagTasks=[]`
- `historicalAiFailureTasks`: one historical AI-stage failed task, `task-1778848110965`.

Direct MinerU `/health` also reported no active processing:

- `queued_tasks=0`
- `processing_tasks=0`
- `completed_tasks=48`
- `failed_tasks=0`

### DB Summary

Read-only DB summaries showed no fresh run after Task 205 was issued at `2026-05-16T08:48:28+0800`:

| Dataset | Total | Terminal / active summary | New records since task issue |
| --- | ---: | --- | ---: |
| tasks | 24 | 23 `review-pending`, 1 `failed`; stages 23 `review`, 1 `ai` | 0 |
| materials | 24 | 23 `reviewing`, 1 `failed` | 0 |
| AI metadata jobs | 24 | 23 `review-pending`, 1 `failed` | 0 |

The one failed item is the known historical AI residual from Task 190, not a fresh MinerU-progress validation item.

## Page Semantics Versus Backend Evidence

`/cms/tasks` was reachable with HTTP 200, but no fresh active pressure task existed to compare page semantics against `progressSnapshot` and direct MinerU API/log evidence.

Therefore this run cannot validate:

- active page progress wording,
- `progressSnapshot` freshness during processing,
- direct MinerU API versus DB lag during active long-running work,
- stale log-channel distinction during active work,
- large-file versus small-file progress semantics,
- AI residual behavior for a new run.

## Skipped Checks And Reasons

- No upload performed: forbidden by task brief.
- No data cleanup/reset performed: forbidden by task brief.
- No submit-probe run: forbidden unless explicitly authorized; this task required no manual submit-probe.
- No retry/reparse/re-AI/repair/cancel/reset: forbidden by task brief.
- No production restart/rebuild/redeploy/rollback: forbidden by task brief.
- No browser screenshot committed: `/cms/tasks` was reachable, but without active run screenshots would not add useful progress-semantics evidence.
- No direct MinerU task API lookup for an active MinerU task: no active `mineruTaskId` was present.

## Risks And Residual Debt

- The deployed `progressSnapshot` surface is present and readiness-only messaging is correct in dependency-health, but real progress semantics remain unvalidated under a fresh active long-running pressure run.
- Log-channel ownership still reports sidecar `not-observed` and selected stdout `api-noise-only` after idle; without active work this is baseline observability context, not progress failure evidence.
- The historical AI residual remains visible as `historicalAiFailureTasks`; it must not be confused with a new MinerU parse-progress problem.

## Recommendation To Director

Keep Task 205 blocked until the user manually starts a fresh pressure run. After the user upload begins, re-run TestAcceptanceEngineer monitoring immediately at a 5-10 minute cadence during active MinerU processing.

Director review is required to decide whether to leave this task pending for user manual upload, issue a new monitoring heartbeat, or close/reissue the task after the user starts the run.

## GitHub Sync

This report and the task ledger update should be committed and pushed after local diff checks pass.
