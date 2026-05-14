# Task Brief: P1 MinerU Sidecar Attach Only Recovery

- Task ID: `TASK-20260514-091558-P1-MinerU-Sidecar-Attach-Only-Recovery`
- Issued at: 2026-05-14T09:15:58+0800
- Issued by: Director
- Assigned role: DevelopmentEngineer
- Trigger: Task 112 remained unanswered for two Director heartbeat/check-task cycles; preflight remained clean; Director applied the standing conservative auto-progression rule.
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`
- Required report: `TaskAndReport/2026-05-14T09-15-58+0800_P1-MinerU-Sidecar-Attach-Only-Recovery_REPORT.md`

## Objective

Attach only the MinerU log observer sidecar (`luceon-sidecar`) in production, then verify that the deployed diagnostics can observe the sidecar or a fresh global observation.

This task is a scoped runtime recovery task. It is not a release, readiness, upload, pressure, or broad ownership-normalization task.

## Current Facts

Task 109 deployed `/ops/mineru/log-channel-ownership`.

Task 111 Architect review established:

- production services are healthy;
- MinerU API is healthy but unmanaged by the intended `luceon-mineru` tmux session;
- `luceon-sidecar` / `mineru-log-observer` is absent;
- `luceon-supervisor` is absent;
- `/ops/mineru/log-channel-ownership` reports `summaryState=empty`, configured log files readable but empty, sidecar `not-observed`;
- Ollama is healthy for Luceon but dual listener risk remains.

Director heartbeat preflight at `2026-05-14T09:14:50+0800` confirmed:

- active-task clean;
- admission circuit closed;
- dependency-health `ok=true`, `blocking=false`, MinerU submit probe OK;
- Docker services healthy;
- direct MinerU `/health` healthy;
- sidecar still not observed;
- Ollama dependency-health healthy despite the recorded dual-listener risk.

## Authorized Scope

DevelopmentEngineer may:

1. Run the read-only preflight listed below.
2. If and only if preflight passes, start a single tmux session named `luceon-sidecar` with exactly the command below.
3. Run the read-only post-checks listed below.
4. Write a completion report and update the tracking row to `已回报待 Director 审查`, `Next Actor=Director`.

## Required Preflight

Run and record outputs/exit codes:

```bash
git status --short --branch
git log -1 --oneline
docker compose ps
tmux ls || true
lsof -nP -iTCP:8081 -iTCP:8083 -iTCP:11434 -iTCP:19001 -sTCP:LISTEN || true
curl -fsS http://localhost:8081/__proxy/upload/health
curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership
curl -fsS http://127.0.0.1:8083/health
curl -fsS http://127.0.0.1:11434/api/version
curl -fsS http://127.0.0.1:11434/api/ps
```

Preflight must pass these gates before starting sidecar:

- no active/current/queued/drift/takeover MinerU task;
- admission circuit closed;
- dependency-health non-blocking with MinerU submit probe OK;
- Docker services healthy;
- direct MinerU health healthy;
- no existing `luceon-sidecar` tmux session;
- Ollama healthy for Luceon.

If any gate fails, do not start sidecar. Write a blocked report instead.

## Authorized Runtime Command

If preflight passes, run exactly:

```bash
tmux new-session -d -s luceon-sidecar "cd '/Users/concm/prod_workspace/Luceon2026' && UPLOAD_SERVER_URL=http://127.0.0.1:8081/__proxy/upload MINERU_LOG_SOURCE_CONTEXT=host-filesystem MINERU_ERR_LOG_PATH=/Users/concm/ops/logs/mineru-api.err.log MINERU_LOG_PATH=/Users/concm/ops/logs/mineru-api.log node ops/mineru-log-observer.mjs"
```

Do not modify this command unless it fails before sidecar starts. If it fails, stop and write a blocked report with the exact error and a recommended correction; do not improvise a different command.

## Required Post-Checks

Run and record outputs/exit codes:

```bash
tmux ls
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/global-observation
bash ops/runtime-ownership-status.sh
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit
curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
```

Success boundary:

- `luceon-sidecar` appears in tmux;
- `/ops/mineru/log-channel-ownership` moves away from `sidecar.runningState=not-observed`, or `/ops/mineru/global-observation` shows a fresh observer snapshot;
- if logs remain empty because no MinerU parse is running, report `sidecar attached but idle`; do not claim business-progress proof.

## Forbidden

- Do not start, stop, restart, kill, reload, or normalize MinerU API ownership.
- Do not start, stop, restart, kill, reload, or mutate Ollama.
- Do not attach `luceon-supervisor`.
- Do not run Docker Compose up/down/rebuild/restart, Docker prune, or volume operations.
- Do not upload PDFs.
- Do not run pressure, batch, soak, broad stress, or long-run validation.
- Do not repair, retry, reparse, re-AI, clean up, delete, or mutate historical tasks/materials/artifacts/logs/data.
- Do not change config, secrets, env, models, samples, PRD, role contracts, or release truth.
- Do not declare L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.

## Required Report

Write the report at the required path with:

- branch/HEAD and production HEAD;
- preflight outputs and exit codes;
- whether sidecar start was attempted;
- exact sidecar command result;
- post-check outputs and exit codes;
- observed endpoint state before/after;
- skipped checks and exact reasons;
- risks/blockers/residual debt;
- explicit statement that no forbidden operations occurred.

Then update `TaskAndReport/TASK_TRACKING_LIST.md` row 113 to `已回报待 Director 审查`, `Next Actor=Director`, and link the report.
