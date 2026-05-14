# Architect Report: P1 MinerU Log Source Ownership Remediation Route

- Task ID: `TASK-20260514-100030-P1-MinerU-Log-Source-Ownership-Remediation-Route`
- Report time: 2026-05-14T10:15:00+0800
- Role: Architect
- Based on Director task brief: `TaskAndReport/2026-05-14T10-00-30+0800_P1-MinerU-Log-Source-Ownership-Remediation-Route_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Result: `CODE_FALLBACK_HYGIENE_FIRST_MINERU_OWNERSHIP_NORMALIZATION_REQUIRES_USER_APPROVAL`

## Executive Conclusion

Task 115 proves the runtime path works for one small/medium upload, but it also sharpens the observability diagnosis:

- `luceon-sidecar` is now alive and observed.
- The configured log channel is still empty.
- The current MinerU API process is not writing stdout/stderr to `/Users/concm/ops/logs/mineru-api.log` or `/Users/concm/ops/logs/mineru-api.err.log`.
- The sidecar still sees stale historical scratch fallback content under `uat/scratch/mineru-api.log`, which can pollute `global-observation` as stale diagnostics.

Therefore this is not primarily a missing-sidecar problem anymore. It is a split between:

1. code semantics issue: stale workspace scratch fallback should not outrank or pollute configured production log channels;
2. runtime ownership issue: true live business-progress recovery likely requires controlled MinerU ownership normalization so MinerU starts through `ops/start-mineru-api.sh` and writes to the configured log files.

Recommended next route:

1. Dispatch a DevelopmentEngineer code-only task for stale fallback exclusion/down-ranking and operator semantic hardening.
2. Separately record a User decision before any MinerU process ownership normalization, because that would require stopping or replacing the current healthy unmanaged MinerU process.

Do not run another upload until stale fallback hygiene is fixed or explicitly accepted as a diagnostic limitation.

## Current Process Ownership Map

Production workspace:

- `git status --short --branch`: `## main...origin/main`, with local modified files:
  - `.gitignore`
  - `docker-compose.override.yml`
  - `server/db-server.mjs`
  - `server/tests/worker-smoke.mjs`
  - `src/app/components/BatchUploadModal.tsx`
  - `src/app/pages/SourceMaterialsPage.tsx`
  - `src/store/appContext.tsx`
- `git log -1 --oneline`: `f4a9720 Review live MinerU progress validation`.
- Docker services `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` are healthy.
- `tmux ls`: `luceon-sidecar` is present.
- `lsof` listeners:
  - Docker on `*:8081`;
  - MinIO console on `127.0.0.1:19001`;
  - MinerU Python on `*:8083`;
  - Ollama on both `127.0.0.1:11434` and `*:11434`.
- `pgrep -fl`: `node ops/mineru-log-observer.mjs` is running; MinerU is running as conda `mineru-api --port 8083 --host 0.0.0.0`; no `luceon-supervisor` process was observed.
- `lsof -p 72358`: MinerU process cwd is the development workspace, not production; stdout/stderr file descriptors are pipes, not `/Users/concm/ops/logs/mineru-api*.log`.
- `lsof -p 88295`: sidecar cwd is production workspace and it is a tmux-owned node process.
- `ps eww` was used only for process ownership clues. Full output is intentionally not reproduced because process environments can contain sensitive values.

Interpretation:

- Sidecar ownership is now recovered.
- MinerU process ownership is still drifted: it is healthy but not started by the production `luceon-mineru` tmux wrapper and not writing to the configured log files.
- Supervisor remains absent; that is not the root cause for live progress.
- Ollama dual listener remains an ownership risk but is not blocking this specific MinerU log-source route while dependency-health is OK.

## Current Log-Source Map

Configured upload-server log paths:

- `MINERU_LOG_PATH=/host/mineru-logs/mineru-api.log`
- `MINERU_ERR_LOG_PATH=/host/mineru-logs/mineru-api.err.log`

Configured sidecar host log paths:

- `MINERU_LOG_PATH=/Users/concm/ops/logs/mineru-api.log`
- `MINERU_ERR_LOG_PATH=/Users/concm/ops/logs/mineru-api.err.log`
- `MINERU_LOG_SOURCE_CONTEXT=host-filesystem`

Host file state:

- `/Users/concm/ops/logs/mineru-api.log`: exists, readable, `0` bytes, mtime `2026-05-12 07:59`.
- `/Users/concm/ops/logs/mineru-api.err.log`: exists, readable, `0` bytes, mtime `2026-05-12 07:59`.
- `/Users/concm/prod_workspace/Luceon2026/uat/scratch/mineru-api.log`: exists, `115` bytes, mtime `2026-05-08 08:09`, contains stale test-like `Predict 99%` content.
- `/Users/concm/prod_workspace/Luceon2026/uat/scratch/mineru-api.err.log`: exists, `0` bytes.

Container view:

- `/host/mineru-logs/mineru-api.log`: exists, readable, `0` bytes.
- `/host/mineru-logs/mineru-api.err.log`: exists, readable, `0` bytes.

Endpoint state:

- `/ops/mineru/log-channel-ownership`: `summaryState=empty`; configured logs empty/readable; sidecar `observed-recent`.
- `/ops/mineru/global-observation`: stale fallback observation from `uat/scratch/mineru-api.log`, with `activityLevel=log-observation-stale`, raw `Predict 99%`, and no current attribution.

Why stale fallback is still selected globally:

- `server/lib/ops-mineru-log-parser.mjs` includes both configured log paths and workspace scratch fallback paths in `getMineruLogPaths()`.
- `parseLatestMineruProgress()` currently ranks candidates with business signals ahead of no-signal empty configured logs, then marks the chosen source stale later.
- In the sidecar process, `process.cwd()` is production workspace, so `uat/scratch/mineru-api.log` exists and is parsed.
- In the upload-server container, the scratch fallback path is different and missing, so the ownership endpoint reports configured logs as empty. This explains the mismatch: endpoint says `empty`, global sidecar observation reports stale fallback.

The configured log paths are not mismatched between host and container; the host files and container mount both point to the same empty configured log files. The mismatch is between the configured production log channel and the stale workspace scratch fallback.

## Why Sidecar Attach Did Not Restore Live Progress

Sidecar attach restored transport, not signal production.

The sidecar can read host files and post observations. It cannot make MinerU write to the configured logs. Current MinerU process evidence shows:

- MinerU was not launched from the production tmux wrapper.
- MinerU cwd is the development workspace.
- MinerU stdout/stderr are pipes, not configured log files.
- `/Users/concm/ops/logs/mineru-api*.log` stayed empty through Task 115.

Therefore the sidecar is attached to the right intended path, but the active MinerU writer is not feeding that path.

## Remediation Options

### Option 1: Code-Only Stale Fallback Exclusion / Down-Ranking

Recommended first.

Scope:

- Change `server/lib/ops-mineru-log-parser.mjs` and focused tests only.
- When explicit `MINERU_LOG_PATH` / `MINERU_ERR_LOG_PATH` are configured, workspace scratch fallback should be disabled or treated strictly as low-priority diagnostic-only.
- Stale fallback should not be selected as `latest-valid-business-signal`.
- Stale fallback should not populate operator-facing phase/page/batch semantics as if current.
- If configured logs are empty and fallback is stale, global observation should state configured log channel empty plus stale fallback ignored/diagnostic, not "Predict 99%" as useful progress.

Risk:

- Low runtime risk; code/test only.
- Does not recover true live business progress.

Acceptance evidence:

- Smoke test where configured logs are empty and scratch fallback has old `Predict 99%` must return configured-channel-empty or stale-fallback-ignored semantics.
- Smoke test where configured log contains current business progress must still return active progress.
- No fabricated progress.

### Option 2: UI / Operator Semantic Hardening

Useful but secondary.

The UI already says `MinerU 已完成，但本次未捕获可归因业务进度日志` at terminal state. Additional hardening can ensure stale fallback phase details are not visually promoted during or after terminal tasks.

Risk:

- Low.
- Cannot solve live observability; only reduces confusion.

Recommendation:

- Fold into Option 1 if the stale fallback semantics surface through `progressSemantics`.

### Option 3: Sidecar / Log-Path Retargeting Without MinerU Restart

Not recommended as primary.

Retargeting sidecar to `uat/scratch/mineru-api.log` would be wrong because that file is stale and not the active MinerU writer. Retargeting to MinerU stdout/stderr pipes is not a stable production contract and would be brittle on macOS.

Conclusion:

- No trustworthy retarget path was found without changing the MinerU process owner.

### Option 4: Controlled MinerU Process Ownership Normalization

Likely required for true live business-progress recovery.

Desired end state:

- `luceon-mineru` tmux session owns MinerU.
- MinerU is started through `ops/start-mineru-api.sh`.
- stdout appends to `/Users/concm/ops/logs/mineru-api.log`.
- stderr appends to `/Users/concm/ops/logs/mineru-api.err.log`.
- `luceon-sidecar` reads those files and reports fresh observations.

Risk:

- Requires runtime mutation: current MinerU process is healthy and owns port `8083`, so a safe transition probably requires stopping or replacing it.
- This needs explicit User approval and a precise Director task brief.
- Production worktree is dirty; any restart/rebuild/deploy task must not overwrite unrelated local changes.

Preconditions:

- no active/current/queued/drift/takeover task;
- admission circuit closed and counts zero;
- dependency-health non-blocking;
- Docker services healthy;
- current MinerU health captured;
- current PID/command captured;
- dirty production worktree recorded and left untouched;
- explicit stop/relaunch authority granted by User.

### Option 5: Supervisor Integration

Later step only.

Supervisor can help expose ownership status or action endpoints, but it should not be the first fix. Starting supervisor will not make MinerU write to the configured logs. If used later, it should be an ops-helper task with action endpoints disabled or explicitly forbidden during validation.

## Recommended Next Task

Recommended immediate task:

- Assignee: `DevelopmentEngineer`
- Task type: code/test only
- Name: `P1 MinerU Stale Fallback Hygiene And Progress Semantics Hardening`

Scope:

- Modify only:
  - `server/lib/ops-mineru-log-parser.mjs`
  - focused MinerU log-channel/log-observation smoke tests
  - UI semantic helper only if required by tests, likely `src/app/utils/taskView.ts`
- Implement stale fallback exclusion/down-ranking for production-style configured log paths.
- Preserve active progress parsing when the configured log channel contains current business signals.
- Preserve diagnostic-only semantics when no current attributable progress exists.

User approval required:

- Not required for code-only dev/test task if Director keeps it out of production mutation.
- Required later for any MinerU restart/kill/relaunch/ownership normalization.

Preflight / checks:

- `git status --short --branch`
- inspect existing dirty workspace and avoid unrelated changes
- run focused log-channel tests
- run `node server/tests/mineru-log-progress-smoke.mjs` if scope touches parser ranking
- run `node server/tests/mineru-log-observation-transport-smoke.mjs`
- run `node server/tests/mineru-log-channel-ownership-smoke.mjs`
- `git diff --check`

Forbidden operations:

- no upload;
- no production mutation;
- no Docker command;
- no MinerU/Ollama/sidecar/supervisor start/stop/restart/kill;
- no log deletion/truncation;
- no sample/config/secret/model mutation;
- no readiness or go-live claim.

Expected evidence:

- stale `uat/scratch/mineru-api.log` cannot outrank empty configured production logs as a current business-progress source;
- stale fallback, if reported, is clearly diagnostic-only and non-attributable;
- current configured business-progress logs still produce page/batch/phase progress;
- `fast-complete-no-business-signal` remains truthful and does not fabricate progress.

## Subsequent User Decision

After code fallback hygiene is accepted, Director should ask the User whether to authorize controlled MinerU ownership normalization.

That future task should not be hidden inside a validation task. It should explicitly authorize, or explicitly forbid:

- stopping current unmanaged MinerU process;
- launching `luceon-mineru` via `ops/start-mineru-api.sh`;
- preserving or rechecking `/Users/concm/ops/logs/mineru-api*.log`;
- keeping sidecar attached;
- running one later controlled observability validation upload.

Until that decision is made, another upload may again pass the main runtime path but still fail to prove live business progress.

## Commands Run And Exit Codes

Development workspace:

- `git status --short --branch` -> 0
- `rg -n "... Architect ..."` on `TaskAndReport/TASK_TRACKING_LIST.md` -> 0
- `sed` reads of Task 116 brief, Task 111/113/115 reports and Director reviews -> 0
- `rg -n "inspectMineruLogChannelOwnership|workspace-scratch-fallback|log-channel|fallback|MINERU_LOG_PATH|MINERU_ERR_LOG_PATH" ...` -> 0
- `sed` reads of `server/lib/ops-mineru-log-parser.mjs` -> 0

Production workspace:

- `git status --short --branch` -> 0
- `git log -1 --oneline` -> 0
- `docker compose ps` -> 0
- `tmux ls` -> 0
- `lsof -nP -iTCP:8081 -iTCP:8083 -iTCP:11434 -iTCP:19001 -sTCP:LISTEN` -> 0
- `pgrep -fl "mineru|mineru-log-observer|luceon-dependency-supervisor|ollama"` -> 0
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership` -> 0
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/global-observation` -> 0
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task` -> 0
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit` -> 0
- `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` -> 0
- `ls -l /Users/concm/ops/logs /Users/concm/prod_workspace/Luceon2026/uat/scratch` -> 0
- `ps eww -p 72339` -> 0, used only for process ownership clues; full environment not recorded because it can contain secrets
- `ps eww -p 72358` -> 0, used only for process ownership clues; full environment not recorded because it can contain secrets
- `ps eww -p 88295` -> 0, used only for sidecar command/env ownership clues; full environment not recorded because it can contain secrets
- `docker compose exec -T upload-server ls -l /host/mineru-logs` -> 0
- `docker compose exec -T upload-server printenv MINERU_LOG_PATH` -> 0
- `docker compose exec -T upload-server printenv MINERU_ERR_LOG_PATH` -> 0
- `lsof -p 72358` -> 0
- `lsof -p 88295` -> 0
- `tail -n 20 /Users/concm/prod_workspace/Luceon2026/uat/scratch/mineru-api.log` -> 0
- `tail -n 20 /Users/concm/ops/logs/mineru-api.log` -> 0
- `tail -n 20 /Users/concm/ops/logs/mineru-api.err.log` -> 0

## Skipped Checks

- No upload was performed.
- No pressure, batch, soak, or long-run validation was performed.
- No restart, stop, kill, relaunch, or ownership normalization was performed.
- No sidecar/supervisor/Docker/DB/MinIO/upload-server/frontend/Ollama operation was performed.
- No source code, PRD, role contract, config, secret, model, sample, production file, task/material/artifact, DB row, MinIO object, or log file was modified.
- No GitHub fetch, pull, push, or sync was performed.
- No L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线 claim is made.

## Next Actor

Director.

Director should review this report and issue the code-only stale fallback hygiene task to DevelopmentEngineer. Director should separately record a User decision before any controlled MinerU ownership normalization.
