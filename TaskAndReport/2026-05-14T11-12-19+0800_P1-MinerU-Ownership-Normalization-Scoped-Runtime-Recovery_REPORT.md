# DevelopmentEngineer Report: P1 MinerU Ownership Normalization Scoped Runtime Recovery

- Report time: 2026-05-14T11:29:39+0800
- Role: DevelopmentEngineer
- Based on Director task brief: `TaskAndReport/2026-05-14T11-12-19+0800_P1-MinerU-Ownership-Normalization-Scoped-Runtime-Recovery_TASK.md`
- Based on user/Director authorization: `TaskAndReport/2026-05-14T11-09-27+0800_P1-MinerU-Ownership-Normalization-Authorization_DECISION.md`

## Scope

Normalize production MinerU runtime ownership so the active listener on port `8083` is owned by the `luceon-mineru` tmux session and started through `ops/start-mineru-api.sh`, with stdout/stderr attached to:

- `/Users/concm/ops/logs/mineru-api.log`
- `/Users/concm/ops/logs/mineru-api.err.log`

No upload, pressure test, DB/MinIO mutation, Docker volume cleanup, model/config/secret/sample mutation, repair/reparse/re-AI, readiness claim, or go-live claim was performed.

## Branch / HEAD / Workspace State

Development workspace:

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- `git status --short --branch` showed a dirty shared worktree with many pre-existing modified/untracked files, including prior TaskAndReport entries and docs. This task intentionally touched only the report file and the Task 120 ledger row.

Production workspace:

- Path: `/Users/concm/prod_workspace/Luceon2026`
- Branch: `main...origin/main`
- HEAD: `b98735c Dispatch MinerU ownership normalization task`
- Known dirty production files before and after this task: `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, `src/app/pages/SourceMaterialsPage.tsx`, `src/store/appContext.tsx`.

## Files Changed

Repository files changed by this task:

- `TaskAndReport/2026-05-14T11-12-19+0800_P1-MinerU-Ownership-Normalization-Scoped-Runtime-Recovery_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Production runtime/process state changed by this task:

- Gracefully terminated the uniquely verified unmanaged MinerU listener on `8083`.
- Started `luceon-mineru` tmux session using `bash ops/start-mineru-api.sh`.

## Implementation Summary

1. Confirmed strict preflight was clean:
   - Docker services were healthy.
   - Upload server health was OK.
   - Dependency health was OK and nonblocking.
   - Admission circuit was closed.
   - No active parse or AI work was present, except historical AI failure records.
   - Direct MinerU health was healthy with no queued or processing work.
2. Verified the old MinerU listener was uniquely identifiable and unmanaged:
   - One listener on `8083`: PID `72358`, command `/Users/concm/miniconda3/envs/mineru/bin/python3.10 ... mineru-api --port 8083 --host 0.0.0.0`.
   - Parent conda runner PID `72339`.
   - No `luceon-mineru` tmux session existed.
   - PID `72358` had cwd `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`.
   - PID `72358` stdout/stderr were pipes, not `/Users/concm/ops/logs/mineru-api.log` or `.err.log`.
3. Verified `ops/start-mineru-api.sh` existed and was unchanged in production, and that it writes stdout/stderr to the configured ops log files.
4. Ran one graceful `kill 72358`, then confirmed PID `72358` exited and no listener remained on `8083`.
5. Started MinerU with:
   - `tmux new-session -d -s luceon-mineru "cd '/Users/concm/prod_workspace/Luceon2026' && bash ops/start-mineru-api.sh"`
6. Verified new ownership and logging:
   - `tmux ls` shows `luceon-mineru` and existing `luceon-sidecar`.
   - One listener on `8083`: PID `61436`.
   - PID `61436` cwd is `/Users/concm/prod_workspace/Luceon2026`.
   - PID `61436` stdout is `/Users/concm/ops/logs/mineru-api.log`.
   - PID `61436` stderr is `/Users/concm/ops/logs/mineru-api.err.log`.
   - Direct MinerU health remains healthy.
   - `/ops/mineru/log-channel-ownership` reports `summaryState=valid-business-progress`.
   - `/ops/mineru/global-observation` reports `activityLevel=active-progress` from the configured err log source.

## Commands Run And Exit Codes

Development workspace:

- `git status --short --branch` -> exit 0.
- `rg -n "TASK-20260514-111219|MinerU-Ownership-Normalization" TaskAndReport/TASK_TRACKING_LIST.md` -> exit 0.

Production workspace/read-only preflight:

- `git status --short --branch` -> exit 0.
- `git log -1 --oneline` -> exit 0.
- `docker compose ps` -> exit 0.
- `curl -fsS http://localhost:8081/__proxy/upload/health` -> exit 0.
- `curl -fsS http://localhost:8081/__proxy/upload/dependency-health` -> exit 0.
- `curl -fsS http://localhost:8081/__proxy/upload/mineru/admission-circuit` -> exit 0.
- `curl -fsS http://localhost:8081/__proxy/db/tasks/active-task` -> exit 0.
- `curl -fsS http://localhost:8083/health` -> exit 0.
- `lsof -nP -iTCP:8083 -sTCP:LISTEN` -> exit 0.
- `pgrep -fl "mineru-api|start-mineru-api|luceon-mineru"` -> exit 0.
- `tmux ls` -> exit 0.
- `sed -n '1,220p' ops/start-mineru-api.sh` -> exit 0.
- `git diff -- ops/start-mineru-api.sh` -> exit 0.
- `ps -p 72358 -o pid,ppid,command` -> exit 0.
- `ps -p 72339 -o pid,ppid,command` -> exit 0.
- `lsof -a -p 72358 -d cwd,1,2` -> exit 0.

Production runtime mutation:

- `kill 72358` -> exit 0.
- `ps -p 72358 -o pid,ppid,command || true` -> exit 0; no process remained.
- `lsof -nP -iTCP:8083 -sTCP:LISTEN || true` -> exit 0; no listener remained.
- `pgrep -fl "mineru-api|start-mineru-api|luceon-mineru" || true` -> exit 0; only `luceon-sidecar` remained before restart.
- `tmux new-session -d -s luceon-mineru "cd '/Users/concm/prod_workspace/Luceon2026' && bash ops/start-mineru-api.sh"` -> exit 0.

Production post-validation:

- `tmux ls` -> exit 0.
- `lsof -nP -iTCP:8083 -sTCP:LISTEN` -> exit 0.
- `pgrep -fl "mineru-api|start-mineru-api|luceon-mineru"` -> exit 0.
- `curl -fsS http://localhost:8083/health` -> exit 0.
- `stat -f "%N size=%z mtime=%Sm" -t "%Y-%m-%d %H:%M:%S %z" /Users/concm/ops/logs/mineru-api.log /Users/concm/ops/logs/mineru-api.err.log` -> exit 0.
- `lsof -a -p 61436 -d cwd,1,2` -> exit 0.
- `curl -fsS http://localhost:8081/__proxy/upload/health` -> exit 0.
- `curl -fsS http://localhost:8081/__proxy/upload/dependency-health` -> exit 0.
- `curl -fsS http://localhost:8081/__proxy/upload/mineru/admission-circuit` -> exit 0.
- `curl -fsS http://localhost:8081/__proxy/db/tasks/active-task` -> exit 0.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership` -> exit 0.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/global-observation` -> exit 0.
- `docker compose ps` -> exit 0.
- `git status --short --branch && git log -1 --oneline` in production workspace -> exit 0.

## Evidence

- Old unmanaged owner:
  - PID `72358` was the sole `8083` listener.
  - PID `72358` cwd was the development workspace.
  - PID `72358` stdout/stderr were pipes.
  - No `luceon-mineru` tmux session existed.
- New normalized owner:
  - `tmux ls` shows `luceon-mineru`.
  - PID `61436` is the sole `8083` listener.
  - PID `61436` cwd is `/Users/concm/prod_workspace/Luceon2026`.
  - PID `61436` fd1/fd2 point to `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log`.
- Runtime:
  - Direct MinerU health OK after restart.
  - Upload server health OK after restart.
  - Dependency health OK/nonblocking after restart.
  - Admission circuit closed after restart.
  - Active task clean except historical AI failures.
  - Log channel ownership selected configured ops log source and reported `summaryState=valid-business-progress`.
  - Global observation reported `activityLevel=active-progress`.

## Skipped Checks And Reasons

- No PDF upload, pressure test, batch test, soak test, repair/reparse/re-AI, or user-material parsing was run because Task 120 explicitly forbids them.
- No Git fetch, pull, push, commit, or branch operation was run in the development workspace because DevelopmentEngineer local check-task rules and this task scope do not authorize GitHub sync.
- No Docker down/down-v, DB/MinIO mutation, Docker volume cleanup, model/config/secret/sample mutation, or supervisor attach was run because Task 120 explicitly forbids them.
- No production readiness, L3, pressure PASS, or go-live claim is made.

## Risks / Blockers / Residual Debt

- This task validates process ownership and configured log-channel visibility only. It does not prove end-to-end parsing throughput for real user PDFs.
- `/ops/mineru/global-observation` active-progress evidence came from the controlled dependency-health submit probe, not from a user upload. It is valid evidence that configured logs are visible and live, but not a business-upload validation.
- Production workspace still has unrelated dirty files. They were not touched.
- Historical AI failure records remain visible in active-task diagnostics; they were not in active running/pending state during this task.

## Review / Follow-Up

- Director review required: Yes.
- Recommended next actor: Director.
- Recommended next action: Review this scoped runtime recovery evidence, then decide whether to dispatch a separate TestAcceptanceEngineer task for exactly-one controlled upload validation or other bounded runtime validation.
- Follow-up production validation or user decision needed: Yes, if the project needs renewed evidence for real upload -> MinerU -> MinIO -> AI metadata flow. This report does not authorize readiness or release claims.
