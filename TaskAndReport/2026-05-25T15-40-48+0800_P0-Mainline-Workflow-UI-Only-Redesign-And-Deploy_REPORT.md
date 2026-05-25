# P0 Mainline Workflow UI Only Redesign And Deploy Report

Reported at: 2026-05-25T15:40:48+0800

Task ID: TASK-20260525-154048-P0-Mainline-Workflow-UI-Only-Redesign-And-Deploy

Result: `SUCCESS_MAINLINE_UI_SURFACE_REBUILT`

## Trigger

The Director requested a UI-only redesign so the project mainline is clear:

```text
提交 PDF -> MinerU 解析 -> AI 元数据识别 -> 目录重建 -> Raw Material 输出 -> Clean Material
```

## Scope

UI-only. No backend behavior, DB schema, MinIO object, CleanService runtime, or
pipeline execution changes.

## Changes

- Added `src/app/utils/mainlinePipeline.ts` to derive a consistent front-end
  mainline view from material/task metadata.
- Added `src/app/components/MainlinePipelinePanel.tsx` to render the mainline
  as a six-step product surface.
- Added the mainline panel to asset detail pages so each asset clearly shows
  where it is in the pipeline.
- Added the mainline panel to the library page so the global product surface
  shows the same PDF/MinerU/AI/toc-rebuild/Raw/Clean flow.
- Preserved the library Clean Material surface from Task 294: `目录重建` column,
  grid badges, counts, filter, and clean-aware search.

## Checks

| Check | Exit |
| --- | ---: |
| `npx tsc --noEmit` | 0 |
| `npm run build` | 0 |
| `git diff --check` | 0 |

## Explicitly Not Done

- No DB write.
- No MinIO write/list/delete/copy/move/cleanup.
- No upload, submit-probe, pressure test, runtime CleanService POST, or
  RawMaterial2CleanMaterial execution.
- No readiness, UAT, L3, pressure PASS, production-readiness, or go-live claim.

## Deployment

Deployed to the local production runtime for manual evaluation:

```bash
git pull --ff-only origin main
docker compose up -d --build --no-deps cms-frontend
```

Deployed source:

```text
ab45d97
```

Only `cms-frontend` was rebuilt/recreated. DB, upload-server, and MinIO were not
recreated for this UI-only change.

## Browser Validation

Playwright browser checks passed against the deployed runtime:

| Page | Result | Screenshot |
| --- | --- | --- |
| `/cms/asset/548758763373874` | mainline panel and all six steps visible | `/tmp/luceon-mainline-asset.png` |
| `/cms/library` | mainline panel, counts, directory-rebuild filter/column, and Raw2Clean labels visible | `/tmp/luceon-mainline-library.png` |

Validated visible text includes:

- `资产处理主线`;
- `提交 PDF`;
- `MinerU 解析`;
- `AI 元数据识别`;
- `目录重建`;
- `Raw Material`;
- `Clean Material`;
- `Raw2Clean`.
