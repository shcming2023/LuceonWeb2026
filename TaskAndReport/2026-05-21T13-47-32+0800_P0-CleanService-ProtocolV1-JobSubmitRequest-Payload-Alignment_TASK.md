# TASK-20260521-134732-P0-CleanService-ProtocolV1-JobSubmitRequest-Payload-Alignment

## 1. Task Summary

Align Luceon CleanService `JobSubmitRequest` payload generation with the live Mineru2Table Protocol v1 schema discovered in Task 231.

This is a code/test-level contract alignment task. It must not perform a real dispatch.

## 2. Mainline Objective

Answer the next critical mainline question:

> Can Luceon generate a Protocol v1 `POST /api/v1/jobs` payload that satisfies live Mineru2Table required fields before we retry the controlled failure-mode loopback dispatch?

This keeps the mainline moving by fixing the exact contract gap that blocked Task 231, without drifting into successful MinIO/LLM execution or UI work.

## 3. Critical Path Scope

Do only the minimum needed to make Luceon-generated CleanService job requests satisfy the live required schema:

- Add `submitted_at` to the job request.
- Add `submitted_by` to the job request.
- Add `endpoint` and `use_ssl` to `inputs[0].source`.
- Add `endpoint` and `use_ssl` to `sink`.
- Preserve existing canonical Raw Material gating:
  - input bucket remains `eduassets-raw`;
  - input object must remain `mineru/{materialId}/{assetVersion}/content_list_v2.json`;
  - sink bucket remains `eduassets-clean`;
  - legacy parsed-only remains `skipped-policy` and must not become dispatch eligible.
- Add focused tests proving the six missing fields are present and no existing no-submit/disabled behavior regresses.

## 4. True Preconditions

Use Task 231 evidence:

- Task 231 classification: `BLOCKED_PAYLOAD_SCHEMA_GAP`.
- Missing fields:
  - `submitted_at`
  - `submitted_by`
  - `inputs[0].source.endpoint`
  - `inputs[0].source.use_ssl`
  - `sink.endpoint`
  - `sink.use_ssl`
- Current live local Mineru2Table OpenAPI requires those fields.

## 5. Environment And Write Boundary

Workspace:

```text
/workspace/dev/Luceon2026
```

Allowed source files:

- `server/services/cleanservice/config.mjs`
- `server/services/cleanservice/cleanservice-worker.mjs`
- `server/services/cleanservice/raw-material-adapter.mjs`

Allowed tests:

- Existing focused CleanService tests under `server/tests/cleanservice-*.mjs`
- One new focused smoke test if needed, named clearly for Protocol v1 payload schema alignment.

Allowed control-plane files:

- `TaskAndReport/2026-05-21T13-47-32+0800_P0-CleanService-ProtocolV1-JobSubmitRequest-Payload-Alignment_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden files and operations:

- No `upload-server` wiring.
- No scheduler activation.
- No frontend changes.
- No Docker, Compose, env, secret, DB, MinIO, model, sample, or volume mutation.
- No real `POST /api/v1/jobs`.
- No cleanup of Mineru2Table job-store.
- No external Mineru2Table repo edits.

## 6. Implementation Guidance

Prefer extending existing CleanService config rather than hardcoding scattered values.

Recommended contract fields:

- `CLEANSERVICE_STORAGE_ENDPOINT`, defaulting to `minio:9000`.
- `CLEANSERVICE_STORAGE_USE_SSL`, defaulting to `false`.
- `CLEANSERVICE_SUBMITTED_BY`, defaulting to `luceon2026/cleanservice-worker`.

For deterministic tests, make timestamp generation injectable or pass an explicit `submittedAt` option to request construction. Do not make tests depend on wall-clock string matching beyond ISO shape unless an existing local pattern already does that.

Keep credentials out of request bodies. Endpoint and bucket allowlist names are not secrets.

## 7. Fast Validation Target

Add or update a focused smoke that:

1. Builds a canonical Raw Material task request.
2. Asserts all six Task 231 missing fields are present.
3. Asserts `source.endpoint === sink.endpoint`.
4. Asserts `source.use_ssl === false` and `sink.use_ssl === false` by default.
5. Asserts `submitted_by` is deterministic from config.
6. Asserts `submitted_at` is present and valid, or equals an injected fixture timestamp.
7. Asserts legacy parsed-only evidence still throws or results in `skipped-policy` and sends no submit.

Also rerun the existing CleanService focused smokes that were touched by the payload shape.

## 8. Positive Acceptance Criteria

- Generated payload satisfies live required-field shape for `JobSubmitRequest`, `SourceRef`, and `SinkRef`.
- Disabled-by-default behavior remains unchanged.
- Missing endpoint transport behavior remains unchanged.
- Legacy parsed-only remains no-submit.
- Mock HTTP tests still use ephemeral mock endpoints and never call `127.0.0.1:8000`.
- `tsc --noEmit` passes.
- `git diff --check origin/main..HEAD` passes.

## 9. Negative Acceptance Criteria

The task fails if:

- Any real `POST /api/v1/jobs` is sent.
- Any MinIO, DB, LLM, Docker, env, secret, model, sample, or volume state is mutated.
- Legacy parsed-only assets become eligible for dispatch.
- Request bodies include MinIO credentials or secret values.
- The task claims UAT, L3, release-readiness, production-readiness, pressure PASS, production上线, or go-live.

## 10. Deferrable Side Work

Defer all of the following:

- Retrying Option B real dispatch.
- Full MinIO/LLM credential configuration.
- Real Raw Material candidate selection.
- Webhook callback integration.
- Luceon DB metadata persistence.
- Dashboard/status UI.

## 11. Report Requirements

Create:

```text
TaskAndReport/2026-05-21T13-47-32+0800_P0-CleanService-ProtocolV1-JobSubmitRequest-Payload-Alignment_REPORT.md
```

The report must include:

- Branch and exact HEAD.
- Changed file list.
- Before/after payload excerpt showing the six fields.
- Test commands and exit codes.
- Explicit statement that no real POST was sent.
- Residual next step: Task 231 Option B may be retried only after Luceon accepts this contract fix and Director authorization remains in force or is reconfirmed by Luceon.
