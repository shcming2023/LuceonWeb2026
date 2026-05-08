# P0 Production Release Readiness Gap Matrix And Validation Plan

Task:
P0 Production Release Readiness Gap Matrix And Validation Plan

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
`TaskAndReport/2026-05-08T10-19-44+0800_P0-Production-Release-Readiness-Gap-Matrix-And-Validation-Plan_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Phase 1 has validated the local real-runtime mainline and has production manual-review readiness evidence. Production release readiness is still explicitly unclaimed.

The Director route decision remained unanswered after two Lucia heartbeat checks. Lucia therefore selected the conservative default route: produce a non-destructive production release-readiness gap matrix and validation plan.

## Current Known Facts

- Current Phase 1 mainline: upload -> local MinerU -> MinIO -> Ollama `qwen3.5:9b` -> AI metadata -> operator review.
- Strict no-skeleton behavior is required.
- Production manual-review URL has been validated as `http://localhost:8081/cms/`.
- Production release readiness, staging readiness, L3 readiness, and full-site acceptance remain unclaimed.
- Known open or documented boundaries include large-PDF soak, concurrent upload, permissions/security, rollback rehearsal, folder upload, error-path validation, monolithic `server/upload-server.mjs`, compatibility-only online MinerU v4, legacy redirects, Vite chunk-size warning, and Docker frontend base-image metadata preflight.

## PRD / Contract Reference

- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/HANDOFF.md`
- `docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md`

## Objective

Create a production release-readiness gap matrix and a concrete validation plan for Phase 1.

The output must distinguish:

- Already accepted evidence.
- Evidence that supports production manual-review readiness only.
- Missing evidence required before production release readiness can be claimed.
- Non-blocking technical debt.
- Blocking release-readiness gaps.
- Recommended validation sequence.

## Non-goals

- Do not approve production release readiness.
- Do not deploy, rebuild, restart, or mutate the production runtime.
- Do not change application behavior.
- Do not implement fixes.
- Do not change PRD truth or role contracts.
- Do not delete, repair, or mutate DB, MinIO, Docker volumes, production artifacts, or historical tasks.

## Allowed Files, Modules, Or Operations

- Read repository documents, source code, tests, scripts, and configuration.
- Run read-only git inspection commands.
- Run read-only runtime health checks if the current runtime is already reachable.
- Create one Lucode report in `TaskAndReport/`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch/HEAD, status, next actor, next action, and required output.

## Forbidden Changes

- Do not start from vague oral instructions or self-created tasks.
- Do not broaden scope beyond this task brief.
- Do not perform broad rewrites or framework-level refactors.
- Do not change unrelated files.
- Do not change PRD truth, project ledger facts, role contracts, or release judgments.
- Do not commit secrets, tokens, local private credentials, or machine-only artifacts.
- Do not run destructive production, MinIO, DB, Docker volume, or data cleanup commands.
- Do not restart MinerU, Ollama, MinIO, DB, upload server, Docker Compose services, sidecar, or supervisor.
- Do not restore deprecated heuristic chapter-preprocessing logic as a main path.
- Do not configure silent degradation for required parsing, preprocessing, or AI recognition paths.
- Do not claim UAT, L2, L3, production readiness, or release readiness.

## Suggested Direction

Build a matrix with at least these columns:

- Area
- Current accepted evidence
- Current boundary label
- Release-readiness requirement
- Gap
- Proposed validation method
- Required command or manual check
- Risk if skipped
- Recommended priority
- Suggested owner

Cover at minimum:

- Upload path.
- MinerU submit path.
- MinIO raw and parsed artifact persistence.
- AI metadata recognition and strict no-skeleton behavior.
- Operator review flow.
- Large-PDF and long-running task behavior.
- Concurrency.
- Error-path behavior.
- Permissions and security.
- Rollback and recovery.
- Docker/frontend base-image preflight.
- Observability and ops-session semantics.
- Legacy route compatibility.
- Documentation and PRD alignment.

## Required Checks

- `git status --short --branch`
- `git fetch origin`
- `git pull --ff-only origin main`
- `git log -1 --oneline`
- `git diff --check`
- Read-only inspection of relevant docs and scripts.
- Optional read-only runtime checks if runtime is already available:
  - `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`
  - `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status`

If optional runtime checks are skipped, state why.

## Required Evidence

The completion report must include:

- Release-readiness gap matrix.
- Validation plan ordered by priority.
- Explicit distinction between manual-review readiness and production release readiness.
- List of checks that must pass before Lucia can consider a release-readiness review.
- List of items that require Director decision.
- Commands run with exit codes.
- Checks skipped and reasons.

## GitHub Sync Requirements

- Before starting: `cd /Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`; `git status --short --branch`; `git fetch origin`; `git pull --ff-only origin main`.
- Before reporting: `git status --short --branch`; `git log -1 --oneline`.
- Commit and push only the completion report and task tracking update if repository files are changed.

## Completion Report Storage Requirements

- Write the completion report into `TaskAndReport/` using this naming rule:
  `YYYY-MM-DDTHH-MM-SS+0800_P0-Production-Release-Readiness-Gap-Matrix-And-Validation-Plan_REPORT.md`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch, HEAD, current status, next actor, next action, and required output.
- Do not rely on Director chat relay for completion reporting.

## Completion Report Must Include

- Confirmation that work was based on this Lucia task brief.
- Branch and HEAD.
- Files changed.
- Gap matrix and validation plan summary.
- Commands run with exit codes.
- Checks skipped and reasons.
- Runtime or test evidence when applicable.
- Risks, blockers, or residual technical debt.
- GitHub sync status.
- Whether Lucia review, Director decision, or additional validation is required.

## Acceptance Criteria

- Report is stored in `TaskAndReport/`.
- Task tracking row is updated with `Next Actor=Lucia`.
- The report does not claim production release readiness.
- The matrix is actionable enough for Lucia to issue follow-up validation or hardening tasks.
- No destructive production operation was performed.
