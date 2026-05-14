# Director Review: Task 157 Pressure Semantics, MinerU Observability, And AI Failure Contract

Task: `TASK-20260515-063020-P1-Pressure-Semantics-MinerU-Observability-And-AI-Failure-Contract`

Review time: 2026-05-15T07:43:09+0800

Reviewer: Director

## Verdict

`ACCEPTED_CODE_TEST_LEVEL_INTEGRATION_PRODUCTION_DEPLOYMENT_DECISION_REQUIRED`

I accept Task 157 at code/test level and integrated the scoped implementation into the clean GitHub-sync working copy for main. This is not production deployment, not runtime validation, not pressure PASS, not L3, not release readiness, and not go-live readiness.

## Scope Reviewed

Reviewed the DevelopmentEngineer report and replayed only the scoped Task 157 implementation files into the clean sync clone, excluding unrelated dirty workspace changes.

Accepted files:

- `server/lib/ai-failure-backfill.mjs`
- `server/lib/pressure-result-semantics.mjs`
- `server/lib/ops-mineru-log-parser.mjs`
- `server/services/ai/metadata-worker.mjs`
- `server/services/ai/providers/ollama.mjs`
- `server/upload-server.mjs`
- `src/app/utils/taskView.ts`
- `server/tests/ai-failure-backfill-smoke.mjs`
- `server/tests/ai-failure-classification-smoke.mjs`
- `server/tests/ai-metadata-repair-hardening-smoke.mjs`
- `server/tests/mineru-runtime-progress-truth-smoke.mjs`
- `server/tests/pressure-result-semantics-smoke.mjs`
- Task 157 report artifact

## Review Findings

No blocking code defect was found in the scoped Task 157 changes.

The implementation addresses the user's correction in three important ways:

1. AI transport/timeout failures are classified as manual-only retry eligible and backfilled into Material and ParseTask metadata.
2. Task display semantics distinguish remote MinerU `processing`, local timeout, stale log observation, and raw-log advancement instead of flattening those cases into terminal failure language.
3. Pressure outcome semantics now have a focused classification helper and smoke test for `20 success-like + 3 retryable AI residual + 1 active MinerU` as partial success with retryable AI residuals, not systemic whole-run failure.

## Residuals

- Production still runs the previous deployed code until a separately authorized deployment task is executed.
- `deriveMineruRuntimeProgressTruth()` is currently a pure helper/tested semantic contract; live persistence of `mineruRuntimeProgressTruth` onto every task row remains a possible follow-up if we need a first-class stored field.
- `classifyPressureRunOutcome()` is a focused helper/test hook; broader dashboard/reporting adoption can be a follow-up after deployment validation.
- The DevelopmentEngineer report omitted the source HEAD despite the task template requiring it. Director recovered the local source HEAD during review as `005ca96b0df620258916ae1e63550060eaa4f24e`. This report-format miss is not blocking because scoped code was replayed and verified in a clean sync clone.

## Checks Re-Run By Director

In the original development workspace:

- `git diff --check` -> 0
- `node --check server/lib/ai-failure-backfill.mjs` -> 0
- `node --check server/lib/pressure-result-semantics.mjs` -> 0
- `node --check server/lib/ops-mineru-log-parser.mjs` -> 0
- `node --check server/upload-server.mjs` -> 0
- `node server/tests/ai-failure-backfill-smoke.mjs` -> 0
- `node server/tests/mineru-runtime-progress-truth-smoke.mjs` -> 0
- `node server/tests/pressure-result-semantics-smoke.mjs` -> 0
- `node server/tests/ai-failure-classification-smoke.mjs` -> 0
- `node server/tests/ai-metadata-repair-hardening-smoke.mjs` -> 0
- `npx pnpm@10.4.1 exec tsc --noEmit` -> 0
- `npx pnpm@10.4.1 run build` -> 0, with only the existing Vite large chunk warning

In the clean GitHub-sync clone after replaying scoped files:

- `git diff --check` -> 0
- `node --check server/lib/ai-failure-backfill.mjs` -> 0
- `node --check server/lib/pressure-result-semantics.mjs` -> 0
- `node --check server/lib/ops-mineru-log-parser.mjs` -> 0
- `node --check server/upload-server.mjs` -> 0
- `node --check server/services/ai/metadata-worker.mjs` -> 0
- `node --check server/services/ai/providers/ollama.mjs` -> 0
- `node server/tests/ai-failure-backfill-smoke.mjs` -> 0
- `node server/tests/mineru-runtime-progress-truth-smoke.mjs` -> 0
- `node server/tests/pressure-result-semantics-smoke.mjs` -> 0
- `node server/tests/ai-failure-classification-smoke.mjs` -> 0
- `node server/tests/ai-metadata-repair-hardening-smoke.mjs` -> 0
- `npx pnpm@10.4.1 exec tsc --noEmit` -> 0
- `npx pnpm@10.4.1 run build` -> 0, with only the existing Vite large chunk warning

## Director Decision

Close Task 157 as accepted at code/test level and record Task 158 as the user-owned production deployment decision.

Recommended next path: Option A in Task 158, scoped production deployment plus read-only validation only.

Still not authorized: production deployment until Task 158 is decided, upload, pressure/batch/soak test, cleanup, repair, retry/reparse/re-AI for existing tasks, destructive DB/MinIO/Docker volume/data mutation, Docker down/restart/rebuild/service ownership mutation beyond a future explicitly scoped deployment task, settings/secrets/config/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, pressure PASS, L3, release-readiness, production-readiness, or go-live claim.
