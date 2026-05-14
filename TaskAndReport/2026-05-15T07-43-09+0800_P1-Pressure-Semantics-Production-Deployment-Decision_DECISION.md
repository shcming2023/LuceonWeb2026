# P1 Pressure Semantics Production Deployment Decision

Decision ID: `TASK-20260515-074309-P1-Pressure-Semantics-Production-Deployment-Decision`

Created: 2026-05-15T07:43:09+0800

Next Actor: `User`

## User Decision

Decision received: 2026-05-15T07:55:03+0800

User approved: `Option A`

Director action: issue Task 159 to DevelopmentEngineer for minimum necessary production deployment plus read-only validation only.

## Context

Task 157 has been accepted at code/test level and integrated to GitHub main by Director review. Production still runs the previous deployed code until a separate deployment task is authorized and executed.

The accepted code/test changes cover:

- AI timeout/transport failure classification and Material/ParseTask backfill.
- Task-page wording that distinguishes local timeout, remote MinerU `processing`, stale observation, and raw-log advancement.
- Pressure result semantics for partial success with retryable AI residuals versus systemic failure.

## Decision Needed

Please choose the next path:

### Option A: Scoped Production Deployment + Read-Only Validation (Director Recommendation)

Authorize a DevelopmentEngineer task to perform the minimum necessary production deployment of the accepted Task 157 code, followed by read-only validation only.

Expected validation:

- Confirm production HEAD matches the accepted GitHub main commit.
- Confirm relevant services are reachable and healthy.
- Confirm dependency-health/admission surfaces remain non-blocking.
- Confirm existing task-page/list semantics render the new wording without new uploads.
- Confirm no obvious console/network regression on the relevant task pages.

Not authorized under Option A:

- Upload.
- Pressure/batch/soak test.
- Cleanup, repair, retry, reparse, or re-AI for existing tasks.
- Destructive DB/MinIO/Docker volume/data mutation.
- Docker down/volume cleanup.
- Settings/secrets/config/model/sample mutation.
- Automatic retry/requeue.
- Skeleton fallback weakening.
- Pressure PASS, L3, release-readiness, production-readiness, or go-live claim.

### Option B: Hold Deployment And Request One More Code Follow-Up

Ask DevelopmentEngineer to first wire `mineruRuntimeProgressTruth` into stored task metadata and/or add broader pressure-summary caller adoption before production deployment.

Risk: this may be cleaner long-term, but delays the immediate fix for the current operator-facing semantic mismatch.

### Option C: Hold

Do not deploy or create another task now.

Risk: production continues to show the old semantics for the exact issue the user identified.

## Director Recommendation

Choose Option A.

Reason: Task 157 already addresses the highest-impact production pain in code and passed focused checks in both the dirty role workspace and a clean sync clone. The remaining persistence/dashboard adoption items are useful follow-ups, but they should not block getting the corrected operator semantics and AI residual classification into production under a narrow, read-only validation boundary.
