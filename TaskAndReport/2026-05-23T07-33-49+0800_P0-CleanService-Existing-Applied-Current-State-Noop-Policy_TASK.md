# TASK-20260523-073349-P0-CleanService-Existing-Applied-Current-State-Noop-Policy

## 1. Mainline Objective

Task 253 proved that the current real task/material metadata contains a valid
completed `toc-rebuild v2` clean material, but the Task 252 runner currently
classifies it as `BLOCKED_EXISTING_TOC_REBUILD_METADATA` because the allocator
advances toward `v3` before the runner can recognize the already-applied
current state.

Task 254 must answer the next mainline question:

> Can the runner safely recognize an already-applied completed clean material as
> the current state, without dispatching, verifying, applying, or generating a
> new asset version?

This task separates two intents:

1. Use the current already-applied clean material as current state.
2. Create a new clean material version in a later explicitly authorized task.

Only the first intent is in scope for Task 254.

## 2. Current Evidence

Accepted current main:

```text
main@9e442a9
Task 253: ACCEPTED_READONLY_REHEARSAL_EVIDENCE_WITH_LUCEON_HEAD_CORRECTION
```

Task 253 facts:

```text
taskId=task-1779085089451
materialId=1842780526581841
existing task cleanServiceJobs['toc-rebuild'].assetVersion=v2
existing task cleanServiceJobs['toc-rebuild'].status=completed
existing material cleanMaterials['toc-rebuild'].latestVersion=v2
existing material cleanMaterials['toc-rebuild'].status=completed
```

Task 253 runner result:

```text
status=BLOCKED_EXISTING_TOC_REBUILD_METADATA
classification=BLOCKED_EXISTING_TOC_REBUILD_METADATA
tripwire calls=[]
```

Interpretation:

- The current runner is safe because it blocks before side effects.
- The current runner is not yet semantically complete because it cannot express
  “use the already applied clean material as current state”.

## 3. Critical Path Scope

Implement a narrow current-state noop policy in the mock-safe orchestration
runner.

The policy should run before new assetVersion/request planning. If both the
task and material already contain aligned, completed `toc-rebuild` metadata,
the runner should return a bounded noop/current-state result and perform zero
submit/query/verifier/candidate/planner/apply calls.

Recommended classification:

```text
CURRENT_CLEAN_MATERIAL_NOOP
```

The exact name may differ only if Lucode has a stronger codebase-aligned
reason. If a different name is used, justify it clearly in the report.

## 4. True Preconditions

Lucode must inspect:

```text
server/services/cleanservice/orchestration-runner.mjs
server/tests/cleanservice-orchestration-runner-smoke.mjs
server/services/cleanservice/asset-version.mjs
server/services/cleanservice/metadata-apply-executor.mjs
```

The current-state noop policy must not rely on live DB, MinIO, Mineru2Table, or
LLM access. All tests must use in-memory fixtures and tripwire dependencies.

## 5. Deferrable Side Work

Do not include these in Task 254:

- real DB reads or writes;
- real MinIO reads or writes;
- real Mineru2Table dispatch or job query;
- new assetVersion execution;
- introducing a real rerun/new-version authorization path;
- worker scheduler activation;
- upload-server route wiring;
- operator UI;
- callback/webhook receiver;
- batch behavior;
- RawMaterial2CleanMaterial.

The future new-version run remains a separate Director-authorized task.

## 6. Environment And Write Boundary

Work in:

```text
/workspace/dev/Luceon2026
```

Allowed source/test files:

```text
server/services/cleanservice/orchestration-runner.mjs
server/tests/cleanservice-orchestration-runner-smoke.mjs
TaskAndReport/2026-05-23T07-33-49+0800_P0-CleanService-Existing-Applied-Current-State-Noop-Policy_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Read-only unless a hard blocker proves a tiny import/export fix is required:

```text
server/services/cleanservice/asset-version.mjs
server/services/cleanservice/cleanservice-worker.mjs
server/services/cleanservice/metadata-apply-executor.mjs
server/services/cleanservice/metadata-persistence.mjs
server/services/cleanservice/metadata-summary.mjs
server/services/cleanservice/output-verifier.mjs
```

Forbidden files and areas:

```text
server/upload-server.mjs
server/db-server.mjs
server/services/tasks/**
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

## 7. Authorized Runtime Boundary

This task authorizes no real runtime operations.

Forbidden operations:

- real `POST /api/v1/jobs`;
- real `POST /api/v1/jobs:from-storage`;
- real `GET /api/v1/jobs/{job_id}` against Mineru2Table;
- real DB `GET`, `PATCH`, `POST`, `PUT`, or `DELETE`;
- any DB write or repair;
- any MinIO list/stat/get/put/copy/delete/move/cleanup/bucket mutation;
- any LLM/API call;
- any Docker/Compose command;
- any `.env` or credential mutation;
- worker/scheduler activation;
- cleanup, reset, rollback, nullify, repair, or data rewrite.

Tests must be pure in-memory mocks.

## 8. Required Runner Behavior

Add a preflight branch that detects aligned completed current clean material.

Minimum detection requirements:

1. `existingTaskJob = task.metadata.cleanServiceJobs[serviceName]` exists.
2. `existingMaterialClean = material.metadata.cleanMaterials[serviceName]`
   exists.
3. `existingTaskJob.assetVersion` equals
   `existingMaterialClean.latestVersion`.
4. Both records represent a completed/applied state. For this task, at minimum
   support `status === 'completed'` or `cleanState === 'completed'` on the task
   job and `status === 'completed'` on the material clean record.
5. The branch returns before calling `allocateAssetVersion`,
   `buildCleanServiceJobRequest`, submit/query/verifier/candidate/planner/apply
   dependencies, or any DB client.

Expected bounded result shape should include:

```js
{
  ok: true,
  status: 'CURRENT_CLEAN_MATERIAL_NOOP',
  classification: 'CURRENT_CLEAN_MATERIAL_NOOP',
  materialId,
  taskId,
  serviceName,
  assetVersion,
  jobId,
  cleanState,
  reason,
  observedAt
}
```

It may include bounded artifact role/object-ref summaries if they are already
present in metadata, but must not include full artifact content.

Do not treat misaligned metadata as current-state noop. Examples that must
remain blocked:

- task job assetVersion differs from material latestVersion;
- task job exists but material clean record is missing;
- material clean record exists but task job is missing;
- current task job status is failed/protocol-failure/skipped/timeout;
- jobId is missing from task metadata.

## 9. Fast Validation Target

Add focused smoke coverage to `cleanservice-orchestration-runner-smoke.mjs`:

1. Completed aligned task/material `toc-rebuild v2` returns
   `CURRENT_CLEAN_MATERIAL_NOOP` and performs zero submit/query/verifier/planner
   /apply calls.
2. The noop result must preserve the existing `v2` assetVersion and historical
   jobId; it must not generate a `v3` jobId.
3. Mismatched task/material versions remain blocked and do not return noop.
4. Missing task or material clean branch remains blocked or follows the existing
   bounded behavior; it must not return noop.
5. Existing Task 252 smoke cases still pass, especially:
   - disabled noop;
   - happy dry-run path for no existing metadata;
   - in-progress job early return;
   - unsupported status early return;
   - no full artifact body in result.

## 10. Required Checks

Run:

```bash
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
for f in server/tests/cleanservice-*.mjs; do node "$f" || exit 1; done
npx pnpm@10.4.1 exec tsc --noEmit
git diff --check origin/main..HEAD
git diff --name-status origin/main..HEAD
```

If any check requires real runtime access, stop and report
`BLOCKED_RUNTIME_DEPENDENCY_LEAK`.

## 11. Positive Acceptance Criteria

Luceon can accept this task if:

- only allowed files are changed;
- completed aligned task/material metadata returns a bounded current-state noop;
- no submit/query/verifier/candidate/planner/apply dependencies are called in
  that noop branch;
- misaligned or failed existing metadata does not become noop;
- no new assetVersion is generated in the current-state noop branch;
- existing runner behavior for no-existing-metadata happy dry-run remains
  covered and passing;
- all required checks pass;
- report records exact branch, full HEAD, diff, checks, and exit codes.

## 12. Negative Acceptance Criteria

Luceon must reject or return the task if it:

- performs any real DB/MinIO/Mineru2Table/LLM/Docker/runtime operation;
- changes upload-server, UI, Docker, package files, docs, or external
  Mineru2Table code;
- auto-generates `v3` when the intent is current-state noop;
- treats mismatched or failed existing metadata as noop;
- hides a future new-version/rerun path inside this task;
- adds cleanup/reset/rollback/nullify behavior;
- returns full artifact text/content instead of bounded refs and summaries;
- claims UAT, L3, production readiness, release readiness, pressure PASS, or
  go-live.

## 13. AI/Data Governance Red Lines

Because this task touches AI-derived clean material metadata:

1. ID-only/source-reference-only: outputs must reference IDs, ObjectRefs,
   hashes, counters, states, and warnings only.
2. Asset hash locking: preserve existing object paths and hashes exactly.
3. Pure layout/code-generation boundary: no LaTeX/TikZ/custom command output is
   involved in this task.

## 14. Stop Rules

Stop and report instead of widening if:

```text
BLOCKED_RUNTIME_DEPENDENCY_LEAK
BLOCKED_FORBIDDEN_FILE_REQUIRED
BLOCKED_POLICY_AMBIGUITY
BLOCKED_TEST_ENVIRONMENT
```

Use `BLOCKED_POLICY_AMBIGUITY` if Lucode cannot implement current-state noop
without also designing new-version/rerun authorization semantics.

## 15. Required Report

Create:

```text
TaskAndReport/2026-05-23T07-33-49+0800_P0-CleanService-Existing-Applied-Current-State-Noop-Policy_REPORT.md
```

The report must include:

- exact branch and full HEAD commit;
- changed files from `git diff --name-status origin/main..HEAD`;
- whitespace check from `git diff --check origin/main..HEAD`;
- command outputs and exit codes;
- smoke case list and pass/fail summary;
- result shape for the new current-state noop case;
- explicit statement that no runtime operations occurred;
- residual debt and recommended next task.

## 16. Review Boundary

Acceptance of Task 254 will mean only:

- mock-safe runner can recognize an already-applied completed clean material as
  current state;
- the runner no longer implicitly advances to a new version for that default
  intent;
- a later real new-version run can be discussed with clearer authorization
  semantics.

It will not mean:

- CleanService is active;
- a new clean asset version has been created;
- real orchestration has been performed;
- DB metadata writes are authorized or performed;
- MinIO outputs are created or changed;
- UAT/L3/production/release readiness is achieved.
