# DevelopmentEngineer Report: P1 MinerU-Only Recovery And Submit-Path Verification

- Task ID: `TASK-20260515-113628-P1-MinerU-Only-Recovery-And-Submit-Path-Verification`
- Based on Director task brief: `TaskAndReport/2026-05-15T11-36-28+0800_P1-MinerU-Only-Recovery-And-Submit-Path-Verification_TASK.md`
- Based on user decision: `TaskAndReport/2026-05-15T11-28-06+0800_P1-MinerU-Submit-Path-Recovery-Authorization_DECISION.md`
- Based on diagnosis: `TaskAndReport/2026-05-15T11-12-51+0800_P1-Production-MinerU-Submit-Path-500-Read-Only-Diagnosis-And-Recovery-Plan_REPORT.md`
- Report time: 2026-05-15T11:44:00+0800
- Role: `DevelopmentEngineer`
- Development branch / HEAD: `main` / `724de0b`
- Production path / HEAD: `/Users/concm/prod_workspace/Luceon2026` / `1716add`

## Outcome

`RECOVERED_SUBMIT_PATH`

PDF/non-Markdown intake is no longer blocked by the MinerU admission circuit at the time of this report:

- The single authorized submit-probe returned HTTP `202`.
- Returned MinerU probe task ID: `f7e76bf6-579f-49d0-a15d-46b7b854762f`.
- Admission circuit changed from `open=true` to `open=false`.
- Post-probe dependency health without submit probe returned `ok=true`, `blocking=false`.
- The synthetic MinerU probe task later reported `status="completed"` with `error=null`.

This is not a pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live claim.

## Pre-Recovery Safety Check

Safety check time: `2026-05-15T11:39:14+0800`.

Active-task diagnostics before mutation:

- `activeTask=null`
- `currentProcessingTask=null`
- `queuedTasks=[]`
- `completedButNotIngestedTasks=[]`
- `driftTasks=[]`
- `submitRetryableTasks=[]`
- `takeoverRequiredTasks=[]`
- Historical AI failure tasks remained visible: `6`, all `failed/ai`.

Admission-circuit state before mutation:

- `open=true`
- `state="open"`
- `reason="mineru-submit-probe-HTTP 500"`
- Last failed submit probe:
  - `status=500`
  - `durationMs=196`
  - `taskId=null`
  - `error="HTTP 500: Internal Server Error"`
  - `observedAt="2026-05-15T03:08:28.443Z"`

Direct MinerU `/health` before mutation:

- `status="healthy"`
- `queued_tasks=0`
- `processing_tasks=0`
- `completed_tasks=0`
- `failed_tasks=0`
- `max_concurrent_requests=1`

Process/tmux/listener state before mutation:

- `tmux ls`: `mineru_api: 1 windows (created Fri May 15 08:31:57 2026)`
- `lsof -nP -iTCP:8083 -sTCP:LISTEN`: PID `1009` listening on `*:8083`.
- `ps -ef` showed the host MinerU API under `tmux new-session -d -s mineru_api ... conda run -n mineru mineru-api --port 8083 --host 0.0.0.0`.
- No competing 8083 listener was observed.
- Ownership was sufficiently clear for a MinerU-only restart.

Log state before mutation:

- `/Users/concm/ops/logs/mineru-api.log` mtime: `2026-05-15T08:23:48+0800`.
- `/Users/concm/ops/logs/mineru-api.err.log` mtime: `2026-05-15T07:47:05+0800`.
- This matched Task 171's stale-log-channel diagnosis before restart.

## Recovery Actions Performed

Authorized scope: restart/relaunch only the host MinerU API session/process bound to port `8083`.

Commands:

```bash
tmux kill-session -t mineru_api
```

- Exit: `0`.
- Timestamp: `2026-05-15T11:39:52+0800`.
- Scope: killed only the `mineru_api` tmux session.

```bash
lsof -nP -iTCP:8083 -sTCP:LISTEN
```

- Exit: non-zero after kill, treated as expected absence.
- Evidence: `listener_after_kill=absent`.

```bash
tmux new-session -d -s mineru_api 'cd /Users/concm/prod_workspace/Luceon2026 && bash ops/start-mineru-api.sh'
```

- Exit: `0`.
- Timestamp: `2026-05-15T11:39:55+0800`.
- Scope: relaunched only host MinerU API with the existing project ops script.

Post-start direct checks:

- `tmux ls`: `mineru_api: 1 windows (created Fri May 15 11:39:55 2026)`.
- `lsof -nP -iTCP:8083 -sTCP:LISTEN`: PID `7092` listening on `*:8083`.
- Direct `/health`: `status="healthy"`, zero queued/processing/completed/failed tasks immediately after startup.

No Docker, upload-server, frontend, DB, MinIO, Ollama, supervisor, sidecar, model, secret, config, sample, repository, or production code mutation was performed.

## Post-Recovery Verification

Upload health after MinerU restart:

- `GET /__proxy/upload/health`: `{"ok":true,"service":"upload-server"}`.

Active-task diagnostics after MinerU restart and before probe:

- `activeTask=null`
- `currentProcessingTask=null`
- `queuedTasks=[]`
- `completedButNotIngestedTasks=[]`
- `driftTasks=[]`
- `submitRetryableTasks=[]`
- `takeoverRequiredTasks=[]`

Log-channel state after restart:

- `GET /__proxy/upload/ops/mineru/log-channel-ownership` returned `summaryState="valid-business-progress"`.
- Selected source: `MINERU_ERR_LOG_PATH:mineru-api.err.log`.
- Log mtimes after restart:
  - `mineru-api.log`: `2026-05-15T11:40:03+0800`
  - `mineru-api.err.log`: `2026-05-15T11:39:57+0800`
- Logs showed:
  - `Start MinerU FastAPI Service: http://0.0.0.0:8083`
  - `Started server process [7092]`
  - `Uvicorn running on http://0.0.0.0:8083`

Exactly one authorized submit-probe:

```bash
curl -sS --max-time 30 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
```

- Executed once at `2026-05-15T11:40:23+0800`.
- Command completed successfully and returned JSON.
- MinerU submit-probe result:
  - `enabled=true`
  - `ok=true`
  - `status=202`
  - `durationMs=25`
  - `taskId="f7e76bf6-579f-49d0-a15d-46b7b854762f"`
  - `error=null`
- Dependency health result:
  - `ok=true`
  - `blocking=false`
  - MinIO OK
  - MinerU OK
  - Ollama OK, `readinessState="resident-chat-succeeded"`

Admission-circuit state after the one authorized probe:

- `open=false`
- `state="closed"`
- `reason=null`
- `message=null`
- `closedAt="2026-05-15T03:40:26.616Z"`
- `lastSuccessfulSubmitAt="2026-05-15T03:40:26.616Z"`
- `closeCriteria`:
  - `submitProbeOk=true`
  - `cooldownElapsed=true`
  - `activeTaskClean=true`
  - `dependencyBlockingClear=true`

Direct MinerU `/health` immediately after probe:

- `status="healthy"`
- `queued_tasks=0`
- `processing_tasks=1`
- `completed_tasks=0`
- `failed_tasks=0`

Interpretation: `processing_tasks=1` was the authorized synthetic probe task itself, not a user upload or Luceon DB task.

Follow-up read-only observation at `2026-05-15T11:40:53+0800`:

- Direct MinerU `/health`:
  - `status="healthy"`
  - `queued_tasks=0`
  - `processing_tasks=0`
  - `completed_tasks=1`
  - `failed_tasks=0`
- `GET /tasks/f7e76bf6-579f-49d0-a15d-46b7b854762f`:
  - `status="completed"`
  - `backend="pipeline"`
  - `file_names=["luceon-health-probe"]`
  - `completed_at="2026-05-15T03:40:32.656804+00:00"`
  - `error=null`
- Upload active-task diagnostics remained clean.

Final dependency health without submit probe:

- `ok=true`
- `blocking=false`
- MinerU `healthOk=true`
- `submitProbe.enabled=false`
- Admission circuit `state="closed"`
- Ollama `readinessState="resident-chat-succeeded"`, `chatOk=true`, `modelResident=true`.

## Files Changed

- Added this report:
  - `TaskAndReport/2026-05-15T11-36-28+0800_P1-MinerU-Only-Recovery-And-Submit-Path-Verification_REPORT.md`
- Updated task ledger row 173:
  - `TaskAndReport/TASK_TRACKING_LIST.md`

## Commands Run And Exit Codes

Development workspace:

- `git status --short --branch` -> exit 0.
- `rg -n "\\| [0-9]+ \\| .*\\| (下达待执行|执行中|退回待修正|修正中) \\| DevelopmentEngineer \\|" TaskAndReport/TASK_TRACKING_LIST.md` -> exit 0.
- Required-reading `sed` commands for task brief, role contract, TaskAndReport README, related decision/reports/reviews, and project documents -> exit 0 except one attempted nonexistent review filename -> exit 1, then corrected by reading `TaskAndReport/2026-05-15T11-28-06+0800_P1-Production-MinerU-Submit-Path-500-Diagnosis_DIRECTOR_REVIEW.md`.

Production workspace / runtime:

- `sed -n '1,220p' ops/start-mineru-api.sh` -> exit 0.
- Pre-recovery safety bundle: active-task diagnostics, admission-circuit, direct MinerU health, `tmux ls`, `lsof`, `ps` -> exit 0.
- Pre-recovery log mtime/tail check -> exit 0.
- `tmux kill-session -t mineru_api` -> exit 0.
- `lsof -nP -iTCP:8083 -sTCP:LISTEN` after kill -> non-zero expected; listener absent.
- `tmux new-session -d -s mineru_api 'cd /Users/concm/prod_workspace/Luceon2026 && bash ops/start-mineru-api.sh'` -> exit 0.
- Post-start `tmux ls`, `lsof`, direct MinerU `/health` -> exit 0.
- Upload health, active-task diagnostics, log-channel ownership -> exit 0.
- Exactly one authorized dependency-health submit-probe with `mineruSubmitProbe=true` -> command completed successfully; response body `ok=true`, `blocking=false`, submit-probe `status=202`.
- Post-probe admission-circuit, active-task diagnostics, direct MinerU `/health` -> exit 0.
- Delayed read-only direct MinerU `/health`, admission-circuit, active-task diagnostics -> exit 0.
- Read-only `GET /tasks/f7e76bf6-579f-49d0-a15d-46b7b854762f` -> exit 0.
- Final dependency-health without submit probe -> exit 0.
- Final `tmux ls`, `lsof`, `ps` -> exit 0.

## Skipped Checks And Reasons

- Did not run a second submit-probe: Task 173 authorizes exactly one.
- Did not upload PDF/Markdown or run pressure/batch/soak/fresh serial validation: forbidden by Task 173.
- Did not manually close/reset the admission circuit: forbidden; circuit closed through the authorized successful submit-probe.
- Did not restart Docker, upload-server, frontend, DB, MinIO, Ollama, supervisor, or sidecar: forbidden by Task 173.
- Did not deploy, rebuild, rollback, fast-forward production code, pull production code, or mutate production repository files: forbidden by Task 173.
- Did not cleanup/cancel/repair/retry/reparse/re-AI/takeover/requeue historical tasks: forbidden by Task 173.
- Did not mutate DB/MinIO/Docker volume/data, settings, secrets, config, models, or sample-library files: forbidden by Task 173.
- Did not run user-file validation after recovery: not authorized by Task 173.

## Risks / Blockers / Residual Debt

- Submit-path recovery is proven only by the authorized synthetic dependency-health probe, not by a user PDF upload.
- The circuit is closed and intake is not blocked by admission circuit, but broader production readiness remains unclaimed.
- The runtime ownership helper still needs code/tooling hardening so "read-only" status collection cannot accidentally run submit-probe without explicit authorization.
- MinerU logging improved after restart, but sidecar still reported `runningState="not-observed"`; observability ownership remains a separate follow-up debt.
- Historical `failed/ai` tasks remain visible and were not repaired, by task boundary.

## Recommended Next Actor

`Director`

Recommended Director action:

- Review and accept this recovery report if evidence is sufficient.
- If further confidence is desired, dispatch a separate read-only TestAcceptanceEngineer follow-up. Do not authorize upload validation unless the user explicitly approves that separate scope.
- Dispatch a separate DevelopmentEngineer hardening task for:
  - `ops/runtime-ownership-status.sh` no-submit/read-only mode;
  - clearer submit-probe/admission-circuit logging;
  - log-channel/sidecar observability follow-up.

## Forbidden Operations Confirmation

No forbidden operation was performed.

Specifically, I did not run more than one submit-probe, did not upload files, did not run pressure/batch/soak/fresh serial validation, did not restart broad stack services, did not mutate Docker/DB/MinIO/Ollama/supervisor/sidecar/model/secret/config/sample state, did not deploy/rebuild/rollback/pull production code, did not manually close/reset the circuit, did not cleanup/cancel/repair/retry/reparse/re-AI/takeover/requeue tasks, did not mutate data/volumes, did not weaken skeleton fallback, and did not claim pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Need For Director Review / User Decision

Director review is required.

No additional user decision is needed for the actions already completed, because Task 172 recorded user approval for Option A. Any upload validation, pressure test, broad recovery, code deployment, or release-readiness decision would require a separate Director task and, where appropriate, explicit user authorization.
