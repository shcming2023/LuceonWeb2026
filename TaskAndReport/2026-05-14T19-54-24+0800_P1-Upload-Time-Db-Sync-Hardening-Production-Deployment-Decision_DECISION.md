# User Decision Required: P1 Upload-Time Db-Sync Hardening Production Deployment Decision

## Current Facts

- Task 146 was accepted at code/test level.
- The accepted patch is narrow frontend db-sync lifecycle hardening in `src/store/appContext.tsx`.
- The patch preserves real db-sync warning visibility and only downgrades transient fetch cancellation during `pagehide` / `beforeunload`.
- Focused smoke, syntax check, `git diff --check`, and TypeScript check passed in a clean sync clone.
- No production deployment or runtime proof has happened for this patch.

## Decision Point

The code is accepted, but production still runs the pre-Task-146 frontend. To prove the residual `[db-sync] POST /materials failed` / `PUT /asset-details/... failed` noise is addressed in real operator conditions, the project needs a separately authorized production deployment and scoped validation.

## Options

### Option A: Recommended

Authorize a scoped production deployment and validation task.

Allowed scope:

- fast-forward production to the accepted Task 146 commit;
- rebuild/restart only the minimum necessary frontend service;
- run non-destructive health checks;
- run exactly one controlled fresh upload from `/Users/concm/prod_workspace/Luceon2026/testpdf`;
- verify task/material/MinerU/AI terminal coherence;
- verify terminal MinerU progress semantics stay clean;
- verify upload-time and post-terminal browser console/network behavior for db-sync warnings;
- stop and report to Director.

Not authorized under Option A:

- second upload;
- batch/intake/pressure/soak/broader serial validation;
- cleanup/repair/reparse/re-AI;
- destructive DB/MinIO/Docker volume/data mutation;
- Docker/service mutation beyond minimum frontend deployment;
- settings/secrets/config/model/sample mutation;
- broad warning suppression;
- readiness/L3/pressure PASS/release-readiness/production-readiness/go-live claim.

### Option B

Hold deployment. Keep Task 146 accepted at code/test level only.

Risk: production continues to run the pre-Task-146 frontend and may keep producing upload-time db-sync console noise.

### Option C

Ask DevelopmentEngineer for more code-level tests before deployment.

Risk: the remaining uncertainty is primarily runtime/browser lifecycle behavior, so additional source-level checks are unlikely to replace production validation.

## Director Recommendation

Choose Option A.

It is the smallest validation that can actually prove the fix in the environment where the issue was observed. It remains bounded, non-destructive, and explicitly does not authorize pressure or readiness claims.

## Heartbeat Wait Evidence

- `2026-05-14T20:12:51+0800`: heartbeat check found Task 147 still waiting for User decision; no Director待审 task was present. Director recommendation remains Option A.

## User Decision

- Decision time: `2026-05-14T20:38:00+0800`
- Decision: `USER_APPROVED_OPTION_A`
- User instruction: `同意option A`

Director will execute Option A as two scoped role tasks to preserve role boundaries:

1. DevelopmentEngineer deploys the accepted Task 146 frontend hardening to production and performs non-destructive read-only health/browser checks.
2. If deployment/read-only validation is accepted, Director may dispatch TestAcceptanceEngineer for exactly one controlled fresh upload validation under this same user authorization.

No second upload, batch/intake/pressure/soak, cleanup/repair/reparse/re-AI, destructive DB/MinIO/Docker volume/data mutation, Docker/service mutation beyond minimum frontend deployment, settings/secrets/config/model/sample mutation, broad warning suppression, readiness/L3/pressure PASS/release-readiness/production-readiness/go-live claim is authorized.
