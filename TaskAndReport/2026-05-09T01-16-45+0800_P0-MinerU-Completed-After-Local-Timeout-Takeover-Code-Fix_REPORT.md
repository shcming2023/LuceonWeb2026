# Lucode Completion Report: P0 MinerU Completed After Local Timeout Takeover Code Fix

- Task ID: `TASK-20260509-004345-P0-MinerU-Completed-After-Local-Timeout-Takeover-Code-Fix`
- Based on Lucia task brief: `TaskAndReport/2026-05-09T00-43-45+0800_P0-MinerU-Completed-After-Local-Timeout-Takeover-Code-Fix_TASK.md`
- Actor: Lucode
- Report time: `2026-05-09T01:16:45+0800`
- Branch: `lucode/p0-mineru-completed-after-local-timeout-takeover`
- Base HEAD before implementation: `2d24392097514fbd48e499cb7fda9fb7d6548dcf`
- Implementation HEAD: `7f9d0037058ed492f9f74332f43f6158df7a71cf`
- Status: completed, awaiting Lucia review

## Files Changed

- `server/services/queue/task-worker.mjs`
- `server/tests/mineru-no-resubmit-smoke.mjs`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-09T01-16-45+0800_P0-MinerU-Completed-After-Local-Timeout-Takeover-Code-Fix_REPORT.md`

## Implementation Summary

Implemented a code-level takeover path for local MinerU tasks that already have a `mineruTaskId`, previously timed out locally, and later report `completed` through the MinerU API.

- `recoverStaleRunningTasks()` now immediately adjudicates local-timeout tasks with `localTimeoutOccurred=true`, even when `updatedAt` is fresh, instead of waiting for the 60s stale threshold.
- `resumeMineruTask()` now performs a worker-side API status recheck when `mineruResumer` throws `MineruStillProcessingError`.
- If the recheck reports a completed MinerU status, the worker transitions the Luceon task to `result-fetching`, fetches the existing MinerU result through `mineruResumer`, stores parsed artifacts through the normal resume completion path, and only then creates the downstream AI metadata job.
- The takeover does not call `mineruProcessor` or POST `/tasks`; it reuses the existing `mineruTaskId`.
- If completed-result fetching or ingestion fails during takeover, the task fails explicitly at `result-fetch-failed` with diagnostic metadata. No skeleton fallback or silent degradation was added.

## No-Resubmission Evidence

Focused smoke coverage added:

- Test 7: `localTimeoutOccurred=true`, fresh `updatedAt`, existing `mineruTaskId`, MinerU API `completed`.
  - Asserted no POST `/tasks`.
  - Asserted existing result resume was called.
  - Asserted task entered `result-fetching`.
  - Asserted task reached `ai-pending`.
- Test 8: `resumeMineruTask()` first receives `MineruStillProcessingError`, then the worker rechecks MinerU API and sees `completed`.
  - Asserted no POST `/tasks`.
  - Asserted `mineruResumer` was retried once for the existing result.
  - Asserted task entered `result-fetching`.
  - Asserted task reached `ai-pending`.

The existing no-resubmit smoke total increased to `36 passed, 0 failed`.

## Commands Run

- `git status --short --branch`
  - Exit code: 0
  - Output before implementation: `## main...origin/main`
- `git fetch origin`
  - Exit code: 0
- `git pull --ff-only origin main`
  - Exit code: 0
  - Output: `Already up to date.`
- `git switch -c lucode/p0-mineru-completed-after-local-timeout-takeover`
  - Exit code: 0
  - Output: `Switched to a new branch 'lucode/p0-mineru-completed-after-local-timeout-takeover'`
- `node server/tests/mineru-no-resubmit-smoke.mjs`
  - Exit code: 0
  - Output summary: `=== Results: 36 passed, 0 failed ===`
- `node server/tests/mineru-timeout-adjudication-smoke.mjs`
  - Exit code: 0
  - Output summary: `=== Results: 59 passed, 0 failed ===`
- `git diff --check`
  - Exit code: 0
- `npx pnpm@10.4.1 exec tsc --noEmit`
  - Exit code: 0
- `npx pnpm@10.4.1 run build`
  - Exit code: 0
  - Output summary: `✓ built in 1.37s`
  - Note: Vite emitted the existing large chunk warning for `dist/assets/index-BAE1e2pH.js` at `698.05 kB`; build still passed.
- `git commit -m "fix mineru completed timeout takeover"`
  - Exit code: 0
  - Implementation commit: `7f9d0037058ed492f9f74332f43f6158df7a71cf`

## Skipped Checks

- No production recovery, production upload, production task mutation, DB mutation, MinIO mutation, Docker operation, service restart/rebuild/redeploy, model/config/secret/override change, or sample mutation was run.
- This was intentional and required by the Lucia task brief. Production task `task-1778249434820` and material `mat-1778249419780` were not touched.

## Risk / Residual Debt

- The code-level fix is validated by focused smokes and build checks only. It does not recover the already-stuck production task.
- A separate Director-authorized production recovery or redeploy/validation task is still required if Lucia wants `task-1778249434820` to be reconciled in production.
- Existing AI job creation test environment network warnings remain non-blocking in these smokes; parsed completion still reaches `ai-pending` before AI job creation attempts.

## Lucia Review Required

Yes. Lucia should review the branch diff and smoke evidence, then decide whether to accept the code-level correction and whether a separate Director-authorized production recovery task is needed.
