# P0 MinerU Submit-Path 500 Circuit Breaker And Failure-State Handling Report

Report time: 2026-05-10T08:06:04+0800
Reporter: Lucode
Reviewer: Lucia
Task brief: `TaskAndReport/2026-05-10T07-51-29+0800_P0-MinerU-Submit-Path-500-Circuit-Breaker-And-Failure-State_TASK.md`
Branch: `lucode/p0-mineru-submit-500-circuit-breaker`
Base HEAD: `4899b30` (`Record pressure failure task heads`)
Implementation HEAD: `c43c2b1aa9a2a2be17ccc1601bbd83524d6c6812`
Report HEAD: `1225ece5df07a4a6947ef2d93d20e3adcffc8ed3` before final metadata amend; final pushed branch HEAD may be this commit's amend successor.
Status: completed for Lucia review.

## Scope

This work was based on Lucia Task 64.

The task asked Lucode to classify and address the release-blocking failure mode where MinerU `/health` remains healthy while `POST /tasks` returns HTTP 500, causing queued PDF tasks to cascade into `execution-failed`.

No production service restart, DB edit, MinIO edit, Docker volume operation, task/material/artifact/log/sample cleanup, new upload, secret change, model change, provider change, timeout-policy change, or production release-readiness declaration was performed.

## Failure Classification

The pressure-test failure is a MinerU submit-path dependency failure:

- MinerU `/health`: healthy.
- MinerU `POST /tasks`: HTTP 500.
- MinIO: healthy.
- Ollama: healthy and `qwen3.5:9b` chat probe passed.
- 24-PDF batch: `24/24` failed, `0` AI jobs.

Code inspection found the direct cascade cause:

- `server/services/mineru/local-adapter.mjs` converted HTTP non-2xx from `POST /tasks` into a generic `Error`.
- `server/services/queue/task-worker.mjs` treated that generic error as a task execution failure.
- Because the failed task did not have a `mineruTaskId`, it was written as `failed / execution-failed`.
- FIFO then moved to the next pending task, producing repeated submit failures instead of holding the queue behind a dependency-failed gate.

## Implementation Summary

Implemented the smallest code-level correction:

1. `local-adapter.mjs`
   - Extended `MineruSubmitUnreachableError` with `status`, `endpoint`, `dependencyBlocking`, and `retryAfterMs`.
   - Converted submit communication failure, submit HTTP 5xx, and missing task id into structured submit-path dependency errors instead of generic parser failures.

2. `task-worker.mjs`
   - Added an in-process MinerU submit circuit breaker.
   - When a dependency-blocking submit failure occurs, the current task remains `pending` with `stage='dependency-blocked'`.
   - The related Material is normalized to `status='processing'`, `mineruStatus='blocked'`, `aiStatus='pending'`, with `processingStage='dependency-blocked'`.
   - Subsequent local-MinerU PDF pending tasks are not submitted while the circuit is open.
   - Markdown passthrough tasks are not blocked by this circuit because they do not need MinerU `/tasks`.
   - Existing behavior for non-dependency `MineruSubmitUnreachableError` remains: bounded retries, then `submit-failed-retryable`.

3. `server/tests/mineru-submit-circuit-breaker-smoke.mjs`
   - Added focused coverage proving HTTP 500 keeps the first task pending/dependency-blocked, does not mark it failed, normalizes Material to blocked, and prevents submission of the next queued PDF task.

## Files Changed

- `server/services/mineru/local-adapter.mjs`
- `server/services/queue/task-worker.mjs`
- `server/tests/mineru-submit-circuit-breaker-smoke.mjs`
- `TaskAndReport/2026-05-10T07-51-29+0800_P0-MinerU-Submit-Path-500-Circuit-Breaker-And-Failure-State_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Test Evidence

| Command | Exit | Evidence |
| --- | ---: | --- |
| `node server/tests/mineru-submit-circuit-breaker-smoke.mjs` | 0 | `9 passed, 0 failed` |
| `node server/tests/mineru-submit-retryable-smoke.mjs` | 0 | `6 passed, 0 failed` |
| `node server/tests/mineru-no-resubmit-smoke.mjs` | 0 | `38 passed, 0 failed` |
| `node server/tests/mineru-metadata-status-cleanup-smoke.mjs` | 0 | `9 passed, 0 failed` |
| `node server/tests/dependency-health-smoke.mjs` | 0 | `40 passed, 0 failed` |
| `git diff --check` | 0 | no whitespace errors |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | passed |
| `npx pnpm@10.4.1 run build` | 0 | passed; Vite reported only the existing large-chunk warning |

## Production Read-Only Evidence

Read-only production checks were run against `http://localhost:8081` and `/Users/concm/prod_workspace/Luceon2026`.

Dependency health with submit probe:

```json
{
  "ok": false,
  "blocking": true,
  "dependencies": {
    "minio": { "ok": true },
    "mineru": {
      "ok": false,
      "healthOk": true,
      "error": "submit probe failed: HTTP 500: Internal Server Error",
      "submitProbe": {
        "enabled": true,
        "ok": false,
        "status": 500,
        "durationMs": 89,
        "error": "HTTP 500: Internal Server Error"
      }
    },
    "ollama": {
      "ok": true,
      "model": "qwen3.5:9b",
      "chatOk": true,
      "durationMs": 389
    }
  }
}
```

Active-task diagnostics:

```json
{
  "activeTask": null,
  "currentProcessingTask": null,
  "queuedTasks": [],
  "completedButNotIngestedTasks": [],
  "driftTasks": [],
  "submitRetryableTasks": [],
  "takeoverRequiredTasks": [],
  "historicalAiFailureTasks": []
}
```

Batch summary for prefix `task-177833`:

```json
{
  "batchCount": 24,
  "counts": {
    "failed/execution-failed": 23,
    "failed/mineru-processing": 1
  },
  "aiJobCount": 0
}
```

This production evidence was read-only. It confirms the current deployed runtime still has the original MinerU submit-path failure. The code change has not been deployed to production by this task.

## Skipped Checks

- No UAT upload was run because the task explicitly forbids new validation uploads without separate Director approval.
- No production rebuild, restart, deployment, or service operation was run because the task forbids production service restart and mutation.
- No DB/MinIO/task/material/artifact/log/sample mutation was performed.

## Risks And Residual Debt

- The circuit breaker is in-process. It prevents the active worker from cascading submissions while running, but a process restart clears the in-memory circuit. The next submit attempt will re-open it if MinerU `/tasks` still fails.
- The fix does not repair the already failed 24 pressure-test tasks. That would require a separate Lucia/Director-authorized recovery task.
- The code does not restart or heal MinerU itself. It only prevents Luceon from converting a dependency outage into many task failures.
- Production still shows MinerU submit probe HTTP 500. Release readiness remains blocked until Lucia decides whether to deploy this fix, repair/restart MinerU, and rerun a bounded validation.

## GitHub Sync

- Implementation branch: `lucode/p0-mineru-submit-500-circuit-breaker`
- Implementation commit: `c43c2b1aa9a2a2be17ccc1601bbd83524d6c6812`
- Report/list commit: `1225ece5df07a4a6947ef2d93d20e3adcffc8ed3` before final metadata amend.
- Branch push: pending at report creation.

## Review Required

Lucia review is required.

Production release readiness is not claimed.
