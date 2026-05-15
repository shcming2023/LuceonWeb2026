# Director Review: P1 MinerU Progress Snapshot Contract And Active-Task Reconciliation

- Task ID: `TASK-20260516-062058-P1-MinerU-Progress-Snapshot-Contract-And-Active-Task-Reconciliation`
- Reviewed at: `2026-05-16T06:49:06+0800`
- Reviewed by: `Director`
- Implementation HEAD reviewed: `c6c5790`
- Result: `ACCEPTED_CODE_TEST_LEVEL_PRODUCTION_DEPLOYMENT_DECISION_REQUIRED`

## Scope Reviewed

Director reviewed the DevelopmentEngineer report and implementation for the MinerU progress-semantics root-cause follow-up:

- backend normalized `progressSnapshot` contract;
- `/ops/mineru/active-task` direct MinerU API / DB reconciliation semantics;
- explicit lag classification for direct MinerU completion while Luceon DB ingestion is still behind;
- terminal/idle log-state distinction so stale logs are not misread as active failure;
- dependency-health readiness-only progress snapshot boundary;
- task-event log cleanup to avoid `Status changed to undefined`;
- minimal frontend display fix so historical AI-stage state does not override canonical terminal failure semantics without AI-failure evidence.

## Director Judgment

Accepted at code/test level.

The implementation addresses the root cause accepted in Task 192: Luceon previously flattened several different truths into one operator-facing meaning. The new contract makes source, source priority, freshness, confidence, lag kind, direct MinerU status, DB state/stage, log state, AI state, and operator message explicit. This is the right direction because the long-running pressure-test confusion was not merely a page-copy issue; it was a missing cross-source semantic contract.

The most important accepted behavior is that when direct MinerU reports completion while Luceon DB still shows a parse-running state, the system now marks the condition as `db-behind-direct-mineru` rather than implying that MinerU is still stuck. That preserves the true async ingestion boundary without pretending the material is fully ready before DB/result ingestion catches up.

## Verification Rerun By Director

Director reran or completed the following checks from the current `main` checkout:

- `git diff --check`: passed.
- `node --check server/lib/progress-snapshot.mjs && node --check server/upload-server.mjs && node --check server/services/queue/task-worker.mjs`: passed.
- `node server/tests/progress-snapshot-contract-smoke.mjs && node server/tests/task-event-message-smoke.mjs && node server/tests/ops-mineru-active-task-classification-smoke.mjs && node server/tests/dependency-health-smoke.mjs && node server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs`: passed, including `89 passed, 0 failed` for dependency-health smoke.
- `npx pnpm@10.4.1 exec tsc --noEmit`: passed.
- `npx pnpm@10.4.1 run build`: passed. Existing Vite chunk-size warning remains non-blocking and unchanged in nature.

## Boundaries Not Accepted As Done

This review does not declare production deployment, pressure PASS, L3, release readiness, or go-live readiness.

Production still needs a scoped deployment/read-only validation decision because the accepted implementation changes both server behavior and a frontend task-display utility. The next step should not be another pressure test yet; first verify that the new production surface exposes the intended progress snapshot semantics without upload, submit-probe, retry, reparse, re-AI, data cleanup, or broad restart.

## Residual Risks / Follow-Up

- `/ops/mineru/active-task` now direct-checks candidate MinerU task IDs by default. This is read-only and appropriate for the ops surface, but production validation should observe endpoint latency and behavior under an idle and active queue.
- The code-level contract is present, but operator value depends on production deployment and UI/ops observation against real runtime state.
- CleanServiceWorker planning Task 189 remains separate and is still assigned to Architect.

## Director Decision

Task 193 is accepted and closed at code/test level.

Director recorded a follow-up User decision row for scoped production deployment and read-only validation of the progress snapshot implementation.
