# Task: P0 Production Deployment For Manual Review

```text
Task:
P0 Production Deployment For Manual Review

Assignee:
Lucode

Issued by:
Lucia

Project:
Luceon2026

Date:
2026-05-07

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-07T09-44-05+0800_P0-Production-Deployment-For-Manual-Review_TASK.md

Required reading before execution:
- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/lucode.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/codex/TEST_POLICY.md
- docs/prd/Luceon2026-PRD-v0.4.md
- docs/deploy/DEPLOY.md
- TaskAndReport/TASK_TRACKING_LIST.md

Background:
TD-001 MinerU submit-path probe has been implemented, merged to GitHub `main`, accepted by Lucia, and validated in a rebuilt local Tier 2 Standard runtime.
Director now requires deployment to the production deployment path so the current application can be manually reviewed.

Current known facts:
- Current GitHub `main` HEAD at task issue time: `39c7e6b3433f43d88d55434a877c03ab7bbff563`.
- Production deployment path exists: `/Users/concm/prod_workspace/Luceon2026`.
- Lucia preflight at issue time observed production workspace:
  - branch: `fix/p2-upload-entry-testability-enhancement...origin/fix/p2-upload-entry-testability-enhancement`
  - HEAD: `042c6508e8357fa07c6a0bb12ec48fc09129e8cc`
  - modified files: `.workbuddy/memory/MEMORY.md`, `docker-compose.override.yml`
  - untracked file: `.workbuddy/memory/2026-05-02.md`
- Production workspace is therefore not a clean `main` checkout. Local configuration and local memory files must not be overwritten silently.

Objective:
Deploy the current GitHub `main` to `/Users/concm/prod_workspace/Luceon2026` non-destructively and provide Director with a stable manual-review URL plus deployment health evidence.

Non-goals:
- Do not implement new product features.
- Do not change PRD truth, project ledger, handoff, role contracts, or release judgments.
- Do not claim production release readiness.
- Do not perform L3, load, concurrency, rollback rehearsal, permissions/security, or full error-path acceptance unless separately assigned.
- Do not create sample business data unless explicitly needed for a smoke check and clearly reported.

Critical safety requirements:
1. Treat production data and local production configuration as protected.
2. Do not run `git reset --hard`, `git clean`, `docker compose down -v`, volume deletion, MinIO bucket deletion, DB deletion, or data cleanup.
3. Do not discard or overwrite production `docker-compose.override.yml` changes.
4. Before changing the production checkout, create a timestamped safety record that includes:
   - `git status --short --branch`
   - `git rev-parse HEAD`
   - `git diff -- docker-compose.override.yml`
   - `git diff -- .workbuddy/memory/MEMORY.md`
   - list of untracked files
   - Docker compose status if Docker is available
5. If local production changes block switching to `main`, preserve them through an explicit patch or copied safety bundle before proceeding. If safe preservation is not possible, stop and write a blocked report.
6. Any production-specific override that is required for service ports or host connectivity must be preserved or intentionally reapplied after syncing `main`.

Required steps:
1. In the development workspace, confirm the task brief and current `origin/main`.
2. In the production deployment path, perform the safety preflight described above.
3. Sync production deployment code to GitHub `main` at `39c7e6b3433f43d88d55434a877c03ab7bbff563` or newer `origin/main` only if newer commits are already on GitHub `main`.
4. Install dependencies only if needed and using the project package manager policy.
5. Build and restart the production Docker stack non-destructively using the existing production compose shape. Prefer the existing production `.env` and `docker-compose.override.yml` rather than replacing them.
6. Confirm the resulting production runtime URL for Director manual review.
7. Validate basic health through the deployed URL:
   - `/cms/`
   - `/cms/tasks`
   - `/__proxy/upload/health`
   - `/__proxy/db/health`
   - `/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true`
8. Confirm dependency-health includes:
   - `dependencies.mineru.healthOk`
   - `dependencies.mineru.submitProbe.enabled`
   - `dependencies.mineru.submitProbe.ok`
9. Run smoke checks against the production URL if reachable without destructive side effects.
10. Write a completion report in the development workspace under `TaskAndReport/`.
11. Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, deployed HEAD, production URL, status, and next actor.
12. Commit and push only task/report tracking changes to GitHub `main`. Do not commit production-only config or local production memory files.

Required commands, adjusted only when production configuration requires it:
- Development workspace:
  - `git status --short --branch`
  - `git fetch origin`
  - `git pull --ff-only origin main`
- Production deployment path:
  - `git status --short --branch`
  - `git rev-parse HEAD`
  - `git fetch origin`
  - `git rev-parse origin/main`
  - `docker compose ps`
  - `docker compose config --quiet`
  - non-destructive deploy command, expected shape: `docker compose up -d --build`
  - `docker compose ps`
  - health checks with `curl` or equivalent
- Validation:
  - `BASE_URL=<production-url> bash uat/smoke-test.sh`, if the production URL is reachable and the check does not mutate business data
  - dependency-health submit probe check against `<production-url>/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true`

Required report evidence:
- Production preflight state before deployment.
- Safety bundle or patch path if local production changes were preserved.
- Exact deployed commit hash.
- Exact deploy command and exit code.
- Docker compose status after deployment.
- Manual-review URL for Director.
- Health endpoint results.
- Dependency-health MinerU fields, including `healthOk` and `submitProbe`.
- UAT smoke result or exact skipped reason.
- Any production configuration preserved or reapplied.
- Any blocker, risk, or residual technical debt.
- Clear statement that this deployment is for manual review and does not claim production release readiness.

Forbidden operations:
- Do not run `docker compose down -v`.
- Do not remove Docker volumes, MinIO buckets, DB files, or production data.
- Do not force-push any branch.
- Do not use `git reset --hard` or `git clean`.
- Do not commit secrets, `.env`, production-only local config, or `.workbuddy` memory files.
- Do not replace production `docker-compose.override.yml` without preserving and reporting the previous content.

Completion report storage requirements:
- Write the completion report into TaskAndReport/ using this naming rule:
  YYYY-MM-DDTHH-MM-SS+0800_P0-Production-Deployment-For-Manual-Review_REPORT.md
- Update TaskAndReport/TASK_TRACKING_LIST.md with report path, production URL, deployed HEAD, current status, and next actor.

Completion report must include:
- confirmation that work was based on this Lucia task brief
- production workspace preflight status
- deployed branch and HEAD
- deployment commands and exit codes
- health and dependency-health evidence
- manual-review URL
- checks skipped and reasons
- production safety notes
- blockers, risks, or residual technical debt
- whether Lucia review or Director decision is required

Acceptance criteria:
- Production deployment path is safely updated to current GitHub `main` or a precise blocker is reported.
- Existing production data and configuration are not destroyed.
- Director receives a working manual-review URL.
- Basic production health checks pass, including upload-server and db-server health.
- MinerU dependency-health submit-probe fields are present; if submit probe cannot pass in production, the report must classify the blocker precisely.
- TaskAndReport is updated and pushed to GitHub `main`.
```
