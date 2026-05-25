# P0 RawMaterial2CleanMaterial Repeatability Upgrade Gate Decision

Decision ID: `TASK-20260525-142745-P0-RawMaterial2CleanMaterial-Repeatability-Upgrade-Gate-Decision`

Decision time: 2026-05-25T14:27:45+0800

Baseline: `main@966d008f5862aa808b1b396e43db72ed18a64d8a`

Status: `DECISION_THIRD_SAMPLE_PILOT_ALLOWED_MINI_BATCH_NOT_YET`

## Decision

RawMaterial2CleanMaterial is allowed to advance from two canonical samples to a
third canonical sample pilot.

It is not yet allowed to advance directly to bounded mini-batch.

## Basis

Two canonical samples have now reached the same durable closed loop:

```text
parsed ZIP -> raw seed -> CleanMaterial artifacts -> accepted CleanMaterial ->
raw2clean candidate -> durable candidate artifact -> accepted raw2clean decision
```

Accepted evidence:

- sample 1: material `1842780526581841`, task `task-1779085089451`,
  candidate SHA
  `49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27`.
- sample 2: material `2241872074049025`, task `task-1779085090677`,
  candidate SHA
  `6849ea4ddda0cbf8f2a3b720417bfdcd69d1806ce8ceff970c59ef36ffd5dbb5`.

This proves that the chain is no longer only a one-off canonical path. It has
repeated once across a second real sample and surfaced real compatibility
learning without breaking the ID-only source boundary.

## Why Not Mini-Batch Yet

The second sample succeeded, but it also exposed repeatability risk that should
be tested once more before batching:

- the first attempted v1 CleanService job failed because an early harness
  dry-run incorrectly allowed POST before raw seed creation;
- the final successful clean version became `v2`, so the pilot had to reconcile
  around a failed prior job namespace;
- the second sample produced zero raw2clean flooded blocks after skipping
  source-less `flooded_content` text;
- an unrelated 4-byte diagnostic raw object was written while verifying the
  container MinIO write path and remains undeleted because deletion was not
  authorized.

These are not blockers for a third sample pilot. They are blockers for claiming
the loop is batch-shape stable.

## Next Critical Path

Run one third canonical sample pilot with stricter preflight gates:

1. dry-run preflight must not submit CleanService jobs;
2. raw seed existence and SHA must be established before any CleanService POST;
3. at most one CleanService POST is allowed for the target sample unless an
   explicit user decision authorizes recovery from a failed namespace;
4. no diagnostic MinIO write is allowed outside the target raw seed and
   candidate artifact;
5. durable apply remains limited to the selected task/material records;
6. final-quality acceptance, UAT, L3, pressure PASS, release readiness,
   production readiness, production online, and go-live remain unclaimed.

If the third sample reaches durable accepted raw2clean decision without a new
shape fix, failed job namespace, or side-effect deviation, the next decision can
upgrade to a bounded mini-batch pilot.

## Deferred Work

The following should not interrupt the third sample pilot:

- cleanup of failed job `luceon-task-1779085090677-toc-rebuild-v1`;
- cleanup of `eduassets-raw/tmp/codex-test.txt`;
- metadata schema consolidation;
- repair/reject decision workflows;
- generalized batch runner and queue governance;
- final quality acceptance semantics.

## Boundary

This decision performs no code change, DB write, MinIO write/delete/list,
runtime POST, Docker/Compose operation, source/sample/env/secret/model mutation,
batch execution, production deployment, readiness claim, or go-live claim.

