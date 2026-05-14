# User Decision: P1 MinerU Terminal Diagnostic Cleanup Production Deployment Decision

- Decision ID: `TASK-20260514-185927-P1-MinerU-Terminal-Diagnostic-Cleanup-Production-Deployment-Decision`
- Created: 2026-05-14T18:59:27+0800
- Created by: Director
- Next Actor: User
- Related review: `TaskAndReport/2026-05-14T18-59-27+0800_P1-MinerU-Terminal-Last-Progress-Diagnostic-Cleanup_DIRECTOR_REVIEW.md`

## Current Facts

Task 141 is accepted at code/test level and integrated to GitHub `main`.

The accepted code cleanup:

- prevents `MinerU 已完成，但本次未捕获可归因业务进度日志` from being appended as `最后可见进度` inside successful terminal primary progress lines
- preserves real backend/pipeline/page progress as `最后可见进度`
- preserves the no-attributed-log condition as inspectable diagnostic metadata

Checks passed:

- focused MinerU terminal diagnostic precedence smoke
- task detail progress and supervisor status smoke
- node syntax check
- diff check
- TypeScript check

Remaining gap:

- the production deployment at `/Users/concm/prod_workspace/Luceon2026` has not yet been updated to this cleanup code path
- no read-only browser/runtime validation has confirmed the cleanup in production UI

## Decision Needed

Choose whether to authorize scoped production deployment and read-only validation.

### Option A: Scoped Production Deployment + Read-Only Validation (Director Recommended)

Authorize DevelopmentEngineer to perform a minimum necessary production deployment of the accepted Task 141 code path and run non-destructive read-only checks.

Required boundaries:

- deploy only the accepted Task 141 cleanup code path
- use the minimum necessary rebuild/restart for affected services
- run health checks and browser/read-only validation on existing task pages
- do not upload new files
- do not run batch/intake, pressure, soak, cleanup, repair, reparse, re-AI, destructive DB/MinIO/Docker volume/data mutation, settings/secrets/config/model/sample mutation, service ownership mutation, readiness, L3, pressure PASS, release-readiness, production-readiness, or go-live claim

Director recommendation: choose Option A.

Reason: code/test evidence is accepted, but the operator-facing cleanup is only meaningful after it is deployed and verified read-only in the production UI.

### Option B: Hold Deployment

Leave the code accepted on GitHub `main` but do not deploy it yet.

Use this if production activity should pause.

Risk: production UI may continue to show the old no-attributed-log diagnostic sentence inside terminal success primary progress lines.

### Option C: Skip Deployment Validation And Proceed To Batch/Pressure

Not recommended.

Reason: batch/intake or pressure validation should not be started while the operator-facing terminal progress cleanup is not yet deployed and verified.

## Director Recommendation

Approve Option A.

This is the smallest next step that turns the accepted code/test cleanup into runtime evidence without widening into uploads or pressure.
