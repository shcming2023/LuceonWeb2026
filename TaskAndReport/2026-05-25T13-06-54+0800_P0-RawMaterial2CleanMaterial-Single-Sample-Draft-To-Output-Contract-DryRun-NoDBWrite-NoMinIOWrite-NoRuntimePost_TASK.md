# TASK-20260525-130654-P0-RawMaterial2CleanMaterial-Single-Sample-Draft-To-Output-Contract-DryRun-NoDBWrite-NoMinIOWrite-NoRuntimePost

Issued at: 2026-05-25T13:06:54+0800

Actor: Luceon

## Mainline Objective

Move the RawMaterial2CleanMaterial path from "real artifacts can feed a draft"
to "the draft can become a deterministic output contract preview".

Task 280 proved the canonical accepted `toc-rebuild v4` sample can read real
artifact bodies and reach `MOCK_ALGORITHM_DRAFT_READY`. The next mainline
question is:

```text
Can one real artifact-backed draft become a deterministic raw2clean candidate
output preview, with source refs and provenance preserved, without writing DB,
MinIO, or runtime output?
```

This is still dry-run only. Do not implement durable output persistence,
runtime service execution, broad cleaning quality, or UI workflow.

## Critical Path Scope

Implement a narrow pure helper that converts an existing
`RawMaterial2CleanMaterialDraftOutput` into an in-memory candidate output
contract.

Required output shape:

- `kind`
- `contractVersion`
- `materialId`
- `taskId`
- `sourceCleanMaterial`
- `sourceInput`
- `sourceArtifacts`
- `sections`
- `blocks`
- `provenance`
- `warnings`
- deterministic output previews, including canonical JSON byte size and
  SHA-256
- boundary flags showing no DB, no MinIO writes, no runtime POST, and no durable
  artifact creation

The helper must preserve source references from the draft and must not invent
new source truth.

## True Preconditions

- Task 280 closed successfully.
- Canonical v4 artifact-backed draft reaches `MOCK_ALGORITHM_DRAFT_READY`.
- Current main at task issue: `51aa8f1cde510df8303701c005133aa33db8b484`.

Canonical single-sample target:

```text
materialId = 1842780526581841
taskId = task-1779085089451
serviceName = toc-rebuild
assetVersion = v4
jobId = luceon-task-1779085089451-toc-rebuild-v4
```

## Environment And Write Boundary

Implement in:

```text
/Users/concm/Dev_workspace/Luceon2026
```

Control-plane closure happens in:

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed runtime interaction is read-only only:

- GET canonical material record;
- GET canonical task record;
- GET exact required artifact ObjectRefs through the upload proxy.

## Deferrable Side Work

Defer:

- MinIO write of raw2clean output;
- DB metadata apply;
- raw2clean runtime endpoint/worker/service;
- UI workflow;
- final cleaning quality;
- multi-sample/batch;
- broad schema migration or cleanup.

## Fast Validation Target

Minimum proof:

```text
canonical accepted CleanMaterial v4
-> exact read-only artifact GETs
-> artifact-backed draft
-> raw2clean candidate output contract preview
-> deterministic SHA/size preview
```

## Stop Rule

Stop and report blocked if:

- the helper must invent source refs;
- the contract cannot preserve source input/artifact refs;
- canonical read-only rehearsal cannot reach the output preview;
- implementation would require DB writes, MinIO writes/list/delete, runtime
  POST, service execution, Docker, job-store edits, source asset mutation,
  model/env/secret mutation, or broad UI/workflow work.

## Review Boundary

Acceptance means only:

```text
one canonical artifact-backed draft can become a deterministic in-memory
raw2clean candidate output preview
```

Acceptance does not mean:

- durable raw2clean output exists;
- DB/MinIO apply is approved;
- runtime service exists;
- final content-cleaning quality is accepted;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live is approved.

## Allowed Files

Allowed implementation files:

- `src/app/utils/rawMaterial2CleanMaterialOutputContract.ts`
- narrow exports/imports in adjacent `rawMaterial2CleanMaterial*` utility files
  only if needed

Allowed tests:

- focused new smoke under `server/tests/`
- existing raw2clean focused smokes as regression checks

Allowed control-plane files:

- this report/task/ledger row under `TaskAndReport/`

## Forbidden Files And Operations

Forbidden files unless a separate task authorizes them:

- `server/upload-server.mjs`
- `server/db-server.mjs`
- `server/services/cleanservice/**`
- endpoint, worker, scheduler, transport, Docker, Compose, package, or service
  deployment files
- UI pages/components
- PRD/architecture docs
- local private role files: `AGENTS.md`, `.agents/**`

Forbidden operations:

- DB POST/PATCH/PUT/DELETE or apply;
- MinIO put/copy/move/delete/write/delete-marker/cleanup/list/bucket scan;
- runtime POST, submit-probe, Mineru2Table POST/query/probe, raw2clean service
  execution, or job submission;
- Docker/Compose build/up/down/restart/recreate/volume/prune/network mutation;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test;
- model, env, secret, sample, source asset, or local override mutation;
- production deployment or production validation;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claim.

## Acceptance Criteria

Positive acceptance:

1. A pure helper converts a draft into a candidate output contract preview.
2. The preview preserves material/task/sourceCleanMaterial/sourceInput/artifact
   refs.
3. Sections and blocks retain source refs.
4. Canonical JSON serialization is deterministic and has SHA-256 and byte-size
   preview.
5. Focused smoke proves the helper and blocks missing/invalid draft input.
6. Canonical read-only rehearsal reaches output preview.
7. Existing raw2clean focused smokes still pass.
8. `npx pnpm@10.4.1 exec tsc --noEmit` passes.
9. `npx pnpm@10.4.1 run build` passes, allowing only pre-existing chunk-size
   warnings.
10. `git diff --check origin/main...HEAD` passes.

Negative acceptance:

1. No DB write/apply or mutating DB method.
2. No MinIO write/delete/list/bucket scan.
3. No runtime POST, service execution, Docker/Compose operation, job-store edit,
   upload/retry/reparse/Re-AI/rollback, or batch action.
4. No final durable raw2clean output asset.
5. No invented source references.
6. No readiness/go-live/UAT/L3/pressure PASS language.

## Required Report

Luceon must report:

- branch name and exact full HEAD;
- changed files;
- implementation summary;
- exact commands and exit codes;
- focused smoke evidence;
- read-only canonical rehearsal evidence or exact blocked reason;
- output preview kind/version/SHA/size/counts;
- proof that no DB write, MinIO write/list/delete, runtime POST, Docker,
  job-store edit, source mutation, model/secret/env mutation, or readiness claim
  occurred;
- residual debt and recommended next mainline step.
