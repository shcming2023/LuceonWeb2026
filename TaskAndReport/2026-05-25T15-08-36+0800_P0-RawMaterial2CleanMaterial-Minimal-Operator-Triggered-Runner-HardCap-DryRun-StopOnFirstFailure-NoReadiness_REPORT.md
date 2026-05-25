# P0 RawMaterial2CleanMaterial Minimal Operator Triggered Runner HardCap DryRun StopOnFirstFailure NoReadiness Report

Task ID: `TASK-20260525-145452-P0-RawMaterial2CleanMaterial-Minimal-Operator-Triggered-Runner-HardCap-DryRun-StopOnFirstFailure-NoReadiness`

Report time: 2026-05-25T15:08:36+0800

Status: `SUCCESS_CODE_TEST_LEVEL_OPERATOR_RUNNER_BOUNDARY`

Implementation branch: `codex/TASK-20260525-145452-operator-runner`

## Summary

Implemented a minimal RawMaterial2CleanMaterial operator-triggered runner
boundary at code/test level.

The new runner is deliberately a boundary/orchestration helper, not a live
service activation. It does not directly talk to DB, MinIO, CleanService,
Docker, queues, or schedulers. Sample execution is injected through a dependency
function, which lets the runner enforce operator, cap, ordering, dry-run,
real-mode confirmation, preflight, stop-on-first-failure, and evidence summary
rules without widening runtime scope.

## Changed Files

- `server/services/rawmaterial2cleanmaterial/operator-runner.mjs`
- `server/tests/rawmaterial2cleanmaterial-operator-runner-smoke.mjs`

## Implemented Boundary

The runner now enforces:

- explicit `operatorId`;
- default hard cap `3`;
- empty-list rejection;
- hard-cap overflow rejection;
- duplicate material/task pair rejection;
- order-preserving sequential execution;
- dry-run mode with zero write/POST operation counts;
- real mode requiring `confirmRealRun=true`;
- real mode always runs dry-run preflight first;
- failed preflight blocks real execution;
- stop-on-first-failure blocks later samples;
- per-sample evidence slots for raw seed, CleanService, candidate, DB patch
  count, product surface, and operation counts;
- top-level and per-sample `readinessClaimed=false`.

## Checks

| Check | Exit |
| --- | ---: |
| `node server/tests/rawmaterial2cleanmaterial-operator-runner-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-protocol-runner-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-candidate-view-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-candidate-decision-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs` | 0 |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 |
| `npx pnpm@10.4.1 run build` | 0 |
| `git diff --check` | 0 |

Build emitted only the existing Vite chunk-size warning.

## Boundary Confirmation

No live real-mode runner execution was performed.

No DB PATCH/POST/PUT/DELETE, MinIO put/delete/copy/move/cleanup/list-bucket scan,
CleanService runtime POST, Docker/Compose restart/recreate/rebuild,
scheduler/daemon/queue/worker activation, retry queue, fallback namespace/version
recovery, cleanup/backfill/migration, repair/reject workflow, final quality
acceptance, UAT, L3, pressure PASS, release readiness, production readiness,
production online, or go-live claim was made.

## Residual Debt

- The runner is not yet wired to an operator UI/API action.
- No live real-mode invocation of the new runner has been authorized or tested.
- No durable manifest file format has been standardized beyond the in-memory
  sample list boundary.
- Retry, repair/reject, cleanup, schema consolidation, quality acceptance, and
  readiness planning remain deferred.

## Recommended Next Step

Use this runner boundary as the basis for a narrow operator action or CLI wiring
task. The next task should still keep a hard cap, dry-run-first behavior, and no
readiness/go-live wording.

