# Task Brief: P0 MinIO Console Local-Only Binding Correction

- Task ID: `TASK-20260516-072305-P0-MinIO-Console-Local-Only-Binding-Correction`
- Created: `2026-05-16T07:23:05+0800`
- Created by: `Director`
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-16T07-23-05+0800_P0-MinIO-Console-Local-Only-Binding-Correction_REPORT.md`
- Related review: `TaskAndReport/2026-05-16T07-23-05+0800_P0-Production-Dirty-Source-Backup-Reconcile-And-Progress-Snapshot-Deploy_DIRECTOR_REVIEW.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`

## Context

Task 197 deployed the progress-snapshot implementation, but reconciliation of the previously dirty production override restored the tracked `docker-compose.override.yml` mapping:

```yaml
services:
  minio:
    ports:
      - "19001:9001"
```

Production now exposes the MinIO console on all interfaces:

- `9001/tcp -> 0.0.0.0:19001`
- `9001/tcp -> [::]:19001`

This conflicts with the repository-backed production runtime contract:

- `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md` says MinIO console must bind local-only as `127.0.0.1:19001:9001`;
- `docs/deploy/DEPLOY.md` says production local should use local-only binding for the MinIO console.

The previous dirty production override backup also shows the intended local-only mapping.

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
11. `TaskAndReport/2026-05-16T07-07-58+0800_P0-Production-Dirty-Source-Backup-Reconcile-And-Progress-Snapshot-Deploy_REPORT.md`
12. `TaskAndReport/2026-05-16T07-23-05+0800_P0-Production-Dirty-Source-Backup-Reconcile-And-Progress-Snapshot-Deploy_DIRECTOR_REVIEW.md`
13. this task brief.

If the task row, role file, or required evidence files are missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`.

## Objective

Restore the documented local-only MinIO console binding in source and production:

```yaml
services:
  minio:
    ports:
      - "127.0.0.1:19001:9001"
```

Then validate that production no longer binds MinIO console to `0.0.0.0` or `[::]`.

## Required Gates

Before any production config sync or MinIO container recreation, verify there is no active/queued/running/takeover-required parse or AI work.

Required read-only preflight evidence:

- upload health;
- dependency-health with `mineruSubmitProbe=false`;
- `/ops/mineru/active-task?queryApi=true`;
- active parse/AI DB summary if available.

If active/queued/running/takeover-required work is present, stop and write a blocked report. Do not restart MinIO while work is active.

## Allowed Files

Development workspace allowed source change:

- `docker-compose.override.yml`

Production workspace allowed source change:

- `/Users/concm/prod_workspace/Luceon2026/docker-compose.override.yml` via Git fast-forward from GitHub/main after the development commit is pushed.

Task/report files:

- this task report under `TaskAndReport/`;
- `TaskAndReport/TASK_TRACKING_LIST.md`.

## Allowed Operations

Allowed:

- update tracked `docker-compose.override.yml` in development workspace to local-only MinIO console binding;
- run `git diff --check`;
- run `docker compose config --services` and inspect effective MinIO port mapping;
- commit and push the source/report/ledger changes to GitHub;
- in production, verify clean worktree, pull fast-forward from GitHub/main;
- run `docker compose up -d --no-deps minio` or the closest equivalent that recreates only the `minio` service;
- inspect actual affected containers and report if Compose touches anything beyond `minio`;
- validate with `docker port cms-minio` or equivalent that `19001` is bound only to `127.0.0.1`;
- run read-only checks:
  - `/cms/`;
  - `/cms/tasks`;
  - upload health;
  - dependency-health with `mineruSubmitProbe=false`;
  - `/ops/mineru/active-task?queryApi=true`.

## Forbidden Operations

Forbidden:

- upload, pressure test, submit-probe, batch/soak/fresh serial validation, or validation material creation;
- retry, reparse, re-AI, cancel, repair, reset, takeover, failed-task repair, or automatic requeue;
- DB, MinIO object, MinIO bucket, Docker volume cleanup, Docker image prune, destructive data mutation, restore/import, or `docker compose down -v`;
- model pull/delete/replace, secret/config/sample mutation beyond the one allowed MinIO port binding config;
- broad service restart beyond the `minio` service;
- changing PRD truth, role contracts, project state, handoff, or release-boundary documents;
- claiming pressure PASS, L3, production readiness, release readiness, go-live readiness, or production上线.

## Required Report Evidence

The report must include:

1. **Initial State**
   - development HEAD;
   - production HEAD;
   - production `git status --short --branch`;
   - current `docker port cms-minio` evidence;
   - active-work gate result.

2. **Source Change**
   - exact diff summary for `docker-compose.override.yml`;
   - commands run and exit codes;
   - GitHub push status.

3. **Production Apply**
   - production pull command and result;
   - exact compose command used;
   - actual affected containers;
   - post-apply `docker port cms-minio` evidence.

4. **Read-Only Validation**
   - `/cms/` and `/cms/tasks` HTTP status;
   - upload health;
   - dependency-health status and proof submit-probe disabled;
   - active-task direct-check summary;
   - endpoint anomalies, if any.

5. **Outcome**
   - one of:
     - `MINIO_CONSOLE_LOCAL_ONLY_BINDING_RESTORED`;
     - `BLOCKED_ACTIVE_WORK_PRESENT`;
     - `BLOCKED_SOURCE_OR_PRODUCTION_DIRTY`;
     - `BLOCKED_COMPOSE_APPLY_FAILED`;
     - `BLOCKED_VALIDATION_FAILED`.

6. **Forbidden Operations Confirmation**
   - explicitly confirm no upload, pressure test, submit-probe, retry/reparse/re-AI/cancel/repair/reset, DB/MinIO object or volume cleanup, model/secret/sample mutation, broad restart, or readiness/release/go-live claim was performed.

## Completion

Write the report:

`TaskAndReport/2026-05-16T07-23-05+0800_P0-MinIO-Console-Local-Only-Binding-Correction_REPORT.md`

Update this task row in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Branch / HEAD populated;
- Notes include outcome, production HEAD, actual affected containers, and final MinIO port binding.

## GitHub Sync

Because this task changes source and repository report/ledger files, commit and push to GitHub after completion. Do not commit production backup artifacts or production-local data.
