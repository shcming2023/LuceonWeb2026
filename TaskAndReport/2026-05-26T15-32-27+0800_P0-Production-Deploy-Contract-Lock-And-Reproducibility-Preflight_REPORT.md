# P0 Production Deploy Contract Lock And Reproducibility Preflight - Report

Status: `COMPLETED_SOURCE_CONTRACT_AND_PREFLIGHT`

## Summary

Locked the deployment source contract around the actual local production port and reproducible MinIO baseline.

## Changes

- `docker-compose.yml`
  - Default CMS port is now `8081`.
  - MinIO image is locked to `minio/minio:RELEASE.2025-09-07T16-13-09Z`.
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

Initial collection observed production/control `docker compose ps` still running MinIO image `minio/minio:latest`. The later full-UAT authorization allowed runtime convergence work, recorded in `Stage2-EVIDENCE.md`, `Stage6-EVIDENCE.md`, and the full-UAT report.

Runtime convergence result under explicit UAT authorization:

- Production `.env` MinIO credentials were rotated locally away from forbidden defaults; secret values were not printed or committed.
- The first selected fixed 2024 tag was not valid/compatible for this existing MinIO volume.
- Source contract was corrected to `minio/minio:RELEASE.2025-09-07T16-13-09Z`.
- Local digest evidence: `sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e`.
- `docker compose build --no-cache`: `PASS`.
- `docker compose up -d`: `PASS`; app services recreated and healthy.
- Running MinIO image after convergence: `minio/minio:RELEASE.2025-09-07T16-13-09Z`.

## Boundary

The initial preflight performed no Docker rebuild/recreate/restart, secret printout, DB write, MinIO write, submit-probe, pressure run, readiness, release-readiness, or go-live claim. Later Docker rebuild/recreate/restart and submit-probe were performed only after explicit full-UAT authorization. No readiness, release-readiness, or go-live claim is made.
