# TASK-20260521-131747-P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch

## 1. Task Summary

Perform one Director-authorized, failure-mode, real loopback dispatch from Luceon CleanService transport to the local Mineru2Table service, but only after a zero-mutation schema gate proves the generated request matches the live Mineru2Table `JobSubmitRequest` contract.

This is a mainline evidence task. It is not a production activation task and not an end-to-end success test.

## 2. Mainline Objective

Answer the next critical mainline question:

> Can Luceon safely cross the real local HTTP boundary to Mineru2Table with a Protocol v1-shaped job request, while dependencies remain intentionally unconfigured and failure remains honest, bounded, and traceable?

Useful side questions such as successful MinIO reads, LLM output quality, clean artifact validation, dashboard UI, webhook callback handling, and Luceon DB persistence are intentionally deferred.

## 3. Critical Path Scope

Do only this:

1. Confirm current Luceon `main` and Mineru2Table local runtime facts.
2. Confirm Mineru2Table is still loopback-bound and dependency-unconfigured.
3. Build exactly one candidate CleanService job request using existing Luceon CleanService modules and a synthetic canonical Raw Material task.
4. Compare that candidate request against the live `/openapi.json` required fields.
5. If the schema gate passes, submit exactly one real `POST /api/v1/jobs`.
6. If a job ID is accepted, perform bounded read-only `GET /api/v1/jobs/{job_id}` checks.
7. Write a report and update the ledger.

## 4. True Preconditions

All must pass before any `POST`:

- Mineru2Table container `mineru2table-api` is running and host port binding is only `127.0.0.1:8000`.
- `GET /health` succeeds and still reports `minio=unconfigured` and `llm=not_configured`.
- Masked env presence check confirms these are empty or absent inside `mineru2table-api`:
  - `MINIO_ACCESS_KEY`
  - `MINIO_SECRET_KEY`
  - `DEEPSEEK_API_KEY`
  - `TOC_REBUILD_CALLBACK_SECRET`
- Live `/openapi.json` confirms the required `JobSubmitRequest`, `InputRef`, `SourceRef`, and `SinkRef` fields.
- Candidate payload contains every field required by the live schema, including nested `endpoint` and `use_ssl` if still required by the runtime.
- The job-store baseline is captured before POST:
  - Container path: `/app/data/jobs.json`
  - Host mount observed by Luceon: `/Users/concm/prod_workspace/Mineru2Tables/data -> /app/data`

If any precondition fails, do not POST.

## 5. Known Evidence From Luceon

Luceon reviewed Task 230 and observed:

- Luceon `origin/main`: `34c9881c89f4bb75ff0f200115ab431a688419fe`
- Mineru2Table deployment HEAD: `af80ced635755384a2c878110013c3e2d8f9cb9a`
- Docker port binding: `127.0.0.1:8000->8000/tcp`
- `/health`: HTTP success with `minio=unconfigured`, `llm=not_configured`, `dependencies=ok`
- Live OpenAPI paths include:
  - `POST /api/v1/jobs`
  - `GET /api/v1/jobs/{job_id}`
  - `POST /api/v1/jobs:from-storage`

Luceon also observed a likely schema mismatch: live OpenAPI requires `SourceRef.endpoint`, `SourceRef.use_ssl`, `SinkRef.endpoint`, `SinkRef.use_ssl`, `submitted_at`, and `submitted_by`; current Luceon `buildCleanServiceJobRequest()` appears not to emit all of these fields. Lucode must verify this before any POST.

## 6. Environment And Write Boundary

### Luceon2026 Workspace

Default workspace:

```text
/workspace/dev/Luceon2026
```

Expected host truth:

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed Git changes in Luceon2026:

- Add one Task 231 report under `TaskAndReport/`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md`.

Forbidden Luceon2026 changes:

- No `server/**`, `src/**`, `.env*`, Docker, Compose, package, lockfile, PRD, architecture, or contract edits.
- No scheduler activation or upload-server integration.
- No DB metadata patch.

### Mineru2Table Runtime

Read-only inspection allowed:

- `docker inspect mineru2table-api`
- `GET /health`
- `GET /openapi.json`
- Bounded `GET /api/v1/jobs/{job_id}` after the one authorized POST, if a job exists.
- Job-store baseline and post-check stat/hash/record-count evidence.

Allowed runtime mutation:

- At most one expected Mineru2Table job-store mutation for the single authorized job.

Forbidden runtime operations:

- No Docker restart/rebuild/recreate/down/prune.
- No environment or credential changes.
- No MinIO object reads/writes/deletes.
- No DB writes.
- No LLM/API calls by configuration.
- No sample file changes.
- No cleanup of `/app/data/jobs.json` or any Docker volume.

## 7. Candidate Payload Rules

Use a synthetic task only. Do not select or scan a real material from Luceon DB or MinIO.

Suggested candidate identity:

```text
materialId: optionb-mock-material
parseTaskId: optionb-mock-parse-task
assetVersion: v1
jobId prefix: luceon-optionb-
input bucket: eduassets-raw
input object: mineru/optionb-mock-material/v1/content_list_v2.json
sink bucket: eduassets-clean
sink prefix: toc-rebuild/optionb-mock-material/v1/
```

Use existing Luceon CleanService modules where possible:

- `server/services/cleanservice/worker-factory.mjs`
- `server/services/cleanservice/cleanservice-worker.mjs`
- `server/services/cleanservice/config.mjs`

Do not use `CleanServiceWorker.tickOnce()` against a real task source. Prefer direct client submission with a one-off, in-memory candidate request so there is no Luceon DB persistence.

## 8. Fast Validation Target

Preferred success evidence:

- Exactly one `POST /api/v1/jobs` is sent.
- Mineru2Table accepts the request and returns a job identity or queued/running/failure response.
- Follow-up status checks show either:
  - honest dependency failure because MinIO/LLM are unconfigured; or
  - a bounded transport/protocol failure that is clearly classified.
- Job-store delta is limited to the single job.

Acceptable blocked evidence:

- `BLOCKED_PAYLOAD_SCHEMA_GAP`: candidate payload does not satisfy live OpenAPI required fields before POST.
- `BLOCKED_DEPENDENCY_DRIFT`: MinIO/LLM credentials are no longer empty.
- `BLOCKED_INGRESS_DRIFT`: endpoint is no longer loopback-only.

Blocked evidence is a valid task outcome if it prevents an unsafe or misleading POST.

## 9. Stop Rules

Stop immediately and report if any of these occur:

1. Schema gate fails before POST.
2. Any Mineru2Table credential that should be empty is present.
3. Port binding is not loopback-only.
4. More than one POST would be required.
5. The first POST returns `400`, `401`, `403`, or `422`.
6. The first POST times out or returns `5xx`.
7. A job is accepted but more than 5 read-only status checks or more than 30 seconds would be needed.
8. Any evidence suggests MinIO write, DB write, LLM call, Docker mutation, or credential/config drift.

Do not retry POST. Do not fix code in this task. Do not clean job-store records.

## 10. Positive Acceptance Criteria

One of these must be true:

- `CONTROLLED_FAILURE_DISPATCH_OBSERVED`: exactly one real POST was sent, the job outcome was observed within bounds, and the only mutation was the single Mineru2Table job-store record.
- `BLOCKED_BEFORE_POST_WITH_EVIDENCE`: no POST was sent because a preflight gate failed, and the report includes exact evidence for the block.

In both cases:

- No secret values are printed.
- No MinIO/DB/LLM/Docker/env mutation occurs.
- The report distinguishes observed facts from hypotheses.

## 11. Negative Acceptance Criteria

The task fails if:

- More than one real POST is sent.
- Any real Luceon material is selected without explicit Director approval.
- Any credential is configured or printed.
- MinIO, DB, LLM, Docker, model, sample, or volume state is mutated beyond the one allowed job-store record.
- Source code is changed.
- The report claims UAT, L3, release-readiness, production-readiness, pressure PASS, production上线, or go-live.

## 12. Report Requirements

Create:

```text
TaskAndReport/2026-05-21T13-17-47+0800_P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch_REPORT.md
```

The report must include:

- Branch and exact HEAD.
- Whether POST was sent: `yes` or `no`.
- If POST was sent, exact job ID and exact count `1`.
- Masked dependency matrix.
- Loopback binding evidence.
- OpenAPI schema gate result.
- Candidate payload with no secrets.
- Job-store baseline and post-check stat/hash/record-count delta.
- HTTP response/status evidence and bounded GET status evidence, if applicable.
- Final classification:
  - `CONTROLLED_FAILURE_DISPATCH_OBSERVED`, or
  - `BLOCKED_PAYLOAD_SCHEMA_GAP`, or
  - another explicit blocked classification.

Update `TaskAndReport/TASK_TRACKING_LIST.md` to `Ready for luceon Review` only after the report is complete.
