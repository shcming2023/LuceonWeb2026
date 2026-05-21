# TASK-20260521-212648-P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch-After-Storage-Alignment

## 1. Task Summary

Retry the Director-authorized controlled failure-mode loopback dispatch after Task 235 aligned Mineru2Table storage endpoint/network semantics.

This task may send exactly one real `POST /api/v1/jobs` to the local loopback Mineru2Table service, but only after all preflight gates pass. It is a mainline evidence task, not production activation and not a success-path Clean Material validation.

## 2. Mainline Objective

Answer the next critical-path question:

> After schema alignment and storage endpoint/network alignment, can Luceon cross the real local HTTP boundary to Mineru2Table exactly once, while dependencies remain intentionally unconfigured and any failure remains bounded, honest, and traceable?

Do not widen into successful MinIO reads, LLM output quality, dashboard UI, webhook callback processing, or Luceon DB persistence.

## 3. Critical Path Scope

Do only this:

1. Confirm current Luceon and Mineru2Table branch/runtime facts.
2. Confirm `mineru2table-api` is loopback-bound and still has empty MinIO/LLM/callback credentials.
3. Confirm `ALLOWED_MINIO_ENDPOINTS=minio:9000`.
4. Confirm `minio` resolves inside `mineru2table-api` through `cms-network`.
5. Capture `jobs.json` baseline size/hash/content before POST.
6. Build exactly one candidate CleanService job request using existing Luceon CleanService modules and a synthetic canonical Raw Material task.
7. Compare that candidate request against the live `/openapi.json` required schema.
8. If and only if all gates pass, submit exactly one real `POST /api/v1/jobs`.
9. If a job ID is accepted, perform bounded read-only `GET /api/v1/jobs/{job_id}` checks.
10. Write a report and update the ledger.

## 4. True Preconditions

All must pass before any `POST`:

- Mineru2Table container `mineru2table-api` is running.
- Docker host port binding is only `127.0.0.1:8000`.
- `GET /health` succeeds and still reports `minio=unconfigured`, `llm=not_configured`, and `dependencies=ok`.
- Masked env check confirms these are empty or absent inside `mineru2table-api`:
  - `MINIO_ACCESS_KEY`
  - `MINIO_SECRET_KEY`
  - `DEEPSEEK_API_KEY`
  - `TOC_REBUILD_CALLBACK_SECRET`
- `ALLOWED_MINIO_ENDPOINTS` includes `minio:9000`.
- `minio` resolves from inside `mineru2table-api`.
- Live `/openapi.json` confirms the required `JobSubmitRequest`, `InputRef`, `SourceRef`, and `SinkRef` fields.
- Candidate payload contains every field required by the live schema, including `submitted_at`, `submitted_by`, nested `endpoint`, and nested `use_ssl` if still required.
- The job-store baseline is captured before POST:
  - Container path: `/app/data/jobs.json`
  - Host path: `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json`

If any precondition fails, do not POST.

## 5. Current Evidence From Luceon

Luceon accepted Task 235 and observed:

- Mineru2Table external `main`: `f487fd82337bbef550e79789440ca45a5a2dd424`.
- Mineru2Table branch: `lucode/task-235-mineru2table-storage-network-alignment@f487fd82337bbef550e79789440ca45a5a2dd424`.
- Docker port binding: `127.0.0.1:8000->8000/tcp`.
- Network: `mineru2table-api` attached to `cms-network` at `172.24.0.6`.
- Container DNS: `minio` resolves to `172.24.0.3`.
- Environment: `ALLOWED_MINIO_ENDPOINTS=minio:9000`; MinIO/LLM/callback credentials are empty.
- `/health`: HTTP success with honest `status=unhealthy`, `minio=unconfigured`, `llm=not_configured`, and `dependencies=ok`.
- `/openapi.json` exposes `/api/v1/jobs`, `/api/v1/jobs/{job_id}`, and `/api/v1/jobs:from-storage`.
- `jobs.json`: `{}`, 2 bytes, SHA256 `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`.

## 6. Environment And Write Boundary

### Luceon2026 Workspace

Default development workspace:

```text
/workspace/dev/Luceon2026
```

Expected host truth:

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed Git changes in Luceon2026:

- Add one Task 236 report under `TaskAndReport/`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md`.

Forbidden Luceon2026 changes:

- No `server/**`, `src/**`, `.env*`, Docker, Compose, package, lockfile, PRD, architecture, or contract edits.
- No scheduler activation or upload-server integration.
- No Luceon DB metadata patch.

### Mineru2Table Runtime

Allowed read-only inspection:

- `docker inspect mineru2table-api`
- `GET /health`
- `GET /openapi.json`
- bounded `GET /api/v1/jobs/{job_id}` only after the one authorized POST, if a job exists
- job-store baseline and post-check stat/hash/record-count evidence

Allowed runtime mutation:

- At most one expected Mineru2Table job-store mutation for the single authorized job.

Forbidden runtime operations:

- No Docker restart/rebuild/recreate/down/prune.
- No environment or credential changes.
- No MinIO object reads/writes/lists/deletes.
- No Luceon DB writes.
- No LLM/API calls by configuration.
- No sample file changes.
- No cleanup, truncation, or manual editing of `/app/data/jobs.json` or any Docker volume.

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
source endpoint: minio:9000
source use_ssl: false
sink bucket: eduassets-clean
sink prefix: toc-rebuild/optionb-mock-material/v1/
sink endpoint: minio:9000
sink use_ssl: false
```

Use existing Luceon CleanService modules where possible:

- `server/services/cleanservice/worker-factory.mjs`
- `server/services/cleanservice/cleanservice-worker.mjs`
- `server/services/cleanservice/config.mjs`

Do not use `CleanServiceWorker.tickOnce()` against a real task source. Prefer direct client submission with a one-off, in-memory candidate request so there is no Luceon DB persistence.

## 8. Fast Validation Target

Preferred success evidence for this task is controlled failure evidence, not a clean artifact:

- Exactly one `POST /api/v1/jobs` is sent.
- Mineru2Table accepts or rejects the request with a clear response.
- If accepted, follow-up status checks show either:
  - honest dependency failure because MinIO/LLM are unconfigured; or
  - a bounded transport/protocol failure that is clearly classified.
- Job-store delta is limited to the single job.

Acceptable blocked evidence:

- `BLOCKED_PAYLOAD_SCHEMA_GAP`: candidate payload does not satisfy live OpenAPI required fields before POST.
- `BLOCKED_DEPENDENCY_DRIFT`: a credential is now present or health no longer reflects the expected unconfigured dependency state.
- `BLOCKED_INGRESS_DRIFT`: endpoint is no longer loopback-only.
- `BLOCKED_STORAGE_ENDPOINT_ALLOWLIST_GAP`: `minio:9000` is no longer allowlisted or resolvable.

Blocked evidence is a valid task outcome if it prevents an unsafe or misleading POST.

## 9. Stop Rules

Stop immediately and report if any of these occur:

1. Schema gate fails before POST.
2. Any Mineru2Table credential that should be empty is present.
3. Port binding is not loopback-only.
4. `minio:9000` is not allowlisted or `minio` does not resolve inside `mineru2table-api`.
5. More than one POST would be required.
6. The first POST returns `400`, `401`, `403`, or `422`.
7. The first POST times out or returns `5xx`.
8. A job is accepted but more than 5 read-only status checks or more than 30 seconds would be needed.
9. Any evidence suggests MinIO write, Luceon DB write, LLM call, Docker mutation, credential/config drift, or real material selection.

Do not retry POST. Do not fix code in this task. Do not clean job-store records.

## 10. Positive Acceptance Criteria

One of these must be true:

- `CONTROLLED_FAILURE_DISPATCH_OBSERVED`: exactly one real POST was sent, the job outcome was observed within bounds, and the only mutation was the single Mineru2Table job-store record.
- `BLOCKED_BEFORE_POST_WITH_EVIDENCE`: no POST was sent because a preflight gate failed, and the report includes exact evidence for the block.

In both cases:

- No secret values are printed.
- No MinIO/DB/LLM/Docker/env mutation occurs; only the single Mineru2Table job-store record may change if the POST is accepted.
- The report distinguishes observed facts from hypotheses.

## 11. Negative Acceptance Criteria

The task fails if:

- More than one real POST is sent.
- Any real Luceon material is selected without explicit Director approval.
- Any credential is configured or printed.
- MinIO, Luceon DB, LLM, Docker, model, sample, or volume state is mutated beyond the one allowed job-store record.
- Source code is changed.
- The report claims UAT, L3, release-readiness, production-readiness, pressure PASS, production上线, or go-live.

## 12. Report Requirements

Create:

```text
TaskAndReport/2026-05-21T21-26-48+0800_P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch-After-Storage-Alignment_REPORT.md
```

The report must include:

- Branch and exact HEAD.
- Whether POST was sent: `yes` or `no`.
- If POST was sent, exact job ID and exact POST count `1`.
- Masked dependency matrix.
- Loopback binding evidence.
- Storage endpoint allowlist and DNS evidence.
- OpenAPI schema gate result.
- Candidate payload with no secrets.
- Job-store baseline and post-check stat/hash/record-count delta.
- HTTP response/status evidence and bounded GET status evidence, if applicable.
- Final classification:
  - `CONTROLLED_FAILURE_DISPATCH_OBSERVED`, or
  - `BLOCKED_BEFORE_POST_WITH_EVIDENCE`, with a specific block reason.
