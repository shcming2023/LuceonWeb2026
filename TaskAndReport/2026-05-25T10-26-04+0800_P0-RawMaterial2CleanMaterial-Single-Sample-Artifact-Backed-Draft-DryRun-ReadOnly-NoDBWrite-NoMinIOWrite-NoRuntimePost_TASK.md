# TASK-20260525-102604-P0-RawMaterial2CleanMaterial-Single-Sample-Artifact-Backed-Draft-DryRun-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost

Issued at: 2026-05-25T10:26:04+0800

Actor: Lucode

## Mainline Objective

Break out of mock-only RawMaterial2CleanMaterial progress by proving the next
single-sample mainline step:

```text
accepted toc-rebuild v4 CleanMaterial metadata
+ read-only real artifact bodies
=> RawMaterial2CleanMaterial draft dry-run evidence
```

The mainline question for this task is:

```text
Can the accepted canonical CleanMaterial v4 sample feed the
RawMaterial2CleanMaterial draft skeleton from actual artifact ObjectRefs,
without writing DB/MinIO and without runtime POST?
```

This is a stage-breakthrough task. Do not spend the task on broad schema cleanup,
general workflow design, future production hardening, or another mock-only
helper unless it directly enables the read-only artifact-backed dry-run.

## Critical Path Scope

Implement the narrow composition needed for one artifact-backed draft dry-run:

1. Reuse the accepted helpers from:

   ```text
   src/app/utils/rawMaterial2CleanMaterialInputBundle.ts
   src/app/utils/rawMaterial2CleanMaterialRunner.ts
   src/app/utils/rawMaterial2CleanMaterialAlgorithm.ts
   ```

2. Add a focused read-only artifact-backed composition helper that can:

   - accept material/task objects or an already-built input bundle/request;
   - resolve only the required artifact body roles from ObjectRefs:

     ```text
     readable_tree
     logic_tree
     skeleton
     flooded_content
     ```

   - use an injected read-only artifact body reader for tests and integration;
   - pass the body map into `buildRawMaterial2CleanMaterialDraftSkeleton`;
   - return a structured dry-run result and evidence summary.

3. The helper must record which ObjectRefs were read and must not read optional
   artifacts unless explicitly required by the implementation.

4. Add a focused smoke test proving the composition boundary with a fake
   read-only reader:

   ```text
   accepted bundle/request + ObjectRef-backed required bodies
   => MOCK_ALGORITHM_DRAFT_READY
   ```

5. Produce a read-only canonical sample rehearsal if the local Luceon runtime is
   reachable:

   ```text
   materialId = 1842780526581841
   taskId = task-1779085089451
   serviceName = toc-rebuild
   assetVersion = v4
   jobId = luceon-task-1779085089451-toc-rebuild-v4
   ```

   The rehearsal may use only exact read-only GETs for the material, task, and
   required artifact ObjectRefs. It must not use POST/PATCH/PUT/DELETE, MinIO
   write/delete, Docker, job submission, or service execution.

6. If the local runtime or artifact bodies are not reachable, stop and report
   blocked with the exact failed read-only precondition. Do not replace the
   artifact-backed requirement with mock-only acceptance.

## True Preconditions

- `origin/main` is the source of truth.
- Task 267 durably promoted canonical `toc-rebuild v4` metadata.
- Task 272 persisted the accepted operator decision for the canonical sample.
- Task 273 accepted the accepted-CleanMaterial input bundle helper.
- Task 274 verified the live-shaped canonical material/task can build a bundle.
- Task 275 accepted the mock-safe request/runner boundary.
- Task 276 accepted the deterministic draft skeleton and numeric source-reference
  preservation fix.

Current main anchor at task issuance:

```text
main@115224f09339e04b11adf5033166f55ff01fbd10
```

## Environment And Write Boundary

Lucode works in:

```text
/Users/concm/Dev_workspace/Luceon2026
```

Allowed runtime interaction for this task is read-only only:

- `GET` the canonical material record;
- `GET` the canonical task record;
- `GET` exact artifact body objects referenced by the accepted v4 metadata.

The preferred artifact body path is the existing upload proxy resolver with
explicit bucket/object refs, for example:

```text
/__proxy/upload/proxy-file?bucket=eduassets-clean&object=<object>
```

Direct MinIO list/write/delete, service runtime POST, and DB mutation remain
forbidden.

## Deferrable Side Work

Defer:

- final RawMaterial2CleanMaterial cleaning quality;
- RawMaterial2CleanMaterial independent service repo/container;
- output asset writing to `eduassets-clean/raw2clean/...`;
- DB metadata persistence for raw2clean output;
- UI product surface for raw2clean results;
- operator decision persistence for raw2clean;
- generalized registry/worker/scheduler;
- multi-sample/batch support;
- cost governance UI;
- legacy migration, retention, cleanup, and release hardening.

## Fast Validation Target

Minimum useful proof:

```text
Task 273 live-shaped bundle
-> Task 275 request
-> read-only required artifact bodies
-> Task 276 draft skeleton
-> MOCK_ALGORITHM_DRAFT_READY
```

Expected evidence should include:

- material id, task id, service name, asset version, and job id;
- artifact roles read;
- artifact ObjectRefs read;
- draft status;
- section/block counts;
- sample source refs from real bodies;
- preservation of sourceInput and artifact hashes when present;
- explicit boundary flags showing no writes and no runtime POST.

## Stop Rule

Stop and report blocked instead of widening scope if:

- canonical material/task GETs fail or return incompatible shape;
- any required artifact ObjectRef is missing;
- any required artifact body cannot be read by exact read-only ref;
- the algorithm returns `MISSING_SOURCE_REFERENCE` or another blocked code on
  real artifact bodies;
- implementation would need DB writes, MinIO writes/deletes, runtime POST,
  Docker, worker/service execution, job-store edits, source asset mutation, or
  broad UI/workflow changes;
- the task starts turning into final content-cleaning quality work rather than
  an artifact-backed dry-run bridge.

## Review Boundary

Acceptance means only:

```text
one accepted canonical toc-rebuild v4 CleanMaterial can feed an
artifact-backed RawMaterial2CleanMaterial draft dry-run without writes or
runtime POST
```

Acceptance does not mean:

- final RawMaterial2CleanMaterial output exists;
- raw2clean DB/MinIO apply is approved;
- raw2clean service/runtime exists;
- content-cleaning quality is accepted;
- product UI is complete;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live is approved.

## Red Lines For Data Processing

1. ID-only / reference-backed extraction: source-derived draft items must keep
   stable Block IDs, node IDs, or source references when available.
2. Asset hash locking: sourceInput and artifact ObjectRef hashes from accepted
   metadata must be preserved, not rewritten.
3. Pure dry-run boundary: no final clean artifact, textbook content, custom
   LaTeX/TikZ, or generated teaching material may be emitted as durable output.

## Allowed Files

Allowed implementation files:

- focused pure helper/module under `src/app/utils/`, for example:

  ```text
  src/app/utils/rawMaterial2CleanMaterialArtifactBackedDraft.ts
  ```

- narrow edits to these existing helper files only if required:

  ```text
  src/app/utils/rawMaterial2CleanMaterialInputBundle.ts
  src/app/utils/rawMaterial2CleanMaterialRunner.ts
  src/app/utils/rawMaterial2CleanMaterialAlgorithm.ts
  ```

- `src/store/types.ts` only for narrow type additions if genuinely required.

Allowed tests:

- a focused smoke test, for example:

  ```text
  server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs
  ```

- existing focused smokes:

  ```text
  server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs
  server/tests/rawmaterial2cleanmaterial-protocol-runner-smoke.mjs
  server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs
  ```

Allowed control-plane files:

- Lucode report under `TaskAndReport/`;
- branch-local update to `TaskAndReport/TASK_TRACKING_LIST.md`.

## Forbidden Files And Operations

Forbidden files unless Luceon issues a separate task:

- `server/upload-server.mjs`
- `server/db-server.mjs`
- `server/services/cleanservice/**`
- endpoint, worker, scheduler, transport, Docker, or package files
- PRD/architecture docs
- UI pages/components
- local private role files: `AGENTS.md`, `.agents/**`

Forbidden operations:

- DB POST/PATCH/PUT/DELETE or apply;
- MinIO put/copy/move/delete/write/delete-marker/cleanup;
- MinIO list/bucket scan beyond exact ObjectRefs;
- runtime POST, submit-probe, Mineru2Table POST/query/probe, or raw2clean
  service execution;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test;
- model, env, secret, sample, source asset, or local override mutation;
- production deployment or production validation;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claim.

## Acceptance Criteria

Positive acceptance:

1. A focused helper composes accepted bundle/request, read-only required artifact
   body resolution, and draft skeleton generation.
2. Fake-reader smoke proves success and verifies that only allowed required
   ObjectRefs are read.
3. Existing Task 273, Task 275, and Task 276 focused smokes still pass.
4. If local runtime is reachable, the report includes canonical read-only
   artifact-backed evidence for material `1842780526581841` and task
   `task-1779085089451`.
5. If local runtime is not reachable, the report explicitly blocks on that
   precondition and does not claim artifact-backed success.
6. `npx pnpm@10.4.1 exec tsc --noEmit` passes.
7. `npx pnpm@10.4.1 run build` passes, allowing only pre-existing chunk-size
   warnings.
8. `git diff --check origin/main...HEAD` passes on the Lucode branch.

Negative acceptance:

1. No DB write/apply or mutating DB method.
2. No MinIO write/delete/list/bucket scan.
3. No runtime POST, service execution, Docker/Compose operation, job-store edit,
   upload/retry/reparse/Re-AI/rollback, or batch action.
4. No broad UI/workflow/registry/worker/service implementation.
5. No final raw2clean output asset or DB metadata persistence.
6. No readiness/go-live/UAT/L3/pressure PASS language.

## Required Report

Lucode must report:

- branch name and exact full HEAD;
- changed files;
- implementation summary;
- exact commands and exit codes;
- read-only canonical rehearsal evidence or explicit blocked reason;
- artifact roles and ObjectRefs read;
- draft summary counts and representative source refs;
- proof that no DB write, MinIO write, runtime POST, Docker, job-store edit,
  source mutation, model/secret/env mutation, or readiness claim occurred;
- residual debt and recommended next mainline step.

Lucode handoff must update the branch-local ledger row to:

```text
Status = Lucode 已回报待 Luceon 审查
Next Actor = Luceon
```

and push a remote branch matching:

```text
origin/lucode/*TASK-20260525-102604*
```

