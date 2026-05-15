# Task Brief: P1 MinerU Progress Snapshot Production Deployment And Read-Only Validation

- Task ID: `TASK-20260516-065643-P1-MinerU-Progress-Snapshot-Production-Deployment-And-Read-Only-Validation`
- Created: `2026-05-16T06:56:43+0800`
- Created by: `Director`
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-16T06-56-43+0800_P1-MinerU-Progress-Snapshot-Production-Deployment-And-Read-Only-Validation_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-16T06-49-06+0800_P1-MinerU-Progress-Snapshot-Production-Deployment-Decision_DECISION.md`
- Accepted implementation task: `TASK-20260516-062058-P1-MinerU-Progress-Snapshot-Contract-And-Active-Task-Reconciliation`
- Accepted implementation HEAD: `c6c5790`
- Current dispatch HEAD: `bb71553`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`

## Context

Task 192 diagnosed the long-running MinerU progress semantic lag as a missing cross-source contract rather than a simple page-copy issue. Task 193 implemented a normalized `progressSnapshot` contract, active-task direct MinerU / DB reconciliation, `db-behind-direct-mineru` lag semantics, terminal/idle stale-log distinction, readiness-only dependency-health boundary, and task-event log cleanup.

Director accepted Task 193 at code/test level only. The user has now approved Option A: scoped production deployment plus read-only validation.

This task must not become another pressure test. The purpose is to make the accepted progress-semantics code visible in production and prove the read-only surfaces expose the expected contract without submitting new work.

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
11. `TaskAndReport/2026-05-16T06-07-44+0800_P1-Pressure-Progress-Semantics-Root-Cause-Diagnosis_REPORT.md`
12. `TaskAndReport/2026-05-16T06-20-58+0800_P1-Pressure-Progress-Semantics-Root-Cause-Diagnosis_DIRECTOR_REVIEW.md`
13. `TaskAndReport/2026-05-16T06-20-58+0800_P1-MinerU-Progress-Snapshot-Contract-And-Active-Task-Reconciliation_REPORT.md`
14. `TaskAndReport/2026-05-16T06-49-06+0800_P1-MinerU-Progress-Snapshot-Contract-And-Active-Task-Reconciliation_DIRECTOR_REVIEW.md`
15. this task brief.

If the task row, required role file, or required evidence files are missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`.

## Objective

Deploy the accepted Task 193 progress-snapshot implementation to production and verify, with read-only checks only, that the production runtime exposes the new progress-semantics contract.

## Required Preflight Gate

Before any production rebuild/restart, verify the production runtime has no active or queued parse/AI work.

Minimum required preflight evidence:

- production `git status --short --branch`;
- production HEAD and whether `c6c5790` is an ancestor or current source is behind it;
- `docker compose ps` or equivalent container status;
- read-only upload health;
- read-only dependency-health with no MinerU submit-probe;
- read-only `/ops/mineru/active-task` with direct check enabled;
- confirmation there are no active/queued/running/takeover-required parse or AI tasks.

If active/queued/running/takeover-required work is present, stop and write a blocked report. Do not rebuild/restart while work is active.

## Allowed Operations

Allowed:

- in the development workspace, run `git status --short --branch`, `git fetch origin`, and `git pull --ff-only origin main`;
- in production, inspect git status, HEAD, and compose service names;
- in production, sync source to current `origin/main` only by fast-forward or another non-overwriting method that preserves unrelated local changes;
- if production has uncommitted local changes that would be overwritten, stop and write a blocked report;
- run `docker compose config --services`;
- rebuild/restart only the minimum required services for Task 193 code to become live. Expected services are `upload-server` and `cms-frontend`; if service names differ, inspect and report the exact names used;
- run `docker compose up -d --build upload-server cms-frontend` only if those services exist and the preflight gate is clear;
- use read-only HTTP checks against production, including:
  - `/cms/`;
  - `/cms/tasks`;
  - upload health;
  - dependency-health without submit-probe;
  - `/ops/mineru/active-task` with direct check enabled;
  - `/ops/mineru/log-channel-ownership`;
- capture concise response evidence that proves the new `progressSnapshot` fields and lag/freshness/source semantics are visible where applicable;
- write the completion report and update this task row.

## Forbidden Operations

Forbidden:

- upload, manual pressure test, batch/soak/fresh serial validation, or creation of new validation materials;
- `mineruSubmitProbe=true`, `RUN_MINERU_SUBMIT_PROBE=1`, `--submit-probe`, or any submit-probe equivalent;
- retry, reparse, re-AI, cancel, repair, reset, takeover, failed-task repair, or automatic requeue;
- DB, MinIO, Docker volume, Docker image prune, data cleanup, `docker compose down -v`, destructive mutation, restore/import, or sample-library mutation;
- MinerU/Ollama model pull/delete/replace or secret/config mutation;
- broad service restart beyond the minimum required services named above;
- PRD truth, role contract, project state, handoff, or release-boundary changes;
- claiming pressure PASS, L3, production readiness, release readiness, go-live readiness, or production上线.

## Required Validation Evidence

The report must include:

1. **Preflight State**
   - dev HEAD;
   - production HEAD before sync;
   - production `git status --short --branch`;
   - active/queued/running/takeover-required check result;
   - whether deploy was allowed or blocked by the preflight gate.

2. **Source Sync**
   - exact commands used;
   - production HEAD after sync;
   - confirmation that accepted implementation `c6c5790` is included;
   - whether any local changes existed and how they were handled.

3. **Deployment**
   - compose services discovered;
   - exact rebuild/restart command;
   - affected containers only;
   - post-deploy container health/status.

4. **Read-Only Runtime Validation**
   - `/cms/` and `/cms/tasks` HTTP status;
   - upload health status;
   - dependency-health status and proof no submit-probe was used;
   - `/ops/mineru/active-task` response summary including direct-check mode and any `progressSnapshot` fields present;
   - `/ops/mineru/log-channel-ownership` response summary including stale/idle/terminal interpretation if present;
   - observed endpoint latency or anomalies, especially for `/ops/mineru/active-task` direct check.

5. **Outcome**
   - one of:
     - `PRODUCTION_PROGRESS_SNAPSHOT_DEPLOYED_READ_ONLY_VALIDATED`;
     - `BLOCKED_ACTIVE_WORK_PRESENT`;
     - `BLOCKED_PRODUCTION_SOURCE_DIRTY`;
     - `BLOCKED_SYNC_FAILED`;
     - `BLOCKED_DEPLOY_FAILED`;
     - `BLOCKED_READ_ONLY_VALIDATION_FAILED`.

6. **Forbidden Operations Confirmation**
   - explicitly state no upload, pressure test, submit-probe, retry/reparse/re-AI/cancel/repair/reset, DB/MinIO/Docker volume cleanup, model/secret/config/sample mutation, or release/readiness claim was performed.

## Completion

Write the report:

`TaskAndReport/2026-05-16T06-56-43+0800_P1-MinerU-Progress-Snapshot-Production-Deployment-And-Read-Only-Validation_REPORT.md`

Update this task row in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Branch / HEAD populated;
- Notes include outcome, production HEAD, services rebuilt/restarted, and read-only validation summary.

## GitHub Sync

Because this task changes repository report/ledger files, DevelopmentEngineer must commit and push the report and ledger update to GitHub after completion. Do not merge branches; use `main` according to the current project contract unless the task row or Director later says otherwise.
