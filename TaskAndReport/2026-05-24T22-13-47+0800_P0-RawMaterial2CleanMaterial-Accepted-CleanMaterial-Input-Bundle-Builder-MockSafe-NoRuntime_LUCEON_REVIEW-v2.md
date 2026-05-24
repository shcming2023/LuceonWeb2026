# TASK-20260524-215051-P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime Luceon Review v2

Review time: 2026-05-24T22:13:47+0800

Decision:

```text
ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_INTEGRATION_AND_HEAD_CORRECTION
```

## Reviewed Evidence

Task brief:

```text
TaskAndReport/2026-05-24T21-50-51+0800_P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime_TASK.md
```

Lucode report:

```text
TaskAndReport/2026-05-24T21-50-51+0800_P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime_REPORT.md
```

Previous return review:

```text
TaskAndReport/2026-05-24T22-05-10+0800_P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime_LUCEON_REVIEW.md
```

Accepted remote branch:

```text
origin/lucode/TASK-20260524-215051-P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime
```

Accepted remote HEAD:

```text
0119e025e14a6afbe8574bcd0f00b25f4bb68ca1
```

Review baseline:

```text
origin/main@b57c7b96e4ebeb3989f0b1f2e0f1f42e68c18489
```

Lucode's revised report still does not self-embed the final pushed remote branch
full HEAD. Luceon verified the GitHub-visible remote HEAD above and records this
as a control-plane evidence correction, not a return blocker.

## Scope Review

Accepted changed files:

```text
A       TaskAndReport/2026-05-24T21-50-51+0800_P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
A       server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs
A       src/app/utils/rawMaterial2CleanMaterialInputBundle.ts
```

The branch stayed inside the helper/test/control-plane scope. Luceon found no
live DB, MinIO, runtime, Docker, production, Mineru2Table, downstream service
execution, UI workflow, batch, permission, or readiness path in the changed
implementation files.

## Accepted Behavior

Accepted at code/test level:

- Pure helper builds a traceable
  `raw-material-2-clean-material-input` bundle only from already-present
  accepted Clean Material metadata.
- Helper requires `serviceName=toc-rebuild`.
- Helper requires `operatorDecision.state=accepted`.
- Bundle contains material/task ids, serviceName, assetVersion, jobId,
  provenance object, sourceInput, required artifact refs, optional artifact refs
  when present, and accepted decision metadata.
- Required artifact refs are `readable_tree`, `logic_tree`, `skeleton`, and
  `flooded_content`.
- Helper blocks missing material/task, unsupported service, missing summaries,
  material/task mismatch, non-accepted decision, non-completed service, missing
  or mismatched asset version, missing or mismatched job id, missing provenance,
  missing sourceInput, missing required artifacts, artifact prefix mismatch, and
  body-shaped artifact refs.
- The returned asset-version blocker is closed: material/task/snapshot/current
  version signals are collected independently and all present signals must
  match before a bundle is built.

## Luceon Checks

```text
git diff --name-status origin/main...origin/lucode/TASK-20260524-215051-P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime
```

Result: file list shown in scope review.

```text
git diff --check origin/main...origin/lucode/TASK-20260524-215051-P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime
```

Result: PASS.

```text
node server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs
```

Result: PASS.

```text
npx pnpm@10.4.1 exec tsc --noEmit
```

Result: PASS.

```text
npx pnpm@10.4.1 run build
```

Result: PASS with the existing Vite chunk-size warning.

Luceon also reran the returned-blocker probe independently:

```text
material/current version = v4
task cleanServiceJobs.toc-rebuild.assetVersion = v5
```

Result:

```text
ok = false
code = ASSET_VERSION_MISMATCH
mismatchedSignals = [{ source: "task.assetVersion", value: "v5" }]
```

## Acceptance Boundary

This is code/test acceptance only.

Not accepted:

- live DB read/write;
- MinIO read/write/delete/list/get;
- runtime execution;
- RawMaterial2CleanMaterial transport, endpoint, service, scheduler, worker, or
  execution;
- Mineru2Table call;
- DB persistence of downstream bundles;
- UI launch/workflow;
- batch processing;
- permissions/governance;
- production validation;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live.

## Next Mainline Recommendation

The next mainline step should stay narrow: either a read-only live-shape
verification that the persisted accepted canonical sample can build this bundle
from current DB metadata without writing anything, or a separately authorized
single-sample RawMaterial2CleanMaterial protocol planning task. Do not jump
straight to service execution before the live-shape input bundle has been
verified.
