# P0 Production Deploy Contract Lock And Reproducibility Preflight - Report

Status: `COMPLETED_SOURCE_CONTRACT_AND_PREFLIGHT`

## Summary

Locked the deployment source contract around the actual local production port and reproducible MinIO baseline.

## Changes

- `docker-compose.yml`
  - Default CMS port is now `8081`.
  - MinIO image is locked to `minio/minio:RELEASE.2024-04-18T19-09-00Z`.
  - Upload server and MinIO require explicit `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY`; no `minioadmin` fallback remains.
- `.env.example`
  - `CMS_PORT=8081`.
  - Public endpoint examples updated to `8081`.
- `ops/start-luceon-runtime.sh`
  - Fails fast if MinIO credentials are unset, empty, or `minioadmin`.
- `docs/deploy/RELEASE_CHECKLIST.md`
  - Added deploy-contract lock section.
  - Replaced placeholder digest claims with Stage 2回填 requirements.
  - Updated Stage 3/4/5/6 pass semantics to avoid fake pass and readiness/go-live wording.

## Evidence

- `docker compose config --quiet` without MinIO credentials: blocked as expected on required variable.
- `MINIO_ACCESS_KEY=preflight_nondefault MINIO_SECRET_KEY=preflight_nondefault_secret docker compose config --quiet`: `PASS`
- `npx tsc --noEmit`: `PASS`
- `npm run build`: `PASS`

## Runtime Observation

Current production/control `docker compose ps` still showed running MinIO image `minio/minio:latest`. This task did not rebuild or recreate runtime services. Runtime convergence to the locked MinIO tag remains pending an explicitly authorized deployment.

## Boundary

No Docker rebuild/recreate/restart, secret printout, DB write, MinIO write, submit-probe, pressure run, readiness, release-readiness, or go-live claim was performed.
