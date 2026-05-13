# User Decision: P1 Next Step After MinerU Observation Hardening Validation

- Recorded at: 2026-05-14T05:40:51+0800
- Role: Director
- Decision ID: `TASK-20260514-054051-P1-Next-Step-After-MinerU-Observation-Hardening-Validation`
- Trigger: Task 104 accepted the exactly-one controlled upload validation, with residual diagnostic-only MinerU progress limitation.
- Current production HEAD: `159d80e Accept MinerU log observation hardening`
- Next Actor: User

## Current Facts

Task 104 validated exactly one production upload from `/Users/concm/prod_workspace/Luceon2026/testpdf`.

The important pass evidence:

- the task hit `log-observation-unreadable` while MinerU API was processing;
- the signal stayed `mineru-log-observation-diagnostic-only`;
- the task did not terminally fail or show an operator-visible false failed state;
- task reached `review-pending`;
- material reached `reviewing`;
- AI job reached `review-pending`;
- final active-task/admission/dependency surfaces were clean.

The remaining limitation:

- the UI still displayed `MinerU 已完成，但本次未捕获可归因业务进度日志`;
- this is truthful and no longer false failure, but it is not rich business progress.

## Why A Decision Is Needed

The project has cleared the narrow false-failed validation for one sample, but the original user concern included task-page observability: operators need to understand whether MinerU is actually progressing during long tasks.

Moving directly to pressure testing now would mix two questions:

- whether false-failed adjudication is fixed;
- whether long-running MinerU progress observability is good enough for unattended operation.

Those should stay separate.

## Options

### Option A: Dispatch A Read-Only Architect Observability Review (Director Recommended)

Assign Architect a read-only task to answer:

- where the authoritative MinerU business-progress signal should come from in the current deployment;
- whether current `fast-complete-no-business-signal` / diagnostic-only behavior is expected for small PDFs only or a broader log-source ownership gap;
- whether UI progress richness is fixable in code, requires sidecar/runtime ownership changes, or should be accepted as a product limitation;
- what minimum evidence is required before any broader serial or pressure validation.

No upload, no restart, no config change, no cleanup, no code change.

Why recommended:

It addresses the remaining operator-observability concern without spending more uploads or creating ambiguous pressure-test failures.

### Option B: Run Another Small Serial Validation

Authorize TestAcceptanceEngineer to run a very small serial validation, such as up to 3 PDFs one at a time, to see whether the diagnostic-only progress limitation repeats.

Risk:

This may produce more pass/fail data but may not explain why attributable progress is missing.

### Option C: Hold Current State

Accept Task 104 as enough for the false-failed defect and pause further work until manual operator review.

Risk:

The project remains without a clear answer on whether progress observability is sufficient for large unattended jobs.

### Option D: Start Pressure Testing

Not recommended now.

Risk:

Pressure testing before resolving or explicitly accepting the progress-observability boundary can recreate the old problem: long-running jobs become hard to interpret, and failures are harder to triage.

## Director Recommendation

Choose Option A.

If this decision item remains unanswered for two consecutive Director heartbeat/check-task cycles, Director may follow the standing no-long-term-blocker rule and issue the conservative read-only Architect task described in Option A. The automatic path must not authorize uploads, production mutation, pressure testing, restarts/rebuilds, cleanup, destructive operations, L3, production readiness, release readiness, go-live readiness, or production上线.

## User Decision

- Decision time: 2026-05-14T05:42:35+0800
- User response: "先治理 MinerU 进度可观测性"
- Recorded decision: `USER_APPROVED_OBSERVABILITY_GOVERNANCE_FIRST`

Director interpreted this as approval of the conservative Option A route: dispatch a read-only Architect task to map MinerU progress signal ownership and recommend the safest observability governance/implementation path before any broader validation.

Explicitly not authorized:

- upload validation;
- pressure, batch-concurrent, soak, broad stress, or long-run tests;
- source-code implementation;
- repair, reparse, re-AI, retry, cleanup, delete, rename, or historical mutation;
- destructive DB/MinIO/Docker volume/data operations;
- model pull/delete/replace, secret/config/env mutation, broad restart/rebuild/rollback;
- sample-file mutation;
- L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线 declaration.
