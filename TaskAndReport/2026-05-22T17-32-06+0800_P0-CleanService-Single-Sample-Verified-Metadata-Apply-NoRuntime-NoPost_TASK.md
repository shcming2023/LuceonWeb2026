# TASK-20260522-173206-P0-CleanService-Single-Sample-Verified-Metadata-Apply-NoRuntime-NoPost

## 1. Mainline Objective

Build the next narrow implementation slice after Task 250.

Task 250 proved that Luceon can construct a dry-run, shallow-merge-safe
metadata persistence plan for verified Mineru2Table `toc-rebuild` output.

Task 251 must answer the next mainline question:

> Can Luceon safely apply one verified `toc-rebuild` metadata plan into the real
> Luceon DB for one known sample, without activating CleanService runtime,
> dispatching Mineru2Table, reading/writing MinIO, calling LLMs, or changing
> Docker/env state?

Director authorization for this task:

```text
Allow exactly one controlled real Luceon DB metadata write for Task 251.
```

This is not an authorization for production readiness, worker activation,
automatic scheduling, MinIO cleanup, or broad migration.

## 2. Current Evidence

Accepted evidence on current `main`:

- Current Luceon main after Task 250 acceptance:
  `102927b4667b27bfb1b36ef475c63a84b8ba3e06`.
- Task 245 produced a successful standalone Mineru2Table `v2` run for:

  ```text
  materialId=1842780526581841
  assetVersion=v2
  jobId=luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230
  ```

- Task 240 identified the canonical parse task:

  ```text
  parseTaskId=task-1779085089451
  ```

- Task 245 verified the canonical raw input:

  ```text
  bucket=eduassets-raw
  object=mineru/1842780526581841/v1/content_list_v2.json
  sizeBytes=31543
  sha256=f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
  ```

- Task 245 verified exactly seven `v2` output artifacts under:

  ```text
  eduassets-clean/toc-rebuild/1842780526581841/v2/
  ```

- Task 246 accepted the `v2` output threshold for minimal orchestration
  planning, while preserving the provenance `input size_bytes=0` residual as a
  visible warning/debt.
- Task 248 accepted seven-artifact verifier code/test level.
- Task 249 accepted verified-output metadata candidate code/test level.
- Task 250 accepted dry-run persistence payload planner code/test level.

Current code gap:

- No code path has applied the verified CleanService metadata plan to the real
  Luceon DB.
- Real DB shallow-merge behavior has not yet been verified for the `toc-rebuild`
  task/material metadata branches.

## 3. Critical Path Scope

Implement only the single-sample metadata apply layer and run it once under
explicit confirmation.

The task may add:

1. a small metadata apply executor that accepts a Task 250 plan and an injected
   DB client;
2. a focused mock smoke test for the executor;
3. a controlled single-sample script that performs read-only preflight, builds
   the accepted Task 245-shaped candidate/plan, applies exactly two DB PATCHes
   only after all gates pass, then performs read-only post-check.

The real apply target is fixed:

```text
materialId=1842780526581841
parseTaskId=task-1779085089451
assetVersion=v2
jobId=luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230
serviceName=toc-rebuild
```

Do not generalize to batch apply, worker apply, UI apply, or arbitrary material
selection in this task.

## 4. True Preconditions

Before any DB PATCH, the controlled script must prove all preflight gates:

1. DB endpoint is reachable by exact `GET /tasks/:id` and
   `GET /materials/:id`.
2. The exact parse task exists:

   ```text
   /tasks/task-1779085089451
   ```

3. The exact material exists:

   ```text
   /materials/1842780526581841
   ```

4. Neither record has an incompatible existing `metadata.cleanServiceJobs`
   or `metadata.cleanMaterials` `toc-rebuild` branch.
   - If the exact same jobId and assetVersion are already present on both
     records, stop with `ALREADY_APPLIED_NOOP` and do not write.
   - If a different `toc-rebuild` branch is present, stop with
     `BLOCKED_EXISTING_TOC_REBUILD_METADATA`.
5. The candidate built from Task 245 evidence must produce
   `plan.ok=true` and `plan.shouldApply=true`.
6. The generated patches must contain only `metadata`.
7. The generated patches must include:
   - source input bucket/object/sha256/size;
   - seven artifact ObjectRefs;
   - non-zero tokens;
   - cost summary including `costCnyActual=0.0`;
   - `input-size-bytes-zero` warning.
8. The generated patches must not include full artifact contents.

If any preflight gate fails, stop and report the specific blocked
classification. Do not patch the DB.

## 5. Environment And Write Boundary

Work in:

```text
/workspace/dev/Luceon2026
```

Allowed source files:

```text
server/services/cleanservice/metadata-apply-executor.mjs        # new narrow module
server/tests/cleanservice-metadata-apply-executor-smoke.mjs     # new focused mock smoke
scripts/cleanservice-task251-single-sample-apply.mjs            # new controlled script
TaskAndReport/2026-05-22T17-32-06+0800_P0-CleanService-Single-Sample-Verified-Metadata-Apply-NoRuntime-NoPost_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Read-only unless a stop rule proves a narrow edit is required:

```text
server/services/cleanservice/metadata-persistence.mjs
server/services/cleanservice/metadata-summary.mjs
server/services/tasks/task-client.mjs
server/db-server.mjs
```

Forbidden files and areas:

```text
server/services/cleanservice/cleanservice-worker.mjs
server/services/cleanservice/protocol.mjs
server/services/cleanservice/worker-factory.mjs
server/services/cleanservice/http-transport.mjs
server/services/cleanservice/config.mjs
server/upload-server.mjs
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

Do not edit external Mineru2Table code in this task.

## 6. Authorized Runtime Boundary

This task authorizes exactly these real DB operations, only after all preflight
gates pass:

```text
GET   /tasks/task-1779085089451
GET   /materials/1842780526581841
PATCH /tasks/task-1779085089451        # at most once
PATCH /materials/1842780526581841      # at most once
GET   /tasks/task-1779085089451
GET   /materials/1842780526581841
```

No other real runtime operations are authorized.

Forbidden runtime operations:

- `POST /api/v1/jobs`;
- `POST /api/v1/jobs:from-storage`;
- any DeepSeek/LLM call;
- any MinIO read/write/list/delete/stat;
- any Docker/Compose command;
- any `.env` or credential mutation;
- any worker/scheduler activation;
- any DB delete, bulk patch, task create, material create, or top-level status
  rewrite;
- any cleanup, rollback, or repair action after a failed apply unless Luceon
  explicitly authorizes it later.

## 7. Required Single-Sample Metadata

The controlled script must build its candidate from the accepted Task 245/246
evidence, not from live MinIO reads.

### 7.1 Raw Input

```js
{
  bucket: 'eduassets-raw',
  object: 'mineru/1842780526581841/v1/content_list_v2.json',
  sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
  sizeBytes: 31543
}
```

### 7.2 Output Artifacts

Use bucket `eduassets-clean` and these ObjectRefs:

| Role | Object | Size | SHA256 |
| --- | --- | ---: | --- |
| `flooded_content` | `toc-rebuild/1842780526581841/v2/flooded_content.json` | `20054` | `e1a8355a80a5014b5a616ed441a4d0851c47d6a3d6092711ce765ffe11eea7b7` |
| `logic_tree` | `toc-rebuild/1842780526581841/v2/logic_tree.json` | `375` | `b61ee669b63bccb597f9ff31e5773ac1cc53a7bf6d6ef7a5ba73d467c7267665` |
| `readable_tree` | `toc-rebuild/1842780526581841/v2/readable_tree.md` | `106` | `bba5cf360fa7c0d92a9489ce84dfc40458de6072f812d7ab5d381b8e828946d7` |
| `skeleton` | `toc-rebuild/1842780526581841/v2/skeleton.json` | `21160` | `c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e` |
| `unresolved_anchors` | `toc-rebuild/1842780526581841/v2/unresolved_anchors.json` | `2` | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| `metrics` | `toc-rebuild/1842780526581841/v2/metrics.json` | `129` | `add72cb0a0c0dcb2fe051961795da8c151181022df79770583d5fb75c7ed9718` |
| `provenance` | `toc-rebuild/1842780526581841/v2/provenance.json` | `2108` | `4762b30f5ab344b1eec0a46b4541b9fa1df314ca756eb837b4622b43169104eb` |

### 7.3 Stats And Warnings

```js
{
  tokensPrompt: 6212,
  tokensCompletion: 54,
  tokensTotal: 6266,
  costCnyEstimated: 0.006319999999999999,
  costCnyActual: 0.0,
  unresolvedAnchorCount: 0,
  warnings: ['input-size-bytes-zero']
}
```

## 8. Required Apply Executor Behavior

The executor must support injected DB clients for tests.

Suggested API shape:

```js
await applyCleanMetadataPersistencePlan({
  plan,
  taskId: 'task-1779085089451',
  materialId: '1842780526581841',
  dbClient,
  allowRealApply: false,
});
```

Behavior requirements:

- If `allowRealApply !== true`, do not call update methods.
- If `plan.shouldApply !== true`, do not call update methods.
- If `taskPatch` or `materialPatch` contains keys outside `metadata`, block
  with `BLOCKED_PATCH_SCOPE_VIOLATION`.
- If either patch contains full artifact content fields, block with
  `BLOCKED_FULL_CONTENT_IN_METADATA`.
- If applying, call exactly:
  - `dbClient.updateTask(taskId, plan.taskPatch)`;
  - `dbClient.updateMaterial(materialId, plan.materialPatch)`.
- Return the attempted operation count and per-call result.
- If the first patch succeeds and the second fails, stop with
  `PARTIAL_DB_APPLY_REQUIRES_LUCEON_REVIEW`; do not attempt rollback.

## 9. Stop Rules

Stop and report `BLOCKED_DB_TARGET_NOT_FOUND` if the exact task or material is
missing.

Stop and report `BLOCKED_EXISTING_TOC_REBUILD_METADATA` if an incompatible
existing `toc-rebuild` branch is already present.

Stop and report `ALREADY_APPLIED_NOOP` if both task and material already contain
the exact same `toc-rebuild` jobId and assetVersion. Do not write.

Stop and report `BLOCKED_PLAN_NOT_APPLYABLE` if Task 250 planner returns
`shouldApply=false`.

Stop and report `BLOCKED_PATCH_SCOPE_VIOLATION` if the patch would modify
anything outside `metadata`.

Stop and report `BLOCKED_FULL_CONTENT_IN_METADATA` if the patch contains full
artifact contents.

Stop and report `PARTIAL_DB_APPLY_REQUIRES_LUCEON_REVIEW` if only one of the two
authorized PATCHes succeeds.

Stop and report `BLOCKED_SCOPE_WOULD_EXPAND` if this task appears to require
worker wiring, upload-server changes, Docker/env mutation, MinIO reads, or any
additional material/task.

## 10. Positive Acceptance Criteria

Luceon will accept this task if:

- only allowed files are changed;
- executor has mock smoke coverage for no-apply, successful apply, scope
  violation, non-applyable plan, and partial apply failure;
- controlled script preflights the exact task and material;
- exactly zero or two PATCHes occur:
  - zero only for `ALREADY_APPLIED_NOOP`;
  - two for the intended first successful apply;
- post-read proves task metadata contains `cleanServiceJobs.toc-rebuild`;
- post-read proves material metadata contains `cleanMaterials.toc-rebuild`;
- existing unrelated metadata branches are preserved;
- sourceInput bucket/object/sha256/size are present after read-back;
- seven artifact ObjectRefs are present after read-back;
- tokens and cost summary are present after read-back, including
  `costCnyActual=0.0`;
- `input-size-bytes-zero` warning remains visible after read-back;
- no full artifact content is written;
- report includes before/after bounded metadata evidence and exact call count.

## 11. Negative Acceptance Criteria

Luceon will reject or return the task if it:

- sends any Mineru2Table job POST;
- calls DeepSeek/LLM;
- reads, writes, lists, stats, deletes, or cleans MinIO;
- changes Docker/Compose/env/credentials;
- activates worker/scheduler behavior;
- modifies top-level task/material state outside metadata;
- touches a material other than `1842780526581841`;
- touches a task other than `task-1779085089451`;
- performs DB delete, create, or bulk-patch;
- attempts rollback/cleanup after a partial failure without Luceon permission;
- stores full artifact content in metadata;
- claims UAT, L3, production readiness, pressure PASS, release readiness, or
  go-live.

## 12. Required Checks

Run and report exact commands and exit codes:

```bash
node --check server/services/cleanservice/metadata-apply-executor.mjs
node --check scripts/cleanservice-task251-single-sample-apply.mjs
node --check server/tests/cleanservice-metadata-apply-executor-smoke.mjs
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
node server/tests/cleanservice-metadata-persistence-smoke.mjs
node server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
git diff --check origin/main..HEAD
git diff --name-status origin/main..HEAD
```

Then run the controlled apply exactly once, with an explicit confirmation
environment variable. The script may choose its final confirmation variable, but
it must require a value at least as specific as:

```bash
TASK251_ALLOW_REAL_DB_WRITE=true \
TASK251_CONFIRM_TARGET=1842780526581841:task-1779085089451:luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230 \
node scripts/cleanservice-task251-single-sample-apply.mjs
```

If the DB endpoint requires a non-default `DB_BASE_URL`, pass it through the
environment without writing it into `.env` or committing it.

## 13. Report Requirements

Create:

```text
TaskAndReport/2026-05-22T17-32-06+0800_P0-CleanService-Single-Sample-Verified-Metadata-Apply-NoRuntime-NoPost_REPORT.md
```

The report must include:

- final branch and HEAD;
- exact changed file list;
- exact DB endpoint label used, without secrets;
- before bounded task/material metadata snapshots for the affected branches;
- preflight gate results;
- exact generated plan summary;
- exact PATCH count and endpoint paths;
- after bounded task/material metadata snapshots for the affected branches;
- proof unrelated metadata branches were preserved;
- exact command outputs and exit codes;
- explicit statement that no Mineru2Table POST, MinIO operation, LLM call,
  Docker/env mutation, worker activation, or cleanup occurred;
- final classification:
  - `APPLIED_SINGLE_SAMPLE_METADATA`;
  - `ALREADY_APPLIED_NOOP`; or
  - a blocked/partial classification from the stop rules.

Update `TaskAndReport/TASK_TRACKING_LIST.md` to `Ready for luceon Review` only
after implementation, checks, the controlled apply/no-op, and report completion.

## 14. Review Boundary

Acceptance of Task 251 will mean only:

- one verified `toc-rebuild` metadata plan can be applied to the existing
  Luceon DB metadata for one known sample; or
- the sample was already exactly applied and safely no-op'd.

It will not mean:

- CleanService worker orchestration is active;
- Mineru2Table dispatch/polling is wired into Luceon;
- broad DB persistence is safe;
- batch or automatic metadata application is authorized;
- RawMaterial2CleanMaterial is implemented;
- the system passed UAT, L3, pressure testing, production readiness, release
  readiness, or go-live.
