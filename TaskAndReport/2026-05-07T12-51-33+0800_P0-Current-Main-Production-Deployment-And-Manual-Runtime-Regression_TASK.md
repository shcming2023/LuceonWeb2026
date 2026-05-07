# Lucia Task Brief

Task ID: `TASK-20260507-125133-P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression`

Task name: P0 Current Main Production Deployment And Manual Runtime Regression

Issued at: `2026-05-07T12:51:33+0800`

Issuer: Lucia

Assignee: Lucode

Priority: P0

Project: Luceon2026

Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path: `/Users/concm/prod_workspace/Luceon2026`

GitHub: `https://github.com/shcming2023/Luceon2026`

TaskAndReport record: `TaskAndReport/2026-05-07T12-51-33+0800_P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

The current `main` branch has completed the recent Phase 1 repair chain:

- MinerU submit-path health probe is merged.
- AI JSON Repair input hardening is merged.
- MinerU sidecar completed-window log backfill is merged.
- MinerU log progress smoke truth alignment is merged.

The Director has approved the next step: deploy current `main` to the production workspace and prepare `http://localhost:8081/cms/` for manual review.

## Current Known Facts

- Current GitHub `main` HEAD at task issue time: `5ffa31d109b2133fdc31645bba25dfe26d36e136`.
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`.
- Manual review URL: `http://localhost:8081/cms/`.
- Current Phase 1 external behavior must remain unchanged: upload -> MinerU -> MinIO -> AI metadata -> review/confirmed state.
- Strict AI mode must remain strict: no silent skeleton success when required AI recognition fails.

## Objective

Deploy current GitHub `main` into the production workspace and verify that the manual-review runtime is ready for Director inspection.

This task must produce an evidence-based deployment report. The report must clearly state whether the production runtime is ready for manual review, not whether it is release-ready.

## Non-Goals

- Do not claim production release readiness, staging readiness, L3 readiness, or full-site acceptance.
- Do not modify PRD truth, role contracts, or release judgments.
- Do not clean, reset, delete, truncate, or migrate production DB, MinIO buckets, Docker volumes, or user data.
- Do not repair unrelated historical tasks or mutate existing failed tasks unless explicitly required by this task.
- Do not broaden this into architectural refactor, UI redesign, dependency upgrade, or test-suite cleanup.

## Allowed Files, Modules, Or Operations

- Production workspace Git sync to current `origin/main`.
- Production Docker image rebuild and service restart, only after preflight confirms no active parse/AI work is in progress.
- Runtime start/recovery through existing project scripts, including `ops/start-luceon-runtime.sh`, if safe to run.
- Read-only production diagnostics through HTTP endpoints, Docker status/logs, tmux session status, and existing smoke/check scripts.
- One controlled sample upload using `server/tests/fixtures/sample.pdf`, only if all preflight gates are green and no active production work is running.
- `TaskAndReport/` report and tracking-list updates.

## Forbidden Changes

- Do not run `git reset --hard`, `git clean`, `docker compose down -v`, `docker volume rm`, MinIO cleanup, DB cleanup, or any equivalent destructive command.
- Do not overwrite `.env`, `docker-compose.override.yml`, local credentials, or machine-specific runtime overrides.
- Do not commit secrets, tokens, local private credentials, logs, DB snapshots, MinIO objects, or machine-only artifacts.
- Do not restart MinerU, Docker services, sidecar, or supervisor if active production parse/AI work is detected. In that case, write a blocked report and leave the task for Lucia review.
- Do not use `.skip`, assertion weakening, or mocked evidence as a substitute for production runtime evidence.
- Do not configure AI skeleton fallback or silent degradation.

## Required Preflight

Run from the development workspace:

```bash
cd /Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026
git status --short --branch
git fetch origin
git rev-parse HEAD
git ls-remote --heads origin main
```

Run from the production workspace before any restart:

```bash
cd /Users/concm/prod_workspace/Luceon2026
git status --short --branch
git fetch origin
git rev-parse HEAD || true
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task || true
curl -fsS http://localhost:8081/__proxy/db/ai-metadata-jobs || true
```

If the preflight shows active parse work, active AI work, or Git state that cannot be safely fast-forwarded, stop and write a blocked completion report. Do not force the workspace into shape.

## Suggested Direction

1. Fast-forward production workspace to `origin/main`.
2. Preserve existing local runtime overrides and environment files.
3. Build and start production services without clearing persistent state.
4. Ensure `luceon-mineru`, `luceon-sidecar`, and `luceon-supervisor` are running when safe.
5. Verify dependency health with MinerU submit probe enabled.
6. Run core smoke and Tier 2 Standard checks against `http://localhost:8081`.
7. If all gates are green and no active work is present, run one controlled sample upload using `server/tests/fixtures/sample.pdf`; poll until a terminal or review state is reached, then record task id, material id, parse artifacts, AI job state, and observed sidecar/log fields.
8. Leave the production runtime available at `http://localhost:8081/cms/` for Director manual review.

## Required Checks

Lucode must run and report exit codes for:

```bash
git status --short --branch
git fetch origin
git pull --ff-only origin main
docker compose ps
docker compose up -d --build
bash ops/start-luceon-runtime.sh
curl -fsS http://localhost:8081/__proxy/upload/health
curl -fsS http://localhost:8081/__proxy/db/health
curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status
curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/global-observation
BASE_URL=http://localhost:8081 npx pnpm@10.4.1 run tier2:standard:check
BASE_URL=http://localhost:8081 bash uat/smoke-test.sh
node server/tests/ai-metadata-repair-hardening-smoke.mjs
node server/tests/mineru-sidecar-completed-window-smoke.mjs
node server/tests/mineru-log-progress-smoke.mjs
```

If `bash ops/start-luceon-runtime.sh` is unsafe because active work is running, skip it and report the exact blocker.

## Required Evidence

The completion report must include:

- Development workspace HEAD and GitHub `origin/main` HEAD.
- Production workspace HEAD before and after deployment.
- Production `git status --short --branch` before and after deployment.
- Docker service status after deployment.
- tmux/session or process evidence for MinerU, sidecar, and supervisor.
- Dependency-health JSON summary including `blocking`, MinIO, MinerU `healthOk`, MinerU `submitProbe.ok`, Ollama, and sidecar/supervisor status.
- Smoke and Tier 2 Standard results.
- Controlled sample upload evidence if executed:
  - exact command or UI/API path used
  - material id and task id
  - final task state/stage/message
  - MinerU status and parsed artifact fields
  - AI metadata job state and whether strict mode was preserved
  - sidecar/global observation status if available
- Manual review readiness statement:
  - `READY_FOR_MANUAL_REVIEW`
  - `NOT_READY_BLOCKED`
  - or `READY_WITH_KNOWN_LIMITATIONS`

## GitHub Sync Requirements

- If repository files are changed for reports/tracking, commit and push them to GitHub.
- Do not merge or push unrelated code changes.
- Report file must be written to `TaskAndReport/`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch/HEAD, current status, next actor, next action, and required output.

## Completion Report Storage Requirements

- Report file name: `TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression_REPORT.md`.
- Do not rely on Director chat relay for completion reporting.

## Completion Report Must Include

- Confirmation that work was based on this Lucia task brief.
- Branch and HEAD.
- Files changed.
- Deployment summary.
- Commands run with exit codes.
- Checks skipped and reasons.
- Runtime evidence.
- Risks, blockers, or residual technical debt.
- GitHub sync status.
- Whether Lucia review, Director decision, or additional validation is required.

## Acceptance Criteria

- Production workspace is fast-forwarded to current GitHub `main` unless preflight proves that a safe deployment is blocked.
- Runtime is reachable at `http://localhost:8081/cms/`.
- Dependency health is non-blocking, with MinerU submit probe passing.
- Core smoke and Tier 2 Standard checks pass, or blockers are precisely documented with raw evidence.
- If controlled sample upload is executed, it reaches a terminal or review state with MinerU and AI evidence recorded.
- No destructive production operation is performed.
