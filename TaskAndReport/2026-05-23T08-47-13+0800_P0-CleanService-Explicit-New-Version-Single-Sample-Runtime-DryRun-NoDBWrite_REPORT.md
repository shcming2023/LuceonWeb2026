# Task 256 Report: CleanService Explicit New-Version Runtime Dry-Run Correction

Report updated: 2026-05-24T11:06:00+0800

## 1. Final Classification

```text
BLOCKED_RUNNER_INTEGRATION_GAPS_AFTER_SINGLE_RUNTIME_ATTEMPT
```

This is a report/ledger-only correction after Luceon Review v2.

No runtime rerun was performed for this correction. No second
`POST /api/v1/jobs` was sent. No DB, MinIO, Docker, env, credential, v1/v2/v3
object, or Mineru2Table job-store mutation was performed.

## 2. Branch And HEAD Evidence

Working branch:

```text
lucode/TASK-20260523-084713-P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite
```

Luceon-reviewed remote runtime evidence HEAD:

```text
028b11ee2baa5691e4ebb6403ac9afdb0772560b
```

This correction branch HEAD:

```text
branch HEAD as pushed; exact full hash is reported in the Lucode handoff and reviewable with git rev-parse HEAD
```

The previous report incorrectly recorded stale or non-reviewed HEAD values.
The reviewable runtime evidence is the GitHub-visible remote branch at
`028b11ee2baa5691e4ebb6403ac9afdb0772560b`.

## 3. Corrected Diff Evidence

The correct branch-level evidence is `origin/main..HEAD`, not a partial cached
diff.

Command:

```bash
git diff --name-status origin/main..HEAD
```

Observed correction-scope output:

```text
A       TaskAndReport/2026-05-23T08-47-13+0800_P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
A       server/tests/cleanservice-task256-explicit-new-version-runtime-dryrun.mjs
```

Command:

```bash
git diff --check origin/main..HEAD
```

Exit code: `0`

Output:

```text
(no output)
```

## 4. Corrected Runtime Interpretation

The single Task 256 runtime attempt remains useful diagnostic evidence, but it
is not accepted as a clean product-chain `DRY_RUN_SUCCESS`.

The observed `DRY_RUN_SUCCESS` was produced only after harness-level adapters
corrected or bypassed integration gaps:

1. Live job response provenance shape was reconstructed or promoted in the
   harness before the product verifier consumed it.
2. `provenance.json` `job_id` was normalized in memory by stripping the
   `-probe` suffix before verification.
3. The real apply dry-run blocker
   `BLOCKED_EXISTING_TOC_REBUILD_METADATA` was caught by the harness and
   converted into `DRY_RUN_SUCCESS` when `allowRealApply=false`.

These adapters identify the next product gaps. They do not prove that the
accepted runner/verifier/candidate/planner/apply-dry-run chain can consume the
live Mineru2Table response unchanged.

## 5. Artifact Integrity Evidence

The previous report listed v3 artifact sizes but recorded SHA256 values as
`inferred`.

No captured log evidence with exact SHA256 values was found in the report.
Per Luceon Review v2, this correction did not perform a new MinIO read to
beautify the evidence. Therefore the v3 seven-artifact integrity record remains
incomplete for Task 256 acceptance.

## 6. Exactly-One-POST Evidence Boundary

The previous report mixed the original runtime attempt with later idempotent
reuse of an already existing v3 job:

```text
existing key count: 5, including the v3 task job
```

This is not clean enough to prove exactly one POST and final reviewed branch
state as one continuous auditable run. No second POST was sent to repair this
evidence. The correct conclusion is blocked diagnostic evidence, not runtime
success.

## 7. Checks Performed For This Correction

```text
git status --short --branch
git fetch origin --prune --tags
git checkout main
git pull --ff-only origin main
git checkout lucode/TASK-20260523-084713-P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite
git merge --no-edit main
git diff --name-status origin/main..HEAD
git diff --check origin/main..HEAD
```

Check results:

```text
git fetch origin --prune --tags: exit 0
git pull --ff-only origin main: exit 0
git merge --no-edit main: initially conflicted only in TaskAndReport/TASK_TRACKING_LIST.md; conflict manually resolved
git diff --check origin/main..HEAD: exit 0
```

Focused runtime or product tests were not rerun because Luceon Review v2
required a report/ledger-only correction and explicitly forbade another runtime
run, POST, DB/MinIO/Docker mutation, or evidence-beautifying read.

## 8. Residual Risks And Debt

- Product runner integration must handle the live Mineru2Table provenance
  response shape without harness reconstruction.
- Product verifier or upstream provenance output must resolve the `job_id`
  `-probe` mismatch without harness mutation.
- Apply dry-run semantics must handle explicit new-version metadata planning
  without converting a real `BLOCKED_EXISTING_TOC_REBUILD_METADATA` conflict in
  the harness.
- v3 artifact SHA256 values were not captured in acceptable evidence during
  the runtime attempt.
- Exactly-one-POST evidence is not cleanly separated from idempotent reuse in
  the prior report trail.

## 9. Recommended Next Step

Recommend a narrow mock-safe product fix task for the three integration gaps:

```text
live provenance shape -> provenance job_id policy -> explicit new-version apply dry-run conflict semantics
```

Do not proceed directly to real DB apply from Task 256 evidence.

Do not rerun runtime or send another POST unless a future task explicitly
reauthorizes a new controlled runtime validation.
