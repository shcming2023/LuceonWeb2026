# Task 261 Report: CleanService Existing v3 No-POST Reconciliation And SourceInput Compatibility

Report time: 2026-05-24T14:21:23+0800

## 1. Branch And HEAD

Branch:

```text
lucode/TASK-20260524-135419-P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime
```

Base HEAD at task sync:

```text
865499d230c490e4917f73c96c6fe2dc11125fdb
```

`origin/main` at task sync:

```text
470ed948775bb9529b94157e8bf8eb09cc501358
```

Final pushed branch HEAD is reported in the Lucode handoff message after commit
and push. This report is part of that final control-plane commit, so it cannot
embed its own final commit hash without changing it.

Return-review baseline:

```text
origin/main@470ed948775bb9529b94157e8bf8eb09cc501358
```

The branch was rebased onto the return-review mainline before the narrow
correction.

## 2. Changed Files

```text
M       server/services/cleanservice/raw-material-adapter.mjs
M       server/services/cleanservice/cleanservice-worker.mjs
M       server/services/cleanservice/orchestration-runner.mjs
M       server/tests/cleanservice-raw-material-adapter-smoke.mjs
M       server/tests/cleanservice-orchestration-runner-smoke.mjs
A       TaskAndReport/2026-05-24T13-54-19+0800_P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
```

The pre-existing untracked `scratch/` directory was not modified.

## 3. Implemented Product Behavior

Source-input compatibility:

- `raw-material-adapter` keeps `metadata.rawMaterial.mineru.contentListV2` as
  the first source of truth.
- When canonical rawMaterial is absent, it can fall back only to completed
  `metadata.cleanServiceJobs[serviceName].sourceInput`.
- The fallback requires `bucket=eduassets-raw`, object path
  `mineru/<materialId>/vN/content_list_v2.json`, and a present SHA256.
- Fallback size is propagated when available.
- Source-input object paths are validated by splitting path segments and doing
  literal segment comparisons, not by interpolating material/version values into
  a dynamic regex.
- Version segments are constrained to numeric `vN` shape.
- Legacy parsed evidence alone still routes through the existing skipped-policy
  behavior and is not promoted into a source input.

Existing v3 no-POST reconciliation:

- `runCleanServiceTocRebuildOnce()` now supports explicit
  `config.reconcileExistingJob === true` with an injected completed-job fixture.
- That path bypasses `submitJob` and `queryJob`, then continues through the
  product verifier, candidate builder, persistence planner, and dry-run apply.
- The runner now passes `allowProbeJobIdSuffix` to the verifier only when
  `config.allowProbeJobIdSuffix === true`.
- Existing v3 fixture coverage preserves canonical job ID vs provenance
  `-probe` job ID, records the accepted probe policy, and reaches
  `DRY_RUN_SUCCESS` only under explicit probe-suffix policy.

Preserved behavior:

- Default/false probe-suffix policy rejects `-probe`.
- Current applied v2 noop behavior remains covered by existing runner tests.
- Explicit new-version mismatch, failed history, one-sided history, and missing
  jobId blockers remain covered by existing runner tests.
- Real apply over incompatible existing metadata remains covered by the apply
  executor smoke.

## 4. Focused Tests Added

`server/tests/cleanservice-raw-material-adapter-smoke.mjs`:

- canonical rawMaterial wins over completed-job sourceInput fallback;
- completed-job sourceInput fallback works when rawMaterial is absent;
- non-completed fallback is rejected;
- fallback without SHA256 is rejected;
- fallback object path for the wrong material is rejected.
- material IDs containing regex metacharacters are matched literally
  (`mat.260` accepts only `mineru/mat.260/...`, not `mineru/matX260/...`);
- non-numeric version segments such as `vABC` are rejected.

`server/tests/cleanservice-orchestration-runner-smoke.mjs`:

- existing v3 no-POST reconciliation with sourceInput fallback, injected
  completed job, no submit/query calls, explicit probe-suffix policy, and dry-run
  success;
- existing v3 no-POST reconciliation with implicit/default probe policy rejects
  provenance `-probe` and does not apply.

## 5. Checks

```text
git status --short --branch: exit 0
git fetch origin --prune --tags: exit 0
git checkout main: exit 0
git pull --ff-only origin main: exit 0
git rev-parse HEAD origin/main: exit 0
git diff --name-status origin/main...HEAD: exit 0
git diff --check origin/main...HEAD: exit 0
node --check server/services/cleanservice/raw-material-adapter.mjs && node --check server/services/cleanservice/cleanservice-worker.mjs && node --check server/services/cleanservice/orchestration-runner.mjs && node --check server/tests/cleanservice-raw-material-adapter-smoke.mjs && node --check server/tests/cleanservice-orchestration-runner-smoke.mjs: exit 0
node server/tests/cleanservice-raw-material-adapter-smoke.mjs: exit 0
node server/tests/cleanservice-orchestration-runner-smoke.mjs: exit 0, 26/26
node server/tests/cleanservice-output-verifier-smoke.mjs: exit 0, 9/9
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs: exit 0
mock-safe cleanservice-*.mjs loop excluding Task 256 runtime harness: exit 0
npx pnpm@10.4.1 exec tsc --noEmit: exit 0
```

Return-fix focused checks:

```text
node --check server/services/cleanservice/raw-material-adapter.mjs && node --check server/tests/cleanservice-raw-material-adapter-smoke.mjs: exit 0
node server/tests/cleanservice-raw-material-adapter-smoke.mjs: exit 0
node server/tests/cleanservice-orchestration-runner-smoke.mjs: exit 0, 26/26
mock-safe cleanservice-*.mjs loop excluding Task 256 runtime harness: exit 0
npx pnpm@10.4.1 exec tsc --noEmit: exit 0
```

The exact all-file loop was intentionally run with
`server/tests/cleanservice-task256-explicit-new-version-runtime-dryrun.mjs`
excluded because Task 261 explicitly forbids modifying or running that runtime
harness.

## 6. Safety Statement

No runtime POST, `POST /api/v1/jobs:from-storage`, live Mineru2Table query, DB
read/write/PATCH/POST/PUT/DELETE, MinIO read/write/list/stat/delete/copy/move,
job-store write/edit, Docker/Compose operation, env/credential/model/sample
mutation, worker/scheduler activation, cleanup/reset/rollback/repair/reparse,
real DB apply, UAT, L3, pressure PASS, readiness, production online, or go-live
claim was performed.

## 7. Residual Risk

This is mock-safe code/test evidence only. It proves the product path can
consume the accepted sourceInput shape and reconcile existing v3 fixture output
without POST, but it does not claim runtime success, live v3 validation, DB
apply, L3, pressure PASS, readiness, or go-live.
