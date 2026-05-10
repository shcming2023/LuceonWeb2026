# Lucia Review: P0 MinerU Submit-Path 500 Circuit Breaker And Failure-State Handling

- Review Time: `2026-05-10T08:12:29+0800`
- Reviewer: Lucia
- Reviewed Task: `TASK-20260510-075129-P0-MinerU-Submit-Path-500-Circuit-Breaker-And-Failure-State`
- Reviewed Report: `TaskAndReport/2026-05-10T07-51-29+0800_P0-MinerU-Submit-Path-500-Circuit-Breaker-And-Failure-State_REPORT.md`
- Lucode Branch: `lucode/p0-mineru-submit-500-circuit-breaker`
- Implementation Commit: `c43c2b1aa9a2a2be17ccc1601bbd83524d6c6812`
- Report Branch HEAD: `d1abdc33a9b0c0def70a6e84be545ef2318f5fa7`
- Integrated To Main: pending Lucia review commit
- Decision: `ACCEPTED_CODE_LEVEL_RELEASE_BLOCKER_REMAINS`

## Review Summary

Lucia accepts the Task 64 implementation at code level and fast-forward integrated the Lucode branch into local `main`.

The fix correctly treats MinerU submit-path HTTP 500 as a dependency-blocking condition rather than a per-task execution failure. This prevents a failing MinerU `/tasks` endpoint from cascading subsequent queued local-MinerU PDF tasks into `execution-failed`.

Accepted behavior:

- `MineruSubmitUnreachableError` now carries structured submit-path evidence including status, endpoint, dependency-blocking flag, and retry-after duration.
- MinerU submit communication failures, submit HTTP 5xx, and missing task id are converted to dependency-blocking submit errors.
- The worker opens an in-process MinerU submit circuit.
- The current task remains `pending / dependency-blocked`.
- The related material is normalized to `status=processing`, `mineruStatus=blocked`, `aiStatus=pending`, and `processingStage=dependency-blocked`.
- Subsequent local-MinerU PDF submissions pause while the circuit is open.
- Markdown passthrough tasks are not blocked by this circuit.
- Existing non-dependency submit-unreachable retry behavior is preserved.

## Independent Verification

Lucia independently ran:

- `node server/tests/mineru-submit-circuit-breaker-smoke.mjs` -> PASS, `9 passed / 0 failed`
- `node server/tests/mineru-submit-retryable-smoke.mjs` -> PASS, `6 passed / 0 failed`
- `node server/tests/mineru-no-resubmit-smoke.mjs` -> PASS, `38 passed / 0 failed`
- `node server/tests/mineru-metadata-status-cleanup-smoke.mjs` -> PASS, `9 passed / 0 failed`
- `node server/tests/dependency-health-smoke.mjs` -> PASS, `40 passed / 0 failed`
- `git diff --check` -> PASS
- `npx pnpm@10.4.1 exec tsc --noEmit` -> PASS
- `npx pnpm@10.4.1 run build` -> PASS, with only the existing Vite large-chunk warning

## Residual Risk

The circuit breaker is in-process and does not heal MinerU itself. Production still had MinerU submit-probe HTTP 500 in Lucode's read-only evidence. Previously failed 24 pressure-test tasks are not repaired by this code change.

Therefore this is not production release readiness. Release readiness remains blocked until Director authorizes and Lucia reviews production deployment and runtime recovery/validation evidence.

## Next Step

Lucia records Director decision Task 65 for production deployment/runtime recovery authorization.

