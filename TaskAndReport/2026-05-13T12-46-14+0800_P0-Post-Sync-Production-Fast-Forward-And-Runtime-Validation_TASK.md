# Task: P0 Post-Sync Production Fast-Forward And Runtime Validation

Assignee:
DevelopmentEngineer

Issued by:
Director

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-13T12-46-14+0800_P0-Post-Sync-Production-Fast-Forward-And-Runtime-Validation_TASK.md

## Required Reading Before Execution

- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/development-engineer.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- docs/codex/TEST_POLICY.md
- docs/codex/REPOSITORY_STRUCTURE.md
- docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md
- TaskAndReport/README.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-13T12-18-44+0800_P0-Post-Smoke-Production-Deployment-And-Non-Destructive-Runtime-Validation_TASK.md
- TaskAndReport/2026-05-13T12-18-44+0800_P0-Post-Smoke-Production-Deployment-And-Non-Destructive-Runtime-Validation_REPORT.md
- TaskAndReport/2026-05-13T12-31-58+0800_P0-Post-Smoke-Production-Deployment-And-Non-Destructive-Runtime-Validation_DIRECTOR_REVIEW.md

## Background

Task 81 was blocked because the accepted Task 77/78/79 code path was not yet available to production through GitHub. Director then repaired a local OneDrive/Git loose-object read hang and successfully pushed accepted HEAD `c2b82198eb72a88cbe3e39d5777a946eb30ce666` to GitHub `main`.

Production path `/Users/concm/prod_workspace/Luceon2026` fetched the updated remote and reported `origin/main=c2b8219`, while local production `main` was still behind and had local `docker-compose.override.yml` modifications that must be preserved.

This task resumes the original Task 81 objective after GitHub synchronization was restored.

## Objective

Fast-forward the production deployment path to GitHub `main@c2b8219` if safe, preserve the local production override boundary, perform the minimum necessary non-destructive deployment mechanics, and collect runtime validation evidence.

## Non-Goals

- Do not create a validation upload.
- Do not run pressure test or pressure retry.
- Do not repair, retry, clean up, or mutate failed historical tasks.
- Do not claim production release readiness, L3, pressure PASS, or full acceptance.
- Do not broaden the task into architecture redesign, product-scope changes, or long-run validation.

## Allowed Operations

In production deployment path only:

- `git fetch origin`
- inspect status, HEAD, local override diff, active work, and service state
- if safe, fast-forward production `main` to `origin/main`
- preserve `docker-compose.override.yml` local changes
- run the minimum necessary Docker Compose build/restart for the accepted code path
- run non-destructive runtime checks

Required runtime checks include:

```bash
git status --short --branch
git log -1 --oneline
docker compose ps
bash ops/runtime-ownership-status.sh
curl -fsS http://localhost:8081/__proxy/upload/health
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
curl -sS --max-time 10 http://127.0.0.1:11434/api/ps
```

## Forbidden Changes

- Do not run validation uploads.
- Do not run pressure tests or pressure retries.
- Do not repair failed tasks.
- Do not delete, prune, recreate, or mutate DB, MinIO, Docker volumes, task rows, artifacts, logs, or sample-library files.
- Do not run `docker compose down -v`, `docker volume rm`, `docker system prune`, or equivalent destructive commands.
- Do not restart MinerU, Ollama, MinIO, or DB unless a new Director task explicitly authorizes that operation.
- Do not pull, delete, reload, replace, or change models.
- Do not change secrets.
- Do not change production override/config except what is strictly required by minimum deployment mechanics already authorized here.
- Do not perform broad stack restart/rollback.
- Do not change public APIs or business logic.
- Do not claim production release readiness, L3, pressure PASS, or full acceptance.

If active parse/AI work is present before deployment mechanics, stop before any restart/rebuild and write a blocked report with exact active-work evidence.

## Required Evidence

The report must include:

- production HEAD before and after sync;
- whether `docker-compose.override.yml` was preserved;
- exact deployment/build/restart commands, if any;
- production override/env boundary summary;
- Docker service state summary;
- upload health;
- dependency health with submit probe;
- admission circuit state;
- active parse/AI work state;
- Ollama residency/readiness state;
- whether task-page MinerU progress semantics are observable from current runtime data;
- what was not validated and why;
- risks, blockers, and residual debt.

## GitHub Sync Requirements

GitHub `main` has already been updated to `c2b8219` by Director. This task may fetch and fast-forward production from GitHub, but must not push new commits to GitHub.

## Completion Report Storage Requirements

- Write the completion report into `TaskAndReport/` using this naming rule:
  `2026-05-13T12-46-14+0800_P0-Post-Sync-Production-Fast-Forward-And-Runtime-Validation_REPORT.md`
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch, HEAD, current status, next actor, next action, and required output.

## Acceptance Criteria

- Production is either fast-forwarded to `c2b8219` and non-destructively validated, or the report clearly blocks with exact reason.
- Required runtime surfaces are checked and reported.
- No validation upload, pressure test, failed-task repair, destructive mutation, model operation, broad restart/rollback, or release-readiness claim occurs.
