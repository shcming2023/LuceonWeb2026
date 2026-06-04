# P0 Expanded Span DeepSeek 4.1 UAT Report

## Status

UAT_COMPLETED_SPAN_EXPANSION_PASS_REMAINING_VISUAL_PROMPT_REVIEW

## Objective

Validate the corrected root cause: `4.1` cleaning unit pack must include the full section body and child Exercise 4.1 body blocks, not just the section opening and exercise title.

## Inputs

Existing evidence only:

- A800 official Popo output: `TaskAndReport/evidence/2026-06-04_Task324_TOC_View_Filter_UAT/popo_outputs/cambridge_igcse_0580_math_2022_luceon_fresh_uat.json`
- A800 MinerU result zip: `TaskAndReport/evidence/2026-06-04_A800_Math_2022_UAT/extracted/mineru-result.zip`
- Prior pack boundary evidence: `TaskAndReport/evidence/2026-06-04_RawCode2CleanCode_Review_Fixes_UAT/minio-readback/cleaning_unit_packs.json`

No MinerU/MinerU-Popo inference was rerun.

## Execution

1. Generated an expanded `4.1` pack by applying official Popo body-order expansion from the `4.1` start to the next `4.2` boundary.
2. Converted expanded pack to RawCode with physical assets copied from local A800 MinerU images.
3. Ran one controlled true LLM pilot with `deepseek-v4-flash` on `toc-0024`.

## Evidence

Expanded pack:

- `4.1` expanded source block count: `158`
- Includes all Exercise 4.1 body nodes `2929-2963`: yes
- Excludes `4.2` boundary node `2964`: yes
- `4.1` content block count: `159`
- unresolved source blocks: `0`

RawCode asset bridge:

- copied image count: `4`
- missing image count: `0`

LLM output:

- Runner status: `NEEDS_REVIEW`
- The prior `missing_content` issue for `Exercise4.1` is resolved: the output now includes Exercise 4.1 questions and subitems.
- Remaining unresolved items are visual-prompt related:
  - flow diagram image was reported unresolved even though asset exists;
  - table image was reported unresolved even though asset exists;
  - one unclear OCR symbol `nP` requires manual review.

## Output Paths

- Expanded pack summary: `TaskAndReport/evidence/2026-06-04_CleaningUnit_SpanExpansion_DeepSeek_41_UAT/adapter-output/expanded_span_repack_summary.json`
- RawCode output: `TaskAndReport/evidence/2026-06-04_CleaningUnit_SpanExpansion_DeepSeek_41_UAT/rawcode-output-with-assets/`
- DeepSeek output: `TaskAndReport/evidence/2026-06-04_CleaningUnit_SpanExpansion_DeepSeek_41_UAT/deepseek-v4-flash-41-expanded/`
- Clean markdown: `TaskAndReport/evidence/2026-06-04_CleaningUnit_SpanExpansion_DeepSeek_41_UAT/deepseek-v4-flash-41-expanded/cleancode/4134323036518274/v337-expanded-span-assets/chapters/toc-0024/clean.md`
- Quality report: `TaskAndReport/evidence/2026-06-04_CleaningUnit_SpanExpansion_DeepSeek_41_UAT/deepseek-v4-flash-41-expanded/cleancode/4134323036518274/v337-expanded-span-assets/chapters/toc-0024/quality_report.json`

## Conclusion

The corrected root cause is confirmed. The blocker was not primarily image/table-to-text conversion: `4.1` lost substantial existing text because the cleaning unit span did not expand through official Popo body order. After span expansion, Exercise 4.1 body text is available to the LLM and appears in CleanCode.

Remaining `NEEDS_REVIEW` is now a separate prompt/validator behavior: when linked visual assets are physically present, the cleaner should prefer preserving markdown image references over reporting them as missing. That should be handled as a narrow follow-up prompt-contract fix, not as another span or Popo problem.

## Boundaries

- No DB write.
- No MinIO write.
- No runtime worker post.
- No GPU operation.
- No MinerU/MinerU-Popo rerun.
- No credential committed.
- No final CleanCode publishability/readiness/L3/go-live claim.
