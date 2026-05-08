# P0 MinIO Console Local-Only Binding Change Plan

Task:
P0 MinIO Console Local-Only Binding Change Plan

Task ID:
`TASK-20260508-123816-P0-MinIO-Console-Local-Only-Binding-Change-Plan`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T12:38:16+0800

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T12-38-16+0800_P0-MinIO-Console-Local-Only-Binding-Change-Plan_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/deploy/DEPLOY.md`
- `TaskAndReport/2026-05-08T12-30-45+0800_P0-Production-Override-Release-Boundary-Decision_DECISION.md`
- `TaskAndReport/2026-05-08T12-38-16+0800_P0-Production-Override-Release-Boundary-Decision_LUCIA_REVIEW.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Director decided that MinIO console exposure must be narrowed to local-only binding before any release-candidate naming. Current production-local override exposure `19001:9001` must not be accepted as-is for release-candidate naming, but complete removal is not required at this stage.

Strict AI/model configuration remains in production-local `docker-compose.override.yml` for now.

This task is non-destructive planning only.

## Objective

Produce a concrete, non-destructive change plan for narrowing MinIO console exposure to local-only binding in the production-local override.

The plan must include:

- The exact current production-local override line or compose port mapping that would need to change.
- The proposed local-only binding form, for example `127.0.0.1:19001:9001`, if supported by the current compose file structure.
- A validation plan confirming MinIO console remains reachable from the local host and is not exposed on non-local interfaces.
- A rollback plan restoring the current boundary if needed.
- A risk assessment for local manual review and operational access.
- A statement that strict AI/model settings remain unchanged.

## Non-goals

- Do not edit the production workspace.
- Do not edit production `docker-compose.override.yml`.
- Do not run Docker commands.
- Do not restart, rebuild, deploy, rollback, or sync production.
- Do not mutate DB, MinIO, Docker volumes, tasks, artifacts, secrets, or local runtime data.
- Do not claim production release readiness.
- Do not implement runtime changes.

## Allowed Files

- One `TaskAndReport/*_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Do not edit docs or code unless blocked and the report explains why. The expected output is a plan report, not implementation.

## Required Checks

- `git status --short --branch`
- `git fetch origin`
- If local `main` is behind `origin/main` and the worktree is clean, `git pull --ff-only origin main`
- Read the task 24 decision and Lucia review.
- Read `docs/deploy/DEPLOY.md`.
- Read only the production-local `docker-compose.override.yml` needed to identify the current MinIO console mapping.

No runtime checks are required. Docker commands are forbidden.

## Required Evidence

The report must include:

- Files read.
- Current observed MinIO console mapping.
- Proposed local-only mapping.
- Validation plan.
- Rollback plan.
- Commands run with exit codes.
- Confirmation that no production runtime mutation occurred.
- Remaining approval required before implementation.

## Completion Report Requirements

- Write report to `TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-MinIO-Console-Local-Only-Binding-Change-Plan_REPORT.md`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch/HEAD, status `已回报待审`, `Next Actor=Lucia`, next action, and required output.
- Commit and push report/task-list updates to GitHub `main`.

## Acceptance Criteria

- The plan identifies the precise proposed local-only binding.
- The plan includes validation and rollback steps.
- No production workspace mutation or Docker command occurred.
- Production release readiness remains unclaimed.
