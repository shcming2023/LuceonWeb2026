# Task 264 Report: CleanService v4 Version Override Planning

Report time: 2026-05-24T15:05:17+0800

## 1. Task And Branch

Task:

```text
TASK-20260524-150104-P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite
```

Task brief:

```text
TaskAndReport/2026-05-24T15-01-04+0800_P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite_TASK.md
```

Branch:

```text
lucode/TASK-20260524-150104-P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite
```

Planning baseline:

```text
HEAD = origin/main = 3c8651c381bebda2e2f24176e8c35e3ae9e70658
```

Final pushed branch HEAD is reported in the Lucode handoff after commit and
push. This planning report is part of that final commit, so the final hash
cannot be embedded in the file without changing the hash.

## 2. Files Changed

```text
A       TaskAndReport/2026-05-24T15-01-04+0800_P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
```

No business source code, PRD, architecture doc, package, config, env, Docker,
data, sample, or external-repo file was edited.

## 3. Files Read

```text
TaskAndReport/TASK_TRACKING_LIST.md
TaskAndReport/2026-05-24T15-01-04+0800_P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite_TASK.md
TaskAndReport/2026-05-24T14-47-59+0800_P0-CleanService-PostTask261-Existing-v3-Live-Evidence-ReadOnly-Revalidation-NoPost-NoDBWrite_REPORT.md
server/services/cleanservice/asset-version.mjs
server/services/cleanservice/orchestration-runner.mjs
server/services/cleanservice/cleanservice-worker.mjs
server/services/cleanservice/raw-material-adapter.mjs
server/services/cleanservice/metadata-apply-executor.mjs
server/tests/cleanservice-asset-version-smoke.mjs
server/tests/cleanservice-orchestration-runner-smoke.mjs
server/tests/cleanservice-metadata-apply-executor-smoke.mjs
```

No live DB, MinIO, Docker, Mineru2Table job-store, runtime, or external API read
was performed.

## 4. Planning Recommendation

Recommended policy:

```text
Use a task-brief-scoped explicit targetAssetVersion for the next mock-safe
implementation task.
```

Suggested future config shape:

```js
{
  intent: 'create-new-version',
  newVersionReason: 'director-authorized-v4-after-diagnostic-v3',
  targetAssetVersion: 'v4'
}
```

Rationale:

- `targetAssetVersion` is clearer than a generic override because it names the
  intended output version, not an algorithmic shortcut.
- It should be valid only inside explicit `create-new-version` intent.
- It should be authorized by a concrete task brief per run, not by default env
  or long-lived config, because skipping `v3` as durable metadata is a product
  decision tied to the diagnostic dual-key evidence.
- It should not promote existing diagnostic `v3`; it should target a new `v4`
  plan and keep `v3` as non-durable evidence.

Rejected alternatives:

- `assetVersionOverride`: too broad; sounds like it could bypass allocator and
  persistence gates for arbitrary reasons.
- `newVersionStrategy`: useful later, but too vague for the immediate single
  `v2 -> v4` decision.
- Config-scoped or env-scoped override: too persistent and easy to reuse
  accidentally after the authorized run.
- Automatic allocator change to skip diagnostic versions: unsafe because the
  allocator currently sees only metadata, not physical/job-store diagnostics.
- Declaring override impossible without runtime reads: unnecessary for the
  mock-safe implementation path; code can validate explicit version semantics
  from injected/current task-material fixtures.

## 5. Required Preconditions For A Future Override

The future implementation should require all of the following before accepting
`targetAssetVersion`:

- `config.intent === 'create-new-version'`;
- non-empty `config.newVersionReason`;
- `config.targetAssetVersion` matches numeric `vN`;
- existing task clean job and material clean material are both present,
  completed, aligned, and have a previous jobId;
- the default allocator result is computed and recorded for comparison;
- target version is greater than the current accepted metadata version;
- target version is greater than or equal to the default allocator result;
- target version is not equal to the previous accepted version;
- no active duplicate clean job is present;
- source input remains canonical-first with completed-job `sourceInput`
  fallback only;
- verifier still rejects provenance `-probe` unless
  `allowProbeJobIdSuffix === true`;
- real apply remains blocked unless a separate Director-authorized DB-apply task
  explicitly changes the apply boundary.

Recommended handling of default allocator interaction:

```text
allocateAssetVersion(task, serviceName) remains the default source of truth.
targetAssetVersion may replace the request assetVersion only after explicit
new-version preconditions pass and after version-shape/order checks pass.
```

For current accepted `v2`, default allocation should still produce `v3`.
With Director-scoped `targetAssetVersion: 'v4'`, the request should intentionally
target `v4`, and the audit should record both:

```text
defaultAllocatedAssetVersion = v3
targetAssetVersion = v4
```

## 6. Proposed Future Implementation Scope

Smallest next implementation task should be mock-safe/no-runtime/no-DB-write.

Allowed future source surfaces:

```text
server/services/cleanservice/asset-version.mjs
server/services/cleanservice/cleanservice-worker.mjs
server/services/cleanservice/orchestration-runner.mjs
server/services/cleanservice/metadata-apply-executor.mjs
server/tests/cleanservice-asset-version-smoke.mjs
server/tests/cleanservice-orchestration-runner-smoke.mjs
server/tests/cleanservice-metadata-apply-executor-smoke.mjs
```

Likely diff shape:

- add a small planner/helper, preferably near `asset-version.mjs`, that returns
  default allocation plus optional accepted target version;
- make `buildCleanServiceJobRequest()` consume the resolved version rather than
  unconditionally calling `allocateAssetVersion()` internally, or pass a
  resolved version through config/internal options;
- make `orchestration-runner` validate `targetAssetVersion` only after
  completed/aligned explicit-new-version preconditions pass;
- include `targetAssetVersion`, `defaultAllocatedAssetVersion`, and
  `newAssetVersion` in `plan.newVersionIntent` audit;
- keep apply executor strict by requiring `newVersionIntent.newAssetVersion`
  exactly equals the target patch version.

Stop rule for that future task:

```text
Stop if proving prefix absence, runtime submit, live job query, DB apply,
MinIO write, job-store edit, Docker mutation, or cleanup is required.
```

## 7. Proposed Test Matrix

Positive tests:

- default current accepted `v2` plus no override still allocates `v3`;
- explicit `create-new-version` plus `targetAssetVersion: 'v4'` creates request
  jobId/sink/artifact expectations for `v4`;
- audit records previous `v2`, default allocated `v3`, and target/new `v4`;
- completed-job `sourceInput` fallback still supplies raw input for the v4
  request;
- explicit `allowProbeJobIdSuffix=true` remains required only for probe-shaped
  provenance fixtures.

Negative tests:

- `targetAssetVersion` without `intent=create-new-version` is blocked;
- missing `newVersionReason` is blocked;
- one-sided, failed, missing-jobId, or misaligned existing metadata is blocked;
- downgrade/equal version such as `v2` is blocked;
- skipped version below default allocator output is blocked when applicable;
- invalid versions such as `vABC` are blocked;
- default/false probe policy still rejects `-probe`;
- `plan.newVersionIntent.newAssetVersion` mismatch still blocks dry-run apply;
- real apply over existing metadata remains `BLOCKED_EXISTING_TOC_REBUILD_METADATA`.

## 8. Later Director Decisions Still Required

Separate Director approval is still required for:

- any runtime `POST /api/v1/jobs` or `jobs:from-storage`;
- any live Mineru2Table job query;
- any DB metadata apply;
- any MinIO write/copy/move/delete or physical `v4` artifact creation;
- any job-store edit or cleanup;
- deciding whether `v3` diagnostic evidence should remain only audit evidence
  or be referenced in a later review note;
- worker/scheduler/upload-server activation;
- UAT, L3, pressure, readiness, release, production online, or go-live claims.

## 9. Recommended Next Task

Recommended title:

```text
P0 CleanService targetAssetVersion v4 Override MockSafe Planning-to-Code NoRuntime NoDBWrite
```

Recommended scope:

```text
Implement task-brief-scoped targetAssetVersion validation and mock-safe v2 -> v4
request planning, with no runtime POST, no live reads, no DB/MinIO write, and no
real apply.
```

Acceptance should mean code/test-level planning support only. It should not mean
runtime `v4` is authorized or that DB apply is authorized.

## 10. Checks

```text
git status --short --branch: exit 0
git fetch origin --prune --tags: exit 0
git checkout main: exit 0
git pull --ff-only origin main: exit 0
git checkout -b lucode/TASK-20260524-150104-P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite: exit 0
git rev-parse HEAD origin/main: exit 0, both 3c8651c381bebda2e2f24176e8c35e3ae9e70658
git diff --check: exit 0
```

Broad implementation test suites were not run because this task made no source
code changes and the task brief asks for a planning report only.

## 11. Safety Statement

No business source-code edit, live DB/MinIO/job-store/runtime read, runtime
POST, submit-probe, live Mineru2Table query, DB/MinIO write, Docker/Compose
mutation, env/credential/model/sample mutation, cleanup/reset/rollback/retry,
worker activation, DB apply, readiness, L3, pressure PASS, release readiness,
production online, or go-live claim was performed.

Luceon review is required.
