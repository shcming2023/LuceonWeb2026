# TASK-20260522-055920-P0-CleanService-Durable-Mineru2Table-Endpoint-Configuration-NoPost-Preflight

## 1. Task Summary

Establish the durable CleanService endpoint configuration strategy for Luceon calling the standalone Mineru2Table service, without enabling dispatch and without sending any `POST`.

This task exists because Task 236 proved the real HTTP boundary through a transient Docker-network container IP (`http://172.24.0.6:8000`). That evidence is useful, but a container IP is not a durable Luceon runtime configuration.

## 2. Mainline Objective

Answer the next critical-path question:

> What stable endpoint should Luceon's containerized runtime use for Mineru2Table, and can that endpoint be proven reachable from Luceon's runtime network without activating CleanService dispatch?

This must be answered before any credentialed success-path run.

## 3. Critical Path Scope

Do only the minimum needed now:

1. Confirm current Luceon main and Mineru2Table runtime facts.
2. From the Luceon runtime container/network side, test read-only reachability to stable Docker DNS candidates:
   - preferred candidate: `http://mineru2table:8000`
   - fallback candidate: `http://mineru2table-api:8000`
3. Choose one durable endpoint based on observed DNS/HTTP evidence.
4. Persist the chosen endpoint in Luceon config surface while keeping `CLEANSERVICE_ENABLED=false`.
5. Render/inspect config to prove the future endpoint is present and dispatch remains disabled.
6. Confirm `jobs.json` did not change from the accepted Task 236 post-state.
7. Write a report and update the ledger.

## 4. True Preconditions

All must hold:

- Luceon control-plane `main` is at or after Task 236 acceptance.
- Mineru2Table main/deployment workspace is at `f487fd82337bbef550e79789440ca45a5a2dd424` or a later Luceon-accepted descendant.
- `mineru2table-api` is running and still host-bound to `127.0.0.1:8000`.
- Mineru2Table credentials remain empty:
  - `MINIO_ACCESS_KEY`
  - `MINIO_SECRET_KEY`
  - `DEEPSEEK_API_KEY`
  - `TOC_REBUILD_CALLBACK_SECRET`
- Current job-store post-state is preserved:
  - host path: `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json`
  - size: `718` bytes
  - SHA256: `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413`
  - contains exactly `luceon-optionb-mock-job-1779399902295`

If any precondition fails, stop and report a specific block reason.

## 5. Environment And Write Boundary

### Luceon2026 Workspace

Allowed files:

- `docker-compose.yml`
- `.env.example`
- `TaskAndReport/2026-05-22T05-59-20+0800_P0-CleanService-Durable-Mineru2Table-Endpoint-Configuration-NoPost-Preflight_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

If a different compose overlay is truly required, stop and report `BLOCKED_ENDPOINT_CONFIG_SURFACE_UNCLEAR` instead of editing broad runtime files.

Forbidden Luceon2026 changes:

- No `server/**` or `src/**` source changes.
- No package/lockfile changes.
- No PRD/architecture/contract changes.
- No local `.env` secret/config mutation unless Director separately authorizes it.
- No upload-server restart/rebuild/recreate.
- No scheduler activation.
- No Luceon DB writes.

### Mineru2Table Workspace And Runtime

Read-only inspection only:

- Docker inspect.
- DNS/HTTP GET probes.
- `GET /health`.
- `GET /openapi.json` if useful.
- job-store stat/hash/content key count.

Forbidden:

- No Mineru2Table code/config edits.
- No Docker restart/rebuild/recreate/down/prune.
- No credential injection.
- No job-store cleanup/edit/truncation.

## 6. Endpoint Selection Rules

Do not use a container IP such as `172.24.0.6` as the durable endpoint.

Probe from Luceon's runtime side, preferably from `cms-upload-server` or an equivalent container already attached to `cms-network`:

```text
http://mineru2table:8000/health
http://mineru2table-api:8000/health
```

Selection rule:

1. If `http://mineru2table:8000/health` is reachable from the Luceon runtime side, choose `CLEANSERVICE_ENDPOINT=http://mineru2table:8000`.
2. If only `http://mineru2table-api:8000/health` is reachable, choose `CLEANSERVICE_ENDPOINT=http://mineru2table-api:8000` and explain why service-name DNS is unavailable.
3. If neither is reachable, stop with `BLOCKED_DURABLE_ENDPOINT_DNS_GAP`.

## 7. Configuration Requirements

Persist only disabled-by-default configuration. Expected shape:

```text
CLEANSERVICE_ENABLED=false
CLEANSERVICE_ENDPOINT=<chosen durable endpoint>
CLEANSERVICE_STORAGE_ENDPOINT=minio:9000
CLEANSERVICE_STORAGE_USE_SSL=false
CLEANSERVICE_SUBMITTED_BY=luceon2026/cleanservice-worker
```

Do not add or print real API keys. Do not configure `CLEANSERVICE_API_KEY` with a secret value. Do not configure callback secrets.

It is acceptable to document an empty placeholder in `.env.example`, but never introduce a real secret.

## 8. Fast Validation Target

Smallest useful proof:

- From Luceon runtime side, a read-only `GET /health` succeeds against the chosen durable endpoint.
- Rendered compose/config evidence shows `CLEANSERVICE_ENDPOINT=<chosen durable endpoint>`.
- Rendered compose/config evidence shows `CLEANSERVICE_ENABLED=false`.
- Current CleanService remains disabled and no dispatch path is run.
- `jobs.json` remains byte/hash identical to the Task 236 post-state.

## 9. Stop Rules

Stop immediately and report if:

1. A stable DNS name cannot be resolved from Luceon's runtime side.
2. Any probe would require a `POST`.
3. Any credential appears or would need to be added.
4. Any Docker restart/rebuild/recreate would be required.
5. `jobs.json` differs from the Task 236 post-state before the task starts.
6. The config surface for persisting endpoint is ambiguous.

Do not repair by widening scope.

## 10. Positive Acceptance Criteria

Luceon can accept if:

- A durable endpoint is chosen from runtime-side evidence.
- The chosen endpoint is persisted in config surface.
- CleanService remains disabled by default.
- No `POST /api/v1/jobs` is sent.
- No credentials, MinIO object operations, Luceon DB writes, LLM calls, Docker/env runtime mutations, source code changes, or job-store cleanup occur.
- `git diff --check` passes.

## 11. Negative Acceptance Criteria

The task fails if:

- Any real dispatch POST is sent.
- Any real material is selected.
- Any credential is configured, printed, or leaked.
- MinIO object/bucket read/write/list/delete occurs.
- Luceon DB, LLM, Docker runtime, model, sample, or volume state is mutated.
- `jobs.json` is cleaned, truncated, edited, or receives another job.
- Source code is changed.
- The report claims UAT, L3, release-readiness, production-readiness, pressure PASS, production上线, or go-live.

## 12. Required AI/Data Governance Red Lines

Even though this is an endpoint task, preserve the CleanService governance boundary:

1. ID-only extraction: no model output or source truth generation is allowed in this task.
2. Asset hash locking: no source asset names or hashes may be renamed or rewritten.
3. Pure layout/code-generation boundary: no LaTeX/TikZ or custom command generation is in scope.

## 13. Report Requirements

Create:

```text
TaskAndReport/2026-05-22T05-59-20+0800_P0-CleanService-Durable-Mineru2Table-Endpoint-Configuration-NoPost-Preflight_REPORT.md
```

The report must include:

- Branch and exact HEAD.
- Candidate endpoint probe matrix.
- Chosen endpoint and rationale.
- Rendered config evidence showing endpoint and disabled flag.
- Masked credential matrix.
- `jobs.json` before/after size/hash/key count.
- Whether any POST was sent: must be `no`.
- Final classification:
  - `DURABLE_ENDPOINT_CONFIGURED_NO_POST`, or
  - `BLOCKED_DURABLE_ENDPOINT_DNS_GAP`, or
  - another explicit blocked classification.

## 14. Review Boundary

Acceptance means only:

- Luceon's future CleanService endpoint configuration is stable and disabled by default.

Acceptance does not mean:

- CleanService worker/scheduler is active.
- MinIO credentials are configured.
- LLM credentials are configured.
- Real Raw Material success path has been tested.
- Clean Material artifacts are valid.
- UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.
