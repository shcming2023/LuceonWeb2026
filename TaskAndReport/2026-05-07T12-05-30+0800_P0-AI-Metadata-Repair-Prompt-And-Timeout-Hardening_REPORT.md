# Lucode Task Report

Task ID: `TASK-20260507-105616-P0-AI-Metadata-Repair-Prompt-And-Timeout-Hardening`

Task brief: `TaskAndReport/2026-05-07T10-56-16+0800_P0-AI-Metadata-Repair-Prompt-And-Timeout-Hardening_TASK.md`

Assignee: Lucode

Branch: `lucode/p0-ai-repair-and-mineru-backfill`

Implementation commit: `ca639e82487b58dc7853f51690fd0eeb06d19ba5`

Status: Development and focused testing completed; ready for Lucia review. Not merged to `main`.

## Files Changed

- `server/services/ai/metadata-worker.mjs`
- `server/services/ai/metadata-standard-v0.2.mjs`
- `server/tests/ai-metadata-real-sample-smoke.mjs`
- `server/tests/ai-metadata-repair-hardening-smoke.mjs`

## Implementation Summary

- Added bounded AI JSON Repair input construction so the repair pass receives compact user content and a capped first-pass draft, not the original sampled Markdown again.
- Added deterministic draft normalization for recoverable `classification_draft`, flat JSON, `descriptive_draft`, `candidate_tags`, and `evidence_snippets` style outputs before spending a second LLM repair call.
- Preserved strict no-skeleton semantics: repair timeout/failure still fails explicitly when `DISABLE_AI_SKELETON_FALLBACK=true` or `ALLOW_AI_SKELETON_FALLBACK=false`.
- Extended raw trace observability with `promptLength`, `inputLength`, `numPredict`, `durationMs`, deterministic repair details, and repair input details.
- Updated existing AI smoke expectations so recoverable flat/schema-invalid drafts are treated as deterministic repair, while unrecoverable schema-invalid repair failure still degrades only in non-strict mode.

## Evidence

- Deterministic repair success case:
  - `node server/tests/ai-metadata-repair-hardening-smoke.mjs`
  - Evidence line: `Case 1 Pass: deterministic draft repair skips second provider call`
  - Asserted provider call count is `1`, `aiClassificationDeterministicRepairSucceeded=true`, and provider is not `skeleton`.
- Strict repair-timeout failure case:
  - `node server/tests/ai-metadata-repair-hardening-smoke.mjs`
  - Evidence line: `Case 2 Pass: strict repair timeout fails without skeleton and bounded input`
  - Asserted terminal state is `failed`, error contains `AI 严格模式拦截`, repair user content does not contain `ORIGINAL_MARKDOWN_SENTINEL`, and repair prompt is bounded under 20000 chars.

## Commands Run

- `git status --short --branch` -> exit `0`; branch `lucode/p0-ai-repair-and-mineru-backfill`, modified source files before commit.
- `node --check server/services/ai/metadata-worker.mjs` -> exit `0`.
- `node --check server/tests/ai-metadata-repair-hardening-smoke.mjs` -> exit `0`.
- `node server/tests/ai-metadata-repair-hardening-smoke.mjs` -> exit `0`.
- `node server/tests/ai-metadata-real-sample-smoke.mjs` -> exit `0`; final line `--- AI Metadata Real Sample Smoke Test Success ---`.
- `node server/tests/worker-smoke.mjs` -> exit `0`; strict AI mode failed fast without skeleton fallback.
- `npx pnpm@10.4.1 exec tsc --noEmit` -> exit `0`.
- `npx pnpm@10.4.1 run build` -> exit `0`; Vite build succeeded with existing chunk-size warning.
- `git diff --check` -> exit `0`.

## Skipped Checks

- Runtime UAT against the running CMS was not executed for this P0 AI task because the branch is not deployed to the local `8081` runtime in this development workspace, and the task brief forbids production/data mutation. This report is code-level and focused-smoke evidence only.

## Risks / Residuals

- Deterministic normalization is intentionally conservative: if no meaningful facet can be recovered, it falls back to the existing LLM repair path.
- Lucia should review whether the added deterministic field mapping is broad enough for real Ollama malformed outputs without becoming over-permissive.

## Review Needed

Lucia review is required before merge to `main` or any project-ledger promotion.
