# Director Review: P1 CleanService Disabled Worker Shell And Metadata Persistence

- Task ID: `TASK-20260516-081514-P1-CleanService-Disabled-Worker-Shell-And-Metadata-Persistence`
- Reviewed at: `2026-05-16T08:27:38+0800`
- Reviewed by: `Director`
- Report reviewed: `TaskAndReport/2026-05-16T08-15-14+0800_P1-CleanService-Disabled-Worker-Shell-And-Metadata-Persistence_REPORT.md`
- Implementation commit reviewed: `474254b`
- Report/ledger commit reviewed: `e2013f6`
- Result: `CHANGES_REQUIRED_INPUT_OBJECT_REF_ELIGIBILITY_GAP`

## Judgment

Returned for correction.

The implementation is correctly isolated from runtime startup and does not touch production, upload flow, pressure validation, or real Mineru2Table dispatch. The disabled no-op behavior and injected mock pattern are directionally correct.

However, Director found a blocking contract gap in the eligibility/input-ref boundary:

- `isCleanServiceTaskEligible()` currently treats a task with only `metadata.mineruStatus = "completed"` as eligible.
- `buildCleanServiceJobRequest()` then falls through to `mineru-parsed-prefix` and emits an input object with no `source.object`.
- This violates Task 201's requirement that a task is eligible only when it has completed MinerU/parsed artifact evidence sufficient for future CleanService input.

Director reproduced the issue with a read-only local snippet:

```json
{
  "eligible": true,
  "input": {
    "role": "mineru-parsed-prefix",
    "source": {
      "type": "minio",
      "bucket": "eduassets-parsed"
    }
  }
}
```

That means a future enabled worker could submit a malformed CleanService job even though the focused smoke tests pass.

## Verification Performed

Director reran:

| Command | Result |
| --- | --- |
| `git diff --check a46ebe3..HEAD` | passed |
| `node --check server/services/cleanservice/cleanservice-worker.mjs server/tests/cleanservice-worker-shell-smoke.mjs` | passed |
| `node server/tests/cleanservice-foundation-smoke.mjs` | passed |
| `node server/tests/cleanservice-worker-shell-smoke.mjs` | passed |
| `npx pnpm@10.4.1 exec tsc --noEmit` | passed |

The checks passing is not sufficient because the regression is in the acceptance criteria and the current test asserts the wrong behavior for `metadata: { mineruStatus: "completed" }`.

## Required Correction

Director issued Task 202 to DevelopmentEngineer.

The correction must:

- make concrete MinIO input evidence mandatory for eligibility;
- reject `mineruStatus=completed` alone when no valid `artifactManifestObjectName`, `markdownObjectName`, or non-empty `parsedPrefix` with parsed-file count exists;
- make `buildCleanServiceJobRequest()` fail explicitly instead of producing `source.object = undefined` if called with invalid input evidence;
- update worker-shell smoke coverage so the reproduced bug becomes a regression test.

## Boundaries Not Accepted

Task 201 is not accepted as complete until Task 202 correction is reviewed.

Still not authorized:

- runtime startup wiring;
- real Mineru2Table dispatch;
- production deployment or validation;
- upload, pressure/batch/soak, submit-probe, retry/reparse/re-AI/cancel/repair/reset;
- DB/MinIO/Docker volume/data cleanup;
- legacy migration/backfill/hiding/deletion;
- global material ID replacement;
- release readiness, production readiness, L3, pressure PASS, production上线, or go-live.

