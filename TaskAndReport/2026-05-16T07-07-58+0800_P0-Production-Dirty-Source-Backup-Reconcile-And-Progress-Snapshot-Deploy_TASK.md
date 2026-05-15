# Task Brief: P0 Production Dirty Source Backup Reconcile And Progress Snapshot Deploy

- Task ID: `TASK-20260516-070758-P0-Production-Dirty-Source-Backup-Reconcile-And-Progress-Snapshot-Deploy`
- Created: `2026-05-16T07:07:58+0800`
- Created by: `Director`
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-16T07-07-58+0800_P0-Production-Dirty-Source-Backup-Reconcile-And-Progress-Snapshot-Deploy_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-16T07-05-35+0800_P0-Production-Dirty-Source-Reconciliation-Authorization_DECISION.md`
- Related blocked deployment task: `TASK-20260516-065643-P1-MinerU-Progress-Snapshot-Production-Deployment-And-Read-Only-Validation`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`

## Context

Task 195 correctly stopped production deployment because the production checkout was behind `origin/main` by 37 commits and had uncommitted tracked source modifications.

The user approved Option A: preserve the dirty production source state outside the Git repo, then reconcile production source and continue the narrowly scoped progress-snapshot deployment/read-only validation.

This task is authorized specifically to clean tracked production source changes after backup. It is not authorization for data cleanup, task repair, uploads, pressure testing, submit-probe, broad restart, or release/readiness claims.

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
11. `TaskAndReport/2026-05-16T06-56-43+0800_P1-MinerU-Progress-Snapshot-Production-Deployment-And-Read-Only-Validation_REPORT.md`
12. `TaskAndReport/2026-05-16T07-05-35+0800_P1-MinerU-Progress-Snapshot-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`
13. `TaskAndReport/2026-05-16T07-05-35+0800_P0-Production-Dirty-Source-Reconciliation-Authorization_DECISION.md`
14. this task brief.

If the task row, role file, or required evidence files are missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`.

## Objective

Safely preserve production dirty source state, clean only backed-up tracked source modifications, fast-forward production source to current `origin/main`, deploy the accepted progress-snapshot implementation, and validate read-only runtime surfaces.

## Required Gates

### Gate 1: Runtime Active-Work Gate

Before any production source mutation, run read-only checks to confirm there is no active/queued/running/takeover-required parse or AI work.

Required evidence:

- upload health;
- dependency-health with `mineruSubmitProbe=false`;
- `/ops/mineru/active-task?queryApi=true`;
- DB/task summary or equivalent active parse/AI summary if available.

If active/queued/running/takeover-required work is present, stop and write a blocked report. Do not mutate production source.

### Gate 2: Backup Gate

Before cleaning any tracked dirty source files, create a timestamped backup outside the production Git repo, under:

`/Users/concm/prod_workspace/Luceon2026-source-backups/`

The backup directory must include:

- `git-status.txt`;
- `head.txt` with production `HEAD`, `origin/main`, branch, and timestamp;
- `dirty-files.txt`;
- `dirty-stat.txt`;
- `dirty.patch` containing the full tracked diff;
- copies of every dirty tracked file, preserving enough path context to restore manually.

If the dirty diff contains apparent secrets, tokens, passwords, or private credentials, do not print those values in the report. Only report the file path and sensitivity type.

After backup creation, verify the backup files exist and are readable. If backup verification fails, stop and write a blocked report.

### Gate 3: Source Reconciliation Gate

After backup verification, clean only the backed-up tracked dirty files by explicit path.

Allowed pattern:

- use `git restore -- <explicit backed-up tracked file paths>` or equivalent explicit-path restore;
- then run `git status --short --branch`;
- then run `git pull --ff-only origin main`.

Do not use `git reset --hard`.

If new dirty tracked files or blocking untracked files appear, stop and write a blocked report rather than broad-cleaning the workspace.

### Gate 4: Pre-Restart Active-Work Gate

After source reconciliation and immediately before any Docker Compose rebuild/restart, re-run the active-work gate. If active work appears, stop and report before rebuild/restart.

## Allowed Operations

Allowed:

- in development workspace: `git status --short --branch`, `git fetch origin`, `git pull --ff-only origin main`;
- in production workspace: inspect git status, HEAD, dirty tracked files, and compose service names;
- create backup files outside the Git repo under `/Users/concm/prod_workspace/Luceon2026-source-backups/`;
- restore only backed-up tracked dirty source files by explicit path;
- fast-forward production source to current `origin/main`;
- run `docker compose config --services`;
- rebuild/restart only the minimum services required for Task 193 to become live, expected:
  - `upload-server`
  - `cms-frontend`
- if both expected services exist, run:
  - `docker compose up -d --build upload-server cms-frontend`
- run read-only HTTP checks against production:
  - `/cms/`;
  - `/cms/tasks`;
  - upload health;
  - dependency-health with `mineruSubmitProbe=false`;
  - `/ops/mineru/active-task?queryApi=true`;
  - `/ops/mineru/log-channel-ownership`;
- write the report and update the task row;
- commit and push repository report/ledger updates to GitHub.

## Forbidden Operations

Forbidden:

- `git reset --hard`;
- deleting untracked production files without a separate Director task;
- upload, manual pressure test, batch/soak/fresh serial validation, or creation of validation materials;
- `mineruSubmitProbe=true`, `RUN_MINERU_SUBMIT_PROBE=1`, `--submit-probe`, or any submit-probe equivalent;
- retry, reparse, re-AI, cancel, repair, reset, takeover, failed-task repair, or automatic requeue;
- DB, MinIO, Docker volume cleanup, Docker image prune, destructive data mutation, restore/import, or `docker compose down -v`;
- MinerU/Ollama model pull/delete/replace or secret/config/sample mutation;
- broad service restart beyond the minimum required services named above;
- changing PRD truth, role contracts, project state, handoff, or release-boundary documents;
- claiming pressure PASS, L3, production readiness, release readiness, go-live readiness, or production上线.

## Required Report Evidence

The report must include:

1. **Initial State**
   - development HEAD;
   - production HEAD before reconciliation;
   - production `origin/main`;
   - production `git status --short --branch`;
   - dirty tracked file list;
   - active-work gate result.

2. **Backup Evidence**
   - backup directory path;
   - list of backup artifacts created;
   - backup verification result;
   - whether any sensitive-looking values were detected, without printing the values.

3. **Source Reconciliation**
   - explicit file paths restored;
   - exact commands used;
   - production status after restore;
   - production HEAD after fast-forward;
   - confirmation that accepted implementation `c6c5790` and dispatch/review commits through current `origin/main` are included.

4. **Deployment**
   - compose services discovered;
   - exact rebuild/restart command;
   - affected containers only;
   - post-deploy container status/health.

5. **Read-Only Validation**
   - `/cms/` and `/cms/tasks` HTTP status;
   - upload health status;
   - dependency-health status and proof submit-probe was disabled;
   - `/ops/mineru/active-task?queryApi=true` summary and any `progressSnapshot` fields present;
   - `/ops/mineru/log-channel-ownership` summary and any `progressSnapshot` fields present;
   - endpoint latency or anomalies.

6. **Outcome**
   - one of:
     - `PRODUCTION_DIRTY_SOURCE_BACKED_UP_RECONCILED_PROGRESS_SNAPSHOT_DEPLOYED_READ_ONLY_VALIDATED`;
     - `BLOCKED_ACTIVE_WORK_PRESENT`;
     - `BLOCKED_BACKUP_FAILED`;
     - `BLOCKED_SOURCE_RECONCILIATION_FAILED`;
     - `BLOCKED_DEPLOY_FAILED`;
     - `BLOCKED_READ_ONLY_VALIDATION_FAILED`.

7. **Forbidden Operations Confirmation**
   - explicitly confirm no upload, pressure test, submit-probe, retry/reparse/re-AI/cancel/repair/reset, DB/MinIO/Docker volume cleanup, model/secret/config/sample mutation, broad restart, or readiness/release/go-live claim was performed.

## Completion

Write the report:

`TaskAndReport/2026-05-16T07-07-58+0800_P0-Production-Dirty-Source-Backup-Reconcile-And-Progress-Snapshot-Deploy_REPORT.md`

Update this task row in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Branch / HEAD populated;
- Notes include outcome, backup path, production HEAD before/after, services rebuilt/restarted, and read-only validation summary.

## GitHub Sync

Because this task changes repository report/ledger files, commit and push the report and ledger update to GitHub after completion. Do not commit backup artifacts or production-local files.
