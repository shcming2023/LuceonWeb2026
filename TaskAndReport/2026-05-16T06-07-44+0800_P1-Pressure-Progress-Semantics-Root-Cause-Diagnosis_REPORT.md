# DevelopmentEngineer Report - Task 192

## Task

- Based on Director task brief: `TaskAndReport/2026-05-16T06-07-44+0800_P1-Pressure-Progress-Semantics-Root-Cause-Diagnosis_TASK.md`
- Role: DevelopmentEngineer
- Scope executed: read-only root-cause diagnosis for pressure-run progress semantics lag.
- Scope not executed: no code/source/UI/test implementation, no production mutation, no upload, no pressure rerun, no retry/reparse/re-AI/repair/reset, no MinerU submit probe, no readiness/L3/pressure PASS/go-live claim.

## Branch / HEAD

- Development workspace: `main` / `7777ca6 Require root cause diagnosis for progress semantics`
- Development workspace status at start: `## main...origin/main`
- Production workspace: `main` / `1716add Dispatch dependency health production validation`
- Production workspace status observed read-only:
  - `.gitignore` modified
  - `docker-compose.override.yml` modified
  - `docs/codex/TEST_MATRIX.md` modified
  - `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md` modified
  - `ops/runtime-ownership-status.sh` modified
  - `server/db-server.mjs` modified
  - `server/tests/worker-smoke.mjs` modified
  - `src/app/components/BatchUploadModal.tsx` modified
  - `src/app/pages/SourceMaterialsPage.tsx` modified
- GitHub sync status: no `git fetch`, `git pull`, `git push`, commit, or branch operation was executed in this DevelopmentEngineer run. The active role-thread rule and task brief did not explicitly authorize sync or push.

## Files Changed

- Added: `TaskAndReport/2026-05-16T06-07-44+0800_P1-Pressure-Progress-Semantics-Root-Cause-Diagnosis_REPORT.md`
- Updated: `TaskAndReport/TASK_TRACKING_LIST.md`

## Executive Diagnosis

The pressure-run semantic lag is not one single MinerU runtime failure. The final runtime truth is coherent: direct MinerU is healthy and idle, 24 pressure tasks are terminal, 23 reached `review-pending/review`, and 1 failed in AI after MinerU completed. The confusing operator experience comes from multiple truth surfaces that update at different clocks and are currently flattened into similar-looking UI/backend messages.

Root-cause ranking:

1. **Primary defect: progress semantics do not expose source/timestamp/confidence as a first-class state model.** The UI and task metadata mainly consume `task.metadata.mineruObservedProgress`, `task.message`, `task.state`, and `task.stage`; they do not present a unified "MinerU API truth vs DB sync vs log observation vs AI phase" model. During long runs this makes stale log observations look like parser state rather than observability state.
2. **Expected async lag: DB ParseTask state lags direct MinerU completion until worker polling/result ingestion catches up.** This is normal in a poll-based worker. It becomes confusing because active-task and UI surfaces can still reflect DB `running/mineru-processing` while direct MinerU already completed or logs have stopped.
3. **Defect/diagnostic gap: log-channel stale after idle or after terminal completion is currently too easy to read as active parse trouble.** The log-channel endpoint correctly says logs are diagnostic and not lifecycle authority, but task-detail copy still says "MinerU still processing" whenever `activityLevel` starts with `log-observation-*`, even if the task is terminal.
4. **Defect/diagnostic gap: dependency-health is readiness, not progress.** It probes MinerU `/health` and Ollama chat with short deadlines. Prior pressure observations where dependency-health timed out during heavy work should be interpreted as readiness/probe latency, not direct evidence that active MinerU parsing stopped.
5. **Secondary defect: event log contains ambiguous progress events such as `Status changed to undefined`.** This comes from transition logging when an update lacks `state/message`, and it muddies timeline reconstruction.

## Source-of-Truth Map

| Surface | Current role | Evidence | Diagnostic conclusion |
| --- | --- | --- | --- |
| Direct MinerU API `/health` | Parser runtime health and queue/process counts | `healthy`, queued `0`, processing `0`, completed `48`, failed `0` | Current MinerU runtime is healthy/idle; this does not reconstruct intermediate UI semantics by itself. |
| Direct MinerU `/tasks/{id}` | MinerU terminal truth for a known task id | Failed residual's MinerU task returned `status=completed`, completed at `2026-05-15T14:16:58.660791+00:00`, no error | The residual failed item is not a MinerU parse failure. |
| DB ParseTask | Durable Luceon task state/stage/progress/message | 24 pressure tasks: 23 `review-pending/review`, 1 `failed/ai` | Final Luceon task state is coherent but intermediate DB state can lag direct MinerU. |
| Material metadata | Durable parsed-artifact and AI status summary | Failed residual has `mineruStatus=completed`, parsed files `6510`, artifact manifest present, AI failure metadata | Confirms MinerU completed and strict AI failure is separate. |
| MinIO parsed outputs | Durable artifact evidence after result-store | Failed residual has `markdownObjectName`, `parsedPrefix`, `artifactManifestObjectName`, parsed files `6510` | Parse artifacts were produced before AI failure. |
| AI job / AI events | AI-phase lifecycle truth | AI provider timed out at `180010ms` against `180000ms`; strict no-skeleton blocked fallback | The one residual is AI-stage and manual-review/retry-policy matter, not parse-progress semantics. |
| `/ops/mineru/active-task` | DB-derived MinerU occupancy diagnostic | Current output: no active/current/queued/takeover; one `historicalAiFailureTasks` row | Good terminal classification. During active work it still uses DB-derived candidates unless `queryApi=true`. |
| `/ops/dependency-health?mineruSubmitProbe=false` | Dependency readiness | Current output: `ok=true`, `blocking=false`, MinerU health OK, Ollama resident chat succeeded in `1792ms` | Current readiness is good; prior timeouts should be treated as probe semantics, not parse state. |
| `/ops/mineru/log-channel-ownership` | Log observability ownership only | Current `summaryState=stale`; selected stderr source stale but has `progressCount=203`, `stageChangeCount=7`, last business signal `2026-05-16 04:13:03`; sidecar `not-observed` | Logs did capture useful business progress during the run, but the channel is stale after idle and not lifecycle authority. |
| `/cms/tasks` list/detail | Operator progress display | Code consumes `deriveMineruProgressLine`, `task.message`, `mineruObservedProgress`, and hides progress bar when stale | Useful, but still does not separate source confidence strongly enough for pressure monitoring. |

## Timeline / Cause Analysis From Task 190

- Around `2026-05-15 20:33 +0800`, pressure run had 1 running and 23 pending; direct MinerU logs/API showed progress on the first large PDF.
- Around `2026-05-15 21:36 +0800`, first large PDF reached review-pending, second large PDF ran; dependency-health no-submit timed out, but direct MinerU/API/logs continued to show progress. This is readiness probe lag under load, not proof of parse failure.
- Around `2026-05-16 00:36 +0800`, 4 review-pending, 1 failed, 1 running, 18 pending; the failed item was already an AI-stage residual after MinerU completion.
- Around `2026-05-16 03:36 +0800`, DB/active-task still had active semantics while direct MinerU showed no processing for the item being judged and logs showed smaller-file progress. This is the clearest "truth-surface split": direct runtime/log evidence and DB-derived status were not synchronized in a way the operator could read confidently.
- At final `2026-05-16 05:53 +0800`, final state was coherent: 23 review-pending and 1 failed/AI; active queues empty.

## Code Path Evidence

### Dependency Health

- `server/upload-server.mjs:483` builds dependency health with independent MinIO, MinerU, and Ollama sections.
- `server/upload-server.mjs:626` checks MinerU `/health` with a 3000ms timeout. This is a runtime health check, not task progress.
- `server/upload-server.mjs:638` only runs the MinerU submit probe when enabled; this run used `mineruSubmitProbe=false`.
- `server/upload-server.mjs:711` performs an Ollama `/api/chat` smoke with `AbortSignal.timeout(DEPENDENCY_HEALTH_OLLAMA_CHAT_TIMEOUT_MS)`.
- `server/upload-server.mjs:779` explicitly describes cold-start timeout as "AI readiness caveat, not a parse/upload blocker"; `server/upload-server.mjs:796` says generic chat timeout also leaves parse/upload readiness separate.
- `server/upload-server.mjs:834` sets `blocking` only from MinIO/MinerU, while `ok` also includes Ollama. This helps avoid blocking parse on AI readiness, but operator-facing monitoring still needs clearer wording when Ollama/probe timing is slow.

### Active Task / Diagnostics

- `server/upload-server.mjs:427` builds `buildMineruActiveTaskSnapshot()` from DB `/tasks` and `/ai-metadata-jobs`.
- `server/upload-server.mjs:447` delegates classification to `classifyMineruActiveTasks()`.
- `server/upload-server.mjs:450` sets `activeTask` to the first DB-derived running MinerU task; `server/upload-server.mjs:451` sets `currentProcessingTask` similarly.
- `server/upload-server.mjs:1271` documents `/ops/mineru/active-task` as DB-derived occupancy, with optional direct MinerU API truth through `?queryApi=true`.
- `server/upload-server.mjs:1326` only performs direct MinerU API checks when `queryApi=true`, and only for running/drift/completed-not-ingested ids.
- `server/lib/ops-mineru-diagnostics.mjs:29` classifies active, drift, completed-but-not-ingested, submit-retryable, historical AI failure, and takeover-required buckets.
- `server/lib/ops-mineru-diagnostics.mjs:15` makes historical terminal AI failures distinct when MinerU is completed and artifacts exist. This is why the final residual is now correctly classified as historical AI failure, not active parse blockage.

### Worker Polling And Expected Lag

- `server/services/mineru/local-adapter.mjs:285` waits/polls MinerU task status and updates progress from callback status payloads.
- `server/services/mineru/local-adapter.mjs:305` tries to parse sidecar/log progress during `processing`; if `progressSemantics.message` exists, it replaces the generic "MinerU 正在解析" message.
- `server/services/mineru/local-adapter.mjs:324` writes `running/mineru-processing` with generic progress `50` plus optional `mineruObservedProgress`.
- `server/services/queue/task-worker.mjs:1417` treats `MineruStillProcessingError` as "keep running and continue observation", not failure. This is correct but can leave the DB active while the direct runtime has already moved ahead until the next poll/result-store transition.
- `server/services/queue/task-worker.mjs:1365` moves successful parse results to `ai-pending` only after result store/artifact handling. That is the expected DB catch-up boundary after MinerU completes.
- `server/services/queue/task-worker.mjs:2433` logs `update.message || Status changed to ${update.state}`. When progress events carry metadata but no `state`, this can create "Status changed to undefined", which was observed in the residual task event timeline.

### MinerU Log Semantics

- `server/lib/ops-mineru-log-parser.mjs:247` attaches UI-safe `progressSemantics.message`.
- `server/lib/ops-mineru-log-parser.mjs:275` derives runtime-progress truth from direct status plus observation; direct completed/failed has precedence before raw log progress.
- `server/lib/ops-mineru-log-parser.mjs:589` returns log-channel ownership diagnostics and explicitly states lifecycle authority boundaries at `server/lib/ops-mineru-log-parser.mjs:610`.
- `server/lib/ops-mineru-log-parser.mjs:1209` attaches stale/missing/unreadable log observation semantics when authoritative log source is not fresh.
- `server/upload-server.mjs:1384` attributes a log snapshot to exactly one live active task, or to one recently completed task within a grace window.
- `server/upload-server.mjs:1428` prevents mutating terminal tasks with completed-window backfill when they already have an observation. This prevents misleading post-terminal rewrites, but it also means global/log truth and task metadata can diverge after terminal completion.

### UI Semantics

- `src/app/utils/taskView.ts:46` formats `mineruObservedProgress` into operator text.
- `src/app/utils/taskView.ts:64` distinguishes direct MinerU processing, local timeout, stale observation, and active raw logs.
- `src/app/utils/taskView.ts:188` returns formatted MinerU text for `stage=mineru-processing`, otherwise falls back to `task.message`.
- `src/app/utils/taskView.ts:198` suppresses in-flight-only stale observations after terminal success and prefers terminal completion lines.
- `src/app/pages/TaskManagementPage.tsx:647` displays `deriveMineruProgressLine(t)` on the task list.
- `src/app/pages/TaskManagementPage.tsx:655` hides the progress bar when log observation is stale, but the row still shows task message and derived line.
- `src/app/pages/TaskDetailPage.tsx:889` displays current log semantics from `mineruObservedProgress`.
- `src/app/pages/TaskDetailPage.tsx:922` uses `obs.activityLevel.startsWith('log-observation-')` to show "MinerU 仍在处理，但日志观测通道滞后/不可用"; this is risky for terminal or post-idle contexts unless guarded by actual task state/direct status.

## Runtime Evidence Collected In This Run

- Direct MinerU health: `healthy`, queued `0`, processing `0`, completed `48`, failed `0`.
- Dependency health no-submit: `ok=true`, `blocking=false`, MinerU `healthOk=true`, Ollama resident-chat-succeeded in `1792ms`, no submit probe executed.
- Active-task: no active/current/queued/completed-not-ingested/drift/submit-retryable/takeover tasks; one historical AI failure `task-1778848110965`.
- Log-channel ownership: `summaryState=stale`; selected stderr source has `progressCount=203`, `stageChangeCount=7`, `lastBusinessSignalTime=2026-05-16 04:13:03`; sidecar `not-observed`.
- Current pressure DB aggregate: 24 tasks total, 23 `review-pending/review`, 1 `failed/ai`.
- Failed residual task `task-1778848110965`: `mineruStatus=completed`, `parsedFilesCount=6510`, parsed artifact manifest present, `aiFailureKind=strict-no-skeleton-fallback-block`, `aiFailureDurationMs=180010`, manual retry eligible.
- Direct MinerU for residual task `3e6a4a27-1066-4ddf-bc7f-2e71cd9b1df1`: `status=completed`, started `2026-05-15T12:55:26.535098+00:00`, completed `2026-05-15T14:16:58.660791+00:00`, no error.
- Residual task events show parse completed and artifacts saved before AI timeout; they also contain one ambiguous `Status changed to undefined` progress event after MinerU completion.

## Expected Async Lag vs Defects

Expected:

- DB task state can lag direct MinerU completion until the worker polls, fetches results, stores artifacts, and transitions to `ai-pending`.
- Logs can become stale after terminal completion or idle because no new MinerU business lines are being written.
- Dependency-health can be slower or time out under active heavy work; it is readiness evidence, not per-task progress truth.
- AI timeout after parse completion is a separate phase failure under strict no-skeleton policy.

Defects / gaps:

- The operator view lacks a single progress truth model with source, observedAt, and confidence. It mixes task state, task message, log observation, dependency-health, and active-task diagnostics.
- `TaskDetailPage` can present stale log observation as "MinerU still processing" based only on `activityLevel`, not sufficiently gated by terminal state/direct MinerU status.
- `/ops/mineru/active-task` uses direct MinerU API only when `queryApi=true`; the default operator/monitoring path is primarily DB-derived and can lag during pressure runs.
- Log-channel ownership reports stale after idle correctly, but the product needs a distinct `idle-stale` / `terminal-stale` semantic rather than a generic stale warning.
- Event logging creates ambiguous timeline rows when transition updates lack `state` and `message`.

## Recommended Follow-Up Tasks

1. **Backend progress snapshot contract.** Add a normalized read-only `progressSnapshot` model for task detail/list and active diagnostics: `phase`, `source`, `sourcePriority`, `observedAt`, `freshness`, `confidence`, `lagKind`, `directMineruStatus`, `dbState`, `logState`, `aiState`, and `operatorMessage`.
2. **Active-task reconciliation hardening.** Make the operator diagnostics path query direct MinerU status for currently active DB candidates by default or expose a clearly named "DB-derived" vs "direct-checked" mode; classify direct-completed/DB-running as `result-ingestion-lag`.
3. **Terminal/idle log semantics.** Change log stale wording so terminal tasks and idle runtime say "日志通道空闲/终态后无新增日志" instead of "MinerU still processing".
4. **UI copy and grouping after backend contract.** Show separate sections: "MinerU API", "Luceon DB sync", "Log observation", "AI phase"; do not flatten them into one status line.
5. **Event-log cleanup.** Avoid writing "Status changed to undefined"; log metadata-only progress updates as "Progress metadata updated" or use explicit event names.
6. **Focused smoke coverage.** Add tests for direct-completed/DB-running lag, terminal stale log observation, idle stale log-channel ownership, dependency-health timeout semantics, and AI failure after MinerU completion.

## Commands Run And Exit Codes

- `git status --short --branch` - exit 0
- `rg -n "\| DevelopmentEngineer \|" TaskAndReport/TASK_TRACKING_LIST.md` - exit 0
- `sed -n` / `nl -ba` reads for required docs, task brief, Task 190 report, Director review, correction decision, and code files - exit 0
- `rg -n "active-task|log-channel|dependency-health|..." server src uat TaskAndReport docs` - exit 2 because `tests` path did not exist; useful matches were still returned from existing paths.
- `git status --short --branch && git rev-parse --short HEAD && git log -1 --oneline` in production workspace - exit 0
- `curl -sS --max-time 10 http://127.0.0.1:8083/health` - exit 0
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=false'` - exit 0
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/active-task` - exit 0
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership` - exit 0
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/diagnostics` - exit 0
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/global-observation` - exit 0
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task?queryApi=true'` - exit 0
- `curl -sS --max-time 15 http://localhost:8081/__proxy/db/tasks | jq ...` - exit 0
- `curl -sS --max-time 15 http://localhost:8081/__proxy/db/tasks/task-1778848110965 | jq ...` - exit 0
- `curl -sS --max-time 15 http://localhost:8081/__proxy/db/ai-metadata-jobs/ai-job-1778854627880-0a6f | jq ...` - exit 0
- `curl -sS --max-time 10 http://127.0.0.1:8083/tasks/3e6a4a27-1066-4ddf-bc7f-2e71cd9b1df1 | jq ...` - exit 0
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/db/task-events?taskId=task-1778848110965' | jq ...` - exit 0
- `date '+%Y-%m-%dT%H:%M:%S%z'` - exit 0

## Skipped Checks And Reasons

- No tests were run. This was a read-only diagnosis task with no code implementation.
- No production restart/rebuild/redeploy/upload/pressure run/retry/reparse/re-AI/repair/reset/submit-probe was run. These were explicitly forbidden.
- No browser UI interaction was run. API, DB, runtime endpoint, code, and task-event evidence were sufficient for root-cause diagnosis, and the task did not require browser screenshots.
- No GitHub sync/push was run. The role-thread instruction says GitHub sync is Director-owned unless explicitly authorized; this task did not authorize DevelopmentEngineer push.

## Risks / Blockers / Residual Debt

- Production workspace is dirty with unrelated local modifications. This report did not alter production workspace.
- Current terminal snapshot is clean/idle, so the report relies on Task 190 timeline plus durable DB/task-event/log evidence for intermediate behavior.
- `ai-metadata-jobs` endpoint did not expose the same nested failure classification fields as the ParseTask metadata; ParseTask metadata and task events carried the usable AI failure details.
- Sidecar running state is currently `not-observed`; this is a residual operational gap for durable live log attribution.
- This diagnosis is not an implementation plan approval, not a pressure PASS, not L3, and not release readiness.

## Director Review Required

Yes. Director should review this causal map and decide which follow-up task(s) to issue first. Recommended first task is backend progress snapshot contract and active-task reconciliation semantics before UI wording changes.

