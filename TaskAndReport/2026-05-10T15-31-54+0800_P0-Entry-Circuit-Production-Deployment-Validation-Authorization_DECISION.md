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
