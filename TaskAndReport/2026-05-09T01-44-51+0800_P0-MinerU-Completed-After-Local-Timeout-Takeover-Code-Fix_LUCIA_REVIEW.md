# Lucia Review: P0 MinerU Completed After Local Timeout Takeover Code Fix

- Task ID: `TASK-20260509-004345-P0-MinerU-Completed-After-Local-Timeout-Takeover-Code-Fix`
- Review time: `2026-05-09T01:44:51+0800`
- Reviewed report: `TaskAndReport/2026-05-09T01-16-45+0800_P0-MinerU-Completed-After-Local-Timeout-Takeover-Code-Fix_REPORT.md`
- Reviewed branch: `lucode/p0-mineru-completed-after-local-timeout-takeover`
- Reviewed implementation commit: `7f9d0037058ed492f9f74332f43f6158df7a71cf`
- Decision: `RETURNED_FOR_CORRECTION`

## Decision

Lucia returns the implementation for correction.

The implementation direction is mostly correct: it avoids resubmitting MinerU, detects completed MinerU API state after local timeout, and routes toward `result-fetching` and existing result ingestion. However, the final completion metadata path has a correctness gap that can preserve or reintroduce stale `metadata.mineruStatus=processing` on the Luceon task after the takeover completes.

This is too close to the original failure mode to accept code-level.

## Independent Checks Run

Lucia ran:

```bash
node server/tests/mineru-no-resubmit-smoke.mjs
node server/tests/mineru-timeout-adjudication-smoke.mjs
git diff --check
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Observed results:

- `mineru-no-resubmit-smoke`: `36 passed, 0 failed`
- `mineru-timeout-adjudication-smoke`: `59 passed, 0 failed`
- `git diff --check`: passed
- `tsc --noEmit`: passed
- production build: passed; existing Vite large-chunk warning remained non-blocking

## Blocking Finding

In `server/services/queue/task-worker.mjs`, `completeResumedMineruResult()` builds the final task metadata from the stale in-memory `task.metadata` and does not explicitly set:

```js
mineruStatus: 'completed'
```

The normal non-resume completion path does set `metadata.mineruStatus='completed'`. The resume/takeover completion path should preserve that invariant.

This matters most for the new timeout-completed takeover path:

1. The task can enter takeover with `metadata.mineruStatus='processing'` and `localTimeoutOccurred=true`.
2. `transitionToMineruResultFetching()` writes `mineruStatus='completed'` to DB.
3. `completeResumedMineruResult()` then uses the older in-memory `task.metadata` and can overwrite final task metadata without `mineruStatus='completed'`.

Current tests assert `Material.mineruStatus === 'completed'`, but they do not assert the final task metadata status. That leaves a gap exactly where the production issue was observed: task-level MinerU state drift.

## Required Correction

Lucode must revise the implementation so the resumed/takeover completion path explicitly writes task metadata `mineruStatus: 'completed'` in the final `ai-pending` / parsed-complete transition.

Add focused smoke assertions covering:

- local-timeout completed takeover final task metadata includes `mineruStatus='completed'`;
- resume `MineruStillProcessingError` then completed takeover final task metadata includes `mineruStatus='completed'`;
- no POST `/tasks` occurs in either path;
- parsed artifact ingestion and AI job ordering remains unchanged.

## Boundary

Do not mutate production task `task-1778249434820`, material `mat-1778249419780`, production DB/MinIO/logs/samples/secrets/override/Docker/services, or create production uploads/retries/reparse.

Production recovery remains unauthorized.
