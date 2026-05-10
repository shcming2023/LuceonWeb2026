# Lucode Task: P0 MinerU Submit Circuit Breaker Production Deployment And Manual Test Prep

- Task ID: `TASK-20260510-081906-P0-MinerU-Submit-Circuit-Breaker-Production-Deployment-And-Manual-Test-Prep`
- Created At: `2026-05-10T08:19:06+0800`
- Created By: Lucia
- Next Actor: Lucode
- Priority: P0
- Status: 待执行
- Related Decision: `TaskAndReport/2026-05-10T08-19-06+0800_P0-MinerU-Submit-Path-500-Production-Deployment-Recovery-Decision_LUCIA_REVIEW.md`
- Related Accepted Code Review: `TaskAndReport/2026-05-10T08-12-29+0800_P0-MinerU-Submit-Path-500-Circuit-Breaker-And-Failure-State_LUCIA_REVIEW.md`

## Objective

Deploy the accepted MinerU submit-path circuit-breaker code to production and determine whether Director can safely restart manual testing.

## Authorized Scope

Allowed:

- sync production workspace to the accepted main commit;
- rebuild/restart only `upload-server` to apply the accepted Task 64 code;
- run read-only production checks:
  - upload health;
  - dependency-health with `mineruSubmitProbe=true`;
  - active-task diagnostics;
  - code HEAD/deployed commit confirmation;
- provide a clear manual-test readiness recommendation.

Forbidden without separate Director approval:

- restarting MinerU, Ollama, MinIO, DB, or broad Docker stack;
- DB/MinIO/Docker volume/task/material/artifact/log/sample deletion or mutation;
- repairing or reprocessing the failed 24 pressure-test tasks;
- creating new automated validation uploads;
- changing secrets, provider/model selection, timeout policy, or production local override;
- declaring production release readiness.

## Required Result Classification

Report one of:

- `DEPLOYED_MANUAL_TEST_READY`: upload-server deployed and dependency-health submit probe passes.
- `DEPLOYED_BUT_MINERU_SUBMIT_STILL_BLOCKED`: upload-server deployed, circuit-breaker code active, but MinerU submit probe still returns HTTP 500 or another blocking failure; manual PDF testing should not continue unless Director knowingly accepts expected blocking behavior.
- `DEPLOYMENT_BLOCKED`: deployment could not be completed safely.

## Required Checks

- `git status --short --branch` in production before and after;
- production HEAD and origin/main comparison;
- `docker compose up -d --build upload-server` or equivalent minimal upload-server rebuild/restart only;
- `curl -fsS http://localhost:8081/__proxy/upload/health`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'`;
- `git diff --check` in development before reporting.

## Required Report

Create:

`TaskAndReport/2026-05-10T08-19-06+0800_P0-MinerU-Submit-Circuit-Breaker-Production-Deployment-And-Manual-Test-Prep_REPORT.md`

Report must include:

- production path and deployed HEAD;
- production local dirty files preserved;
- exact deploy command(s);
- health/dependency-health/active-task outputs;
- result classification;
- whether manual testing should start now;
- remaining blocker if any;
- explicit statement that production release readiness is not claimed.

