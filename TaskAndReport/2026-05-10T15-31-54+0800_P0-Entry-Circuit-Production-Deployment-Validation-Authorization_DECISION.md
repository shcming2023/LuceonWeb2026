# Director Decision Required: P0 Entry Circuit Production Deployment Validation Authorization

- Decision ID: `TASK-20260510-153154-P0-Entry-Circuit-Production-Deployment-Validation-Authorization`
- Created At: `2026-05-10T15:31:54+0800`
- Created By: Lucia
- Status: 挂起
- Next Actor: Director
- Related Accepted Task: `TASK-20260510-142045-P1-Entry-Circuit-And-Durable-Admission-State`

## Decision Needed

Lucia accepted the P1 durable MinerU admission circuit at code level and integrated it into `main`.

Director must decide whether to authorize a scoped production deployment and non-destructive runtime validation of this accepted code.

## Director Review Note

At `2026-05-10T15:41:06+0800`, Director reviewed Lucia's Task 70 acceptance and stated that the evidence supports `ACCEPTED_CODE_LEVEL_PRODUCTION_DEPLOYMENT_REQUIRED`.

Director also confirmed the boundary: Task 70 must not be upgraded to production deployed, L3, production readiness, or manual pressure-test restart. Task 72 must stay limited to deployment and non-destructive runtime validation. It must not include validation upload, pressure test, failed-task repair, or release-readiness declaration unless separately approved.

If Option A is later approved, Lucode's report must include both `dependency-health?mineruSubmitProbe=true` and `/ops/mineru/admission-circuit`; ordinary health-green evidence alone is insufficient.

This review note is not an Option A approval. Task 72 remains pending Director deployment/validation authorization.

## Recommended Option

`Option A`: authorize Lucode to perform the minimum necessary production apply/rebuild for the accepted P1 admission-circuit code, then run non-destructive runtime validation only.

Required evidence for Option A:

- GitHub/main HEAD deployed in production;
- production `docker-compose.override.yml` boundary summary, preserving strict AI/model and MinIO console local-only settings;
- `dependency-health?mineruSubmitProbe=true`;
- `/ops/mineru/admission-circuit`;
- active-task / queue state showing whether intake is safe;
- Ollama `/api/ps` or equivalent read-only residency evidence;
- clear statement of what was not tested or not ready.

## Forbidden Without Separate Approval

- Production release-readiness declaration;
- validation upload or pressure test beyond explicit scope;
- DB row deletion or manual DB state repair;
- MinIO object deletion, Docker volume deletion/pruning, or destructive Docker operation;
- secret/model/timeout/config/override mutation;
- broad stack restart, rollback, or unrelated failed-task recovery;
- silent fallback or skeleton metadata as recognition.

## Decision Boundary

This decision is about deploying and validating the accepted P1 intake-safety control. It is not a release-readiness decision.

If Director does not answer after two Lucia heartbeat checks, Lucia may only issue non-destructive read-only preflight or documentation tasks. Lucia may not autonomously approve production deployment, production upload validation, destructive operations, or production release readiness.
