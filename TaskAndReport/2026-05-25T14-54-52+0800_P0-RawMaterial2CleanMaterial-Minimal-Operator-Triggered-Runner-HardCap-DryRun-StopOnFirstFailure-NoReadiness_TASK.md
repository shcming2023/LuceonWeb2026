# P0 RawMaterial2CleanMaterial Minimal Operator Triggered Runner HardCap DryRun StopOnFirstFailure NoReadiness Task

Task ID: `TASK-20260525-145452-P0-RawMaterial2CleanMaterial-Minimal-Operator-Triggered-Runner-HardCap-DryRun-StopOnFirstFailure-NoReadiness`

Issued at: 2026-05-25T14:54:52+0800

Owner: Luceon

Baseline: `main@5c7e1c71329dcb2d839a69d1b3b4f97c430b3369`

## Mainline Objective

Convert the proven RawMaterial2CleanMaterial pilot harness boundary into a
minimal operator-triggered runner that can be invoked deliberately with a bounded
sample set.

This task should create the controlled entrypoint and tests. It should not run a
new live batch against DB/MinIO/CleanService.

## Critical Path Scope

Implement the smallest runner boundary that supports:

- explicit operator invocation;
- hard cap, default and maximum `3` samples;
- dry-run mode that performs no DB writes, no MinIO writes, and no CleanService
  POSTs;
- real mode as an explicit option in code/API shape, but not exercised against
  live services in this task;
- sequential execution only;
- stop-on-first-failure;
- per-sample evidence records;
- no readiness wording.

## Required Behavior

The runner must:

1. require an explicit sample manifest or sample list;
2. reject empty sample lists;
3. reject sample count above the hard cap;
4. reject duplicate material/task pairs;
5. preserve input sample order;
6. run dry-run preflight before any real-mode sample work;
7. stop immediately on the first failed sample;
8. emit a summary with:
   - attempted sample count;
   - completed sample count;
   - stopped sample and stage when blocked;
   - per-sample raw seed SHA/size;
   - CleanService job id plan or submitted job id;
   - candidate ObjectRef/SHA when produced;
   - DB patch count;
   - boundary operation counts;
   - explicit `readinessClaimed=false`.

## Allowed Files / Modules

Keep implementation narrow. Prefer a new server-side service/helper plus focused
tests, for example:

- `server/services/rawmaterial2cleanmaterial/operator-runner.mjs`
- `server/tests/rawmaterial2cleanmaterial-operator-runner-smoke.mjs`

Small imports or exports may be added only if required by the tests.

## Forbidden Operations

During this task:

- do not execute live real-mode runner;
- do not perform DB PATCH/POST/PUT/DELETE;
- do not perform MinIO put/delete/copy/move/cleanup/list-bucket scan;
- do not perform CleanService runtime POST;
- do not run Docker/Compose restart/recreate/rebuild;
- do not activate scheduler, daemon, queue worker, background worker, or broad
  automatic scan;
- do not implement retry queues;
- do not implement fallback namespace/version recovery;
- do not implement cleanup/backfill/migration;
- do not implement repair/reject workflow;
- do not implement final quality acceptance;
- do not claim UAT, L3, pressure PASS, release readiness, production readiness,
  production online, or go-live.

## Fast Validation Target

Focused tests should prove:

- happy-path dry-run over 3 samples with fake dependencies;
- real-mode shape with fake dependencies and explicit operator confirmation;
- hard cap rejection;
- duplicate rejection;
- empty-list rejection;
- stop-on-first-failure prevents later samples from running;
- dry-run has zero write/POST operation counts;
- summary never claims readiness.

## Review Boundary

Acceptance means only that the minimal operator-triggered runner boundary exists
at code/test level and preserves the Task 289 safety model.

Acceptance does not authorize a live real-mode run, production deployment,
background automation, broad batch processing, final quality acceptance,
readiness, UAT, L3, pressure PASS, production online, or go-live.

