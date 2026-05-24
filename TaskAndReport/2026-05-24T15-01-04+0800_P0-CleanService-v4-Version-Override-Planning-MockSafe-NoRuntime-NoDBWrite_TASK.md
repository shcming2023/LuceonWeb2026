# TASK-20260524-150104-P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite

Issued at: 2026-05-24T15:01:04+0800

Actor: Lucode

## Mainline Objective

Plan a clean future path for `toc-rebuild v4` / version-override evidence so
the project does not elevate the current diagnostic dual-key `v3` record into
durable Clean Material metadata.

This is a planning/design task only. It should prepare the next implementation
or validation task, not implement it.

## Critical Path Scope

Lucode must produce a bounded planning report that answers:

1. What version-override semantics are needed to intentionally target `v4`
   while current DB metadata remains accepted `v2`.
2. Whether the override should be Director-authorized per run, task-brief
   scoped, config-scoped, or impossible without explicit code support.
3. How to preserve existing safety gates:
   - completed/aligned history required before explicit new-version;
   - no silent legacy parsed evidence promotion;
   - completed-job `sourceInput` fallback remains traceable;
   - `-probe` provenance remains rejected unless explicitly allowed;
   - real apply/mismatch conflicts remain blocked.
4. What the smallest mock-safe implementation task would need to change later,
   including allowed files, tests, and stop rules.
5. What later runtime/DB-apply decisions would still require Director approval.

This task must not change business logic. If Lucode discovers that source-code
changes are needed, record the proposed diff shape in the report and stop.

## True Preconditions

- Start from current GitHub `main`.
- Read the Task 263 report first, then only directly relevant Task 259-263
  evidence and CleanService source/test files.
- Treat current DB accepted state as `toc-rebuild v2`.
- Treat existing physical/job-store `v3` as diagnostic dual-key evidence only.
- Preserve Task 263's non-claims: no runtime success, no DB apply, no readiness.

## Deferrable Side Work

Defer all of the following:

- implementation of version override;
- runtime POST or live Mineru2Table query;
- DB apply or DB metadata migration;
- worker/scheduler/upload-server activation;
- `v4` physical artifact creation;
- fresh sample selection;
- provenance-quality repair for existing `input size_bytes=0`;
- UI/operator review changes;
- broad Clean Material quality review.

## Fast Validation Target

The smallest useful output is a design/report that can seed the next task brief:

- a recommended version-override policy;
- a concrete no-runtime implementation boundary for a later Lucode task;
- positive and negative test matrix;
- blocked/forbidden operation list;
- recommendation for what Luceon should ask the Director to authorize next.

## Environment And Write Boundary

Default workspace:

```text
/Users/concm/Dev_workspace/Luceon2026
```

Lucode must work on a scoped branch:

```text
lucode/TASK-20260524-150104-P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite
```

Allowed writes:

- `TaskAndReport/2026-05-24T15-01-04+0800_P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite_REPORT.md`
- branch-local `TaskAndReport/TASK_TRACKING_LIST.md`

No source-code, PRD, architecture-doc, package, config, env, Docker, data,
sample, or external-repo edits are allowed in this task.

## Allowed Reads

- `TaskAndReport/TASK_TRACKING_LIST.md`
- this task brief
- Task 259, Task 260, Task 261, Task 263 task/report/review files
- directly relevant CleanService files, likely:
  - `server/services/cleanservice/asset-version.mjs`
  - `server/services/cleanservice/orchestration-runner.mjs`
  - `server/services/cleanservice/cleanservice-worker.mjs`
  - `server/services/cleanservice/raw-material-adapter.mjs`
  - `server/services/cleanservice/output-verifier.mjs`
  - `server/services/cleanservice/metadata-apply-executor.mjs`
  - `server/tests/cleanservice-*.mjs`

No live DB, MinIO, Docker, Mineru2Table job-store, runtime, or external API read
is required. If Lucode believes a live read is required, stop and report why.

## Forbidden Operations

This task forbids:

- business source-code edits;
- runtime POST, including `POST /api/v1/jobs` and
  `POST /api/v1/jobs:from-storage`;
- submit-probe;
- live Mineru2Table query;
- DB GET/PATCH/POST/PUT/DELETE;
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
main = origin/main = ee317c2d96bf5f19f5700cd1dab8dadd144bc5a3
```

Task 263 accepted only read-only live-evidence rehearsal:

- live-shaped DB payload still has current accepted `toc-rebuild v2`;
- live task lacks canonical `metadata.rawMaterial.mineru.contentListV2`;
- completed-job `sourceInput` fallback is present and traceable;
- MinIO contains seven existing `v3` artifacts;
- job-store contains both canonical and `-probe` completed `v3` keys pointing
  to the same prefix;
- current main product rehearsal can reach `DRY_RUN_SUCCESS` for existing `v3`
  with `submitJob=0`, `queryJob=0`, DB updates `0`, and explicit
  `allowProbeJobIdSuffix=true`;
- `v3` remains diagnostic and not DB-applied.

## Planning Questions

The report must answer these questions clearly:

1. Should `v4` be selected by a dedicated `targetAssetVersion`, an
   `assetVersionOverride`, a `newVersionStrategy`, or another explicit field?
2. What exact preconditions must be true before a version override can be used?
3. How does the override interact with `allocateAssetVersion()`?
4. How does it interact with explicit `create-new-version` intent and
   `newVersionReason`?
5. How should the system prevent override reuse, downgrade, skipped-version
   ambiguity, or accidental overwrite of existing clean prefixes?
6. How should tests prove that default behavior still allocates `v3` from DB
   `v2`, while an explicit override can target `v4` only under authorization?
7. What should remain blocked until a later Director-authorized runtime task?

## Positive Acceptance Criteria

Luceon can accept this planning task if the report:

- states one recommended version-override policy and alternatives rejected;
- specifies exact future implementation surfaces and tests;
- preserves current safety gates and explains how they are tested;
- distinguishes mock-safe implementation evidence from runtime evidence;
- keeps existing `v3` classified as diagnostic dual-key evidence;
- includes a stop rule for any future task that would require runtime POST,
  DB apply, MinIO write, job-store edit, Docker mutation, or source/data cleanup;
- includes a recommended next task title and scope.

## Negative Acceptance Criteria

Luceon must return or block if Lucode:

- edits business source code in this planning task;
- performs live DB/MinIO/job-store/runtime reads;
- performs runtime POST or submit-probe;
- proposes promoting `v3` diagnostic evidence into durable DB metadata without
  separate Director decision;
- weakens `sourceInput`, provenance, explicit intent, or apply-conflict gates;
- uses readiness, UAT, L3, pressure PASS, release-readiness, or go-live wording;
- omits exact branch/HEAD/report evidence.

## Required Checks

Minimum checks:

- `git status --short --branch`
- `git fetch origin --prune --tags`
- `git checkout main`
- `git pull --ff-only origin main`
- `git checkout -b <scoped branch>`
- `git diff --check`

Optional read-only static checks may be run if they help confirm file names or
test names, but this task should not run broad implementation test suites unless
the report explains why.

## Report Requirements

Write:

```text
TaskAndReport/2026-05-24T15-01-04+0800_P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite_REPORT.md
```

The report must include:

- task id and brief path;
- branch and exact full HEAD;
- files changed;
- documents/source files read;
- planning recommendation;
- rejected alternatives;
- proposed future implementation scope;
- proposed test matrix;
- risk and residual debt;
- skipped checks and exact reasons;
- whether Luceon review is required.

## Handoff

After completing the report, Lucode must update the branch-local row to:

```text
Status = Lucode 已回报待 Luceon 审查
Next Actor = Luceon
```

Then commit and push the branch to GitHub.

## Stop Rule

Stop and report blocked if the planning cannot be completed without source-code
changes, runtime reads, DB/MinIO/job-store access, POST, or any forbidden
operation.

## Review Boundary

Acceptance of this task can only mean:

```text
Version-override/v4 planning accepted as a basis for the next scoped task.
```

It must not mean version override is implemented, runtime `v4` is authorized,
DB apply is authorized, or CleanService is ready for activation.
