# Luceon Review v3 - TASK-20260522-164820-P0-CleanService-Verified-Metadata-Persistence-Payload-Planner-NoDB

## Review Result

`ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_EVIDENCE_CORRECTION`

Task 250 is accepted at code/test level and merged into `main`.

This acceptance covers only the mock-safe dry-run metadata persistence payload
planner. It does not accept real DB persistence, worker activation, job
dispatch, runtime wiring, or production readiness.

## Reviewed Branch

```text
origin/lucode/TASK-20260522-164820
```

Reviewed remote HEAD:

```text
7740faec009bffd155c8815a00b72f1320b79acc
```

Reviewed against:

```text
origin/main=dbddcbccdbcbe61f9136debbd2abcb26fd98bffd
```

Integrated by Luceon merge commit before evidence correction:

```text
74d0298f3a748729190b4fbe3856ab8b4a95eba1
```

## Scope Accepted

Accepted implementation files:

```text
server/services/cleanservice/metadata-persistence.mjs
server/services/cleanservice/metadata-summary.mjs
server/tests/cleanservice-metadata-persistence-smoke.mjs
```

Accepted behavior:

- `buildCleanMetadataPersistencePlan(...)` builds dry-run task/material PATCH
  payloads only.
- Non-persistable candidates produce no PATCH payload.
- Source input bucket/object/sha256/size is carried into both task-side and
  material-side patch summaries.
- Missing `materialId`, `assetVersion`, or `jobId` blocks the plan with a
  specific reason.
- Seven artifact ObjectRefs and non-zero token totals remain hard gates.
- Existing unrelated `metadata.cleanServiceJobs` and
  `metadata.cleanMaterials` branches are preserved by pre-merge patch
  construction.
- Cost source is explicitly classified as `job-stats`,
  `verification/candidate`, or `unavailable`.
- No full artifact contents are stored in the patch.

## Luceon Verification

Commands run after merge into the production control workspace:

```bash
node server/tests/cleanservice-metadata-persistence-smoke.mjs
node server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-foundation-smoke.mjs
node server/tests/cleanservice-worker-shell-smoke.mjs
node server/tests/cleanservice-http-transport-smoke.mjs
node server/tests/cleanservice-worker-factory-smoke.mjs
node server/tests/cleanservice-payload-alignment-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
git diff --check HEAD~1..HEAD
```

Observed result:

- metadata persistence smoke: PASS 7/7;
- output ingestion candidate smoke: PASS 7/7;
- seven-artifact output verifier smoke: PASS 8/8;
- foundation, worker shell, HTTP transport, worker factory, and payload
  alignment smokes: PASS;
- `tsc --noEmit`: exit 0;
- whitespace check: no output.

Additional Luceon independent reproduction confirmed:

```text
sourceInput in generated patches: true
task source sha: source-sha
material source size: 31543
materialId: {"ok":false,"shouldApply":false,"reason":"missing-material-id"}
assetVersion: {"ok":false,"shouldApply":false,"reason":"missing-asset-version"}
jobId: {"ok":false,"shouldApply":false,"reason":"missing-job-id"}
```

## Evidence Correction

Lucode's final branch was physically reviewed at:

```text
7740faec009bffd155c8815a00b72f1320b79acc
```

The submitted ledger/report still referred to intermediate
`345fc10b78a000413f855d385519cfecedaaf925` as the final head. Luceon corrected
that control-plane evidence during acceptance instead of returning the task
again, because the implementation and tests were acceptable.

## Explicit Non-Acceptance Boundary

This review does not accept:

- real Luceon DB writes;
- `/tasks/:id` or `/materials/:id` API calls;
- `POST /api/v1/jobs`;
- Mineru2Table polling;
- worker/protocol/transport/upload-server wiring;
- CleanService runtime activation;
- MinIO object reads, writes, deletes, or cleanup;
- LLM calls;
- Docker/Compose/env mutation;
- RawMaterial2CleanMaterial work;
- UAT, L3, pressure PASS, release readiness, production readiness, or go-live.

## Next Mainline Candidate

The next mainline decision is whether Director authorizes a tightly scoped DB
metadata apply task. If not, the next task should remain mock-safe and use an
injected DB client executor.
