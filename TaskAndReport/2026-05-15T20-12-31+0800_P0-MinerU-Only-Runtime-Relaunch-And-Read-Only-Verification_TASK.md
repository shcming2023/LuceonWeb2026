# Task: P0 MinerU Only Runtime Relaunch And Read-Only Verification

- Task ID: `TASK-20260515-201231-P0-MinerU-Only-Runtime-Relaunch-And-Read-Only-Verification`
- Assignee: `DevelopmentEngineer`
- Issued by: `Director`
- Issued at: 2026-05-15T20:12:31+0800
- Priority: P0
- Project: Luceon2026
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- GitHub: `https://github.com/shcming2023/Luceon2026`
- Task brief: `TaskAndReport/2026-05-15T20-12-31+0800_P0-MinerU-Only-Runtime-Relaunch-And-Read-Only-Verification_TASK.md`
- Expected report: `TaskAndReport/2026-05-15T20-12-31+0800_P0-MinerU-Only-Runtime-Relaunch-And-Read-Only-Verification_REPORT.md`

## Required Reading

Before execution, read:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-15T19-29-28+0800_P0-MinerU-Runtime-Loss-And-Pressure-State-Read-Only-Diagnosis_REPORT.md`
- `TaskAndReport/2026-05-15T19-40-38+0800_P0-MinerU-Runtime-Loss-Read-Only-Diagnosis_DIRECTOR_REVIEW.md`
- `TaskAndReport/2026-05-15T19-40-38+0800_P0-MinerU-Runtime-Recovery-Authorization_DECISION.md`

## User Authorization

User approved Task 185 Option A at 2026-05-15T20:12:31+0800.

This authorizes only scoped MinerU runtime relaunch plus read-only verification.

It does not authorize submit-probe, upload, task retry/reparse/re-AI, task repair/reset/cancel, DB/MinIO/Docker cleanup, Docker down/down-v/prune, broad service restart, or readiness/go-live claims.

## Background

Task 181 pressure monitoring showed the 24-PDF run was blocked by MinerU runtime loss, not by AI/Ollama failure. Task 183 read-only diagnosis found:

- MinerU was not listening on `8083`;
- direct MinerU health failed with connection refused;
- `com.office.mineru` LaunchAgent existed but was `not running`;
- no visible tmux session existed;
- ownership naming is split between repo-documented `luceon-mineru` and host LaunchAgent/script `mineru_api`.

Director chose `luceon-mineru` as the canonical owner for this recovery, matching `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`.

## Objective

Restore the host MinerU API runtime with the smallest blast radius, then verify observability without mutating task data.

## Allowed Operations

Allowed preflight read-only checks:

- development and production `git status`, `git rev-parse`, `git log`;
- `lsof -nP -iTCP:8083 -sTCP:LISTEN`;
- `tmux list-sessions`;
- `launchctl print gui/$(id -u)/com.office.mineru`;
- read-only process inventory;
- read-only dependency-health with `mineruSubmitProbe=false`;
- direct MinerU `/health` attempt;
- read-only log tail/stat.

Allowed relaunch operation, only if preflight shows no existing listener on `8083` and no active MinerU tmux owner:

```bash
cd /Users/concm/prod_workspace/Luceon2026
tmux new-session -d -s luceon-mineru "cd '/Users/concm/prod_workspace/Luceon2026' && bash ops/start-mineru-api.sh"
```

Allowed post-relaunch read-only verification:

- `tmux list-sessions`;
- `lsof -nP -iTCP:8083 -sTCP:LISTEN`;
- `curl -sS --max-time 10 http://127.0.0.1:8083/health`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=false'`;
- `curl -sS --max-time 20 http://localhost:8081/__proxy/upload/ops/mineru/active-task`;
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit`;
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership`;
- read-only log tail/stat.

## Stop Conditions

Stop and write a blocked report without relaunching if:

- any process is already listening on `8083`;
- a `luceon-mineru` or `mineru_api` tmux session already exists;
- preflight suggests another active owner is running MinerU;
- production workspace or script path is missing in a way that makes the authorized command unsafe;
- the relaunch command returns non-zero or no session/listener appears after a reasonable wait.

## Forbidden Operations

Do not:

- run manual or extra MinerU submit-probe;
- upload files;
- retry, reparse, re-AI, repair, cancel, reset, or mutate tasks;
- clean DB/MinIO/Docker data;
- run `docker compose up`, `docker compose down`, `docker compose down -v`, Docker prune, or volume commands;
- restart/rebuild/redeploy upload-server, DB, MinIO, Ollama, supervisor, sidecar, or any Docker service;
- use `launchctl load/bootstrap/kickstart/bootout` or mutate LaunchAgent state;
- kill existing processes or tmux sessions unless a future task explicitly authorizes it;
- mutate config, secrets, models, sample files, production source files, or runtime data other than starting the single authorized `luceon-mineru` tmux session;
- declare pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

## Required Evidence

Your report must include:

- confirmation that work was based on this Director task brief and Task 185 Option A;
- branch/HEAD in development workspace;
- production HEAD and dirty-file summary;
- exact commands run with exit codes;
- preflight listener/session/process/LaunchAgent evidence;
- exact relaunch command run, if run;
- post-relaunch direct MinerU health evidence;
- dependency-health without submit-probe;
- active-task/admission/log-channel evidence;
- confirmation that no submit-probe, upload, retry/reparse/re-AI, task mutation, DB/MinIO/Docker cleanup, or broad restart occurred;
- residual risks and recommended next decision, especially whether a separate submit-probe and/or task-state reconciliation decision is needed.

## Completion Report

Write:

`TaskAndReport/2026-05-15T20-12-31+0800_P0-MinerU-Only-Runtime-Relaunch-And-Read-Only-Verification_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查`
- Next Actor: `Director`
- Next Action: Director reviews MinerU runtime relaunch evidence and decides whether to request submit-probe authorization or task-state reconciliation.
- Required Output: Director review.

Commit and push the report and ledger update to GitHub `main`.

## Acceptance Criteria

Director can accept this task only if:

- exactly one canonical MinerU owner is used or the task blocks before mutation;
- MinerU direct health and dependency-health without submit-probe are clearly evidenced;
- no forbidden task/data/runtime mutation occurred;
- the next decision boundary is explicit.
