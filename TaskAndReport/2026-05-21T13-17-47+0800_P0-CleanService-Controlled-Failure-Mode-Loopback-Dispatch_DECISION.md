# Director Decision: Authorize Option B Controlled Failure-Mode Loopback Dispatch

## Decision

Director approved Option B on 2026-05-21:

> Use a controlled failure-mode real loopback dispatch before full dependency configuration.

## Authorization Boundary

Authorized:

- Exactly one controlled real `POST /api/v1/jobs` to local Mineru2Table, only if all preflight gates pass.
- Keep Mineru2Table MinIO and LLM credentials unconfigured.
- Read-only follow-up status checks for the single submitted job.
- The only allowed runtime mutation is the expected Mineru2Table local job-store record for that one job.

Not authorized:

- Credential injection or environment/config changes.
- MinIO write/read validation, DB patching, LLM/API call, scheduler-wide activation, Docker rebuild/restart, upload flow, or real material selection.
- More than one `POST /api/v1/jobs`.
- UAT, L3, pressure PASS, release-readiness, production-readiness, production上线, or go-live claim.

## Luceon Clarification

Before the single POST, Lucode must run a zero-mutation schema gate against the live Mineru2Table OpenAPI contract. Current Luceon evidence suggests `buildCleanServiceJobRequest()` may not yet emit all fields required by the live `JobSubmitRequest` schema, including `endpoint`, `use_ssl`, `submitted_at`, and `submitted_by`.

If that schema gap is confirmed, Lucode must stop before POST and report `BLOCKED_PAYLOAD_SCHEMA_GAP`; no code fix is authorized inside the dispatch task.
