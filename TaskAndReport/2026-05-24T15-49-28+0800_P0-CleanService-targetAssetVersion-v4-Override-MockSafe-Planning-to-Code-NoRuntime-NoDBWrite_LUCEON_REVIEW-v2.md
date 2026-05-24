# Task 265 Luceon Review v2: targetAssetVersion v4 Mock-Safe Implementation

Review time: 2026-05-24T15:49:28+0800

Decision: `ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_INTEGRATION_AND_HEAD_CORRECTION`

## Reviewed Branch

```text
origin/lucode/TASK-20260524-151650-P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite
accepted remote HEAD = 6daf22990d11fa3e90b98086d36671e2fa825ae6
merge base with origin/main = f5e7747d6d5858f733f88bd44a10926988b93f30
origin/main at review start = f5e7747d6d5858f733f88bd44a10926988b93f30
```

Luceon fast-forwarded `main` to the accepted branch before writing this review.

## Scope Result

Accepted at mock-safe code/test level.

The previous return blocker is closed:

- the exported request builder rejects raw `targetAssetVersion` without a
  gated `resolvedAssetVersion` plan;
- the runner resolves the target only after explicit create-new-version intent,
  non-empty reason, completed/aligned task and material history, previous job
  id, numeric/order/default gates, and no active duplicate;
- the direct builder no longer turns a fresh/no-history raw-material task into
  a `v4` request from naked `targetAssetVersion`;
- the positive `v2 -> explicit target v4` path keeps request job id, sink,
  verifier expected asset version, persistence plan, and audit aligned on `v4`;
- default behavior without `targetAssetVersion` remains the normal allocator
  path.

The changed files stayed inside the task-approved source, test, report, and
ledger surface.

## Luceon Control-Plane Correction

Lucode's report still omits the exact final remote HEAD and includes an
incorrect full baseline SHA string:

```text
reported baseline = f5e774724938cab64475a56862a4ce5601e2f22f
actual review baseline = f5e7747d6d5858f733f88bd44a10926988b93f30
accepted branch HEAD = 6daf22990d11fa3e90b98086d36671e2fa825ae6
```

Because the code/test result is acceptable and the exact remote facts are
independently verified above, Luceon corrects this evidence in this review and
in the task ledger instead of returning the task again.

## Luceon Checks

Commands and results:

```text
git status --short --branch
# exit 0, main clean before review

git fetch origin --prune --tags
git pull --ff-only origin main
# exit 0, main already up to date

git diff --name-status origin/main...origin/lucode/TASK-20260524-151650-P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite
# exit 0; only approved TaskAndReport, CleanService source, and focused tests changed

git diff --check origin/main...origin/lucode/TASK-20260524-151650-P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite
# exit 0, no output

node --check server/services/cleanservice/asset-version.mjs
node --check server/services/cleanservice/cleanservice-worker.mjs
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/services/cleanservice/metadata-apply-executor.mjs
node --check server/tests/cleanservice-asset-version-smoke.mjs
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs
node --check server/tests/cleanservice-metadata-apply-executor-smoke.mjs
# exit 0

node server/tests/cleanservice-asset-version-smoke.mjs
# exit 0, PASS

node server/tests/cleanservice-orchestration-runner-smoke.mjs
# exit 0, PASS 29/29

node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
# exit 0, PASS

npx pnpm@10.4.1 exec tsc --noEmit
# exit 0 in detached review worktree using a temporary node_modules symlink to
# the existing main-workspace dependency tree; no repo file was changed
```

Additional Luceon negative probe:

```text
buildCleanServiceJobRequest(fresh raw-material task, {
  serviceName: "toc-rebuild",
  intent: "create-new-version",
  newVersionReason: "probe",
  targetAssetVersion: "v4"
})
=> throws target-asset-version-requires-resolved-version-plan
```

Extra mock-safe CleanService test loop passed for `server/tests/cleanservice-*.mjs`
with `server/tests/cleanservice-task256-explicit-new-version-runtime-dryrun.mjs`
skipped because that harness is runtime-oriented and this task forbids runtime
operations.

## Safety Boundary

No runtime POST, submit-probe, live Mineru2Table query, live DB/MinIO/job-store
read, DB/MinIO write, Docker/Compose mutation, job-store edit, worker
activation, cleanup, retry, reparse, real DB apply, UAT, L3, pressure PASS,
readiness, production online, or go-live claim is accepted or authorized.

Acceptance means only:

```text
Mock-safe code/test support for task-scoped targetAssetVersion v4 is accepted.
```

It does not prove or authorize runtime `v4`, physical `v4` artifacts, DB
metadata apply, CleanService activation, or any production/readiness milestone.
