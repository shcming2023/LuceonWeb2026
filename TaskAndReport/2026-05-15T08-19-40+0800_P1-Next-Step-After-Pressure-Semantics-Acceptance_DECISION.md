# Decision: P1 Next Step After Pressure Semantics Acceptance

- Decision ID: `TASK-20260515-081940-P1-Next-Step-After-Pressure-Semantics-Acceptance`
- Created: 2026-05-15T08:19:40+0800
- Created by: Director
- Current owner: Director
- Related accepted task: `TASK-20260515-080916-P1-Pressure-Semantics-Production-Read-Only-Acceptance-Review`

## Current Facts

- Task 157 pressure semantics code was accepted at code/test level and deployed through Task 159.
- Task 160 read-only production acceptance passed within scope.
- The recent manual pressure window is no longer interpreted as whole-run/systemic failure:
  - `24` pressure-window tasks;
  - `21 review-pending/review`;
  - `3 failed/ai`.
- Production is currently reachable/non-blocking in read-only checks, and MinerU active-task diagnostics are idle.
- This still does not declare pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Remaining Boundaries

- Existing historical `failed/ai` tasks were not repaired or retried.
- The failed-AI detail copy is acceptable but generic (`需排查或重试`).
- No dedicated pressure-batch summary dashboard was observed.
- Production retains known local modified files, which remain a source-drift/override boundary.
- No final release-readiness consolidation has been performed after the pressure-semantics correction.

## Options

### Option A: Start Release-Readiness Consolidation (Director Recommended)

Authorize Director to issue a read-only Architect or ProductManager task to refresh the release-readiness/gap matrix after the pressure-semantics acceptance.

Scope:

- consolidate current code/deployment/runtime evidence;
- list remaining blockers and optional polish separately;
- produce a go/no-go recommendation boundary;
- no upload, pressure, cleanup, retry, deployment, service mutation, or readiness claim.

Why recommended:

- The pressure-semantics stream has reached a clean read-only acceptance point.
- The next risk is not another narrow semantic check; it is deciding what still blocks production readiness.
- This keeps the project moving without prematurely declaring上线.

### Option B: Polish AI Residual Copy First

Authorize a small DevelopmentEngineer task to make the failed-AI detail wording more explicit, for example replacing generic `需排查或重试` copy with AI-residual/manual-judgment wording.

Why not first:

- The current wording is understandable and bounded to `当前阶段 ai`.
- It is useful polish, but it should not block the readiness consolidation unless the user wants UI wording tightened first.

### Option C: Hold And Do Nothing

Pause after pressure-semantics acceptance.

Risk:

- The project may stall again without a consolidated view of what remains before production readiness.

## Director Recommendation

Choose Option A.

If the same User decision remains unanswered for two heartbeat cycles, Director may proceed with Option A under the existing heartbeat auto-advance rule, because it is read-only, non-destructive, scoped, and does not declare readiness.

## User Decision

User approved Option A in-thread on 2026-05-15.

Director action:

- issue Task 162 to `Architect`;
- keep the task read-only and non-destructive;
- require a release-readiness consolidation/gap refresh and go/no-go recommendation boundary;
- do not authorize upload, pressure testing, cleanup, retry/reparse/re-AI, production/service/config mutation, or any readiness/go-live claim.

## Not Authorized By This Decision Row

No upload, pressure/batch/soak/fresh serial validation, cleanup/cancel/repair/retry/reparse/re-AI, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup/prune, service start/stop/restart/rebuild, MinerU/Ollama/supervisor mutation, settings/secrets/config/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live claim is authorized by this decision.
