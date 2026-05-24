# TASK-20260524-215051-P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime Luceon Review

Review time: 2026-05-24T22:05:10+0800

Decision:

```text
RETURNED_FOR_ASSET_VERSION_ALIGNMENT_BLOCKER
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

Reviewed remote branch:

```text
origin/lucode/TASK-20260524-215051-P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime
```

Reviewed remote HEAD:

```text
56ae89dbebbc3b2e7c646cfd8d7f8c885ee4cd66
```

Review baseline:

```text
origin/main@d8c3aa5bb340f469140db3542bdbfc4199105756
```

## Scope Review

Changed files:

```text
A       TaskAndReport/2026-05-24T21-50-51+0800_P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
A       server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs
A       src/app/utils/rawMaterial2CleanMaterialInputBundle.ts
```

The branch stayed within the intended helper/test/control-plane scope. Luceon
found no live DB, MinIO, runtime, Docker, production, or downstream service
execution path in the changed implementation files.

## Passing Checks

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

## Return Blocker

The helper does not reject a material/task asset-version mismatch when the
material summary and caller current version are `v4`, but the task
`cleanServiceJobs.toc-rebuild.assetVersion` is `v5`.

Luceon independent probe:

```text
material.metadata.cleanMaterials.toc-rebuild.latestVersion = v4
currentAssetVersion = v4
task.metadata.cleanServiceJobs.toc-rebuild.assetVersion = v5
task.metadata.cleanServiceJobs.toc-rebuild.jobId = job-v4
artifact refs = toc-rebuild/1842780526581841/v4/*
```

Actual result:

```text
ok = true
bundle.assetVersion = v4
```

Expected result:

```text
ok = false
code = ASSET_VERSION_MISMATCH
```

Why this blocks acceptance:

- the task brief requires current-version alignment and says missing or
  mismatched asset version must block;
- this helper is the gate between accepted Clean Material and the future
  RawMaterial2CleanMaterial input;
- accepting a bundle when task/material version evidence is inconsistent would
  let downstream input become traceably ambiguous.

## Required Correction

Lucode should keep the same narrow scope and fix only this blocker:

1. Extract material summary version, task summary version, operator decision
   snapshot version, and caller `currentAssetVersion` independently.
2. Require all present version signals to match.
3. Return `ASSET_VERSION_MISMATCH` with details when any present version signal
   differs.
4. Add or extend the focused smoke to cover at least:
   - material `v4` + task `v5` blocks;
   - material `v4` + snapshot `v5` blocks;
   - caller `currentAssetVersion=v5` with material/task/snapshot `v4` blocks.

Do not expand into RawMaterial2CleanMaterial execution, service protocol, UI,
live DB/MinIO reads, Docker, production validation, workflow, batch, permissions,
or readiness work.

## Secondary Evidence Issue

Lucode's report does not self-embed the final pushed remote branch full HEAD.
This is a control-plane evidence issue that should be corrected in the revised
report, but it is not the main functional blocker.

## Acceptance Boundary

This return review does not accept the branch. No source implementation was
merged to `main` by Luceon.

No live DB read/write, MinIO read/write/delete, runtime, Docker/production
operation, RawMaterial2CleanMaterial execution, UAT, L3, pressure PASS, release
readiness, production readiness, production online, or go-live claim was made.
