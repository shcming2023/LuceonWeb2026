# Task Brief: P1 MinerU-Only Recovery And Submit-Path Verification

- Task ID: `TASK-20260515-113628-P1-MinerU-Only-Recovery-And-Submit-Path-Verification`
- Created: 2026-05-15T11:36:28+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-15T11-36-28+0800_P1-MinerU-Only-Recovery-And-Submit-Path-Verification_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-15T11-28-06+0800_P1-MinerU-Submit-Path-Recovery-Authorization_DECISION.md`
- Based on diagnosis: `TaskAndReport/2026-05-15T11-12-51+0800_P1-Production-MinerU-Submit-Path-500-Read-Only-Diagnosis-And-Recovery-Plan_REPORT.md`

## Context

Production currently has a live MinerU submit-path blocker:

- direct MinerU `/health` is healthy;
- active-task diagnostics show no active parse queue or takeover work;
- the last submit-probe returned HTTP `500`;
- the durable admission circuit is open and new non-Markdown/PDF intake is blocked.

The user approved Option A: a scoped MinerU-only recovery plus exactly one submit-path verification. This task is authorized to mutate only the host MinerU API runtime, and only after confirming no active parse/AI work.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/development-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. Task 170 report and Director review
12. Task 171 report and Director review
13. Task 172 decision file
14. This task brief

If the task row, role file, or required evidence files are missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`.

## Objective

Recover the MinerU submit path with the smallest possible runtime mutation and produce evidence of one authorized submit-path verification.

## Allowed Operations

Allowed:

- read development and production status files, configs, logs, process/listener state, and task reports;
- in production, confirm active-task diagnostics are clean before mutation;
- capture current MinerU process/listener/tmux/log state;
- restart or relaunch only the host MinerU API session/process bound to port `8083`;
- use existing project ops script if appropriate: `bash ops/start-mineru-api.sh`;
- verify direct MinerU `/health`;
- run exactly one authorized dependency-health submit-probe through:
  - `http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true`
- inspect admission-circuit state after the one authorized probe;
- inspect upload-server health and active-task diagnostics after recovery;
- write the completion report and update the task row.

## Required Stop Conditions

Stop and write a blocked report if any of these occur:

- active-task diagnostics show active parse/AI work, queued parse/AI work, takeover-required work, or any state that makes recovery unsafe;
- MinerU process ownership is ambiguous enough that a MinerU-only restart could affect another service;
- restarting/relaunching MinerU would require Docker, DB, MinIO, Ollama, supervisor, sidecar, model, secret, config, or sample mutation;
- direct MinerU `/health` does not recover after the scoped MinerU-only restart/relaunch;
- the single authorized submit-probe fails again;
- more than one submit-probe would be needed to continue.

## Forbidden Operations

Forbidden:

- more than one submit-probe;
- PDF upload, Markdown upload, pressure/batch/soak/fresh serial validation, or any new user validation artifact;
- broad stack restart, Docker restart, Docker rebuild, Docker down/down-v/prune, upload-server restart, frontend restart, DB restart, MinIO restart, Ollama restart, supervisor/sidecar mutation, or model operation;
- deploy, rebuild, rollback, fast-forward production code, pull production code, or mutate repository files in production;
- close/reset admission circuit manually;
- cleanup, cancel, repair, retry, reparse, re-AI, takeover, automatic retry/requeue, or historical task mutation;
- DB/MinIO/Docker volume/data mutation, restore/import, object deletion/overwrite;
- settings, secrets, config, model, sample-library mutation;
- PRD truth, role contract, project state, or handoff changes;
- skeleton fallback weakening or silent degradation;
- declaring pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Required Report Structure

The report must include:

1. **Pre-Recovery Safety Check**
   - active-task diagnostics;
   - admission-circuit state;
   - direct MinerU `/health`;
   - process/tmux/listener/log state.

2. **Recovery Actions Performed**
   - exact commands run;
   - exact scope confirmation that only host MinerU API was restarted/relaunched;
   - timestamps and exit codes.

3. **Post-Recovery Verification**
   - direct MinerU `/health`;
   - upload health;
   - active-task diagnostics;
   - exactly one submit-probe result;
   - admission-circuit state after the probe.

4. **Outcome**
   - one of:
     - `RECOVERED_SUBMIT_PATH`;
     - `STILL_BLOCKED_AFTER_MINERU_ONLY_RECOVERY`;
     - `BLOCKED_BEFORE_MUTATION`;
     - `PARTIAL_RECOVERY_NEEDS_CODE_FIX`;
   - state whether PDF intake remains blocked.

5. **Recommended Next Actor**
   - Director review;
   - if recovered, recommend a read-only follow-up and no upload unless separately authorized;
   - if not recovered, recommend code-level diagnosis or user decision for broader recovery.

6. **Forbidden Operations Confirmation**
   - explicitly state no forbidden operation was performed.

## GitHub Sync

Do not fetch, pull, push, merge, or create commits unless Director explicitly instructs you. Work in the current synchronized workspace. Write the report and update the task row locally; Director will review and handle GitHub synchronization.

## Completion

Write:

`TaskAndReport/2026-05-15T11-36-28+0800_P1-MinerU-Only-Recovery-And-Submit-Path-Verification_REPORT.md`

Update row 173 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Notes include outcome and whether intake remains blocked.
