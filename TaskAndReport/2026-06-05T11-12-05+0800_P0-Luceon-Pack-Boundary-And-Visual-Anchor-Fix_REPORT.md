# P0 Luceon Pack Boundary And Visual Anchor Fix Report

## Scope

This is a Luceon adapter / pack-layer fix only.

No MinerU upstream change, no MinerU-Popo upstream change, no inference rerun, no LLM call, no DB write, no MinIO write, and no production/runtime worker operation was performed.

## Root Cause

The traced failures were introduced after official MinerU-Popo output, inside Luceon layer-3 pack / RawCode generation:

- MinerU-Popo official tree grouped related source blocks and used `<|txt_split|>` / `<|txt_contd|>` as internal content separators.
- Luceon pack generation expanded a grouped Popo row once per `source_block_id`, duplicating the same grouped raw text into many `content_blocks`.
- RawCode generation passed Popo internal separators through to LLM-facing Markdown.
- Glossary text containing ordinary terms such as `graph` / `image` triggered visual evidence review despite having no image/table assets.
- Official Popo tree preserves image/table anchors through image/table node `level` values; Luceon had not surfaced those anchors into pack/RawCode metadata.

## Changes

- Deduplicated cleaning-unit `content_blocks` by source row while preserving the full `source_block_ids` list for traceability.
- Normalized Popo text separators to Markdown paragraphs before pack/RawCode reaches the LLM surface.
- Added RawCode runner preclean fallback for legacy `<|txt_split|>` / `<|txt_contd|>` artifacts.
- Restricted generated visual evidence requirements to packs with actual linked image/table assets.
- Preserved visual anchor metadata as `linked_source_block_ids` in pack blocks, RawCode visual comments, source maps, and image maps.
- Updated validator smoke tests so explicit visual contracts remain strict, while bare glossary-like visual words without a visual contract do not false-positive.

## Real Artifact Replay Evidence

Read-only replay used the existing A800 Math 2022 official Popo artifacts:

- source tree: `TaskAndReport/evidence/2026-06-04_Task324_TOC_View_Filter_UAT/generated/official_popo_tree.json`
- canonical TOC / spans: `TaskAndReport/evidence/2026-06-05_MechanicalSlicing_UAT/pack-output`
- content list: `TaskAndReport/evidence/2026-06-05_FullBook_SectionCleanCode_UAT_v7/input/content_list.json`

Replay output was written only under `/tmp/luceon_pack_fix_uat2`.

Results:

- old full-book pack content blocks: `18146`
- new full-book pack content blocks: `3834`
- pack count: `111`
- unresolved source blocks: `0`
- asset hash count: `1751`

Targeted sample checks:

- `toc-0017 / 3.1 Lines and angles`: `blocks=112`, duplicate groups `0`, split markers `0`, visual comments `71`, linked image-map entries `71`.
- `toc-0145 / Glossary`: `blocks=2`, duplicate groups `0`, split markers `0`, images `0`, visual requirements `0`.
- `toc-0061 / 11.3 Understandingsimilarshapes`: `blocks=105`, duplicate groups `0`, split markers `0`, visual comments `81`, linked image-map entries `81`.
- Example visual anchor: `source_block_ids=7854` now carries `linked_source_block_ids=7852`.

## Verification

Passed:

- `python3 -m py_compile luceon_service/service.py luceon_service/app.py`
- `node server/tests/rawcode2cleancode-runner-smoke.mjs`
- `git diff --check`
- read-only full-book pack replay from existing official Popo artifacts
- RawCode conversion replay for all `111` packs

Not run:

- `pytest` was unavailable in the local Python environment (`No module named pytest`).

## Outcome

Code-level fix is ready for mainline merge and subsequent controlled regeneration of pack/RawCode artifacts. The remaining CleanCode quality issues should now be evaluated on the cleaner input itself rather than on duplicated pack text, leaked Popo separators, or missing visual anchor metadata.
