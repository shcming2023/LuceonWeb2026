# P1 AI Timeout Classification And Manual Retry Eligibility Contract - Director Review

Review time: 2026-05-15T06:23:37+0800

Task: `TaskAndReport/2026-05-15T05-48-28+0800_P1-AI-Timeout-Classification-And-Manual-Retry-Eligibility-Contract_TASK.md`

Report reviewed: `TaskAndReport/2026-05-15T05-48-28+0800_P1-AI-Timeout-Classification-And-Manual-Retry-Eligibility-Contract_REPORT.md`

Result: `NEEDS_CORRECTION_TASK_AND_MATERIAL_BACKFILL_GAP`

## Director Judgment

The DevelopmentEngineer implementation is directionally correct and the focused checks passed, but I am not accepting it for integration yet.

The task objective required failed AI job/task/material metadata to be decision-safe. The submitted implementation records classification metadata on the AI job update and task event payload, but the production completion callback in `server/upload-server.mjs` does not currently propagate `update.metadata` or `update.aiFailureClassification` into Material or ParseTask metadata on failed AI terminal states. As a result, the operator-visible task/material surfaces can still miss the new classification contract.

This is a correction requirement, not a rejection of the core classification idea.

## Evidence Checked

Director re-ran:

- `node --check server/services/ai/metadata-worker.mjs` -> passed
- `node --check server/services/ai/providers/ollama.mjs` -> passed
- `node --check server/tests/ai-failure-classification-smoke.mjs` -> passed
- `node server/tests/ai-failure-classification-smoke.mjs` -> passed
- `node --check server/tests/ai-metadata-repair-hardening-smoke.mjs` -> passed
- `node server/tests/ai-metadata-repair-hardening-smoke.mjs` -> passed
- `git diff --check` -> passed

Director source review found:

- `buildAiFailureClassification()` classifies first-pass, repair-pass, repair-retry, provider-unreachable, JSON parse, schema validation, and strict no-skeleton block cases.
- `autoRetryAllowed` remains false.
- Strict no-skeleton remains enforced.
- No automatic retry/requeue was added.
- `server/upload-server.mjs` `onComplete` material/task backfill still merges only `update.result` into metadata and does not carry failed-state `update.metadata` / `update.aiFailureClassification`.

## Required Correction

Director issued:

- `TASK-20260515-062337-P1-AI-Failure-Classification-Task-Material-Backfill-Correction`

The correction should preserve the current classification implementation, then add failed-state propagation to Material and ParseTask metadata, with focused tests.

## Boundaries

Not authorized:

- production deployment;
- upload, pressure/batch/soak testing;
- cleanup, repair, retry, reparse, or re-AI of existing tasks;
- destructive DB/MinIO/Docker volume/data mutation;
- settings, secrets, config, model, or sample mutation;
- automatic retry/requeue or skeleton fallback weakening;
- pressure PASS, L3 PASS, release-readiness, production-readiness, or go-live.

