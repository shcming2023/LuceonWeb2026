# Task 265 Luceon Review: targetAssetVersion v4 Mock-Safe Implementation

Review time: 2026-05-24T15:36:15+0800

Decision: `RETURNED_TO_LUCODE_SCOPE_FIX_REQUIRED`

## Reviewed Branch

```text
origin/lucode/TASK-20260524-151650-P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite
remote HEAD = 6b35e796a8043d37ab1d983d0062d66071dc7451
merge base with origin/main = 2116432c5661a2e7186021e8f4f12e4500472c26
origin/main at review = 2116432c5661a2e7186021e8f4f12e4500472c26
```

Three-dot diff commands used:

```text
git diff --name-status origin/main...origin/lucode/TASK-20260524-151650-P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite
git diff --check origin/main...origin/lucode/TASK-20260524-151650-P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite
```

`git diff --check` passed with no output.

## Findings

### 1. Blocker: direct request planner accepts target v4 without the required existing-version gates

`server/services/cleanservice/cleanservice-worker.mjs:55-65` only rejects
`targetAssetVersion` when `intent !== "create-new-version"`. It then calls
`resolveAssetVersion()` with `previousAssetVersion` defaulting to `null`.

`server/services/cleanservice/asset-version.mjs:60-105` treats a missing
`previousAssetVersion` as acceptable for target resolution. That means an
exported request-planning entry can produce a `targetAssetVersion: "v4"`
request for a fresh/no-history task, without completed aligned `v2` task and
material metadata, without a previous job id, and without the full task-brief
target validity preconditions.

Independent Luceon repro on the reviewed branch:

```text
buildCleanServiceJobRequest(fresh raw-material task, {
  serviceName: "toc-rebuild",
  intent: "create-new-version",
  newVersionReason: "probe",
  targetAssetVersion: "v4"
})
=> direct-builder-fresh-target-allowed v4 luceon-task-direct-1-toc-rebuild-v4
```

This violates the Task 265 implementation requirement that
`targetAssetVersion` is valid only with explicit new-version intent, non-empty
reason, completed/aligned existing task and material clean metadata, previous
job id, numeric/order/default gates, and no active duplicate clean job.

The runner path has stronger preconditions and the focused runner tests pass,
but acceptance cannot rely on only one caller being safe while the exported
request planner admits the unsafe target shape.

### 2. Control-plane evidence issue: report omits the exact final remote HEAD

The branch report states that the final pushed branch HEAD cannot be embedded in
the report itself. Luceon verified the remote HEAD as
`6b35e796a8043d37ab1d983d0062d66071dc7451`, but the task brief required exact
branch/full HEAD evidence in the report. This is not the main product blocker,
but the revised handoff should put the exact remote HEAD in the branch-local
ledger and report or a supplemental report.

## Checks Run By Luceon

Review worktree:

```text
/tmp/luceon-review-task265.1JqUu7
```

Commands and results:

```text
git status --short --branch
# exit 0, detached review worktree clean

git diff --check origin/main...HEAD
# exit 0

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
# exit 0, PASS 28/28

node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
# exit 0, PASS

npx pnpm@10.4.1 exec tsc --noEmit
# initial temp worktree attempt failed because node_modules was absent there;
# rerun with a temporary node_modules symlink to the main workspace dependency tree exited 0
```

## Scope And Safety Review

Changed files stayed within the allowed task surface. Luceon observed no
evidence of runtime POST, submit-probe, live Mineru2Table query, live DB/MinIO
operation, Docker/Compose mutation, job-store edit, worker activation, DB apply,
UAT, L3, pressure PASS, readiness, production online, or go-live claim.

The branch is not merged.

## Required Lucode Fix

Revise the implementation so `targetAssetVersion` cannot produce a request from
any exported request-planning path unless the task-brief gates are satisfied.
At minimum, cover the direct request planner or shared helper with tests that
block:

- fresh/no-history target v4;
- missing non-empty `newVersionReason`;
- missing previous job id;
- active duplicate clean job;
- missing or misaligned material clean metadata where that path has enough
  context to decide.

If a low-level request builder cannot safely verify material-side history, keep
`targetAssetVersion` out of that low-level API and pass only a previously
resolved version from the gated orchestration path.

The revised report/handoff must include the exact remote branch and full HEAD.

## Review Boundary

This is a return for scoped correction, not a runtime verdict. No runtime `v4`,
physical `v4` artifacts, DB metadata apply, CleanService activation,
readiness, L3, pressure, or go-live status is accepted or authorized.
