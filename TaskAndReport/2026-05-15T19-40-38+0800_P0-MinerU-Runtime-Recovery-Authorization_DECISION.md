# User Decision Required: P0 MinerU Runtime Recovery Authorization

- Task ID: `TASK-20260515-194038-P0-MinerU-Runtime-Recovery-Authorization`
- Created: 2026-05-15T19:40:38+0800
- Created by: `Director`
- Next Actor: `User`
- Based on report: `TaskAndReport/2026-05-15T19-29-28+0800_P0-MinerU-Runtime-Loss-And-Pressure-State-Read-Only-Diagnosis_REPORT.md`
- Based on review: `TaskAndReport/2026-05-15T19-40-38+0800_P0-MinerU-Runtime-Loss-Read-Only-Diagnosis_DIRECTOR_REVIEW.md`

## Current Facts

The 24-PDF pressure run is blocked by MinerU runtime loss:

- 5 pressure tasks reached `review-pending`.
- Current pressure task state has drifted to 5 `review-pending`, 17 `failed`, and 2 `pending`.
- MinerU is not listening on `8083`.
- Direct MinerU health fails with connection refused.
- `com.office.mineru` LaunchAgent exists but is `not running`.
- No expected tmux MinerU session is visible.
- Upload-server and Ollama remain reachable.

This is not pressure PASS, L3, release readiness, production readiness, or go-live evidence.

## Decision Options

### Option A: Scoped MinerU Runtime Relaunch Only

Authorize DevelopmentEngineer to perform a narrowly scoped MinerU-only runtime relaunch and read-only verification.

Allowed:

- decide and use one canonical owner for this recovery;
- prefer repo-documented owner `luceon-mineru` unless the task proves the host LaunchAgent path is safer;
- relaunch only the host MinerU API required for `127.0.0.1:8083` / `host.docker.internal:8083`;
- verify direct `/health`, dependency-health without submit-probe, active-task diagnostics, listener/session evidence, and log ownership.

Still forbidden:

- manual submit-probe;
- task retry/reparse/re-AI/cancel/repair/reset;
- DB/MinIO/Docker cleanup;
- Docker down/down-v/prune;
- upload/pressure run;
- readiness/go-live claim.

### Option B: MinerU Relaunch Plus Exactly One Submit-Path Probe

Authorize Option A plus exactly one side-effecting MinerU submit-probe after direct health is restored.

Still forbidden:

- task retry/reparse/re-AI/cancel/repair/reset;
- DB/MinIO/Docker cleanup;
- upload/pressure run;
- readiness/go-live claim.

### Option C: Hold / No Mutation

Do not authorize recovery now. Keep project blocked until manual operator intervention or further discussion.

### Option D: Broader Recovery Including Task Reconciliation

Authorize runtime recovery plus pressure-task retry/reparse/re-AI or state reconciliation.

Director does not recommend this now because the runtime owner is not yet stable.

## Director Recommendation

Choose Option A now.

Reason:

- It restores the missing foundation with the smallest blast radius.
- It does not mutate DB/MinIO/task state.
- It allows us to confirm whether MinerU can be owned and observed reliably before deciding on submit-probe or task retry/reparse.
- It keeps the pressure-test evidence honest: we recover the service first, then separately decide whether to re-run or reconcile the 19 unresolved pressure tasks.

If there are two Director heartbeats with no user response, Director may proceed with Option A under the existing conservative auto-progress rule, because it is scoped, reversible, and does not mutate task data. Director may not auto-authorize Option B or D.

## User Decision Recorded

- Decision time: 2026-05-15T20:12:31+0800
- User decision: approved Option A.

Authorized scope:

- issue a DevelopmentEngineer task for scoped MinerU-only runtime relaunch;
- use one canonical owner for this recovery, with repo-documented `luceon-mineru` preferred;
- verify direct MinerU health, dependency-health without submit-probe, active-task diagnostics, listener/session evidence, and log ownership.

Still not authorized:

- manual or extra MinerU submit-probe;
- upload or pressure run;
- task retry/reparse/re-AI/cancel/repair/reset;
- DB/MinIO/Docker cleanup or volume mutation;
- Docker down/down-v/prune;
- broad service restart/redeploy;
- readiness, pressure PASS, L3, production readiness, production上线, or go-live claim.
