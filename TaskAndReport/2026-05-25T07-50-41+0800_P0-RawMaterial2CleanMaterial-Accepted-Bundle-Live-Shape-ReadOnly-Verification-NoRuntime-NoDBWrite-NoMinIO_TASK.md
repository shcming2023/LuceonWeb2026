# TASK-20260525-075041-P0-RawMaterial2CleanMaterial-Accepted-Bundle-Live-Shape-ReadOnly-Verification-NoRuntime-NoDBWrite-NoMinIO

Issued at: 2026-05-25T07:50:41+0800

Actor: Luceon

## Mainline Objective

Prove the next mainline bridge without widening into downstream execution:

```text
durable accepted toc-rebuild v4 Clean Material metadata
=> live DB-shaped material/task GET results
=> RawMaterial2CleanMaterial input bundle helper
```

Task 273 accepted the pure helper against mock-safe fixtures. This task verifies
whether the persisted canonical sample's current read-only DB shape can feed the
same helper.

## Critical Path Scope

Run a narrow Luceon-owned read-only verification for the canonical sample:

```text
materialId = 1842780526581841
taskId = task-1779085089451
serviceName = toc-rebuild
assetVersion = v4
jobId = luceon-task-1779085089451-toc-rebuild-v4
```

Required checks:

1. Read current material by GET only.
2. Read current task by GET only.
3. Compile/import the accepted helper:

   ```text
   src/app/utils/rawMaterial2CleanMaterialInputBundle.ts
   ```

4. Call `buildRawMaterial2CleanMaterialInputBundle()` with the live-shaped
   material/task objects and `currentAssetVersion = v4`.
5. Verify the bundle contains:

   - `kind = raw-material-2-clean-material-input`
   - `serviceName = toc-rebuild`
   - canonical material/task ids
   - `assetVersion = v4`
   - canonical job id
   - provenance object name
   - sourceInput object and sha256
   - required artifact refs:
     `readable_tree`, `logic_tree`, `skeleton`, `flooded_content`
   - optional current refs if present:
     `metrics`, `provenance`, `unresolved_anchors`
   - `operatorDecision.state = accepted`

## True Preconditions

- Current `main` must be synchronized before execution.
- Existing app/proxy/db service may be queried only if already running.
- Do not start, restart, rebuild, deploy, or mutate runtime services to make the
  check pass.

## Deferrable Side Work

- RawMaterial2CleanMaterial service protocol design.
- RawMaterial2CleanMaterial runtime execution.
- DB persistence of downstream Clean Material output.
- UI launch/approval workflow for downstream cleaning.
- Batch/operator governance.
- General artifact registry cleanup.

## Fast Validation Target

A successful result is a small evidence file under `/tmp` plus a Luceon report
showing the helper returned `ok=true` from current read-only material/task
objects.

## Stop Rule

Stop and report blocked instead of widening scope if:

- GET material or task is unavailable;
- material/task shape no longer contains accepted v4 metadata;
- the helper returns a structured blocked result;
- verification would require POST/PATCH/PUT/DELETE, MinIO read/write/list/get,
  runtime POST, service execution, Docker/Compose operation, or source-code
  changes.

## Review Boundary

Acceptance means only:

```text
the current persisted accepted canonical sample can build a traceable
RawMaterial2CleanMaterial input bundle from live-shaped read-only DB objects
```

Acceptance does not mean RawMaterial2CleanMaterial exists, has a runtime
protocol, has run, wrote output, is production-ready, or is approved for go-live.

## Allowed Files And Evidence

Allowed durable files:

- this task brief;
- the Luceon report for this task;
- `TaskAndReport/TASK_TRACKING_LIST.md`.

Allowed temporary evidence:

- `/tmp/luceon-task274-*`

## Forbidden Operations

Forbidden:

- DB POST/PATCH/PUT/DELETE;
- MinIO get/list/put/copy/move/delete/write/delete-marker/cleanup;
- CleanService runtime run;
- RawMaterial2CleanMaterial execution, transport, endpoint, worker, or Docker
  service;
- Mineru2Table POST/query/probe;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test;
- model, env, secret, sample, source asset, or local override mutation;
- source-code edit;
- production deployment or production runtime validation;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claim.

## Required Report

The report must include:

- task id and baseline `main` SHA;
- GET endpoints used and read-only status;
- helper invocation summary;
- pass/block decision;
- bundle field summary without artifact body content;
- exact commands and exit codes;
- explicit non-operations;
- residual risks and recommended next mainline step.
