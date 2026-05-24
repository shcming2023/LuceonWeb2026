# Luceon Review v2 - Task 259 Mock-Safe Runner Integration Gap Fix

Review time: 2026-05-24T12:39:29+0800

Task:

```text
TASK-20260524-112801-P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime
```

Reviewed branch:

```text
origin/lucode/TASK-20260524-112801-P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime@507906bd517a37f563038a02ba9b0abe6f70bfaf
```

Verdict:

```text
ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_CONTROL_PLANE_HEAD_CORRECTION
```

## Review Boundary

This review used the Lucode branch-handoff rule. `origin/main` still carried
Task 259 as `Next Actor=Lucode`, while the matching Lucode branch had
branch-local `Status=Lucode 已回报待 Luceon 审查` and `Next Actor=Luceon`.

Acceptance is code/test-level and mock-safe only. It does not accept Task 256 as
runtime success, does not verify Task 256 v3 artifacts in production, and does
not authorize or claim a real DB apply.

No runtime rerun, `POST /api/v1/jobs`, live Mineru2Table query, DB/MinIO/Docker
operation, env/credential/model/sample mutation, Task 256 evidence rewrite,
worker/scheduler activation, real DB apply, UAT/L3/readiness/pressure PASS,
readiness, production online, or go-live claim was performed.

## Branch Evidence

Commands:

```bash
git diff --name-status origin/main...origin/lucode/TASK-20260524-112801-P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime
git diff --check origin/main...origin/lucode/TASK-20260524-112801-P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime
```

Observed name-status:

```text
A       TaskAndReport/2026-05-24T11-28-01+0800_P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
M       server/services/cleanservice/metadata-apply-executor.mjs
M       server/services/cleanservice/metadata-summary.mjs
M       server/services/cleanservice/orchestration-runner.mjs
M       server/services/cleanservice/output-verifier.mjs
M       server/tests/cleanservice-metadata-apply-executor-smoke.mjs
M       server/tests/cleanservice-orchestration-runner-smoke.mjs
M       server/tests/cleanservice-output-verifier-smoke.mjs
```

`git diff --check` exited `0` with no output.

## Checks Run By Luceon

Review worktree:

```text
/tmp/luceon-task259-review.D4cOxt
```

Checks:

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
node server/tests/cleanservice-output-verifier-smoke.mjs: exit 0, 9/9
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs: exit 0
node server/tests/cleanservice-orchestration-runner-smoke.mjs: exit 0, 24/24
mock-safe cleanservice-*.mjs loop excluding Task 256 runtime harness: exit 0
npx pnpm@10.4.1 exec tsc --noEmit: exit 0
```

The full `cleanservice-*.mjs` loop was intentionally not run verbatim because
`server/tests/cleanservice-task256-explicit-new-version-runtime-dryrun.mjs` is a
runtime harness and conflicts with Task 259's no-runtime boundary. Luceon ran
the loop over all mock-safe CleanService smokes and explicitly skipped that
runtime harness.

For `tsc --noEmit`, the detached review worktree used the main workspace
`node_modules` via a temporary symlink so the check could run without package
installation or dependency mutation.

## Accepted Findings

The return blockers from the first review are closed:

- `verifyCleanServiceOutputArtifacts()` now rejects `expectedJobId + "-probe"`
  by default and also rejects it when `allowProbeJobIdSuffix: false`; only
  explicit `allowProbeJobIdSuffix: true` accepts the suffix.
- The accepted suffix path preserves `canonicalJobId`, `provenanceJobId`,
  `provenanceJobIdPolicy=accepted-probe-suffix`, and warning
  `provenance-job-id-probe-suffix-accepted` without mutating parsed provenance.
- The runner can process a completed live-shaped job response with seven
  artifact refs and no top-level `job.provenance`, reading `provenance.json`
  through the injected artifact reader.
- The explicit new-version dry-run exception requires
  `plan.newVersionIntent.newAssetVersion` to match the target patch version,
  completed aligned previous task/material metadata, a previous jobId, and
  `allowRealApply=false`.
- Intent target mismatch and real apply over the same existing-metadata
  conflict remain blocked.

## Luceon Control-Plane Correction

Lucode's branch report and branch-local ledger left the final correction branch
HEAD as a handoff placeholder. The reviewed remote branch HEAD is:

```text
507906bd517a37f563038a02ba9b0abe6f70bfaf
```

Because product behavior and review checks passed, Luceon corrected the report
and ledger HEAD evidence during acceptance instead of returning the task again.

## Acceptance Boundary

Task 259 is accepted only as mock-safe product code/test evidence for the three
integration gaps:

1. live provenance artifact shape;
2. explicit `job_id -probe` compatibility policy;
3. explicit new-version apply dry-run conflict semantics.

This acceptance does not authorize runtime rerun, DB apply, MinIO operation,
Docker/Compose operation, cleanup/reset/rollback, worker activation, UAT, L3,
pressure PASS, release readiness, production readiness, production online, or
go-live.
