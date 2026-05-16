# Director Review: P1 CleanService Mock Protocol Foundation Disabled By Default

- Task ID: `TASK-20260516-080216-P1-CleanService-Mock-Protocol-Foundation-Disabled-By-Default`
- Reviewed at: `2026-05-16T08:15:14+0800`
- Reviewed by: `Director`
- Report reviewed: `TaskAndReport/2026-05-16T08-02-16+0800_P1-CleanService-Mock-Protocol-Foundation-Disabled-By-Default_REPORT.md`
- Implementation commit reviewed: `942420c`
- Report/ledger commit reviewed: `8957577`
- Result: `ACCEPTED_CODE_TEST_LEVEL_MOCK_FOUNDATION_ONLY`

## Judgment

Accepted at code/test level.

The implementation stays inside the task boundary. It added isolated CleanService foundation modules under `server/services/cleanservice/**` plus a focused smoke test. It did not wire CleanService into `server/upload-server.mjs`, `ParseTaskWorker`, `AiMetadataWorker`, frontend UI, Docker, production, or runtime startup.

The accepted behavior is limited to:

- disabled-by-default config and availability summary;
- protocol and transport-error normalization through injected transport only;
- product state, label, task-intent, and cost-policy helpers;
- bounded task/material metadata patch helpers;
- mock output/provenance verification;
- no-silent-fallback checks for raw MinerU / placeholder / skeleton-only output.

## Director Verification

Director spot-read the new modules and focused test, then reran:

| Command | Result |
| --- | --- |
| `git diff --check c5a051f..HEAD` | passed |
| `node --check server/services/cleanservice/config.mjs server/services/cleanservice/states.mjs server/services/cleanservice/protocol.mjs server/services/cleanservice/output-verifier.mjs server/services/cleanservice/metadata-summary.mjs server/tests/cleanservice-foundation-smoke.mjs` | passed |
| `node server/tests/cleanservice-foundation-smoke.mjs` | passed: `PASS cleanservice foundation smoke` |
| `npx pnpm@10.4.1 exec tsc --noEmit` | passed |

## Boundaries Not Accepted

This review does not accept or imply real CleanService runtime behavior.

Still not authorized:

- real Mineru2Table dispatch;
- production deployment or production validation;
- upload, pressure/batch/soak, submit-probe, retry/reparse/re-AI/cancel/repair/reset;
- DB/MinIO/Docker volume/data cleanup;
- external repository mutation;
- legacy asset migration/backfill/hiding/deletion;
- global material ID replacement;
- release readiness, production readiness, L3, pressure PASS, production上线, or go-live.

## Director Decision

Task 200 is accepted and closed.

Director issued Task 201 to DevelopmentEngineer for the next narrow slice: an isolated disabled CleanService worker shell and metadata persistence contract, still not wired into runtime startup and still no real external service dispatch.

