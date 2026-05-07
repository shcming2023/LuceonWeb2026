# Lucia Review

Task ID: `TASK-20260507-105616-P1-MinerU-Sidecar-Completed-Window-Log-Backfill`

Task name: P1 MinerU Sidecar Completed-Window Log Backfill

Review time: `2026-05-07T12:13:24+0800`

Reviewer: Lucia

Result: `ACCEPTED_WITH_SEPARATE_TEST_DEBT`

## Reviewed Inputs

- Task brief: `TaskAndReport/2026-05-07T10-56-16+0800_P1-MinerU-Sidecar-Completed-Window-Log-Backfill_TASK.md`
- Lucode report: `TaskAndReport/2026-05-07T12-05-30+0800_P1-MinerU-Sidecar-Completed-Window-Log-Backfill_REPORT.md`
- Implementation branch: `lucode/p0-ai-repair-and-mineru-backfill`
- Implementation commit: `ca639e82487b58dc7853f51690fd0eeb06d19ba5`
- Report commit: `bc178df2a2a68854e6cdc1a2a37cba3a83826ef0`

## Review Findings

- The existing live exact-one active attribution path is preserved and explicitly marked with `attributionMode=live-active`.
- The completed-window path is conservative: it requires local MinerU, a MinerU task id, a known start time, a known completion time, a bounded grace window, and exactly one matching candidate.
- Ambiguous windows remain unattributed. Before-start, after-grace, multiple-candidate, missing-time, and canceled-task cases are covered by focused smoke tests.
- The implementation updates only observation metadata and global observation. It does not mutate parse state, material state, MinIO objects, or MinerU runtime.

## Lucia Verification

- `git diff --check`: PASS.
- `node --check server/upload-server.mjs`: PASS.
- `node server/tests/mineru-sidecar-completed-window-smoke.mjs`: PASS.
- `node server/tests/mineru-sidecar-smoke.mjs`: PASS.
- `node server/tests/mineru-log-source-live-smoke.mjs`: PASS.
- `npx pnpm@10.4.1 exec tsc --noEmit`: PASS.
- `npx pnpm@10.4.1 run build`: PASS, with the existing Vite chunk-size warning only.

## Residual Test Debt

`node server/tests/mineru-log-progress-smoke.mjs` still fails at Test 4 because the test expects `failed-confirmed` while the current parser returns `log-error-signal`. Lucia verified that `server/lib/ops-mineru-log-parser.mjs` and `server/tests/mineru-log-progress-smoke.mjs` were not modified by this implementation branch, so this is treated as pre-existing test-truth drift rather than a regression introduced by the completed-window backfill.

## Decision

The implementation is accepted for merge to `main`. A separate P0 test-truth alignment task is issued to restore the MinerU log progress smoke test without masking the failure through `.skip` or broad semantic changes.
