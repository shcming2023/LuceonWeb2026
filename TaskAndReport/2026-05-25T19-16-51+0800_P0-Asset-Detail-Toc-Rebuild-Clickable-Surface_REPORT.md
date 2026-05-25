# P0 Asset Detail Toc Rebuild Clickable Surface Report

## Result

`SUCCESS_TOC_REBUILD_STEP_CLICKABLE_ON_ASSET_DETAIL`

## Trigger

The Director observed that `目录重建` on `/cms/asset/548758763373874` looked like a mainline step but could not be clicked.

## Root Cause

The `资产处理主线` panel was implemented as a pure status surface. The actual toc-rebuild output and artifact preview existed below in the `Clean Material` card, but the mainline `目录重建` step had no link to that inspection surface.

## Change

- `MainlinePipelinePanel` now accepts a narrow `stepLinks` map.
- Linked steps render as accessible anchors with focus/hover affordance and `查看产物` cue.
- Asset detail links the `toc` step to `#clean-material-toc-rebuild` only when Clean Material/toc-rebuild metadata is present.
- `CleanMaterialSummaryCard` now exposes `id="clean-material-toc-rebuild"` with `scroll-mt-24`.
- Pending toc-rebuild state now says `待执行目录重建` instead of implying that a product already exists.

## Checks

- `npx tsc --noEmit` passed.
- `npm run build` passed.
- `git diff --check` passed.

## Boundary

UI-only navigation fix. No DB write, MinIO write/delete/copy/move/cleanup, upload, submit-probe, CleanService POST, RawMaterial2CleanMaterial execution, Docker volume mutation, pressure/UAT/L3/readiness/go-live claim.

## Next Validation

After production redeploy:

- Assets with existing Clean Material/toc-rebuild artifacts should show a clickable `目录重建` step that jumps to the artifact inspection area.
- Assets without Clean Material/toc-rebuild artifacts should show `待执行目录重建` and no fake product link.
