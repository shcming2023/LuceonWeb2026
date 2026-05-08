# P0 Release Candidate Non-Destructive Preflight And Evidence Pack

Task:
P0 Release Candidate Non-Destructive Preflight And Evidence Pack

Assignee:
Lucode

Issued by:
Lucia

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T10-41-37+0800_P0-Release-Candidate-Non-Destructive-Preflight-And-Evidence-Pack_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `TaskAndReport/2026-05-08T10-31-12+0800_P0-Production-Release-Readiness-Gap-Matrix-And-Validation-Plan_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Lucode's release-readiness gap matrix was accepted by Lucia. The next safe step is to gather a non-destructive release-candidate preflight evidence pack while Director-owned operational decisions remain pending.

## Objective

Produce a non-destructive evidence pack that shows the current release-candidate baseline, reachable runtime dependencies, existing production workspace boundary, and the exact remaining blockers before any production release-readiness claim.

## Non-goals

- Do not approve production release readiness.
- Do not deploy, rebuild, restart, rollback, or mutate the production runtime.
- Do not run Docker pull/build/compose operations.
- Do not mutate DB, MinIO, Docker volumes, tasks, production artifacts, secrets, or local overrides.
- Do not implement fixes.
- Do not change PRD truth, role contracts, or release judgments.

## Allowed Operations

- Read repository documents, source, tests, scripts, and configuration.
- Run read-only git commands in the development workspace and production workspace.
- Run read-only runtime health checks against the already-running `http://localhost:8081` service.
- Run non-mutating local checks in the development workspace if they do not require service restarts.
- Write one completion report under `TaskAndReport/`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md`.

## Required Checks

In the development workspace:

- `git status --short --branch`
- `git fetch origin`
- `git pull --ff-only origin main`
- `git log -1 --oneline`
- `git diff --check`
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`
- `node server/tests/dependency-health-smoke.mjs`

Read-only runtime checks, if the service is reachable:

- `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`
- `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status`
- `curl -fsS http://localhost:8081/__proxy/db/health`

In the production workspace, read-only only:

- `git status --short --branch`
- `git log -1 --oneline`
- `git diff --stat`

If any check is skipped, report the exact reason.

## Required Evidence

The report must include:

- Development workspace HEAD and cleanliness.
- Production workspace HEAD, branch divergence, and local modification boundary.
- Runtime dependency-health summary with MinerU submit probe result.
- DB health summary.
- Ops-session status summary.
- TypeScript/build/dependency smoke results.
- Exact blockers that remain before production release-readiness review.
- Director decisions still pending.

## Forbidden Changes

- Do not restart or rebuild any service.
- Do not run `docker compose up`, `docker compose down`, `docker compose restart`, `docker pull`, or equivalent production-changing commands.
- Do not repair DB/MinIO/task state.
- Do not alter `docker-compose.override.yml`.
- Do not claim production release readiness.

## Completion Report Requirements

- Write report to `TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Release-Candidate-Non-Destructive-Preflight-And-Evidence-Pack_REPORT.md`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch/HEAD, status `已回报待审`, `Next Actor=Lucia`, next action, and required output.
- Commit and push only the report and task tracking update if repository files are changed.

## Acceptance Criteria

- Evidence pack is complete and non-destructive.
- All executed commands include exit codes.
- Any skipped checks include exact reasons.
- Production release readiness is not claimed.
- Remaining blockers and Director decisions are explicit.
