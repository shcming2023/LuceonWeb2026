# DevelopmentEngineer Report: P0 MinerU Only Runtime Relaunch And Read-Only Verification

- Report time: 2026-05-15T20:16:22+0800
- Based on Director task brief: `TaskAndReport/2026-05-15T20-12-31+0800_P0-MinerU-Only-Runtime-Relaunch-And-Read-Only-Verification_TASK.md`
- Based on user authorization: Task 185 Option A, recorded in `TaskAndReport/2026-05-15T19-40-38+0800_P0-MinerU-Runtime-Recovery-Authorization_DECISION.md`
- Execution role: DevelopmentEngineer
- Scope: scoped MinerU-only runtime relaunch plus read-only verification

## Branch / HEAD

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
  - `git status --short --branch`: `## main...origin/main`
  - HEAD: `c3033b0 Authorize scoped MinerU relaunch task`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
  - `git status --short --branch`: `## main...origin/main`
  - HEAD: `1716add Dispatch dependency health production validation`
  - Dirty files observed before relaunch: `.gitignore`, `docker-compose.override.yml`, `docs/codex/TEST_MATRIX.md`, `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`, `ops/runtime-ownership-status.sh`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, `src/app/pages/SourceMaterialsPage.tsx`
  - No production source/config files were edited by this task.

## Files Changed

- `TaskAndReport/2026-05-15T20-12-31+0800_P0-MinerU-Only-Runtime-Relaunch-And-Read-Only-Verification_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Implementation / Runtime Action Summary

Preflight met the task brief relaunch conditions:

- no listener on TCP `8083`;
- no visible tmux server;
- `tmux has-session -t luceon-mineru` exited `1`;
- `tmux has-session -t mineru_api` exited `1`;
- `launchctl print gui/501/com.office.mineru` showed `state = not running`;
- production path existed;
- `ops/start-mineru-api.sh` existed;
- direct `http://127.0.0.1:8083/health` failed with connection refused;
- dependency-health without submit-probe reported `mineru.ok=false`, `blocking=true`, `error=connect ECONNREFUSED`.

I then ran the single authorized relaunch command:

```bash
tmux new-session -d -s luceon-mineru "cd '/Users/concm/prod_workspace/Luceon2026' && bash ops/start-mineru-api.sh"
```

The command returned exit code `0`.

Post-relaunch evidence:

- `tmux list-sessions`: `luceon-mineru: 1 windows`
- `lsof -nP -iTCP:8083 -sTCP:LISTEN`: `python3.1 ... TCP *:8083 (LISTEN)`
- direct MinerU health returned:

```json
{"status":"healthy","version":"3.1.0","protocol_version":1,"queued_tasks":0,"processing_tasks":0,"completed_tasks":0,"failed_tasks":0,"max_concurrent_requests":1,"processing_window_size":64,"task_retention_seconds":86400,"task_cleanup_interval_seconds":300}
```

- dependency-health without submit-probe returned `ok=true`, `blocking=false`, `mineru.ok=true`, `mineru.healthOk=true`, `submitProbe.enabled=false`.
- log-channel ownership changed from stale to `valid-business-progress` on `mineru-api.err.log`; selected source mtime `2026-05-15T12:15:42.508Z`, last business signal `2026-05-15 20:15:42`.
- active-task diagnostics returned no active task, no queued tasks, no takeover-required tasks, and 18 `submitRetryableTasks`.
- admission circuit remained `closed`; no submit-probe was run.

## Pressure Task State Observation

This task did not manually retry, reparse, re-AI, repair, reset, cancel, or mutate any task.

Current read-only task snapshot after relaunch:

| State | Stage | Count |
| --- | --- | ---: |
| `review-pending` | `review` | 5 |
| `failed` | `submit-failed-retryable` | 18 |
| `failed` | `mineru-processing` | 1 |

The earlier 6 `pending/upload` pressure tasks had already drifted to `failed/submit-failed-retryable` with timestamps around 2026-05-15T11:36:58Z to 2026-05-15T11:41:58Z, before this relaunch at 20:15 local time. The original large MinerU task `task-1778821666605` now reports `failed/mineru-processing` with message `[failed 已确认] MinerU 任务记录已丢失 (404)，需人工审计`, updated at 2026-05-15T12:15:50.790Z, shortly after the relaunch. This appears to be existing worker/diagnostic adjudication after MinerU became reachable; I did not issue a retry, reparse, repair, reset, or task-state write command.

## Commands Run And Exit Codes

Development workspace:

- `git status --short --branch` — exit 0
- `rg -n "\\| DevelopmentEngineer \\|" TaskAndReport/TASK_TRACKING_LIST.md` — exit 0
- `sed -n ... TaskAndReport/2026-05-15T20-12-31+0800_P0-MinerU-Only-Runtime-Relaunch-And-Read-Only-Verification_TASK.md` — exit 0
- Required reading `sed -n ...` commands for role/registry/runtime ownership and prior diagnosis/review/decision records — exit 0
- `git status --short --branch && git rev-parse --short HEAD && git log -1 --oneline` — exit 0

Production preflight:

- `git status --short --branch && git rev-parse --short HEAD && git log -1 --oneline` — exit 0
- `lsof -nP -iTCP:8083 -sTCP:LISTEN || true` — command exit 0; no listener returned
- `tmux list-sessions || true` — command exit 0; output `no server running on /private/tmp/tmux-501/default`
- `tmux has-session -t luceon-mineru; echo luceon-mineru-exit:$?` — exit marker `1`
- `tmux has-session -t mineru_api; echo mineru_api-exit:$?` — exit marker `1`
- `launchctl print gui/$(id -u)/com.office.mineru` — exit 0; `state = not running`
- `pgrep -af 'mineru-api|mineru|uvicorn' || true` — command exit 0; only diagnostic commands matched
- `ps -ef | rg -i 'mineru-api|uvicorn|mineru' || true` — command exit 0; only diagnostic commands matched
- `test -d /Users/concm/prod_workspace/Luceon2026; echo prod-dir-exit:$?` — exit marker `0`
- `test -f ops/start-mineru-api.sh; echo start-script-exit:$?` — exit marker `0`
- `curl -sS --max-time 10 http://127.0.0.1:8083/health || true` — command exit 0 wrapper; curl reported connection refused
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=false' || true` — command exit 0; MinerU blocking before relaunch

Authorized relaunch:

- `tmux new-session -d -s luceon-mineru "cd '/Users/concm/prod_workspace/Luceon2026' && bash ops/start-mineru-api.sh"; echo relaunch-exit:$?` — exit marker `0`

Post-relaunch verification:

- `tmux list-sessions || true` — command exit 0; `luceon-mineru` present
- `lsof -nP -iTCP:8083 -sTCP:LISTEN || true` — command exit 0; `python3.1` listening on `*:8083`
- `curl -sS --max-time 10 http://127.0.0.1:8083/health || true` — command exit 0; health JSON returned
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=false' || true` — command exit 0; `ok=true`, `blocking=false`, submit-probe disabled
- `curl -sS --max-time 20 http://localhost:8081/__proxy/upload/ops/mineru/active-task || true` — command exit 0
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit || true` — command exit 0
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership || true` — command exit 0
- `curl -sS --max-time 20 http://localhost:8081/__proxy/db/tasks > /tmp/luceon-task187-tasks.json` — exit 0
- `jq ... /tmp/luceon-task187-tasks.json` — exit 0
- `docker compose logs --since '2026-05-15T20:15:00+08:00' ... upload-server | rg ... || true` — command exit 0; read-only log inspection
- `curl -sS --max-time 20 'http://localhost:8081/__proxy/db/task-events?taskId=task-1778821666605' || true` — command exit 0; read-only event inspection

## Skipped Checks And Reasons

- MinerU submit-probe: skipped because Task 187 forbids submit-probe.
- Upload/pressure run: skipped because Task 187 forbids upload/pressure.
- Retry/reparse/re-AI/cancel/repair/reset/task mutation: skipped because Task 187 forbids task mutation.
- DB/MinIO/Docker cleanup: skipped because Task 187 forbids cleanup and data mutation.
- Docker up/down/down-v/prune/rebuild/redeploy: skipped because Task 187 forbids broad Docker/service mutation.
- LaunchAgent mutation: skipped because Task 187 forbids `launchctl load/bootstrap/kickstart/bootout`.

## Evidence

- Canonical owner now present: `luceon-mineru: 1 windows`.
- MinerU listener now present: `python3.1 ... TCP *:8083 (LISTEN)`.
- Direct MinerU health is healthy and reports zero queued/processing/completed/failed tasks in the restored in-memory MinerU runtime.
- Dependency health without submit-probe is `ok=true`, `blocking=false`; `submitProbe.enabled=false`.
- Log-channel ownership is no longer stale and reports `valid-business-progress`.
- No manual submit-probe, upload, retry/reparse/re-AI, task repair, DB/MinIO cleanup, Docker cleanup, or broad service restart was run.

## Risks / Blockers / Residual Debt

- The 24-PDF pressure task state still needs separate Director review. After current observation it is 5 `review-pending` and 19 `failed`; this task did not authorize reconciliation.
- `task-1778821666605` now appears unrecoverable from the restored MinerU in-memory task store (`MinerU task record lost / 404`), so any next recovery would require explicit task-state reconciliation or reparse/retry authorization.
- The admission circuit is `closed` and dependency-health is non-blocking without submit-probe, but true submit-path readiness remains unverified because submit-probe was not authorized.
- Restoring MinerU as a tmux session does not fix the host LaunchAgent mismatch. `com.office.mineru` still points to `/Users/concm/ops/bin/start-mineru-all.sh` and was not mutated.
- Production workspace remains dirty with pre-existing unrelated changes.

## Review Need

Director review is required.

Recommended next decision:

1. Decide whether to authorize exactly one MinerU submit-probe now that direct health is restored.
2. Separately decide whether to reconcile or leave closed the 19 failed pressure tasks.
3. Separately decide whether to align long-term runtime ownership between repo-documented `luceon-mineru` and host LaunchAgent `start-mineru-all.sh` / `mineru_api`.

