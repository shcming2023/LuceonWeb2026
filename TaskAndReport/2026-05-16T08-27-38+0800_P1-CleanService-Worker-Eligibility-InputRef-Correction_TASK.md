# Task: P1 CleanService Worker Eligibility InputRef Correction

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
TaskAndReport/2026-05-16T08-27-38+0800_P1-CleanService-Worker-Eligibility-InputRef-Correction_TASK.md

Expected report:
TaskAndReport/2026-05-16T08-27-38+0800_P1-CleanService-Worker-Eligibility-InputRef-Correction_REPORT.md

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-16T08-15-14+0800_P1-CleanService-Disabled-Worker-Shell-And-Metadata-Persistence_TASK.md`
- `TaskAndReport/2026-05-16T08-15-14+0800_P1-CleanService-Disabled-Worker-Shell-And-Metadata-Persistence_REPORT.md`
- `TaskAndReport/2026-05-16T08-27-38+0800_P1-CleanService-Disabled-Worker-Shell-And-Metadata-Persistence_DIRECTOR_REVIEW.md`

## Background

Director returned Task 201 because the worker shell can mark a task eligible with only:

```json
{ "mineruStatus": "completed" }
```

and then build a CleanService input whose `source.object` is missing.

This is a contract bug in the mock/worker foundation. It does not affect production today because the worker is not wired into runtime startup, but it must be corrected before any next CleanService orchestration slice.

## Objective

Correct CleanService worker eligibility and job-request construction so a task cannot be dispatched unless it has concrete input ObjectRef evidence.

## Required Fix

Implement the smallest scoped correction:

1. `isCleanServiceTaskEligible()` must require one of:
   - non-empty `metadata.artifactManifestObjectName`;
   - non-empty `metadata.markdownObjectName`;
   - non-empty `metadata.parsedPrefix` plus `parsedFilesCount > 0`.
2. `metadata.mineruStatus = "completed"` alone is not sufficient.
3. `buildCleanServiceJobRequest()` must fail explicitly with a precise error if called without valid input evidence. It must not emit `source.object = undefined`.
4. Existing valid cases must continue to work:
   - artifact manifest preferred over markdown;
   - markdown preferred over parsed prefix;
   - parsed prefix accepted only when non-empty and file count is positive.
5. Update focused smoke coverage so the Director-reproduced bug is a regression test.
6. Preserve disabled no-op behavior and one-at-a-time mock dispatch behavior.

## Allowed Files

DevelopmentEngineer may modify only:

- `server/services/cleanservice/cleanservice-worker.mjs`
- `server/tests/cleanservice-worker-shell-smoke.mjs`
- optionally a new focused `server/tests/cleanservice-worker-eligibility-smoke.mjs` if clearer
- `TaskAndReport/2026-05-16T08-27-38+0800_P1-CleanService-Worker-Eligibility-InputRef-Correction_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Do not edit unrelated CleanService files unless absolutely necessary; if necessary, explain why in the report.

## Non-Goals / Forbidden Actions

- Do not wire the worker into runtime startup.
- Do not dispatch to real Mineru2Table.
- Do not call production services.
- Do not mutate production, Docker, DB, MinIO, MinerU, Ollama, models, secrets, configs, samples, or external repositories.
- Do not run submit-probe, upload, pressure/batch/soak validation, retry, reparse, re-AI, cleanup, repair, reset, or task-state reconciliation.
- Do not migrate, hide, delete, or backfill legacy assets.
- Do not globally replace material IDs with hash IDs.
- Do not change public runtime API or current task top-level status unions.
- Do not claim production acceptance, production readiness, release readiness, L3, pressure PASS, production上线, or go-live.

## Required Checks

Run and record exit codes:

- `git status --short --branch`
- `git diff --check`
- `node --check` for changed `.mjs` files
- `node server/tests/cleanservice-foundation-smoke.mjs`
- `node server/tests/cleanservice-worker-shell-smoke.mjs`
- any new focused eligibility smoke, if added
- `npx pnpm@10.4.1 exec tsc --noEmit`

Run `npx pnpm@10.4.1 run build` only if any frontend, TypeScript app, shared type, or build-sensitive file is touched. If skipped, record the exact reason.

Do not run production checks for this task.

## Required Evidence In Report

The report must include:

- confirmation that this Director correction task was followed;
- branch and HEAD;
- files changed;
- implementation summary;
- evidence that `mineruStatus=completed` alone is no longer eligible;
- evidence that invalid job-request construction fails explicitly;
- evidence that valid artifact manifest / markdown / parsed-prefix input cases still work;
- commands run with exit codes;
- skipped checks and exact reasons;
- residual risks;
- whether Director review is required.

## Completion

Write:

`TaskAndReport/2026-05-16T08-27-38+0800_P1-CleanService-Worker-Eligibility-InputRef-Correction_REPORT.md`

Update this task row in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Branch / HEAD populated;
- Notes summarize correction, checks, and residual risks.

## GitHub Sync Requirements

- Before starting: run `git status --short --branch`.
- Work on current `main` unless local policy or branch state requires a scoped branch.
- Do not overwrite unrelated worktree changes.
- If repository files are changed, commit and push to GitHub `main` after checks pass.

## Acceptance Criteria

Director can accept the correction if:

- the reproduced bug is fixed and covered by tests;
- valid input evidence cases still work;
- no runtime wiring or real external service dispatch was added;
- required checks pass;
- no forbidden production/data/model/sample/release action occurred.

