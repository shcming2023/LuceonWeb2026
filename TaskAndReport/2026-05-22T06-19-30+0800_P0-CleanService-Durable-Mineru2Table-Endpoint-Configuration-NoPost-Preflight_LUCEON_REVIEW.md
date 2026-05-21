# TASK-237 Luceon Review: Durable Mineru2Table Endpoint Configuration No-POST Preflight

## Review Decision

`ACCEPTED_DURABLE_ENDPOINT_CONFIGURED_NO_POST_WITH_LUCEON_HEAD_CORRECTION`

Task 237 is accepted as a disabled-by-default configuration and preflight task. It establishes `http://mineru2table:8000` as the durable Luceon runtime endpoint candidate for Mineru2Table while preserving `CLEANSERVICE_ENABLED=false`.

This is not CleanService activation, real dispatch acceptance, credentialed success-path acceptance, UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.

## Reviewed Evidence

- Delivery branch: `origin/lucode/task-237@5bee9cddf03ff47d4dca5d919ed161855889315a`.
- Diff scope:
  - `M .env.example`
  - `A TaskAndReport/2026-05-22T05-59-20+0800_P0-CleanService-Durable-Mineru2Table-Endpoint-Configuration-NoPost-Preflight_REPORT.md`
  - `M TaskAndReport/TASK_TRACKING_LIST.md`
  - `M docker-compose.yml`
- `git diff --check origin/main..origin/lucode/task-237` passed with exit 0 before Luceon acceptance.

## Luceon Spot Checks

Luceon independently confirmed:

- `docker compose config | rg CLEANSERVICE` renders:
  - `CLEANSERVICE_ENABLED: "false"`
  - `CLEANSERVICE_ENDPOINT: http://mineru2table:8000`
  - `CLEANSERVICE_STORAGE_ENDPOINT: minio:9000`
  - `CLEANSERVICE_STORAGE_USE_SSL: "false"`
  - `CLEANSERVICE_SUBMITTED_BY: luceon2026/cleanservice-worker`
- From `cms-upload-server`, read-only `GET /health` succeeds for both:
  - `http://mineru2table:8000/health`
  - `http://mineru2table-api:8000/health`
- Both endpoints return honest degraded state: `minio=unconfigured`, `llm=not_configured`, `dependencies=ok`.
- Host job-store `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json` remains 718 bytes with SHA256 `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413`.
- Job-store contains exactly one key: `luceon-optionb-mock-job-1779399902295`.

## Luceon Corrections

1. The submitted report and ledger recorded `ae9708bc5a76b87ccc912e860fc8d87d74f94ddd`, but the GitHub-visible branch HEAD reviewed by Luceon is `5bee9cddf03ff47d4dca5d919ed161855889315a`. Luceon corrected this evidence during acceptance.
2. The submitted report used the dev-container job-store path only. Luceon added the host path verified during review: `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json`.

## Accepted Boundary

Accepted:

- Durable endpoint candidate selected: `http://mineru2table:8000`.
- Endpoint is persisted in `.env.example` and `docker-compose.yml` config surface.
- `CLEANSERVICE_ENABLED=false` remains the default.
- Runtime-side GET-only reachability from `cms-upload-server` is proven.
- `jobs.json` did not change from Task 236 post-state.

Not accepted or not performed:

- Any `POST /api/v1/jobs`.
- Any real material selection.
- Any credential injection or secret configuration.
- Any MinIO object/bucket read/write/list/delete.
- Any Luceon DB write, LLM call, Docker restart/rebuild/recreate, source code edit, job-store cleanup, UAT, L3, readiness, pressure PASS, production上线, or go-live.

## Next-Step Planning Boundary

Per Director's updated Luceon operating rule, Luceon will not issue the next concrete task directly from this acceptance. Before any Task 238 is drafted, Luceon must review current project state, check progress, present the next-step plan, and wait for Director confirmation.
