# P0 Fixed Visual Asset Pack DeepSeek 4.1 Pilot UAT Report

## Status

UAT_COMPLETED_VISUAL_ASSET_CHAIN_PASS_CLEANCONTENT_NEEDS_REVIEW

## Objective

Regenerate pack/RawCode artifacts from the fixed adapter visual asset contract, then run one controlled true LLM pilot on `4.1 Colectingand classifyingdata` using only `deepseek-v4-flash`.

## Inputs

Existing local evidence only; no MinerU/MinerU-Popo inference rerun:

- A800 MinerU result zip: `TaskAndReport/evidence/2026-06-04_A800_Math_2022_UAT/extracted/mineru-result.zip`
- A800 official Popo output: `TaskAndReport/evidence/2026-06-04_Task324_TOC_View_Filter_UAT/popo_outputs/cambridge_igcse_0580_math_2022_luceon_fresh_uat.json`
- Prior accepted pack boundary: `TaskAndReport/evidence/2026-06-04_RawCode2CleanCode_Review_Fixes_UAT/minio-readback/cleaning_unit_packs.json`

## Execution Summary

1. Rebuilt fixed visual-asset packs using existing v329 pack boundaries plus official Popo/MinerU asset evidence.
2. Extracted A800 MinerU images to a local asset root.
3. Regenerated RawCode with `--asset-root`, copying hash-named images into the RawCode bundle.
4. Ran `scripts/rawcode2cleancode-pilot.mjs` on `toc-0024` with `--cleaner llm --model deepseek-v4-flash`.

No DB writes, MinIO writes, runtime worker posts, GPU operations, or production metadata updates were performed.

## Key Evidence

Fixed pack/RawCode asset evidence:

- `4.1` pack source ids: `2885, 2886, 2887, 2888, 2928`
- Asset index from MinerU: `images=1438`, `tables=373`
- `4.1` linked image hashes:
  - `71ef028a11659ad184c2c55a77eec9c6447b1168a81d59e273fb945c43d6929f.jpg`
  - `bbf34311e6f90877988bf75e1c9d798d6ae2437cbbe10fde4b218b6f5bffafe5.jpg`
- RawCode asset copy: `copied_count=4`, `missing_count=0`
- `toc-0024` CleanCode image files exist under the output chapter `images/` directory.

LLM output behavior:

- The model preserved both linked image references.
- The model did not invent replacement visual content.
- The model corrected OCR spacing and removed duplicated paragraphs / `<|txt_split|>` markers.
- The model produced an unresolved review item for missing textual exercise content.

Final status:

- Runner status: `NEEDS_REVIEW`
- Visual asset chain: PASS
- Physical image packaging: PASS
- Remaining review reason: `Exercise4.1` has a header/table image but no extracted readable exercise text; human review or a later image/table-to-text pass is required before automatic approval.

## Output Paths

- Fixed pack summary: `TaskAndReport/evidence/2026-06-04_CleanLaTeX_VisualAsset_FixedPack_DeepSeek_41_UAT/adapter-output/fixed_visual_asset_repack_summary.json`
- RawCode with copied assets: `TaskAndReport/evidence/2026-06-04_CleanLaTeX_VisualAsset_FixedPack_DeepSeek_41_UAT/rawcode-output-with-assets/`
- DeepSeek `4.1` output: `TaskAndReport/evidence/2026-06-04_CleanLaTeX_VisualAsset_FixedPack_DeepSeek_41_UAT/deepseek-v4-flash-41-with-assets/`
- Clean markdown: `TaskAndReport/evidence/2026-06-04_CleanLaTeX_VisualAsset_FixedPack_DeepSeek_41_UAT/deepseek-v4-flash-41-with-assets/cleancode/4134323036518274/v333-visual-asset-fixed-assets/chapters/toc-0024/clean.md`
- Quality report: `TaskAndReport/evidence/2026-06-04_CleanLaTeX_VisualAsset_FixedPack_DeepSeek_41_UAT/deepseek-v4-flash-41-with-assets/cleancode/4134323036518274/v333-visual-asset-fixed-assets/chapters/toc-0024/quality_report.json`

## Conclusion

The main visual asset fidelity blocker is closed for this pilot: official MinerU/MinerU-Popo visual assets now reach pack, RawCode, LLM request, CleanCode markdown, and output image files with original hash names preserved.

The pilot is not automatically publishable yet because the cleaner correctly surfaced a content completeness issue in `Exercise 4.1`. That is a downstream CleanCode review/content-completeness problem, not a visual asset reference/pack fidelity failure.
