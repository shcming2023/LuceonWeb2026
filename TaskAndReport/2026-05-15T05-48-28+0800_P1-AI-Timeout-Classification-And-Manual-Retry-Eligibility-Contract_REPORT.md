# DevelopmentEngineer Report: P1 AI Timeout Classification And Manual Retry Eligibility Contract

## Based On

- Director task brief: `TaskAndReport/2026-05-15T05-48-28+0800_P1-AI-Timeout-Classification-And-Manual-Retry-Eligibility-Contract_TASK.md`
- Upstream accepted diagnosis: `TaskAndReport/2026-05-15T05-38-16+0800_P1-Pressure-Test-AI-Timeout-Failure-Architecture-Diagnosis_REPORT.md`
- Director review: `TaskAndReport/2026-05-15T05-48-28+0800_P1-Pressure-Test-AI-Timeout-Failure-Architecture-Diagnosis_DIRECTOR_REVIEW.md`

## Branch / HEAD

- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- HEAD: `005ca96`
- Initial workspace status command: `git status --short --branch` exited 0 and showed a shared dirty worktree with many unrelated role-thread changes. I did not revert or sync them.

## Files Changed

- `server/services/ai/metadata-worker.mjs`
- `server/services/ai/providers/ollama.mjs`
- `server/tests/ai-failure-classification-smoke.mjs`
- `server/tests/ai-metadata-repair-hardening-smoke.mjs`
- `TaskAndReport/2026-05-15T05-48-28+0800_P1-AI-Timeout-Classification-And-Manual-Retry-Eligibility-Contract_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Implementation Summary

- Added `buildAiFailureClassification()` and `sanitizeProviderBaseUrl()` to produce decision-safe AI failure metadata without leaking URL credentials/query/hash.
- Classified failures into:
  - `first-pass-provider-timeout`
  - `repair-pass-provider-timeout`
  - `repair-retry-pass-provider-timeout`
  - `provider-unreachable`
  - `json-parse-failure`
  - `schema-validation-failure`
  - `strict-no-skeleton-fallback-block`
- Terminal failed AI jobs now include `metadata.aiFailureClassification`, `autoRetryAllowed: false`, `manualRetryEligible`, and `manualRetryEligibilityReason`.
- Strict no-skeleton block remains enforced. When the strict block wraps an underlying provider timeout/unreachable failure, the terminal classification preserves the strict block while keeping the underlying provider failure visible for manual-only retry review.
- No automatic retry, requeue, repair, reparse, re-AI, or existing failed task mutation was added.
- Ollama provider error details now include provider id for caller-side classification.

## Failure Metadata Contract

- `kind`: stable failure classification string.
- `aiPhase`: `first-pass`, `repair-pass`, `repair-retry-pass`, `provider-unreachable`, `json-parse`, `schema-validation`, or `strict-skeleton-block`.
- `timeoutKind`: provider timeout subtype when present.
- `durationMs`, `timeoutMs`: observed duration and configured timeout when available.
- `providerId`, `model`, `baseUrl`: provider identity with base URL sanitized.
- `autoRetryAllowed`: always `false`.
- `manualRetryEligible`: conservative manual-only eligibility. Provider timeout/unreachable can be eligible after review; JSON/schema semantic failures are not eligible. Strict skeleton block inherits eligibility only when its underlying failure is a provider timeout/unreachable candidate.
- `manualRetryEligibilityStatus` and `manualRetryEligibilityReason`: operator-facing review metadata.
- `underlying`: preserved summary when strict no-skeleton block wraps an earlier classified failure.

## Commands Run And Exit Codes

- `git status --short --branch` -> 0
- `node --check server/services/ai/metadata-worker.mjs` -> 0
- `node --check server/services/ai/providers/ollama.mjs` -> 0
- `node --check server/tests/ai-failure-classification-smoke.mjs` -> 0
- `node --check server/tests/ai-metadata-repair-hardening-smoke.mjs` -> 0
- `node server/tests/ai-failure-classification-smoke.mjs` -> 0
- `node server/tests/ai-metadata-repair-hardening-smoke.mjs` -> 0
- `git diff --check` -> 0
- `git rev-parse --short HEAD` -> 0
- `git branch --show-current` -> 0

## Skipped Checks And Reasons

- `npx pnpm@10.4.1 exec tsc --noEmit` skipped because no TypeScript or frontend file was changed.
- Production deployment, upload, pressure/batch/soak validation, cleanup, repair, retry, reparse, and re-AI were skipped because Task 154 explicitly forbids them.

## Evidence

- `server/tests/ai-failure-classification-smoke.mjs` passed and verifies timeout phases, provider unreachable, JSON parse failure, schema validation failure, strict no-skeleton wrapping, URL sanitization, `autoRetryAllowed: false`, and manual-only eligibility.
- Updated `server/tests/ai-metadata-repair-hardening-smoke.mjs` passed and verifies strict repair timeout still fails without skeleton fallback, does not repeat original markdown in repair input, and writes terminal failed metadata with strict block plus underlying `repair-pass-provider-timeout`.
- Implementation does not call any task retry/requeue APIs and does not modify existing failed tasks.
- Only source/test/report/ledger files were changed; no production DB, MinIO, Docker volume, sample, secret, model, provider, timeout, or runtime setting was modified.

## Risks / Blockers / Residual Debt

- This is code/test-level evidence only. Production runtime validation remains a separate Director decision.
- Existing failed pressure-test tasks are intentionally not retroactively classified or mutated; their metadata remains as-is unless Director/user later authorizes a bounded migration or manual retry workflow.
- Manual retry action itself is not implemented here; this task only makes eligibility metadata explicit and conservative.

## Review / Follow-Up

- Director review required: yes.
- Follow-up production validation or user decision required: yes, if Director wants this code deployed or wants a manual retry workflow for the three failed AI jobs.
