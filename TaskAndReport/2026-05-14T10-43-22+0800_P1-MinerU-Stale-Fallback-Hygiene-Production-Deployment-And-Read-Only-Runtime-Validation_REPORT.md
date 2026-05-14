# DevelopmentEngineer Report: P1 MinerU Stale Fallback Hygiene Production Deployment And Read-Only Runtime Validation

- Task ID: `TASK-20260514-104322-P1-MinerU-Stale-Fallback-Hygiene-Production-Deployment-And-Read-Only-Runtime-Validation`
- Report time: 2026-05-14T10:59:00+0800
- Role: DevelopmentEngineer
- Based on Director task brief: `TaskAndReport/2026-05-14T10-43-22+0800_P1-MinerU-Stale-Fallback-Hygiene-Production-Deployment-And-Read-Only-Runtime-Validation_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Result: `COMPLETED_SCOPED_PRODUCTION_DEPLOYMENT_AND_READ_ONLY_VALIDATION`

## Scope Boundary

This task deployed the accepted Task 117 code path to production with the minimum authorized runtime change.

Performed:

- production `git fetch origin`;
- production `git pull --ff-only origin main`;
- `docker compose up -d --build upload-server`;
- restart/re-attach only `luceon-sidecar` with the task-brief command pattern;
- read-only runtime validation endpoints.

Not performed:

- no PDF upload;
- no pressure, batch, soak, or long-run validation;
- no MinerU restart/kill/relaunch/ownership normalization;
- no Ollama mutation;
- no supervisor attach/restart;
- no Docker down/down -v, volume cleanup, DB reset, MinIO cleanup, model operation, broad restart, rollback, data cleanup, repair, reparse, re-AI, retry, or historical task/material/artifact mutation;
- no log deletion/truncation/rename/edit;
- no sample/config/secret/model/PRD/role/release truth mutation;
- no readiness, L3, pressure PASS, release-readiness, go-live, or production上线 claim.

## Branch / HEAD / Workspace State

Development workspace:

- `git status --short --branch` exit 0.
- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`.
- `git log -1 --oneline` exit 0: `005ca96 Hold Task 108 auto progress on GitHub sync`.
- Shared dirty worktree remains present; only this report and Task 118 row were intentionally changed in the development workspace for this task.

Production workspace:

- Initial `git status --short --branch` exit 0: `## main...origin/main`.
- Initial `git log -1 --oneline` exit 0: `416a963 Accept MinerU fallback hygiene`.
- After `git fetch origin`, production `HEAD` and `origin/main` both resolved to `416a963`.
- `git pull --ff-only origin main` exit 0: `Already up to date.`
- Final production `git log -1 --oneline` exit 0: `416a963 Accept MinerU fallback hygiene`.
- Known dirty production files remained:
  - `.gitignore`
  - `docker-compose.override.yml`
  - `server/db-server.mjs`
  - `server/tests/worker-smoke.mjs`
  - `src/app/components/BatchUploadModal.tsx`
  - `src/app/pages/SourceMaterialsPage.tsx`
  - `src/store/appContext.tsx`

Dirty-file stop-condition assessment:

- None of the dirty files are the Task 117 deployment-critical paths listed in the task brief: `server/lib/ops-mineru-log-parser.mjs`, `server/lib/ops-mineru-diagnostics.mjs`, `ops/mineru-log-observer.mjs`, `server/upload-server.mjs`, `server/services/mineru/`, `server/services/queue/`, `docker-compose.yml`, or upload-server Dockerfile/build/package files.
- `git diff --name-only HEAD..origin/main` was empty after fetch, so ff-only pull had no incoming file changes to overwrite dirty files.
- Deployment proceeded under the task brief stop-condition boundary.

## Preflight Evidence

Preflight passed before deployment:

- `docker compose ps` exit 0: `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` healthy.
- `/ops/mineru/active-task` exit 0: no active/current/queued/drift/takeover tasks; only unchanged historical AI failure tasks.
- `/ops/mineru/admission-circuit` exit 0: `open=false`, circuit `closed`, active task clean.
- `/ops/dependency-health?mineruSubmitProbe=true&ollamaChatProbe=true` exit 0: `ok=true`, `blocking=false`; MinerU submit probe `202`; Ollama `qwen3.5:9b` resident and `chatOk=true`.
- `tmux ls || true` exit 0: `luceon-sidecar` present before restart.
- Task 117 code marker was present in production parser before deployment validation: `workspace-scratch-fallback-ignored-when-configured-logs-explicit`.

## Commands Run And Exit Codes

Development workspace:

| Command | Exit Code | Notes |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Required check-task command; shared dirty worktree observed. |
| `rg -n "DevelopmentEngineer\|开发工程师\|下达待执行\|执行中\|退回待修正\|修正中" TaskAndReport/TASK_TRACKING_LIST.md` | 0 | Found Task 118 assigned to DevelopmentEngineer. |
| `sed -n ... Task 118 task brief / Task 117 review / role contract` | 0 | Required task context read. |
| `git log -1 --oneline` | 0 | Development HEAD recorded. |

Production workspace:

| Command | Exit Code | Notes |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Production branch and dirty files recorded. |
| `git log -1 --oneline` | 0 | Production HEAD before/after: `416a963`. |
| `git diff --name-only` | 0 | Dirty file names recorded. |
| `docker compose ps` | 0 | Preflight and final service state healthy. |
| `curl -fsS .../ops/mineru/active-task` | 0 | No active/current/queued/drift/takeover work. |
| `curl -fsS .../ops/mineru/admission-circuit` | 0 | Circuit closed/open=false. |
| `curl -fsS .../ops/dependency-health?mineruSubmitProbe=true&ollamaChatProbe=true` | 0 | Preflight and final checks non-blocking. |
| `git fetch origin` | 0 | Remote refs refreshed. |
| `git diff --name-only HEAD..origin/main` | 0 | Empty; no incoming diff. |
| `git rev-parse --short HEAD && git rev-parse --short origin/main` | 0 | Both `416a963`. |
| `git pull --ff-only origin main` | 0 | Already up to date. |
| `rg -n "workspace-scratch-fallback-ignored-when-configured-logs-explicit\|hasExplicitConfiguredLogPaths" server/lib/ops-mineru-log-parser.mjs` | 0 | Task 117 code markers present. |
| `docker compose up -d --build upload-server` | 0 | Rebuilt/recreated only `cms-upload-server`; warning only for existing orphan `cms-minio-init`. |
| `tmux kill-session -t luceon-sidecar && tmux new-session -d -s luceon-sidecar "...node ops/mineru-log-observer.mjs"` | 0 | Restarted/re-attached only `luceon-sidecar`. |
| `curl -fsS .../health` | 0 | Upload-server health OK. |
| `curl -fsS .../ops/mineru/log-channel-ownership` | 0 | `summaryState=empty`; sidecar `observed-recent`. |
| `curl -fsS .../ops/mineru/global-observation` | 0 | Stale fallback suppressed as diagnostic; see evidence below. |
| `curl -fsS http://127.0.0.1:8083/health` | 0 | MinerU healthy; queued `0`, processing `0`. |
| `tmux ls || true` | 0 | `luceon-sidecar` present after restart. |

## Runtime Evidence

Upload-server:

- `/__proxy/upload/health`: `{"ok":true,"service":"upload-server"}`.
- Final `docker compose ps`: `cms-upload-server` healthy, created after scoped rebuild; other core services healthy.

Dependency and intake:

- Final dependency health: `ok=true`, `blocking=false`.
- MinerU submit probe: `status=202`, `ok=true`.
- Ollama: `model=qwen3.5:9b`, `modelResident=true`, `chatOk=true`.
- Admission circuit: `open=false`, state `closed`.
- Active task: no active/current/queued/drift/takeover work; only unchanged historical AI failures.
- Direct MinerU health: `healthy`, `queued_tasks=0`, `processing_tasks=0`.

Log-channel ownership:

- `/ops/mineru/log-channel-ownership`:
  - `summaryState=empty`;
  - selected source `MINERU_ERR_LOG_PATH:mineru-api.err.log`;
  - configured stderr/stdout logs exist, are readable, and are empty;
  - `sidecar.runningState=observed-recent`;
  - workspace scratch fallback sources are missing from the upload-server container view.

Global observation:

- `/ops/mineru/global-observation` returned:
  - `activityLevel=log-observation-empty`;
  - `observationStale=true`;
  - `observationStaleReason=configured log file exists but is empty; workspace scratch fallback ignored as non-authoritative diagnostic`;
  - selected log source `configuredBy=MINERU_ERR_LOG_PATH`, `logSourceSelectedReason=file-empty`;
  - `progressSemantics.phase=null`, no batch/pages/stage progress fabricated;
  - `progressSemantics.message=MinerU 已提交/正在处理，但暂无可归因业务日志`;
  - `ignoredDiagnosticLogSource.configuredBy=workspace-scratch-fallback`;
  - `ignoredDiagnosticLogSource.logSourceSelectedReason=workspace-scratch-fallback-ignored-when-configured-logs-explicit`;
  - ignored fallback path `/Users/concm/prod_workspace/Luceon2026/uat/scratch/mineru-api.log` still had `hasBusinessSignal=true` and `activityLevel=active-progress`, proving the old scratch `Predict 99%` content was seen but not promoted as current progress.

This matches the expected Task 118 behavior: stale fallback is visible only as diagnostic metadata, not useful current MinerU progress.

## Skipped Checks And Reasons

- No PDF upload: explicitly forbidden.
- No pressure/batch/soak/long-run validation: explicitly forbidden.
- No frontend browser check: task requested read-only runtime endpoint validation, not UI/UAT.
- No TypeScript/build in development workspace: Task 118 was production deployment/read-only runtime validation of already accepted code, and the task did not require developer rebuild checks.
- No production MinerU/Ollama/supervisor ownership normalization: explicitly forbidden.

## Risks / Residual Debt

- Live business-progress observability remains absent because configured MinerU stdout/stderr logs are still empty.
- The current MinerU process remains unmanaged for this observability path; true live progress likely still requires a separate controlled MinerU ownership normalization decision.
- Production worktree remains dirty with unrelated files. They were not overwritten or normalized, but future deployment tasks should continue treating them as a stop-condition review item.
- This task validates runtime surfaces after deploying fallback hygiene; it does not validate a new upload, pressure behavior, L3, or release readiness.

## Review / Follow-Up

- Director review required: yes.
- Additional production validation required: only if Director wants a later controlled upload to prove operator-visible behavior during a new parse.
- User decision required now: not for this scoped deployment; a future MinerU ownership normalization still requires explicit user approval.
- GitHub sync: not performed from this DevelopmentEngineer thread; production was already at `origin/main` `416a963`.
