# TASK-20260524-163124-P0-CleanService-Existing-v4-Metadata-Apply-ExactlyTwoPatch-NoPost-NoMinIOWrite

Issued at: 2026-05-24T16:31:24+0800

Actor: Luceon

## Mainline Objective

Promote the already completed CleanService `toc-rebuild v4` runtime output from
external evidence into Luceon's durable product truth.

The stage breakthrough is:

```text
existing completed v4 job/artifacts
=> verifier accepts canonical v4 evidence
=> exactly two DB metadata PATCHes
=> task/material now point to accepted v4 Clean Material
=> no new POST and no MinIO write
```

This task exists to move the mainline from "v4 artifacts exist" to "Luceon
recognizes v4 as current Clean Material".

## Critical Path Scope

Use the existing runtime job and artifacts only:

```text
parseTaskId/task id = task-1779085089451
materialId = 1842780526581841
serviceName = toc-rebuild
previous accepted assetVersion = v2
previous accepted jobId = luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230
target assetVersion = v4
target jobId = luceon-task-1779085089451-toc-rebuild-v4
target prefix = eduassets-clean/toc-rebuild/1842780526581841/v4/
raw input = eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
raw input sha256 = f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
raw input size = 31543
```

## Director Authorization

The Director approved the stage-mainline analysis and instructed Luceon to
execute on 2026-05-24 after Task 266 completed.

This authorization is limited to the operations below and does not authorize a
new runtime job, broader product rollout, cleanup, or readiness claim.

## Authorized Operations

Allowed:

1. Git sync and TaskAndReport control-plane edits for this task.
2. Read-only DB/API reads for the exact target task/material before and after
   apply.
3. Read-only Mineru2Table job status/job-store inspection for the exact existing
   v4 job.
4. Read-only MinIO list/get/stat for:
   - the exact raw input object;
   - the existing target v4 artifact prefix.
5. Current product verifier, candidate builder, metadata persistence planner,
   and metadata apply executor.
6. Exactly two DB metadata PATCHes if and only if all preflight gates pass:
   - `PATCH /tasks/task-1779085089451`
   - `PATCH /materials/1842780526581841`
7. Post-apply DB reads to verify task/material now point to accepted `v4`.
8. Focused local checks needed to ensure the current product path is valid.

## Forbidden Operations

Forbidden:

- runtime POST, retry POST, submit-probe, or alternate endpoint POST;
- any new Mineru2Table job creation;
- MinIO put/copy/move/delete/write/delete-marker/cleanup;
- manual job-store edit/delete/cleanup/reset;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- env, credential, model, secret, source sample, or local override mutation;
- worker, scheduler, or upload-server CleanService activation;
- retry/reparse/re-AI/repair/rollback;
- source-code changes;
- batch processing, fresh sample selection, pressure test, UAT, L3, production
  readiness, release readiness, production online, or go-live claims.

## True Preconditions

Stop before DB PATCH if any gate fails:

1. GitHub `main` is synchronized.
2. Current DB task/material still have completed, aligned `toc-rebuild v2`
   accepted metadata.
3. Existing v4 job id is present and completed.
4. Existing v4 job status matches the target task/material and assetVersion.
5. Existing v4 prefix has exactly the seven required artifacts.
6. Raw input object exists and matches expected SHA256 and size.
7. Verifier accepts v4 artifacts with `allowProbeJobIdSuffix=false`.
8. Metadata candidate is persistable.
9. Persistence plan targets only the exact task/material metadata roots and
   proposes target v4 values.
10. Dry-run apply succeeds with `DRY_RUN_SUCCESS` and operation count 0 before
    real apply.

## Fast Validation Target

The task is successful when:

```text
preflight gates pass
dry-run apply succeeds with operationCount=0
real apply performs exactly two DB PATCHes
post-read task.cleanServiceJobs.toc-rebuild.assetVersion = v4
post-read material.cleanMaterials.toc-rebuild.latestVersion = v4
post-read task/material sourceInput and artifact refs match verified v4 evidence
```

## Acceptance Boundary

Success means the canonical single sample now has durable Luceon `toc-rebuild
v4` Clean Material metadata.

Success does not mean:

- broad CleanService automation is enabled;
- scheduler/worker activation is accepted;
- batch/pressure/UAT/L3/release/production readiness is accepted;
- RawMaterial2CleanMaterial is implemented;
- provenance `input.size_bytes=0` debt is fully fixed.

## Required Report

Write:

```text
TaskAndReport/2026-05-24T16-31-24+0800_P0-CleanService-Existing-v4-Metadata-Apply-ExactlyTwoPatch-NoPost-NoMinIOWrite_REPORT.md
```

The report must include:

- execution main SHA;
- exact preflight table;
- v4 job/artifact/verifier evidence;
- dry-run apply result;
- real DB apply result and exact PATCH count;
- post-apply DB evidence;
- skipped checks and reasons;
- boundary statement and residual risks;
- next recommendation focused on product visible read surface.
