# TASK-20260524-125020-P0-CleanService-PostTask259-ReadOnly-Revalidation-Target-Dossier

Issued at: 2026-05-24T12:50:20+0800

## 1. Mainline Objective

Task 259 accepted the mock-safe product fixes for the three Task 256 runner
integration gaps:

```text
live provenance response shape
-> explicit job_id -probe policy
-> explicit new-version apply dry-run conflict semantics
```

Before any new runtime dry-run, DB apply, or CleanService activation task is
issued, Luceon must decide which evidence target is safe and truthful:

- reuse or query existing Task 256 `v3` evidence;
- perform an idempotent same-job runtime reconciliation;
- run a new `v4` explicit new-version target;
- switch to a fresh canonical sample.

The mainline question is:

> What is the least-mutating, evidence-clean next validation target after Task
> 259, given existing `v2` accepted metadata and Task 256 `v3` diagnostic
> evidence?

## 2. Current Evidence

Current control-plane baseline:

```text
origin/main@09e5032f27800bf5f34e6a070cde5df321b53adb
```

Relevant accepted evidence:

- Task 245: standalone Mineru2Table single-sample `v2` success path completed
  with exactly seven required artifacts under
  `eduassets-clean/toc-rebuild/1842780526581841/v2/`; residual provenance
  `input size_bytes=0` was recorded.
- Task 253: read-only physical rehearsal confirmed current DB task/material
  metadata and MinIO `v2` artifacts align; runner safely blocked unintended
  new dispatch with `BLOCKED_EXISTING_TOC_REBUILD_METADATA`.
- Task 254: current applied `v2` noop policy accepted at code/test level.
- Task 255: explicit `create-new-version` mock-safe intent accepted at
  code/test level.
- Task 256: runtime single-sample explicit new-version dry-run was closed only
  as blocked diagnostic evidence because the harness reconstructed/promoted
  provenance shape, normalized provenance `job_id -probe`, and converted
  `BLOCKED_EXISTING_TOC_REBUILD_METADATA` into `DRY_RUN_SUCCESS`.
- Task 259: mock-safe product fixes for those three gaps were accepted at
  code/test level; no runtime rerun or DB apply was accepted.

Known fixed product behavior after Task 259:

- completed live-shaped job responses no longer need top-level
  `job.provenance`;
- `expectedJobId + "-probe"` is rejected by default/false and accepted only
  with explicit `allowProbeJobIdSuffix: true`;
- explicit new-version dry-run conflict semantics require
  `newVersionIntent.newAssetVersion` to match the target patch version and keep
  real apply/mismatch blocked.

## 3. Critical Path Scope

This is a Luceon read-only control/evidence task, not a Lucode business-code
implementation task.

Luceon must produce a target decision dossier that:

1. inventories the current accepted `v2` state and Task 256 `v3` diagnostic
   state;
2. identifies whether any existing `v3` evidence is reusable without mutation;
3. compares candidate next validation targets:
   - existing `v3` read-only verification only;
   - same `v3` idempotent submit/query;
   - new `v4` explicit new-version runtime dry-run;
   - fresh-sample runtime dry-run;
4. names the recommended next task shape and its safety boundary;
5. names not-recommended paths and why they would contaminate evidence or widen
   scope.

## 4. True Preconditions

Before reading live runtime/data evidence, Luceon must confirm:

- GitHub `main` is synchronized and the worktree is clean or only contains this
  task's report/ledger edits;
- Task 259 is closed on `origin/main`;
- the task can be completed using read-only commands and existing reports;
- any required DB or MinIO access is read-only and limited to the canonical
  sample / Task 256 evidence.

If the next target cannot be decided without POST, DB write, MinIO write/delete,
Docker/Compose mutation, env/secret mutation, cleanup, retry, reparse, or
runtime rerun, stop and write a blocked report.

## 5. Deferrable Side Work

Do not include:

- runtime POST or same-job submit;
- live Mineru2Table job query if it would mutate or enqueue work;
- real DB metadata apply;
- DB/MinIO cleanup, reset, rollback, overwrite, copy, move, or delete;
- Docker/Compose restart, recreate, rebuild, down/up, volume operation, or env
  change;
- upload-server scheduler/worker activation;
- operator UI work;
- RawMaterial2CleanMaterial planning or implementation;
- broader pressure, batch, UAT, L3, readiness, or go-live validation.

## 6. Environment And Write Boundary

Work in the Luceon workspace:

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed write files:

```text
TaskAndReport/2026-05-24T12-50-20+0800_P0-CleanService-PostTask259-ReadOnly-Revalidation-Target-Dossier_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Allowed read sources:

```text
TaskAndReport/TASK_TRACKING_LIST.md
TaskAndReport/2026-05-22T13-18-32+0800_P0-Mineru2Table-Single-Sample-Success-Path-Rerun-NewAssetVersion_REPORT.md
TaskAndReport/2026-05-22T21-28-10+0800_P0-CleanService-ReadOnly-Physical-Rehearsal-And-Existing-v2-Decision-Audit_REPORT.md
TaskAndReport/2026-05-23T08-47-13+0800_P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite_REPORT.md
TaskAndReport/2026-05-24T11-21-26+0800_P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite_LUCEON_REVIEW-v3.md
TaskAndReport/2026-05-24T12-39-29+0800_P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime_LUCEON_REVIEW-v2.md
server/services/cleanservice/**
server/tests/cleanservice-*.mjs
```

Conditionally allowed read-only runtime/data access:

```text
DB GET only for task/material records relevant to materialId 1842780526581841 and Task 256/245 evidence
MinIO stat/list/get only for eduassets-raw/mineru/1842780526581841/ and eduassets-clean/toc-rebuild/1842780526581841/
Mineru2Table job-store read-only inspection only if it can be done without editing jobs.json or restarting services
Existing container read-only exec only for GET/stat/list/read commands
```

Forbidden write files and operations:

```text
server/**
src/**
docs/**
docker-compose.yml
.env
.env.*
package.json
pnpm-lock.yaml
AGENTS.md
.agents/**
/Users/concm/prod_workspace/Mineru2Tables/**
```

The external Mineru2Table workspace is read-only for this task. Do not edit,
commit, push, restart, rebuild, deploy, or mutate it.

## 7. Safety Boundary

Strictly forbidden:

- `POST /api/v1/jobs`;
- `POST /api/v1/jobs:from-storage`;
- runtime submit-probe;
- DB PATCH/POST/PUT/DELETE;
- MinIO put/copy/move/delete/write/delete-marker operation;
- direct `jobs.json` write/edit;
- Docker/Compose restart/recreate/build/down/up/volume/prune;
- env/credential/model/sample-file mutation;
- cleanup/reset/rollback/repair/reparse/re-AI;
- worker/scheduler activation;
- real DB apply;
- UAT, L3, pressure PASS, production readiness, release readiness, production
  online, or go-live declaration.

Read-only observations must be labeled as read-only observations, not runtime
validation success.

## 8. Fast Validation Target

Minimum useful output:

1. a current-state table for `v2` accepted metadata/artifacts and Task 256 `v3`
   evidence;
2. a target-decision matrix comparing `v3 read-only`, `v3 idempotent
   reconciliation`, `v4 new-version`, and fresh sample;
3. a recommended next task type with exact authorization required;
4. a stop rule for the next task;
5. an explicit statement that this dossier itself did not perform runtime
   validation.

## 9. Required Checks

Run and record exact commands and exit codes for:

```bash
git status --short --branch
git fetch origin --prune --tags
git pull --ff-only origin main
git rev-parse HEAD origin/main
git diff --check
```

For any DB/MinIO/job-store read-only evidence, record:

- exact command or request shape;
- target task/material/job/prefix;
- exit code or HTTP status;
- whether the command was read-only;
- any skipped evidence and exact reason.

Do not run the Task 256 runtime harness, CleanService runtime POST, submit-probe,
or any mutation command.

## 10. Report Requirements

Create:

```text
TaskAndReport/2026-05-24T12-50-20+0800_P0-CleanService-PostTask259-ReadOnly-Revalidation-Target-Dossier_REPORT.md
```

The report must include:

- task id and baseline HEAD;
- evidence read list with paths/commands;
- current `v2` accepted state summary;
- Task 256 `v3` evidence summary and gaps;
- target decision matrix;
- recommended next task and exact authorization boundary;
- not-recommended paths;
- skipped checks with reasons;
- safety statement;
- residual risk.

## 11. Positive Acceptance Criteria

Luceon may accept this task when the report:

- cleanly separates accepted `v2` state, blocked Task 256 `v3` diagnostic
  evidence, and Task 259 mock-safe product fixes;
- recommends one next validation target with a narrow safety boundary;
- avoids declaring runtime success, readiness, pressure PASS, L3, or go-live;
- records enough evidence for a subsequent task brief to be written without
  rereading the whole history.

## 12. Negative Acceptance Criteria

Return or block the task if it:

- performs any POST, DB write, MinIO write/delete, Docker/env mutation, cleanup,
  retry, reparse, or real DB apply;
- treats Task 256 `DRY_RUN_SUCCESS` as accepted product-chain success;
- hides the `v2`/`v3` version collision risk;
- recommends cleanup or overwrite as the default route;
- widens into UI, scheduler, worker activation, RawMaterial2CleanMaterial, or
  pressure validation.

## 13. Stop Rule

Stop and report blocked if:

- the current data state cannot be read safely with read-only commands;
- the evidence is insufficient to choose a target without mutation;
- multiple target choices require user decision before a task can be scoped;
- any required command would expose secrets or mutate runtime/data state.

## 14. Review Boundary

Acceptance of this task will mean only:

```text
Luceon has selected or narrowed the safe next runtime-validation target after
Task 259 based on read-only evidence.
```

It will not mean:

- runtime dry-run success;
- DB apply acceptance;
- CleanService production activation;
- operator UI acceptance;
- UAT/L3/readiness/pressure PASS/go-live.
