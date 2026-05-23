# Luceon Review v2 - Task 255 Explicit New-Version Intent Policy

Review time: `2026-05-23T08:38:48+0800`

Reviewed branch:

```text
origin/lucode/TASK-20260523-080011-P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime
```

Reviewed remote HEAD:

```text
402a97e8917b731426efd763b619b6daf1831bc5
```

## Verdict

```text
ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_EVIDENCE_CORRECTION
```

Task 255 is accepted at code/test level. This acceptance is limited to the
mock-safe explicit new-version intent policy. It does not authorize any real
new-version runtime run.

## What Changed Since Return Review

The previous return review found that `intent=create-new-version` bypassed
incompatible metadata safety gates and reached `submitJob` for failed, version
mismatched, and one-sided metadata states.

The resubmitted runner now adds a pre-allocation explicit new-version
precondition gate:

- both task and material `toc-rebuild` records must exist;
- task assetVersion must equal material latestVersion;
- task and material must be completed;
- task jobId must exist;
- otherwise the runner returns `BLOCKED_EXISTING_TOC_REBUILD_METADATA` before
  allocator/submit/query/verifier/planner/apply.

Only after this precondition succeeds may the explicit new-version intent bypass
`CURRENT_CLEAN_MATERIAL_NOOP` and continue into mock/dry-run v3 planning.

## Review Evidence

Remote branch verification:

```text
git rev-parse origin/lucode/TASK-20260523-080011-P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime
=> 402a97e8917b731426efd763b619b6daf1831bc5
```

Changed files before Luceon merge/correction:

```text
A TaskAndReport/2026-05-23T08-00-11+0800_P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime_REPORT.md
D TaskAndReport/2026-05-23T08-27-39+0800_P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime_LUCEON_REVIEW.md
M TaskAndReport/TASK_TRACKING_LIST.md
M server/services/cleanservice/orchestration-runner.mjs
M server/tests/cleanservice-orchestration-runner-smoke.mjs
```

The deleted review file was a branch-basing artifact. Luceon preserved the
review file during merge and corrected the report/ledger HEAD evidence during
acceptance.

Focused runner smoke:

```text
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
=> ALL cleanservice orchestration runner smoke tests PASSED! (23/23)
```

CleanService regression smokes:

```text
for f in server/tests/cleanservice-*.mjs; do node "$f" || exit 1; done
=> PASS for all cleanservice smoke scripts
```

Type check:

```text
npx pnpm@10.4.1 exec tsc --noEmit
=> exit 0
```

Note: the review worktree initially lacked local dependencies, so Luceon linked
the main workspace `node_modules` into the temporary review worktree before
running the type check. No project files were changed by that review aid.

Whitespace:

```text
git diff --check origin/main..HEAD
=> no output
```

Independent reproduction of the returned defect:

```text
failed-existing-task-job BLOCKED_EXISTING_TOC_REBUILD_METADATA
version-mismatch BLOCKED_EXISTING_TOC_REBUILD_METADATA
material-only BLOCKED_EXISTING_TOC_REBUILD_METADATA
missing-job-id BLOCKED_EXISTING_TOC_REBUILD_METADATA
```

These probes used tripwire submit/query/verifier/apply functions. None were
called.

## Acceptance Boundary

Accepted:

- default aligned completed v2 remains `CURRENT_CLEAN_MATERIAL_NOOP`;
- explicit `create-new-version` with non-empty `newVersionReason` can bypass
  current-state noop only after completed/aligned existing metadata is proven;
- positive mock v3 dry-run path records bounded `newVersionIntent` audit;
- missing reason and unsupported intent block before dependencies;
- failed, mismatched, one-sided, and missing-jobId histories block before
  dependencies.

Not accepted or authorized:

- real `POST /api/v1/jobs`;
- real Mineru2Table polling;
- real MinIO reads/writes/lists/stats/deletes;
- real DB reads/writes/PATCH apply;
- Docker/Compose/env/credential change;
- LLM call;
- worker/scheduler activation;
- cleanup, reset, rollback, or nullification;
- UAT, L3, pressure PASS, production readiness, release readiness, or go-live.

## Next Planning Note

The next mainline decision is whether to authorize a separately scoped
controlled single-sample runtime validation for a new assetVersion. That would
be a new task and would require explicit Director authorization for any real
POST, MinIO output, LLM usage, and DB write boundary.
