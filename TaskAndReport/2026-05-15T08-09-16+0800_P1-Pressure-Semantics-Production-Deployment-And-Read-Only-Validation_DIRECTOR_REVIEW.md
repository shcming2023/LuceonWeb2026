# Director Review: P1 Pressure Semantics Production Deployment And Read-Only Validation

- Reviewed task: `TASK-20260515-075503-P1-Pressure-Semantics-Production-Deployment-And-Read-Only-Validation`
- Reviewed report: `TaskAndReport/2026-05-15T07-55-03+0800_P1-Pressure-Semantics-Production-Deployment-And-Read-Only-Validation_REPORT.md`
- Review time: 2026-05-15T08:09:16+0800
- Reviewer: Director
- Result: `ACCEPTED_SCOPED_DEPLOYMENT_AND_READ_ONLY_VALIDATION_PASS_ACCEPTANCE_REVIEW_REQUIRED`

## Review Summary

Task 159 is accepted at the scoped production deployment and read-only validation level.

The accepted Task 157 code is now deployed in production: production fast-forwarded from `89271a1` to `91c1352`, which contains the accepted implementation commit `2b59ef4`. The DevelopmentEngineer report records required preflight, marker checks, deployment command exit codes, post-deploy health, and read-only browser evidence.

This review does not declare production readiness, release readiness, L3, pressure PASS, production上线, or go-live readiness.

## Evidence Reviewed

- DevelopmentEngineer report confirms the work was based on the Director task brief and required reading.
- Production before deployment: `main` at `89271a1`.
- Production after deployment: `main` at `91c1352`.
- Accepted target commit present in production history: `2b59ef4 Accept pressure semantics and AI failure contract`.
- Accepted production source markers were present:
  - `ai-failure-backfill`
  - `pressure-result-semantics`
  - `deriveMineruRuntimeProgressTruth`
  - `partial-success-with-retryable-ai-residuals`
  - `AI 识别失败，待人工判断是否手动重试`
- `docker compose up -d --build upload-server cms-frontend` exited `0`.
- Compose recreated `cms-db-server`, `cms-upload-server`, and `cms-frontend`; `cms-minio` remained running. This was broader than the named service pair but was recorded, and post-deploy health passed.
- Post-deploy checks in the report show healthy core services, upload health OK, dependency-health non-blocking, admission circuit closed, active-task idle, direct MinerU healthy, `/cms/` 200, and `/cms/tasks` 200.
- Browser read-only validation visited `/cms/tasks` and `task-1778765415701`; observed 0 relevant `[db-sync]` warnings/errors, 0 Failed-to-fetch, 0 HTTP 5xx, 0 non-stream request failures, `/settings` 2x200, and `/secrets` 2x200.

## Director Spot Check

Director independently ran read-only production checks after reviewing the report:

- Production `git status --short --branch`: `main...origin/main` with six known local modified files still present:
  - `.gitignore`
  - `docker-compose.override.yml`
  - `server/db-server.mjs`
  - `server/tests/worker-smoke.mjs`
  - `src/app/components/BatchUploadModal.tsx`
  - `src/app/pages/SourceMaterialsPage.tsx`
- Production `git log -1 --oneline`: `91c1352 Authorize pressure semantics production deployment`.
- `docker compose ps`: `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` healthy.
- Upload health returned `{"ok":true,"service":"upload-server"}`.
- Canonical dependency-health route `/__proxy/upload/ops/dependency-health?ollamaChatProbe=true` returned `ok=true`, `blocking=false`, MinerU OK, MinIO OK, Ollama resident/chat OK, and `keepAlive.value=24h`.
- MinerU admission circuit returned `open=false`.
- Active-task diagnostics returned `activeTask=null` and no queued/current/drift/takeover work; historical AI failures remain listed as historical.
- Direct MinerU `/health` returned healthy with `queued_tasks=0` and `processing_tasks=0`.
- `/cms/tasks` returned HTTP `200`.

The earlier short route `/__proxy/upload/dependency-health` returns 404 and is not the canonical endpoint. This is not a blocker because the canonical `/__proxy/upload/ops/dependency-health` route passed.

## Boundary Judgment

Accepted:

- Production has the accepted pressure semantics code.
- Production deployment/read-only health checks passed.
- Existing task-list/detail read-only browser checks did not show the db-sync/browser-noise regressions being guarded here.

Not accepted or not claimed:

- No PDF upload validation was performed.
- No pressure, batch, soak, or broader serial validation was performed.
- No cleanup, cancel, repair, retry, reparse, or re-AI was performed.
- No destructive DB, MinIO, Docker volume, or data mutation was performed.
- No Docker down, volume cleanup, prune, MinerU/Ollama/supervisor mutation, settings/secrets/config/model/sample mutation, automatic retry/requeue, or skeleton fallback weakening was authorized or accepted.
- No production readiness, release readiness, L3, pressure PASS, production上线, or go-live readiness is declared.

## Residual Risk And Next Step

Residual risks:

- Production still contains six local modified files. They did not block this deployment, but they remain a source-drift/override boundary that must stay visible.
- Compose recreated `db-server` as a dependency of the requested service deployment. Health is now good, but this should remain visible as operational evidence.
- Task 159 proves deployment and read-only health only. It does not prove the newly deployed operator-facing pressure semantics under a fresh upload or broader pressure path.

Next step:

- Issue Task 160 to `TestAcceptanceEngineer` for a read-only production acceptance review of the deployed pressure semantics on existing tasks only. This next task must not upload files, clean or repair data, retry/reparse/re-AI tasks, mutate services/config/secrets/models/samples, or declare readiness.
