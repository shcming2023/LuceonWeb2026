# Director Review: P1 Terminal MinerU Diagnostic Precedence

Review time:
2026-05-13T16:31:04+0800

Reviewed task:
`TASK-20260513-153448-P1-Terminal-MinerU-Diagnostic-Precedence`

Reviewed report:
`TaskAndReport/2026-05-13T15-34-48+0800_P1-Terminal-MinerU-Diagnostic-Precedence_REPORT.md`

Reviewed implementation HEAD:
`54c4786 Prefer terminal MinerU diagnostics`

Decision:
`ACCEPTED_CODE_TEST_LEVEL_PRODUCTION_DEPLOYMENT_REQUIRED`

## Summary

Director accepts Task 93 at code/test level.

The implementation makes terminal MinerU completion diagnostics take precedence over stale or unreadable in-flight log diagnostics when MinerU is already completed and parsed artifact evidence exists. It does not fabricate page, batch, phase, or percent progress, and it keeps final AI failure visible separately.

Production deployment is not performed by this review. Director issues a separate scoped deployment/runtime validation task that batches the accepted Task 91 AI worker fix and the accepted Task 93 MinerU display semantics fix.

## Evidence Reviewed

DevelopmentEngineer reported:

- `src/app/utils/taskView.ts` now detects parsed artifact evidence;
- terminal completion diagnostics return `MinerU 已完成，但本次未捕获可归因业务进度日志`;
- Task 90-shaped data no longer displays the old in-flight wording after MinerU completion;
- active live progress with real phase/batch/page details remains preserved;
- final AI failure status still displays separately;
- no production deployment, upload, repair, cleanup, destructive mutation, restart, L3, pressure PASS, or release-readiness claim occurred.

Director independently rechecked in a clean detached worktree at `54c4786` using a temporary `node_modules` symlink only for dependency resolution:

- `git diff --check` -> exit 0
- `node --check server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs` -> exit 0
- `node server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs` -> exit 0
- `node server/tests/mineru-log-progress-smoke.mjs` -> exit 0, `144 passed, 0 failed`
- `npx pnpm@10.4.1 exec tsc --noEmit` -> exit 0
- `npx pnpm@10.4.1 run build` -> exit 0 with existing Vite chunk-size warning only

## Boundary

Accepted:

- code/test-level terminal MinerU diagnostic precedence;
- no fabricated progress details;
- AI failure remains separate;
- Task 91 and Task 93 are now both eligible for a combined production deployment/runtime validation decision.

Not accepted or not claimed:

- production deployment;
- live upload validation;
- repair of historical failed tasks;
- production release readiness;
- L3;
- pressure PASS.

## Follow-Up

Director issued:

`TASK-20260513-163104-P0-Batched-AI-And-MinerU-Fixes-Production-Deployment-And-Runtime-Validation`

Assigned to:

`DevelopmentEngineer`

This follow-up is limited to production fast-forward, minimum necessary service rebuild/recreate, and non-destructive runtime validation. It does not authorize upload validation or production readiness claims.
