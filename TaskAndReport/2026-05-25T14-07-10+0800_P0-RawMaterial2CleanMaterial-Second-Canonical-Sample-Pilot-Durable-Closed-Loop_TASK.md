# P0 RawMaterial2CleanMaterial Second Canonical Sample Pilot Durable Closed Loop

Task ID: `TASK-20260525-140710-P0-RawMaterial2CleanMaterial-Second-Canonical-Sample-Pilot-Durable-Closed-Loop`

Created: 2026-05-25T14:07:10+0800

Owner: Luceon

Status: Open

## Mainline Objective

Verify repeatability of the RawMaterial2CleanMaterial closed loop on a second
canonical sample, without turning this into batch work or schema cleanup.

The first canonical sample proved:

```text
CleanMaterial v4 artifacts -> raw2clean candidate -> durable artifact ->
product surface -> accepted decision
```

This task must answer one narrow question:

Can the same closed loop be repeated on one additional small parsed material?

## Target Sample

Use the smallest suitable parsed candidate found by read-only DB/proxy
inspection:

- material: `2241872074049025`
- parse task: `task-1779085090677`
- title: `蓝月、血月、橙月？月亮为啥还会变色？`
- source parsed ZIP:
  `eduassets-parsed/parsed/2241872074049025/mineru-result.zip`

## Critical Path Scope

Allowed operations for this one sample:

1. Extract the existing `_content_list_v2.json` entry from the parsed ZIP.
2. Create or verify exactly one canonical raw seed object:
   `eduassets-raw/mineru/2241872074049025/v1/content_list_v2.json`.
3. Submit at most one CleanService `toc-rebuild` runtime job for this sample.
4. Verify seven `toc-rebuild` artifacts under:
   `eduassets-clean/toc-rebuild/2241872074049025/v1/`.
5. Build a raw2clean candidate from those artifacts.
6. Create or verify exactly one raw2clean candidate object:
   `eduassets-clean/raw-material-2-clean-material/2241872074049025/v1/candidate.json`.
7. Apply one combined durable metadata update to the one task and one material:
   - `tasks/task-1779085090677`
   - `materials/2241872074049025`
8. Verify read-back and product-surface visibility.

The DB metadata may include:

- `cleanServiceJobs.toc-rebuild`;
- `cleanMaterials.toc-rebuild` with `operatorDecision.state=accepted`;
- `rawMaterial2CleanMaterialJobs["raw-material-2-clean-material"]`;
- `rawMaterial2CleanMaterial.currentCandidate`;
- `rawMaterial2CleanMaterial.candidates.v1`;
- `rawMaterial2CleanMaterial.currentDecision`.

## True Preconditions

- The parsed ZIP must exist and contain exactly one usable
  `_content_list_v2.json` entry.
- Target raw seed and clean/candidate prefixes must be absent or already match
  the exact expected content.
- Runtime CleanService health must be available before POST.
- The job must complete and the seven CleanService artifact ObjectRefs must be
  readable before any DB metadata apply.
- Raw2clean candidate JSON SHA/size must be known before DB metadata apply.

## Deferrable Side Work

- batch/multi-sample automation;
- final quality scoring;
- repair/reject paths;
- generic schema migration;
- runtime worker scheduling;
- UI form expansion;
- cleanup of stale objects or failed attempts.

## Fast Validation Target

The task is successful only if:

- the second sample reaches `rawMaterial2CleanMaterial.currentDecision.state =
  accepted`;
- task and material metadata agree on the same CleanService job and raw2clean
  candidate ObjectRef/SHA;
- product surface shows `Decision: accepted` for
  `/cms/asset/2241872074049025`;
- all checks pass.

## Stop Rule

Stop and report blocked if:

- parsed ZIP extraction is ambiguous or missing;
- any target object exists with different content;
- CleanService health is unavailable;
- the single CleanService job fails or does not complete;
- required artifacts are missing or unreadable;
- metadata patch would affect any other material/task;
- the task needs a second runtime POST, Docker mutation, cleanup, batch scan, or
  schema migration.

## Review Boundary

Acceptance means only that a second canonical sample repeated the durable
closed loop. It does not mean final CleanMaterial quality acceptance, broad
batch readiness, UAT, L3, pressure PASS, release readiness, production
readiness, production online, or go-live.

## Forbidden Operations

- Docker/Compose rebuild/restart/recreate;
- MinIO delete/list-bucket cleanup/copy/move;
- writes outside the target raw seed, target CleanService output prefix, target
  raw2clean candidate object, and the two target DB records;
- second or batch CleanService POST;
- source/sample/env/secret/model mutation;
- readiness/go-live claims.

## Required Report

Write a report with:

- selected sample and why;
- exact real operation counts;
- raw seed SHA/size;
- CleanService job ID, artifact ObjectRefs/SHA/size;
- raw2clean candidate ObjectRef/SHA/size;
- DB affected IDs;
- product-surface evidence;
- check commands and exit codes;
- residual debt and next mainline recommendation.
