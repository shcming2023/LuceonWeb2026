# User Decision: P1 Task Detail Progress Hardening One Upload Validation Authorization

- Decision ID: `TASK-20260514-122944-P1-Task-Detail-Progress-Hardening-One-Upload-Validation-Authorization`
- Created: 2026-05-14T12:29:44+0800
- Created by: Director
- Current status: `PENDING_USER_DECISION`
- Based on Director review: `TaskAndReport/2026-05-14T12-29-44+0800_P1-Task-Detail-Progress-Hardening-Production-Deployment-And-Read-Only-Runtime-Validation_DIRECTOR_REVIEW.md`

## Current Facts

Task 124 deployed the accepted Task 123 code path to production and passed read-only runtime validation:

- production HEAD is `5ca2615 Accept task detail progress hardening`;
- frontend `/cms/` is HTTP 200;
- upload health is OK;
- dependency-health is `ok=true`, `blocking=false`;
- MinerU admission circuit is closed;
- active task is idle;
- direct MinerU is healthy;
- `luceon-mineru` and `luceon-sidecar` remain present;
- port `8083` is owned by the production MinerU process with configured log files;
- `/__proxy/upload/ops/dependency-repair/status` now returns HTTP 200 with structured `SUPERVISOR_UNAVAILABLE`, not HTTP 503.

What remains unproven is the user-facing behavior during an actual fresh parse:

- whether task detail now surfaces fine-grained MinerU progress under `当前进展`;
- whether task list and task detail progress semantics are consistent during processing;
- whether browser console noise from read-only dependency repair polling is reduced in the real UI session;
- whether terminal state remains clean after the deployed detail-page hardening.

## Decision Needed

Please choose the next validation scope.

## Option A: Exactly One Controlled Upload Validation (Director Recommended)

Authorize TestAcceptanceEngineer to run exactly one controlled small/medium PDF upload from:

`/Users/concm/prod_workspace/Luceon2026/testpdf`

Validation boundary:

- preflight first: production HEAD, health, dependency-health, admission circuit, active-task, direct MinerU, tmux ownership, 8083 ownership;
- choose one small/medium PDF only;
- upload once through the UI or documented production route;
- observe task list and task detail page during processing;
- specifically verify detail overview label `当前进展` and whether fine-grained MinerU progress appears there;
- observe browser console behavior around dependency-repair status polling;
- observe log-channel/global-observation surfaces during and after processing;
- stop after one terminal state or clear systemic failure;
- write a TestAcceptanceEngineer report and return to Director review.

Forbidden in Option A:

- second upload;
- pressure, batch, soak, or long-run test;
- failed-task repair, reparse, re-AI, cleanup, or data deletion;
- destructive DB/MinIO/Docker volume/data mutation;
- MinerU/Ollama/supervisor mutation;
- model/config/secret/sample mutation;
- L3, pressure PASS, production readiness, release readiness, or go-live claim.

Why recommended:

- It directly tests the residual risk left by Task 124.
- It is narrow, observable, and bounded to one new sample.
- It gives real UI/runtime evidence for the exact issue the user flagged: task-page progress semantics.

## Option B: Hold Upload, Do Only Browser Read-Only Smoke

Authorize a read-only browser check of existing task pages and current console behavior only.

This is lower risk but cannot prove in-flight MinerU detail progress because no task is currently processing.

## Option C: Pause This Line

Pause validation here and leave the deployed code as code/runtime-surface accepted only.

This avoids any new production data but leaves the original UX concern unresolved.

## Director Recommendation

Choose Option A.

Because this creates a new production upload record, Director will wait for explicit user approval rather than auto-advancing it from heartbeat silence.
