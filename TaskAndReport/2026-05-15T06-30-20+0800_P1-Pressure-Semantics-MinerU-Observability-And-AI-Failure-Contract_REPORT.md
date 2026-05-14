# DevelopmentEngineer Report: P1 Pressure Semantics, MinerU Observability, and AI Failure Contract

- Task: `TASK-20260515-063020-P1-Pressure-Semantics-MinerU-Observability-And-AI-Failure-Contract`
- Based on Director task brief: `TaskAndReport/2026-05-15T06-30-20+0800_P1-Pressure-Semantics-MinerU-Observability-And-AI-Failure-Contract_TASK.md`
- Merge decision read: `TaskAndReport/2026-05-15T06-30-20+0800_P1-Pressure-Semantics-MinerU-Observability-And-AI-Contract-Merge-Decision_DECISION.md`
- Branch / workspace state: `development-engineer/p0-post-validation-ollama-mineru-blockers`; workspace is dirty with many pre-existing shared-role changes and untracked task/report artifacts. No `git fetch`, `git pull`, `git push`, commit, or branch switch was run.
- HEAD: not re-queried in this role run; current DevelopmentEngineer shortcut restricts Git operations to `git status --short --branch`.

## Files changed for this task

- `server/lib/ai-failure-backfill.mjs` (new): extracts AI failure classification and builds Material/ParseTask backfill metadata.
- `server/lib/pressure-result-semantics.mjs` (new): classifies pressure-run outcomes as systemic failure vs partial success with retryable AI residuals.
- `server/lib/ops-mineru-log-parser.mjs`: adds `deriveMineruRuntimeProgressTruth()` so direct MinerU `processing` plus advancing raw logs or stale observation is not treated as terminal failure.
- `server/upload-server.mjs`: backfills AI failure classification metadata into both Material and ParseTask on failed AI terminal state; failed AI task message now reflects manual retry eligibility.
- `src/app/utils/taskView.ts`: operator-facing task status now distinguishes local wait timeout from remote MinerU still-processing, stale log observation, raw-log advancement, and manual-retry-eligible AI residual failure.
- `server/tests/ai-failure-backfill-smoke.mjs` (new).
- `server/tests/mineru-runtime-progress-truth-smoke.mjs` (new).
- `server/tests/pressure-result-semantics-smoke.mjs` (new).

Related pre-existing dirty files used by this merged task but not authored anew in this report include `server/services/ai/metadata-worker.mjs`, `server/services/ai/providers/ollama.mjs`, and `server/tests/ai-failure-classification-smoke.mjs`; Director should review the full dirty workspace diff before accepting.

## Implementation summary

1. AI failure contract:
   - Preserved strict no-skeleton behavior.
   - Failed AI updates now carry classification into Material and ParseTask metadata, including failure kind/phase/timeout/provider/model/baseUrl, `aiAutoRetryAllowed=false`, and manual retry eligibility fields.
   - Failed AI ParseTask message now says whether it is a manual-retry-eligible residual failure.

2. MinerU observability semantics:
   - Added a pure runtime-truth derivation helper for direct MinerU API status plus raw-log/observation signals.
   - Direct MinerU `processing` with advancing raw logs remains non-terminal even when local wait timeout occurred.
   - Direct MinerU `processing` with stale observation is explicitly labeled as observation lag, not terminal failure.
   - Task page utility wording now distinguishes stale observation from true failure and avoids flattening these cases into generic failed status.

3. Pressure-result semantics:
   - Added focused classification for the user-corrected case: mostly completed/review-pending tasks plus a few retryable AI residual failures should be `partial-success-with-retryable-ai-residuals`, not systemic failure.
   - Systemic failure remains reserved for non-retryable broad failure signals without success evidence.

## Commands run and exit codes

- `git status --short --branch` -> 0
- `sed ...` / `rg ...` source and task brief reads -> 0 where applicable
- `node --check server/lib/ai-failure-backfill.mjs` -> 0
- `node --check server/lib/pressure-result-semantics.mjs` -> 0
- `node --check server/lib/ops-mineru-log-parser.mjs` -> 0
- `node --check server/upload-server.mjs` -> 0
- `node server/tests/ai-failure-backfill-smoke.mjs` -> 0
- `node server/tests/mineru-runtime-progress-truth-smoke.mjs` -> 0
- `node server/tests/pressure-result-semantics-smoke.mjs` -> 0
- `node server/tests/ai-failure-classification-smoke.mjs` -> 0
- `node server/tests/ai-metadata-repair-hardening-smoke.mjs` -> 0
- `git diff --check` -> 0
- `npx pnpm@10.4.1 exec tsc --noEmit` -> 0
- `npx pnpm@10.4.1 run build` -> 0; Vite emitted only the existing large chunk warning.

## Skipped checks and reasons

- No production deployment, upload, pressure/batch/soak test, cleanup, repair, retry/reparse/re-AI, service restart/rebuild, DB/MinIO/Docker volume/data mutation, settings/secrets/config/model/sample mutation, or model operation was run because Task 157 explicitly forbids them.
- No GitHub sync was run because this DevelopmentEngineer role thread is explicitly forbidden to fetch/pull/push unless Director and the task brief authorize it.
- No release readiness, production readiness, L3, pressure PASS, or go-live claim is made.

## Evidence

- Backfill smoke confirms classified AI timeout metadata is available for Material/ParseTask updates and remains manual-only retry eligible.
- MinerU runtime-truth smoke confirms `localTimeoutOccurred=true` plus direct `processing` and raw-log advancement returns `terminalFailure=false`.
- MinerU stale-observation smoke confirms direct `processing` plus stale observation is labeled non-terminal and "不能按终态失败处理".
- Pressure semantics smoke confirms `20 success-like + 3 retryable AI residual + 1 active MinerU` is not systemic failure and classifies as `partial-success-with-retryable-ai-residuals`.
- `tsc --noEmit` and `vite build` passed after UI utility changes.

## Risks / blockers / residual debt

- The workspace is highly dirty from shared role threads; Director review should inspect the full diff and decide what belongs in the eventual commit.
- Task 157 is code/test only. Runtime behavior still requires later Director-authorized deployment and validation.
- The new pressure semantics helper is pure classification support; any dashboard/reporting caller adoption beyond the focused utility path may need a follow-up task.
- MinerU raw-log/direct-API truth is now represented in helper/page wording, but live runtime storage of `mineruRuntimeProgressTruth` may require a later integration task if Director wants it persisted on every task row.

## Review request

Director review required. No production validation or user release decision was performed in this task.
