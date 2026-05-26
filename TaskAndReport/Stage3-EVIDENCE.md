# Stage 3 Evidence - Smoke Verification

Collected at: `2026-05-26T15:32:27+0800`

Scope: read-only smoke evidence against local `http://127.0.0.1:8081`. No upload, submit-probe, DB write, MinIO write, Docker mutation, pressure run, readiness, or go-live claim was performed.

## Runtime Observations

Production/control workspace `docker compose ps` showed:

- `cms-frontend`: healthy, `0.0.0.0:8081->80/tcp`
- `cms-upload-server`: healthy
- `cms-db-server`: healthy
- `cms-minio`: healthy, console bound to `127.0.0.1:19001->9001/tcp`

## Smoke Command

`BASE_URL=http://127.0.0.1:8081 bash uat/smoke-test.sh`

Result:

```text
SMOKE_RESULT PASS=13 FAIL=0 SKIP=0 TOTAL=13
```

Covered:

- Frontend pages and SPA routes.
- Upload and DB health via Nginx proxy.
- `dependency-health` no-submit check:
  - `ok=true`
  - `blocking=false`
  - `minio=true`
  - `mineru=true`
  - `ollama=true`
  - `submitProbe=false`
- DB REST read endpoints.
- MinIO reverse proxy health.
- MinIO console reachability.

## Status

- Read-only local smoke: `PASS`
- Formal Stage 3 after locked-image rebuild: `PENDING_AUTHORIZED_DEPLOYMENT_AND_RERUN`
