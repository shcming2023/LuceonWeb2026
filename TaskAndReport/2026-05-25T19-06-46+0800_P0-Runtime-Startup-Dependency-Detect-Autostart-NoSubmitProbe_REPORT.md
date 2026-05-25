# P0 Runtime Startup Dependency Detect Autostart NoSubmitProbe Report

## Result

`SUCCESS_STARTUP_DEPENDENCY_DETECT_AUTOSTART_GUARD`

## Trigger

The Director observed that the app could open while a core dependency was not running, and stated that project startup should first detect and start related dependencies.

## Root Cause

`ops/start-luceon-runtime.sh` previously issued startup commands but did not wait for core dependency health. A failed or absent MinerU API process could leave Docker services and the frontend reachable while `/__proxy/upload/ops/dependency-health` remained blocking.

## Change

- Reworked `ops/start-luceon-runtime.sh` into a fail-fast startup guard.
- Added Docker/upload dependency wait before continuing.
- Added MinerU `/health` detection before restart/start.
- Preserved already healthy unmanaged MinerU processes instead of killing them.
- Restarted only the managed `luceon-mineru` tmux session when MinerU health is down.
- Added bounded wait controls:
  - `DOCKER_START_TIMEOUT_SEC`
  - `MINERU_START_TIMEOUT_SEC`
  - `DEPENDENCY_HEALTH_TIMEOUT_SEC`
- Added final `/ops/dependency-health` verification without `mineruSubmitProbe=true`.
- Added explicit `ALLOW_DEGRADED_START=1` escape hatch for intentional degraded startup.
- Added static smoke coverage in `server/tests/start-luceon-runtime-script-smoke.mjs`.

## Checks

- `bash -n ops/start-luceon-runtime.sh` passed.
- `node server/tests/start-luceon-runtime-script-smoke.mjs` passed.
- `git diff --check` passed.
- `npx tsc --noEmit` passed.
- `npm run build` passed.

## Boundary

No upload, submit-probe, MinerU `/tasks` probe, CleanService POST, DB write, MinIO write/delete/copy/move/cleanup, Docker volume mutation, pressure run, UAT/L3/readiness/go-live claim was performed by this code/test step.

## Production Workspace Validation

After the patch was pushed and pulled into `/Users/concm/prod_workspace/Luceon2026`, Luceon ran:

```bash
bash ops/start-luceon-runtime.sh
curl -fsS http://127.0.0.1:8083/health
curl -fsS http://127.0.0.1:8081/__proxy/upload/ops/dependency-health
```

Observed outcome:

- `bash ops/start-luceon-runtime.sh` detected MinerU down, started managed tmux session `luceon-mineru`, waited until `/health` was reachable, started `luceon-sidecar` and `luceon-supervisor`, then completed final dependency health verification.
- `tmux list-sessions -F '#S'` showed `luceon-mineru`, `luceon-sidecar`, and `luceon-supervisor`.
- `curl -fsS http://127.0.0.1:8083/health` returned `status=healthy`, `version=3.1.0`.
- `curl -fsS http://127.0.0.1:8081/__proxy/upload/ops/dependency-health` returned `ok=true`, `blocking=false`, `minio=true`, `mineru=true`, `ollama=true`, with MinerU submit probe disabled.
- `docker compose ps` showed `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` healthy/running.
- Browser read-only validation on `/cms/asset/548758763373874` found no `核心依赖未启动` warning and preserved the `资产处理主线` surface.

This is startup/runtime-health validation only. It is not UAT, L3, production readiness, release readiness, pressure PASS, or go-live acceptance.
