# User Decision Required: P1 MinerU Live Progress Observability Validation

- Task ID: `TASK-20260514-093412-P1-MinerU-Live-Progress-Observability-Validation-Decision`
- Decision created: 2026-05-14T09:34:12+0800
- Created by: Director
- Current Next Actor: `User`
- Based on accepted review: `TaskAndReport/2026-05-14T09-34-12+0800_P1-MinerU-Sidecar-Attach-Only-Recovery_DIRECTOR_REVIEW.md`

## Current Facts

Task 113 restored the `luceon-sidecar` transport only:

- `luceon-sidecar` is present in tmux.
- `/ops/mineru/log-channel-ownership` reports `sidecar.runningState=observed-recent`.
- Runtime preflight surfaces were clean: dependency-health non-blocking, MinerU submit probe accepted, admission circuit closed, and no active/current/queued/takeover parse work was present.
- Configured MinerU logs are still empty.
- `/ops/mineru/global-observation` can still see stale fallback log content from `uat/scratch/mineru-api.log`; that content is stale and unattributed.
- No live upload was authorized or run in Task 113.

## Why A User Decision Is Needed

The project objective is not merely to have a sidecar process running. The operator must be able to see whether MinerU is genuinely advancing during real work. That requires a live validation upload, but an upload is a runtime mutation and must stay user-authorized.

## Options

### Option A: Recommended

Authorize TestAcceptanceEngineer to run exactly one controlled small/medium PDF upload from:

`/Users/concm/prod_workspace/Luceon2026/testpdf`

Validation boundaries:

- run preflight first;
- choose one PDF only;
- upload once;
- observe task list/detail semantics and MinerU observability endpoints;
- continue until terminal state or clear system failure;
- stop immediately after the one upload;
- report whether live MinerU business progress is visible, still diagnostic-only, stale/unattributed, or absent.

Not authorized under Option A:

- pressure, batch, soak, or second upload;
- cleanup, repair, reparse, re-AI, failed-task mutation, or historical data mutation;
- Docker/DB/MinIO volume or data cleanup;
- MinerU restart/kill/ownership normalization;
- Ollama mutation;
- supervisor attach;
- config/secret/model/sample mutation;
- L3, pressure PASS, production-readiness, release-readiness, go-live claim.

### Option B

Do not upload yet. First dispatch a read-only stale-fallback-log hygiene review to decide whether `uat/scratch/mineru-api.log` should be excluded, renamed, or surfaced differently.

Tradeoff: lower runtime risk, but it delays the core question of whether live MinerU business progress is now observable.

### Option C

Hold runtime validation and continue only code-level diagnostics.

Tradeoff: lowest runtime touch, but it cannot answer the operator-facing observability question.

## Director Recommendation

Choose Option A.

Reason: sidecar transport has been restored, the current runtime preflight is clean, and the remaining question is empirical: during one real parse, does MinerU progress become visible and attributable? One controlled upload is the smallest useful validation. It is reversible at the workflow level because it does not authorize cleanup, repair, pressure, ownership normalization, model mutation, or readiness claims.

If the user gives no response after two heartbeat checks, Director may apply the conservative autonomous rule only to create a scoped TestAcceptanceEngineer task for Option A, provided the preflight remains clean. That autonomous action still must not claim production readiness or authorize any forbidden operation.

## Heartbeat Wait Evidence

- Wait evidence 1 recorded at 2026-05-14T09:35:50+0800 by Director heartbeat. No user response was present after this decision row was created. No autonomous task was issued yet.
