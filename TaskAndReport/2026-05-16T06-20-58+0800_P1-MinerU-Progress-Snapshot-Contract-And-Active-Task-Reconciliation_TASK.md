# Task: P1 MinerU Progress Snapshot Contract And Active-Task Reconciliation

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
TaskAndReport/2026-05-16T06-20-58+0800_P1-MinerU-Progress-Snapshot-Contract-And-Active-Task-Reconciliation_TASK.md

Expected report:
TaskAndReport/2026-05-16T06-20-58+0800_P1-MinerU-Progress-Snapshot-Contract-And-Active-Task-Reconciliation_REPORT.md

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
- `TaskAndReport/2026-05-15T20-29-08+0800_P1-Manual-Clean-24-PDF-Pressure-Monitoring_REPORT.md`
- `TaskAndReport/2026-05-16T06-01-21+0800_P1-Manual-Clean-24-PDF-Pressure-Monitoring_DIRECTOR_REVIEW.md`
- `TaskAndReport/2026-05-16T06-07-44+0800_P1-Pressure-Progress-Semantics-Root-Cause-Diagnosis_REPORT.md`
- `TaskAndReport/2026-05-16T06-20-58+0800_P1-Pressure-Progress-Semantics-Root-Cause-Diagnosis_DIRECTOR_REVIEW.md`

## Background

Task 192 root-caused the recurring progress-semantics lag. The accepted diagnosis is that UI/backend surfaces flatten multiple truth sources into one ambiguous status line:

- DB task state;
- direct MinerU status;
- MinerU log observation freshness;
- dependency-health readiness;
- material/AI phase.

The next step is to implement a backend progress contract and active-task reconciliation semantics before broad UI copy changes.

## Objective

Implement a normalized backend progress snapshot model for MinerU/AI task progress and active-task diagnostics.

The implementation should make downstream UI and operators able to distinguish:

- direct MinerU still processing;
- DB task state lagging behind direct MinerU truth;
- log observation stale because runtime is terminal/idle;
- dependency-health readiness probe timeout versus per-task progress;
- terminal MinerU failure;
- terminal AI failure after successful MinerU parse;
- manual retry/review candidates under strict no-skeleton-fallback policy.

## Required Behavior

Create or extend a structured `progressSnapshot` contract in backend task/diagnostic payloads. Exact field names may be adjusted to fit existing code, but the model must carry the following concepts:

- `phase`: parse / result-ingestion / ai / review / terminal / unknown;
- `source`: db / direct-mineru / log / ai / material / mixed;
- `sourcePriority`: which source is authoritative for the current message;
- `observedAt` or equivalent timestamp;
- `freshness`: fresh / stale / idle / terminal / unknown;
- `confidence`: high / medium / low;
- `lagKind`: none / db-behind-direct-mineru / log-stale-after-terminal / dependency-health-readiness-only / ai-after-parse / unknown;
- `directMineruStatus` when known;
- `dbState` / `dbStage`;
- `logState`;
- `aiState`;
- `operatorMessage`.

Active-task diagnostics must make DB-derived versus direct-checked status clear. For running MinerU candidates with a known MinerU task id, either:

- query direct MinerU status in the operator diagnostics path and classify direct-completed/DB-running as `result-ingestion-lag`; or
- expose an explicitly named DB-derived mode and add a direct-checked mode that operators can reliably request.

Terminal/idle log semantics must avoid implying "MinerU still processing" when task/runtime is terminal or idle.

Metadata-only task progress events must not log `Status changed to undefined`; use an explicit metadata/progress event message instead.

## Non-Goals

- Do not run a pressure test.
- Do not upload files.
- Do not mutate existing tasks/materials/AI jobs.
- Do not retry/reparse/re-AI/cancel/repair/reset anything.
- Do not run submit-probe against production.
- Do not deploy to production.
- Do not restart/rebuild/redeploy services.
- Do not mutate DB, MinIO, Docker volumes, runtime config, secrets, models, or sample files.
- Do not perform broad UI redesign or large copy rewrites. Minimal UI/type adjustments are allowed only if required to compile against the backend contract.
- Do not edit PRD truth, role contracts, `PROJECT_STATE`, or `HANDOFF`.
- Do not claim pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

## Allowed Files

- Backend source files needed for progress snapshot and diagnostics.
- Focused frontend type/display utilities only if required for contract compatibility.
- Focused tests/smokes.
- Task report under `TaskAndReport/`.
- `TaskAndReport/TASK_TRACKING_LIST.md`.

## Suggested Investigation Targets

Use `rg` before editing. Likely areas:

- `server/upload-server.mjs`
- `server/lib/ops-mineru-diagnostics.mjs`
- `server/lib/ops-mineru-log-parser.mjs`
- `server/services/mineru/local-adapter.mjs`
- `server/services/queue/task-worker.mjs`
- `src/app/utils/taskView.ts`
- focused tests under `server/tests/`

## Required Checks

Run relevant focused checks. At minimum:

- `git status --short --branch`
- `git diff --check`
- syntax checks for changed server files, if any;
- focused smoke tests covering:
  - direct MinerU completed while DB still running;
  - terminal/idle stale log observation;
  - dependency-health as readiness, not per-task progress;
  - AI failure after MinerU completion classified separately;
  - no `Status changed to undefined` event message.
- `npx pnpm@10.4.1 exec tsc --noEmit`

Run `npx pnpm@10.4.1 run build` if frontend files are changed.

If a check is skipped, report the exact reason.

## Required Report

Write:

`TaskAndReport/2026-05-16T06-20-58+0800_P1-MinerU-Progress-Snapshot-Contract-And-Active-Task-Reconciliation_REPORT.md`

The report must include:

- confirmation that work was based on this Director task brief;
- branch and HEAD;
- files changed;
- implementation summary;
- progress snapshot contract summary;
- before/after semantics for the root-cause scenarios;
- commands/checks run with exit codes;
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

- the backend exposes clearer structured progress truth instead of a flattened status line;
- active-task diagnostics can distinguish DB lag from direct MinerU truth;
- terminal/idle stale logs do not imply active processing;
- AI residual failure remains explicit and separate from MinerU parsing;
- event logs no longer write `Status changed to undefined`;
- focused tests cover the changed behavior;
- strict no-skeleton-fallback and explicit failure semantics remain intact;
- no production/runtime/data mutation occurs.

