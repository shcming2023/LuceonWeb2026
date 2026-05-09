# Lucode Task: P0 MinerU Submit-Path 500 Circuit Breaker And Failure-State Handling

- Task ID: `TASK-20260510-075129-P0-MinerU-Submit-Path-500-Circuit-Breaker-And-Failure-State`
- Created At: `2026-05-10T07:51:29+0800`
- Created By: Lucia
- Next Actor: Lucode
- Priority: P0
- Status: 待执行
- Related Report: `TaskAndReport/2026-05-10T07-45-14+0800_P0-24-PDF-Pressure-Test-Failure-Field-Report_REPORT.md`
- Related Review: `TaskAndReport/2026-05-10T07-51-29+0800_P0-24-PDF-Pressure-Test-Failure_LUCIA_REVIEW.md`

## Objective

Address the release-blocking failure mode where MinerU `/health` remains healthy but the real submit path `/tasks` returns HTTP 500, causing a 24-PDF pressure batch to fully fail before any AI metadata job is created.

## Required Work

1. Read the field report and Lucia review.
2. Reproduce or confirm the failure with read-only checks first:
   - dependency-health with `mineruSubmitProbe=true`;
   - active-task diagnostics;
   - batch task summary for prefix `task-177833`.
3. Inspect source code paths for:
   - pre-parse dependency gating;
   - queue dequeue / next-task behavior after dependency failure;
   - MinerU submit failure handling;
   - local-timeout / 404 / task-record-lost failure semantics;
   - material status normalization after parse failure.
4. Implement the smallest safe code-level correction if the route is clear. Expected direction:
   - treat MinerU submit-probe failure as a blocking parse dependency failure;
   - stop or pause further queue submission while the submit path is failing, instead of cascading many tasks to `execution-failed`;
   - make failure state semantics explicit for task/material when MinerU timeout or task-record-lost is confirmed;
   - preserve strict no-silent-success behavior.
5. If a safe code correction is not clear, write a blocked report with exact evidence and a Director decision request.

## Boundaries

Allowed:

- source-code changes in the development repository;
- focused tests/smokes for dependency-health, queue circuit breaker, submit failure handling, and material status semantics;
- read-only production inspection.

Forbidden without separate Director approval:

- restarting MinerU, Docker, Ollama, MinIO, DB, or production services;
- deleting or mutating DB rows, MinIO objects, Docker volumes, task/material/artifact/log/sample data;
- creating new validation uploads;
- changing secrets, model selection, provider config, timeout policy, or production local override;
- declaring production release readiness.

## Required Checks

Run all applicable checks and report exact results:

- `git diff --check`
- focused server tests/smokes for the changed failure path
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`
- read-only dependency-health with `mineruSubmitProbe=true` if production is inspected

## Required Report

Create:

`TaskAndReport/2026-05-10T07-51-29+0800_P0-MinerU-Submit-Path-500-Circuit-Breaker-And-Failure-State_REPORT.md`

Report must include:

- branch and HEAD;
- files changed;
- exact failure classification;
- implemented behavior or blocker;
- test evidence;
- production read-only evidence if inspected;
- remaining risks;
- explicit statement that production release readiness is not claimed.

