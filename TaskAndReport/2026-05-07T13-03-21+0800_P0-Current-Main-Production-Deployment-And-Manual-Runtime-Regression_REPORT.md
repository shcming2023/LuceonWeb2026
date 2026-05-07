# Lucode Task Report

Task ID: `TASK-20260507-125133-P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression`

Task brief: `TaskAndReport/2026-05-07T12-51-33+0800_P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression_TASK.md`

Assignee: Lucode

Production path: `/Users/concm/prod_workspace/Luceon2026`

Manual review URL: `http://localhost:8081/cms/`

Status: `READY_WITH_KNOWN_LIMITATIONS`

## HEAD And Git State

- Development workspace before deployment check: `main@a4fcb05a95d59847b6218cb7a8d2f590097fb4e0`, clean, tracking `origin/main`.
- GitHub `origin/main` at execution time: `a4fcb05a95d59847b6218cb7a8d2f590097fb4e0`.
- Note: task issue text mentioned `5ffa31d109b2133fdc31645bba25dfe26d36e136`, but live preflight showed the current GitHub `main` head was `a4fcb05a95d59847b6218cb7a8d2f590097fb4e0`; Lucode deployed the current fetched `origin/main`.
- Production workspace before deployment: `main@f02684c3aee392fdc0e6a9e8fd8da911c17db892`, status `M docker-compose.override.yml`.
- Production workspace after deployment: `main@a4fcb05a95d59847b6218cb7a8d2f590097fb4e0`, status still `M docker-compose.override.yml`.
- The local production override file was preserved and not overwritten.

## Deployment Summary

- Preflight found no active MinerU parse work and no active AI jobs.
- Production workspace was fast-forwarded from `f02684c3...` to `a4fcb05...`.
- `docker compose up -d --build` rebuilt/recreated CMS frontend, DB server, and upload server containers; MinIO remained running and persistent state was not cleared.
- `bash ops/start-luceon-runtime.sh` completed successfully and started sidecar/supervisor sessions.
- Existing MinerU API is reachable on port `8083` through existing `mineru_api` tmux/process, not through the newly named `luceon-mineru` session. The script attempted `luceon-mineru`, but that session exited because port `8083` was already served by the existing MinerU runtime. Dependency health and submit probe passed.

## Runtime Evidence

- Docker status after deployment:
  - `cms-db-server`: Up healthy.
  - `cms-frontend`: Up healthy, `0.0.0.0:8081->80/tcp`.
  - `cms-minio`: Up healthy, persistent container from two days ago.
  - `cms-upload-server`: Up healthy.
- tmux/process evidence:
  - `luceon-sidecar`: present.
  - `luceon-supervisor`: present.
  - `luceon-mineru`: not present.
  - `mineru_api`: present from existing runtime.
  - `lsof -nP -iTCP:8083 -sTCP:LISTEN`: `python3.10 ... mineru-api --host 0.0.0.0 --port 8083`.
  - `curl http://192.168.31.33:8083/health`: healthy, version `3.1.0`, `queued_tasks=0`, `processing_tasks=0`.
- Dependency health with MinerU submit probe:
  - `blocking=false`.
  - `minio.ok=true`.
  - `mineru.ok=true`.
  - `mineru.healthOk=true`.
  - `mineru.submitProbe.enabled=true`.
  - `mineru.submitProbe.ok=true`.
  - `mineru.submitProbe.status=202`.
  - `ollama.ok=true`.
  - `ollama.model=qwen3.5:9b`.
- Dependency repair status:
  - `ok=true`, `message=Supervisor running`.
  - `sessions.sidecar=true`, `sessions.mineru=false`, `services.ollamaReachable=true`.
- Active work after deployment/sample:
  - `activeTask=null`, `currentProcessingTask=null`, `queuedTasks=[]`.
  - Existing historical takeover-required failed tasks remain: `task-1778120784621`, `task-1778118934116`.

## Controlled Sample Upload Evidence

- Path used: API path `POST http://localhost:8081/__proxy/upload/tasks`.
- File: `server/tests/fixtures/sample.pdf`.
- Upload command: Node `FormData` script using the production runtime.
- Uploaded file name: `manual-regression-sample-1778130108356.pdf`.
- `materialId`: `mat-1778130108378`.
- `taskId`: `task-1778130109102`.
- Final task:
  - `state=review-pending`.
  - `stage=review`.
  - `progress=100`.
  - `message=AI 识别完成: review-pending (待人工复核)`.
  - `mineruTaskId=a3c372a3-ceaa-4479-a73d-7f85c44e883c`.
  - `mineruStatus=completed`.
  - `parsedPrefix=parsed/mat-1778130108378/`.
  - `markdownObjectName=parsed/mat-1778130108378/full.md`.
  - `parsedFilesCount=8`.
  - `artifactManifestObjectName=parsed/mat-1778130108378/artifact-manifest.json`.
- MinIO evidence:
  - `artifact-manifest.json` HEAD returned `200`.
  - `full.md` HEAD returned `200`.
- AI metadata evidence:
  - `aiJobId=ai-job-1778130125128-910f`.
  - `state=review-pending`.
  - `message=AI 识别完成 (48191ms)`.
  - `phase=repair-deterministic-succeeded`.
  - `provider=ollama`.
  - `model=qwen3.5:9b`.
  - `deterministicRepair=true`.
  - `repairSucceeded=true`.
  - No skeleton provider was used.
- Sidecar/log observation:
  - Task metadata contained `mineruObservedProgress.attribution=task-1778130109102`, `attributionMode=live-active`.
  - Global observation after completion was `active-progress` but `unattributed` with reason `no matching completed-window task`, which is non-blocking after task completion.

## Commands Run

- Development workspace:
  - `git status --short --branch` -> exit `0`; `## main...origin/main`.
  - `git fetch origin` -> exit `0`.
  - `git rev-parse HEAD` -> exit `0`; `a4fcb05a95d59847b6218cb7a8d2f590097fb4e0`.
  - `git ls-remote --heads origin main` -> exit `0`; `a4fcb05a95d59847b6218cb7a8d2f590097fb4e0`.
- Production preflight:
  - `git status --short --branch` -> exit `0`; `## main...origin/main`, `M docker-compose.override.yml`.
  - `git fetch origin` -> exit `0`.
  - `git rev-parse HEAD || true` -> exit `0`; `f02684c3aee392fdc0e6a9e8fd8da911c17db892`.
  - `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task || true` -> exit `0`; no active/current/queued tasks.
  - `curl -fsS http://localhost:8081/__proxy/db/ai-metadata-jobs || true` -> exit `0`; summary by follow-up script: `total=33`, `review-pending=31`, `failed=2`, `activeCount=0`.
- Deployment:
  - `git pull --ff-only origin main` -> exit `0`; fast-forward `f02684c..a4fcb05`.
  - `docker compose ps` before deployment -> exit `0`.
  - `docker compose up -d --build` -> exit `0`.
  - `bash ops/start-luceon-runtime.sh` -> exit `0`.
- Health and runtime checks:
  - `curl -fsS http://localhost:8081/__proxy/upload/health` -> exit `0`; `{"ok":true,"service":"upload-server"}`.
  - `curl -fsS http://localhost:8081/__proxy/db/health` -> exit `0`; `{"ok":true,"service":"db-server"}`.
  - `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` -> exit `0`; `blocking=false`, submit probe ok.
  - `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status` -> exit `0`; supervisor running.
  - `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/global-observation` -> exit `0`; global observation available.
  - `docker compose ps` after deployment -> exit `0`; all Docker services healthy.
- Required validation:
  - `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 run tier2:standard:check` -> exit `0`; Tier 2 Standard pre-check PASS.
  - `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh` -> exit `0`; `12 passed / 0 failed / 0 skipped`.
  - `node server/tests/ai-metadata-repair-hardening-smoke.mjs` -> exit `0`.
  - `node server/tests/mineru-sidecar-completed-window-smoke.mjs` -> exit `0`.
  - `node server/tests/mineru-log-progress-smoke.mjs` -> exit `0`; `118 passed / 0 failed`.
- Controlled sample:
  - Node `FormData` upload/poll script -> exit `0`; final task `review-pending`, AI job `review-pending`.

## Skipped Checks

- No destructive cleanup, DB migration, MinIO cleanup, Docker volume removal, or failed-task repair was run.
- No release-readiness, L3, large-PDF soak, concurrency, rollback, permission/security, or full-site acceptance validation was attempted because those are non-goals.

## Risks / Known Limitations

- `luceon-mineru` tmux session is absent even though MinerU API is healthy via existing `mineru_api` tmux/process. Manual review is not blocked, but Lucia should decide whether ops naming convergence is required in a follow-up.
- Two historical failed AI-stage tasks remain in takeover-required diagnostics; they predate this deployment and were not mutated under this task.
- Production `docker-compose.override.yml` remains locally modified as a preserved machine-specific override.

## Manual Review Readiness

`READY_WITH_KNOWN_LIMITATIONS`

The production runtime is reachable at `http://localhost:8081/cms/`, dependency health is non-blocking with MinerU submit probe passing, Tier 2 Standard and smoke checks pass, and the controlled PDF sample reached `review-pending` with MinerU, MinIO, and Ollama AI evidence.

## GitHub Sync

This report and the task-tracking update must be committed and pushed to GitHub `main` for Lucia review.

## Review Needed

Lucia review is required. Director manual review can proceed at `http://localhost:8081/cms/` with the known limitations above.
