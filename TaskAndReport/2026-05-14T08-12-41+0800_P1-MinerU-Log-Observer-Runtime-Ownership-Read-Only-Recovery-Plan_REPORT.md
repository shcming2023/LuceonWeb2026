# Architect Report: P1 MinerU Log Observer Runtime Ownership Read-Only Recovery Plan

- Task ID: `TASK-20260514-081241-P1-MinerU-Log-Observer-Runtime-Ownership-Read-Only-Recovery-Plan`
- Report time: 2026-05-14T08:20:00+0800
- Role: Architect
- Based on Director task brief: `TaskAndReport/2026-05-14T08-12-41+0800_P1-MinerU-Log-Observer-Runtime-Ownership-Read-Only-Recovery-Plan_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Result: `OPTION_A_PLANNING_COMPLETE_SCOPED_RUNTIME_RECOVERY_RECOMMENDED`

## Executive Conclusion

The current production line is functionally healthy but ownership is not aligned with the repository contract.

Observed runtime:

- MinerU API is reachable and healthy on `*:8083`, but it is a bare conda `mineru-api` process, not a `luceon-mineru` tmux session.
- `mineru-log-observer` / `luceon-sidecar` is not running.
- `luceon-supervisor` is not running and `/ops/dependency-repair/status` returns HTTP 503.
- Docker services are healthy.
- Ollama is healthy for Luceon, but two listeners are present: `127.0.0.1:11434` and `*:11434`, with launchd labels `com.ollama.launchd` and `com.ollama.ollama` also present.
- `/ops/mineru/log-channel-ownership` remains `summaryState=empty`; configured stdout/stderr logs are readable but empty and sidecar is `not-observed`.

Recommendation: complete Option A and proceed to a narrowly scoped DevelopmentEngineer runtime recovery task. The next task should first attach or restore `luceon-sidecar` without touching MinerU/Ollama. MinerU ownership normalization should be a separate user-authorized step because the current MinerU process is healthy but unmanaged. Ollama mutation should be held; record and monitor the dual-listener risk only.

## Current Observed Facts

Production workspace:

- `git status --short --branch`: `## main...origin/main`, local `docker-compose.override.yml` modified.
- `git log -1 --oneline`: `fec8598 Dispatch MinerU ownership recovery plan`.
- `docker compose ps`: `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` healthy.
- `tmux ls`: no tmux server.
- `runtime-ownership-status.sh`: `mineru_api=absent`, `luceon-mineru=absent`, `luceon-sidecar=absent`, `luceon-supervisor=absent`.
- `lsof`: Docker listens on `*:8081`, MinIO console on `127.0.0.1:19001`, MinerU Python listens on `*:8083`, Ollama listens on both `127.0.0.1:11434` and `*:11434`.
- `launchctl list | grep -i -E 'mineru|ollama|luceon'`: `com.ollama.launchd`, `com.ollama.ollama`, and `com.office.mineru` are present.
- upload-server env truth includes `LOCAL_MINERU_ENDPOINT=http://host.docker.internal:8083`, `MINERU_LOG_PATH=/host/mineru-logs/mineru-api.log`, `MINERU_ERR_LOG_PATH=/host/mineru-logs/mineru-api.err.log`, `OLLAMA_API_URL=http://host.docker.internal:11434`, `OLLAMA_TIER2_MODEL=qwen3.5:9b`, strict no-skeleton flags.
- dependency-health with MinerU submit probe is `ok=true`, `blocking=false`, submit probe HTTP `202`.
- active-task diagnostics are clean except unchanged historical AI failures.
- `/ops/mineru/log-channel-ownership` reports `summaryState=empty`; `mineru-api.log` and `mineru-api.err.log` exist/readable but empty; workspace scratch fallback logs are missing; sidecar `runningState=not-observed`.
- MinerU health is `healthy`, `queued_tasks=0`, `processing_tasks=0`, `completed_tasks=50`, `failed_tasks=0`.
- Ollama reports version `0.23.2`; `qwen3.5:9b` is resident.

## Recommended Ownership Contract

### MinerU API Startup

Authoritative owner should remain: host tmux session `luceon-mineru` running `bash ops/start-mineru-api.sh`.

Reason:

- `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md` already defines this contract.
- `ops/start-mineru-api.sh` is the only repo-backed wrapper that creates stable log files and appends stdout/stderr to `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log`.
- The upload-server and container mount expect those log files.

Current deviation:

- MinerU is healthy but not owned by `luceon-mineru`; it appears to be a direct conda process and launchd label `com.office.mineru` exists.

Recommendation:

- Do not restart MinerU in the immediate sidecar recovery task while it is healthy and idle.
- Record this as a runtime ownership drift.
- If Director/User later authorizes MinerU ownership normalization, use a separate task that explicitly permits replacing the unmanaged process with `luceon-mineru`.

### MinerU Log Observer

Authoritative owner should be: host tmux session `luceon-sidecar` running `ops/mineru-log-observer.mjs`.

Required command shape for a later authorized task:

```bash
tmux new-session -d -s luceon-sidecar "cd '/Users/concm/prod_workspace/Luceon2026' && UPLOAD_SERVER_URL=http://127.0.0.1:8081/__proxy/upload MINERU_LOG_SOURCE_CONTEXT=host-filesystem MINERU_ERR_LOG_PATH=/Users/concm/ops/logs/mineru-api.err.log MINERU_LOG_PATH=/Users/concm/ops/logs/mineru-api.log node ops/mineru-log-observer.mjs"
```

Reason:

- `ops/mineru-log-observer.mjs` reads host log files directly and posts snapshots to `/ops/mineru-log-observation`.
- The observer is not lifecycle authority. It should improve observability only.
- It can be started without restarting Docker, MinerU, MinIO, DB, or Ollama.

### Luceon Supervisor

Authoritative owner, if kept, should be: host tmux session `luceon-supervisor` running `node ops/luceon-dependency-supervisor.mjs`.

Required command shape for a later authorized task:

```bash
tmux new-session -d -s luceon-supervisor "cd '/Users/concm/prod_workspace/Luceon2026' && node ops/luceon-dependency-supervisor.mjs"
```

Recommendation:

- Treat supervisor as optional ops helper, not owner of MinerU/Ollama/MinIO/DB.
- Start it only after sidecar preflight passes, or in the same task only if Director explicitly authorizes supervisor start.
- Do not use supervisor action endpoints for recovery in the first recovery task; direct tmux commands are more transparent and easier to audit.

### Ollama Ownership

Authoritative owner should remain: host Ollama app/runtime, not Luceon tmux.

Observed risk:

- Two listeners are present for port `11434`: one on `127.0.0.1`, one on `*`.
- launchd labels `com.ollama.launchd` and `com.ollama.ollama` are present.
- dependency-health and `/api/ps` are healthy, and `qwen3.5:9b` is resident.

Recommendation:

- Do not start, stop, restart, kill, or replace Ollama in the next MinerU observability recovery task.
- Keep dual listener risk as a follow-up ownership review, not a blocker for sidecar recovery.
- Preflight must verify that both listeners still answer consistently enough for Luceon dependency-health; if health fails, hold instead of mutating Ollama.

## Future Executable Command Candidates

These commands are candidates for a later DevelopmentEngineer task only after Director/User authorization. They were not run in this Architect task.

### Read-Only Preflight

```bash
git status --short --branch
git log -1 --oneline
docker compose ps
tmux ls
lsof -nP -iTCP:8081 -iTCP:8083 -iTCP:11434 -iTCP:19001 -sTCP:LISTEN
launchctl list | grep -i -E 'mineru|ollama|luceon'
curl -fsS http://localhost:8081/__proxy/upload/health
curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership
curl -fsS http://127.0.0.1:8083/health
curl -fsS http://127.0.0.1:11434/api/version
curl -fsS http://127.0.0.1:11434/api/ps
```

### Minimum Sidecar Attach

```bash
tmux new-session -d -s luceon-sidecar "cd '/Users/concm/prod_workspace/Luceon2026' && UPLOAD_SERVER_URL=http://127.0.0.1:8081/__proxy/upload MINERU_LOG_SOURCE_CONTEXT=host-filesystem MINERU_ERR_LOG_PATH=/Users/concm/ops/logs/mineru-api.err.log MINERU_LOG_PATH=/Users/concm/ops/logs/mineru-api.log node ops/mineru-log-observer.mjs"
```

Use only if:

- no `luceon-sidecar` session already exists;
- active-task diagnostics are clean;
- dependency-health is non-blocking;
- MinerU is healthy;
- upload-server health is OK.

### Optional Supervisor Attach

```bash
tmux new-session -d -s luceon-supervisor "cd '/Users/concm/prod_workspace/Luceon2026' && node ops/luceon-dependency-supervisor.mjs"
```

Use only if Director explicitly includes supervisor in the next task. It should not be used to restart MinerU or Ollama in that task.

### Separate MinerU Ownership Normalization

Only if separately authorized:

```bash
tmux new-session -d -s luceon-mineru "cd '/Users/concm/prod_workspace/Luceon2026' && bash ops/start-mineru-api.sh"
```

This command alone is not sufficient if another unmanaged MinerU process already owns `8083`; a safe normalization plan would need explicit authority for stop/kill/restart, which is not recommended in the immediate sidecar recovery task.

## Preflight Gates Before Any Runtime Mutation

All must pass before sidecar/supervisor attach:

1. No active parse/AI workload:
   - `/ops/mineru/active-task` has no active/current/queued/drift/takeover task.
   - admission circuit counts are zero.
2. Upload-server healthy:
   - `/health` returns `ok=true`.
3. MinerU lifecycle healthy:
   - `/ops/dependency-health?mineruSubmitProbe=true` returns `ok=true`, `blocking=false`, MinerU submit probe HTTP `202`.
   - direct MinerU `/health` returns `healthy`.
4. Docker services healthy:
   - `docker compose ps` shows db-server, frontend, minio, upload-server healthy.
5. Log path visible:
   - `/ops/mineru/log-channel-ownership` endpoint is reachable.
   - configured log paths exist/readable or the report explains why sidecar will read host paths directly.
6. Sidecar not already running:
   - `tmux has-session -t luceon-sidecar` is false, or the task switches to post-check only.
7. Ollama not blocking Luceon:
   - dependency-health Ollama is OK and `qwen3.5:9b` resident.
   - if dual listener remains but health is OK, record as follow-up; if health fails, hold.

Hold conditions:

- Any active parse/AI task exists.
- admission circuit is open.
- MinerU submit probe fails.
- upload-server or Docker service unhealthy.
- `tmux` unavailable.
- sidecar session already exists but endpoint still says `not-observed`, requiring diagnosis instead of blind restart.
- Ollama dependency-health fails or the dual-listener state produces inconsistent health.

## Post-Validation Checklist

After authorized sidecar attach, run only read-only checks:

```bash
tmux ls
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/global-observation
bash ops/runtime-ownership-status.sh
```

Expected improvement:

- `luceon-sidecar` appears in tmux.
- `/ops/mineru/log-channel-ownership.sidecar.runningState` changes away from `not-observed`, or `global-observation` shows a fresh `host-mineru-log-observer` snapshot.
- If logs remain empty because no MinerU parse is running, this is acceptable only as `SIDEcar_ATTACHED_LOGS_EMPTY_IDLE`, not as progress observability fixed.
- For true business-progress proof, a later separately authorized TestAcceptanceEngineer upload must show at least one attributable `active-progress`, `active-business-log`, `active-stage-change`, or explicit fast-complete diagnostic boundary.

Endpoint state interpretation:

- `empty/not-observed` -> not recovered.
- `empty/observed` or fresh global observation with empty logs -> sidecar attached, but no business progress yet.
- `active-*` with business signals -> progress channel working for the observed task.
- `log-observation-stale` -> sidecar/log path may be attached but not fresh; investigate before validation.

## Explicit Forbidden Operations For Next Recovery Task

Unless Director/User explicitly broadens scope, the next task should forbid:

- PDF upload.
- pressure, batch, soak, broad stress, or long-run validation.
- Docker Compose up/down/rebuild/restart.
- DB/MinIO/Docker volume/data mutation.
- failed-task repair, retry, reparse, re-AI, cleanup, delete, rename, or historical task mutation.
- log deletion, truncation, rotation, or inode replacement.
- Ollama start/stop/restart/kill/reload, model pull/delete/replace, or model/env/config mutation.
- MinerU API stop/kill/restart while current unmanaged MinerU is healthy.
- production override, secrets, sample-file, PRD, release, or role-contract mutation.
- L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线 claim.

## Recommended Next Step

Architect recommends: `OPTION_A_PLANNING_COMPLETE_SCOPED_RUNTIME_RECOVERY_NEXT`.

Next actor should be Director. Director should issue a DevelopmentEngineer task with one of two precise scopes:

1. Preferred minimum scope: attach `luceon-sidecar` only, with the preflight and post-checks above.
2. Broader but still bounded scope: attach `luceon-sidecar` and `luceon-supervisor`, but explicitly forbid supervisor action endpoints and all service restarts.

MinerU ownership normalization and Ollama dual-listener cleanup should remain separate decisions. The project should not pressure-test until sidecar attach is verified and a later controlled observability validation proves business-progress capture or records an explicit product boundary.

## Commands Run And Exit Codes

Development workspace:

- `git status --short --branch` -> 0
- `rg -n "... Architect ..."` on `TaskAndReport/TASK_TRACKING_LIST.md` -> 0
- `sed` reads of Task 111 brief, Architect role, Task 109 report/review, Task 110 decision, production ownership doc, runtime scripts, sidecar script, MinerU startup script, supervisor script, upload-server ownership surfaces -> 0
- `rg -n "luceon-supervisor|dependency-supervisor|mineru-log-observer|luceon-sidecar|luceon-mineru|start-mineru-api|tmux" ops docs server package.json` -> 0

Production workspace:

- `git status --short --branch` -> 0
- `git log -1 --oneline` -> 0
- `docker compose ps` -> 0
- `lsof -nP -iTCP:8081 -iTCP:8083 -iTCP:11434 -iTCP:19001 -sTCP:LISTEN` -> 0
- `tmux ls` -> 1, no tmux server running
- `bash ops/runtime-ownership-status.sh` -> 0
- `launchctl list | grep -i -E 'mineru|ollama|luceon'` -> 0
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership` -> 0
- `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status` -> 22, HTTP 503 because supervisor is unavailable

## Skipped Checks

- No service start/stop/restart/kill/reload was performed.
- No upload or validation workload was created.
- No Docker mutation was performed.
- No log cleanup, truncation, rotation, or filesystem mutation was performed.
- No production config, env, secret, model, sample, DB, MinIO, task, material, or artifact mutation was performed.
- No GitHub fetch/pull/push was performed by Architect.
- No readiness, L3, pressure PASS, release, or go-live claim is made.
