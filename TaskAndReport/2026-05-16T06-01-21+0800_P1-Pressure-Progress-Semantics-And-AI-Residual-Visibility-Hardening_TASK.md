# Task: P1 Pressure Progress Semantics And AI Residual Visibility Hardening

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
TaskAndReport/2026-05-16T06-01-21+0800_P1-Pressure-Progress-Semantics-And-AI-Residual-Visibility-Hardening_TASK.md

Expected report:
TaskAndReport/2026-05-16T06-01-21+0800_P1-Pressure-Progress-Semantics-And-AI-Residual-Visibility-Hardening_REPORT.md

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/TEST_MATRIX.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-15T20-29-08+0800_P1-Manual-Clean-24-PDF-Pressure-Monitoring_TASK.md`
- `TaskAndReport/2026-05-15T20-29-08+0800_P1-Manual-Clean-24-PDF-Pressure-Monitoring_REPORT.md`
- `TaskAndReport/2026-05-16T06-01-21+0800_P1-Manual-Clean-24-PDF-Pressure-Monitoring_DIRECTOR_REVIEW.md`

## Background

The clean 24-PDF pressure run reached terminal observed state: 23 `review-pending/review`, 1 `failed/ai`, and all 24 materials completed MinerU. Director accepted the monitoring evidence with residuals.

The run also confirmed the user's concern: during long-running MinerU work, page/active-task/dependency-health wording can lag or conflict with direct MinerU API and MinerU log progress. The system must help an operator see that MinerU is still moving instead of encouraging premature failure judgment.

## Objective

Harden operator-facing progress semantics and residual AI-failure visibility for pressure/long-running parse runs.

The implementation should make it clearer when:

- MinerU is still genuinely progressing based on direct API/log evidence;
- UI/backend state is lagging but not terminally failed;
- dependency-health no-submit timeout happens during active heavy processing and should be treated as a warning/latency risk, not immediate task failure;
- an AI-stage failure is isolated after MinerU completion and is a manual retry/review candidate under strict no-skeleton-fallback rules.

## Suggested Investigation Targets

Use the current codebase to find exact files. Likely areas include:

- upload server ops endpoints for active-task / dependency-health / MinerU log-channel ownership;
- task/material aggregation or pressure-result semantics;
- `/cms/tasks` page and task-detail rendering;
- AI failure classification and task/material backfill display semantics;
- tests around MinerU runtime progress truth, pressure result semantics, dependency-health, and AI failure classification.

Do not assume these paths are exhaustive; inspect before editing.

## Required Behavior Direction

Preserve strict no-silent-fallback semantics.

Do not turn AI failure into success. Do not auto-retry or silently hide the failure.

Improve display/API semantics so that an operator can distinguish:

- `MinerU still processing and evidence is moving`;
- `backend/UI stale or lagging but direct/log evidence shows progress`;
- `terminal MinerU failure`;
- `terminal AI failure after successful MinerU parse`;
- `manual retry/review candidate`.

If the current code already exposes some of this, improve the contract or UI wording only where the Task 190 evidence shows ambiguity.

## Non-Goals

- Do not run a pressure test.
- Do not upload files.
- Do not mutate existing tasks/materials/AI jobs.
- Do not retry/reparse/re-AI/cancel/repair/reset anything.
- Do not run submit-probe unless a test uses mocked/local-only code without production side effects.
- Do not deploy to production.
- Do not restart/rebuild/redeploy services.
- Do not mutate DB, MinIO, Docker volumes, runtime config, secrets, models, or sample files.
- Do not edit PRD truth, role contracts, `PROJECT_STATE`, or `HANDOFF`.
- Do not claim pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

## Allowed Files

- Source files needed for the scoped implementation.
- Focused tests.
- Task completion report under `TaskAndReport/`.
- `TaskAndReport/TASK_TRACKING_LIST.md`.

If you believe docs need later updates, record the recommendation in the report rather than broadening this task.

## Required Checks

Run the most relevant focused checks, including any tests you update or add.

At minimum:

- `git status --short --branch`
- `git diff --check`
- syntax checks for changed server files, if any;
- focused MinerU progress/pressure/AI failure tests relevant to changed behavior;
- `npx pnpm@10.4.1 exec tsc --noEmit`

Run `npx pnpm@10.4.1 run build` if frontend files are changed.

If a check is skipped, report the exact reason.

## Required Evidence

The report must include:

- confirmation that work was based on this Director task brief;
- branch and HEAD;
- files changed;
- implementation summary;
- before/after behavior summary for operator-visible semantics;
- tests/checks run with exit codes;
- skipped checks and reasons;
- risks, blockers, and residual debt;
- GitHub sync status;
- whether Director review is required.

## GitHub Sync Requirements

- Start with `git status --short --branch`.
- Do not overwrite unrelated dirty changes.
- Commit and push repository changes to GitHub `main` unless blocked by unrelated dirty work. If blocked, write the report and explain.

## Acceptance Criteria

Director can accept the task if:

- long-running MinerU progress is represented with clearer multi-source semantics;
- UI/backend semantics no longer encourage premature failure judgment when direct MinerU/log evidence is moving;
- AI residual failure remains explicit and visible as AI-stage/manual retry-review candidate;
- strict no-skeleton-fallback semantics are preserved;
- focused tests cover the changed behavior;
- no production/runtime/data mutation occurs.

