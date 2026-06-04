# P0 Source-Bound Cleaning Unit Pack Generator For CleanLaTeX Pilot Report

Task ID: TASK-20260604-145530-P0-Source-Bound-Cleaning-Unit-Pack-Generator-For-CleanLaTeX-Pilot

Branch: `codex/task-329-source-bound-cleaning-unit-pack-generator`

## Summary

Implemented the first source-bound structure-level CleanLaTeX pack generator in the Luceon adapter.

The adapter now compiles additional pilot artifacts:

- `cleanlatex_pack_manifest.json`
- `cleaning_unit_packs.json`
- `cleaning_unit_prompts.json`
- `cleanlatex_validation_manifests.json`

These artifacts are generated from `canonical_toc`, `chapter_spans`, and `official_popo_tree`. They do not replace existing toc-rebuild compatibility artifacts.

## Implementation Notes

- Introduced `luceon-cleanlatex-cleaning-unit-pack/v1`.
- Added `pack_level`, `pack_role`, `boundary_basis=structure-level`, and `semantic_kind_is_boundary_driver=false`.
- Added source block extraction from official tree by stable block IDs.
- Added derived prompt generation from pack JSON.
- Added validation manifests with pending checks for source coverage, asset hash preservation, LaTeX parse, forbidden custom commands, and structure boundary.
- Pilot selection is currently limited to `1.1` and `4.1`.

## Real Math 2022 Evidence Replay

Read-only replay used production evidence:

- `TaskAndReport/evidence/2026-06-04_Task324_TOC_View_Filter_UAT/generated/official_popo_tree.json`
- `TaskAndReport/evidence/2026-06-04_Task325_Production_Canonical_TOC_UAT/mineru_markdown/cambridge_igcse_0580_math_2022_luceon_fresh_uat.md`

Replay summary:

```json
{
  "pack_count": 2,
  "content_block_count": 36,
  "unresolved_source_block_count": 0,
  "asset_hash_count": 0
}
```

Pilot packs:

- `1.1 Different types of numbers`
  - parent: `1 Review of number concepts`
  - pack level: `3`
  - content blocks: `31`
  - source block count: `31`
  - source pages: `[16, 17]`
  - unresolved source blocks: `0`
- `4.1 Colectingand classifyingdata`
  - parent: `4 Collectingorganisingand displayingdata`
  - pack level: `3`
  - content blocks: `5`
  - source block count: `5`
  - source pages: `[122, 123]`
  - unresolved source blocks: `0`

Both packs set `semantic_kind_is_boundary_driver=false`.

## Checks

```bash
PYTHONPATH=. python3 luceon_service/tests/test_popo_invocation_boundary.py
# PASS popo invocation boundary tests

python3 -m py_compile luceon_service/service.py luceon_service/tests/test_popo_invocation_boundary.py
# Exit code 0

node server/tests/cleanservice-output-verifier-smoke.mjs
# PASS cleanservice seven-artifact output verifier smoke tests (9/9)

node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
# All apply-executor smoke cases passed successfully

git diff --check
# Exit code 0
```

## Boundary

This is code-level implementation only. No production rebuild, MinIO write, DB metadata mutation, LLM call, CleanLaTeX output, final PDF, readiness, L3, release, or go-live claim is made.

## Next Recommended Task

```text
P0 Production Repackage V329 Cleaning Unit Pack Artifacts From A800 Math 2022 Output
```

Then, after product/MinIO pack evidence is available:

```text
P0 CleanLaTeX Pilot For One Cleaning Unit
```
