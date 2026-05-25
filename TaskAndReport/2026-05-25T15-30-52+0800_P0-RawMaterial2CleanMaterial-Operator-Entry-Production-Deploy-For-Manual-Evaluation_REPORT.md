# P0 RawMaterial2CleanMaterial Operator Entry Production Deploy For Manual Evaluation Report

Reported at: 2026-05-25T15:30:52+0800

Task ID: TASK-20260525-153052-P0-RawMaterial2CleanMaterial-Operator-Entry-Production-Deploy-For-Manual-Evaluation

Result: `DEPLOYED_AND_HEALTH_VALIDATED_FOR_MANUAL_EVALUATION`

## Scope

The Director explicitly requested production rebuild/recreate and service
restart so manual evaluation can access the current application runtime.

Deployed source:

```text
ef6816104da84d11a4f614b7db294c451cba7fd7
```

## Deployment Command

```bash
docker compose up -d --build --no-deps cms-frontend upload-server db-server
```

Services rebuilt/recreated:

- `cms-frontend`
- `upload-server`
- `db-server`

Services not recreated:

- `minio`

## Validation

```bash
docker compose ps
curl -fsS http://localhost:8081/cms/
curl -fsS http://localhost:8081/__proxy/upload/health
curl -fsS http://localhost:8081/__proxy/db/health
docker inspect -f '{{.State.Health.Status}}' cms-frontend cms-upload-server cms-db-server cms-minio
```

Observed:

- `cms-frontend`: healthy, mapped at `0.0.0.0:8081->80/tcp`
- `cms-upload-server`: healthy
- `cms-db-server`: healthy
- `cms-minio`: healthy
- `/cms/`: HTML returned successfully
- `/__proxy/upload/health`: `{"ok":true,"service":"upload-server"}`
- `/__proxy/db/health`: `{"ok":true,"service":"db-server",...}`

## Notes

Docker Compose emitted the existing orphan-container warning for
`cms-minio-init`. No orphan cleanup was performed.

## Explicitly Not Done

- No MinIO volume cleanup, delete, copy, move, or broad object scan.
- No DB data cleanup, migration, reset, or manual mutation.
- No upload, submit-probe, pressure test, UAT/L3 claim, readiness claim, or
  go-live claim.
- No Docker volume mutation.

