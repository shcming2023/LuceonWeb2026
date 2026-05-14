# DevelopmentEngineer Report: P1 MinerU Sidecar Attach Only Recovery

- Task ID: `TASK-20260514-091558-P1-MinerU-Sidecar-Attach-Only-Recovery`
- Report time: 2026-05-14T09:30:00+0800
- Role: DevelopmentEngineer
- Based on Director task brief: `TaskAndReport/2026-05-14T09-15-58+0800_P1-MinerU-Sidecar-Attach-Only-Recovery_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`

## Result

`luceon-sidecar` was attached successfully with the exact authorized command.

The sidecar is now present in tmux and `/ops/mineru/log-channel-ownership` reports `sidecar.runningState=observed-recent`, `runningObserved=true`.

This is a sidecar attachment / observability transport recovery only. It is not business-progress proof, readiness, L3, pressure PASS, release readiness, go-live readiness, or production上线.

## Branch / HEAD

Development workspace:

- Branch from required check: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- Worktree had existing modified/untracked files from the multi-role shared workspace.

Production workspace:

- Branch: `main...origin/main`
- HEAD: `890ecf7 Dispatch MinerU sidecar attach recovery`
- Existing local modification: `docker-compose.override.yml`

## Files Changed

- `TaskAndReport/2026-05-14T09-15-58+0800_P1-MinerU-Sidecar-Attach-Only-Recovery_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

No source code, production config, PRD, role contract, sample, model, DB, MinIO, Docker volume, or historical task/material/artifact was modified by this task.

## Preflight Commands And Exit Codes

All preflight gates passed before sidecar start.

- `git status --short --branch` in development workspace — exit 0.
- `git status --short --branch` in production workspace — exit 0; output showed `## main...origin/main` and modified `docker-compose.override.yml`.
- `git log -1 --oneline` — exit 0; `890ecf7 Dispatch MinerU sidecar attach recovery`.
- `docker compose ps` — exit 0; `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` were healthy.
- `tmux ls || true` — exit 0; no tmux server before attach.
- `lsof -nP -iTCP:8081 -iTCP:8083 -iTCP:11434 -iTCP:19001 -sTCP:LISTEN || true` — exit 0; Docker on `8081`, MinerU Python on `8083`, MinIO console on `19001`, Ollama listeners on `127.0.0.1:11434` and `*:11434`.
- `curl -fsS http://localhost:8081/__proxy/upload/health` — exit 0; `{"ok":true,"service":"upload-server"}`.
- `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` — exit 0; `ok=true`, `blocking=false`, MinerU submit probe `ok=true`/`status=202`, Ollama `chatOk=true`, `qwen3.5:9b` resident.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task` — exit 0; active/current/queued/drift/takeover tasks empty; only unchanged historical AI failures listed.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit` — exit 0; circuit `closed`, `open=false`, counts zero.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership` — exit 0; before attach `summaryState=empty`, sidecar `runningState=not-observed`.
- `curl -fsS http://127.0.0.1:8083/health` — exit 0; MinerU `healthy`, queued `0`, processing `0`.
- `curl -fsS http://127.0.0.1:11434/api/version` — exit 0; Ollama `0.23.2`.
- `curl -fsS http://127.0.0.1:11434/api/ps` — exit 0; `qwen3.5:9b` resident.

## Sidecar Start

Attempted: yes.

Exact authorized command run:

```bash
tmux new-session -d -s luceon-sidecar "cd '/Users/concm/prod_workspace/Luceon2026' && UPLOAD_SERVER_URL=http://127.0.0.1:8081/__proxy/upload MINERU_LOG_SOURCE_CONTEXT=host-filesystem MINERU_ERR_LOG_PATH=/Users/concm/ops/logs/mineru-api.err.log MINERU_LOG_PATH=/Users/concm/ops/logs/mineru-api.log node ops/mineru-log-observer.mjs"
```

Result: exit 0.

No alternate command was used.

## Post-Checks And Exit Codes

- `tmux ls` — exit 0; `luceon-sidecar: 1 windows`.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership` — exit 0; `sidecar.runningState=observed-recent`, `runningObserved=true`, last observer checked at `2026-05-14T01:25:57.932Z` / later `2026-05-14T01:26:06.040Z`.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/global-observation` — exit 0; fresh `host-mineru-log-observer` snapshot exists, but it reported stale historical fallback log data and `attribution=unattributed`.
- `bash ops/runtime-ownership-status.sh` — exit 0; `luceon-sidecar=present`, `luceon-mineru=absent`, `luceon-supervisor=absent`; Docker services healthy; ownership diagnostics showed `summaryState=empty`, `sidecar.runningState=observed-recent`.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task` — exit 0; active/current/queued/drift/takeover tasks empty; only historical AI failures listed.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit` — exit 0; circuit `closed`, `open=false`.
- `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` — exit 0; `ok=true`, `blocking=false`, MinerU submit probe `ok=true`, Ollama healthy/resident.
- Additional read-only clarification: `sleep 3; curl -fsS http://127.0.0.1:8083/health` — exit 0; MinerU returned `processing_tasks=0` after a transient submit-probe task, confirming no persistent active MinerU processing.

## Before / After Endpoint State

Before sidecar attach:

- `/ops/mineru/log-channel-ownership`: `summaryState=empty`, configured logs empty/readable, `sidecar.runningState=not-observed`.
- `/ops/mineru/active-task`: no active/current/queued/drift/takeover tasks.

After sidecar attach:

- tmux: `luceon-sidecar` present.
- `/ops/mineru/log-channel-ownership`: `summaryState=empty`, `sidecar.runningState=observed-recent`, `runningObserved=true`.
- `/ops/mineru/global-observation`: fresh observer snapshot present, but based on stale workspace fallback log and `unattributed`.

Interpretation:

- `SIDEcar_ATTACHED_LOGS_EMPTY_IDLE` with a residual stale fallback observation artifact.
- The sidecar transport is attached and observed.
- Host/container configured MinerU logs remain empty; no business-progress proof exists because no authorized parse/upload ran.

## Skipped Checks And Reasons

- No upload validation was run; forbidden by task.
- No pressure/batch/soak/long-run validation was run; forbidden by task.
- No Docker Compose command was run; forbidden by task.
- No MinerU restart/ownership normalization was run; forbidden by task.
- No Ollama mutation was run; forbidden by task.
- No supervisor attach was run; forbidden by task.
- No repair/reparse/re-AI/cleanup or historical task/material mutation was run; forbidden by task.
- No code/static test suite was run because this task changed no source code.

## Risks / Blockers / Residual Debt

- MinerU API remains healthy but unmanaged by intended `luceon-mineru`; this was explicitly out of scope.
- `luceon-supervisor` remains absent; this was explicitly out of scope.
- Ollama dual-listener ownership risk remains; this was explicitly out of scope and dependency-health was healthy.
- `/ops/mineru/global-observation` picked up stale `uat/scratch/mineru-api.log` fallback content. This is not a current task attribution and should not be treated as business-progress proof.
- Configured production MinerU stdout/stderr log files remain empty. A later separately authorized validation upload is needed to prove live business-progress observability.

## Forbidden Operations Statement

No forbidden operation was performed: no upload, no pressure/batch/soak, no Docker mutation, no DB/MinIO/Docker volume/data cleanup, no MinerU restart/kill/ownership normalization, no Ollama mutation, no supervisor attach, no config/secret/model/sample mutation, no repair/reparse/re-AI/cleanup, no PRD/role/release truth change, and no readiness/go-live claim.

## Review / Next Step

- Director review required: yes.
- Current Next Actor after ledger update: `Director`.
- Recommended next step: Director review. If accepted, decide whether to dispatch a separate TestAcceptanceEngineer controlled validation to prove live business-progress observability, or first address stale fallback log hygiene / MinerU ownership normalization.
