# Luceon Review: Task 217 Host MinerU Log Sidecar Authoritative Progress Bridge (Acceptance)

**Task ID**: 217
**Review time**: 2026-05-18T13:03:03+0800
**Reviewed branch**: `lucode/task-217-resubmit-v2`
**Reviewed branch HEAD**: `c07bc81f6ca6a9623b9ec663f0fd97ed94e11274`
**Reviewed implementation commit**: `fd50b98f4daf781e3e7e9100906ba689d44574d9`
**Decision**: **ACCEPTED CODE/TEST LEVEL**

## Scope

This review inspected Lucode's v2 resubmission after Luceon's third-review DB-write race feedback. No production service, Docker/MinIO/DB volume, model, sample file, upload, submit-probe, pressure run, retry, reparse, or re-AI operation was performed.

The review was performed in a clean temporary worktree:

`/tmp/luceon-review-217-v2`

The local governance workspace remains dirty with unrelated OneDrive/conflict-copy documentation changes, so Luceon did not edit or overwrite that checkout.

## Review Result

Accepted at code/test level.

The prior blocker is resolved:

- `ParseTaskWorker.transition()` no longer spreads captured stale `task.metadata` when writing `progressEventKey`; the second progress-event PATCH now sends only `metadata.progressEventKey`.
- `processWithLocalMinerU()` and `resumeWithLocalMinerU()` now fetch current task metadata through `getLatestTask` and use `currentMetadata` when composing in-flight progress updates.
- `updateCompletionObservation()` no longer spreads stale captured task metadata into completion metadata updates.
- `reconcileLogObservations()` remains in the local adapter polling path and reconciles container observations against the current task metadata baseline.
- The new Test 35 covers the `transition()` progress-event-key non-rollback regression.

Luceon also reran the focused DB shallow-merge reproducer from the third review. The reproduced result is now:

```json
{
  "updateCount": 2,
  "finalObserver": "host-mineru-log-observer",
  "finalPercent": 70,
  "secondPatchKeys": ["progressEventKey"],
  "secondPatchObserver": null
}
```

This confirms the second PATCH no longer rolls a fresh sidecar observation back to stale container metadata.

## Checks Run

- `git ls-remote origin refs/heads/main refs/heads/lucode/task-217-resubmit-v2`
  - Remote `main`: `81688c9850fc0bdf0625b229869a080a5f9c5343`
  - Remote branch: `c07bc81f6ca6a9623b9ec663f0fd97ed94e11274`
- `git fetch origin refs/heads/main:refs/remotes/origin/main refs/heads/lucode/task-217-resubmit-v2:refs/remotes/origin/lucode/task-217-resubmit-v2`
  - Exit code: `0`
- `git worktree add --detach /tmp/luceon-review-217-v2 origin/lucode/task-217-resubmit-v2`
  - Exit code: `0`
- `node --check server/services/mineru/local-adapter.mjs`
  - Exit code: `0`
- `node --check server/services/queue/task-worker.mjs`
  - Exit code: `0`
- `node --check server/lib/ops-mineru-log-parser.mjs`
  - Exit code: `0`
- `node --check server/lib/progress-snapshot.mjs`
  - Exit code: `0`
- `node --check server/upload-server.mjs`
  - Exit code: `0`
- `node --check server/tests/mineru-log-progress-smoke.mjs`
  - Exit code: `0`
- `npx pnpm@10.4.1 install --frozen-lockfile`
  - Exit code: `0`
- Focused DB shallow-merge race reproducer
  - Exit code: `0`
  - Result: fresh sidecar observation preserved at `70%`; second PATCH only contains `progressEventKey`.
- `node server/tests/mineru-log-progress-smoke.mjs`
  - Exit code: `0`
  - Result: `156 passed, 0 failed`
- `npx pnpm@10.4.1 exec tsc --noEmit`
  - Exit code: `0`

## Luceon Integration Cleanup

`git diff --check origin/main...HEAD` initially found trailing whitespace in the report and Test 35 block. Luceon removed only trailing whitespace before acceptance. This was formatting cleanup only and did not change behavior.

Final `git diff --check` was rerun after cleanup and passed before merge/commit.

## Boundary

This closes Task 217 at code/test level only. It does not claim production deployment, production validation, pressure PASS, L2/L3 readiness, release readiness, production上线, or go-live.

Task 218 is no longer blocked by Task 217 and may proceed under its existing Figma-driven, no-functional-change scope.
