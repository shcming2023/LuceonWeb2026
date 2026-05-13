# Task: P0 Post-Smoke Production Deployment And Non-Destructive Runtime Validation

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
TaskAndReport/2026-05-13T12-18-44+0800_P0-Post-Smoke-Production-Deployment-And-Non-Destructive-Runtime-Validation_TASK.md

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
- TaskAndReport/2026-05-13T11-20-49+0800_P0-Post-Smoke-Production-Validation-Authorization_DECISION.md

## Background

Task 77 restored task-page MinerU progress semantics at code level. Task 78 restored Ollama keep-alive and cold/warm dependency-health semantics at code level. Task 79 cleared the current-main AI metadata smoke timeout assertion drift at code/test level.

Task 80 asked the user whether to authorize scoped production deployment and non-destructive runtime validation. The user approved Director's recommendation for Option A on 2026-05-13.

This task applies that authorization. It is not a release-readiness task.

## Current Known Facts

- Production release readiness remains unclaimed.
- The bounded 24-PDF pressure restart remains inconclusive and is not pressure PASS.
- Task 60 was closed by Director as blocked/stale release-readiness evidence and superseded by the current Task 80/81 validation path.
- Task 79 accepted repository-level checks: diff-check, provider syntax check, AI metadata real-sample smoke, dependency-health smoke 65/0, TypeScript, and build.
- The current workspace has existing unrelated uncommitted changes. Do not overwrite, revert, or tidy unrelated work.
- Production deployment path is `/Users/concm/prod_workspace/Luceon2026`.

## PRD / Contract / Architecture / Validation Reference

- Current Phase 1 mainline: upload -> local MinerU -> MinIO -> Ollama `qwen3.5:9b` -> AI metadata -> operator review.
- Strict no-skeleton behavior must remain enforced.
- Production runtime ownership is governed by `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`.
- Runtime env truth must preserve:
  - `LOCAL_MINERU_ENDPOINT=http://host.docker.internal:8083`
  - `OLLAMA_API_URL=http://host.docker.internal:11434`
  - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
  - `DISABLE_AI_SKELETON_FALLBACK=true`
  - `ALLOW_AI_SKELETON_FALLBACK=false`

## Objective

Apply the accepted Task 77/78/79 code path to the production deployment with the minimum necessary deployment mechanics, then collect non-destructive runtime evidence that production surfaces are healthy.

Required evidence must cover:

- production deployed HEAD;
- production override/env boundary summary;
- upload-server health;
- dependency-health with `mineruSubmitProbe=true`;
- `/ops/mineru/admission-circuit`;
- `/ops/mineru/active-task`;
- Ollama residency or readiness evidence, such as `/api/ps`;
- task/API evidence that MinerU progress semantics are available when current runtime data supports it;
- explicit list of what was not validated.

## Non-Goals

- Do not create a validation upload.
- Do not run a pressure test or pressure retry.
- Do not repair, retry, clean up, or mutate failed historical tasks.
- Do not claim production release readiness, L3, pressure PASS, or full acceptance.
- Do not broaden the task into architecture redesign, product-scope changes, or long-run validation.

## Allowed Files, Modules, Or Operations

Development workspace:

- Read repository docs, task records, source, tests, and git state.
- Update only the completion report and the task tracking row required by this task.

Production deployment path:

- Inspect git status/HEAD.
- Inspect production override/env boundary.
- Inspect Docker Compose state.
- Run read-only runtime status and health commands.
- If no active parse/AI work is running, perform the minimum necessary production apply/build/restart for the accepted code path.
- Prefer limiting restart/rebuild to the smallest service set necessary, normally upload-server/front-end related services only.

Suggested read-only commands include:

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
- Do not change PRD truth, role contracts, release judgments, or unrelated project docs.
- Do not claim production release readiness, L3, pressure PASS, or full acceptance.

If active parse/AI work is present before deployment mechanics, stop before any restart/rebuild and write a blocked report with exact active-work evidence.

## Suggested Direction

1. In the development workspace, confirm the assigned task and current git state.
2. In the production deployment path, inspect current HEAD, dirty state, active work, service state, and runtime ownership status.
3. If GitHub synchronization is required to make production match accepted code, stop and report the required sync to Director. Non-Director roles must not perform GitHub fetch/pull/push in this workflow unless a later Director task explicitly authorizes it.
4. If production can be applied without GitHub sync and without disturbing active work, perform the minimum necessary deployment mechanics.
5. Run the required non-destructive runtime checks.
6. Report precise evidence and boundaries.

## Required Checks

At minimum:

- `git status --short --branch` in development workspace.
- `git status --short --branch` and `git log -1 --oneline` in production deployment path.
- Production runtime ownership/status inspection.
- Upload health.
- Dependency health with MinerU submit probe.
- Admission circuit endpoint.
- Active-task endpoint.
- Ollama residency/readiness endpoint.
- If any deployment/build/restart command is run, record exact command and exit code.

## Required Evidence

The report must include:

- production deployed HEAD and whether it includes the accepted code path;
- whether GitHub sync was required or skipped;
- exact deployment commands, if any;
- production override/env boundary summary;
- Docker service state summary;
- health endpoint outputs summarized with raw status details;
- admission circuit state;
- active parse/AI work state;
- Ollama residency/readiness state;
- whether task-page MinerU progress semantics were observable from current runtime data;
- what was not validated and why;
- risks, blockers, and residual debt.

## GitHub Sync Requirements

- Do not perform GitHub fetch, pull, push, or branch publication from this role task.
- If production deployment requires GitHub synchronization, report `BLOCKED_NEEDS_DIRECTOR_GITHUB_SYNC` with exact reason, current production HEAD, required target HEAD, and current dirty state.
- If only local report/tracking files are changed, leave them local for Director review and later Director-owned synchronization.

## Completion Report Storage Requirements

- Write the completion report into `TaskAndReport/` using this naming rule:
  `2026-05-13T12-18-44+0800_P0-Post-Smoke-Production-Deployment-And-Non-Destructive-Runtime-Validation_REPORT.md`
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch, HEAD, current status, next actor, next action, and required output.
- Do not rely on chat relay for completion reporting.

## Completion Report Must Include

- confirmation that work was based on this Director task brief;
- assigned role;
- branch and HEAD for development workspace and production deployment path;
- files changed;
- deployment/validation summary;
- commands run with exit codes;
- checks skipped and reasons;
- runtime evidence;
- risks, blockers, or residual technical debt;
- GitHub sync status;
- whether Director review or user decision is required.

## Acceptance Criteria

- Production deployment either reaches the accepted code path with minimum necessary non-destructive deployment mechanics, or the report clearly blocks with exact reason.
- Required runtime surfaces are checked and reported.
- No validation upload, pressure test, failed-task repair, destructive mutation, model operation, broad restart/rollback, or release-readiness claim occurs.
- Tracking list is updated to `已回报待 Director 审查` with `Next Actor=Director` after the report is written.
