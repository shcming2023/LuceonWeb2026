# TASK-20260522-212810-P0-CleanService-ReadOnly-Physical-Rehearsal-And-Existing-v2-Decision-Audit

## 1. Mainline Objective

Task 252 accepted the mock-safe CleanService `toc-rebuild` orchestration runner
at code/test level. Task 253 must answer the next mainline question:

> When the runner is fed the current real Luceon task/material metadata for the
> accepted single sample, what bounded decision does it make, and does it stay
> strictly read-only?

Do not pre-assume that the correct result must be `ALREADY_APPLIED_NOOP`. The
expected outcome may be `ALREADY_APPLIED_NOOP`,
`BLOCKED_EXISTING_TOC_REBUILD_METADATA`, `no-eligible-task`, or another bounded
preflight classification. The purpose is to observe and explain the real state,
not to make the runner pass by changing code or data.

## 2. Current Evidence

Accepted current main:

```text
main@d7ba1fa
Task 252: CLOSED_CODE_TEST_ACCEPTED_MOCKSAFE_NORUNTIME
```

Known single-sample identifiers:

```text
materialId=1842780526581841
parseTaskId/taskId=task-1779085089451
canonical Raw Material=eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
accepted clean output prefix=eduassets-clean/toc-rebuild/1842780526581841/v2/
Task 245 jobId=luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230
```

Accepted facts from prior Luceon reviews:

- Task 245 produced a real standalone Mineru2Table `v2` success output with the
  required seven artifacts.
- Task 246 accepted the `v2` output as sufficient for minimal orchestration
  planning, with residual provenance `input size_bytes=0` debt.
- Task 251 recorded that the current DB contains `toc-rebuild` `v2` metadata on
  the task/material, but also recorded a runtime-scope deviation from
  unauthorized pre-apply DB reset operations.
- Task 252 runner now handles non-completed jobs before verifier/apply and
  propagates raw input traceability dynamically.

## 3. Critical Path Scope

Perform a read-only physical rehearsal using the current real sample:

1. Fetch the current task record and material record from the Luceon DB API
   using GET-only requests.
2. Inspect only the relevant `toc-rebuild` metadata branches needed to explain
   the runner decision.
3. Perform read-only MinIO evidence checks for the known raw input and the
   accepted `v2` output prefix.
4. Invoke `runCleanServiceTocRebuildOnce` with the real fetched task/material
   objects and mock/tripwire dependencies.
5. Record the exact bounded runner result and whether any tripwire dependency
   was called.
6. Explain what that result means for the next mainline step.

This is a rehearsal/audit task. Do not modify business code in this task.

## 4. True Preconditions

Lucode must use current `origin/main` and confirm the Task 252 runner exists:

```text
server/services/cleanservice/orchestration-runner.mjs
```

The read-only rehearsal must be against exactly this sample unless Luceon issues
a new task:

```text
taskId=task-1779085089451
materialId=1842780526581841
serviceName=toc-rebuild
```

## 5. Deferrable Side Work

Do not include these in Task 253:

- changing the runner behavior;
- changing assetVersion allocation;
- changing DB metadata schema;
- real Mineru2Table dispatch or status polling;
- real DB write/apply;
- new assetVersion creation;
- MinIO output writing, deletion, cleanup, or replacement;
- upload-server wiring;
- worker scheduling;
- operator UI;
- callback/webhook handling;
- batch mode;
- RawMaterial2CleanMaterial.

If the rehearsal shows the existing `v2` metadata cannot be recognized as
already-applied, record that as mainline evidence and recommend the next narrow
task. Do not fix it inside Task 253.

## 6. Environment And Write Boundary

Work in:

```text
/workspace/dev/Luceon2026
```

Allowed committed files:

```text
TaskAndReport/2026-05-22T21-28-10+0800_P0-CleanService-ReadOnly-Physical-Rehearsal-And-Existing-v2-Decision-Audit_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Temporary local scripts are allowed only under `scratch/` or `/tmp` and must not
be committed. If a temporary script is used, summarize its logic in the report
and delete it before commit.

Read-only source inspection allowed:

```text
server/services/cleanservice/orchestration-runner.mjs
server/services/cleanservice/cleanservice-worker.mjs
server/services/cleanservice/asset-version.mjs
server/services/cleanservice/raw-material-adapter.mjs
server/services/cleanservice/output-verifier.mjs
server/services/cleanservice/metadata-summary.mjs
server/services/cleanservice/metadata-persistence.mjs
server/services/cleanservice/metadata-apply-executor.mjs
```

Forbidden committed changes:

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

## 7. Authorized Runtime Boundary

This task authorizes read-only runtime observation only.

Allowed read-only operations:

- `GET /tasks/task-1779085089451`;
- `GET /materials/1842780526581841`;
- MinIO list/stat/get for:
  - `eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json`;
  - `eduassets-clean/toc-rebuild/1842780526581841/v2/`;
- local execution of the runner with injected mock/tripwire dependencies;
- read-only container/process inspection if needed to reach the DB/MinIO
  endpoints, with secrets redacted from any report.

Forbidden operations:

- real `POST /api/v1/jobs`;
- real `POST /api/v1/jobs:from-storage`;
- real `GET /api/v1/jobs/{job_id}` against Mineru2Table;
- `PATCH`, `POST`, `PUT`, or `DELETE` against Luceon DB APIs;
- any DB write or repair;
- any MinIO put/copy/delete/move/cleanup/bucket mutation;
- any LLM/API call;
- any Docker/Compose restart/recreate/build/down/volume/network mutation;
- any `.env` or credential mutation;
- worker/scheduler activation;
- cleanup, reset, rollback, nullify, repair, or data rewrite.

If any forbidden operation appears necessary, stop and report
`BLOCKED_RUNTIME_SCOPE_WOULD_EXPAND`.

## 8. Required Rehearsal Shape

Run the runner in at least this mode:

```js
runCleanServiceTocRebuildOnce({
  task: fetchedTask,
  material: fetchedMaterial,
  config: {
    enabled: true,
    serviceName: 'toc-rebuild',
    storageEndpoint: 'minio:9000',
    storageUseSsl: false,
    submittedBy: 'luceon2026/cleanservice-readonly-rehearsal',
    costPolicy: { hardLimitCny: 8 }
  },
  deps: {
    submitJob: tripwire,
    queryJob: tripwire,
    verifyCleanServiceOutputArtifacts: tripwire,
    buildVerifiedCleanOutputMetadataCandidate: tripwire,
    buildCleanMetadataPersistencePlan: tripwire,
    applyCleanMetadataPersistencePlan: tripwire,
    artifactReader: tripwireReader,
    dbClient: tripwireDbClient
  }
})
```

The tripwires must record whether they were called and fail loudly if the runner
tries to leave the preflight path. This makes the rehearsal prove whether the
current real DB metadata is recognized before any dispatch/query/verify/apply
path.

If the runner legitimately reaches a path where artifact verification is needed
for an additional diagnostic, perform it only as a separate explicitly labeled
read-only sub-check with a MinIO read-only artifact reader. Do not mix that with
the primary tripwire rehearsal.

## 9. Fast Validation Target

The report must answer:

1. What exact task/material metadata branches were observed for `toc-rebuild`?
2. Do the canonical Raw Material object and `v2` clean output prefix exist?
3. What exact runner status/classification was returned?
4. Were submit/query/verifier/candidate/planner/apply tripwires called?
5. If the result is not `ALREADY_APPLIED_NOOP`, what exact mismatch or gate
   explains it?
6. What is the next narrow mainline task implied by the result?

## 10. Required Checks

Run:

```bash
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
git diff --check origin/main..HEAD
git diff --name-status origin/main..HEAD
```

Also record the read-only rehearsal command(s), with any secrets redacted.

## 11. Positive Acceptance Criteria

Luceon can accept this task if:

- committed changes are limited to the report and ledger;
- DB access is GET-only and limited to the specified task/material;
- MinIO access is read-only and limited to the specified raw object and `v2`
  output prefix;
- no tripwire dependency is unexpectedly called in the primary runner
  rehearsal, unless the report classifies it as a blocker;
- the runner result is bounded and explained;
- the report does not claim UAT, L3, production readiness, pressure PASS, or
  go-live;
- all command outputs and exit codes are recorded honestly.

## 12. Negative Acceptance Criteria

Luceon must return the task if it:

- performs any POST/PATCH/PUT/DELETE against DB, Mineru2Table, or MinIO;
- calls real Mineru2Table job submission or job status APIs;
- calls an LLM;
- writes, deletes, cleans, moves, or overwrites any MinIO object;
- changes source code, Docker, Compose, `.env`, package files, or UI;
- edits the real task/material metadata;
- forces the outcome to `ALREADY_APPLIED_NOOP` by changing code or data;
- hides a non-noop result as success;
- leaks secrets or raw credentials.

## 13. AI/Data Governance Red Lines

Because this task touches AI-derived clean material metadata:

1. ID-only/source-reference-only: report object refs, hashes, state, warnings,
   counters, and bounded metadata only. Do not copy full artifact contents into
   the report.
2. Asset hash locking: preserve object names and hashes exactly; do not rename,
   rewrite, or normalize object identity.
3. Pure layout/code-generation boundary: no LaTeX/TikZ/custom command output is
   involved in this task.

## 14. Stop Rules

Stop and report one of these classifications instead of widening:

```text
BLOCKED_RUNTIME_SCOPE_WOULD_EXPAND
BLOCKED_DB_TARGET_NOT_FOUND
BLOCKED_MINIO_TARGET_NOT_FOUND
BLOCKED_UNEXPECTED_RUNTIME_PATH
BLOCKED_SECRET_REDACTION_RISK
BLOCKED_TEST_ENVIRONMENT
```

## 15. Required Report

Create:

```text
TaskAndReport/2026-05-22T21-28-10+0800_P0-CleanService-ReadOnly-Physical-Rehearsal-And-Existing-v2-Decision-Audit_REPORT.md
```

The report must include:

- exact branch and full HEAD commit;
- current `origin/main` baseline;
- changed file list;
- read-only DB GET evidence;
- read-only MinIO evidence;
- runner result JSON;
- tripwire call matrix;
- command outputs and exit codes;
- conclusion and recommended next task;
- explicit red-line statement that no POST, DB write, MinIO write/delete,
  Docker mutation, LLM call, cleanup/reset/rollback, UAT/L3/readiness/pressure
  PASS/go-live claim occurred.

## 16. Review Boundary

Acceptance of Task 253 will mean only:

- current real task/material metadata was read and used as runner input;
- the current `v2` MinIO evidence was observed read-only;
- the runner's current-state decision is known and explained;
- the next mainline implementation/authorization decision can be made with
  evidence.

It will not mean:

- CleanService is active;
- real orchestration has been performed;
- a new clean asset version has been created;
- DB metadata writes are authorized or performed;
- MinIO outputs are created or changed;
- UAT/L3/production/release readiness is achieved.
