# TASK-20260525-133541-P0-RawMaterial2CleanMaterial-Durable-Candidate-Product-Surface-ReadOnly-NoRuntimeNoDBWriteNoMinIOWrite

Issued at: 2026-05-25T13:35:41+0800

Actor: Luceon

## Mainline Objective

Verify that the single-sample durable RawMaterial2CleanMaterial candidate from
Task 282 is product-visible: it can be discovered from material/task metadata,
opened by ObjectRef, and inspected read-only.

## Critical Path Scope

Build the smallest read-only product surface needed to expose the existing
candidate metadata on the material detail page.

Required:

- derive a narrow Raw2Clean candidate view from:
  - `material.metadata.rawMaterial2CleanMaterial`;
  - `task.metadata.rawMaterial2CleanMaterialJobs`;
- show candidate status, asset version, job id, ObjectRef, SHA/size, source
  Clean Material, source input, counts, and warning/boundary summary;
- reuse the existing proxy-file read pattern to open/preview the candidate JSON;
- provide focused read-only smokes and one canonical live read verification.

## True Preconditions

- Task 282 is closed on main.
- Canonical candidate ObjectRef exists:

```text
eduassets-clean/raw-material-2-clean-material/1842780526581841/v1/candidate.json
sha256=49a6189e12fe1c65ffdfbdf2e5b73d204c432002dff55812dc8c3be17ac2ce27
size_bytes=21767
```

## Environment And Write Boundary

Implementation workspace:

```text
/Users/concm/Dev_workspace/Luceon2026
```

Control-plane closure workspace:

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed runtime interaction:

- GET canonical material/task;
- GET exact candidate ObjectRef through upload proxy;
- browser/local UI preview if needed.

## Deferrable Side Work

Defer:

- operator approval workflow;
- DB/MinIO apply or correction;
- raw2clean runtime service;
- final quality acceptance;
- multi-sample/batch;
- broad design-system work.

## Stop Rule

Stop and report blocked if:

- candidate cannot be discovered from existing metadata;
- ObjectRef cannot be opened read-only;
- UI would require DB/MinIO writes, runtime POST, Docker/Compose mutation, broad
  workflow/approval changes, or batch work.

## Review Boundary

Acceptance means only:

```text
the durable single-sample raw2clean candidate is discoverable and inspectable
read-only from the product surface
```

Acceptance does not mean final Clean Material quality acceptance, approval
workflow readiness, runtime service readiness, UAT, L3, pressure PASS, release
readiness, production readiness, production online, or go-live.

## Allowed Files

- `src/app/utils/*rawMaterial2CleanMaterial*`
- a narrow component under `src/app/components/`
- minimal wiring in `src/app/pages/AssetDetailPage.tsx`
- focused smokes under `server/tests/`
- this task/report/ledger row under `TaskAndReport/`

## Forbidden Operations

- DB POST/PATCH/PUT/DELETE;
- MinIO put/copy/move/delete/list/bucket scan/cleanup;
- runtime POST/service execution/job submission;
- Docker/Compose build/up/down/restart/recreate/volume/network mutation;
- upload/retry/reparse/Re-AI/rollback/batch;
- source/sample/env/secret/model mutation;
- readiness/go-live/UAT/L3/pressure PASS claims.

## Acceptance Criteria

1. View helper discovers candidate from material and/or task metadata.
2. UI surface shows candidate identity and ObjectRef summary.
3. Candidate JSON can be opened/previewed through existing upload proxy URL.
4. Focused smoke covers material-only, task-only, conflict/missing, and URL
   generation behavior.
5. Canonical read-only verification GETs material/task/candidate and confirms
   SHA/size/counts.
6. `npx pnpm@10.4.1 exec tsc --noEmit` passes.
7. `npx pnpm@10.4.1 run build` passes, allowing only existing chunk-size
   warning.
8. `git diff --check origin/main...HEAD` passes.

## Required Report

Report changed files, exact checks and exit codes, canonical read-only evidence,
browser/UI verification if performed, and explicit confirmation that no DB,
MinIO, runtime, Docker, batch, or readiness boundary was crossed.
