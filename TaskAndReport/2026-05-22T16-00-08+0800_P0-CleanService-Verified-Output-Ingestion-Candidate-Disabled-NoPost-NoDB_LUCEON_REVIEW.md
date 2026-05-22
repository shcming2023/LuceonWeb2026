# Task 249 Luceon Review

Review time: 2026-05-22T16:00:08+0800

Reviewed branch:

```text
origin/lucode/TASK-20260522-150902@f8a3f7c2ba0cfa19020e27ca9a47b3163944724d
```

Baseline:

```text
origin/main@3cc55362d53cc0feb0c5fdb295c8ab3c3ea7365e
```

## Verdict

Task 249 is not accepted yet.

The implementation is directionally close and the focused smoke passes, but it
misses the mainline ingestion contract in one important place: a real
Task-248-verifier-to-candidate path can lose the source input ObjectRef/hash.
There are also small but hard control-plane blockers in whitespace and
HEAD evidence.

Final classification:

```text
CHANGES_REQUIRED_SOURCE_INPUT_CONTRACT_AND_CONTROL_PLANE_EVIDENCE
```

This review does not merge the implementation branch and does not accept any
runtime, DB persistence, worker activation, POST dispatch, MinIO mutation, UAT,
L3, readiness, pressure PASS, release, or go-live claim.

## Findings

### F1. Source input traceability can be lost in the real Task 248 -> Task 249 path

Severity: P0

Evidence:

- `server/services/cleanservice/metadata-summary.mjs:105-117`

`buildVerifiedCleanOutputMetadataCandidate(...)` derives `sourceInput` from
`job.provenance`. In the real path this task is meant to prepare, the job
response normally carries artifact ObjectRefs, while `provenance.json` is read
inside Task 248's verifier. The accepted Task 248 verifier currently returns
`inputSizeBytes` and warnings, but it does not return
`sourceInput.bucket/object/sha256`.

Luceon reproduced the gap in the review worktree by calling the candidate
builder with a Task-245-shaped job containing seven artifact refs and a
Task-248-shaped verification result. The candidate returned:

```json
{
  "sourceInput": {
    "bucket": null,
    "object": null,
    "sha256": null,
    "sizeBytes": 31543
  }
}
```

This violates Task 249's mainline objective: the candidate must preserve bounded
source traceability before any later DB persistence task. Do not rely on a test
fixture that injects `job.provenance` unless the real upstream contract also
guarantees that field.

Required correction:

1. Make the candidate builder consume source input from a verifier-provided
   bounded summary, such as `verification.sourceInput`, when present.
2. Keep a backward-compatible fallback to `job.provenance.inputs[0]` /
   `job.provenance.input` only as a fallback.
3. If the accepted Task 248 verifier result still lacks the needed
   `sourceInput` contract, follow Task 249's stop rule and report
   `BLOCKED_VERIFIER_CONTRACT_GAP`; do not silently build a persistable
   candidate with null source bucket/object/hash.
4. Add a focused negative/real-shape test where the job has no inline
   `provenance`, the verification result supplies source input, and the
   candidate preserves bucket/object/sha256/size.

### F2. Prompt/completion token details are dropped

Severity: P1

Evidence:

- `server/services/cleanservice/metadata-summary.mjs:41-46`
- `server/tests/cleanservice-output-ingestion-candidate-smoke.mjs:41-48`

Task 249 requires preserving prompt tokens and completion tokens when available.
The current task summary stores only `tokensTotal`, while the smoke fixture also
does not assert `prompt=6212` and `completion=54` from the Task 245 evidence.

Required correction:

- Preserve `tokensPrompt` and `tokensCompletion` or an equivalent bounded token
  summary when the input job or verification summary includes them.
- Add focused assertions that prompt, completion, and total token counts survive
  into the candidate summary.

### F3. `git diff --check` fails due to trailing whitespace

Severity: P1

Evidence:

```text
server/tests/cleanservice-output-ingestion-candidate-smoke.mjs:191: trailing whitespace.
server/tests/cleanservice-output-ingestion-candidate-smoke.mjs:220: trailing whitespace.
```

This directly fails Task 249's required check.

Required correction:

- Remove the trailing whitespace and rerun:

```bash
git diff --check origin/main..HEAD
```

### F4. Report and ledger HEAD evidence do not match the physical branch

Severity: P1

Evidence:

- Actual reviewed remote HEAD:

```text
f8a3f7c2ba0cfa19020e27ca9a47b3163944724d
```

- Report records:

```text
TaskAndReport/2026-05-22T15-09-02+0800_P0-CleanService-Verified-Output-Ingestion-Candidate-Disabled-NoPost-NoDB_REPORT.md:7
HEAD Commit: b49215e478546114eb7ce2e90f23d0618037a346 (to be committed by Lucode)
```

- Ledger records the same stale/non-final branch evidence at
  `TaskAndReport/TASK_TRACKING_LIST.md:255`.

Required correction:

- Update report and ledger to the actual final pushed remote HEAD after the
  implementation and checks are complete.
- Keep report link in the report/review column and branch/HEAD in the
  branch/HEAD column.

## Checks Performed By Luceon

```bash
git fetch origin lucode/TASK-20260522-150902 --prune
git rev-parse origin/lucode/TASK-20260522-150902
git merge-base origin/main origin/lucode/TASK-20260522-150902
git diff --name-status origin/main..origin/lucode/TASK-20260522-150902
git diff --check origin/main..origin/lucode/TASK-20260522-150902
node server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
```

Observed results:

- remote branch exists;
- diff changes only Task-249-allowed file categories;
- focused ingestion smoke passed 4/4;
- Task 248 output verifier smoke passed 8/8;
- `git diff --check` failed on trailing whitespace;
- Luceon independent real-shape reproduction failed because `sourceInput`
  bucket/object/sha256 became `null`.

## Narrow Return Requirements

Lucode should make only the following changes:

1. Correct the source-input contract so a verifier-shaped result can provide
   source bucket/object/sha256/size to the candidate without relying on
   `job.provenance`.
2. Preserve prompt and completion token details when available.
3. Add or adjust focused smoke coverage for:
   - real-shape job with no inline `job.provenance`;
   - verifier-provided `sourceInput`;
   - prompt/completion/total token preservation;
   - non-persistable failure remains blocked.
4. Remove trailing whitespace and rerun `git diff --check origin/main..HEAD`.
5. Correct report and ledger final HEAD evidence after the final push.

Do not widen scope into:

- `output-verifier.mjs` changes unless reporting `BLOCKED_VERIFIER_CONTRACT_GAP`
  is unavoidable under the task stop rule;
- worker/protocol/transport/upload-server wiring;
- DB writes;
- real POST dispatch;
- real MinIO reads/writes;
- Docker/env/package changes;
- external Mineru2Table changes;
- UAT/L3/readiness/pressure PASS/go-live claims.
