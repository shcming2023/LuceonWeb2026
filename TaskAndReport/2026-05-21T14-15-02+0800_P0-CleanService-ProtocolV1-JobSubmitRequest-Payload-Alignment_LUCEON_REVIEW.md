# TASK-232 Luceon Review: ProtocolV1 JobSubmitRequest Payload Alignment

## Review Decision

`ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_MECHANICAL_CORRECTION`

Task 232 is accepted at code/test level. The generated CleanService `JobSubmitRequest` payload now satisfies the live Mineru2Table Protocol v1 required fields that blocked Task 231.

This is not a real dispatch acceptance, UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.

## Reviewed Evidence

- Branch: `origin/lucode/task-232-payload-alignment@7ba37ccfc9aa8c4cd9b49d4bc2d94a9e289918d3`
- Report: `TaskAndReport/2026-05-21T13-47-32+0800_P0-CleanService-ProtocolV1-JobSubmitRequest-Payload-Alignment_REPORT.md`
- Diff scope:
  - `server/services/cleanservice/config.mjs`
  - `server/services/cleanservice/cleanservice-worker.mjs`
  - `server/tests/cleanservice-payload-alignment-smoke.mjs`
  - report and ledger files

## Luceon Verification

Luceon reviewed the implementation in an isolated worktree and ran:

- `node --check server/services/cleanservice/config.mjs`
- `node --check server/services/cleanservice/cleanservice-worker.mjs`
- `node --check server/tests/cleanservice-payload-alignment-smoke.mjs`
- `for f in server/tests/cleanservice-*.mjs; do node "$f"; done`
- `npx pnpm@10.4.1 exec tsc --noEmit`
- live OpenAPI comparison against `http://127.0.0.1:8000/openapi.json` without submitting any job

All focused checks passed.

The live OpenAPI comparison showed no missing required fields after the fix:

```json
{
  "missing": []
}
```

## Luceon Corrections

Two control-plane / mechanical issues were corrected during acceptance:

1. The ledger referenced implementation HEAD `eeeae45...`, but the GitHub-visible reviewed branch HEAD was `7ba37ccfc9aa8c4cd9b49d4bc2d94a9e289918d3`.
2. `git diff --check origin/main..origin/lucode/task-232-payload-alignment` reported one trailing whitespace in `server/services/cleanservice/config.mjs`. Luceon removed that mechanical whitespace during integration and rechecked the integrated diff.

No business logic was changed by Luceon beyond this whitespace correction.

## Accepted Boundary

Accepted:

- `submitted_at` and `submitted_by` are emitted in generated job requests.
- `inputs[0].source.endpoint` and `inputs[0].source.use_ssl` are emitted.
- `sink.endpoint` and `sink.use_ssl` are emitted.
- Defaults are non-secret: `minio:9000`, `false`, and `luceon2026/cleanservice-worker`.
- Legacy parsed-only evidence remains `skipped-policy` / no-submit.
- Disabled-by-default and mock transport behavior remain intact.

Not accepted or not performed:

- No real `POST /api/v1/jobs`.
- No MinIO/DB/LLM/Docker/env/secret/model/sample mutation.
- No external Mineru2Table source change.
- No scheduler activation, upload-server wiring, webhook handling, output ingestion, or real material selection.

## Next Task

Issue Task 233 to retry the controlled failure-mode loopback dispatch under the same one-POST Option B boundary, now that the schema gate is repaired.
