# Luceon Review: Task 217 Host MinerU Log Sidecar Authoritative Progress Bridge (Third Review)

**Task ID**: 217  
**Review time**: 2026-05-18T12:48:41+0800  
**Reviewed branch**: `lucode/task-217-resubmit`  
**Reviewed HEAD**: `b0c5a227d4f5f6f44af2ad2be4a4ec8bc767ac57`  
**Decision**: **NOT ACCEPTED / RETURN TO LUCODE**

## Scope

This review inspected Lucode's force-pushed resubmission after Luceon's second-review race-condition feedback. No production service, data, MinIO, Docker volume, model, sample file, upload, submit-probe, pressure run, retry, reparse, or re-AI operation was performed.

The review was performed in a clean temporary worktree at:

`/tmp/luceon-review-217-third`

The local governance workspace remains dirty with unrelated OneDrive/conflict-copy documentation changes, so Luceon did not edit or overwrite it.

## Checks Run

- `git ls-remote origin refs/heads/lucode/task-217-resubmit refs/heads/main`
  - Confirmed remote `lucode/task-217-resubmit` HEAD: `b0c5a227d4f5f6f44af2ad2be4a4ec8bc767ac57`
  - Confirmed remote `main` HEAD: `9f6d166bb1c1b55c9854521009d6013b923facc4`
- `git fetch origin refs/heads/main:refs/remotes/origin/main +refs/heads/lucode/task-217-resubmit:refs/remotes/origin/lucode/task-217-resubmit`
  - Exit code: `0`
  - Note: force refspec was required because Lucode force-pushed the branch.
- `git worktree add --detach /tmp/luceon-review-217-third origin/lucode/task-217-resubmit`
  - Exit code: `0`
- `git diff --check origin/main...HEAD`
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
- `node server/tests/mineru-log-progress-smoke.mjs`
  - Exit code: `0`
  - Result: `153 passed, 0 failed`
- `npx pnpm@10.4.1 exec tsc --noEmit`
  - Exit code: `0`

## Findings

### P1: `transition()` still reintroduces stale metadata after a successful fresh progress update

Lucode added `getLatestTask` into the local MinerU adapter polling path, and the primary `processWithLocalMinerU` progress metadata now spreads `currentMetadata` before writing `mineruObservedProgress`.

However, the same progress update then flows through `ParseTaskWorker.transition()`. After the first `updateTaskWithRetry(task.id, update, ...)` succeeds, the `progress-update` event-dedup path writes `progressEventKey` in a second PATCH:

`server/services/queue/task-worker.mjs:2452-2455`

```js
await this.updateTaskWithRetry(task.id, {
  metadata: { ...(task.metadata || {}), progressEventKey: semanticKey }
}, { enqueueOnFailure: true });
```

That `task.metadata` is still the stale closure object captured when the worker picked up the task. Because `server/db-server.mjs` performs a shallow metadata merge, the second PATCH can overwrite the first PATCH's freshly reconciled `metadata.mineruObservedProgress` with the old in-memory value.

This means the race condition from the second review is still reproducible: a fresh sidecar/DB observation can be written by the main update and then immediately rolled back by the event-key update in the same `transition()` call.

Luceon ran a focused in-memory reproducer against `ParseTaskWorker.transition()` using db-server-style shallow metadata merge:

```json
{
  "updateCount": 2,
  "finalObserver": "container-mounted-log",
  "finalPercent": 20,
  "secondPatchObserver": "container-mounted-log"
}
```

The reproducer started with DB metadata containing a fresher `host-mineru-log-observer` observation at `70%`, then called `transition()` with that fresh metadata. The second `progressEventKey` PATCH carried the stale `container-mounted-log` observation from the captured task and rolled DB state back to `20%`.

This is still a task-blocking defect because Task 217's core purpose is to prevent stale worker/container state from overwriting authoritative sidecar progress.

### P1: resume path still spreads stale task metadata in its progress update body

In `resumeWithLocalMinerU`, the callback fetches `currentMetadata` and reconciles observations against it:

`server/services/mineru/local-adapter.mjs:649-672`

But the actual `updateProgress` metadata body still starts from the captured `task.metadata`:

`server/services/mineru/local-adapter.mjs:682-696`

```js
metadata: {
  ...(task.metadata || {}),
  mineruTaskId,
  mineruStatus,
  ...
}
```

If parsing fails, returns no observation, or the status branch does not attach an observation, this can still send stale metadata into DB. The process path was updated to spread `currentMetadata`; the resume path needs the same freshness boundary or an equivalent safer merge strategy.

### P2: report and ledger evidence remain stale/mismatched

The fetched branch HEAD is:

`b0c5a227d4f5f6f44af2ad2be4a4ec8bc767ac57`

But the branch report still states:

`TaskAndReport/2026-05-17T17-56-39+0800_P1-Host-MinerU-Log-Sidecar-Authoritative-Progress-Bridge_REPORT.md:9`

```md
- **提交 HEAD**: `209920d` (修复二审发现的 race condition)
```

The branch ledger row also still carries earlier not-accepted evidence text rather than the current third resubmission state. This must be corrected before acceptance because Luceon/Lucode coordination depends on GitHub task/report evidence matching the submitted branch.

## Required Correction

Lucode should resubmit Task 217 with all of the following:

1. Remove the remaining stale metadata overwrite in `ParseTaskWorker.transition()`'s `progressEventKey` write path. The second PATCH must not include stale `task.metadata.mineruObservedProgress` or other stale metadata keys.
2. Apply the same freshness rule to resume/completion-related progress metadata writes where captured `task.metadata` can still overwrite fresher DB state, or document and test a safer equivalent.
3. Add a focused race-covering test that simulates db-server-style shallow metadata merge and proves that a fresh sidecar `mineruObservedProgress` cannot be rolled back by the worker's later progress-event-key update.
4. Update the report and ledger to the actual resubmitted branch HEAD and current review state.

## Review Boundary

The submitted code passes syntax, smoke, and TypeScript checks, but this is not sufficient for acceptance because the core race condition remains reachable. No production validation, deployment, or runtime mutation was authorized or performed.

Task 218 remains behind Task 217 until this task is accepted or explicitly cleared by the user.
