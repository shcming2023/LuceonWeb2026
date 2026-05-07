# Task: P0 Production Ops Sidecar Supervisor Recovery

```text
Task:
P0 Production Ops Sidecar Supervisor Recovery

Assignee:
Lucode

Issued by:
Lucia

Project:
Luceon2026

Date:
2026-05-07

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-07T10-13-05+0800_P0-Production-Ops-Sidecar-Supervisor-Recovery_TASK.md

Required reading before execution:
- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/lucode.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/codex/TEST_POLICY.md
- docs/prd/Luceon2026-PRD-v0.4.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-07T09-52-08+0800_P0-Production-Deployment-For-Manual-Review_REPORT.md

Background:
Production deployment for manual review is complete at:

- `http://localhost:8081/cms/`

Director manual review and Lucode investigation found that a user upload failed after MinerU completed parsing. The failure is not currently classified as a MinerU parsing failure.

Known incident facts from Lucode investigation:

- Task: `task-1778118934116`
- File: `G7_Workbook_ready_to_print.pdf`
- Current task state: `stage=ai`, `state=failed`
- MinerU status: `completed`
- Parsed artifacts exist: `full.md`, `artifact-manifest.json`, `mineru-result.zip`
- Parsed files count: `99`
- Failure point: AI metadata stage
- Upload-server log error:
  - `Provider ollama failed: Ollama Provider Error: [TimeoutError] The operation was aborted due to timeout`
  - Model: `qwen3.5:9b`
  - Duration: `299998ms`
  - Timeout: `300000ms`
- Current dependency-health later recovered:
  - MinIO ok=true
  - MinerU ok=true
  - MinerU submitProbe ok=true
  - Ollama ok=true
  - blocking=false
- Host MinerU raw logs are present:
  - `/Users/concm/ops/logs/mineru-api.log`
  - `/Users/concm/ops/logs/mineru-api.err.log`
- UI observation endpoint currently returns:
  - `/ops/mineru/global-observation => {"observation":null}`
- Missing processes observed:
  - `mineru-log-observer`
  - `luceon-sidecar`
  - `luceon-supervisor`
- Repair proxy currently returns:
  - `SUPERVISOR_UNAVAILABLE`
  - suggested command: `bash ops/start-luceon-runtime.sh`

Lucia interpretation:

- This incident does not prove MinerU parsing regression.
- The user-visible failed task is consistent with Ollama metadata recognition timeout under strict no-skeleton mode.
- Missing MinerU log visibility is likely caused by the host log observer sidecar not running.
- The repair proxy is unavailable because the dependency supervisor is not running.
- `bash ops/start-luceon-runtime.sh` is too broad for this repair because it restarts MinerU. This task must avoid restarting MinerU while production is available for manual review.

Objective:
Restore production ops observability and repair control by starting only the missing supervisor and MinerU log observer sidecar, then verify that UI diagnostics can access them.

Non-goals:
- Do not restart MinerU.
- Do not restart Ollama.
- Do not retry, repair, or mutate `task-1778118934116`.
- Do not implement new code.
- Do not change PRD truth, project ledger, handoff, role contracts, or release judgments.
- Do not claim production release readiness.
- Do not delete or clean Docker volumes, MinIO buckets, DB files, logs, or production data.

Allowed operations:
- Inspect production processes, tmux sessions, Docker status, and relevant logs.
- Start `luceon-supervisor` if absent.
- Start `luceon-sidecar` / `mineru-log-observer` if absent.
- Use the production deployment path as working directory when starting tmux sessions.
- Use `/__proxy/upload/ops/dependency-repair/status` to verify supervisor reachability after the supervisor is running.
- Use `/__proxy/upload/ops/mineru/global-observation` to verify sidecar observation push behavior.

Forbidden operations:
- Do not run `bash ops/start-luceon-runtime.sh` because it restarts MinerU.
- Do not run `restart-mineru`, `start-mineru`, `restart-ollama`, or broad repair actions.
- Do not run `docker compose down -v`.
- Do not remove volumes, DB files, MinIO buckets, logs, or production data.
- Do not use `git reset --hard` or `git clean` in production.
- Do not commit `.env`, production-only config, `.workbuddy`, or logs.

Required production commands or equivalent:

```bash
cd /Users/concm/prod_workspace/Luceon2026
git status --short --branch
git rev-parse HEAD
tmux ls || true
ps aux | rg 'mineru-log-observer|luceon-dependency-supervisor|start-mineru-api|ollama' || true
curl -sS http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true
curl -sS http://localhost:8081/__proxy/upload/ops/dependency-repair/status || true
curl -sS http://localhost:8081/__proxy/upload/ops/mineru/global-observation || true
```

Suggested narrow recovery sequence:

```bash
cd /Users/concm/prod_workspace/Luceon2026
tmux has-session -t luceon-supervisor || tmux new-session -d -s luceon-supervisor "cd '/Users/concm/prod_workspace/Luceon2026' && node ops/luceon-dependency-supervisor.mjs"
tmux has-session -t luceon-sidecar || tmux new-session -d -s luceon-sidecar "cd '/Users/concm/prod_workspace/Luceon2026' && UPLOAD_SERVER_URL=http://127.0.0.1:8081/__proxy/upload node ops/mineru-log-observer.mjs"
```

Required validation after recovery:

- `tmux ls` shows `luceon-supervisor`.
- `tmux ls` shows `luceon-sidecar`.
- `http://localhost:8081/__proxy/upload/ops/dependency-repair/status` no longer returns `SUPERVISOR_UNAVAILABLE`.
- dependency-repair status reports supervisor running and includes sidecar session status.
- `http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true` remains `blocking=false`.
- `http://localhost:8081/__proxy/upload/ops/mineru/global-observation` is checked after sidecar startup. If it remains `observation:null`, report exact response, tmux logs, and whether this is because there is no active MinerU task.
- `http://localhost:8081/cms/` remains reachable for Director manual review.

Optional evidence:

- `tmux capture-pane -pt luceon-supervisor -S -120`
- `tmux capture-pane -pt luceon-sidecar -S -120`
- Tail of `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log`, only if needed for diagnosis.

Completion report storage requirements:

- Write the completion report into TaskAndReport/ using this naming rule:
  `YYYY-MM-DDTHH-MM-SS+0800_P0-Production-Ops-Sidecar-Supervisor-Recovery_REPORT.md`
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, production URL, status, next actor, and evidence summary.
- Commit and push only task/report tracking changes to GitHub `main`.

Completion report must include:

- confirmation that work was based on this Lucia task brief
- production path and HEAD
- pre-recovery supervisor/sidecar/process status
- exact commands run and exit codes
- supervisor recovery result
- sidecar recovery result
- dependency-repair status response after recovery
- dependency-health response after recovery
- global-observation response after recovery
- manual-review URL status
- skipped checks and reasons
- whether `task-1778118934116` was left unchanged
- blockers, risks, or residual technical debt
- whether Lucia review is required

Acceptance criteria:

- `luceon-supervisor` is running or a precise blocker is reported.
- `luceon-sidecar` / `mineru-log-observer` is running or a precise blocker is reported.
- Repair proxy no longer returns `SUPERVISOR_UNAVAILABLE`.
- Production dependency-health remains non-blocking.
- Director manual-review URL remains reachable.
- Existing failed AI task is not silently altered.
- No production data, config, logs, Docker volumes, MinIO buckets, or DB files are destroyed.
```
