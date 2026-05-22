# Task 249 Luceon Review v2

Review time: 2026-05-22T16:40:30+0800

Reviewed branch:

```text
origin/lucode/TASK-20260522-150902@76d9ac557ea66a0f2a49c8d6a4fd4ff0efc2c26c
```

Baseline:

```text
origin/main@afb75fe56965b4fa5580513322d44d3ff8df2266
```

## Verdict

Task 249 is accepted at code/test level.

Final classification:

```text
ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_EVIDENCE_CORRECTION_AND_BOUNDED_VERIFIER_CONTRACT_EXCEPTION
```

This accepts only the mock-safe metadata candidate and verifier-summary
contract needed for the next mainline step. It does not accept runtime
activation, DB persistence, worker orchestration, real POST dispatch, real
MinIO mutation, Docker/env/package changes, UAT, L3, pressure PASS, release
readiness, or go-live.

## Accepted Scope

Accepted implementation files:

```text
server/services/cleanservice/metadata-summary.mjs
server/services/cleanservice/output-verifier.mjs
server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
server/tests/cleanservice-output-verifier-smoke.mjs
```

`output-verifier.mjs` was outside the original Task 249 preferred write
boundary. Luceon accepts this as a bounded exception because the prior return
identified a verifier-to-candidate source-input contract gap, and the accepted
change only extends the verifier's in-memory summary with sourceInput and token
details. This is not a general relaxation of future task boundaries.

## Acceptance Basis

The resubmission fixes the previous blockers:

- candidate construction now consumes `verification.sourceInput` before falling
  back to inline `job.provenance`;
- real-shape tests cover a job with no inline provenance;
- missing source bucket/object/sha256 now blocks persistence through
  `BLOCKED_VERIFIER_CONTRACT_GAP`;
- prompt/completion/total token counts are preserved in task and material
  summaries;
- trailing whitespace was removed;
- branch, report, and ledger evidence are GitHub-visible.

Luceon corrected report/ledger evidence during acceptance:

- report baseline was corrected to the review baseline
  `afb75fe56965b4fa5580513322d44d3ff8df2266`;
- report HEAD was expanded to the full reviewed SHA
  `76d9ac557ea66a0f2a49c8d6a4fd4ff0efc2c26c`;
- changed-file evidence was corrected so
  `server/tests/cleanservice-output-ingestion-candidate-smoke.mjs` is recorded
  as added relative to the review baseline;
- fixture coverage wording was corrected from six cases to seven cases.

## Checks Performed By Luceon

```bash
git fetch origin lucode/TASK-20260522-150902 --prune
git rev-parse origin/lucode/TASK-20260522-150902
git merge-base origin/main origin/lucode/TASK-20260522-150902
git diff --name-status origin/main..origin/lucode/TASK-20260522-150902
git diff --check origin/main..origin/lucode/TASK-20260522-150902
node --check server/services/cleanservice/metadata-summary.mjs
node --check server/services/cleanservice/output-verifier.mjs
node --check server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
node --check server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-foundation-smoke.mjs
node server/tests/cleanservice-worker-shell-smoke.mjs
node server/tests/cleanservice-http-transport-smoke.mjs
node server/tests/cleanservice-worker-factory-smoke.mjs
node server/tests/cleanservice-payload-alignment-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
```

Observed results:

- remote branch exists at
  `76d9ac557ea66a0f2a49c8d6a4fd4ff0efc2c26c`;
- `git diff --check` passes;
- focused ingestion candidate smoke passes 7/7;
- output verifier smoke passes 8/8;
- CleanService regression smokes pass;
- `tsc --noEmit` passes in Luceon's dependency-linked review worktree;
- Luceon independent verifier-to-candidate reproduction confirmed source
  bucket/object/sha256 and prompt/completion/total tokens survive when the job
  has no inline provenance or stats.

## Residual Boundary

This task does not persist anything. The next persistence task must still prove
that the chosen persistence path receives the exact bounded candidate and does
not write DB records when `shouldPersist=false`.

Cost fields are accepted for the job-stats path. Before DB persistence, the
next task should explicitly assert the final cost source used by the candidate
when job stats are absent and only `metrics.json` has cost fields.

## Closeout

Task 249 is closed. The next mainline step can be a narrow disabled-by-default
persistence-preflight or metadata-patch application task, still without worker
activation or real automatic dispatch unless separately authorized.
