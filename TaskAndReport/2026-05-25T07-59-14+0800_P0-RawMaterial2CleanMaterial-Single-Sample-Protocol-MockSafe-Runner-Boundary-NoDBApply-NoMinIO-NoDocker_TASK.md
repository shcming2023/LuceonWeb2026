# TASK-20260525-075914-P0-RawMaterial2CleanMaterial-Single-Sample-Protocol-MockSafe-Runner-Boundary-NoDBApply-NoMinIO-NoDocker

Issued at: 2026-05-25T07:59:14+0800

Actor: Lucode

## Mainline Objective

Move the current phase one step past the accepted input bundle without starting
or pretending to have a downstream service.

The mainline question for this task is:

```text
Can the accepted toc-rebuild v4 input bundle feed a minimal
RawMaterial2CleanMaterial request/response boundary and mock-safe dry-run runner?
```

This task must not build a real RawMaterial2CleanMaterial service, endpoint,
worker, DB apply path, MinIO output writer, Docker service, or production
readiness path.

## Critical Path Scope

Implement a pure, mock-safe single-sample boundary:

```text
accepted Clean Material input bundle
=> RawMaterial2CleanMaterial request object
=> mock-safe runner
=> dry-run result object
```

Required behavior:

1. Reuse the accepted input bundle shape from:

   ```text
   src/app/utils/rawMaterial2CleanMaterialInputBundle.ts
   ```

2. Define a minimal protocol object for the downstream request. It must be
   plain JSON and include:

   - stable kind, for example `raw-material-2-clean-material-request`;
   - mock protocol version, for example `v0.mock`;
   - mode `mock-dry-run`;
   - material id;
   - task id;
   - source clean service name `toc-rebuild`;
   - source asset version;
   - source job id;
   - source provenance object;
   - sourceInput object ref;
   - required artifact object refs;
   - accepted operator-decision state.

3. Implement a pure mock-safe runner that accepts either:

   - a successfully built input bundle; or
   - a request built from that bundle.

4. The runner must return a bounded dry-run result such as:

   ```text
   ok = true
   status = MOCK_DRY_RUN_SUCCESS
   classification = MOCK_DRY_RUN_SUCCESS
   ```

   and a small summary of:

   - what artifact roles would be read later;
   - what source clean material version/job would feed the downstream stage;
   - what output category would be produced later.

5. The runner must not include artifact body content. Object refs only.

6. The runner must use structured blocked results instead of throwing for
   expected invalid input.

Required blocked semantics include at least:

```text
MISSING_INPUT_BUNDLE
UNSUPPORTED_INPUT_KIND
UNSUPPORTED_MODE
CLEAN_MATERIAL_NOT_ACCEPTED
MISSING_REQUIRED_ARTIFACT
ARTIFACT_BODY_READ_REQUIRED
LIVE_DEPENDENCY_NOT_ALLOWED
```

Stable names may vary, but the behavior must be explicit in the report and
tests.

## True Preconditions

- Current `main` is the source of truth.
- Task 273 helper is accepted at code/test level.
- Task 274 confirms the persisted canonical sample can build the helper bundle
  from live-shaped read-only DB objects.
- Lucode must work in its normal development workspace and branch, then report
  through `TaskAndReport/`.

Canonical sample context for fixtures:

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

- real RawMaterial2CleanMaterial service algorithm;
- artifact body reading;
- MinIO artifact fetch/write/list;
- DB persistence of downstream results;
- UI launch button or operator workflow;
- worker/scheduler/endpoint integration;
- Docker/Compose service definition;
- batch processing and permissions/governance;
- quality scoring or output acceptance;
- production validation, readiness, and go-live language.

## Fast Validation Target

Fast validation is a focused smoke proving:

```text
accepted bundle fixture -> request -> mock runner -> MOCK_DRY_RUN_SUCCESS
```

The smoke must also prove invalid input blocks without live dependencies.

## Stop Rule

Stop and report blocked instead of widening scope if:

- request/runner implementation requires artifact body reads;
- implementation wants live DB reads or writes;
- implementation wants MinIO get/list/write/delete;
- implementation wants runtime POST, endpoint wiring, worker activation, or
  Docker/Compose changes;
- code changes need broad CleanService refactor or existing runtime path edits;
- product questions require deciding the real RawMaterial2CleanMaterial
  algorithm or persistence model.

## Review Boundary

Acceptance means only:

```text
the accepted input bundle can feed a minimal mock-safe downstream protocol and
dry-run runner boundary
```

Acceptance does not mean RawMaterial2CleanMaterial exists as a service, has run,
read artifact bodies, produced real output, wrote DB/MinIO, is production-ready,
or is approved for go-live.

## Allowed Files

Allowed implementation files:

- a focused pure module under `src/app/utils/`, for example:

  ```text
  src/app/utils/rawMaterial2CleanMaterialRunner.ts
  ```

- `src/app/utils/rawMaterial2CleanMaterialInputBundle.ts` only for narrow type
  exports or helper reuse needed by the runner;
- `src/store/types.ts` only if a narrow type addition is genuinely required.

Allowed tests/checks:

- a focused smoke test, for example:

  ```text
  server/tests/rawmaterial2cleanmaterial-protocol-runner-smoke.mjs
  ```

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

- request builder preserves bundle traceability fields;
- mock runner returns `MOCK_DRY_RUN_SUCCESS` for an accepted canonical-shaped
  bundle;
- result includes object-ref-only input summary and no artifact bodies;
- blocked results cover missing bundle, wrong kind/mode, non-accepted decision,
  missing required artifacts, body-shaped refs, and live dependency leakage;
- existing Task 273 helper smoke still passes;
- TypeScript/build checks pass.

Negative acceptance:

- no runtime endpoint, worker, service process, or transport is added;
- no DB or MinIO API is called in tests;
- no generated output artifact is written;
- no product UI or approval workflow is added;
- no readiness/go-live wording is introduced.

## Required Checks

Run and report exit codes:

```text
node server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs
node server/tests/rawmaterial2cleanmaterial-protocol-runner-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
git diff --check origin/main...HEAD
```

If a check is skipped, report the exact reason and residual risk.

## Required Report

Lucode report must include:

- exact branch and full HEAD;
- changed files;
- protocol/request shape summary;
- runner result shape summary;
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
