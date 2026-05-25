# P0 RawMaterial2CleanMaterial Third Canonical Sample Pilot Strict Preflight Task

Task ID: `TASK-20260525-143252-P0-RawMaterial2CleanMaterial-Third-Canonical-Sample-Pilot-Strict-Preflight`

Issued at: 2026-05-25T14:32:52+0800

Owner: Luceon

Baseline: `main@3630ccc777ef3b0dddfb791ef4e4e1e6c33f87fe`

## Mainline Objective

Determine whether the RawMaterial2CleanMaterial durable closed loop is stable
enough after two samples to justify a later bounded mini-batch pilot.

This task must run exactly one third canonical sample pilot with stricter
preflight gates than Task 285.

## Target Sample

- material: `589495534045014`
- task: `task-1779085091953`
- title: `出国`
- parsed ZIP: `eduassets-parsed/parsed/589495534045014/mineru-result.zip`
- extracted raw seed target:
  `eduassets-raw/mineru/589495534045014/v1/content_list_v2.json`
- raw seed SHA from read-only preflight:
  `6dc482285a6ad529497294fc96a0f31456155f33f082debb821f8d1a8bd8920a`
- raw seed size from read-only preflight: `5873`
- raw2clean candidate target:
  `eduassets-clean/raw-material-2-clean-material/589495534045014/v1/candidate.json`

## Critical Path Scope

Implement and execute the smallest third-sample harness needed to prove or
disprove repeatability:

1. read the target material/task metadata;
2. read the parsed ZIP and extract exactly one `_content_list_v2.json`;
3. prove the raw seed SHA/size before any CleanService POST;
4. put the raw seed only if missing and exact content is known;
5. submit at most one CleanService `toc-rebuild` job for this sample;
6. build the accepted CleanMaterial snapshot from verified artifacts;
7. build the raw2clean artifact-backed draft and output contract;
8. write exactly one raw2clean candidate artifact if missing or exact;
9. patch only `tasks/task-1779085091953` and `materials/589495534045014`;
10. verify product surface read-back for `/cms/asset/589495534045014`;
11. report the result and operation counts.

## Strict Preconditions

- Dry-run/preflight mode must not submit a CleanService job.
- Dry-run/preflight mode must not write DB or MinIO.
- Raw seed SHA and size must be established before any CleanService POST.
- If the target raw seed exists with different content, stop blocked.
- If the target raw2clean candidate exists with different content, stop blocked.
- If a CleanService job already exists for the chosen target job id in a
  non-completed state, stop blocked instead of choosing a new namespace.
- If the single allowed CleanService POST fails, stop blocked. Do not retry under
  a new asset version without a separate user decision.

## Allowed Operations

Only for the target sample:

- read-only DB GETs for the target task/material;
- read-only parsed ZIP GET;
- exact raw seed `putObject` to
  `eduassets-raw/mineru/589495534045014/v1/content_list_v2.json`;
- at most one CleanService `POST /api/v1/jobs`;
- CleanService job query polling for that one job;
- exact candidate `putObject` to
  `eduassets-clean/raw-material-2-clean-material/589495534045014/v1/candidate.json`;
- exactly two DB PATCHes:
  - `tasks/task-1779085091953`
  - `materials/589495534045014`;
- local product-surface verification.

## Forbidden Operations

- extra diagnostic MinIO writes;
- MinIO delete, copy, move, cleanup, bucket-wide scan, or broad listing;
- second CleanService POST or namespace recovery without separate approval;
- runtime POSTs other than the single authorized CleanService job POST;
- Docker/Compose restart/recreate/rebuild, volume mutation, or service mutation;
- job-store manual edit;
- source/sample/env/secret/model mutation;
- batch or multi-sample execution;
- final quality acceptance;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claim.

## Fast Validation Target

The task succeeds only if the third sample reaches:

```text
parsed ZIP -> raw seed -> CleanMaterial artifacts -> accepted CleanMaterial ->
raw2clean candidate -> durable candidate artifact -> accepted raw2clean decision
```

with no new code-shape fix, no failed CleanService namespace, no extra diagnostic
MinIO write, and no second POST.

## Stop Rule

Stop and report blocked if:

- dry-run would POST or write;
- raw seed SHA/size cannot be proven;
- target object conflict is detected;
- CleanService health or single job execution fails;
- artifact verifier rejects required outputs;
- raw2clean draft cannot be built without weakening source-reference rules;
- DB patch would embed full candidate content;
- product surface cannot discover/open the durable candidate after apply.

## Review Boundary

Acceptance means only that a third canonical sample pilot repeated the durable
raw2clean closed loop under stricter boundaries.

Acceptance does not mean final content quality acceptance, batch readiness,
runtime service readiness, production readiness, UAT, L3, pressure PASS, release
readiness, production online, or go-live.

