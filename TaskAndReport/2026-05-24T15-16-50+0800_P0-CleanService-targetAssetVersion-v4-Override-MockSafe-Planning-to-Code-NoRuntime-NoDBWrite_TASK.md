# TASK-20260524-151650-P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite

Issued at: 2026-05-24T15:16:50+0800

Actor: Lucode

## Mainline Objective

Implement the planning-level direction accepted in Task 264: a
task-brief-scoped explicit `targetAssetVersion: "v4"` path for mock-safe
CleanService `toc-rebuild` request planning.

The goal is to let future validation target a clean `v4` evidence path without
promoting the diagnostic dual-key `v3` record into durable Clean Material
metadata.

## Critical Path Scope

Lucode must implement only mock-safe code/test support for `targetAssetVersion`
in the local CleanService product path.

The implementation must prove:

1. Default behavior is unchanged: accepted current `v2` metadata still allocates
   `v3` when no `targetAssetVersion` is supplied.
2. Explicit `intent=create-new-version`, non-empty `newVersionReason`, completed
   aligned existing `v2` history, and `targetAssetVersion: "v4"` can plan a
   bounded `v4` request in mock-safe tests.
3. The request job id, sink prefix, verifier expected asset version, persistence
   plan, and audit all agree on `v4`.
4. The audit records both default allocation and explicit target:
   - `defaultAllocatedAssetVersion = v3`
   - `targetAssetVersion = v4`
   - `newAssetVersion = v4`
5. Existing safety gates remain intact:
   - completed/aligned history required before explicit new-version;
   - no silent legacy parsed evidence promotion;
   - completed-job `sourceInput` fallback remains traceable;
   - `-probe` provenance remains rejected unless explicitly allowed;
   - real apply over existing metadata remains blocked unless a later task
     explicitly authorizes a different DB apply boundary.

## True Preconditions

- Start from current GitHub `main`.
- Read Task 264 Luceon review first, then the Task 264 report, Task 263 report,
  and only directly relevant CleanService source/tests.
- Treat current accepted DB state as `toc-rebuild v2`.
- Treat existing physical/job-store `v3` as diagnostic dual-key evidence only.
- Do not use live DB, MinIO, Docker, Mineru2Table job-store, runtime, or
  external API evidence in this task.

## Deferrable Side Work

Defer:

- runtime POST or live Mineru2Table query;
- DB metadata apply;
- MinIO write or physical `v4` artifact creation;
- job-store read/write/edit/cleanup;
- worker/scheduler/upload-server activation;
- fresh sample selection;
- provenance-quality repair for existing `input size_bytes=0`;
- UI/operator review changes;
- broad Clean Material quality review.

## Fast Validation Target

The smallest useful proof is a mock-safe test path showing:

```text
current accepted v2 history + create-new-version + targetAssetVersion=v4
=> request/job/sink/verification/persistence/audit target v4
=> no submit/query/runtime/DB write occurs in tests
```

## Environment And Branch

Default Lucode workspace:

```text
/Users/concm/Dev_workspace/Luceon2026
```

Use this branch:

```text
lucode/TASK-20260524-151650-P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite
```

## Allowed Source Files

Lucode may edit only these source files if needed:

```text
server/services/cleanservice/asset-version.mjs
server/services/cleanservice/cleanservice-worker.mjs
server/services/cleanservice/orchestration-runner.mjs
server/services/cleanservice/metadata-apply-executor.mjs
```

Lucode may edit only focused CleanService tests needed for this behavior:

```text
server/tests/cleanservice-asset-version-smoke.mjs
server/tests/cleanservice-orchestration-runner-smoke.mjs
server/tests/cleanservice-metadata-apply-executor-smoke.mjs
```

Allowed control-plane writes:

```text
TaskAndReport/2026-05-24T15-16-50+0800_P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Do not edit PRD, architecture docs, package files, Docker files, env/config
files, runtime data, samples, or external repositories.

## Implementation Requirements

Implement the minimum local product-code support needed for a task-scoped
target version.

Required semantics:

- `targetAssetVersion` is optional.
- Without `targetAssetVersion`, current behavior remains unchanged.
- With `targetAssetVersion`, the only accepted shape for this task is a numeric
  version string such as `v4`.
- `targetAssetVersion` is valid only when:
  - `config.intent === "create-new-version"`;
  - `config.newVersionReason` is non-empty;
  - existing task clean job and material clean material are present, completed,
    aligned, and include a previous job id;
  - the target version is greater than the current accepted metadata version;
  - the target version is greater than or equal to the default allocator result;
  - the target version is not equal to the previous accepted version;
  - no active duplicate clean job is present.
- The code must compute and preserve the default allocator result before
  applying the explicit target.
- The request planner must not double-allocate conflicting versions.
- The request job id, sink prefix, verifier expected asset version,
  persistence patch, and dry-run apply audit must agree on the resolved version.
- The new-version audit must include the previous accepted version/job id,
  the default allocated version, the target asset version, and the final new
  asset version.
- Dry-run explicit new-version apply over existing metadata may pass only when
  the target version exactly matches the plan's new version intent.
- Real apply over existing metadata must remain blocked in this task.

Preferred naming from Task 264:

- Use `targetAssetVersion` as the external/task-scoped config field.
- If a helper is added, keep it small and close to `asset-version.mjs`.

## Forbidden Operations

This task forbids:

- runtime POST, including `POST /api/v1/jobs` and
  `POST /api/v1/jobs:from-storage`;
- submit-probe;
- live Mineru2Table query;
- live DB GET/PATCH/POST/PUT/DELETE;
- MinIO list/get/put/copy/move/delete/write/delete-marker;
- Docker/Compose restart/recreate/build/down/up/volume/prune;
- job-store read or edit;
- env, credential, model, secret, or sample mutation;
- cleanup, reset, rollback, retry, reparse, re-AI, or repair;
- worker, scheduler, or upload-server CleanService activation;
- UAT, L3, pressure PASS, production readiness, release readiness,
  production online, or go-live claims.

## Current Evidence

Dispatch anchor:

```text
main = origin/main = 56b5e36a4f7f1269a921795b4a1b57903c1d6557
```

Task 263 accepted only read-only live-evidence rehearsal:

- current accepted metadata remains `toc-rebuild v2`;
- existing physical/job-store `v3` is diagnostic dual-key evidence;
- product code can reconcile existing `v3` mock-safe with explicit
  `allowProbeJobIdSuffix=true`;
- no runtime success or DB apply was accepted.

Task 264 accepted planning-level direction:

- future path should use task-brief-scoped explicit `targetAssetVersion: "v4"`;
- it must be valid only with `intent=create-new-version`, non-empty reason,
  aligned completed v2 history, default allocation comparison, numeric
  version/order gates, preserved sourceInput/provenance/probe/apply blockers,
  and separate Director authorization for any runtime/query/DB apply.

## Positive Acceptance Criteria

Luceon can accept this task if:

- changed files stay within the allowed source/test/control-plane scope;
- default allocation from accepted `v2` remains `v3`;
- explicit `targetAssetVersion: "v4"` produces a mock-safe `v4` request/job id,
  sink, verifier expectation, persistence plan, and audit;
- audit records previous `v2`, default allocated `v3`, target `v4`, and final
  new `v4`;
- invalid target versions, missing intent/reason, equal/downgrade target,
  below-default target, failed/one-sided/missing-jobId/misaligned histories, and
  default/false `-probe` cases are blocked by tests;
- dry-run apply allows explicit new-version over existing metadata only when
  `newVersionIntent.newAssetVersion` exactly matches the target patch version;
- real apply over existing metadata remains blocked;
- no runtime/live/data operation is performed;
- report records exact branch, full HEAD, changed files, checks, and residual
  risk.

## Negative Acceptance Criteria

Luceon must return or block if Lucode:

- performs any forbidden live/runtime/data operation;
- edits files outside the allowed surface;
- weakens sourceInput, provenance, explicit intent, version order, or apply
  conflict gates;
- changes default allocation behavior when no target is supplied;
- allows persistent env/config override semantics;
- promotes diagnostic `v3` as durable metadata;
- uses readiness, UAT, L3, pressure PASS, release-readiness, production online,
  or go-live wording;
- omits exact branch/HEAD/report evidence.

## Required Checks

Minimum checks:

```text
git status --short --branch
git fetch origin --prune --tags
git checkout main
git pull --ff-only origin main
git checkout -b lucode/TASK-20260524-151650-P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite
git diff --check
node --check <changed .mjs files>
node server/tests/cleanservice-asset-version-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
```

If any check is skipped, the report must state the exact reason.

## Report Requirements

Write:

```text
TaskAndReport/2026-05-24T15-16-50+0800_P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite_REPORT.md
```

The report must include:

- task id and task brief path;
- exact remote branch and full HEAD;
- files changed;
- implementation summary;
- command table with exit codes;
- evidence for default `v3` and explicit target `v4`;
- safety gate matrix;
- skipped checks and exact reasons;
- risks, blockers, residual debt;
- whether Luceon review is required.

## Handoff

After completing the report, Lucode must update the branch-local row to:

```text
Status = Lucode 已回报待 Luceon 审查
Next Actor = Luceon
```

Then commit and push the branch to GitHub.

## Stop Rule

Stop and report blocked if the implementation requires runtime POST, live
DB/MinIO/job-store/runtime reads, DB apply, MinIO write, Docker mutation,
job-store edit, source/data cleanup, or a broader versioning redesign.

## Review Boundary

Acceptance of this task can only mean:

```text
Mock-safe code/test support for task-scoped targetAssetVersion v4 is accepted.
```

It must not mean runtime `v4` is authorized, physical `v4` artifacts exist,
DB apply is authorized, CleanService is activated, or the system is ready for
UAT/L3/pressure/readiness/go-live.
