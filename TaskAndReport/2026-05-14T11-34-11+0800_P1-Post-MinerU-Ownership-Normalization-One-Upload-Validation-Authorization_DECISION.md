# User Decision Required: P1 Post MinerU Ownership Normalization One Upload Validation Authorization

- Task ID: `TASK-20260514-113411-P1-Post-MinerU-Ownership-Normalization-One-Upload-Validation-Authorization`
- Decision created: 2026-05-14T11:34:11+0800
- Created by: Director
- Current Next Actor: `User`
- Based on accepted review: `TaskAndReport/2026-05-14T11-34-11+0800_P1-MinerU-Ownership-Normalization-Scoped-Runtime-Recovery_DIRECTOR_REVIEW.md`

## Current Facts

Task 120 normalized MinerU process/log ownership:

- current MinerU listener on port `8083` is now under `luceon-mineru`;
- the process cwd is `/Users/concm/prod_workspace/Luceon2026`;
- stdout/stderr are attached to `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log`;
- `luceon-sidecar` is present;
- direct MinerU health, upload health, dependency-health, admission circuit, and active-task surfaces are healthy/nonblocking/idle.

The remaining proof gap is not process ownership. The remaining proof gap is whether a real upload now produces live, attributable MinerU progress semantics visible through the task page and observability endpoints.

## Why A User Decision Is Needed

The next useful validation requires creating exactly one new production upload/material/task from the local sample directory. That is not destructive, but it is still a production runtime mutation and should be explicitly authorized.

## Options

### Option A: Recommended

Authorize TestAcceptanceEngineer to run exactly one controlled small/medium PDF upload from:

`/Users/concm/prod_workspace/Luceon2026/testpdf`

The task must:

- run strict preflight first;
- upload at most one PDF;
- wait for terminal state or clear blocked evidence;
- observe the task page/list/detail progress semantics;
- observe `/ops/mineru/log-channel-ownership` and `/ops/mineru/global-observation` during processing and after terminal state;
- verify whether the configured MinerU logs now provide fresh attributable business progress for a real upload;
- stop immediately on system-level failure or ambiguous active work;
- report the exact sample path, size, hash, task/material/MinerU/AI IDs, browser/page observations, endpoint observations, final state, and residual risk.

Still not authorized under Option A:

- pressure, batch, soak, or long-run validation;
- second upload;
- cleanup, repair, reparse, re-AI, or historical task mutation;
- destructive DB/MinIO/Docker volume/data operation;
- Docker down/down-v;
- MinerU ownership mutation;
- Ollama mutation;
- supervisor attach;
- model/config/secret/sample mutation;
- L3, production-readiness, release-readiness, pressure PASS, go-live readiness, or production上线 claim.

### Option B

Hold after ownership normalization and do not create another upload yet.

Impact: process/log ownership is improved, but the user-facing progress-observability goal remains unproven for a real upload.

### Option C

Request another read-only runtime monitoring pass first.

Impact: safer but likely lower value, because idle monitoring already shows the log channel becomes stale when no real work is running. The remaining question needs a real controlled upload.

## Director Recommendation

Choose Option A.

Reason: the process ownership blocker has been removed, and the next smallest meaningful validation is one real upload, not a pressure test. This keeps the blast radius tight while testing the exact user-facing objective: whether MinerU progress semantics are now observable during real processing.

If the standing heartbeat auto-progress rule is invoked after two unanswered wakeups, Director may only choose this Option A if preflight is clean and the task remains exactly one upload with all restrictions above. It still must not declare readiness, L3, pressure PASS, or go-live.

## User Decision Recorded

- Decision recorded: 2026-05-14T11:37:27+0800
- User decision: `APPROVED_OPTION_A`
- Director action: issue a scoped TestAcceptanceEngineer task for exactly one controlled upload validation after MinerU ownership normalization.

The approved scope is limited to one small/medium PDF upload from `/Users/concm/prod_workspace/Luceon2026/testpdf`, strict preflight, task-page/list/detail observation, canonical MinerU observability endpoint observation during and after processing, terminal or blocked evidence collection, and a completion report.

This decision still does not authorize pressure, batch, soak, long-run validation, a second upload, cleanup, repair, reparse, re-AI, historical task mutation, destructive DB/MinIO/Docker volume/data operation, Docker down/down-v, MinerU/Ollama/supervisor mutation, model/config/secret/sample mutation, L3, production-readiness, release-readiness, pressure PASS, go-live readiness, or production上线 claim.
