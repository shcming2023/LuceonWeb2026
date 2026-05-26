# Stage 2 Evidence - Docker Build And Image Signatures

Collected at: `2026-05-26T15:32:27+0800`

Scope: reproducibility preflight only. No Docker rebuild, image push, image deletion, volume mutation, or service restart was performed in this collection.

Full-UAT supplement collected at: `2026-05-26T16:22:05+0800` after user authorization for production rebuild/recreate/restart.

## Source Contract Locked

- `docker-compose.yml` frontend port default: `CMS_PORT=8081`.
- MinIO image source contract: `minio/minio:RELEASE.2025-09-07T16-13-09Z`.
- MinIO image digest observed locally: `sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e`.
- MinIO credential contract: `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` are required and must not be `minioadmin`.
- Compose validation:
  - Without credentials: blocked by required-variable interpolation.
  - With non-default preflight credentials: `docker compose config --quiet` passed.

## Current Runtime Observation After Authorized UAT

- `docker compose build --no-cache` passed for `cms-frontend`, `upload-server`, and `db-server`.
- `docker compose up -d` recreated the rebuilt app services.
- `docker compose ps` showed all services healthy.
- Running MinIO image converged to `minio/minio:RELEASE.2025-09-07T16-13-09Z`.
- Production `.env` MinIO credentials were rotated locally away from forbidden default values; secret values were not printed or committed.

## UAT Finding And Correction

- The previously selected `RELEASE.2024-04-18T19-09-00Z` tag was not pullable.
- The nearby `RELEASE.2024-04-18T19-09-19Z` tag pulled but could not read the existing MinIO volume because the volume had been created by a newer MinIO data format.
- Source contract was corrected to the locally compatible fixed tag `RELEASE.2025-09-07T16-13-09Z` and digest `sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e`.

## Status

- Compose/env source reproducibility contract: `PASS`
- No-cache Docker build: `PASS`
- Image digest capture: `PASS`
- Runtime convergence to the locked MinIO tag: `PASS`

## Boundary

This file records deployment convergence under explicit UAT authorization. It does not claim release readiness or go-live.
