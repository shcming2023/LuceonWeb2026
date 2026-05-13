# User Decision Required: P0 Post-Smoke Production Validation Authorization

- Decision ID: `TASK-20260513-112049-P0-Post-Smoke-Production-Validation-Authorization`
- Created At: `2026-05-13T11:20:49+0800`
- Recorded By: Director
- Status: 挂起
- Next Actor: User
- Related Tasks:
  - `TASK-20260510-171943-P1-Task-Page-MinerU-Progress-Semantics-Restoration`
  - `TASK-20260510-225807-P1-Ollama-Keep-Alive-And-Cold-Warm-Health-Semantics`
  - `TASK-20260513-105212-P0-AI-Metadata-Smoke-Timeout-Semantics-Alignment`

## Decision Boundary

Task 77 restored task-page MinerU progress semantics at code level. Task 78 restored explicit Ollama keep-alive and cold/warm dependency-health semantics at code level. Task 79 cleared the current-main AI metadata smoke timeout assertion drift.

The next project step is not production release readiness. The next possible step is a scoped production deployment/runtime validation task so the accepted code can be applied and observed in the production deployment path.

Because this touches the production runtime, Director will not silently dispatch it without user authorization.

## Options Considered

### Option A: Authorize Scoped Production Deployment And Non-Destructive Runtime Validation

Authorize a role task to:

- integrate/synchronize the accepted repository state as needed;
- apply the minimum necessary production build/rebuild/restart for the accepted code;
- preserve production-local override boundaries and strict AI/model settings;
- run non-destructive runtime validation only.

Required validation evidence should include:

- production deployed HEAD;
- production override boundary summary;
- upload-server health;
- `dependency-health?mineruSubmitProbe=true`;
- `/ops/mineru/admission-circuit`;
- Ollama `/api/ps` or equivalent residency evidence;
- task-page/API evidence that MinerU progress semantics are available when runtime data supports it;
- clear list of what was not validated.

Not authorized under Option A:

- validation upload;
- pressure test or pressure retry;
- failed-task repair;
- DB/MinIO/Docker volume deletion or manual data repair;
- model pull/delete/reload/replace;
- secret/config/override mutation beyond the minimum deployment mechanics already required by the task;
- production release-readiness declaration;
- L3/full-site acceptance.

### Option B: Hold Production Runtime Changes

Do not deploy or validate in production yet. Keep the accepted code/test work as repository-level progress only.

### Option C: Request More Planning Before Deployment

Ask Architect or TestAcceptanceEngineer to write a short production validation plan before any deployment task is issued.

## User Decision

Approved Option A.

At 2026-05-13, after Director recommended Option A in chat, the user replied: "同意你的建议".

## Director Interpretation

The user authorizes scoped production deployment and non-destructive runtime validation for the accepted Task 77/78/79 code path.

This authorization is narrow. It permits only the minimum necessary production deployment mechanics and runtime checks needed to observe the accepted code in the production deployment path.

It does not authorize release readiness, validation upload, pressure retry/test, failed-task repair, destructive data operations, model operations, broad restart/rollback, L3/full-site acceptance, or sample-library mutation.

## Authorized Next Action

Director issued:

- `TASK-20260513-121844-P0-Post-Smoke-Production-Deployment-And-Non-Destructive-Runtime-Validation`

Assigned role:

- `DevelopmentEngineer`

## Explicitly Not Authorized

Production release readiness, pressure PASS, L3 acceptance, validation uploads, pressure retries, failed-task repair, destructive data operations, secret changes, model operations, broad restart/rollback, or sample-library mutation.

## Next Actor

`DevelopmentEngineer`

## Required Output

DevelopmentEngineer writes the scoped production deployment and non-destructive runtime validation report, then updates the task ledger for Director review.
