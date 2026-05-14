# User Decision: P1 MinerU Terminal Progress Hardening Production Deployment Decision

- Decision ID: `TASK-20260514-165648-P1-MinerU-Terminal-Progress-Hardening-Production-Deployment-Decision`
- Created: 2026-05-14T16:56:48+0800
- Created by: Director
- Next Actor: User
- Related review: `TaskAndReport/2026-05-14T16-56-48+0800_P1-MinerU-Terminal-Progress-Attribution-Hardening_DIRECTOR_REVIEW.md`

## Current Facts

Task 138 is accepted at code/test level and integrated to GitHub `main`.

The accepted code changes:

- make successful terminal MinerU tasks with completed MinerU state and parsed artifact evidence show a completion-oriented primary line
- preserve `未捕获可归因业务进度日志` as diagnostic metadata when applicable
- keep failed/no-artifact/in-flight semantics explicit

Checks passed:

- focused MinerU terminal diagnostic precedence smoke
- node syntax check
- task detail progress and supervisor status smoke
- diff check
- TypeScript check

Remaining gap:

- the production deployment at `/Users/concm/prod_workspace/Luceon2026` has not yet been updated to this code path
- no browser/runtime validation has confirmed the production UI display semantics

## Decision Needed

Choose whether to authorize scoped production deployment and read-only validation.

### Option A: Scoped Production Deployment + Read-Only Validation (Director Recommended)

Authorize DevelopmentEngineer to perform a minimum necessary production deployment of the accepted Task 138 code path and run non-destructive read-only checks.

Required boundaries:

- deploy only the accepted Task 138 code path
- use the minimum necessary rebuild/restart for affected services
- run health checks and browser/read-only validation on existing task pages
- do not upload new files
- do not run batch/intake, pressure, soak, cleanup, repair, reparse, re-AI, destructive DB/MinIO/Docker volume/data mutation, settings/secrets/config/model/sample mutation, readiness, L3, pressure PASS, release-readiness, or go-live claim

Director recommendation: choose Option A.

Reason: code/test evidence is accepted, but the operator-facing fix is only meaningful after it is deployed and verified read-only in the production UI.

### Option B: Hold Deployment

Leave the code accepted on GitHub `main` but do not deploy it yet.

Use this if production activity should pause.

Risk: the production UI will continue to show the old terminal progress-attribution wording.

### Option C: Skip Deployment Validation And Proceed To Batch/Pressure

Not recommended.

Reason: batch/intake or pressure validation should not be started before the operator-facing progress semantics fix is deployed and verified.

## Director Recommendation

Approve Option A.

This is the smallest next step that turns the accepted code/test fix into runtime evidence without widening into uploads or pressure.
