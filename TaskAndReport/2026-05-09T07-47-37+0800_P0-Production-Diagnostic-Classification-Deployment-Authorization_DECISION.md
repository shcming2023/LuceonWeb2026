# Director Decision: Production Diagnostic Classification Deployment Authorization

- Decision record time: 2026-05-09T07:47:37+0800
- Task ID: `TASK-20260509-074737-P0-Production-Diagnostic-Classification-Deployment-Authorization`
- Status: `挂起`
- Next Actor: `Director`

## Decision Needed

Lucia accepted Task 50 at code level. Director must decide whether to authorize a scoped production deployment/validation of the diagnostic classification fix that separates historical terminal AI failures from actionable MinerU takeover tasks.

## Recommended Option

Option A: approve scoped production diagnostic deployment and read-only validation.

Allowed scope under Option A:

- Sync production workspace to the accepted `main` commit containing Task 50.
- Preserve production-local override boundaries, including strict AI/model settings and MinIO console local-only binding.
- Use only minimum necessary non-destructive Docker/Compose action to apply the upload-server code if required.
- Run read-only validation for `/ops/mineru/active-task` and `/ops/mineru/diagnostics`.
- Confirm that the three known historical terminal AI failures are surfaced in `historicalAiFailureTasks`, not `takeoverRequiredTasks`, while real actionable takeover buckets remain available.

## Alternative Options

Option B: hold production deployment. Keep the fix on `main` only and defer production validation.

Option C: request additional code-level or read-only analysis before production deployment.

## Safety Boundary

This decision must not be treated as production release readiness. It must not authorize DB row deletion, MinIO object deletion, Docker volume deletion/pruning, production data cleanup, unrelated task recovery, new uploads, reparses, retries, service/model/config/secret/override changes, skeleton fallback, silent degradation, or external/multi-user release acceptance.

## Autonomy Rule

If Director does not answer after two Lucia heartbeat checks, Lucia may not autonomously deploy or restart production for this item. The only permitted fallback is to hold production deployment and keep Task 50 accepted at code level.
