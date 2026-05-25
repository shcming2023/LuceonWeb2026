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

## Next Validation

After this patch is pulled into the production workspace, run:

```bash
bash ops/start-luceon-runtime.sh
curl -fsS http://127.0.0.1:8083/health
curl -fsS http://127.0.0.1:8081/__proxy/upload/ops/dependency-health
```

Expected outcome: MinerU becomes reachable before startup completes, and dependency health is non-blocking.
