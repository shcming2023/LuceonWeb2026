# Director Decision Required: P0 Sample 3 Production Recovery Authorization

- Created: 2026-05-09T02:42:47+0800
- Owner: Director
- Recorder: Lucia
- Related diagnosis: TASK-20260508-234438-P0-Sample3-MinerU-Long-Processing-Read-Only-Diagnosis
- Related accepted code fix: TASK-20260509-004345-P0-MinerU-Completed-After-Local-Timeout-Takeover-Code-Fix

## Decision Question

Should Lucia issue a scoped Lucode production recovery task for the stuck sample 3 task `task-1778249434820` / material `mat-1778249419780`, now that the code-level takeover fix has been accepted?

## Confirmed Facts

- MinerU API reported task `ec9452cc-94e4-4b36-bb64-efba86f38cf6` as `completed`.
- The MinerU result ZIP was reported available.
- Luceon production state still had sample 3 as `running` / `mineru-processing`, with material status still processing and no AI metadata job.
- Lucia accepted the code-level correction in Task 46. The accepted code path ingests an already-completed MinerU result after a local timeout and writes final task metadata `mineruStatus='completed'`.
- No production recovery has been authorized or performed by the Task 46 review.

## Options

- Option A: Approve a narrowly scoped production recovery task. Lucode may apply the accepted main fix to production if needed, preserve all override/secret/model boundaries, perform a single-task recovery for `task-1778249434820`, and verify the task transitions to parsed/AI-pending or a clearly evidenced terminal state.
- Option B: Hold production recovery. Keep the code-level fix in main, but leave the existing sample 3 production task unchanged until a later manual decision.
- Option C: Request more read-only evidence before any production recovery task.

## Required Output

Director must choose Option A, B, or C.

If no Director answer is received after two Lucia heartbeat checks, Lucia may only keep the decision on hold or issue further read-only diagnosis. Lucia must not autonomously authorize production write-side recovery because the recovery can mutate production task/material/AI-job state.

## Forbidden Without Separate Approval

- Production release-readiness declaration.
- DB row deletion or manual data cleanup.
- MinIO object deletion or overwrite outside the specific recovery flow.
- Docker volume deletion, pruning, or destructive Docker operation.
- Secret, model, timeout, service, or override changes.
- Broad deploy/rebuild/restart/rollback unrelated to the accepted fix and the single stuck task.
- Skeleton fallback or silent degradation.

