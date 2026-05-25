# P0 Library CleanMaterial TocRebuild Surface Restore And Deploy Report

Reported at: 2026-05-25T15:35:28+0800

Task ID: TASK-20260525-153528-P0-Library-CleanMaterial-TocRebuild-Surface-Restore-And-Deploy

Result: `FIXED_LIBRARY_CLEAN_MATERIAL_SURFACE`

## Trigger

The Director noticed that `/cms/library` did not visibly expose the previously
integrated directory-rebuild / Clean Material chain.

## Finding

Directory rebuild was not removed from the project:

- detail pages already render `CleanMaterialSummaryCard`;
- task detail pages already render `CleanMaterialSummaryCard`;
- current DB contains 6 materials with `metadata.cleanMaterials['toc-rebuild']`;
- those 6 also have RawMaterial2CleanMaterial accepted metadata.

The product gap was the library surface: `/cms/library` only showed parse/AI
product information and did not show Clean Material / `toc-rebuild` /
Raw2Clean status in the list/card view or filters.

## Fix

Updated `src/app/pages/ProductsPage.tsx`:

- added Clean Material status derivation from material/task metadata;
- added a `目录重建` list column;
- added card badges for `目录重建` / `Raw2Clean`;
- added page header counts for directory-rebuilt and Raw2Clean accepted assets;
- added a directory-rebuild status filter;
- included `toc-rebuild`, `Raw2Clean`, `Clean Material`, and `目录重建` in search
  only for materials that actually have Clean Material evidence;
- fixed empty/expanded row colspans to match the expanded table column count.

## Checks

| Check | Exit |
| --- | ---: |
| `npx tsc --noEmit` | 0 |
| `npm run build` | 0 |
| `git diff --check` | 0 |

## Explicitly Not Done

- No DB write.
- No MinIO write/list/delete/copy/move/cleanup.
- No upload, submit-probe, pressure test, or runtime CleanService POST.
- No readiness, UAT, L3, pressure PASS, production-readiness, or go-live claim.

