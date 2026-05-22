# TASK-20260522-202101-P0-CleanService-Minimal-Orchestration-Runner-MockSafe-NoRuntime

## 1. Mainline Objective

Task 251 closed the code/test-level DB apply executor and recorded the current
single-sample DB metadata state, but it also exposed a process risk: ad-hoc
manual scripts can drift into unauthorized reset/cleanup behavior.

Task 252 must answer the next mainline question:

> Can Luceon compose the accepted CleanService building blocks into one
> deterministic orchestration runner, while remaining fully mock-safe and
> disabled-by-default?

This task is the bridge between isolated modules and a future controlled
single-sample orchestration. It must not activate runtime dispatch.

## 2. Current Evidence

Accepted evidence on current `main`:

- Task 245 produced a real standalone Mineru2Table `v2` success path for:

  ```text
  materialId=1842780526581841
  parseTaskId=task-1779085089451
  assetVersion=v2
  jobId=luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230
  ```

- Task 246 accepted that `v2` output is good enough for minimal orchestration
  planning, with known residual warning `input-size-bytes-zero`.
- Task 248 accepted the seven-artifact output verifier at code/test level.
- Task 249 accepted the verified output ingestion candidate builder.
- Task 250 accepted the dry-run metadata persistence payload planner.
- Task 251 accepted the metadata apply executor at code/test level and recorded
  the current DB state, but did not accept the runtime execution as a clean
  exactly-one-write success path because a pre-apply shallow-null reset occurred.

Current runtime facts from Luceon read-only review:

```text
cms-upload-server: healthy
cms-db-server: healthy
mineru2table-api: healthy
CLEANSERVICE_ENABLED=false
CLEANSERVICE_ENDPOINT=http://mineru2table:8000
mineru2table jobs.json job_count=3
task/material now contain toc-rebuild v2 metadata for the accepted sample
```

Current code gap:

- The worker shell can submit a job-shaped request, but it does not yet compose
  dispatch, status query, seven-artifact verification, candidate construction,
  persistence planning, and apply execution into one tested orchestration path.
- Existing Task 248-251 modules are useful, but still manually stitched by
  tasks/scripts.

## 3. Critical Path Scope

Implement a new mock-safe orchestration runner with dependency injection.

The runner should coordinate only the minimal `toc-rebuild` path:

```text
preflight
-> build/request planning
-> submit mock
-> query mock
-> verify output mock/injected verifier
-> build metadata candidate
-> build persistence plan
-> apply executor in dry-run/mock mode
-> return a bounded orchestration result
```

The task may add:

1. `server/services/cleanservice/orchestration-runner.mjs`
2. `server/tests/cleanservice-orchestration-runner-smoke.mjs`
3. the Task 252 report and ledger update

Do not wire this runner into `upload-server`, timers, route handlers, UI, or the
existing production worker loop in this task.

## 4. True Preconditions

Before implementing, Lucode must inspect the current accepted modules:

```text
server/services/cleanservice/cleanservice-worker.mjs
server/services/cleanservice/worker-factory.mjs
server/services/cleanservice/http-transport.mjs
server/services/cleanservice/output-verifier.mjs
server/services/cleanservice/metadata-summary.mjs
server/services/cleanservice/metadata-persistence.mjs
server/services/cleanservice/metadata-apply-executor.mjs
```

The runner must not require live DB, live MinIO, live HTTP transport, or live
LLM access. Any external dependency must be provided as a test double.

## 5. Deferrable Side Work

Do not include these in Task 252:

- real `POST /api/v1/jobs`;
- real `GET /api/v1/jobs/{job_id}`;
- real MinIO artifact reads;
- real DB PATCH or readback;
- worker scheduler activation;
- upload-server route wiring;
- operator UI;
- batch mode;
- webhook/callback receiver;
- RawMaterial2CleanMaterial;
- cleanup of old Task 238 ledger residue;
- cleaning or rewriting Task 251 DB state;
- broad false-success hardening inside Mineru2Table.

These remain valid later work, but they are not required to prove the next
mainline integration step.

## 6. Environment And Write Boundary

Work in:

```text
/workspace/dev/Luceon2026
```

Allowed source files:

```text
server/services/cleanservice/orchestration-runner.mjs       # new narrow module
server/tests/cleanservice-orchestration-runner-smoke.mjs    # new focused smoke
TaskAndReport/2026-05-22T20-21-01+0800_P0-CleanService-Minimal-Orchestration-Runner-MockSafe-NoRuntime_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Read-only unless a hard blocker proves a narrow import/export fix is required:

```text
server/services/cleanservice/cleanservice-worker.mjs
server/services/cleanservice/worker-factory.mjs
server/services/cleanservice/http-transport.mjs
server/services/cleanservice/protocol.mjs
server/services/cleanservice/output-verifier.mjs
server/services/cleanservice/metadata-summary.mjs
server/services/cleanservice/metadata-persistence.mjs
server/services/cleanservice/metadata-apply-executor.mjs
server/services/cleanservice/asset-version.mjs
server/services/cleanservice/raw-material-adapter.mjs
server/services/cleanservice/config.mjs
```

Forbidden files and areas:

```text
server/upload-server.mjs
server/db-server.mjs
server/services/tasks/task-client.mjs
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

## 7. Authorized Runtime Boundary

This task authorizes no real runtime operations.

Forbidden operations:

- real `POST /api/v1/jobs`;
- real `POST /api/v1/jobs:from-storage`;
- real `GET /api/v1/jobs/{job_id}`;
- real `GET /tasks/:id`, `GET /materials/:id`, `PATCH /tasks/:id`, or
  `PATCH /materials/:id`;
- any DB write or read against Luceon runtime;
- any MinIO read/write/list/stat/delete;
- any LLM/API call;
- any Docker/Compose command;
- any `.env` or credential mutation;
- any worker/scheduler activation;
- any cleanup, reset, rollback, repair, or data rewrite.

Tests may use in-memory mocks only.

## 8. Required Runner Behavior

The new runner should expose a small function, for example:

```js
runCleanServiceTocRebuildOnce({
  task,
  material,
  config,
  deps,
  now
})
```

The exact signature may differ if it better fits the codebase, but the module
must keep these properties:

1. **Dependency injection only**:
   - task/material inputs are passed in;
   - submit/query clients are injected;
   - verifier is injected or wraps existing verifier with an injected reader;
   - persistence planner and apply executor are used as pure functions or with
     mock clients.
2. **Disabled default**:
   - if config is disabled, return `disabled-noop`;
   - do not call submit/query/verifier/apply dependencies.
3. **No reset path**:
   - no function named or behaving like reset, cleanup, rollback, repair, clear,
     nullify, truncate, or delete;
   - no metadata branch should ever be set to `null` by this runner.
4. **Already-applied noop**:
   - if existing task/material metadata already contains matching
     `jobId + assetVersion`, return `ALREADY_APPLIED_NOOP`;
   - do not submit, query, verify, or apply.
5. **Protocol-failure on verifier failure**:
   - if job status is `completed` but the verifier reports invalid output,
     return a bounded `PROTOCOL_FAILURE` result;
   - do not build a persistence apply plan.
6. **Dry-run persistence by default**:
   - the runner must invoke the apply executor with `allowRealApply=false`;
   - no mock test should depend on a real DB client.
7. **Bounded result shape**:
   - return only IDs, states, ObjectRef summaries, warnings, and counters;
   - never return or persist full artifact contents.

## 9. Fast Validation Target

Add focused smoke tests covering at least these cases:

1. disabled config returns `disabled-noop` and performs zero calls;
2. already-applied task/material metadata returns `ALREADY_APPLIED_NOOP` and
   performs zero submit/query/verify/apply calls;
3. happy-path mock completed job runs through verify -> candidate -> plan ->
   dry-run apply and returns a completed dry-run result;
4. completed job with verifier failure returns `PROTOCOL_FAILURE` and performs
   no apply;
5. dispatch failure returns a bounded dispatch failure and performs no verify or
   apply;
6. incompatible existing `toc-rebuild` metadata blocks before submit;
7. no dependency receives or emits reset/cleanup/null metadata behavior;
8. no result contains full artifact content keys such as `blocks`,
   `paragraphs`, `nodes`, `children`, or large markdown/json bodies.

## 10. Required Checks

Run these from the development container:

```bash
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
node server/tests/cleanservice-metadata-persistence-smoke.mjs
node server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-worker-shell-smoke.mjs
node server/tests/cleanservice-worker-factory-smoke.mjs
node server/tests/cleanservice-http-transport-smoke.mjs
node server/tests/cleanservice-payload-alignment-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
git diff --check origin/main..HEAD
git diff --name-status origin/main..HEAD
```

If any check requires real runtime access, stop and report
`BLOCKED_RUNTIME_DEPENDENCY_LEAK` instead of widening scope.

## 11. Positive Acceptance Criteria

Luceon can accept this task if:

- only allowed source/test/report/ledger files changed, or any exception is
  explicitly justified and tiny;
- the new runner composes the existing accepted modules without real clients;
- focused tests prove disabled, already-applied noop, happy dry-run,
  verifier-failure blocking, dispatch-failure blocking, incompatible metadata
  blocking, no reset behavior, and ID/ObjectRef-only outputs;
- existing CleanService smoke tests remain green;
- `CLEANSERVICE_ENABLED=false` remains the default runtime posture;
- report records exact branch, HEAD, changed files, command outputs, and exit
  codes.

## 12. Negative Acceptance Criteria

Luceon must reject or return the task if it:

- sends any real HTTP request to Mineru2Table;
- reads or writes real DB/MinIO;
- modifies Docker, Compose, `.env`, package files, frontend, or upload-server;
- activates worker scheduling or automatic scanning;
- adds reset/cleanup/rollback/nullify behavior;
- stores or returns full artifact text/content instead of ObjectRefs and
  summaries;
- claims UAT, L3, production readiness, release readiness, pressure PASS, or
  go-live.

## 13. AI/Data Governance Red Lines

Because this task touches AI-derived clean material metadata:

1. ID-only/source-reference-only: outputs must reference IDs, ObjectRefs, hashes,
   counters, and warnings; do not invent or persist source truth.
2. Asset hash locking: object refs must preserve the known hash names and object
   paths; no renaming or rewritten asset identity.
3. Pure layout/code-generation boundary: no LaTeX/TikZ/custom command output is
   involved in this task; if any such requirement appears, stop and report it as
   out of scope.

## 14. Stop Rules

Stop and report instead of widening if:

- an existing module cannot be composed without editing forbidden runtime files;
- the runner needs real DB/MinIO/Mineru2Table access to pass tests;
- test setup tempts reset/cleanup/rollback behavior;
- current branch cannot be cleanly based on `origin/main`;
- required checks cannot run without environment mutation.

Use one of these classifications:

```text
BLOCKED_RUNTIME_DEPENDENCY_LEAK
BLOCKED_FORBIDDEN_FILE_REQUIRED
BLOCKED_RESET_OR_CLEANUP_TEMPTATION
BLOCKED_TEST_ENVIRONMENT
```

## 15. Required Report

Create:

```text
TaskAndReport/2026-05-22T20-21-01+0800_P0-CleanService-Minimal-Orchestration-Runner-MockSafe-NoRuntime_REPORT.md
```

The report must include:

- exact branch and full HEAD commit;
- changed file list from `git diff --name-status origin/main..HEAD`;
- whitespace check output from `git diff --check origin/main..HEAD`;
- all command outputs and exit codes from required checks;
- smoke test case list and pass/fail summary;
- explicit statement that no runtime operations were performed;
- explicit statement that the runner has no reset/cleanup/rollback path;
- residual debt and recommended next task.

## 16. Review Boundary

Acceptance of Task 252 will mean only:

- mock-safe orchestration composition works at code/test level;
- disabled-by-default behavior is preserved;
- the next mainline read-only rehearsal can be considered.

It will not mean:

- CleanService is active;
- Mineru2Table is dispatched by Luceon;
- DB metadata writes are authorized;
- MinIO artifacts are read or written;
- any UI/operator workflow is complete;
- UAT/L3/production/release readiness is achieved.
