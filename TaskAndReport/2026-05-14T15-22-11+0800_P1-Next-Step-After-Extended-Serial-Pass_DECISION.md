# User Decision: P1 Next Step After Extended Serial Pass

- Decision ID: `TASK-20260514-152211-P1-Next-Step-After-Extended-Serial-Pass`
- Created: 2026-05-14T15:22:11+0800
- Created by: Director
- Next Actor: User
- Related review: `TaskAndReport/2026-05-14T15-22-11+0800_P1-Extended-Strict-Serial-Validation-After-Small-Serial-Pass_DIRECTOR_REVIEW.md`

## Current Facts

The current production-like path now has these fresh-upload validation layers:

- Task 132: exactly one fresh upload passed after db-sync hardening
- Task 134: three additional strict-serial uploads passed
- Task 136: six additional strict-serial uploads passed

Across Task 136:

- all six uploads reached task `review-pending`
- all six materials reached `reviewing`
- all six MinerU parses reached `completed`
- all six AI jobs reached `review-pending` with `qwen3.5:9b`
- parsed files counts were `8/9/21/21/25/82`
- production runtime returned to idle after every upload
- db-sync/settings/secrets warning recurrence count was `0`
- direct runtime spot-check after the run was healthy and nonblocking

Remaining issue:

- MinerU terminal progress attribution is still imperfect. The task detail page shows `当前进展` during most observations, but terminal/list-row text can still say `MinerU 已完成，但本次未捕获可归因业务进度日志` after a successful parse.

## Decision Needed

Choose the next step.

### Option A: Fix MinerU Terminal Progress Attribution Before Batch/Pressure (Director Recommended)

Assign DevelopmentEngineer a scoped implementation task to harden MinerU progress semantics:

- preserve or derive the last valid task-attributed business progress snapshot for terminal rows
- avoid showing `未捕获可归因业务进度日志` as the dominant terminal message when the task had meaningful in-flight progress or completed cleanly
- keep diagnostic warnings visible as secondary diagnostics, not as the primary successful-terminal wording
- add focused smoke coverage for terminal completed-task semantics
- no production deployment, pressure, batch, cleanup, repair, reparse, re-AI, destructive mutation, model/config/secret/sample mutation, readiness/L3/go-live claim unless later separately authorized

Director recommendation: choose Option A.

Reason: the serial pipeline is now reasonably proven under bounded conditions. The next visible blocker is operator trust and unattended-run observability. Fixing the terminal progress attribution before batch/intake validation will make later failures easier to interpret.

### Option B: Proceed To Controlled Batch-Intake/Backpressure Validation

Authorize TestAcceptanceEngineer to run a small controlled batch-intake validation, still without pressure claims:

- upload a small batch through the UI
- observe whether admission/backpressure/queue semantics stay coherent
- stop on any systemic failure
- no pressure PASS, L3, release-readiness, or go-live claim

Risk: the current terminal progress-attribution residual will make batch results harder to read and may confuse operator-facing evidence.

### Option C: Treat Current Evidence As Release-Candidate Enough

Not recommended.

Reason: current evidence is strong for strict serial execution, but it does not prove batch intake, pressure, soak, L3, release-readiness, or unattended long-run behavior.

## Director Recommendation

Approve Option A.

This keeps the project moving while avoiding a noisy jump into broader validation before the remaining observability debt is cleaned up.

## Heartbeat Wait Evidence

- Wait evidence 1: 2026-05-14T15:51:21+0800 heartbeat found this decision still pending with no user reply after the Director recommendation. No autonomous advance was triggered yet.
- Wait evidence 2: 2026-05-14T16:22:51+0800 heartbeat found this decision still pending with no user reply after wait evidence 1.

## Autonomous Decision

- Decision time: 2026-05-14T16:23:11+0800
- Decision: `DIRECTOR_AUTONOMOUS_OPTION_A`

After two unanswered heartbeat checks, Director applied the previously stated conservative recommendation: issue a scoped DevelopmentEngineer task to harden MinerU terminal progress-attribution semantics before batch/intake or pressure-style validation.

This autonomous decision only authorizes a code/test-level implementation task. It does not authorize production deployment, uploads, batch/intake validation, pressure validation, soak, cleanup, repair, reparse, re-AI, destructive DB/MinIO/Docker volume/data mutation, settings/secrets/config/model/sample mutation, service ownership mutation, readiness, L3, pressure PASS, release-readiness, or go-live.

Director issued `TASK-20260514-162311-P1-MinerU-Terminal-Progress-Attribution-Hardening`.
