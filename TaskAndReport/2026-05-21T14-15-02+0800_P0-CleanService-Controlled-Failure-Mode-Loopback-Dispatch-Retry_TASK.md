# TASK-20260521-141502-P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch-Retry

## 1. Task Summary

Retry the Director-authorized Option B controlled failure-mode loopback dispatch now that Task 232 repaired the `JobSubmitRequest` schema gap.

This task is still not a success-path MinIO/LLM validation. It is a bounded real HTTP boundary test with intentionally unconfigured dependencies.

## 2. Mainline Objective

Answer the next critical mainline question:

> After the payload contract fix, can Luceon send exactly one valid real `POST /api/v1/jobs` to local Mineru2Table and observe an honest, bounded failure-mode result without touching MinIO, LLM, DB, or scheduler activation?

## 3. Critical Path Scope

Do only this:

1. Reconfirm Luceon main includes Task 232.
2. Reconfirm Mineru2Table is loopback-bound at `127.0.0.1:8000`.
3. Reconfirm Mineru2Table MinIO/LLM/callback credentials remain empty or absent.
4. Rebuild the same synthetic canonical Raw Material request using current Luceon modules.
5. Run the live OpenAPI schema gate and require zero missing fields.
6. Capture `jobs.json` baseline.
7. Send exactly one real `POST /api/v1/jobs`.
8. Perform bounded read-only status checks for the returned job if accepted.
9. Capture `jobs.json` post-state and report the exact mutation delta.

## 4. Authorization Boundary

This task uses the Director's Option B authorization recorded in:

```text
TaskAndReport/2026-05-21T13-17-47+0800_P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch_DECISION.md
```

Allowed:

- Exactly one real `POST /api/v1/jobs`.
- Read-only `GET /api/v1/jobs/{job_id}` checks for that one job.
- The expected Mineru2Table local job-store mutation for that one job.

Forbidden:

- More than one POST.
- Credential injection or environment/config changes.
- MinIO reads/writes/deletes.
- DB writes or Luceon metadata patching.
- LLM/API calls by configuration.
- Docker restart/rebuild/recreate/down/prune.
- Scheduler-wide activation.
- Real Luceon material selection.
- Job-store cleanup.
- UAT, L3, pressure PASS, release-readiness, production-readiness, production上线, or go-live claims.

## 5. Required Gates Before POST

All must pass:

- `mineru2table-api` container is running.
- `docker inspect` shows host binding only `127.0.0.1:8000`.
- `/health` returns HTTP success with `minio=unconfigured` and `llm=not_configured`.
- Masked env check confirms these are empty or absent:
  - `MINIO_ACCESS_KEY`
  - `MINIO_SECRET_KEY`
  - `DEEPSEEK_API_KEY`
  - `TOC_REBUILD_CALLBACK_SECRET`
- Live OpenAPI schema comparison reports `missing: []`.
- `jobs.json` baseline stat/hash/record-count is captured.

If any gate fails, do not POST and report a blocked classification.

## 6. Candidate Payload

Use a synthetic task only. Do not query Luceon DB or MinIO for a real material.

Suggested identity:

```text
materialId: optionb-mock-material
parseTaskId: optionb-mock-parse-task
assetVersion: v1
input bucket: eduassets-raw
input object: mineru/optionb-mock-material/v1/content_list_v2.json
sink bucket: eduassets-clean
sink prefix: toc-rebuild/optionb-mock-material/v1/
```

The generated payload must include:

- `submitted_at`
- `submitted_by`
- `inputs[0].source.endpoint`
- `inputs[0].source.use_ssl`
- `sink.endpoint`
- `sink.use_ssl`

## 7. Stop Rules

Stop immediately if:

1. Preflight schema gate is not `missing: []`.
2. Any dependency credential is present.
3. Port binding is not loopback-only.
4. The first POST returns `400`, `401`, `403`, or `422`.
5. The first POST times out or returns `5xx`.
6. A job is accepted but more than 5 read-only status checks or more than 30 seconds would be required.
7. Any evidence suggests MinIO write, DB write, LLM call, Docker mutation, credential drift, or scheduler activation.

Do not retry POST. Do not fix code in this task. Do not clean runtime records.

## 8. Positive Acceptance Criteria

One of these must be true:

- `CONTROLLED_FAILURE_DISPATCH_OBSERVED`: exactly one POST was sent; one job was created or rejected in a bounded, traceable way; only expected job-store mutation occurred.
- `BLOCKED_BEFORE_POST_WITH_EVIDENCE`: no POST was sent because a required gate failed.

The report must clearly state which classification applies.

## 9. Report Requirements

Create:

```text
TaskAndReport/2026-05-21T14-15-02+0800_P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch-Retry_REPORT.md
```

Include:

- Branch and exact HEAD.
- Whether POST was sent: `yes` or `no`.
- Exact POST count.
- Exact job ID if accepted.
- Masked dependency matrix.
- Loopback binding evidence.
- Live schema gate result.
- Candidate payload excerpt with no secrets.
- `jobs.json` baseline and post-state stat/hash/record-count.
- HTTP response and bounded GET status evidence, if applicable.
- Final classification.
