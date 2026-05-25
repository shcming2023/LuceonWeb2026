# P0 RawMaterial2CleanMaterial Pilot To Minimal Operator Runner Decision

Decision ID: `TASK-20260525-145240-P0-RawMaterial2CleanMaterial-Pilot-To-Minimal-Operator-Runner-Decision`

Decision time: 2026-05-25T14:52:40+0800

Baseline: `main@d99e7533611c6e523094c860b1416db2626edc9e`

Status: `DECISION_MINIMAL_OPERATOR_TRIGGERED_RUNNER_NEXT`

## Decision

RawMaterial2CleanMaterial should now advance from pilot harnesses to a minimal
operator-triggered runner.

The next implementation task must convert the proven pilot boundary into a
controlled entrypoint with:

- hard sample cap;
- dry-run mode;
- stop-on-first-failure;
- per-sample evidence;
- explicit no-readiness wording.

Do not continue by blindly increasing the sample count.

## Basis

The chain has crossed three evidence gates:

1. single-sample durable candidate and accepted decision;
2. third canonical sample strict pilot with no failed namespace, no fallback
   asset version, no second POST, and no diagnostic MinIO write;
3. bounded mini-batch pilot with 3/3 samples completed sequentially.

Task 288 evidence:

```json
{
  "sampleCount": 3,
  "rawSeedPutObject": 3,
  "cleanServicePost": 3,
  "raw2cleanCandidatePutObject": 3,
  "dbPatch": 6,
  "minioDelete": 0,
  "runtimePostOtherThanCleanService": 0,
  "dockerOperation": 0
}
```

The mainline question is no longer whether the path can be repeated by a local
harness. The next question is whether the proven boundary can be exposed as a
controlled operator action without turning into an uncontrolled batch system.

## Required Runner Boundary

The minimal operator-triggered runner must be narrow:

- explicit operator invocation only;
- no background daemon, scheduler, queue worker, or automatic scan;
- hard cap, initially no more than 3 samples per invocation;
- explicit sample IDs supplied by the operator or a tightly bounded manifest;
- dry-run mode that performs no DB write, no MinIO write, and no CleanService
  POST;
- real mode that must first pass dry-run preflight;
- sequential execution only;
- stop-on-first-failure;
- one CleanService POST maximum per sample;
- no automatic fallback to another asset version or namespace;
- no extra diagnostic MinIO writes;
- per-sample evidence containing raw seed SHA, CleanService job id, candidate
  ObjectRef/SHA, DB patch count, and product-surface/read-back status.

## Forbidden For Next Task

The next task must not implement:

- broad batch processing;
- automatic discovery/scanning of all materials;
- scheduler/daemon/worker activation;
- retry queues;
- cleanup, deletion, migration, or backfill;
- fallback namespace/version recovery;
- final quality acceptance;
- repair/reject workflows;
- production deployment/restart;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claim.

## Acceptance Boundary For Next Implementation

Acceptance of the next task should mean only:

```text
operator-selected samples -> dry-run preflight -> bounded real run ->
per-sample durable candidate evidence
```

It must not mean the service is generally batch-ready, production-ready, or
quality-accepted.

## Deferred Work

Defer until after the minimal operator runner exists:

- larger sample caps;
- retry policy;
- repair/reject decision paths;
- cleanup of Task 285 residual failed job and diagnostic object;
- metadata schema consolidation;
- quality acceptance workflow;
- production deployment/readiness plan.

## Boundary

This decision performs no code change, DB write, MinIO write/delete/list,
runtime POST, Docker/Compose operation, source/sample/env/secret/model mutation,
batch execution, production deployment, readiness claim, or go-live claim.

