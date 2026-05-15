# User Decision Required: P0 MinerU Submit-Probe And Pressure-State Reconciliation

- Decision record time: 2026-05-15T20:21:23+0800
- Related accepted task: `TASK-20260515-201231-P0-MinerU-Only-Runtime-Relaunch-And-Read-Only-Verification`
- Recorded by: Director
- Status: waiting for User decision

## Current Facts

MinerU has been relaunched under the canonical `luceon-mineru` tmux session and direct `/health` is healthy.

Dependency-health without submit-probe is non-blocking. The admission circuit is closed. There is no active/queued/takeover-required task.

The 24-PDF pressure run is not PASS. Current task distribution is:

- 5 `review-pending/review`;
- 18 `failed/submit-failed-retryable`;
- 1 `failed/mineru-processing`.

The submit path has not been freshly verified after relaunch because Task 187 explicitly forbade submit-probe.

## Why This Needs User Decision

The next step can mutate runtime state depending on the option chosen. A submit-probe creates a synthetic MinerU task through the real submit path. Failed-task reconciliation, retry, reparse, re-AI, repair, or reset would mutate the pressure-run task set. Director should not silently choose those boundaries.

## Options

### Option A: Submit-Probe Only First (Director Recommended)

Authorize TestAcceptanceEngineer or DevelopmentEngineer to run exactly one MinerU submit-probe validation after clean preflight:

- confirm no active/queued/takeover-required task;
- confirm direct MinerU health;
- run exactly one dependency-health submit-probe or equivalent documented helper with submit-probe explicitly enabled;
- record submit status, duration, task id, admission-circuit state, active-task state, and log-channel state;
- do not upload PDFs;
- do not retry/reparse/re-AI/repair/reset/cancel any pressure task;
- do not run cleanup, destructive Docker/DB/MinIO commands, or readiness claims.

Reason: this verifies the recovered submit path before touching the failed pressure-run tasks.

### Option B: Hold With No Runtime Mutation

Do not run submit-probe and do not reconcile pressure tasks. Keep the state as accepted recovery evidence plus unresolved submit-path evidence.

Risk: the project remains blocked on unverified submit readiness.

### Option C: Submit-Probe Plus Pressure-Task Reconciliation

Authorize submit-probe and a separate scoped reconciliation/retry plan for the 18 retryable submit-failed tasks and 1 lost MinerU processing task.

Risk: this mixes readiness validation with task-state mutation. It may obscure whether the relaunch alone restored the submit path.

### Option D: Close Pressure Run As Partial/Failed Evidence, Then Reset Later

Do not reconcile the 24 pressure tasks. Treat them as evidence of the old runtime-loss incident and plan a later clean pressure test after submit-path validation.

Risk: this avoids touching failed tasks but requires a future clean validation cycle before any pressure PASS claim.

## Director Recommendation

Choose Option A now.

It is the smallest useful next step: one controlled submit-path validation, no PDF upload, no failed-task mutation, and no readiness claim. After Option A evidence is reviewed, Director can ask a cleaner second question: whether to leave the 24 pressure tasks as historical incident evidence, repair/retry selected tasks, or reset for a clean pressure run.

## Forbidden Without Further Approval

- pressure PASS, L3, production readiness, release readiness, production上线, or go-live claim;
- upload, pressure/batch/soak run, or second validation beyond the chosen option;
- retry/reparse/re-AI/cancel/repair/reset unless explicitly authorized;
- DB/MinIO/Docker volume/data cleanup;
- `docker compose down -v`, Docker prune, broad restart/redeploy;
- model pull/delete/replace, config/secret/sample mutation;
- destructive task or material mutation.

