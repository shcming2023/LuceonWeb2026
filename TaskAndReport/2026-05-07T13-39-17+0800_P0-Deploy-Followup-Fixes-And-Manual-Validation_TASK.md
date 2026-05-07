# Lucia Task Brief

Task ID: `TASK-20260507-133917-P0-Deploy-Followup-Fixes-And-Manual-Validation`

Task name: P0 Deploy Followup Fixes And Manual Validation

Issued at: `2026-05-07T13:39:17+0800`

Issuer: Lucia

Assignee: Lucode

Priority: P0

## Background

Tasks 11 and 12 were accepted at code level and integrated into `main`, but both require production runtime validation before their manual-review impact can be promoted.

Accepted code-level changes:

- MinerU log observer source is explicit and attribution has a bounded timestamp tolerance.
- AI deterministic repair success and reachable-but-unmanaged Ollama now have more accurate UI/ops wording.

## Objective

Deploy current GitHub `main` with the accepted follow-up fixes into `/Users/concm/prod_workspace/Luceon2026`, then validate the manual-review runtime at `http://localhost:8081/cms/`.

## Non-Goals

- Do not claim production release readiness, staging readiness, L3 readiness, or full-site acceptance.
- Do not clean, reset, delete, truncate, migrate, or repair production DB, MinIO, Docker volumes, or historical failed tasks.
- Do not change code outside a narrow report/tracking update.
- Do not broaden this into new feature work.

## Required Preflight

Before deployment, run from production workspace:

```bash
cd /Users/concm/prod_workspace/Luceon2026
git status --short --branch
git fetch origin
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task || true
curl -fsS http://localhost:8081/__proxy/db/ai-metadata-jobs || true
```

If active parse or AI work is running, do not restart services. Write a blocked report instead.

## Required Work

1. Fast-forward production workspace to current `origin/main`.
2. Preserve `.env`, `docker-compose.override.yml`, credentials, logs, DB, MinIO, and Docker volumes.
3. Rebuild/restart services without clearing persistent state.
4. Start/recover runtime sessions only if no active task blocks restart.
5. Validate dependency health with MinerU submit probe.
6. Run Tier 2 Standard and UAT smoke against `http://localhost:8081`.
7. Execute one controlled production sample upload using `server/tests/fixtures/sample.pdf` if preflight remains green.
8. Verify task-level MinerU observation fields after the sample:
   - `mineruObservedProgress.activityLevel`
   - `attribution`
   - `attributionMode`
   - `logSource.logSourceContext`
   - `logFreshnessDiagnostic` or `mountDiagnostic`
9. Verify AI UI/status semantics for a deterministic repair success case:
   - backend result is provider `ollama`, not skeleton
   - UI or source-visible status says completed/review-needed, not AI dependency blocked
   - reachable-but-unmanaged Ollama is not presented as service outage
10. Store the report in `TaskAndReport/` and update the tracking list.

## Required Checks

Lucode must run and report exit codes for:

```bash
git status --short --branch
git fetch origin
git pull --ff-only origin main
docker compose up -d --build
bash ops/start-luceon-runtime.sh
curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status
BASE_URL=http://localhost:8081 npx pnpm@10.4.1 run tier2:standard:check
BASE_URL=http://localhost:8081 bash uat/smoke-test.sh
node server/tests/mineru-log-observation-transport-smoke.mjs
node server/tests/mineru-sidecar-completed-window-smoke.mjs
node server/tests/mineru-log-progress-smoke.mjs
```

If `bash ops/start-luceon-runtime.sh` is unsafe because active work is running, skip it and report the exact blocker.

## Required Evidence

- Production HEAD before and after deployment.
- Runtime health summary.
- Controlled sample task id, material id, final state, MinerU status, parsed artifacts, AI job state, and observation fields.
- Evidence for deterministic repair wording or status rendering.
- Confirmation that no destructive production operation occurred.

## GitHub Sync Requirements

- Store report under `TaskAndReport/`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md`.
- Commit and push report/tracking updates to GitHub `main`.

## Acceptance Criteria

- Current `main` is deployed to production workspace unless preflight blocks it.
- Runtime remains reachable at `http://localhost:8081/cms/`.
- Core health and smoke checks pass.
- Controlled sample demonstrates improved or accurately diagnosed MinerU observation.
- AI deterministic repair success is not presented as AI dependency blocked.
