# Stage 2 Evidence - Docker Build And Image Signatures

Collected at: `2026-05-26T15:32:27+0800`

Scope: reproducibility preflight only. No Docker rebuild, image push, image deletion, volume mutation, or service restart was performed in this collection.

## Source Contract Locked

- `docker-compose.yml` frontend port default: `CMS_PORT=8081`.
- MinIO image source contract: `minio/minio:RELEASE.2024-04-18T19-09-00Z`.
- MinIO credential contract: `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` are required and must not be `minioadmin`.
- Compose validation:
  - Without credentials: blocked by required-variable interpolation.
  - With non-default preflight credentials: `docker compose config --quiet` passed.

## Current Runtime Observation

- `docker compose ps` in production/control workspace showed all current app services healthy.
- Current running MinIO image was still `minio/minio:latest`; this is pre-existing runtime state and was not mutated in this task.

## Status

- Compose/env source reproducibility contract: `PASS`
- No-cache Docker build: `PENDING_AUTHORIZED_BUILD`
- Image digest capture: `PENDING_AFTER_BUILD_OR_PULL`
- Runtime convergence to the locked MinIO tag: `PENDING_AUTHORIZED_DEPLOYMENT`

## Boundary

This file does not claim that the currently running containers were rebuilt from the new contract.
