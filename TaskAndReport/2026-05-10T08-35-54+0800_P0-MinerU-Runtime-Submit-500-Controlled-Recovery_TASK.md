# Lucode Task: P0 MinerU Runtime Submit-500 Controlled Recovery

- Task ID: `TASK-20260510-083554-P0-MinerU-Runtime-Submit-500-Controlled-Recovery`
- Created At: `2026-05-10T08:35:54+0800`
- Created By: Lucia
- Next Actor: Lucode
- Priority: P0
- Status: 待执行
- Related Director Decision: `TaskAndReport/2026-05-10T08-35-54+0800_P0-MinerU-Runtime-Submit-500-Recovery-Authorization_LUCIA_REVIEW.md`
- Related Blocker Review: `TaskAndReport/2026-05-10T08-31-41+0800_P0-MinerU-Submit-Circuit-Breaker-Production-Deployment-And-Manual-Test-Prep_LUCIA_REVIEW.md`

## Objective

Recover the production MinerU runtime submit path from the current release-blocking condition:

- MinerU `/health` is OK;
- MinerU submit probe through `dependency-health?mineruSubmitProbe=true` returns HTTP 500 and `blocking=true`;
- upload-server is already deployed and healthy.

The goal is to determine whether the MinerU submit path can be restored with a controlled runtime recovery so Director can later decide whether manual PDF testing may restart.

## Authorized Scope

Allowed:

- inspect production runtime state with read-only checks first;
- run the minimum necessary MinerU runtime recovery action needed to clear the submit-path HTTP 500;
- restart or recover only the MinerU runtime/API process or directly related MinerU runtime wrapper if required;
- use existing project ops scripts only if they are the narrowest appropriate recovery path;
- verify upload-server health after recovery;
- verify `dependency-health?mineruSubmitProbe=true` after recovery;
- verify active-task diagnostics after recovery;
- preserve production-local `docker-compose.override.yml`;
- record exact commands, before/after evidence, and final classification.

Prefer:

- read-only diagnosis before mutation;
- graceful service-level recovery before any stronger action;
- the narrowest MinerU-only recovery action over broad stack changes.

Forbidden without separate Director approval:

- DB row mutation or deletion;
- MinIO object mutation or deletion;
- Docker volume deletion, pruning, or recreation;
- failed 24 pressure-test task repair or reprocessing;
- creating a new validation upload;
- source code changes;
- secret, model/provider, timeout-policy, or production override changes;
- broad Docker stack restart/rebuild/rollback;
- restarting Ollama, MinIO, DB, or upload-server unless needed only for a read-only post-check failure and separately justified in the report;
- production release-readiness declaration.

## Required Result Classification

Report one of:

- `MINERU_RUNTIME_RECOVERED_MANUAL_TEST_PRECHECK_READY`: submit probe passes after controlled recovery, upload health OK, active-task diagnostics clean. This means Director may decide whether to restart manual testing; it is not release readiness.
- `MINERU_RUNTIME_RECOVERY_ATTEMPTED_STILL_BLOCKED`: scoped recovery was attempted, but submit probe remains blocking.
- `MINERU_RUNTIME_RECOVERY_BLOCKED`: safe scoped recovery could not be attempted within the authorized boundary.

## Required Checks

Before recovery:

- `git status --short --branch` in production;
- production HEAD and `origin/main`;
- inspect production-local dirty files without changing them;
- `curl -fsS http://localhost:8081/__proxy/upload/health`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'`;
- narrow MinerU runtime/API process/listener/status inspection sufficient to choose the smallest recovery action.

Recovery:

- run only the minimum necessary MinerU runtime recovery command(s);
- do not delete DB/MinIO/Docker volume/task/material/artifact/log/sample data.

After recovery:

- `curl -fsS http://localhost:8081/__proxy/upload/health`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'`;
- if available, read-only MinerU `/health` check;
- `git status --short --branch` in production;
- `git diff --check` in development before reporting.

## Required Report

Create:

`TaskAndReport/2026-05-10T08-35-54+0800_P0-MinerU-Runtime-Submit-500-Controlled-Recovery_REPORT.md`

Report must include:

- exact production path and production HEAD;
- production local dirty files preserved;
- before-recovery health/dependency/active-task evidence;
- exact recovery command(s);
- after-recovery health/dependency/active-task evidence;
- result classification;
- whether manual testing may restart as a next Director decision;
- explicit statement that no production release readiness is claimed;
- explicit statement of any skipped checks and why.

