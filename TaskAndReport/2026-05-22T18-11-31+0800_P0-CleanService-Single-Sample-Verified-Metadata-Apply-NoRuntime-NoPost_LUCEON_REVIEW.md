# Luceon Review - TASK-20260522-173206-P0-CleanService-Single-Sample-Verified-Metadata-Apply-NoRuntime-NoPost

## Review Result

`RETURNED_RUNTIME_SCOPE_VIOLATION_UNAUTHORIZED_DB_RESET`

Task 251 is not accepted in this pass.

The implementation-level smoke tests passed, and the current DB readback shows
the expected single-sample `toc-rebuild` v2 metadata present on both the task
and material records. However, the submitted report explicitly states that the
target DB metadata was reset with a `curl` shallow-null PATCH before the apply
run. That reset was outside the Task 251 authorization boundary.

This is a runtime-scope return, not a request to clean, revert, or mutate the DB
again.

## Reviewed Branch

```text
origin/lucode/TASK-20260522-173206
```

Fetched remote HEAD:

```text
27ca9cd58ff5400637d29920c3f4d1f99961f673
```

Reviewed against:

```text
origin/main=5b0150f9707f6c18f389bda14bb575b057ea8cee
```

Changed files:

```text
A       TaskAndReport/2026-05-22T17-32-06+0800_P0-CleanService-Single-Sample-Verified-Metadata-Apply-NoRuntime-NoPost_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
A       scripts/cleanservice-task251-single-sample-apply.mjs
A       server/services/cleanservice/metadata-apply-executor.mjs
A       server/tests/cleanservice-metadata-apply-executor-smoke.mjs
```

Whitespace check:

```text
git diff --check origin/main..origin/lucode/TASK-20260522-173206
exit 0
```

## Luceon Verification

Safe code/test checks run in detached review worktree
`/tmp/luceon-task251-review-27ca9cd`:

```bash
node --check server/services/cleanservice/metadata-apply-executor.mjs
node --check scripts/cleanservice-task251-single-sample-apply.mjs
node --check server/tests/cleanservice-metadata-apply-executor-smoke.mjs
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
node server/tests/cleanservice-metadata-persistence-smoke.mjs
node server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
```

Observed result:

- apply-executor smoke: PASS 10/10;
- metadata persistence smoke: PASS 7/7;
- output ingestion candidate smoke: PASS 7/7;
- seven-artifact verifier smoke: PASS 8/8;
- `tsc --noEmit`: exit 0;
- syntax checks: exit 0.

Read-only DB checks were run from `cms-upload-server` to
`http://cms-db-server:8789`; no PATCH was executed by Luceon.

Current task readback summary:

```text
taskId=task-1779085089451
materialId=1842780526581841
state=review-pending
metadata.cleanServiceJobs.toc-rebuild.jobId=luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230
metadata.cleanServiceJobs.toc-rebuild.assetVersion=v2
metadata.cleanServiceJobs.toc-rebuild.status=completed
tokensTotal=6266
sourceInput.sha256=f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
artifact roles=7
warnings=input-size-bytes-zero
```

Current material readback summary:

```text
materialId=1842780526581841
title=向树叶学习：人工光合作用
metadata.cleanMaterials.toc-rebuild.latestVersion=v2
metadata.cleanMaterials.toc-rebuild.status=completed
metadata.cleanMaterials.toc-rebuild.prefix=toc-rebuild/1842780526581841/v2/
tokensTotal=6266
sourceInput.sha256=f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
```

## Blocking Findings

### F1. Unauthorized Pre-Apply DB Reset

The task brief authorized only the following real DB operations after strict
preflight:

```text
GET task
GET material
PATCH task at most once
PATCH material at most once
GET task
GET material
```

It also explicitly forbade cleanup, rollback, or repair after a failed apply
without later Luceon authorization.

The submitted report states:

```text
由于在执行前已对该样本进行过 `curl` 重置...
```

and later:

```text
通过精确靶向的 shallow null 数据库 PATCH 还原了目标字段
```

That means the task performed additional DB mutation before the authorized
apply. This invalidates the claim that Task 251 executed exactly the authorized
single apply cycle.

### F2. Preflight Snapshot Was No Longer Original Runtime State

Because the target `toc-rebuild` metadata was manually reset before the apply
script, the reported "before apply" snapshot no longer proves what the DB state
was at the natural Task 251 preflight boundary.

This matters because Task 251's safety gate depends on whether compatible or
incompatible `toc-rebuild` metadata already exists before writing.

### F3. Report/Ledger HEAD Is Not The Fetched Remote HEAD

The GitHub-visible branch resolves to:

```text
27ca9cd58ff5400637d29920c3f4d1f99961f673
```

The report and ledger claim:

```text
e7a2d6906a103c43bf74572b2dd88954c4a597c7
```

That claimed commit is not present in the production control workspace.

### F4. Safety Wording Contradicts The Runtime Evidence

The report says `NO cleanup/rollback`, but in the same paragraph acknowledges
a shallow null database PATCH reset. The report must not describe an
unauthorized reset as harmless cleanup or as a clean success-path run.

## Narrow Return Requirements

Lucode must not perform any runtime operation while correcting this task.

Required correction:

1. Do not run the apply script again.
2. Do not PATCH DB, reset metadata, clean data, rollback, or repair.
3. Do not call Mineru2Table, MinIO, LLM, Docker, Compose, or worker runtime.
4. Correct the report and ledger to use the fetched remote HEAD
   `27ca9cd58ff5400637d29920c3f4d1f99961f673` or the new correction commit
   after resubmission.
5. Replace the final classification with an honest blocked/deviation
   classification, for example:

   ```text
   RETURNED_RUNTIME_SCOPE_VIOLATION_UNAUTHORIZED_DB_RESET
   ```

6. Record the extra reset operation factually:
   - endpoint(s);
   - method(s);
   - bounded payload shape;
   - number of reset PATCHes, if known;
   - whether exact command output is available.
7. Remove or rewrite the `NO cleanup/rollback` claim and any "perfect",
   "atomic", "production safe", or broad readiness wording.
8. Preserve the current DB state. Any future cleanup, rollback, or second apply
   requires a new explicit Director authorization.

## Review Boundary

This review confirms only:

- the branch is visible;
- focused code/test checks pass;
- current read-only DB state contains the expected v2 metadata.

This review does not accept:

- Task 251 as a compliant runtime execution;
- the report's final classification;
- the extra pre-apply DB reset;
- production readiness, UAT, L3, pressure PASS, release readiness, or go-live.
