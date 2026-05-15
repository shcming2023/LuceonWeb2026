# User Decision: P1 MinerU Progress Snapshot Production Deployment

- Decision ID: `TASK-20260516-064906-P1-MinerU-Progress-Snapshot-Production-Deployment-Decision`
- Created at: `2026-05-16T06:49:06+0800`
- Created by: `Director`
- Current owner: `User`
- Related accepted implementation: `TASK-20260516-062058-P1-MinerU-Progress-Snapshot-Contract-And-Active-Task-Reconciliation`
- Current implementation HEAD: `c6c5790`

## Current Facts

Task 193 has been accepted at code/test level. The implementation introduces a backend progress snapshot contract and active-task reconciliation semantics to reduce the long-running MinerU progress-semantic lag that appeared during pressure monitoring.

The implementation has not yet been deployed to the production workspace.

## Why A User Decision Is Needed

Production deployment changes live operator-facing semantics and requires rebuilding/restarting at least the affected application services. This is not a pressure test and should not be bundled with new uploads or task repair. The safest next step is to deploy narrowly, verify read-only surfaces, and only then decide whether to run another controlled long task or pressure observation.

## Options

### Option A: Scoped Production Deployment + Read-Only Validation (Recommended)

Authorize DevelopmentEngineer to deploy the accepted Task 193 implementation to `/Users/concm/prod_workspace/Luceon2026` and perform read-only validation only.

Allowed scope:

- synchronize production source to the accepted GitHub/main implementation;
- rebuild/restart only the minimum required services for the changed code, expected to include `upload-server` and the frontend service/image if the deployment topology requires it;
- validate `/cms/`, `/cms/tasks`, upload health, dependency-health without submit-probe, `/ops/mineru/active-task`, `/ops/mineru/log-channel-ownership`, and related read-only progress snapshot fields;
- report exact production HEAD, commands, endpoint responses, and any latency or semantic anomalies.

Explicitly not authorized:

- upload, pressure test, submit-probe, retry/reparse/re-AI/cancel/repair/reset;
- DB/MinIO/Docker volume cleanup, `docker compose down -v`, prune, destructive data mutation;
- model pull/delete/replace, secret/config mutation, sample-library mutation;
- pressure PASS, L3, release readiness, or go-live declaration.

Director recommendation: choose Option A. It is the narrowest way to learn whether the root-cause fix is visible in production without mixing deployment validation with another stressful workload.

### Option B: Hold Deployment

Keep the accepted code on GitHub/main but do not deploy it yet.

This avoids live-service change now, but leaves the known progress-semantic lag unresolved in production observation.

### Option C: Additional Code-Level Review Before Deployment

Assign Architect or DevelopmentEngineer another review-only task before deployment.

This is conservative, but current focused tests and Director reruns are already clean. It may slow progress without adding much evidence unless there is a specific concern about the new contract.

## Pending User Reply

Please choose Option A, B, or C.
