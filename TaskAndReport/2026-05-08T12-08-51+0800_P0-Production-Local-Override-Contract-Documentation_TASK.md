# P0 Production Local Override Contract Documentation

Task:
P0 Production Local Override Contract Documentation

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
`TaskAndReport/2026-05-08T12-08-51+0800_P0-Production-Local-Override-Contract-Documentation_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/deploy/DEPLOY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/2026-05-08T11-56-11+0800_P0-Production-Workspace-Override-Boundary-Review_REPORT.md`
- `TaskAndReport/2026-05-08T12-08-51+0800_P0-Production-Workspace-Override-Boundary-Review_LUCIA_REVIEW.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Lucode's read-only production override review was accepted by Lucia. The local production `docker-compose.override.yml` appears to preserve required strict AI/model semantics and expose the MinIO console on `19001:9001`.

This boundary must be documented before release-candidate naming or any production sync/deploy task is considered.

## Objective

Document the production-local override contract in repository documentation.

The documentation must state:

- The production-local override is not a release-readiness claim.
- `DISABLE_AI_SKELETON_FALLBACK=true` is required for strict Phase 1 AI semantics.
- `OLLAMA_TIER2_MODEL=qwen3.5:9b` is required for the current Standard model.
- MinIO console `19001:9001` is a local-admin exposure boundary and must be explicitly accepted or changed before production release readiness.
- The production workspace can remain locally configured, but release-candidate naming requires exact HEAD and override boundary confirmation.
- Production sync, rebuild, restart, rollback, Docker pull/build/compose, and override mutation still require separate Director approval.

## Non-goals

- Do not edit the production workspace.
- Do not edit the production `docker-compose.override.yml`.
- Do not run Docker commands.
- Do not restart, rebuild, deploy, or rollback.
- Do not mutate DB, MinIO, Docker volumes, tasks, artifacts, secrets, or local overrides.
- Do not claim production release readiness.
- Do not implement runtime changes.

## Allowed Files

- `docs/deploy/DEPLOY.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- One `TaskAndReport/*_REPORT.md`

Do not edit other files unless the report explains why and the change is strictly documentation-only.

## Required Checks

- `git status --short --branch`
- `git fetch origin`
- `git pull --ff-only origin main`
- `git log -1 --oneline`
- `git diff --check`
- Read the accepted task 22 report and Lucia review.
- Inspect `docs/deploy/DEPLOY.md` for the best insertion point.

No runtime checks are required.

## Required Evidence

The completion report must include:

- Files changed.
- Summary of documentation changes.
- Confirmation that production runtime was not touched.
- Commands run with exit codes.
- Checks skipped and reasons.
- Remaining Director decisions.

## Forbidden Changes

- No production workspace writes.
- No Docker commands.
- No runtime mutations.
- No release-readiness claim.
- No broad documentation rewrite.

## Completion Report Requirements

- Write report to `TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Production-Local-Override-Contract-Documentation_REPORT.md`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch/HEAD, status `已回报待审`, `Next Actor=Lucia`, next action, and required output.
- Commit and push repository documentation changes and report updates to GitHub `main`.

## Acceptance Criteria

- Production-local override contract is documented clearly.
- No runtime or production workspace mutation occurred.
- Production release readiness remains unclaimed.
