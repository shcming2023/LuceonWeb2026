# User Decision: P1 Next Validation Scope After Small Serial Pass

- Decision ID: `TASK-20260514-144224-P1-Next-Validation-Scope-After-Small-Serial-Pass`
- Created: 2026-05-14T14:42:24+0800
- Created by: Director
- Next Actor: User
- Related review: `TaskAndReport/2026-05-14T14-42-24+0800_P1-Post-Db-Sync-Hardening-Small-Serial-Validation_DIRECTOR_REVIEW.md`

## Current Facts

Task 132 proved exactly one fresh upload after db-sync hardening.

Task 134 then proved three additional strict-serial UI uploads:

- all three reached task `review-pending`
- all three materials reached `reviewing`
- all three MinerU parses reached `completed`
- all three AI jobs reached `review-pending` with `qwen3.5:9b`
- parsed files counts were `9`, `8`, and `8`
- production runtime returned to idle after each upload
- db-sync/settings/secrets warning recurrence count was `0`
- no pressure, batch, soak, cleanup, repair, destructive mutation, service ownership mutation, readiness, L3, or go-live claim was made

Remaining issue:

- MinerU terminal progress attribution is still imperfect for fast/short tasks. The UI can truthfully say MinerU completed while also saying no attributable business-progress log was captured.

## Decision Needed

Choose the next validation scope.

### Option A: Extended Strict-Serial Validation (Director Recommended)

Authorize TestAcceptanceEngineer to run a larger but still conservative serial validation:

- up to 6 additional PDFs from `/Users/concm/prod_workspace/Luceon2026/testpdf`
- UI upload only
- one at a time
- terminal state before next upload
- stop immediately on systemic failure, db-sync warning recurrence, dependency/admission/active-task inconsistency, or unsafe runtime state
- explicitly track MinerU progress semantics and terminal attribution residual
- no pressure, no batch concurrency, no soak, no cleanup/repair/reparse/re-AI, no destructive mutation, no readiness/L3/go-live claim

Director recommendation: choose Option A.

Reason: the core path has now passed one-upload plus three-upload strict serial validation. The next meaningful risk is longer serial endurance, not batch pressure yet. The MinerU attribution residual is visible and should be tracked, but it is not currently blocking terminal completion.

### Option B: Pause Validation Expansion And Fix Progress Attribution First

Assign Architect/DevelopmentEngineer to refine the remaining terminal progress-attribution semantics before any further upload expansion.

Use this if operator-facing observability is more important than gaining the next serial-endurance evidence immediately.

Risk: this may create additional code churn before we have measured the longer serial runtime boundary.

### Option C: Start Pressure Or Batch Validation

Not recommended now.

Reason: current evidence is still serial. Jumping to pressure/batch could mix multiple risk sources and make failures harder to interpret.

## Director Recommendation

Approve Option A: extended strict-serial validation, still no pressure.

This keeps progress moving toward unattended long-run confidence while preserving the current safety boundary.
