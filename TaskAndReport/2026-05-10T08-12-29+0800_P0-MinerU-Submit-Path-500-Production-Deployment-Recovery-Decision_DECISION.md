# Director Decision: P0 MinerU Submit-Path 500 Production Deployment And Recovery Authorization

- Decision ID: `TASK-20260510-081229-P0-MinerU-Submit-Path-500-Production-Deployment-Recovery-Decision`
- Created At: `2026-05-10T08:12:29+0800`
- Created By: Lucia
- Status: 挂起
- Next Actor: Director
- Related Task: `TASK-20260510-075129-P0-MinerU-Submit-Path-500-Circuit-Breaker-And-Failure-State`
- Related Review: `TaskAndReport/2026-05-10T08-12-29+0800_P0-MinerU-Submit-Path-500-Circuit-Breaker-And-Failure-State_LUCIA_REVIEW.md`

## Decision Needed

Task 64 is accepted at code level, but production still needs an explicit Director decision before Lucia authorizes production deployment and any runtime recovery action.

## Options

### Option A: Authorize Minimal Production Deployment And Read-Only Validation

Allow Lucode to:

- sync production to the accepted main commit;
- rebuild/restart only `upload-server` to apply the circuit-breaker code;
- run read-only health and dependency-health checks;
- not restart MinerU or mutate existing failed tasks/materials.

This validates that production has the protective queue behavior available in code, but it may leave MinerU submit path still returning HTTP 500.

### Option B: Authorize Minimal Production Deployment Plus Scoped MinerU Runtime Recovery

Allow Lucode to:

- perform Option A;
- perform the minimum necessary non-destructive MinerU runtime recovery action after recording current state, such as restarting the local MinerU API/service if needed;
- verify `/health` and `/tasks` submit probe recover;
- run no new validation uploads unless separately authorized.

Forbidden under Option B unless separately approved:

- DB/MinIO/Docker volume/task/material/artifact/log/sample deletion or cleanup;
- model/provider/timeout/secret/override changes;
- broad production rebuild/restart/rollback;
- reprocessing/recovering the failed 24 pressure-test tasks;
- production release-readiness declaration.

### Option C: Hold

Do not deploy or recover now. Keep production release readiness blocked and request more read-only evidence.

## Lucia Recommendation

Lucia recommends Option B if Director wants to continue toward release readiness, because code-level queue protection alone does not restore the currently failing MinerU submit path. If Director wants zero service operations, choose Option A or C explicitly.

## Autonomy Boundary

Lucia may not autonomously approve production release readiness. Lucia also should not autonomously authorize MinerU runtime restart/recovery after heartbeat waits because it is a production service operation. If Director does not respond, Lucia may only keep release readiness on hold or issue read-only evidence tasks.

