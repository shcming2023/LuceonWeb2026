# TASK-20260523-080011-P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime

## 1. Mainline Objective

Task 254 proved that an already-applied completed `toc-rebuild v2` record can
be treated as the current clean material without allocating a new version or
calling any downstream dependency.

The next mainline question is:

> Can the runner express a separate, explicit "create a new clean material
> version" intent in mock-safe code, while keeping the default current-state
> behavior as `CURRENT_CLEAN_MATERIAL_NOOP`?

Task 255 is the mock-safe policy layer before any real new-version run.

It must prove two things:

1. Default execution against aligned completed v2 metadata remains noop.
2. Only an explicit new-version intent with a bounded reason may bypass that
   noop branch and proceed to new assetVersion planning.

This task does not authorize a real v3 execution.

## 2. Current Evidence

Accepted current main:

```text
main@30ef796
Task 254: ACCEPTED_CODE_TEST_LEVEL
```

Task 254 facts:

```text
existing completed task/material toc-rebuild v2 metadata
default runner result: CURRENT_CLEAN_MATERIAL_NOOP
tripwire calls: []
```

Task 254 accepted behavior:

- aligned completed task/material metadata returns current-state noop before
  `allocateAssetVersion`;
- mismatched version, missing `jobId`, and failed task job remain blocked;
- no runtime/data operation was authorized or performed.

Director decision for Task 255:

```text
同意先做一个 mock
```

Interpretation:

- implement only mock-safe new-version authorization semantics;
- do not perform real POST, polling, verification against real MinIO, DB apply,
  Docker operation, LLM call, or data cleanup.

## 3. Critical Path Scope

Implement an explicit new-version intent policy inside the mock-safe
orchestration runner.

Required default:

```text
aligned completed v2 metadata + no explicit new-version intent
=> CURRENT_CLEAN_MATERIAL_NOOP
```

Required explicit new-version path:

```text
aligned completed v2 metadata
+ config intent to create a new version
+ non-empty bounded reason
=> bypass current-state noop
=> allocate next assetVersion, expected v3 in current fixtures
=> continue existing mock/dry-run orchestration only
```

Recommended intent shape:

```js
{
  enabled: true,
  serviceName: 'toc-rebuild',
  intent: 'create-new-version',
  newVersionReason: 'operator-requested-rerun'
}
```

If Lucode chooses a slightly different field name to better match local code,
the report must explain the reason and preserve the same semantics. Do not use
ambiguous names like `allowRerun: true` as the only gate.

## 4. True Preconditions

Lucode must inspect:

```text
server/services/cleanservice/orchestration-runner.mjs
server/tests/cleanservice-orchestration-runner-smoke.mjs
server/services/cleanservice/asset-version.mjs
server/services/cleanservice/cleanservice-worker.mjs
```

The implementation must remain pure in-memory and dependency-injected.

Task 255 must not read the real DB, real MinIO, real Mineru2Table, or real LLM
runtime.

## 5. Deferrable Side Work

Do not include these in Task 255:

- real new assetVersion execution;
- real Mineru2Table `POST /api/v1/jobs`;
- real job polling;
- real MinIO object reads/writes/lists/stats/deletes;
- real DB reads/writes/PATCH apply;
- Docker/Compose restart, rebuild, recreate, or env mutation;
- upload-server route wiring;
- worker scheduler activation;
- operator UI;
- callback/webhook receiver;
- batch strategy;
- cost desk UI;
- RawMaterial2CleanMaterial;
- cleanup/reset/rollback/nullify of Task 242, Task 245, or Task 251 data.

Those remain separate Director-authorized tasks.

## 6. Environment And Write Boundary

Work in:

```text
/workspace/dev/Luceon2026
```

Allowed source/test files:

```text
server/services/cleanservice/orchestration-runner.mjs
server/tests/cleanservice-orchestration-runner-smoke.mjs
TaskAndReport/2026-05-23T08-00-11+0800_P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Read-only unless a tiny import/export blocker is proven and reported before
widening:

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
- any DB write, repair, reset, or rollback;
- any MinIO list/stat/get/put/copy/delete/move/cleanup/bucket mutation;
- any LLM/API call;
- any Docker/Compose command;
- any `.env` or credential mutation;
- worker/scheduler activation;
- cleanup, reset, rollback, nullify, repair, or data rewrite.

Tests must use pure in-memory mocks and tripwire dependencies.

## 8. Required Runner Behavior

### 8.1 Default Intent

When no explicit intent is provided, the runner must preserve the Task 254
behavior:

```text
aligned completed current clean material
=> CURRENT_CLEAN_MATERIAL_NOOP
```

The noop result must continue to preserve:

- existing assetVersion, e.g. `v2`;
- existing historical `jobId`;
- bounded reason;
- zero calls to submit/query/verifier/candidate/planner/apply dependencies.

### 8.2 Explicit New-Version Intent

When aligned completed metadata exists, the runner may bypass the current-state
noop only if all required conditions are present:

1. `intent === 'create-new-version'` or an equivalent explicit field documented
   in the report.
2. A non-empty bounded reason is provided, recommended field:
   `newVersionReason`.
3. The previous task/material metadata is completed and aligned.
4. The path still goes through existing assetVersion allocation and existing
   mock/dry-run orchestration gates.

Expected audit fields should be included in the bounded result or request audit
where practical:

```js
{
  intent: 'create-new-version',
  triggerReason: 'operator-requested-rerun',
  previousAssetVersion: 'v2',
  previousJobId: '<existing job id>',
  newAssetVersion: 'v3'
}
```

Do not overwrite v2 or imply v2 is invalid. A new-version run creates a new
traceable clean material version.

### 8.3 Missing Or Unsupported Intent Data

If `intent === 'create-new-version'` is present but the reason is missing or
empty, return a bounded block before dispatch:

```text
BLOCKED_NEW_VERSION_REASON_REQUIRED
```

If an unsupported explicit intent is provided, return a bounded block before
dispatch:

```text
BLOCKED_UNSUPPORTED_CLEANSERVICE_INTENT
```

The exact names may differ only if Lucode has a stronger codebase-aligned
reason. If changed, justify in the report.

### 8.4 Existing Metadata Safety

The new-version intent must not weaken the Task 254 safety cases:

- failed existing task job must not become noop;
- version mismatch must not silently become current-state noop;
- missing jobId must remain blocked;
- missing task or material clean branch must not be treated as current-state
  completion.

If Lucode decides that explicit new-version intent should allow some mismatch
case to proceed, stop and report `BLOCKED_NEW_VERSION_POLICY_AMBIGUITY` instead
of inventing semantics.

## 9. AI/Data Governance Red Lines

Because this task sits on the Clean Material path:

1. ID-only/source-reference-only: do not introduce logic that persists full
   source text, full Markdown, full artifact JSON bodies, or model-generated
   source truth into metadata.
2. Asset hash locking: do not rename, rewrite, or normalize any object hash or
   object path in fixtures as a shortcut.
3. Pure structural boundary: do not introduce LaTeX/TikZ/custom command logic.

## 10. Fast Validation Target

Extend `cleanservice-orchestration-runner-smoke.mjs` with focused cases.

Minimum required tests:

1. No intent + aligned completed v2 returns `CURRENT_CLEAN_MATERIAL_NOOP`.
2. Explicit `create-new-version` + reason on aligned completed v2 bypasses noop
   and reaches mock dry-run orchestration with allocated `v3`.
3. The explicit path preserves or reports previous version/jobId and new
   version in bounded audit fields.
4. `create-new-version` without reason returns
   `BLOCKED_NEW_VERSION_REASON_REQUIRED` before submit/query/verifier/apply.
5. Unsupported intent returns `BLOCKED_UNSUPPORTED_CLEANSERVICE_INTENT` before
   submit/query/verifier/apply.
6. Existing Task 252/254 cases still pass:
   - disabled noop;
   - happy dry-run path with no existing metadata;
   - in-progress job early return;
   - unsupported job status early return;
   - current-state noop;
   - mismatch/missing-jobId/failed existing metadata remains blocked.

Every negative preflight test must use tripwire dependencies that throw if any
external dependency is called.

## 11. Required Checks

Run and record exact commands and exit codes:

```bash
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
for f in server/tests/cleanservice-*.mjs; do node "$f" || exit 1; done
npx pnpm@10.4.1 exec tsc --noEmit
git diff --check origin/main..HEAD
git diff --name-status origin/main..HEAD
```

Do not run Docker, DB, MinIO, Mineru2Table, or LLM commands.

## 12. Report Requirements

Create:

```text
TaskAndReport/2026-05-23T08-00-11+0800_P0-CleanService-Explicit-New-Version-Intent-Policy-MockSafe-NoRuntime_REPORT.md
```

The report must include:

- final branch and exact GitHub-visible HEAD;
- changed file list from `git diff --name-status origin/main..HEAD`;
- exact test commands and exit codes;
- intent field name and reason field name;
- default noop behavior proof;
- explicit new-version mock behavior proof;
- missing reason / unsupported intent block proof;
- statement that no real runtime/data operation occurred;
- residual debt and next recommended task boundary.

## 13. Stop Rules

Stop and report blocked if:

- implementing this requires real DB/MinIO/Mineru2Table/LLM access;
- implementing this requires Docker/env/package changes;
- the existing runner shape cannot express intent without broad refactor;
- current metadata mismatch semantics become ambiguous;
- any test would require real Task 245/253 physical data;
- any secret or runtime credential would be needed.

Recommended blocked classifications:

```text
BLOCKED_NEW_VERSION_POLICY_AMBIGUITY
BLOCKED_RUNTIME_DEPENDENCY_REQUIRED
BLOCKED_SCOPE_WOULD_EXPAND
```

## 14. Acceptance Boundary

Acceptance of Task 255 means only:

- mock-safe code/test-level new-version intent policy is accepted;
- default current-state noop remains protected;
- explicit new-version path can be planned in memory and tested with mocks.

Acceptance does not mean:

- real v3 run is authorized;
- CleanService worker is activated;
- DB persistence is authorized;
- MinIO output generation is authorized;
- LLM usage is authorized;
- upload-server/operator route/UI/batch/callback behavior is accepted;
- UAT, L3, pressure PASS, production readiness, release readiness, or go-live.
