# TASK-20260525-132001-P0-RawMaterial2CleanMaterial-Single-Sample-Durable-Candidate-Artifact-And-Metadata-Apply

Issued at: 2026-05-25T13:20:01+0800

Actor: Luceon

## Mainline Objective

Cross the RawMaterial2CleanMaterial durable boundary for exactly one canonical
sample. Task 281 proved the real artifact-backed draft can become a deterministic
in-memory candidate output contract. This task must prove the candidate can be
persisted as a durable, traceable single-sample artifact and recorded in DB
metadata without widening into runtime service, batch, UI, or readiness work.

## Critical Path Scope

Allowed durable operation:

```text
write exactly one raw2clean candidate JSON artifact
PATCH exactly the canonical task metadata
PATCH exactly the canonical material metadata
read back artifact and DB records for verification
```

Canonical target:

```text
materialId = 1842780526581841
taskId = task-1779085089451
source serviceName = toc-rebuild
source assetVersion = v4
raw2clean serviceName = raw-material-2-clean-material
raw2clean assetVersion = v1
raw2clean jobId = luceon-task-1779085089451-raw2clean-v1
target bucket = eduassets-clean
target object = raw-material-2-clean-material/1842780526581841/v1/candidate.json
```

The persisted metadata must be explicit that this is a candidate/draft output,
not accepted final Clean Material and not production readiness.

## True Preconditions

- Task 281 is closed on main.
- The canonical read-only rehearsal still reaches output contract preview.
- Existing target artifact should not be silently overwritten. If the target
  object already exists with different SHA, stop and report blocked.
- Existing DB metadata should not be silently overwritten if it points to a
  different raw2clean job/version/object. Stop and report blocked.

## Environment And Write Boundary

Implementation workspace:

```text
/Users/concm/Dev_workspace/Luceon2026
```

Control-plane closure workspace:

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed runtime writes:

- one MinIO `putObject` to `eduassets-clean/raw-material-2-clean-material/1842780526581841/v1/candidate.json`;
- one DB `PATCH /tasks/task-1779085089451`;
- one DB `PATCH /materials/1842780526581841`.

Allowed runtime reads:

- GET canonical material/task records;
- GET exact required source clean artifacts;
- stat/GET the exact target candidate object;
- GET canonical material/task after PATCH for verification.

## Deferrable Side Work

Defer:

- raw2clean runtime endpoint/worker/service;
- operator approval UI for raw2clean;
- final content-cleaning quality;
- multi-sample/batch;
- schema migration;
- cleanup of candidate drafts;
- production readiness, UAT, L3, pressure, release, or go-live work.

## Fast Validation Target

Minimum proof:

```text
accepted toc-rebuild v4 artifacts
-> artifact-backed draft
-> output contract preview
-> one durable candidate JSON ObjectRef
-> task/material metadata ObjectRef points to that artifact
-> read-back SHA/size match the generated preview
```

## Stop Rule

Stop and report blocked if:

- canonical draft/output preview cannot be regenerated;
- source artifact SHA checks fail;
- target object exists with different SHA;
- DB metadata already contains incompatible raw2clean candidate state;
- metadata patch would embed full candidate JSON content rather than ObjectRef
  summaries;
- more than one artifact write or more than two DB PATCHes would be needed;
- implementation requires runtime POST, Docker/Compose mutation, job-store edit,
  source/sample/env/secret/model mutation, broad service changes, UI, batch, or
  readiness claims.

## Review Boundary

Acceptance means only:

```text
one canonical raw2clean candidate output is durably materialized and traceably
referenced by task/material metadata
```

Acceptance does not mean:

- final Clean Material quality is accepted;
- operator approval workflow exists;
- raw2clean runtime service exists;
- multi-sample/batch is validated;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live is approved.

## Allowed Files

Implementation:

- a narrow server-side helper or controlled script under `server/services/` or
  `server/tests/`;
- focused tests under `server/tests/`;
- narrow imports/exports needed by existing raw2clean helpers.

Control plane:

- this task, report, and ledger row under `TaskAndReport/`.

## Forbidden Files And Operations

Forbidden files unless separately authorized:

- `server/upload-server.mjs`
- `server/db-server.mjs`
- endpoint, worker, scheduler, transport, Docker, Compose, package, or
  deployment files
- UI pages/components
- PRD/architecture docs
- local private role files: `AGENTS.md`, `.agents/**`

Forbidden operations:

- any object write except the single target candidate JSON;
- any MinIO delete/list/bucket scan/copy/move/cleanup;
- any DB write except the two exact PATCHes above;
- runtime POST, submit-probe, service job submission, Mineru2Table query/probe,
  raw2clean service execution, upload/retry/reparse/Re-AI/rollback, batch;
- Docker/Compose build/up/down/restart/recreate/volume/prune/network mutation;
- model/env/secret/source sample mutation;
- production deployment;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claim.

## Acceptance Criteria

Positive acceptance:

1. Durable helper/script has explicit one-sample gates for material/task/version
   and exact target ObjectRef.
2. Candidate JSON written once to the allowed ObjectRef, or idempotently
   confirmed if the exact same SHA already exists.
3. Task/material metadata are patched with ObjectRef summary only.
4. Metadata records candidate/draft status, source clean material, source input,
   source artifact refs, section/block/sourceRef counts, preview SHA/size, and
   boundary/audit timestamps.
5. Read-back verification proves target object SHA/size and DB ObjectRefs match.
6. Focused non-mutating smoke covers planning/blocking behavior.
7. Existing raw2clean focused smokes still pass.
8. `npx pnpm@10.4.1 exec tsc --noEmit` passes.
9. `npx pnpm@10.4.1 run build` passes, allowing only existing chunk-size warning.
10. `git diff --check origin/main...HEAD` passes.

Negative acceptance:

1. No more than one MinIO object write.
2. No more than two DB PATCHes.
3. No MinIO delete/list/bucket scan/copy/move/cleanup.
4. No runtime POST, service execution, Docker/Compose mutation, job-store edit,
   upload/retry/reparse/Re-AI/rollback, batch, model/env/secret/source mutation.
5. No full candidate JSON embedded in DB metadata.
6. No readiness/go-live/UAT/L3/pressure PASS language.

## Required Report

Report:

- branch and exact HEAD;
- changed files;
- exact durable ObjectRef, SHA, and size;
- exact DB metadata paths patched;
- pre/post verification evidence;
- commands and exit codes;
- confirmation of operation counts;
- residual debt and next mainline step.
