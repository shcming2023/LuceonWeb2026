# Task 265 Report: CleanService targetAssetVersion v4 Mock-Safe Implementation

Report time: 2026-05-24T15:26:22+0800

## 1. Task And Branch

Task:

```text
TASK-20260524-151650-P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite
```

Task brief:

```text
TaskAndReport/2026-05-24T15-16-50+0800_P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite_TASK.md
```

Branch:

```text
lucode/TASK-20260524-151650-P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite
```

Implementation baseline:

```text
HEAD = origin/main = 2116432c5661a2e7186021e8f4f12e4500472c26
```

Final pushed branch HEAD is reported in the Lucode handoff after commit and
push. This report is part of that final commit, so it cannot embed its own final
hash without changing it.

## 2. Files Changed

```text
M       server/services/cleanservice/asset-version.mjs
M       server/services/cleanservice/cleanservice-worker.mjs
M       server/services/cleanservice/orchestration-runner.mjs
M       server/services/cleanservice/metadata-apply-executor.mjs
M       server/tests/cleanservice-asset-version-smoke.mjs
M       server/tests/cleanservice-orchestration-runner-smoke.mjs
M       server/tests/cleanservice-metadata-apply-executor-smoke.mjs
A       TaskAndReport/2026-05-24T15-16-50+0800_P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
```

No files outside the allowed task surface were edited.

## 3. Implementation Summary

`asset-version.mjs`:

- added numeric asset-version parsing/comparison helpers;
- added `resolveAssetVersion()` to preserve the default allocator result while
  optionally resolving an explicit `targetAssetVersion`;
- rejects invalid targets and targets below default allocation or not greater
  than the previous accepted version.

`cleanservice-worker.mjs`:

- request planning now uses `resolveAssetVersion()`;
- direct request planning rejects `targetAssetVersion` unless
  `intent=create-new-version`;
- target planning still feeds the same job id, `asset_version`, and sink prefix
  fields used by the existing protocol request.

`orchestration-runner.mjs`:

- rejects `targetAssetVersion` unless the explicit new-version intent gate is
  active;
- validates and resolves the target version after completed/aligned history
  preconditions pass;
- passes the resolved target to request planning without double allocation;
- records `defaultAllocatedAssetVersion`, `targetAssetVersion`, and final
  `newAssetVersion` in `plan.newVersionIntent` and bounded result audit.

`metadata-apply-executor.mjs`:

- dry-run explicit new-version over existing metadata still requires
  `newVersionIntent.newAssetVersion` to match the target patch version;
- if `targetAssetVersion` is present, it must also match that new version;
- real apply over existing metadata remains blocked.

## 4. Evidence For Default v3 And Explicit Target v4

Default behavior:

- Existing asset-version smoke still proves completed `v2` allocates `v3`.
- Existing runner positive rerun test still proves no target override keeps
  `v2 -> v3` behavior.

Explicit target behavior:

- New runner test with completed/aligned `v2` history plus
  `intent=create-new-version`, non-empty `newVersionReason`, and
  `targetAssetVersion="v4"` produces:
  - request `asset_version=v4`;
  - request job id `luceon-task-clean-123-toc-rebuild-v4`;
  - sink prefix `toc-rebuild/1842780526581841/v4/`;
  - verifier expected `assetVersion=v4`;
  - persistence plan `newVersionIntent.newAssetVersion=v4`;
  - audit `defaultAllocatedAssetVersion=v3`;
  - audit `targetAssetVersion=v4`.

## 5. Safety Gate Matrix

| Gate | Coverage |
| --- | --- |
| No target supplied keeps default allocation | Existing asset-version and runner smokes |
| `targetAssetVersion` requires `create-new-version` | New runner negative test |
| `newVersionReason` remains required | Existing runner negative test |
| Completed/aligned two-sided history remains required | Existing runner negative tests |
| Invalid version such as `vABC` blocks | New asset-version and runner negative tests |
| Equal/downgrade/below-default target blocks | New asset-version and runner negative tests |
| Request/job/sink/verifier/plan/audit agree on v4 | New runner positive test |
| Default/false `-probe` remains rejected | Existing runner/output-verifier tests |
| Real apply over existing metadata remains blocked | Existing apply-executor test |
| Target mismatch in newVersionIntent blocks dry-run apply | New apply-executor negative test |

## 6. Checks

| Command | Exit | Notes |
| --- | ---: | --- |
| `git status --short --branch` | 0 | clean at task start on `main` |
| `git fetch origin --prune --tags` | 0 | main fast-forwarded before task |
| `git checkout main` | 0 | already synchronized before branch |
| `git pull --ff-only origin main` | 0 | fast-forwarded to task dispatch state |
| `git checkout -b lucode/TASK-20260524-151650-P0-CleanService-targetAssetVersion-v4-Override-MockSafe-Planning-to-Code-NoRuntime-NoDBWrite` | 0 | scoped branch created |
| `node --check` for changed source/tests | 0 | no syntax errors |
| `node server/tests/cleanservice-asset-version-smoke.mjs` | 0 | PASS |
| `node server/tests/cleanservice-orchestration-runner-smoke.mjs` | 0 | PASS 28/28 |
| `node server/tests/cleanservice-metadata-apply-executor-smoke.mjs` | 0 | PASS |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | PASS |
| mock-safe `cleanservice-*.mjs` loop excluding Task 256 runtime harness | 0 | PASS |
| `git diff --check` | 0 | no output |

No required check was skipped. The Task 256 runtime harness was excluded only
from the extra mock-safe loop because this task forbids runtime operations and
that harness is explicitly runtime-oriented.

## 7. Safety Statement

No runtime POST, `POST /api/v1/jobs:from-storage`, submit-probe, live
Mineru2Table query, live DB GET/PATCH/POST/PUT/DELETE, MinIO
list/get/put/copy/move/delete/write, Docker/Compose operation, job-store read
or edit, env/credential/model/secret/sample mutation, cleanup/reset/rollback,
worker activation, DB apply, UAT, L3, pressure PASS, readiness, production
online, or go-live claim was performed.

## 8. Residual Risk

This is mock-safe code/test support only. It does not authorize or prove
runtime `v4`, physical `v4` artifacts, DB metadata apply, worker activation, or
production readiness. A later Director-authorized runtime/DB-apply task is still
required before any live validation or durable metadata change.

Luceon review is required.
