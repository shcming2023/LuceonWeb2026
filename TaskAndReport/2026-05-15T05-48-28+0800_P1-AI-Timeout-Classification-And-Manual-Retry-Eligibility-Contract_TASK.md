# P1 AI Timeout Classification And Manual Retry Eligibility Contract

Issued at: 2026-05-15T05:48:28+0800

Task ID: `TASK-20260515-054828-P1-AI-Timeout-Classification-And-Manual-Retry-Eligibility-Contract`

Assigned role: `DevelopmentEngineer`

Expected report: `TaskAndReport/2026-05-15T05-48-28+0800_P1-AI-Timeout-Classification-And-Manual-Retry-Eligibility-Contract_REPORT.md`

## Context

Task 151 pressure monitoring failed: 24 user-submitted pressure tasks produced 20 `review-pending/review`, 3 `failed/ai`, and 1 active MinerU residue task.

Task 152 architecture diagnosis was accepted. The three terminal AI failures are owned by AI metadata / Ollama timeout semantics:

- two failures timed out during first-pass provider generation near the 180000ms strict-mode deadline;
- one failure timed out during JSON repair after a successful first pass;
- strict no-skeleton fallback behaved correctly and must be preserved.

Current source already has provider-level timeout details in `server/services/ai/providers/ollama.mjs`, and raw trace support in `server/services/ai/metadata-worker.mjs`, but terminal failed AI tasks do not yet expose a clear enough phase-aware failure contract for safe operator/Director decisions about later manual retry or re-AI.

## Objective

Implement a narrow code/test-level change that makes AI timeout failures phase-aware and decision-safe without automatically retrying, repairing, reparsing, or re-AIing existing tasks.

The desired result is: when AI metadata fails, the failed job/task/material metadata and raw trace make it clear whether the failure was:

- first-pass provider timeout;
- repair-pass provider timeout;
- repair-retry provider timeout;
- provider unreachable / transport failure;
- JSON parse failure;
- schema validation failure;
- strict no-skeleton fallback block.

## Allowed Files

Primary scope:

- `server/services/ai/metadata-worker.mjs`
- `server/services/ai/providers/ollama.mjs`
- focused tests under `server/tests/`

Optional only if needed for clear operator display:

- `src/app/components/MetadataTab.tsx`
- `src/app/pages/TaskDetailPage.tsx`
- `src/app/utils/taskView.ts`

Do not change public API shape broadly. Add metadata fields compatibly.

## Required Behavior

Preserve strict no-skeleton behavior exactly: skeleton fallback must not be represented as real AI recognition, and strict mode must still fail explicitly.

Add or standardize phase-aware failure metadata so later review can inspect:

- failure kind;
- AI phase, for example `first-pass`, `repair-pass`, `repair-retry-pass`, `strict-skeleton-block`, `json-parse`, `schema-validation`, or `provider-unreachable`;
- timeout kind when present;
- durationMs;
- timeoutMs;
- provider id;
- model;
- base URL without secrets;
- `autoRetryAllowed: false`;
- `manualRetryEligible` or equivalent conservative boolean/status with reason;
- no automatic requeue or retry of failed jobs.

Classification guidance:

- Transport/provider timeout and provider unreachable errors may be marked as potentially manually retryable.
- JSON parse, schema validation, and strict skeleton block must not be treated as automatic retry candidates.
- Repair timeout must be distinguishable from first-pass timeout.
- Existing failed pressure tasks must not be retried, repaired, reparsed, re-AIed, or mutated by this task.

## Forbidden Actions

Do not:

- deploy to production;
- run production uploads or pressure tests;
- mutate production DB, MinIO, Docker volumes, samples, settings, secrets, models, or local config;
- run cleanup, repair, retry, reparse, or re-AI for any existing task;
- add generic automatic retry, infinite retry, or background failed-task auto-recovery;
- weaken strict no-skeleton semantics;
- declare pressure PASS, L3 PASS, release-readiness, production-readiness, or go-live.

## Required Checks

Run the relevant focused checks and record exact commands and exit codes:

- `node --check server/services/ai/metadata-worker.mjs`
- `node --check server/services/ai/providers/ollama.mjs`
- focused new/updated smoke tests for AI failure classification and strict no-skeleton behavior
- `git diff --check`
- `npx pnpm@10.4.1 exec tsc --noEmit` if any TypeScript/frontend file is changed

If a check cannot be run, state the exact reason.

## Required Report

Write the expected report with:

- branch and HEAD;
- files changed;
- implementation summary;
- exact failure metadata contract added or standardized;
- commands run and exit codes;
- skipped checks and reasons;
- evidence that no existing task was retried/repaired/reparsed/re-AIed;
- risks and residual debt;
- whether Director review is required.

Then update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查`
- Next Actor: `Director`
- Report / Review: link to your report

