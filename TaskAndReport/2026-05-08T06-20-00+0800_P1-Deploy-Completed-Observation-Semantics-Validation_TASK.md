# Lucia Task Brief

Task ID: `TASK-20260508-062000-P1-Deploy-Completed-Observation-Semantics-Validation`

Task name: P1 Deploy Completed Observation Semantics Validation

Issued at: `2026-05-08T06:20:00+0800`

Issuer: Lucia

Assignee: Lucode

Priority: P1

## Background

Task `TASK-20260507-142907-P1-Completed-Task-Observation-And-Ops-Session-Semantics` has been accepted at code level and integrated into `main` as commit `a3078b019f1abb4fc71777bc31f5b950e7ebee65`.

The accepted code changes tighten two observability semantics:

- Terminal local-MinerU tasks with an existing observation should not keep receiving misleading post-completion observation mutations.
- Dependency repair/session status should separate service reachability from tmux session ownership.

## Objective

Deploy current GitHub `main` to `/Users/concm/prod_workspace/Luceon2026` without destructive operations, then validate the two observability semantics in the production runtime at `http://localhost:8081/cms/`.

## Non-Goals

- Do not claim production release readiness, staging readiness, L3 readiness, or full-site acceptance.
- Do not delete, reset, truncate, migrate, clean, or repair production DB, MinIO, Docker volumes, historical tasks, generated artifacts, credentials, or local overrides.
- Do not broaden this into core pipeline feature work.
- Do not rename or kill unmanaged production tmux sessions unless active-task preflight proves it is safe and Lucia explicitly assigned that operation.

## Required Preflight

Run from `/Users/concm/prod_workspace/Luceon2026`:

```bash
git status --short --branch
git fetch origin
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task || true
curl -fsS http://localhost:8081/__proxy/db/ai-metadata-jobs || true
```

If active parse or AI work is running, do not restart services. Write a blocked report instead.

## Required Work

1. Fast-forward production workspace to current `origin/main`.
2. Preserve `.env`, `docker-compose.override.yml`, credentials, logs, DB, MinIO, and Docker volumes.
3. Rebuild/restart services only if preflight confirms no active work blocks restart.
4. Start or recover runtime sessions only if safe.
5. Validate dependency health and dependency repair status.
6. Run smoke checks against `http://localhost:8081`.
7. Execute one controlled sample upload using `server/tests/fixtures/sample.pdf` if preflight remains green.
8. Verify completed-task observation semantics:
   - terminal task reaches `review-pending` or another accepted terminal state;
   - after terminal completion, later completed-window observations do not mutate the task's existing final observation;
   - stale or diagnostic wording does not imply the completed task is still processing.
9. Verify dependency repair/session semantics:
   - `services.mineruReachable` accurately reports MinerU service reachability;
   - `sessions.mineru` remains a managed tmux ownership fact;
   - `ownership.mineru.warning` or unmanaged-session fields distinguish reachable unmanaged sessions from dependency outage;
   - Ollama reachability and ownership are similarly separated.

## Required Checks

Run and report exit codes for:

```bash
git status --short --branch
git fetch origin
git pull --ff-only origin main
docker compose up -d --build
bash ops/start-luceon-runtime.sh
curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status
BASE_URL=http://localhost:8081 bash uat/smoke-test.sh
node server/tests/mineru-completed-observation-semantics-smoke.mjs
node server/tests/dependency-supervisor-smoke.mjs
node server/tests/mineru-log-observation-transport-smoke.mjs
node server/tests/mineru-sidecar-completed-window-smoke.mjs
node server/tests/mineru-log-progress-smoke.mjs
```

If `bash ops/start-luceon-runtime.sh` is unsafe because active work is running, skip it and report the exact blocker.

## Required Report

Store the report in `TaskAndReport/` and update `TaskAndReport/TASK_TRACKING_LIST.md`.

The report must include:

- Production HEAD before and after deployment.
- Runtime health summary.
- Controlled sample task id, material id, final state, MinerU status, parsed artifacts, and AI job state.
- Evidence that completed-task observation remains stable or is explicitly non-mutating after terminal completion.
- Evidence that dependency repair/status separates service reachability from tmux ownership.
- Confirmation that no destructive production operation occurred.

## Acceptance Criteria

- Current `main` is deployed to production workspace unless preflight blocks it.
- Runtime remains reachable at `http://localhost:8081/cms/`.
- Core smoke checks pass.
- Completed-task observation semantics are validated in production runtime.
- Dependency status semantics distinguish reachable services from unmanaged tmux ownership.
