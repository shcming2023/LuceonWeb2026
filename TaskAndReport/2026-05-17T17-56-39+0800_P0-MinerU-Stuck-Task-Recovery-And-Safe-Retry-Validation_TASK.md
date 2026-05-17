# Task: P0 MinerU Stuck Task Recovery And Safe Retry Validation

## Context

User approved this task on 2026-05-17 after a manual single-PDF regression appeared stuck.

Current known stuck case:

- Luceon ParseTask: `task-1779010154264`
- Material: `696446087521346`
- File: `曹云童八年级咬文嚼字.pdf`
- File size: `321137` bytes
- MinerU task: `935081dc-b871-45ba-95ff-d836d5e9731d`
- Direct MinerU API last observed: `status=processing`, `completed_at=null`, `error=null`, `queued_ahead=0`
- Luceon DB last observed: `running / mineru-processing / 50`
- Last host stderr business progress: `Table-ocr rec ch: 0/2`
- Host stderr log stopped advancing after about `2026-05-17 17:29:25 +0800`
- Current submitted options included `backend=pipeline`, `enableOcr=false`, `enableFormula=true`, `enableTable=true`, `localTimeout=3600`

Comparison with milestone `v6.9` found no core MinerU submit-path parameter regression:

- `server/services/mineru/local-adapter.mjs` unchanged since `v6.9`
- `src/app/utils/mineruTaskOptions.ts` unchanged since `v6.9`
- `src/store/seedData.ts` MinerU defaults unchanged since `v6.9`
- Current evidence points to MinerU pipeline table OCR stalling on this PDF, not to the Task 214 Settings cleanup changing submit parameters.

Separate observation-chain issue discovered during diagnosis:

- Host `/Users/concm/ops/logs/mineru-api.err.log` contained newer business progress than the upload-server container could see through `/host/mineru-logs/mineru-api.err.log`.
- This task may record that fact, but it must not implement the code-level fix. The code-level fix is Task 217.

## Role

Next Actor: `Luceon`

Luceon may perform only the scoped production recovery and validation steps below.

## Workspaces And Runtime

- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- MinerU owner: host tmux session `luceon-mineru`
- MinerU start script: `ops/start-mineru-api.sh`
- Host logs: `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log`
- Production UI: `http://127.0.0.1:8081/cms/`

## Objective

Recover from the current stuck MinerU processing state without broad production mutation, then determine whether this same PDF can proceed with a safe no-table profile.

The purpose is operational recovery and evidence, not a release/readiness claim.

## Allowed Scope

1. Run read-only preflight:
   - `git status --short --branch`
   - direct MinerU `/health` and current `/tasks/{mineruTaskId}`
   - Luceon active-task and dependency-health read-only endpoints
   - Docker service health/status
   - host/container log stat comparison
   - `ps`, `lsof`, and `tmux list-sessions` for MinerU ownership
2. Confirm there is no unrelated active parse/AI work before changing MinerU runtime.
3. Record the stuck task facts before recovery.
4. Gracefully stop the current `luceon-mineru` MinerU process if it is still stuck:
   - prefer tmux interrupt/controlled process termination;
   - if a graceful stop does not work, terminate only the confirmed `mineru-api --host 0.0.0.0 --port 8083` PID owned by `luceon-mineru`.
5. Relaunch MinerU only through `bash ops/start-mineru-api.sh` inside tmux session `luceon-mineru`.
6. Verify direct MinerU health and log file ownership after restart.
7. Start or verify the existing host log observer sidecar if it can be done through existing repo script/command without code changes:
   - expected host-side command pattern:
     `UPLOAD_SERVER_URL=http://127.0.0.1:8081/__proxy/upload MINERU_LOG_SOURCE_CONTEXT=host-filesystem MINERU_ERR_LOG_PATH=/Users/concm/ops/logs/mineru-api.err.log MINERU_LOG_PATH=/Users/concm/ops/logs/mineru-api.log node ops/mineru-log-observer.mjs`
   - this is allowed only as runtime recovery/verification of existing code, not as code modification.
8. Observe what happens to `task-1779010154264` after MinerU restart.
9. If the original task becomes terminal failed, lost, or remains unrecoverably stuck, run at most one safe retry for the same PDF/material with:
   - `backend=pipeline`
   - `enableTable=false`
   - keep all other parse options as close to the original as possible unless the existing UI/API requires otherwise
   - one PDF only, no batch, no pressure, no second retry.

## Forbidden Scope

- Do not run pressure tests.
- Do not upload additional files beyond the one approved same-PDF safe retry.
- Do not clean MinIO, DB, Docker volumes, or sample libraries.
- Do not run `docker compose down -v`, volume cleanup, prune, or destructive repair.
- Do not modify code.
- Do not change model files, secrets, production env secrets, or external sample files.
- Do not declare production readiness, L3, pressure PASS, release readiness, or go-live.
- Do not silently mark skeleton/fallback output as real parsing or AI recognition.

## Stop Conditions

Stop and report blocked instead of continuing if:

- more than the current stuck task is actively parsing or AI-processing;
- the MinerU listener is not owned by `luceon-mineru` or ownership cannot be verified;
- restart would require broad service shutdown;
- retry requires unsupported manual DB surgery or unclear destructive mutation;
- any command would affect DB/MinIO/Docker volumes beyond the explicit one-task recovery boundary.

## Required Output

Write:

`TaskAndReport/2026-05-17T17-56-39+0800_P0-MinerU-Stuck-Task-Recovery-And-Safe-Retry-Validation_REPORT.md`

The report must include:

- before/after runtime facts;
- exact stuck task evidence;
- commands run and exit codes;
- whether MinerU was stopped/restarted and how;
- whether sidecar was started/verified;
- whether safe retry was used;
- final state of original task and retry task, if any;
- direct MinerU health after recovery;
- host/container log stat comparison after recovery;
- risks, blockers, and residual debt.

Update `TaskAndReport/TASK_TRACKING_LIST.md` when complete.

## Acceptance Criteria

- MinerU runtime is healthy after scoped recovery, or the report clearly explains the blocker.
- The original stuck task is no longer treated as silently healthy progress without evidence.
- If safe retry is used, it is exactly one same-PDF retry with `enableTable=false`.
- No broad production mutation occurs.
- Task 217 remains the code-level follow-up for the Docker bind-mount/log-observation architecture gap.
