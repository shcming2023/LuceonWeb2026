# Task 259 Report: CleanService Mock-Safe Runner Integration Gap Fix

Report time: 2026-05-24T12:32:00+0800

## 1. Branch And HEAD

Remote branch:

```text
origin/lucode/TASK-20260524-112801-P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime
```

Implementation HEAD:

```text
f60e8d46efc88b94448715dde45d4153bfbff1bc
```

Return-reviewed branch HEAD:

```text
b4f4e3a24c9d1f5bceb1f74c2bf7f99810bb7186
```

Correction branch final remote HEAD reviewed by Luceon:

```text
507906bd517a37f563038a02ba9b0abe6f70bfaf
```

Luceon corrected this final remote HEAD evidence during acceptance review.

## 2. Changed Files

Command:

```bash
git diff --name-status origin/main...HEAD
```

Output after implementation commit:

```text
M       server/services/cleanservice/metadata-apply-executor.mjs
M       server/services/cleanservice/metadata-summary.mjs
M       server/services/cleanservice/orchestration-runner.mjs
M       server/services/cleanservice/output-verifier.mjs
M       server/tests/cleanservice-metadata-apply-executor-smoke.mjs
M       server/tests/cleanservice-orchestration-runner-smoke.mjs
M       server/tests/cleanservice-output-verifier-smoke.mjs
```

Report/ledger files added/updated after this implementation commit:

```text
A       TaskAndReport/2026-05-24T11-28-01+0800_P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
```

## 3. Implemented Product Behavior

Live provenance response shape:

- `verifyCleanServiceOutputArtifacts()` now relies on the injected artifact reader and `artifacts.provenance`; it does not require a top-level `job.provenance` to verify a completed job.
- `metadata-summary` preserves bounded verifier-derived traceability and does not persist full artifact bodies.

Provenance `job_id -probe` policy:

- Exact `provenance.job.job_id === expectedJobId` still passes.
- `expectedJobId + "-probe"` is rejected by default.
- `expectedJobId + "-probe"` is accepted only when the caller explicitly sets
  `allowProbeJobIdSuffix: true`.
- The verifier records `canonicalJobId`, `provenanceJobId`, `provenanceJobIdPolicy=accepted-probe-suffix`, and warning `provenance-job-id-probe-suffix-accepted`.
- Arbitrary job IDs still fail with `job-id-mismatch`.
- Product code does not mutate parsed provenance to pretend IDs are identical.

Explicit new-version dry-run conflict semantics:

- `applyCleanMetadataPersistencePlan()` now permits `DRY_RUN_SUCCESS` over aligned completed previous-version metadata only when `allowRealApply=false` and `plan.newVersionIntent.intent=create-new-version`.
- The policy requires previous task jobId, previous assetVersion, completed
  task/material metadata, a different target version, and
  `plan.newVersionIntent.newAssetVersion` exactly matching the target patch
  version.
- `allowRealApply=true` remains blocked by `BLOCKED_EXISTING_TOC_REBUILD_METADATA` for this conflict shape.

## 4. Focused Tests Added

- `cleanservice-output-verifier-smoke`: added omitted/false policy `-probe`
  rejection, explicit opt-in bounded `-probe` acceptance, exact ID success,
  and unrelated-job rejection.
- `cleanservice-metadata-apply-executor-smoke`: added explicit `v2 -> v3`
  dry-run conflict success, real-apply blocking, and intent target-version
  mismatch blocking.
- `cleanservice-orchestration-runner-smoke`: added Task 256-shaped product-chain case with no top-level provenance, `-probe` provenance jobId, real verifier/candidate/planner/apply dry-run path, and no DB writes.

## 5. Checks

```text
node --check server/services/cleanservice/protocol.mjs: exit 0
node --check server/services/cleanservice/output-verifier.mjs: exit 0
node --check server/services/cleanservice/metadata-summary.mjs: exit 0
node --check server/services/cleanservice/metadata-persistence.mjs: exit 0
node --check server/services/cleanservice/metadata-apply-executor.mjs: exit 0
node --check server/services/cleanservice/orchestration-runner.mjs: exit 0
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs: exit 0
node --check server/tests/cleanservice-output-verifier-smoke.mjs: exit 0
node --check server/tests/cleanservice-metadata-apply-executor-smoke.mjs: exit 0
node server/tests/cleanservice-orchestration-runner-smoke.mjs: exit 0, 24/24
node server/tests/cleanservice-output-verifier-smoke.mjs: exit 0, 9/9
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs: exit 0
node server/tests/cleanservice-orchestration-runner-smoke.mjs && node server/tests/cleanservice-output-verifier-smoke.mjs && node server/tests/cleanservice-metadata-apply-executor-smoke.mjs: exit 0
mock-safe cleanservice-*.mjs loop excluding Task 256 runtime harness: exit 0
npx pnpm@10.4.1 exec tsc --noEmit: exit 0
git diff --name-status origin/main...HEAD: exit 0
git diff --check origin/main...HEAD: exit 0
```

The exact required `for f in server/tests/cleanservice-*.mjs; do node "$f" || exit 1; done`
was not run verbatim because it would execute
`server/tests/cleanservice-task256-explicit-new-version-runtime-dryrun.mjs`,
which is a real runtime harness and conflicts with Task 259's no-runtime
safety boundary. The loop was run over all mock-safe CleanService smokes and
explicitly skipped that runtime harness.

## 6. Safety Statement

No runtime rerun, `POST /api/v1/jobs`, live Mineru2Table query, DB GET/write,
MinIO read/write/list/stat, Docker/Compose operation, env/credential/model/sample
mutation, job-store read/write, cleanup/reset/rollback/reparse/re-AI, worker
activation, real DB apply, UAT, L3, pressure PASS, readiness, production online,
or go-live claim was performed.

The existing untracked `scratch/` directory was not modified.

## 7. Residual Risk

This is code/test-level mock-safe evidence only. A later controlled runtime
validation may be useful after Luceon accepts the product behavior, but Task 259
does not authorize or claim runtime success, Task 256 v3 artifact verification,
or real DB apply.
