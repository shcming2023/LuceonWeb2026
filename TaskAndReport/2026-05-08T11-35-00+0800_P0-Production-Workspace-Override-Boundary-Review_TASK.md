# P0 Production Workspace Override Boundary Review

Task:
P0 Production Workspace Override Boundary Review

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
`TaskAndReport/2026-05-08T11-35-00+0800_P0-Production-Workspace-Override-Boundary-Review_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `TaskAndReport/2026-05-08T11-20-00+0800_P0-Release-Candidate-Standard-Checks-And-Docs-Reconciliation_LUCIA_REVIEW.md`
- `TaskAndReport/2026-05-08T11-35-00+0800_P0-Director-Release-Readiness-Scope-Decisions_LUCIA_REVIEW.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Director approved continuing toward production release-readiness preparation, while keeping production release readiness unclaimed.

Production workspace has been observed behind `origin/main` with a local modified `docker-compose.override.yml`. This is a P0 release boundary and must be understood before further release-candidate naming or production mutation is considered.

## Objective

Perform a read-only review of:

- `/Users/concm/prod_workspace/Luceon2026` branch, HEAD, and divergence from `origin/main`.
- Local `docker-compose.override.yml` modification.
- Whether the override appears to be machine-local runtime configuration, accidental drift, or deployment configuration that should be documented.
- Risks of preserving, normalizing, or replacing the override.
- Recommended next task and required Director approval boundary.

## Non-goals

- Do not modify the production workspace.
- Do not pull, reset, checkout, stash, clean, commit, or edit production files.
- Do not run Docker pull/build/compose commands.
- Do not restart, rebuild, deploy, or rollback.
- Do not mutate DB, MinIO, Docker volumes, tasks, artifacts, secrets, or local overrides.
- Do not claim production release readiness.

## Allowed Operations

In the development workspace:

- Read repository docs and task records.
- Run git status/fetch/pull for the development workspace only.
- Write one completion report under `TaskAndReport/`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md`.

In the production workspace, read-only only:

- `git status --short --branch`
- `git log -1 --oneline`
- `git rev-parse HEAD`
- `git rev-parse origin/main`
- `git diff -- docker-compose.override.yml`
- `git diff --stat`
- Read relevant compose files with `sed` or equivalent read-only commands.

Runtime checks are optional and must be read-only if performed.

## Required Checks

Development workspace:

- `git status --short --branch`
- `git fetch origin`
- `git pull --ff-only origin main`
- `git log -1 --oneline`
- `git diff --check`

Production workspace, read-only:

- `git status --short --branch`
- `git log -1 --oneline`
- `git rev-parse HEAD`
- `git rev-parse origin/main`
- `git diff --stat`
- `git diff -- docker-compose.override.yml`

## Required Evidence

The completion report must include:

- Development workspace HEAD and cleanliness.
- Production workspace HEAD and `origin/main`.
- Exact production branch divergence.
- Exact `docker-compose.override.yml` diff summary and relevant content.
- Classification of the override: local runtime config, accidental drift, deployment config candidate, or unknown.
- Risk analysis for preserve vs document vs normalize vs replace.
- Recommended next action.
- Any required Director decision.
- Commands run with exit codes.
- Checks skipped and reasons.

## Forbidden Changes

- No production file writes.
- No destructive git commands.
- No Docker commands.
- No service operations.
- No data mutations.
- No release-readiness claim.

## Completion Report Requirements

- Write report to `TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Production-Workspace-Override-Boundary-Review_REPORT.md`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch/HEAD, status `已回报待审`, `Next Actor=Lucia`, next action, and required output.
- Commit and push only the report and task tracking update if repository files are changed.

## Acceptance Criteria

- Report is read-only and complete.
- Production override boundary is clear enough for Lucia to recommend preserve/document/normalize/review-next.
- Production release readiness is not claimed.
