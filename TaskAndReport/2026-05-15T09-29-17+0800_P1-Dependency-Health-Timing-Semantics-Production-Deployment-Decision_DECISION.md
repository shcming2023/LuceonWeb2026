# Decision: P1 Dependency Health Timing Semantics Production Deployment

- Decision ID: `TASK-20260515-092917-P1-Dependency-Health-Timing-Semantics-Production-Deployment-Decision`
- Created: 2026-05-15T09:29:17+0800
- Created by: Director
- Current owner: User
- Related accepted task: `TASK-20260515-090601-P1-Dependency-Health-Timing-Semantics-Hardening`

## Current Facts

- Task 164 is accepted at code/test level by Director review.
- The accepted code adds explicit Ollama dependency-health timing/readiness fields so cold-before-chat slow success, cold timeout, warm timeout, chat HTTP failure, missing model, and service/tag failures are distinguishable.
- The accepted code keeps parse/upload blocking separate from AI readiness blocking.
- Development and clean sync clone checks passed, including dependency-health smoke `89 passed, 0 failed` and `tsc --noEmit`.
- No production deployment, production rebuild/restart, upload, pressure validation, cleanup, retry/reparse/re-AI, or readiness/go-live claim has been performed for this change.

## Decision Needed

Should the accepted Task 164 code/test change be deployed to production for scoped read-only validation?

## Options

### Option A: Scoped Production Deployment And Read-Only Validation (Director Recommended)

Authorize Director to issue a `DevelopmentEngineer` task to perform the minimum necessary production deployment and read-only validation for Task 164.

Scope:

- sync accepted main into production if needed;
- rebuild/restart only the minimum production service surface required for `server/upload-server.mjs` dependency-health changes;
- run read-only dependency-health validation and capture the new Ollama readiness/timing fields;
- verify no production upload, pressure/batch/soak/fresh serial validation, cleanup, retry/reparse/re-AI, destructive DB/MinIO/Docker volume/data mutation, settings/secrets/model/sample mutation, or readiness/go-live claim is performed;
- write a report for Director review.

Why recommended:

- The code/test change is accepted and directly addresses a release-readiness blocker around Ollama cold-start timing semantics.
- The next missing evidence is runtime visibility in production, not more local-only code review.
- This route is scoped, reversible, and can be validated without submitting new PDFs or touching existing data.

### Option B: Hold Deployment

Keep the accepted code on GitHub main and do not deploy yet.

Risk:

- The project remains unable to confirm whether production operators and scripts can see the corrected dependency-health semantics.
- Release-readiness consolidation remains blocked by missing runtime evidence for this accepted fix.

### Option C: Route Back For More Code Polish

Ask DevelopmentEngineer to add more local code/UI polish before production deployment.

Why not first:

- The current accepted change is sufficient for the specific timing-semantics blocker.
- Additional UI/operator wording can be handled later if production read-only validation reveals a concrete display gap.

## Director Recommendation

Choose Option A.

If this same User decision remains unanswered for two heartbeat cycles, Director may proceed with Option A under the existing heartbeat auto-advance rule, because it is scoped, reversible, non-destructive, and does not authorize uploads, cleanup, retry/reparse/re-AI, pressure testing, or any readiness/go-live declaration.

## User Decision

User approved Option A in-thread on 2026-05-15.

Director action:

- issue Task 166 to `DevelopmentEngineer`;
- keep scope to minimum necessary production deployment and read-only dependency-health validation;
- require validation of the new Ollama readiness/timing fields in production;
- do not authorize upload, pressure/batch/soak/fresh serial validation, cleanup/cancel/repair/retry/reparse/re-AI, destructive DB/MinIO/Docker volume/data mutation, settings/secrets/config/model/sample mutation, skeleton fallback weakening, pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live claim.

## Not Authorized By This Decision Row

No upload, pressure/batch/soak/fresh serial validation, cleanup/cancel/repair/retry/reparse/re-AI, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup/prune, broad service restart/rollback, MinerU/Ollama/supervisor mutation beyond minimum required dependent service restart for deployment, settings/secrets/config/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live claim is authorized unless the user explicitly approves Option A and the subsequent task brief keeps these exclusions.
