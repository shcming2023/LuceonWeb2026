# Stage 6 Evidence - Production Rehearsal And Contract Check

Collected at: `2026-05-26T15:32:27+0800`

Scope: read-only production/control workspace observation plus deploy-contract source preflight. No deployment, restart, submit-probe, upload, DB write, MinIO write, Docker volume mutation, pressure run, readiness, or go-live claim was performed.

Full-UAT supplement collected at: `2026-05-26T16:22:05+0800` after user authorization for deployment, restart, submit-probe, fault injection, and bounded pressure.

## Read-Only Production Observations

- `docker compose ps` showed frontend/upload/db/minio healthy.
- Frontend exposed `0.0.0.0:8081->80/tcp`.
- MinIO console exposed `127.0.0.1:19001->9001/tcp`.
- Dependency health endpoint returned:
  - `ok=true`
  - `blocking=false`
  - MinIO/MinerU/Ollama dependencies true
  - `submitProbe.enabled=false`
- `bash ops/runtime-ownership-status.sh` confirmed `RUN_MINERU_SUBMIT_PROBE=0`; no synthetic MinerU task was created by that helper.
- Active task diagnostics showed no active task.

## Authorized UAT Runtime Observations

- `docker compose build --no-cache` passed.
- `docker compose up -d` recreated the rebuilt app services.
- Post-deploy health:
  - upload health: `ok=true`
  - db health: `ok=true`
  - smoke: `SMOKE_RESULT PASS=13 FAIL=0 SKIP=0 TOTAL=13`
- Runtime ownership status with submit-probe passed after no-cache deployment:
  - submit probe status `202`
  - submit probe task id `d0847bcd-bfaa-4452-bd5a-0bf0e5c3dc1f`
  - admission circuit closed
  - Docker services healthy
- MinerU settled after submit-probe:
  - `queued_tasks=0`
  - `processing_tasks=0`
  - `failed_tasks=0`
  - `completed_tasks=25`

## Contract Lock

- Source now defaults CMS to `8081`.
- Source now requires non-default MinIO credentials and forbids `minioadmin` at startup.
- Source now locks MinIO tag to `minio/minio:RELEASE.2025-09-07T16-13-09Z`.

## Blockers / Pending Items

- Current running MinIO image is `minio/minio:RELEASE.2025-09-07T16-13-09Z`.
- Stage 6 submit-probe was run under explicit UAT authorization.
- Production `.env` secret values were not printed or copied into evidence. The startup contract will fail fast if they are missing or default.

## Status

- Read-only production dependency-health no-submit: `PASS`
- Override/port/control-plane observation: `PASS_READ_ONLY`
- Locked-source deploy contract: `PASS`
- Runtime convergence to locked MinIO tag: `PASS`
- Submit-probe production preflight: `PASS`
- Stage 7 signature/readiness/go-live authorization: `UNSIGNED_NOT_CLAIMED`
