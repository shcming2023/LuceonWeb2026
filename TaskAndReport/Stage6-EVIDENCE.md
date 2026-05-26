# Stage 6 Evidence - Production Rehearsal And Contract Check

Collected at: `2026-05-26T15:32:27+0800`

Scope: read-only production/control workspace observation plus deploy-contract source preflight. No deployment, restart, submit-probe, upload, DB write, MinIO write, Docker volume mutation, pressure run, readiness, or go-live claim was performed.

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

## Contract Lock

- Source now defaults CMS to `8081`.
- Source now requires non-default MinIO credentials and forbids `minioadmin` at startup.
- Source now locks MinIO tag to `minio/minio:RELEASE.2024-04-18T19-09-00Z`.

## Blockers / Pending Items

- Current running MinIO image was observed as `minio/minio:latest`; runtime has not yet been rebuilt/recreated under the new locked source contract.
- Stage 6 submit-probe was not run because it creates a real MinerU submit-path task and requires explicit authorization.
- Production `.env` secret values were not printed or copied into evidence. The startup contract will fail fast if they are missing or default.

## Status

- Read-only production dependency-health no-submit: `PASS`
- Override/port/control-plane observation: `PASS_READ_ONLY`
- Locked-source deploy contract: `PASS`
- Runtime convergence to locked MinIO tag: `PENDING_AUTHORIZED_DEPLOYMENT`
- Submit-probe production preflight: `PENDING_EXPLICIT_SUBMIT_PROBE_AUTHORIZATION`
