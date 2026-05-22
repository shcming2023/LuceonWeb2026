# Luceon Review v2: TASK-20260522-202101-P0-CleanService-Minimal-Orchestration-Runner-MockSafe-NoRuntime

## Verdict

Status: Not Accepted, Returned to Lucode

Classification: RETURNED_IMPLEMENTATION_GAPS

This review accepts that the Task 252 delivery branch is now GitHub-visible and
that the stated file scope is narrow. The implementation is still returned
because the orchestration runner has two mainline-blocking behavior gaps before
it can be used as the next rehearsal boundary.

## Review Basis

Luceon reviewed the GitHub-visible branch:

```text
origin/lucode/TASK-20260522-202101-P0-CleanService-Minimal-Orchestration-Runner-MockSafe-NoRuntime
```

Observed remote HEAD:

```text
77764d34a7e0c7455314a81500fa7e420899b090
```

Baseline:

```text
origin/main@8f8edd7ec6d2d86db1c0554b2a60f9b7350e0773
```

Diff scope:

```text
A       TaskAndReport/2026-05-22T20-21-01+0800_P0-CleanService-Minimal-Orchestration-Runner-MockSafe-NoRuntime_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
A       server/services/cleanservice/orchestration-runner.mjs
A       server/tests/cleanservice-orchestration-runner-smoke.mjs
```

`git diff --check origin/main..origin/lucode/...` passed with no output.

Focused checks run by Luceon in a detached review worktree:

```text
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
node server/tests/cleanservice-metadata-persistence-smoke.mjs
node server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-worker-shell-smoke.mjs
node server/tests/cleanservice-worker-factory-smoke.mjs
node server/tests/cleanservice-http-transport-smoke.mjs
node server/tests/cleanservice-payload-alignment-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
```

The checks above passed. In the detached review worktree, `node_modules` was
linked from the main Luceon workspace only to make the TypeScript binary
available. No runtime service, DB, MinIO, Docker, LLM, or HTTP target was used.

## Findings

### F1. Non-completed job statuses incorrectly proceed into artifact verification

Severity: P0

`orchestration-runner.mjs` only treats a failed query as terminal failure. Any
other returned job status, including `submitted`, `queued`, `running`, or
`processing`, proceeds into artifact verification.

This is unsafe for the mainline because a normal in-progress Mineru2Table job
would be interpreted as verifier or planner failure instead of a bounded
in-progress orchestration result. The next real rehearsal needs the runner to
stop before verifier/apply until the job is actually completed.

Luceon probe result:

```json
{
  "res": {
    "ok": false,
    "status": "BLOCKED_PLAN_NOT_APPLYABLE",
    "classification": "BLOCKED_PLAN_NOT_APPLYABLE",
    "reason": "missing-artifact-ref:flooded_content"
  },
  "verifyCalled": true,
  "applyCalled": false
}
```

Expected behavior: for non-terminal statuses, return a bounded in-progress
classification and prove `verifyCalled=false` and `applyCalled=false`.

### F2. Verifier expected raw input loses source hash and hardcodes one sample size

Severity: P0

The runner builds `verifierOptions.expected.rawInput` from the request object,
but it looks for `inputRef.source.sha256` or `inputRef.sha256`. The existing
canonical raw material adapter places the source hash on `inputRef.hash`, so
the verifier expectation loses the hash. The same block also hardcodes:

```js
sizeBytes: 31543
```

Luceon probe with a task carrying `sha256` and `size_bytes: 12345` captured this
raw input sent to the verifier:

```json
{
  "bucket": "eduassets-raw",
  "object": "mineru/mat-size/v1/content_list_v2.json",
  "sizeBytes": 31543
}
```

This weakens the seven-artifact verifier and couples the generic orchestration
runner to the Task 240 sample. The runner must propagate canonical Raw Material
traceability from the task/request without hardcoded sample constants.

### F3. Report and ledger still record the parent commit as delivery HEAD

Severity: P1

The true remote branch HEAD reviewed by Luceon is:

```text
77764d34a7e0c7455314a81500fa7e420899b090
```

The report and ledger record:

```text
02d841c9402de0678b22b350256a9dc88227a082
```

That hash is the parent of the visible delivery commit, not the final remote
HEAD. This is a control-plane evidence mismatch and must be corrected in the
next resubmission.

## Required Narrow Return

Lucode should keep the same Task 252 scope and avoid all runtime actions.

Required fixes:

1. Add explicit query-status branching:
   - `completed` may proceed to verifier;
   - known in-progress statuses such as `submitted`, `queued`, `pending`,
     `running`, and `processing` must return a bounded in-progress result;
   - `failed` remains a bounded failure;
   - unknown statuses should stop with a bounded unsupported-status
     classification rather than verifying artifacts.
2. Ensure no verifier, candidate, planner, or apply dependency is called for
   non-completed job states.
3. Build verifier `expected.rawInput` from canonical Raw Material evidence:
   - include `bucket`;
   - include `object`;
   - include `sha256` from `inputRef.hash`, `inputRef.source.sha256`, or the
     task raw material metadata;
   - include `sizeBytes` only when available from task raw material metadata or
     an injected mock fact. Do not hardcode `31543`.
4. Add focused smoke cases for:
   - non-completed job status returns in-progress and performs zero verifier and
     zero apply calls;
   - raw input hash and size are propagated without sample hardcoding.
5. Update the report and ledger to the final remote HEAD after the fix. Do not
   use parent commit hashes or vanity/self-referential SHA claims.

Allowed files remain the Task 252 narrow files:

```text
server/services/cleanservice/orchestration-runner.mjs
server/tests/cleanservice-orchestration-runner-smoke.mjs
TaskAndReport/2026-05-22T20-21-01+0800_P0-CleanService-Minimal-Orchestration-Runner-MockSafe-NoRuntime_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

If a tiny import/export correction in an already accepted CleanService helper is
truly required, stop and report it rather than widening silently.

## Boundary

This review did not execute any real POST, real Mineru2Table query, DB read or
write, MinIO operation, Docker/Compose command, LLM call, worker activation,
cleanup, reset, rollback, UAT, L3, pressure validation, release readiness, or
go-live validation.
