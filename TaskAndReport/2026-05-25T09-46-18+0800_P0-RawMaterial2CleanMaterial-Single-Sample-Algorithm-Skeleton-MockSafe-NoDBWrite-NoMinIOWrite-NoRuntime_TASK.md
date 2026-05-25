# TASK-20260525-094618-P0-RawMaterial2CleanMaterial-Single-Sample-Algorithm-Skeleton-MockSafe-NoDBWrite-NoMinIOWrite-NoRuntime

Issued at: 2026-05-25T09:46:18+0800

Actor: Lucode

## Mainline Objective

Move the current RawMaterial2CleanMaterial bridge from protocol-only into the
smallest visible transformation skeleton.

The mainline question for this task is:

```text
Can one accepted toc-rebuild v4 request plus injected mock artifact bodies
produce a bounded, traceable RawMaterial2CleanMaterial draft output shape?
```

This task must not build the real service, read MinIO, write DB/MinIO, launch a
runtime, or claim output quality/readiness. It is a deterministic algorithm
skeleton only.

## Critical Path Scope

Implement a pure mock-safe algorithm skeleton:

```text
RawMaterial2CleanMaterial mock request
+ injected mock artifact bodies
=> traceable draft output object
```

Required behavior:

1. Reuse the accepted Task 275 request shape from:

   ```text
   src/app/utils/rawMaterial2CleanMaterialRunner.ts
   ```

2. Add a pure algorithm skeleton that accepts:

   - a `raw-material-2-clean-material-request`;
   - an injected in-memory artifact body map or reader object;
   - optional clock/options for deterministic tests.

3. Produce a plain JSON draft object with stable shape, for example:

   ```text
   kind = raw-material-2-clean-material-draft
   protocolVersion = v0.mock
   status = MOCK_ALGORITHM_DRAFT_READY
   materialId
   taskId
   source service/version/job/provenance refs
   input artifact refs
   extracted section/block summaries with source block ids where present
   quality flags / warnings
   output persistence plan = none
   ```

4. The skeleton may parse only injected mock artifact bodies in tests. It must
   not fetch, list, stream, or read live artifacts.

5. The skeleton must preserve traceability:

   - every extracted item that comes from `flooded_content`, `skeleton`, or
     similar structured sources must carry a source block id, node id, or source
     reference when available;
   - do not invent source text or untraceable facts;
   - preserve source ObjectRefs and hashes from the request.

6. Use structured blocked results instead of throwing for expected invalid
   input.

Required blocked semantics include at least:

```text
MISSING_REQUEST
UNSUPPORTED_REQUEST_KIND
UNSUPPORTED_MODE
MISSING_ARTIFACT_BODY
INVALID_ARTIFACT_BODY
MISSING_SOURCE_REFERENCE
LIVE_DEPENDENCY_NOT_ALLOWED
```

Stable names may vary if the behavior is explicit in tests and report.

## True Preconditions

- Current `main` is the source of truth.
- Task 273 accepted the input bundle helper.
- Task 274 verified the persisted canonical sample can build the input bundle
  from live-shaped read-only DB objects.
- Task 275 accepted the mock-safe request/runner boundary.
- Lucode must work in its normal development workspace and report through
  `TaskAndReport/`.

Canonical single-sample context for fixtures:

```text
materialId = 1842780526581841
taskId = task-1779085089451
serviceName = toc-rebuild
assetVersion = v4
jobId = luceon-task-1779085089451-toc-rebuild-v4
```

Fixtures may use this shape, but implementation must not hard-code this as the
only usable code path.

## Deferrable Side Work

Defer:

- real RawMaterial2CleanMaterial cleaning algorithm;
- LLM/VLM/model calls;
- MinIO artifact body reading or output writing;
- DB persistence of draft or final output;
- service endpoint, worker, scheduler, or Docker service;
- UI launch or operator review workflow;
- batch/multi-sample processing;
- quality scoring policy beyond simple skeleton warnings;
- production validation, readiness, and go-live language.

## Fast Validation Target

Fast validation is a focused smoke proving:

```text
mock request + injected readable_tree / logic_tree / skeleton / flooded_content
=> MOCK_ALGORITHM_DRAFT_READY
```

The smoke must also prove invalid input blocks without live dependencies.

## Stop Rule

Stop and report blocked instead of widening scope if:

- the skeleton needs live DB reads or writes;
- the skeleton needs MinIO get/list/write/delete;
- the skeleton needs runtime POST, endpoint wiring, worker activation, Docker,
  or service-process code;
- algorithm design becomes a broad content-cleaning or AI-quality problem;
- output persistence or UI workflow decisions become necessary;
- extracting content would require inventing source truth without source ids or
  source references.

## Review Boundary

Acceptance means only:

```text
a single accepted mock request can produce a deterministic, traceable draft
output skeleton from injected mock artifact bodies
```

Acceptance does not mean the real RawMaterial2CleanMaterial algorithm exists,
has read live artifacts, has written output, is product-quality, is production
ready, or is approved for go-live.

## Red Lines For Data Processing

These red lines are part of the task scope:

1. ID-only / reference-backed extraction: extracted source content must preserve
   stable Block IDs, node IDs, or source references when available.
2. Asset hash locking: source ObjectRefs and hashes from the request must be
   preserved and not rewritten.
3. Pure generation boundary: do not emit final textbook/layout/code artifacts,
   custom LaTeX/TikZ, or generated teaching content beyond the bounded draft
   skeleton.

## Allowed Files

Allowed implementation files:

- a focused pure module under `src/app/utils/`, for example:

  ```text
  src/app/utils/rawMaterial2CleanMaterialAlgorithm.ts
  ```

- `src/app/utils/rawMaterial2CleanMaterialRunner.ts` only for narrow type reuse
  or a mock-safe call path into the new skeleton;
- `src/app/utils/rawMaterial2CleanMaterialInputBundle.ts` only for narrow type
  exports if genuinely needed;
- `src/store/types.ts` only if a narrow type addition is genuinely required.

Allowed tests/checks:

- a focused smoke test, for example:

  ```text
  server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs
  ```

- existing focused smokes for Task 273 and Task 275 should continue to run.

Allowed control-plane files:

- Lucode report under `TaskAndReport/`;
- branch-local update to `TaskAndReport/TASK_TRACKING_LIST.md`.

## Forbidden Files And Operations

Forbidden files unless Luceon issues a separate task:

- `server/upload-server.mjs`
- `server/db-server.mjs`
- `server/services/cleanservice/**`
- RawMaterial2CleanMaterial endpoint/worker/transport/runtime service files
- package files
- Docker/Compose files
- PRD/architecture docs
- UI pages/components
- local private role files: `AGENTS.md`, `.agents/**`

Forbidden operations:

- live DB read/write for validation;
- DB POST/PATCH/PUT/DELETE or apply;
- MinIO get/list/put/copy/move/delete/write/delete-marker/cleanup;
- CleanService runtime run;
- RawMaterial2CleanMaterial real execution, transport, endpoint, worker,
  scheduler, or Docker service;
- Mineru2Table POST/query/probe;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test;
- model, env, secret, sample, source asset, or local override mutation;
- production deployment or production runtime validation;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claim.

## Acceptance Criteria

Positive acceptance:

- algorithm skeleton accepts a Task 275 request and injected artifact bodies;
- draft output shape is stable, plain JSON, and traceable to request refs;
- source-derived items include source ids/references when available;
- request ObjectRefs and hashes are preserved;
- draft declares no persistence/output write plan;
- blocked results cover missing request, wrong kind/mode, missing/invalid body,
  missing source references, and live dependency markers;
- Task 273 and Task 275 focused smokes still pass;
- TypeScript/build checks pass.

Negative acceptance:

- no runtime endpoint, worker, service process, or transport is added;
- no DB or MinIO API is called in tests;
- no generated output artifact is written;
- no product UI or approval workflow is added;
- no broad AI/LLM quality algorithm is introduced;
- no readiness/go-live wording is introduced.

## Required Checks

Run and report exit codes:

```text
node server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs
node server/tests/rawmaterial2cleanmaterial-protocol-runner-smoke.mjs
node server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
git diff --check origin/main...HEAD
```

If a check is skipped, report the exact reason and residual risk.

## Required Report

Lucode report must include:

- exact branch and full HEAD;
- changed files;
- algorithm skeleton input/output shape summary;
- sample draft summary;
- blocked-code coverage;
- commands run with exit codes;
- explicit statement that no DB/MinIO/runtime/Docker/production operation was
  performed;
- residual debt and next recommended mainline step.

Branch-local ledger row must be updated to:

```text
Status = Lucode 已回报待 Luceon 审查
Next Actor = Luceon
```

when the task is complete.
