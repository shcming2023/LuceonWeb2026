# TASK-20260524-164128-P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime Report

Report time: 2026-05-24T17:05:00+0800

## Task And Branch

Task:

```text
TASK-20260524-164128-P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime
```

Task brief:

```text
TaskAndReport/2026-05-24T16-41-28+0800_P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime_TASK.md
```

Branch:

```text
lucode/TASK-20260524-164128-P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime
```

Baseline:

```text
origin/main = 80d1af06a4850dddbf48d1182e000daab1a94d5e
```

Final remote branch HEAD is reported in the Lucode handoff after commit and push.
This report is part of that final commit, so it cannot embed its own final hash
without changing it.

## Files Changed

```text
M       src/store/types.ts
A       src/app/utils/cleanMaterialView.ts
A       src/app/components/CleanMaterialSummaryCard.tsx
M       src/app/pages/AssetDetailPage.tsx
M       src/app/pages/TaskDetailPage.tsx
A       TaskAndReport/2026-05-24T16-41-28+0800_P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
```

No files outside the task's allowed surface were edited.

## Implementation Summary

- Added focused Clean Material metadata types for existing task/material summary
  shapes.
- Added `buildCleanMaterialView()` as a read-only view helper over:
  - `material.metadata.cleanMaterials["toc-rebuild"]`;
  - `task.metadata.cleanServiceJobs["toc-rebuild"]`.
- Added `CleanMaterialSummaryCard` for the operator-visible summary and empty
  state.
- Added the card to:
  - `AssetDetailPage` under the existing processing pipeline;
  - `TaskDetailPage` overview tab above the existing status cards.

## Product Surface Summary

The new card shows:

- service name;
- status / clean state;
- current clean version;
- job id from task clean metadata;
- provenance object;
- source input object, SHA256, and size;
- total tokens;
- unresolved anchor count;
- artifact count;
- expandable artifact role/object refs.

When no Clean Material metadata exists, the card renders:

```text
暂无 Clean Material 元数据
```

## v4 Evidence And prefix=null Handling

The read model treats a Clean Material as present when material summary,
task summary, current version, provenance object, or artifact refs exist.
It does not require `material.metadata.cleanMaterials["toc-rebuild"].prefix`.

For the Task 267 shape:

```text
material.cleanMaterials.toc-rebuild.latestVersion = v4
material.cleanMaterials.toc-rebuild.status = completed
material.cleanMaterials.toc-rebuild.provenanceObjectName = toc-rebuild/1842780526581841/v4/provenance.json
material.cleanMaterials.toc-rebuild.prefix = null
task.cleanServiceJobs.toc-rebuild.jobId = luceon-task-1779085089451-toc-rebuild-v4
task.cleanServiceJobs.toc-rebuild.assetVersion = v4
task.cleanServiceJobs.toc-rebuild.artifacts = seven role refs
sourceInput.object = mineru/1842780526581841/v1/content_list_v2.json
sourceInput.sha256 = f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
sourceInput.size_bytes = 31543
stats.tokensTotal = 6266
stats.unresolvedAnchorCount = 0
```

The card displays v4 and shows a quiet prefix-gap note:

```text
prefix 为空；当前摘要使用 task artifact refs 与 material provenance ref 展示，不隐藏已接受版本。
```

No artifact content fetch is required.

## Commands

| Command | Exit | Notes |
| --- | ---: | --- |
| `git status --short --branch` | 0 | initial branch status checked |
| `git fetch origin --prune --tags` | 0 | fetched `origin/main` |
| `git checkout main` | 0 | returned to main |
| `git pull --ff-only origin main` | 0 | fast-forwarded to `80d1af06a4850dddbf48d1182e000daab1a94d5e` |
| `git checkout -b lucode/TASK-20260524-164128-P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime` | 0 | scoped branch created |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | PASS |
| `npx pnpm@10.4.1 run build` | 1 | first attempt failed before app build because local Rollup optional package `@rollup/rollup-darwin-arm64` was missing from `node_modules` |
| `CI=true npx pnpm@10.4.1 install --frozen-lockfile` | 0 | rebuilt local `node_modules`; lockfile stayed up to date |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | PASS after dependency repair |
| `npx pnpm@10.4.1 run build` | 0 | PASS; Vite built 1648 modules, with existing >500 kB chunk warning |
| `git diff --check origin/main...HEAD` | 0 | no whitespace errors |

No required check was skipped.

## Boundary Statement

No CleanService runtime run, Mineru2Table POST/query/probe, DB
POST/PATCH/PUT/DELETE, MinIO write/copy/move/delete/cleanup, Docker/Compose
operation, job-store edit, upload, retry, reparse, Re-AI, model/env/secret/sample
mutation, production deployment, production runtime validation, UAT, L3, pressure
PASS, release readiness, production online, or go-live claim was performed.

## Risks And Residual Debt

- This is a minimal read-only surface, not a generalized CleanService registry.
- Material `prefix=null` remains a data normalization debt. The UI handles it
  without hiding v4, but no DB correction was made.
- Artifact content preview/download authorization remains deferred.
- Browser runtime verification was not run; the static TypeScript/build checks
  passed and no production/runtime operation was performed.

Luceon review is required.
