# TASK-236 Luceon Review: Controlled Failure-Mode Loopback Dispatch After Storage Alignment

## Review Decision

`ACCEPTED_CONTROLLED_FAILURE_DISPATCH_OBSERVED_WITH_ENDPOINT_SCOPE_NOTE`

Task 236 is accepted as a bounded controlled failure-mode dispatch. Exactly one real `POST /api/v1/jobs` was sent to Mineru2Table, the job was accepted, and the only durable runtime mutation observed was the single Mineru2Table job-store record for `luceon-optionb-mock-job-1779399902295`.

This is not success-path Clean Material validation, MinIO integration acceptance, LLM acceptance, Luceon scheduler activation, UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.

## Reviewed Evidence

- Delivery branch: `origin/lucode/TASK-20260521-212648-P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch-After-Storage-Alignment@17e899b4b85328b3926f55ce11fa6b67f091ebf6`.
- Diff scope:
  - `A TaskAndReport/2026-05-21T21-26-48+0800_P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch-After-Storage-Alignment_REPORT.md`
  - `M TaskAndReport/TASK_TRACKING_LIST.md`
- `git diff --check origin/main..origin/lucode/TASK-20260521-212648-P0-CleanService-Controlled-Failure-Mode-Loopback-Dispatch-After-Storage-Alignment` passed with exit 0.
- Report classification: `CONTROLLED_FAILURE_DISPATCH_OBSERVED`.

## Luceon Spot Checks

Luceon independently confirmed:

- `jobs.json` is still 718 bytes with SHA256 `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413`.
- `jobs.json` contains exactly one key: `luceon-optionb-mock-job-1779399902295`.
- `GET /api/v1/jobs/luceon-optionb-mock-job-1779399902295` returns `status=failed` with `error.message=MinIO credentials not configured.` and `error.retriable=false`.
- `mineru2table-api` remains host-bound to `127.0.0.1:8000`.
- Masked environment still shows `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `DEEPSEEK_API_KEY`, and `TOC_REBUILD_CALLBACK_SECRET` at length 0.
- `ALLOWED_MINIO_ENDPOINTS=minio:9000` remains configured.
- Container logs show one `POST /api/v1/jobs HTTP/1.1" 202 Accepted` for the controlled job and read-only status checks afterward.

## Luceon Corrections

1. The submitted report recorded the branch but did not explicitly record the delivery commit. Luceon added `17e899b4b85328b3926f55ce11fa6b67f091ebf6`.
2. The submitted report described `/workspace/ops/Mineru2Tables/data/jobs.json` as the mapped file path. Luceon clarified the dev-container path and the host path `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json`.

## Endpoint Scope Note

The task report shows the scratch dispatch target as `http://172.24.0.6:8000`, which is the Mineru2Table container address on `cms-network`.

This is accepted as evidence that the local Docker-network HTTP ingress, schema, storage endpoint allowlist, and Mineru2Table job runner boundary work together under controlled failure conditions.

It is not accepted as evidence that Luceon's production CleanService worker endpoint environment has been durably configured, that scheduler dispatch is active, or that host-loopback `127.0.0.1:8000` is the correct endpoint for a containerized Luceon worker.

## Accepted Boundary

Accepted:

- One and only one real `POST /api/v1/jobs`.
- The request used synthetic material identifiers only.
- Mineru2Table accepted the job and persisted exactly one job-store record.
- The terminal failure was the expected honest dependency failure: MinIO credentials are not configured.
- No MinIO object read/write/list/delete is evidenced.
- No Luceon DB write, LLM call, Docker restart/rebuild, credential injection, real material selection, or source code edit is evidenced.

Not accepted or not performed:

- Successful MinIO read/write or Clean Material artifact generation.
- Credentialed success-path execution.
- Luceon scheduler/upload-server wiring.
- Webhook callback processing.
- Operator UI state validation.
- UAT, L3, readiness, pressure PASS, production上线, or go-live.

## Next Decision Boundary

The next mainline step crosses a larger boundary than Task 236. Before any credentialed success-path run, Director must explicitly authorize:

- whether to configure a durable CleanService endpoint for the Luceon runtime first;
- whether to inject scoped MinIO/LLM credentials;
- which exact Raw Material candidate, cost ceiling, and output bucket/prefix policy to use;
- whether the existing single failed mock job remains as audit evidence or is handled by a separately authorized cleanup/archive policy.
