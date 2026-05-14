# Task Brief: P1 MinerU Ownership Normalization Scoped Runtime Recovery

- Task ID: `TASK-20260514-111219-P1-MinerU-Ownership-Normalization-Scoped-Runtime-Recovery`
- Created: 2026-05-14T11:12:19+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-14T11-12-19+0800_P1-MinerU-Ownership-Normalization-Scoped-Runtime-Recovery_REPORT.md`
- Decision authorization: `TaskAndReport/2026-05-14T11-09-27+0800_P1-MinerU-Ownership-Normalization-Authorization_DECISION.md`

## Context

Task 118 accepted the deployed stale fallback hygiene fix. Production no longer treats old `uat/scratch/mineru-api.log` progress as current MinerU business progress.

The remaining blocker is runtime ownership:

- the configured production MinerU logs `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log` remain empty;
- the currently healthy MinerU listener on port `8083` is an unmanaged conda process rather than the `luceon-mineru` tmux session;
- because it was not launched by `ops/start-mineru-api.sh`, its stdout/stderr are not attached to the configured log channel;
- `luceon-sidecar` was previously attached and should remain present, or be re-attached only if needed.

The user approved Option A at 2026-05-14T11:12:19+0800: controlled MinerU ownership normalization, with strict preflight, no upload, no data mutation, and no readiness claim.

## Objective

Normalize MinerU runtime ownership so the production MinerU process is launched as `luceon-mineru` through `ops/start-mineru-api.sh`, causing stdout/stderr to flow to the configured production log files.

This task is process-ownership recovery only. It does not prove live business progress by itself. A later separate one-upload validation may be needed after this task succeeds.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/development-engineer.md` if present; if not present, follow `AGENTS.md`, `TEAM_CONTRACT`, and this task brief
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. `TaskAndReport/2026-05-14T10-43-22+0800_P1-MinerU-Stale-Fallback-Hygiene-Production-Deployment-And-Read-Only-Runtime-Validation_REPORT.md`
12. `TaskAndReport/2026-05-14T11-09-27+0800_P1-MinerU-Stale-Fallback-Hygiene-Production-Deployment-And-Read-Only-Runtime-Validation_DIRECTOR_REVIEW.md`
13. `TaskAndReport/2026-05-14T11-09-27+0800_P1-MinerU-Ownership-Normalization-Authorization_DECISION.md`

## Workspaces

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`

## Allowed Scope

In the development workspace:

- read repository/task documents;
- update only this task row and your completion report;
- do not modify source code, PRD truth, role contracts, project state, or handoff unless this task explicitly requires it. It does not.

In the production workspace, you may run only the minimum commands needed to complete this scoped recovery:

- inspect repository and runtime state:
  - `git status --short --branch`
  - `git log -1 --oneline`
  - `docker compose ps`
- inspect health and queues with read-only HTTP calls:
  - upload health
  - dependency-health, including the existing MinerU submit probe if needed for consistency with prior validation
  - admission circuit
  - active task/AI state
  - direct MinerU `/health`
  - `/ops/mineru/log-channel-ownership`
  - `/ops/mineru/global-observation`
- inspect process ownership:
  - `lsof -nP -iTCP:8083 -sTCP:LISTEN`
  - `ps` / `pgrep`
  - `tmux ls`
  - `lsof -p <pid>` when needed to identify the current listener
- record the current MinerU listener PID, command, and ownership evidence.

If and only if the preflight below is clean and one unmanaged MinerU listener on port `8083` is uniquely identified, you may:

1. gracefully terminate only that verified unmanaged MinerU listener with `kill <pid>`;
2. wait briefly and confirm the old PID is gone and port `8083` is free or ready for the new owner;
3. start MinerU with exactly:

```bash
tmux new-session -d -s luceon-mineru "cd '/Users/concm/prod_workspace/Luceon2026' && bash ops/start-mineru-api.sh"
```

If `luceon-sidecar` is absent or stale after the MinerU ownership normalization, you may re-attach it with exactly:

```bash
tmux new-session -d -s luceon-sidecar "cd '/Users/concm/prod_workspace/Luceon2026' && UPLOAD_SERVER_URL=http://127.0.0.1:8081/__proxy/upload MINERU_LOG_SOURCE_CONTEXT=host-filesystem MINERU_ERR_LOG_PATH=/Users/concm/ops/logs/mineru-api.err.log MINERU_LOG_PATH=/Users/concm/ops/logs/mineru-api.log node ops/mineru-log-observer.mjs"
```

## Mandatory Stop Conditions

Stop and write a blocked report if any of these are true:

- active parse work or active AI work exists;
- admission circuit is open;
- dependency-health is blocking;
- Docker core services are unhealthy;
- direct MinerU health is unreachable or ambiguous before ownership replacement;
- the current port `8083` owner cannot be uniquely identified as exactly one unmanaged MinerU listener;
- port `8083` has multiple listeners or an ambiguous owner;
- `luceon-mineru` is already the current owner, but configured logs remain empty;
- `ops/start-mineru-api.sh` is missing, modified, untrusted, or cannot be inspected;
- the old unmanaged process does not exit after one graceful `TERM`;
- completing the task would require `kill -9`, Docker restart/down/down-v, DB/MinIO mutation, data cleanup, Ollama mutation, supervisor attach, model/config/secret/sample mutation, upload, repair/reparse/re-AI, or broad rollback.

Do not use `kill -9`. If graceful termination is not enough, stop and report blocked.

## Required Validation After Ownership Normalization

After starting `luceon-mineru`, verify and report:

- `tmux ls` includes `luceon-mineru`;
- `luceon-sidecar` is present or was re-attached only if needed;
- port `8083` has exactly one listener;
- the listener/process evidence shows MinerU is now owned by the intended `luceon-mineru` path/session;
- direct MinerU `/health` is healthy;
- upload health is healthy;
- dependency-health is non-blocking;
- admission circuit is closed;
- active task/AI state has no active work;
- `/ops/mineru/log-channel-ownership` reports the configured log paths and sidecar state;
- `/Users/concm/ops/logs/mineru-api.log` and `.err.log` exist and are readable;
- log freshness/size after launch is recorded;
- `/ops/mineru/global-observation` no longer promotes stale scratch fallback as current business progress.

It is acceptable if no real business-progress signal exists immediately after normalization, because this task does not upload a PDF. If logs remain empty after a successful launch, report that as residual evidence and do not claim the live progress issue is solved.

## Forbidden Scope

Do not:

- upload any PDF;
- run pressure, batch, soak, or long-run validation;
- run Docker down/down-v, Docker volume mutation, DB cleanup, MinIO cleanup, or destructive data commands;
- mutate DB/MinIO records;
- mutate Ollama, pull/delete/replace models, or change model configuration;
- attach or start `luceon-supervisor`;
- change secrets, local private credentials, samples, or production configuration;
- run repair/reparse/re-AI or mutate historical task/material state;
- delete, truncate, rename, or edit log files directly;
- commit machine-only artifacts or secrets;
- declare L3, production readiness, release readiness, go-live readiness, or production上线.

## Required Report

Write the expected report with:

- exact task brief path;
- branch/HEAD for development workspace and production HEAD;
- all commands run with exit codes;
- preflight evidence;
- old MinerU listener PID/command/ownership evidence;
- exact mutation performed, if any;
- post-recovery health/log-channel evidence;
- whether sidecar was untouched or re-attached, with exact reason;
- skipped checks and exact reasons;
- residual risks/debt;
- explicit statement that no upload, pressure, cleanup, DB/MinIO mutation, Ollama mutation, supervisor attach, repair/reparse/re-AI, readiness, or go-live claim was made.

Update `TaskAndReport/TASK_TRACKING_LIST.md` so this row becomes `已回报待 Director 审查` with `Next Actor=Director`, and include the report path.
