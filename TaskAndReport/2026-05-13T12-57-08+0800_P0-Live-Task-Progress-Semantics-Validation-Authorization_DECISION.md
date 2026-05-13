# User Decision Required: P0 Live Task Progress Semantics Validation Authorization

- Decision ID: `TASK-20260513-125708-P0-Live-Task-Progress-Semantics-Validation-Authorization`
- Created At: `2026-05-13T12:57:08+0800`
- Recorded By: Director
- Status: 挂起
- Next Actor: User
- Related Task:
  - `TASK-20260513-124614-P0-Post-Sync-Production-Fast-Forward-And-Runtime-Validation`

## Decision Boundary

Task 83 confirmed that the accepted Task 77/78/79 code path is now deployed in production and non-destructive runtime surfaces are healthy.

However, current production DB task inventory has no task with populated `progressSemantics`. This means task-page MinerU progress semantics are deployed, but were not demonstrated against a live/current task.

Creating a live validation task requires a controlled upload, which was not authorized by Task 83 and should be decided explicitly.

## Options Considered

### Option A: Authorize One Controlled Live-Task Validation Upload

Authorize a TestAcceptanceEngineer task to perform exactly one controlled validation upload from the read-only external sample library or another user-approved local sample.

Required boundaries:

- preflight must pass before upload;
- no active parse/AI work before upload;
- sample should be small/medium and likely to emit MinerU progress logs quickly;
- stop after one upload;
- observe task detail/API MinerU progress semantics and terminal state;
- record whether task reaches `review-pending`, `completed`, `failed`, or remains running;
- no pressure test, pressure retry, failed-task repair, cleanup, destructive mutation, model operation, L3, pressure PASS, or release-readiness declaration.

Director recommendation: Option A.

Reason: this is the smallest meaningful next validation after Task 83. It checks the exact user-visible observability gap the user previously highlighted, without reopening the 24-PDF pressure track.

### Option B: Hold Live-Task Validation

Do not create any validation upload. Keep the current state as non-destructive runtime-surface pass only.

This is safest operationally, but leaves the deployed progress-semantics work unobserved in production.

### Option C: Request A Short TestAcceptanceEngineer Plan First

Ask TestAcceptanceEngineer to write a short validation plan before authorizing any upload.

This adds one planning step and may be useful if the user wants sample choice and stop rules reviewed before runtime action.

## User Decision

Pending.

## Director Interpretation

Pending user response.

## Authorized Next Action

None until user decides.

## Explicitly Not Authorized

Production release readiness, L3 acceptance, pressure PASS, 24-PDF pressure retry/test, failed-task repair, destructive DB/MinIO/Docker volume/data operations, model operations, secret changes, broad restart/rollback, sample-library mutation, or multiple validation uploads.

## Next Actor

`User`

## Required Output

User chooses Option A, B, C, or provides a different instruction.
