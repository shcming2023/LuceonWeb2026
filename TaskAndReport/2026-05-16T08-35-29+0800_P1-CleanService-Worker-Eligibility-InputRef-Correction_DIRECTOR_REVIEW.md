# Director Review: P1 CleanService Worker Eligibility InputRef Correction

- Task ID: `TASK-20260516-082738-P1-CleanService-Worker-Eligibility-InputRef-Correction`
- Reviewed at: `2026-05-16T08:35:29+0800`
- Reviewed by: `Director`
- Report reviewed: `TaskAndReport/2026-05-16T08-27-38+0800_P1-CleanService-Worker-Eligibility-InputRef-Correction_REPORT.md`
- Implementation commit reviewed: `061282b`
- Report/ledger commit reviewed: `0f69c5f`
- Result: `ACCEPTED_CORRECTION_CODE_TEST_LEVEL`

## Judgment

Accepted.

The correction closes the eligibility/input-ref gap that caused Task 201 to be returned. `metadata.mineruStatus="completed"` alone is no longer sufficient input evidence, and invalid job-request construction now fails explicitly instead of emitting an input whose `source.object` is missing.

## Director Verification

Director spot-read the implementation diff and reran the original reproducer:

```json
{
  "eligible": false,
  "thrown": "cleanservice-input-object-ref-missing: expected artifactManifestObjectName, markdownObjectName, or parsedPrefix with parsedFilesCount > 0"
}
```

Director also reran:

| Command | Result |
| --- | --- |
| `git diff --check 405462e..HEAD` | passed |
| `node --check server/services/cleanservice/cleanservice-worker.mjs server/tests/cleanservice-worker-shell-smoke.mjs` | passed |
| `node server/tests/cleanservice-foundation-smoke.mjs` | passed |
| `node server/tests/cleanservice-worker-shell-smoke.mjs` | passed |
| `npx pnpm@10.4.1 exec tsc --noEmit` | passed |

## Accepted Scope

Accepted at code/test level only:

- concrete input evidence is now mandatory for CleanService worker eligibility;
- artifact manifest, markdown, and parsed-prefix valid cases remain covered;
- invalid input construction throws a precise error;
- worker shell remains isolated from runtime startup.

## Boundaries Not Accepted

This review does not accept real CleanService runtime behavior.

Still not authorized:

- runtime startup wiring;
- real Mineru2Table dispatch;
- production deployment or validation;
- upload, pressure/batch/soak, submit-probe, retry/reparse/re-AI/cancel/repair/reset;
- DB/MinIO/Docker volume/data cleanup;
- external repository mutation;
- legacy asset migration/backfill/hiding/deletion;
- global material ID replacement;
- release readiness, production readiness, L3, pressure PASS, production上线, or go-live.

## Director Decision

Task 202 is accepted and closed.

Director issued Task 203 to Architect for a read-only Mineru2Table CleanService protocol evidence/gap review. Before Luceon proceeds toward real dispatch or runtime wiring, the external service side must be checked against `docs/contracts/CleanService-Protocol-v1.md`.

