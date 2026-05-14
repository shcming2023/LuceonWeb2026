# TASK-20260514-104322-P1-MinerU-Stale-Fallback-Hygiene-Production-Deployment-And-Read-Only-Runtime-Validation

Task:
P1 MinerU Stale Fallback Hygiene Production Deployment And Read-Only Runtime Validation

Assignee:
DevelopmentEngineer

Issued by:
Director

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-14T10-43-22+0800_P1-MinerU-Stale-Fallback-Hygiene-Production-Deployment-And-Read-Only-Runtime-Validation_TASK.md`

Expected completion report:
`TaskAndReport/2026-05-14T10-43-22+0800_P1-MinerU-Stale-Fallback-Hygiene-Production-Deployment-And-Read-Only-Runtime-Validation_REPORT.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md` if present in the local workspace; if absent, do not block solely on that missing file, and follow `AGENTS.md`, `TEAM_CONTRACT`, and this task brief.
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- This task brief
- Task 117 report and Director review:
  - `TaskAndReport/2026-05-14T10-13-43+0800_P1-MinerU-Stale-Fallback-Hygiene-And-Progress-Semantics-Hardening_REPORT.md`
  - `TaskAndReport/2026-05-14T10-43-22+0800_P1-MinerU-Stale-Fallback-Hygiene-And-Progress-Semantics-Hardening_DIRECTOR_REVIEW.md`

## Background

Task 117 was accepted at code/test level. It prevents stale workspace scratch fallback logs from being promoted as current MinerU business progress when explicit production log paths are configured.

Production still runs old code until deployment. The parser is used by upload-server runtime surfaces and by the host `luceon-sidecar` process, so this validation needs both:

- update/rebuild `cms-upload-server`;
- restart/re-attach only `luceon-sidecar` so it imports the updated parser.

Do not touch the MinerU API process itself.

## Objective

Deploy the accepted Task 117 code to production with the smallest non-destructive runtime change, then verify read-only surfaces show stale fallback hygiene behavior.

This task must not upload any PDF. It is runtime-surface validation only.

## Allowed Operations

In development workspace:

- run `git status --short --branch`;
- read required files;
- write this task report;
- update only Task 118 row in `TaskAndReport/TASK_TRACKING_LIST.md`.

In production workspace, only after preflight passes:

- `git status --short --branch`;
- `git log -1 --oneline`;
- `git fetch origin`;
- `git pull --ff-only origin main`;
- inspect dirty files with `git status --short` and `git diff --name-only`;
- inspect active work/admission/dependency health with read-only curls;
- inspect Docker services with `docker compose ps`;
- rebuild/recreate only upload-server with:
  - `docker compose up -d --build upload-server`
- restart/re-attach only `luceon-sidecar` with the existing exact command pattern:

```bash
tmux kill-session -t luceon-sidecar
tmux new-session -d -s luceon-sidecar "cd '/Users/concm/prod_workspace/Luceon2026' && UPLOAD_SERVER_URL=http://127.0.0.1:8081/__proxy/upload MINERU_LOG_SOURCE_CONTEXT=host-filesystem MINERU_ERR_LOG_PATH=/Users/concm/ops/logs/mineru-api.err.log MINERU_LOG_PATH=/Users/concm/ops/logs/mineru-api.log node ops/mineru-log-observer.mjs"
```

- run read-only validation:
  - upload health;
  - dependency-health with MinerU submit probe and Ollama chat probe if available;
  - `/ops/mineru/admission-circuit`;
  - `/ops/mineru/active-task`;
  - `/ops/mineru/log-channel-ownership`;
  - `/ops/mineru/global-observation`;
  - direct MinerU `/health` if reachable;
  - `tmux ls`;
  - Docker service state.

## Preflight Stop Conditions

Stop before `git pull`, rebuild, or sidecar restart and write a blocked report if:

- active parse or AI work exists;
- admission circuit is open;
- dependency-health is blocking;
- core Docker services are unhealthy;
- production HEAD/status cannot be identified;
- `git pull --ff-only origin main` would overwrite or conflict with local changes;
- dirty production files include any of the Task 117 deployment-critical paths:
  - `server/lib/ops-mineru-log-parser.mjs`
  - `server/lib/ops-mineru-diagnostics.mjs`
  - `ops/mineru-log-observer.mjs`
  - `server/upload-server.mjs`
  - `server/services/mineru/`
  - `server/services/queue/`
  - `docker-compose.yml`
  - upload-server Dockerfile/build scripts/package files
- you cannot confidently show that existing dirty production files are unrelated to this scoped upload-server/sidecar validation;
- the operation would require MinerU restart/kill/ownership normalization, Ollama mutation, supervisor attach, DB/MinIO/Docker volume/data cleanup, config/secret/model/sample mutation, or historical task/material mutation.

Known dirty production files such as `docker-compose.override.yml` must be recorded, but must not be overwritten or normalized.

## Expected Runtime Evidence

After deployment and sidecar restart, record:

- production HEAD before and after;
- exact Docker/tmux commands run and exit codes;
- upload-server health;
- dependency-health result;
- active-task and admission-circuit result;
- `log-channel-ownership` result;
- `global-observation` result.

Expected result:

- stale `uat/scratch/mineru-api.log` should no longer be promoted as useful current `Predict 99%` progress when explicit configured production logs are present;
- configured empty logs should remain empty/diagnostic;
- sidecar should be `observed-recent`;
- no upload or live business-progress proof is expected from this read-only validation.

## Forbidden Operations

- Do not upload PDFs.
- Do not run pressure, batch, soak, or long-run validation.
- Do not restart, stop, kill, relaunch, or normalize MinerU.
- Do not mutate Ollama.
- Do not attach/restart supervisor.
- Do not run `docker compose down`, `docker compose down -v`, volume deletion, DB reset, MinIO cleanup, model pull/delete/replace, broad restart, rollback, or data cleanup.
- Do not repair, reparse, re-AI, retry, mutate, delete, or clean historical tasks/materials/artifacts.
- Do not delete, truncate, rename, or edit log files.
- Do not modify samples, secrets, configs, model files, PRD truth, role contracts, release docs, or GitHub settings.
- Do not overwrite or normalize unrelated dirty worktree changes.
- Do not claim L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.

## Completion Report Requirements

Write the report to:

`TaskAndReport/2026-05-14T10-43-22+0800_P1-MinerU-Stale-Fallback-Hygiene-Production-Deployment-And-Read-Only-Runtime-Validation_REPORT.md`

Then update only Task 118 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- `Status=已回报待 Director 审查` if completed;
- `Status=挂起` if blocked before deployment;
- `Next Actor=Director`;
- include production HEAD, whether deployment occurred, whether sidecar restart occurred, validation endpoint summary, and residual risk.

Do not update project state docs, PRD, role contracts, release docs, or GitHub.

## Acceptance Criteria

Director can accept this task if:

- preflight evidence is complete;
- deployment occurs only if safe under the dirty-worktree stop conditions;
- only upload-server and `luceon-sidecar` are touched;
- no upload or forbidden operation is performed;
- runtime endpoints show the accepted stale fallback hygiene behavior, or a precise blocked report explains why validation could not safely proceed;
- no readiness or上线 claim is made.
