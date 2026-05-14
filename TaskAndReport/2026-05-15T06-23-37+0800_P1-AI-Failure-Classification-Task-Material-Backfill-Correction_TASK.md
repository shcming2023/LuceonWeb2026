# P1 AI Failure Classification Task Material Backfill Correction

Issued at: 2026-05-15T06:23:37+0800

Task ID: `TASK-20260515-062337-P1-AI-Failure-Classification-Task-Material-Backfill-Correction`

Assigned role: `DevelopmentEngineer`

Expected report: `TaskAndReport/2026-05-15T06-23-37+0800_P1-AI-Failure-Classification-Task-Material-Backfill-Correction_REPORT.md`

## Context

Task 154 added the right core AI failure classification direction, but Director review found an integration gap:

- AI job metadata receives the classification.
- Task events receive the classification.
- Material and ParseTask metadata do not yet receive the classification in failed AI terminal states, because `server/upload-server.mjs` `onComplete` currently merges `update.result` only.

The task objective requires failed AI job/task/material metadata to be decision-safe.

## Objective

Extend the Task 154 implementation so failed AI terminal state propagation includes the AI failure classification metadata in Material and ParseTask metadata, without changing strict no-skeleton semantics and without retrying or mutating existing production tasks.

## Allowed Files

You may touch only:

- `server/services/ai/metadata-worker.mjs`
- `server/services/ai/providers/ollama.mjs`
- `server/upload-server.mjs`
- focused tests under `server/tests/`
- your report
- `TaskAndReport/TASK_TRACKING_LIST.md`

Do not touch frontend files unless Director explicitly reassigns UI display work later.

## Required Behavior

Preserve Task 154 behavior:

- phase-aware AI failure classification;
- `autoRetryAllowed: false`;
- conservative manual-only retry eligibility;
- strict no-skeleton still fails explicitly;
- no automatic retry/requeue.

Add failed-state backfill behavior:

- when AI job terminal state is `failed`, Material metadata should include the AI failure classification fields needed for operator/Director review;
- ParseTask metadata should also include equivalent classification fields;
- existing `update.result` success/review-pending behavior must remain unchanged;
- no existing production failed task may be retried, reparsed, re-AIed, repaired, migrated, or mutated by this task.

## Required Checks

Run and record exact commands and exit codes:

- `node --check server/services/ai/metadata-worker.mjs`
- `node --check server/services/ai/providers/ollama.mjs`
- `node --check server/upload-server.mjs`
- focused AI classification smoke test
- focused repair hardening smoke test
- a focused backfill smoke test proving failed AI classification reaches material/task metadata
- `git diff --check`

If any check cannot be run, state the exact reason.

## Forbidden Actions

Do not:

- deploy to production;
- upload files or run pressure/batch/soak validation;
- cleanup, repair, retry, reparse, or re-AI existing tasks;
- mutate production DB, MinIO, Docker volumes, samples, settings, secrets, models, or local config;
- add automatic retry/requeue;
- weaken strict no-skeleton fallback;
- declare pressure PASS, L3 PASS, release-readiness, production-readiness, or go-live.

## Required Report

Write the expected report with:

- branch and HEAD;
- files changed;
- correction summary;
- exact metadata fields now written to AI job, Material, and ParseTask;
- commands run and exit codes;
- skipped checks and reasons;
- evidence that no existing production task was retried/repaired/reparsed/re-AIed or migrated;
- risks/residual debt;
- whether Director review is required.

Then update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查`
- Next Actor: `Director`
- Report / Review: link to your report

