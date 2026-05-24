# Luceon Review - Task 259 Mock-Safe Runner Integration Gap Fix

Review time: 2026-05-24T11:40:53+0800

Task:

- `TASK-20260524-112801-P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime`

Reviewed branch:

```text
origin/lucode/TASK-20260524-112801-P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime@b4f4e3a24c9d1f5bceb1f74c2bf7f99810bb7186
```

Implementation commit named in report:

```text
f60e8d46efc88b94448715dde45d4153bfbff1bc
```

Verdict:

```text
CHANGES_REQUIRED_PROBE_POLICY_AND_DRY_RUN_TARGET_GATE
```

## Review Boundary

This review used the Lucode branch-handoff rule. `origin/main` still had Task
259 as `Next Actor=Lucode`, and the matching Lucode branch had branch-local
`Status=Lucode 已回报待 Luceon 审查` and `Next Actor=Luceon`.

No runtime rerun, `POST /api/v1/jobs`, live Mineru2Table query, DB/MinIO/Docker
operation, env/credential/model/sample mutation, Task 256 evidence rewrite,
worker/scheduler activation, real DB apply, UAT/L3/readiness/pressure PASS, or
go-live claim was performed.

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

Mock-safe checks in a detached review worktree:

```text
node --check server/services/cleanservice/output-verifier.mjs: exit 0
node --check server/services/cleanservice/metadata-summary.mjs: exit 0
node --check server/services/cleanservice/metadata-apply-executor.mjs: exit 0
node --check server/services/cleanservice/orchestration-runner.mjs: exit 0
node server/tests/cleanservice-output-verifier-smoke.mjs: exit 0, 9/9
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs: exit 0
node server/tests/cleanservice-orchestration-runner-smoke.mjs: exit 0, 24/24
```

`npx pnpm@10.4.1 exec tsc --noEmit` could not run in the detached review
worktree because `tsc` was unavailable there:

```text
ERR_PNPM_RECURSIVE_EXEC_FIRST_FAIL Command "tsc" not found
```

Lucode's report says `tsc --noEmit` passed in its workspace; Luceon did not
independently confirm that in this review worktree.

## Positive Findings

- The branch is correctly scoped to the allowed CleanService product/test files
  plus report and ledger.
- The product chain no longer requires top-level `job.provenance` when the
  seven artifact ObjectRefs include `artifacts.provenance`; the artifact reader
  path is exercised by mock tests.
- The branch carries bounded canonical/provenance job ID values into
  verification summaries instead of mutating parsed provenance to make the IDs
  look identical.
- The metadata apply executor now has a product-level path for explicit
  new-version dry-run over aligned completed previous metadata, with real apply
  still blocked in the covered test.

## Blocking Findings

### F1. `-probe` compatibility is default-on, not explicit

Task 259 required the `expectedJobId + "-probe"` compatibility to be accepted
only as a bounded, explicit policy.

The implementation accepts a `-probe` provenance job ID whenever
`expected.allowProbeJobIdSuffix` is anything other than `false`:

```text
server/services/cleanservice/output-verifier.mjs:42-44
```

That means callers that omit the option accept `-probe` by default. The new
output verifier test also demonstrates this: it calls
`verifyCleanServiceOutputArtifacts(..., { artifactReader, expected:
expectedOpts })` without setting `allowProbeJobIdSuffix`, and expects the
`-probe` ID to pass.

Evidence:

```text
server/tests/cleanservice-output-verifier-smoke.mjs:346-355
```

This does not satisfy the task's explicit-policy requirement. The safe fix is
to make the default strict, require an explicit opt-in such as
`allowProbeJobIdSuffix === true`, and add a negative test proving omitted/false
policy rejects `expectedJobId + "-probe"`.

### F2. Dry-run new-version conflict gate does not verify target version against intent

Task 259 required target mismatch to remain blocked. The new dry-run
compatibility gate checks previous version/jobId, completed previous metadata,
and `targetVersion !== previousVersion`, but it does not require
`plan.newVersionIntent.newAssetVersion` to equal the target patch version.

Evidence:

```text
server/services/cleanservice/metadata-apply-executor.mjs:73-93
```

As written, a malformed plan could carry `newVersionIntent.newAssetVersion=v3`
while the patch target is another different version, and still pass the
explicit new-version dry-run exception if the previous v2 metadata matches.

Required correction:

- require `plan.newVersionIntent.newAssetVersion === targetVersion`;
- add a negative smoke case where the intent target and patch target differ and
  the executor returns `BLOCKED_EXISTING_TOC_REBUILD_METADATA` or a stricter
  target-mismatch blocker;
- keep `allowRealApply=true` blocked for this conflict shape.

### F3. Report/ledger handoff omits the final branch HEAD

The report lists implementation commit
`f60e8d46efc88b94448715dde45d4153bfbff1bc`, then says the final report/ledger
commit is "the branch HEAD reported in the Lucode handoff". The branch-local
ledger similarly says "final HEAD in handoff".

Task 259 required the report to include the exact remote branch and full HEAD.
The reviewed remote branch HEAD is:

```text
b4f4e3a24c9d1f5bceb1f74c2bf7f99810bb7186
```

Required correction: update the report and branch-local ledger with the exact
final remote branch HEAD.

## Required Return

Lucode should perform a narrow correction on the same Task 259 scope:

1. Make `-probe` compatibility strict-by-default and explicit opt-in only.
2. Add negative tests for omitted/false `allowProbeJobIdSuffix`.
3. Add the dry-run target-version intent gate and a negative target-mismatch
   test.
4. Correct report/ledger final HEAD evidence.
5. Re-run mock-safe checks; do not run the Task 256 runtime harness.

Forbidden during correction:

- runtime rerun or any `POST /api/v1/jobs`;
- live Mineru2Table query;
- DB/MinIO/Docker/env/credential/model/sample mutation;
- Task 256 evidence rewrite;
- worker/scheduler activation;
- real DB apply;
- UAT/L3/readiness/pressure PASS/go-live claim.

## Acceptance Boundary

This branch is not accepted yet. The green focused smokes are useful, but they
currently prove a too-broad default `-probe` policy and miss one dry-run target
mismatch gate.
