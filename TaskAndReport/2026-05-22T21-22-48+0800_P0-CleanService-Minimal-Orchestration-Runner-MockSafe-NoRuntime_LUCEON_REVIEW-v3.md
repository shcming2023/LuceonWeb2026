# Luceon Review v3: TASK-20260522-202101-P0-CleanService-Minimal-Orchestration-Runner-MockSafe-NoRuntime

## Verdict

Status: Accepted and Closed

Classification: CLOSED_CODE_TEST_ACCEPTED_MOCKSAFE_NORUNTIME

Task 252 is accepted at code/test level only. This means the mock-safe
orchestration runner can compose the accepted CleanService modules behind
dependency injection and dry-run apply. It does not mean CleanService is active
or that a real runtime orchestration has been authorized.

## Review Basis

Luceon reviewed and merged the GitHub-visible branch:

```text
origin/lucode/TASK-20260522-202101-P0-CleanService-Minimal-Orchestration-Runner-MockSafe-NoRuntime@d04af5890862ae3b19da5f18b62c4a94628ecfe6
```

Baseline before merge:

```text
origin/main@b8f16a434026891c98954b2e7675051384fe689d
```

The delivered diff scope was exactly the expected Task 252 scope:

```text
A       TaskAndReport/2026-05-22T20-21-01+0800_P0-CleanService-Minimal-Orchestration-Runner-MockSafe-NoRuntime_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
A       server/services/cleanservice/orchestration-runner.mjs
A       server/tests/cleanservice-orchestration-runner-smoke.mjs
```

During acceptance, Luceon performed a mechanical correction only:

- removed trailing whitespace in `server/services/cleanservice/orchestration-runner.mjs`;
- corrected the report and ledger from stale HEAD evidence to the true remote
  delivery HEAD;
- added this Review v3 and closed the ledger row.

No business logic was changed by Luceon during acceptance.

## Implementation Findings

Review v2 required two mainline fixes. Both are now satisfied.

### F1 Closed: Non-completed jobs now return before verifier/apply

The runner now branches on queried job status:

- `completed` proceeds to seven-artifact verification;
- `submitted`, `queued`, `pending`, `running`, and `processing` return
  `ORCHESTRATION_IN_PROGRESS`;
- `failed` returns a bounded failure;
- unsupported statuses return `UNSUPPORTED_STATUS`.

Luceon independent probe result:

```json
{
  "res": {
    "ok": true,
    "status": "ORCHESTRATION_IN_PROGRESS",
    "classification": "ORCHESTRATION_IN_PROGRESS",
    "reason": "Job is currently in active state: processing"
  },
  "verifyCalled": false,
  "applyCalled": false
}
```

### F2 Closed: Raw input traceability is dynamic, not sample-hardcoded

The runner no longer hardcodes `sizeBytes: 31543`. It now derives raw input
evidence from the canonical request/task metadata and supports injected mock
facts for tests.

Luceon independent probe with a non-sample size produced:

```json
{
  "bucket": "eduassets-raw",
  "object": "mineru/mat-size/v1/content_list_v2.json",
  "sha256": "source-sha",
  "sizeBytes": 12345
}
```

## Verification

Luceon ran these checks in a detached review worktree using only in-memory
mocks and local source code:

```text
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
for f in server/tests/cleanservice-*.mjs; do node "$f" || exit 1; done
npx pnpm@10.4.1 exec tsc --noEmit
```

Results:

```text
cleanservice-orchestration-runner-smoke.mjs: PASS 11/11
all server/tests/cleanservice-*.mjs: PASS
tsc --noEmit: PASS
```

The first remote delivery still had trailing whitespace in the new runner
source. Luceon removed it during acceptance and then verified:

```text
git diff --check: PASS
```

## Acceptance Boundary

Accepted:

- mock-safe orchestration composition;
- dependency-injected submit/query/verifier/planner/apply path;
- disabled and already-applied no-op behavior;
- non-completed job early return;
- dynamic raw input traceability;
- dry-run apply enforcement;
- no reset/cleanup/rollback/null metadata path in the runner;
- bounded result shape without full artifact bodies.

Not accepted or claimed:

- real Mineru2Table dispatch;
- real Mineru2Table status query;
- real MinIO artifact reads;
- real DB reads or writes;
- worker scheduler activation;
- upload-server wiring;
- UAT, L3, pressure PASS, release readiness, production readiness, or go-live.

## Recommended Next Step

The next mainline task should be a separately authorized read-only/mock
rehearsal around a concrete existing task/material pair. It should load current
task/material metadata as inputs only if the Director authorizes that DB read,
or use recorded fixture snapshots if DB reads remain out of scope.
