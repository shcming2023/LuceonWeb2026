# Architect Report: P1 MinerU Progress Observability Ownership Review

- Report time: 2026-05-14T05:58:00+0800
- Role: Architect
- Based on Director task brief: `TaskAndReport/2026-05-14T05-42-35+0800_P1-MinerU-Progress-Observability-Ownership-Review_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production HEAD observed: `159d80e Accept MinerU log observation hardening`
- Result: `OBSERVABILITY_OWNERSHIP_GAP_CONFIRMED_READ_ONLY`

## Executive Conclusion

Task 104's diagnostic-only progress was not primarily a UI defect and should not be treated as a MinerU parsing failure. The current architecture already separates two facts:

1. MinerU lifecycle truth comes from the MinerU API and Luceon task/material state.
2. Operator-visible page/batch/business progress is expected to come from structured MinerU log observation, then be persisted as `metadata.mineruObservedProgress` and rendered by the task UI.

Current production read-only evidence shows the expected host log files are present but empty, the container-visible mounted files are also empty, `/ops/mineru/global-observation` is null, and no `mineru-log-observer` sidecar process is running. Therefore the residual limitation is primarily a sidecar/log-source ownership gap, with a secondary expected-behavior factor for small/fast PDFs. The code hardening from Task 101 correctly prevents false failure, but it does not and should not fabricate page/batch progress when no attributable business log exists.

Broader serial validation or pressure testing should wait until Director dispatches a scoped observability ownership task. Otherwise long-running runs may be operationally ambiguous: false failure is improved, but a slow job and an unobserved job can still look too similar to operators.

## Current MinerU Progress Signal Map

| Layer | Current source | Current role | UI impact |
| --- | --- | --- | --- |
| MinerU lifecycle | MinerU FastAPI `/health` and `/tasks/{mineruTaskId}` | Authoritative for queued/processing/completed/failed lifecycle and submit availability | Drives running/completed/failure adjudication through worker code |
| Luceon task state | DB task/material/AI job records | Authoritative Luceon workflow state | Task list/detail status, review state, parsed artifact and AI state |
| Business progress | MinerU stdout/stderr logs parsed by `server/lib/ops-mineru-log-parser.mjs` | Intended source for phase/page/batch/window progress | Stored as `metadata.mineruObservedProgress`, rendered through `taskView.ts` and task detail diagnostics |
| In-process polling | `server/services/mineru/local-adapter.mjs` calls `parseLatestMineruProgress()` while MinerU is processing | Adds observation metadata during worker polling | Can replace generic `MinerU 正在解析` with structured progress when logs exist |
| Host sidecar | `ops/mineru-log-observer.mjs` posts snapshots to `/ops/mineru-log-observation` | Intended long-lived observer/backfill path independent of one worker poll | Updates task metadata when exactly one active task, or stores global observation |
| Attribution endpoint | `server/upload-server.mjs` `/ops/mineru/active-task` and `/ops/mineru-log-observation` | Maps snapshots to active/completed tasks and avoids stale/multi-task misattribution | Prevents old/global log noise from becoming task progress |
| UI semantics | `src/app/utils/taskView.ts`, `src/app/pages/TaskDetailPage.tsx` | Renders only persisted progress semantics or truthful diagnostic messages | Shows page/batch progress when present; otherwise shows diagnostic-only completion |

## Evidence From Prior Tasks

### Task 100

Task 100 uploaded three small serial samples. All eventually reached `review-pending`, but every sample exposed the same P1 defect: Luceon transiently marked MinerU work failed because `mineruObservedProgress.activityLevel=log-observation-unreadable` while MinerU API still reported `processing`. Director accepted the small serial boundary but required a P1 observability/adjudication follow-up before broader validation.

### Task 101

Task 101 changed `server/services/mineru/local-adapter.mjs` and focused smoke tests so unreadable/stale/no-business log observation during MinerU `queued`/`pending`/`processing`/`running` becomes warning metadata:

- `metadata.mineruLogObservationWarning.kind=mineru-log-observation-diagnostic-only`
- the task remains `running`
- explicit MinerU API `failed` or confirmed failure signals remain terminal

This fixed false-failure adjudication at code/test level. It did not claim production observability richness.

### Task 104

Task 104 performed exactly one controlled upload after deployment at production HEAD `159d80e`.

Accepted evidence:

- MinerU API was processing.
- Task metadata showed `mineruObservedProgress.activityLevel=log-observation-unreadable`.
- `mineruLogObservationWarning.kind=mineru-log-observation-diagnostic-only`.
- Task reached `review-pending`.
- Material reached `reviewing`.
- Parsed files count was `21`.
- UI showed `MinerU 已完成，但本次未捕获可归因业务进度日志`, not an operator-visible false failure.

Residual limitation:

- The task still had no attributable page/batch/business progress.
- This is honest diagnostic behavior, not progress-rich observability.

## Current Read-Only Runtime Evidence

Production services were healthy:

- `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` were up and healthy.
- Upload health returned `{"ok":true,"service":"upload-server"}`.
- Dependency health returned `ok=true`, `blocking=false`.
- MinerU `/health` returned `status=healthy`, `queued_tasks=0`, `processing_tasks=0`, `completed_tasks=45`, `failed_tasks=0`.
- Admission circuit was closed and clean.
- Active-task surface had no active/current/queued/drift/takeover work.
- `/ops/mineru/global-observation` returned `{"observation":null}`.

Log ownership evidence:

- Host `/Users/concm/ops/logs/mineru-api.log` existed but was `0` bytes.
- Host `/Users/concm/ops/logs/mineru-api.err.log` existed but was `0` bytes.
- Container `/host/mineru-logs/mineru-api.log` existed but was `0` bytes.
- Container `/host/mineru-logs/mineru-api.err.log` existed but was `0` bytes.
- Upload-server environment points at `/host/mineru-logs/mineru-api.log` and `/host/mineru-logs/mineru-api.err.log`.
- `pgrep -fl mineru-log-observer` found no running sidecar.
- MinerU itself is running as a conda `mineru-api --port 8083 --host 0.0.0.0` process.

This means Luceon currently has a live MinerU API but no confirmed live business-log transport into the files that the parser and container mount expect.

## Root-Cause Classification

Primary classification: sidecar/log-source ownership issue.

The expected business-progress source is the host MinerU log file observed by parser/sidecar. Current production evidence shows that source is empty from both host and container views, and the sidecar observer is not running. In that condition, `log-observation-unreadable` or diagnostic-only completion is expected.

Secondary classification: expected behavior for small/fast PDFs.

For a small/fast PDF, MinerU may complete before a parser poll or sidecar attribution window captures a business line. The code has an explicit `fast-complete-no-business-signal` diagnostic path for this boundary. This remains acceptable only if the system does not claim fabricated progress.

Not primary: UI/product semantics.

The UI currently renders the correct product truth: no false failure, no fabricated page/batch progress, and a diagnostic-only message when progress is missing. Product clarity can be improved later, but it is not the root cause.

Not primary: code parser capability.

`server/lib/ops-mineru-log-parser.mjs` supports pipeline/hybrid progress, windows, document shape, engine config, attribution, stale/missing/unreadable states, and UI-safe `progressSemantics`. Tests assert page/batch semantics when suitable log lines are present and assert no fabricated progress on fast-complete diagnostics.

Not enough evidence to call MinerU API capability the blocker.

The MinerU API is authoritative for lifecycle but does not currently provide the rich page/batch progress Luceon wants through the read-only surfaces inspected here. Rich progress therefore remains log-derived unless a future MinerU API capability is proven and integrated.

## Product Boundary

Current behavior is acceptable for the narrow Task 104 boundary: a small/fast task completed safely, avoided false failure, and gave an honest diagnostic completion message.

Current behavior is not sufficient as a broader validation or pressure-test boundary. For long-running PDFs, operators need to distinguish:

- MinerU is alive but waiting;
- MinerU is actively progressing through pages/batches;
- Luceon has lost its observation channel;
- MinerU is truly stuck or failed.

Without verified log-source ownership or an explicit product decision to accept diagnostic-only progress, pressure results would be harder to interpret and easier to overclaim.

## Recommended Next Task

Recommended assignee: `DevelopmentEngineer` first, then `TestAcceptanceEngineer` after Director review.

### DevelopmentEngineer Task

Scope:

- Read-only first, then scoped implementation if needed, limited to MinerU observability ownership and diagnostics.
- Inspect and, if assigned, harden the startup/runtime contract among:
  - `ops/start-mineru-api.sh`
  - `ops/mineru-log-observer.mjs`
  - `server/lib/ops-mineru-log-parser.mjs`
  - `server/upload-server.mjs` observability endpoints
  - deployment docs/runbook areas that define sidecar/log ownership
- Add or adjust non-destructive diagnostics that report:
  - host/container log paths expected;
  - file exists/readable/size/mtime;
  - observer process expected/running status if available;
  - last global observation;
  - active-task attribution mode;
  - whether missing progress is due to no log source, no business signal, stale source, or fast-complete diagnostic.

Forbidden operations:

- No PDF upload.
- No pressure/batch/soak/long-run validation.
- No production restart/rebuild/rollback.
- No DB/MinIO/Docker volume mutation.
- No log deletion/truncation/rotation.
- No model/config/secret change unless Director explicitly creates a separate ops task.
- No release/readiness claims.

Acceptance criteria:

- Report identifies a single owner for starting and supervising MinerU API logging and sidecar observation.
- Existing parser tests still pass.
- A focused smoke proves diagnostic endpoint/metadata distinguishes:
  - log file missing;
  - log file present but empty;
  - log file stale;
  - valid business progress line;
  - fast completed task with no business signal.
- No false terminal failure is reintroduced for in-flight MinerU API states.
- Operator-facing semantics still do not expose host paths and do not fabricate page/batch progress.

### Follow-Up TestAcceptanceEngineer Task

After Director accepts the ownership/diagnostic change or runbook, authorize one controlled observability validation only if preflight proves the log channel is live. Use exactly one sample chosen to be long enough to emit progress but not a pressure test. Stop on dependency blocking, admission open, active-task drift, or any forbidden mutation need.

Acceptance criteria for that validation:

- Before upload, host and container log files are non-empty or the observer contract explains how they will become non-empty.
- Sidecar or in-process parser records at least one attributable business-progress signal for a running task, or the report proves the file completed too fast and classifies that boundary explicitly.
- UI shows page/batch/phase semantics when a business signal exists.
- If no business signal exists, report must not call progress observability fixed.

## Risks Of Going Straight To Pressure Now

- A long-running job with empty logs may look like diagnostic-only processing until much later, making stall vs progress ambiguous.
- Pressure evidence would mix throughput, queueing, false-failure adjudication, log transport, and UI semantics into one hard-to-review result.
- Operators would still lack verified page/batch progress for unattended monitoring.
- Failure triage would be weaker because active-task state could be clean while the observation channel is absent.
- Any pressure PASS claim would be overbroad under the current evidence.

## Commands Run

Development workspace:

- `git status --short --branch` -> exit 0
- `sed -n '1,260p' TaskAndReport/2026-05-14T05-42-35+0800_P1-MinerU-Progress-Observability-Ownership-Review_TASK.md` -> exit 0
- `rg -n "TASK-20260514-054235|MinerU Progress Observability" TaskAndReport/TASK_TRACKING_LIST.md` -> exit 0
- `rg -n "mineruObservedProgress|mineruLogObservationWarning|log-observation|progressSemantics|active-task|admission-circuit|MinerU 已完成|暂无可归因" server src ops` -> exit 0
- `rg --files | rg 'mineru|taskView|TaskManagement|TaskDetail|upload-server|local-adapter|ops-mineru|admission'` -> exit 0
- Read-only `sed` inspections of required role/project docs, Task 100/101/104 reports and reviews, user decision record, MinerU parser, local adapter, upload-server observability routes, sidecar observer, task UI semantics, and focused tests -> exit 0

Production workspace:

- `git status --short --branch` -> exit 0
- `git log -1 --oneline` -> exit 0
- `docker compose ps` -> exit 0
- `curl -fsS http://localhost:8081/__proxy/upload/health` -> exit 0
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task` -> exit 0
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit` -> exit 0
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/global-observation` -> exit 0
- `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-health` -> exit 0
- `ls -l /Users/concm/ops/logs` -> exit 0
- `pgrep -fl mineru-log-observer` -> exit 1, no matching process found
- `pgrep -fl start-mineru-api` -> exit 1, no matching process found
- `pgrep -fl mineru` -> exit 0, MinerU conda API process present
- `docker compose exec -T upload-server ls -l /host/mineru-logs` -> exit 0
- `docker compose exec -T upload-server printenv MINERU_LOG_PATH` -> exit 0
- `docker compose exec -T upload-server printenv MINERU_ERR_LOG_PATH` -> exit 0
- `curl -fsS http://localhost:8083/health` -> exit 0
- `docker logs --tail 120 cms-upload-server` -> exit 0

## Skipped Checks

- No upload was performed because the task explicitly forbids uploads.
- No pressure, batch, soak, or long-run test was performed because the task explicitly forbids them.
- No production restart/rebuild/rollback was performed.
- No DB/MinIO/Docker volume/data mutation was performed.
- No log cleanup, truncation, repair, reparse, retry, or re-AI operation was performed.
- No source code, PRD truth, role contract, release document, environment, secret, model, or Docker Compose file was changed.
- No GitHub fetch, pull, push, or sync was performed.
- No production readiness, release readiness, L3, pressure PASS, or go-live claim is made.

## Recommended Next Actor

Director.

Director should review this report and, if accepted, dispatch a scoped DevelopmentEngineer observability ownership/diagnostic task before any broader validation or pressure work.
