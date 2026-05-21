# TASK-235 Luceon Review: Mineru2Table Storage Endpoint Network Alignment And Read-Only Verification

## Review Decision

`ACCEPTED_RUNTIME_CONFIG_LEVEL_WITH_EXTERNAL_MAIN_INTEGRATION_AND_LUCEON_EVIDENCE_CORRECTION`

Task 235 is accepted at the runtime/config alignment level. Mineru2Table is now aligned with Luceon's intended storage endpoint semantics for the next controlled failure-mode dispatch: `minio:9000` on `cms-network`.

This is not real dispatch acceptance, MinIO integration acceptance, UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.

## Reviewed Evidence

- Luceon delivery branch: `origin/lucode/task-235-storage-network-alignment@3e1772a5312ed63f86b771d978dfaf0e4a204c7b`.
- Mineru2Table delivery branch: `origin/lucode/task-235-mineru2table-storage-network-alignment@f487fd82337bbef550e79789440ca45a5a2dd424`.
- Mineru2Table external `main` fast-forwarded by Luceon from `af80ced635755384a2c878110013c3e2d8f9cb9a` to `f487fd82337bbef550e79789440ca45a5a2dd424`.
- Luceon diff scope before review correction:
  - `A TaskAndReport/2026-05-21T15-18-29+0800_P0-Mineru2Table-Storage-Endpoint-Network-Alignment-And-ReadOnly-Verification_REPORT.md`
  - `M TaskAndReport/TASK_TRACKING_LIST.md`
- Mineru2Table diff scope:
  - `M .env.example`
  - `M docker-compose.yml`

## Luceon Spot Checks

Luceon independently confirmed:

- `mineru2table-api` is running and Docker reports `Up ... (healthy)`.
- Host API binding remains `127.0.0.1:8000->8000/tcp`.
- `mineru2table-api` is attached to `cms-network` at `172.24.0.6` and to `mineru2tables_default` at `172.26.0.2`.
- From inside `mineru2table-api`, DNS resolves `minio` to `172.24.0.3`.
- Masked environment confirms:
  - `ALLOWED_MINIO_ENDPOINTS=minio:9000`
  - `ALLOWED_INPUT_BUCKETS=eduassets-raw`
  - `ALLOWED_OUTPUT_BUCKETS=eduassets-clean`
  - `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `DEEPSEEK_API_KEY`, and `TOC_REBUILD_CALLBACK_SECRET` all have masked length `0`.
- `GET /health` returns HTTP success with `status=unhealthy`, `minio=unconfigured`, `llm=not_configured`, and `dependencies=ok`, which is expected because credentials remain empty.
- `GET /openapi.json` exposes `/api/v1/jobs`, `/api/v1/jobs/{job_id}`, and `/api/v1/jobs:from-storage`.
- `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json` remains 2 bytes with content `{}` and SHA256 `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`.

## Luceon Corrections

1. `git diff --check origin/main..origin/lucode/task-235-storage-network-alignment` reported two trailing whitespace lines in the submitted report. Luceon removed them during acceptance.
2. The submitted report and ledger recorded the jobs hash as `...4fc77...`; Luceon corrected it to the observed SHA256 `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`.
3. The submitted report listed Luceon control-plane HEAD as base `a6e0caca9941539509cf8c91056a669bb6cbe16e`; Luceon corrected the submitted branch HEAD to `3e1772a5312ed63f86b771d978dfaf0e4a204c7b`.
4. The submitted report mixed Git-tracked changes with local runtime `.env`. Luceon clarified that `.env` was local runtime config only, while Git-tracked Mineru2Table changes are limited to `.env.example` and `docker-compose.yml`.

## Accepted Boundary

Accepted:

- Durable Compose-level attachment of `mineru2table-api` to `cms-network`.
- Allowlist alignment to `minio:9000`.
- Loopback host binding preserved.
- Credentials remain empty.
- Job-store remained unchanged.
- No real dispatch POST was sent.

Not accepted or not performed:

- Any MinIO object or bucket read/write/list/delete.
- Any credential injection.
- Any Luceon DB metadata patch.
- Any LLM call.
- Any scheduler activation or Luceon service rebuild/restart.
- Any success-path Clean Material generation, UAT, L3, pressure PASS, readiness, production上线, or go-live claim.

## Next Task

Luceon issues Task 236 as the next mainline-critical retry: a single controlled failure-mode loopback `POST /api/v1/jobs`, with gates preserved and only one Mineru2Table job-store mutation allowed if the POST is accepted.
