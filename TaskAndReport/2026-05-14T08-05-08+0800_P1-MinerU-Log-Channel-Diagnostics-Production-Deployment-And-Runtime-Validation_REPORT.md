# Report: P1 MinerU Log Channel Diagnostics Production Deployment And Runtime Validation

- Task ID: `TASK-20260514-080508-P1-MinerU-Log-Channel-Diagnostics-Production-Deployment-And-Runtime-Validation`
- Reported at: 2026-05-14T08:07:47+0800
- Executor: Director, per explicit User instruction
- Result: `DEPLOYED_AND_RUNTIME_VALIDATED_WITH_RESIDUAL_LOG_CHANNEL_OWNERSHIP_GAP`

## Summary

GitHub synchronization was restored first, then production was fast-forwarded and the accepted MinerU log-channel diagnostics were deployed through the minimum authorized upload-server rebuild.

The new production endpoint is reachable and returns structured diagnostics. It confirms the current observability gap: the configured MinerU stdout/stderr log files exist and are readable but empty, fallback host log files are missing, and the `mineru-log-observer` sidecar is not observed. This task did not start or restart the sidecar.

## GitHub Synchronization

- Direct push from the OneDrive development checkout repeatedly timed out while packing/sending objects.
- A clean temporary clone at `/tmp/luceon-github-sync` was used to restore normal GitHub synchronization.
- `origin/main` advanced:
  - `392416c` -> `69108e1 Sync MinerU log channel diagnostics`
  - `69108e1` -> `df23335 Authorize MinerU diagnostics production validation`

## Production Deployment

- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Pre-deploy HEAD: `159d80e Accept MinerU log observation hardening`
- Post-deploy source HEAD: `df23335 Authorize MinerU diagnostics production validation`
- Preserved local production override: `docker-compose.override.yml` remains modified locally.
- Deployment command: `docker compose up -d --build upload-server`
- Exit code: 0
- Docker result: `cms-upload-server` recreated and started; container status became healthy.

## Runtime Validation Evidence

- `curl http://localhost:8081/__proxy/upload/health`
  - `ok=true`, `service=upload-server`
- `curl http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true`
  - `ok=true`, `blocking=false`
  - MinerU submit probe `ok=true`, HTTP `202`, duration `40ms`
  - Ollama `qwen3.5:9b` present, resident, `chatOk=true`, `keepAlive=24h`
- `curl http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit`
  - `state=closed`, `open=false`
- `curl http://localhost:8081/__proxy/upload/ops/mineru/active-task`
  - no active task, no current processing task, no queued tasks, no takeover-required tasks
  - historical AI failure tasks remain listed and were not modified
- `curl http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership`
  - `kind=mineru-log-channel-ownership`
  - `summaryState=empty`
  - configured stdout/stderr log files exist, are readable, and are empty
  - workspace scratch fallback logs are missing
  - sidecar `runningState=not-observed`
  - endpoint explicitly reports diagnostic-only management scope
- Source markers found in production files:
  - `server/upload-server.mjs`
  - `server/lib/ops-mineru-log-parser.mjs`
  - `ops/runtime-ownership-status.sh`
- Container markers found in `cms-upload-server`:
  - `/app/server/upload-server.mjs`
  - `/app/server/lib/ops-mineru-log-parser.mjs`
- `bash ops/runtime-ownership-status.sh` completed and included the new log-channel ownership diagnostics.

## Residual Risks / Follow-Up

- MinerU progress remains observable only as a diagnostic ownership gap, not as business progress. The deployed endpoint confirms empty production log files and no observed sidecar.
- The runtime ownership script showed `mineru_api`, `luceon-mineru`, `luceon-sidecar`, and `luceon-supervisor` tmux sessions absent.
- The runtime ownership script also showed two Ollama listeners (`127.0.0.1:11434` and `*:11434`). Dependency-health was healthy, so no action was taken under this task, but ownership should be reviewed before broader long-run validation.

## Explicitly Not Performed

- No PDF upload.
- No pressure, batch, soak, broad stress, or long-run test.
- No MinerU log observer sidecar start/restart.
- No MinerU/Ollama/MinIO/DB restart beyond the authorized upload-server deployment.
- No failed-task repair, reparse, re-AI, cleanup, historical mutation, or destructive operation.
- No model, secret, config, sample, or production data mutation.
- No L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线 claim.
