# TASK-20260521-151829-P0-Mineru2Table-Storage-Endpoint-Network-Alignment-And-ReadOnly-Verification

## 1. Task Summary

Implement Director-approved Option A from Task 234: align the standalone Mineru2Table runtime with Luceon's MinIO service boundary so the generated CleanService payload endpoint `minio:9000` is reachable and allowlisted.

This is a runtime/config alignment and read-only verification task. It must not retry the real CleanService dispatch.

## 2. Mainline Objective

Answer the next mainline prerequisite question:

> Can Mineru2Table be configured to use Luceon's intended storage endpoint semantics (`minio:9000` on `cms-network`) without injecting credentials, reading/writing MinIO, or activating real dispatch?

This removes the blocker discovered in Task 233 while preserving the safety boundary for the later controlled failure-mode POST.

## 3. Critical Path Scope

Do only the minimum needed to align runtime/storage endpoint semantics:

1. Work in the external Mineru2Table deployment workspace:

   ```text
   /Users/concm/prod_workspace/Mineru2Tables
   ```

2. Create a dedicated branch in the Mineru2Table repository, for example:

   ```text
   lucode/task-235-mineru2table-storage-network-alignment
   ```

3. Update Mineru2Table Docker/Compose configuration so `mineru2table-api` is attached to the Luceon Docker network where `cms-minio` has alias `minio`.
4. Update Mineru2Table allowlist configuration so `ALLOWED_MINIO_ENDPOINTS` includes `minio:9000`.
5. Keep `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `DEEPSEEK_API_KEY`, and `TOC_REBUILD_CALLBACK_SECRET` empty.
6. Recreate/restart only the `mineru2table-api` service as needed for the configuration to take effect.
7. Run read-only verification only:
   - Docker network membership;
   - `ALLOWED_MINIO_ENDPOINTS`;
   - empty credential matrix;
   - `/health`;
   - `/openapi.json`;
   - `jobs.json` unchanged.
8. Update Luceon control-plane report and ledger.

## 4. Allowed Files

In `/Users/concm/prod_workspace/Mineru2Tables`:

- `docker-compose.yml`
- `.env.example`
- `.env` only if needed for local runtime alignment, and only without secrets

In `/Users/concm/prod_workspace/Luceon2026`:

- `TaskAndReport/2026-05-21T15-18-29+0800_P0-Mineru2Table-Storage-Endpoint-Network-Alignment-And-ReadOnly-Verification_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## 5. Forbidden Operations

Do not:

- configure or print MinIO credentials;
- configure or print LLM/API keys;
- read, write, list, or delete MinIO objects or buckets;
- patch Luceon DB metadata;
- send `POST /api/v1/jobs`;
- run CleanService worker against the real endpoint;
- activate scheduler-wide dispatch;
- select a real Luceon material;
- clean or truncate `jobs.json`;
- rebuild/restart Luceon services;
- mutate Docker volumes beyond the expected `mineru2table-api` container recreation needed for config application;
- claim UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.

## 6. Required Runtime Facts To Preserve

Before and after the change:

- `mineru2table-api` host API binding must remain loopback-only:

  ```text
  127.0.0.1:8000
  ```

- `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `DEEPSEEK_API_KEY`, and `TOC_REBUILD_CALLBACK_SECRET` must remain empty or absent.
- `jobs.json` must remain unchanged.

## 7. Expected Target State

After the task:

- `mineru2table-api` is attached to a network where `minio` resolves to Luceon's `cms-minio` service.
- `ALLOWED_MINIO_ENDPOINTS` includes `minio:9000`.
- Candidate Luceon payload endpoint `minio:9000` passes Mineru2Table storage endpoint allowlist gate.
- `/health` may still report `minio=unconfigured` and `llm=not_configured`; that is acceptable and expected because credentials remain empty.

## 8. Suggested Implementation Shape

Prefer a durable Compose-level solution over ad hoc `docker network connect` commands.

Likely direction:

- add an external network reference for Luceon's `cms-network`;
- attach the `mineru2table` service to both its default network and `cms-network`, or otherwise ensure it can resolve `minio`;
- set `ALLOWED_MINIO_ENDPOINTS=minio:9000` through `.env` / Compose defaults without adding credentials.

If Compose cannot safely express the target in the current repo, stop and report `BLOCKED_COMPOSE_NETWORK_ALIGNMENT_GAP` rather than using an untracked manual Docker state as the only fix.

## 9. Read-Only Verification Requirements

Record exact commands and outputs for:

- Git branch and exact HEAD in Mineru2Table.
- Changed files in Mineru2Table.
- `docker inspect mineru2table-api` network membership and port binding.
- `docker inspect mineru2table-api` masked environment matrix:
  - `ALLOWED_MINIO_ENDPOINTS`
  - `ALLOWED_INPUT_BUCKETS`
  - `ALLOWED_OUTPUT_BUCKETS`
  - `MINIO_ACCESS_KEY`
  - `MINIO_SECRET_KEY`
  - `DEEPSEEK_API_KEY`
  - `TOC_REBUILD_CALLBACK_SECRET`
- `GET /health`.
- `GET /openapi.json` path list.
- `jobs.json` before/after size/hash/content excerpt.
- A no-POST statement.

Do not use MinIO client commands or object listing in this task.

## 10. Positive Acceptance Criteria

Luceon can accept the task if:

- Mineru2Table branch is pushed and exact remote HEAD is reported.
- Runtime container is loopback-bound and healthy/running after config application.
- `ALLOWED_MINIO_ENDPOINTS` includes `minio:9000`.
- `mineru2table-api` can resolve or is network-attached to Luceon's `cms-network` MinIO boundary.
- credentials remain empty/absent.
- `jobs.json` remains unchanged.
- no real dispatch POST was sent.
- `git diff --check` passes for changed Git files.

## 11. Negative Acceptance Criteria

The task fails or must be returned if:

- a real `POST /api/v1/jobs` is sent;
- any credential is configured, printed, or leaked;
- any MinIO object or bucket is read/written/listed/deleted;
- Luceon DB is patched;
- Luceon services are rebuilt/restarted;
- host API binding widens beyond `127.0.0.1`;
- job-store is cleaned or mutated;
- the report claims readiness/UAT/L3/go-live.

## 12. Report Requirements

Create:

```text
TaskAndReport/2026-05-21T15-18-29+0800_P0-Mineru2Table-Storage-Endpoint-Network-Alignment-And-ReadOnly-Verification_REPORT.md
```

The report must include:

- Mineru2Table branch and exact HEAD.
- Luceon control-plane commit if updated.
- Exact changed files.
- Before/after runtime matrix.
- Proof that `minio:9000` is allowlisted.
- Proof that credentials remain empty.
- Proof that no POST was sent and `jobs.json` did not change.
- Residual next step: Task 233 retry may be reissued only after Luceon accepts this runtime/config alignment.
