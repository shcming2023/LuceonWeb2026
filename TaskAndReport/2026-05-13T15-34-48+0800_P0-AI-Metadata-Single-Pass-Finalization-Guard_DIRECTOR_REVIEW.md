# Director Review: P0 AI Metadata Single Pass Finalization Guard

Review time:
2026-05-13T15:34:48+0800

Reviewed task:
`TASK-20260513-151715-P0-AI-Metadata-Single-Pass-Finalization-Guard`

Reviewed report:
`TaskAndReport/2026-05-13T15-17-15+0800_P0-AI-Metadata-Single-Pass-Finalization-Guard_REPORT.md`

Reviewed implementation HEAD:
`3ac7b80 Guard AI metadata single-pass finalization`

Decision:
`ACCEPTED_CODE_TEST_LEVEL_PRODUCTION_DEPLOYMENT_HELD_FOR_BATCH`

## Summary

Director accepts Task 91 at code/test level.

The implementation addresses the duplicate-processing mechanism seen in Task 90: an AI metadata job could be processed once from the post-recovery snapshot and then again from the stale pre-recovery jobs snapshot. This is consistent with Task 90's trace where one AI job produced a successful Ollama/repair path and was later overwritten by a second repair failure.

Production deployment is not authorized by this review. Director will hold deployment until the MinerU terminal diagnostic precedence task is completed, then decide whether to batch both accepted fixes into one scoped production deployment/runtime validation.

## Evidence Reviewed

DevelopmentEngineer reported:

- root cause confirmed in `server/services/ai/metadata-worker.mjs::scanAndProcess()`;
- added early `return` after processing a recovered/pending job;
- added start-of-`processJob()` latest-state guard via `getJobById(job.id)`;
- added `server/tests/ai-metadata-single-pass-guard-smoke.mjs`;
- strict no-skeleton behavior was not changed;
- no production deployment, upload, pressure test, failed-task repair, cleanup, destructive mutation, model operation, or release-readiness claim occurred.

Director independently rechecked in a clean detached worktree at `3ac7b80` using a temporary `node_modules` symlink only for dependency resolution:

- `git diff --check` -> exit 0
- `node --check server/services/ai/metadata-worker.mjs` -> exit 0
- `node --check server/tests/ai-metadata-single-pass-guard-smoke.mjs` -> exit 0
- `node server/tests/ai-metadata-single-pass-guard-smoke.mjs` -> exit 0
- `node server/tests/ai-metadata-real-sample-smoke.mjs` -> exit 0
- `node server/tests/dependency-health-smoke.mjs` -> exit 0, `65 passed, 0 failed`
- `npx pnpm@10.4.1 exec tsc --noEmit` -> exit 0
- `npx pnpm@10.4.1 run build` -> exit 0 with existing Vite chunk-size warning only

## Boundary

Accepted:

- code-level fix for stale-snapshot duplicate AI job processing;
- focused regression coverage;
- preservation of strict no-skeleton semantics.

Not accepted or not claimed:

- production deployment;
- live upload validation;
- repair of historical failed tasks;
- production release readiness;
- L3;
- pressure PASS.

## Follow-Up

No immediate production task is issued from this review.

Director will first dispatch and review the MinerU terminal diagnostic precedence implementation, then decide whether to authorize one combined production deployment/runtime validation for both accepted code paths.
