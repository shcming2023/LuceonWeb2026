# Luceon Review - Task 255 Explicit New-Version Intent Policy

Review time: `2026-05-23T08:27:39+0800`

Reviewed branch:

```text
origin/lucode/TASK-20260523-080011-P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime
```

Remote HEAD verified by Luceon:

```text
a9315a1c1077f021c70e216eee1ac931a68fabc2
```

## Verdict

```text
RETURNED
```

Task 255 is not accepted. The implementation proves the happy mock
new-version path, but it weakens the existing metadata safety gate in precisely
the cases the task brief required to keep blocked or report as ambiguous.

## Evidence Checked

Luceon verified the remote branch and changed file set:

```text
git rev-parse origin/lucode/TASK-20260523-080011-P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime
=> a9315a1c1077f021c70e216eee1ac931a68fabc2

git diff --name-status origin/main..origin/lucode/TASK-20260523-080011-P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime
=> A TaskAndReport/2026-05-23T08-00-11+0800_P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime_REPORT.md
=> M TaskAndReport/TASK_TRACKING_LIST.md
=> M server/services/cleanservice/orchestration-runner.mjs
=> M server/tests/cleanservice-orchestration-runner-smoke.mjs

git diff --check origin/main..origin/lucode/TASK-20260523-080011-P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime
=> no output
```

Luceon also created a detached review worktree at:

```text
/tmp/luceon-review-255
```

and ran an independent in-memory reproduction against the submitted runner.
For `intent: 'create-new-version'` with a non-empty reason, these three cases
all reached the injected `submitJob` tripwire instead of returning a bounded
pre-submit block:

```text
failed-existing-task-job threw SUBMIT_CALLED
version-mismatch threw SUBMIT_CALLED
material-only threw SUBMIT_CALLED
```

## Findings

### F1 - Explicit new-version intent bypasses incompatible metadata safety gates

Severity: P0

In `server/services/cleanservice/orchestration-runner.mjs`, `hasNewVersionIntent`
skips both the current-state noop branch and the incompatible existing metadata
check:

```js
if ((existingTaskJob || existingMaterialJob) && !hasNewVersionIntent) {
  ...
}
```

The task brief required the explicit new-version path to proceed only when the
previous task/material metadata is completed and aligned. It also required
failed existing task jobs, version mismatches, missing `jobId`, and one-sided
metadata to remain blocked or to stop as `BLOCKED_NEW_VERSION_POLICY_AMBIGUITY`.

The submitted code instead allows those cases to continue into submit planning.
This is a mainline safety bug because it turns an explicit rerun flag into a
broad bypass of the existing metadata guard.

Required correction:

- before bypassing `CURRENT_CLEAN_MATERIAL_NOOP`, validate that both task and
  material `toc-rebuild` records exist;
- validate aligned version, completed state, and existing `jobId`;
- if that precondition is not met, return a bounded pre-submit block such as
  `BLOCKED_EXISTING_TOC_REBUILD_METADATA` or
  `BLOCKED_NEW_VERSION_POLICY_AMBIGUITY`;
- do not call submit/query/verifier/candidate/planner/apply in those blocked
  paths.

### F2 - Focused smoke coverage misses the negative policy cases

Severity: P0

The submitted smoke tests cover:

- aligned completed v2 + explicit reason => v3 dry-run;
- missing reason => `BLOCKED_NEW_VERSION_REASON_REQUIRED`;
- unsupported intent => `BLOCKED_UNSUPPORTED_CLEANSERVICE_INTENT`.

They do not cover the task brief's most important safety cases under explicit
new-version intent:

- failed existing task job + intent;
- task/material version mismatch + intent;
- one-sided metadata + intent;
- missing task `jobId` + intent.

Required correction:

Add focused tripwire tests proving all of the above return bounded pre-submit
blocks and never call `submitJob`, `queryJob`, verifier, planner, or apply.

### F3 - Control-plane evidence is not physically aligned

Severity: P1

The remote branch HEAD verified by Luceon is:

```text
a9315a1c1077f021c70e216eee1ac931a68fabc2
```

However the submitted report records:

```text
HEAD Commit Hash: 8889ee898b04a8bca2eb8488e0b62e49c8d5069d
```

and the branch ledger row also records `8889ee...` while wording the result as
"Code/test level accepted" before Luceon review. This must be corrected during
resubmission.

Required correction:

- update report and ledger to the final GitHub-visible HEAD after the code
  correction;
- do not describe the work as accepted before Luceon accepts it;
- keep status as `Ready for luceon Review` only after resubmitting.

### F4 - Report wording drifts into UAT framing

Severity: P2

The report's next-step section uses "UAT 级 Success-path Rerun" language. Task
255 is a mock-safe code/test task and must not frame the next step as UAT.

Required correction:

- replace UAT wording with "controlled single-sample runtime validation
  planning" or similar bounded development-verification language.

## Narrow Return Requirements

Lucode should make only the following corrections:

1. Add the explicit new-version precondition gate for existing metadata:
   completed, aligned, both sides present, and `jobId` present.
2. Add focused tripwire tests for failed existing job, version mismatch,
   one-sided metadata, and missing `jobId` under `create-new-version`.
3. Correct report/ledger HEAD evidence and remove premature accepted/UAT
   wording.
4. Re-run the Task 255 required checks:

```bash
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
for f in server/tests/cleanservice-*.mjs; do node "$f" || exit 1; done
npx pnpm@10.4.1 exec tsc --noEmit
git diff --check origin/main..HEAD
git diff --name-status origin/main..HEAD
```

No real POST, DB, MinIO, Mineru2Table, Docker, `.env`, credential, LLM, worker
activation, cleanup, reset, rollback, UAT, L3, readiness, or go-live action is
authorized.
