# Task Brief: P1 Production MinerU Submit-Path 500 Read-Only Diagnosis And Recovery Plan

- Task ID: `TASK-20260515-111251-P1-Production-MinerU-Submit-Path-500-Read-Only-Diagnosis-And-Recovery-Plan`
- Created: 2026-05-15T11:12:51+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-15T11-12-51+0800_P1-Production-MinerU-Submit-Path-500-Read-Only-Diagnosis-And-Recovery-Plan_REPORT.md`
- Based on TestAcceptanceEngineer report: `TaskAndReport/2026-05-15T10-59-51+0800_P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-15T11-12-51+0800_P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack_DIRECTOR_REVIEW.md`

## Context

Task 170 found a live production blocker: production MinerU `/health` is healthy and queues are empty, but a MinerU submit-probe returned HTTP `500`, opening the upload-server durable admission circuit. The UI now correctly reports that MinerU cannot currently accept files. New non-Markdown parse intake should not proceed until this submit-path condition is diagnosed and recovered or fixed.

This task is a read-only diagnosis and recovery-plan task. It does not authorize recovery, restart, repair, deploy, upload, submit-probe retry, or any production mutation.

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
12. This task brief

If the task row, role file, or required evidence files are missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`. Do not improvise from partial context.

## Objective

Determine, without mutating production, the likely cause and safest recovery route for the live MinerU submit-path HTTP `500` / open admission-circuit condition.

The report must answer:

1. Is the failure likely inside MinerU, upload-server submit-probe handling, network routing, stale circuit state, or service ownership/config mismatch?
2. What logs or existing state explain the HTTP `500`?
3. Is there evidence MinerU is still internally busy/recovering despite `/health` reporting healthy and queue counts zero?
4. What exact recovery options exist, from lowest-risk to highest-risk?
5. Which options require explicit user approval because they mutate production/runtime state?
6. Is a code fix likely needed, or is this currently an operational recovery issue?

## Allowed Read-Only Operations

Allowed:

- inspect development and production `git status`, `git log`, and source/config files;
- inspect current admission-circuit JSON and dependency-health without submit-probe;
- inspect upload-server health, active-task diagnostics, and direct MinerU `/health`;
- inspect Docker status with `docker compose ps`;
- inspect read-only process/listener status using `ps`, `lsof`, `tmux ls`, and similar non-mutating commands;
- inspect read-only logs:
  - Docker logs with `docker compose logs` or `docker logs`;
  - upload-server logs;
  - MinerU host logs under known log paths;
  - supervisor/sidecar logs if present;
- inspect code paths for dependency-health submit-probe, admission circuit, local MinerU adapter, and runtime ownership helper behavior;
- write the DevelopmentEngineer report and update the task row.

## Forbidden Operations

Forbidden:

- run dependency-health with `mineruSubmitProbe=true`;
- run any direct `POST /tasks` or submit-probe retry;
- upload PDF/Markdown or create any new validation artifact;
- close/reset admission circuit;
- restart, stop, kill, attach, start, or mutate MinerU, upload-server, Docker services, Ollama, MinIO, DB, supervisor, or sidecar;
- deploy, rebuild, rollback, fast-forward, pull production code, or mutate production files;
- cleanup, cancel, repair, retry, reparse, re-AI, takeover, or automatic retry/requeue;
- DB/MinIO/Docker volume/data mutation, restore/import, object deletion/overwrite, Docker prune/down/down -v;
- settings, secrets, config, model, sample-library mutation;
- PRD truth, role contract, project state, or handoff changes;
- skeleton fallback weakening or silent degradation;
- declaring pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Required Report Structure

Write a report with:

1. **Current Live State**
   - production HEAD/status;
   - service/container/process/listener state;
   - admission circuit state;
   - dependency-health without submit-probe;
   - active-task diagnostics;
   - direct MinerU `/health`.

2. **Evidence From Logs**
   - relevant upload-server log lines around the failed submit-probe timestamp;
   - relevant MinerU log lines around the same timestamp;
   - whether logs show accepted work, internal error, model/OCR/table pipeline state, queue state, port ownership issue, or missing context.

3. **Code/Config Path Analysis**
   - dependency-health submit-probe path;
   - MinerU adapter/API path;
   - admission circuit open/close criteria;
   - runtime ownership helper side effect and whether it needs a no-submit/read-only mode.

4. **Likely Root Cause Classification**
   - one of:
     - `MINERU_RUNTIME_STALE_OR_RECOVERING`;
     - `MINERU_SUBMIT_API_BROKEN`;
     - `UPLOAD_SERVER_PROBE_OR_ROUTING_BUG`;
     - `ADMISSION_CIRCUIT_STALE_ONLY`;
     - `SERVICE_OWNERSHIP_OR_CONFIG_MISMATCH`;
     - `INCONCLUSIVE_NEEDS_AUTHORIZED_PROBE_OR_RECOVERY`.

5. **Recovery Options**
   - list options from safest to riskiest;
   - for each, state whether it is read-only, requires user approval, or is forbidden before approval;
   - include exact commands only as proposed commands, not executed commands.

6. **Recommended Next Actor**
   - recommend Director user-decision row, TestAcceptanceEngineer validation, DevelopmentEngineer code fix, or scoped runtime recovery task.

7. **Forbidden Operations Confirmation**
   - explicitly state no forbidden operation was performed.

## GitHub Sync

Do not fetch, pull, push, merge, or create commits unless Director explicitly instructs you. Work in the current synchronized workspace. Write the report and update the task row locally; Director will review and handle GitHub synchronization.

## Completion

Write:

`TaskAndReport/2026-05-15T11-12-51+0800_P1-Production-MinerU-Submit-Path-500-Read-Only-Diagnosis-And-Recovery-Plan_REPORT.md`

Update row 171 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Notes include the recommended recovery route and whether user approval is required.
