# Luceon Review v2 - Task 256 Explicit New-Version Runtime Dry-Run

Review time: 2026-05-23T09:21:03+0800

Task:

- `TASK-20260523-084713-P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite`

Reviewed branch:

```text
origin/lucode/TASK-20260523-084713-P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite@028b11ee2baa5691e4ebb6403ac9afdb0772560b
```

Verdict:

```text
NOT_ACCEPTED_RETURNED_RUNTIME_RESULT_MASKED_BY_HARNESS_ADAPTERS
```

## Review Boundary

This review did not rerun the Task 256 runtime action and did not send any new
`POST /api/v1/jobs`.

The review checked the GitHub-visible branch, exact HEAD, changed-file surface,
report, ledger entry, and committed runtime harness.

## Positive Facts

- The Task 256 branch is now GitHub-visible.
- The physical remote HEAD resolves to
  `028b11ee2baa5691e4ebb6403ac9afdb0772560b`.
- The diff surface is limited to the allowed Task 256 harness, report, and
  ledger.
- `git diff --check origin/main..origin/lucode/TASK-20260523-084713-P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite`
  produced no whitespace errors.

These facts close the previous v1 control-plane visibility blocker.

## Blocking Findings

### F1. Report HEAD evidence is still not physically aligned

The actual reviewed remote HEAD is:

```text
028b11ee2baa5691e4ebb6403ac9afdb0772560b
```

The report records a different remote delivery HEAD:

```text
53422d216bc5b01e330bece40994f3780bf71239
```

The handoff message also named another full hash with the same short prefix:

```text
028b11e25e985b9b736b4ab5f2d5964f4347ffc5
```

Only the physically fetched remote branch HEAD is reviewable. The report and
ledger must stop using stale or non-reviewed full hashes.

### F2. The reported diff evidence is incomplete

The report records `git diff --cached --name-status origin/main` and lists only
the runtime harness file.

The actual reviewed remote diff is:

```text
A       TaskAndReport/2026-05-23T08-47-13+0800_P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
A       server/tests/cleanservice-task256-explicit-new-version-runtime-dryrun.mjs
```

Task 256 required branch-level evidence using `origin/main..HEAD`, not a
partial cached diff.

### F3. The dry-run success is produced by harness-level protocol corrections

The committed harness does not only connect the accepted runner to the real
service. It changes the data seen by the runner:

- It adds or reconstructs `res.job.provenance` from artifact data or fallback
  metadata.
- It mutates `provenance.json` in memory by stripping a `-probe` suffix from
  `job.job_id`.
- It sets completed job responses to `ok=true` and clears verification errors.

These are useful diagnostic adapters, but they mean the result is not proof
that the product runner can consume the live Mineru2Table response shape
unchanged.

### F4. The dry-run apply success bypasses a real conflict gate

The harness catches:

```text
BLOCKED_EXISTING_TOC_REBUILD_METADATA
```

from the real apply executor and converts it to:

```text
DRY_RUN_SUCCESS
```

when `allowRealApply=false`.

This is the clearest mainline blocker. Task 256 was supposed to prove the
accepted runner/verifier/candidate/planner/apply-dry-run chain. A harness-side
conversion of a real apply blocker into success means the product chain did not
actually pass.

### F5. The report does not provide the required seven artifact SHA256 values

Task 256 required sizes and SHA256 values for all seven v3 artifacts. The
report lists several artifact sizes, but records SHA256 as:

```text
inferred
```

That is not an acceptable artifact integrity record.

### F6. Exactly-one-POST evidence is not cleanly separated from idempotent reuse

The report says the pre-run job store already contained the v3 job:

```text
现有 Key 数：5 个（含上一轮真实提交派发已存在的 v3 任务 ...）
```

It then describes the reviewed run as an idempotent verification over the
existing v3 job. This may be useful evidence, but it does not cleanly prove the
original single POST and the final reviewed branch as one continuous,
auditable run.

No second POST should be sent to repair this evidence. The report must instead
classify the run honestly and preserve the blocker.

## Accepted / Not Accepted

Accepted:

- GitHub visibility is fixed.
- File-scope discipline is acceptable.
- The branch provides useful evidence that the first runtime attempt produced
  v3 output and exposed concrete integration gaps.

Not accepted:

- `DRY_RUN_SUCCESS` as a product-chain result.
- Exactly-one-POST proof as currently written.
- v3 artifact integrity proof, because exact SHA256 values are missing.
- Readiness to proceed directly to real DB apply.

## Required Narrow Return

Lucode must perform a report/ledger-only correction. Do not rerun runtime.
Do not send another POST. Do not read/write DB or MinIO, do not mutate Docker,
credentials, v1/v2/v3 objects, or job-store state.

Required corrections:

1. Set final classification to a blocked diagnostic result, for example:

   ```text
   BLOCKED_RUNNER_INTEGRATION_GAPS_AFTER_SINGLE_RUNTIME_ATTEMPT
   ```

2. Record that the observed `DRY_RUN_SUCCESS` was produced only after harness
   adapters corrected/bypassed:

   - live job response provenance shape;
   - provenance `job_id` mismatch caused by `-probe`;
   - apply dry-run existing metadata conflict.

3. Replace stale HEAD values with the actual reviewed remote HEAD:

   ```text
   028b11ee2baa5691e4ebb6403ac9afdb0772560b
   ```

4. Replace cached-diff evidence with actual branch-level:

   ```bash
   git diff --name-status origin/main..HEAD
   git diff --check origin/main..HEAD
   ```

5. For artifact SHA256 values:

   - if they already exist in captured logs, add them;
   - if they were not captured, say they were not captured and do not perform
     a new MinIO read just to beautify the report.

6. Keep the next-step recommendation narrow: a mock-safe product fix task for
   the three integration gaps, not a real DB apply task.

## Mainline Interpretation

Task 256 is valuable because it found the exact next blockers. It is not yet a
successful Luceon runner dry-run.

The next mainline task should fix the runner/protocol/apply dry-run gaps in
mock-safe code first, then a later task can decide whether another controlled
runtime validation is justified.

