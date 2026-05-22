# TASK-20260522-094459-P0-Mineru2Table-Credentialed-Preflight-And-Clean-Bucket-NoPost

## 1. Task Summary

Prepare the standalone Mineru2Table service for the first real success-path
dispatch by injecting required runtime credentials and creating an empty
`eduassets-clean` bucket, without sending any job POST.

This task is a credentialed preflight only. It must not dispatch Mineru2Table,
must not call an LLM, must not write Luceon DB, and must not write any object to
`eduassets-clean`.

## 2. Mainline Objective

Answer the next critical-path question:

> Can the standalone Mineru2Table service become credentialed and storage-ready
> for the already seeded canonical Raw Material input, while still making zero
> job submissions?

Task 240 prepared the canonical Raw Material input:

```text
eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
```

The next real dispatch should only happen after this credentialed preflight is
accepted.

## 3. Director Authorization

The Director explicitly authorized Task 241 to:

- inject runtime credentials into Mineru2Table;
- create an empty `eduassets-clean` bucket.

The Director explicitly kept these prohibitions:

- no `POST /api/v1/jobs`;
- no LLM call;
- no Luceon DB write;
- no business source code change;
- no Docker image build;
- no object write/delete/cleanup.

## 4. Current Project State From Luceon

Luceon reviewed current state before issuing this task:

- Luceon `main` and `origin/main`:
  `1a3afae44dff59013ac41a18eee247b89fe54b19`.
- `cms-upload-server` is healthy and Compose-managed.
- `mineru2table-api` is running and healthy at Docker level.
- `GET http://127.0.0.1:8000/health` currently returns:
  - `minio=unconfigured`
  - `llm=not_configured`
  - `dependencies=ok`
- Current `mineru2table-api` sensitive env presence check:
  - `MINIO_ACCESS_KEY=empty`
  - `MINIO_SECRET_KEY=empty`
  - `DEEPSEEK_API_KEY=empty`
  - `TOC_REBUILD_CALLBACK_SECRET=empty`
- Current allowed storage config:
  - `ALLOWED_MINIO_ENDPOINTS=minio:9000`
  - `ALLOWED_INPUT_BUCKETS=eduassets-raw`
  - `ALLOWED_OUTPUT_BUCKETS=eduassets-clean`
  - `JOB_STORE_PATH=/app/data/jobs.json`
- Current selected Raw Material input:
  - bucket: `eduassets-raw`
  - object: `mineru/1842780526581841/v1/content_list_v2.json`
  - size: `31543` bytes
  - sha256:
    `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`
- Current Mineru2Table job store:
  - path:
    `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json`
  - size: `718` bytes
  - sha256:
    `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413`
  - key count: `1`

## 5. Critical Path Scope

Do only this:

1. Reconfirm baseline runtime, canonical Raw Material object, and `jobs.json`.
2. Update the Mineru2Table deployment environment so the running
   `mineru2table-api` receives non-empty:
   - `MINIO_ACCESS_KEY`
   - `MINIO_SECRET_KEY`
   - `DEEPSEEK_API_KEY`
3. Keep these existing allowlists:
   - `ALLOWED_MINIO_ENDPOINTS=minio:9000`
   - `ALLOWED_INPUT_BUCKETS=eduassets-raw`
   - `ALLOWED_OUTPUT_BUCKETS=eduassets-clean`
4. Create bucket `eduassets-clean` if absent.
5. Recreate/restart only the `mineru2table-api` / `mineru2table` service with
   no image build and no dependency recreation, solely to load the environment.
6. Verify, without printing secret values:
   - sensitive env values are `set`, not `empty`;
   - `/health` no longer reports `minio=unconfigured` or
     `llm=not_configured`;
   - the service remains `protocol_version=v1`.
7. Verify MinIO access without writing objects:
   - selected input object can be stat/read-checked from `eduassets-raw`;
   - `eduassets-clean` exists;
   - target output prefix
     `toc-rebuild/1842780526581841/v1/` has no objects.
8. Verify `jobs.json` remains unchanged.
9. Write a report and update the ledger.

## 6. Authorized Runtime/Data Operations

Authorized:

- update only the Mineru2Table deployment environment needed for credentials;
- single-service no-build restart/recreate of `mineru2table-api` /
  `mineru2table`;
- create empty bucket `eduassets-clean` if absent;
- read/stat the selected canonical Raw Material input object;
- list only the target empty output prefix for absence proof.

Credential values must come from the local Director-approved environment or
existing local deployment secrets. If the required values are unavailable, stop
and report:

```text
BLOCKED_CREDENTIALS_UNAVAILABLE
```

## 7. Environment And Write Boundary

Allowed Luceon2026 files:

- `TaskAndReport/2026-05-22T09-44-59+0800_P0-Mineru2Table-Credentialed-Preflight-And-Clean-Bucket-NoPost_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Allowed external deployment file:

- `/Users/concm/prod_workspace/Mineru2Tables/.env`

Allowed external runtime:

- `mineru2table-api` / `mineru2table` single-service no-build restart/recreate
  only.

Forbidden file changes:

- No `server/**` or `src/**` in Luceon2026.
- No `docker-compose*.yml`.
- No `.env*` in Luceon2026.
- No package or lock files.
- No PRD, architecture, or contract docs.
- No AGENTS.md or `.agents/**`.
- No external Mineru2Table source code, tests, Dockerfile, compose file, docs,
  or lock/config files except `/Users/concm/prod_workspace/Mineru2Tables/.env`.

Forbidden runtime/data operations:

- No `POST /api/v1/jobs`.
- No CleanService worker tick or scheduler activation.
- No `CLEANSERVICE_ENABLED=true`.
- No LLM/API call.
- No Luceon DB write.
- No source PDF overwrite, move, rename, or deletion.
- No legacy parsed ZIP overwrite, move, rename, or deletion.
- No object write to `eduassets-clean`.
- No object write to `eduassets-raw`.
- No MinIO object delete, rename, move, cleanup, or broad migration.
- No Docker image build.
- No dependency service restart/rebuild/recreate.
- No Docker network mutation.
- No Docker volume cleanup/prune.
- No job-store cleanup, truncation, or manual edit.
- No secret or credential value printing in reports, terminal excerpts, logs,
  or ledger notes.

## 8. Fast Validation Target

Smallest useful proof:

- `mineru2table-api` has MinIO and LLM credential env values set, with values
  redacted.
- `/health` reports credentialed MinIO and LLM readiness instead of
  `unconfigured` / `not_configured`.
- `eduassets-clean` exists and target prefix is empty.
- Canonical input object remains unchanged.
- `jobs.json` remains unchanged.
- No POST occurred.

## 9. Stop Rules

Stop immediately and report a specific blocked classification if:

1. Required credential values are unavailable.
2. Credential injection would require printing raw secret values.
3. Applying credentials would require Docker image build.
4. Applying credentials would require dependency service restart/recreate.
5. Applying credentials would require network or volume mutation.
6. `/health` still reports `minio=unconfigured` or `llm=not_configured` after
   one safe single-service no-build recreate.
7. Creating `eduassets-clean` would require deleting/replacing an existing
   bucket or object.
8. Any object write beyond empty bucket creation would be needed.
9. Any POST, LLM/API call, Luceon DB write, source code change, or cleanup would
   be needed.
10. `jobs.json` changes unexpectedly.

Do not repair by widening scope.

## 10. Positive Acceptance Criteria

Luceon can accept if:

- Only Mineru2Table deployment `.env`, `mineru2table-api` runtime env, and empty
  `eduassets-clean` bucket state changed.
- `mineru2table-api` remains healthy/running.
- Sensitive env values are present but never printed.
- `/health` indicates MinIO and LLM are configured.
- `eduassets-clean` exists with no target output objects.
- Canonical input object is still present with SHA256
  `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`.
- `jobs.json` remains unchanged.
- No source/config files are modified except the allowed report/ledger and
  Mineru2Table `.env`.
- No `POST`, LLM/API call, DB write, Docker build, dependency recreate, network
  mutation, volume cleanup, object write/delete/cleanup, or wider migration
  occurs.
- `git diff --check` passes.

## 11. Negative Acceptance Criteria

The task fails if:

- Any CleanService dispatch POST is sent.
- Any LLM/API call occurs.
- Any Luceon DB write occurs.
- Any business source code is changed.
- Any object is written to `eduassets-clean`.
- Any object in `eduassets-raw` is modified.
- Any legacy source/parsed object is deleted, renamed, moved, or overwritten.
- Mineru2Table `jobs.json` changes.
- Docker build, dependency recreate, network mutation, or volume cleanup occurs.
- The report prints raw credentials.
- The report claims UAT, L3, release-readiness, production-readiness, pressure
  PASS, production上线, or go-live.

## 12. Required AI/Data Governance Red Lines

1. ID-only / source-only extraction: no model output or source truth generation
   is allowed in this task.
2. Asset hash locking: no source asset names or hashes may be renamed or
   rewritten.
3. Pure layout/code-generation boundary: no LaTeX/TikZ or custom command
   generation is in scope.

## 13. Report Requirements

Create:

```text
TaskAndReport/2026-05-22T09-44-59+0800_P0-Mineru2Table-Credentialed-Preflight-And-Clean-Bucket-NoPost_REPORT.md
```

The report must include:

- Branch and exact HEAD.
- Director authorization summary.
- Exact external `.env` keys changed, with values redacted.
- Exact single-service runtime command shape used.
- Before/after sensitive env presence matrix:
  - `MINIO_ACCESS_KEY`
  - `MINIO_SECRET_KEY`
  - `DEEPSEEK_API_KEY`
  - `TOC_REBUILD_CALLBACK_SECRET` if touched
- Before/after `/health` response with no secrets.
- `eduassets-clean` bucket state and target prefix empty proof.
- Canonical input object size/SHA before/after.
- `jobs.json` before/after size/hash/key-count.
- Whether any POST was sent: must be `no`.
- Whether any LLM/API call occurred: must be `no`.
- Confirmation that no DB write, source code change, Docker build, dependency
  recreate, network mutation, volume cleanup, object write/delete/cleanup, or
  wider migration occurred.
- Final classification:
  - `MINERU2TABLE_CREDENTIALED_PREFLIGHT_READY_NO_POST`, or
  - a specific blocked classification.

## 14. Review Boundary

Acceptance means only:

- Mineru2Table is credentialed and storage-ready for a future single real
  dispatch against the selected canonical Raw Material input.

Acceptance does not mean:

- Mineru2Table dispatch has happened.
- LLM has been called successfully.
- CleanService is active.
- Luceon DB references clean outputs.
- Clean Material artifacts exist.
- UAT, L3, pressure PASS, release readiness, production readiness,
  production上线, or go-live.
