# P0 Pack Boundary Fix DeepSeek 8Unit UAT Report

## Scope

This UAT validates the merged `main@a79e11b4` Luceon pack/RawCode boundary fix.

The run reused existing A800 Math 2022 official Popo artifacts. It did not rerun MinerU, did not rerun MinerU-Popo, did not write DB, did not write MinIO, and did not call runtime workers.

## Regenerated Artifacts

Evidence root:

`TaskAndReport/evidence/2026-06-05_PackBoundaryFix_CleanCode_Batch_UAT`

Generated artifacts:

- `pack-output/cleaning_unit_packs.json`
- `pack-output/canonical_toc.json`
- `pack-output/chapter_spans.json`
- `rawcode-output/rawcode/4134323036518274/v339-pack-boundary-fix`
- `CONTROLLED_8UNIT_DEEPSEEK_AGGREGATE.json`
- `CONTROLLED_8UNIT_DEEPSEEK_UAT_REVIEW.md`

Pack replay summary:

- pack count: `111`
- content block count: `3834`
- unresolved source block count: `0`
- asset hash count: `1751`
- RawCode asset copy: `copiedCount=1751`, `missingCount=0`

## DeepSeek Batch

Cleaner:

- provider: DeepSeek OpenAI-compatible API
- model: `deepseek-v4-flash`
- samples: `8`

Results:

- `PASS`: `4`
- `NEEDS_REVIEW`: `4`
- validator risk counts: `{}`
- split markers: `0` in all raw/clean outputs
- image hash files: all copied, no missing images
- production side effects: `0 DB writes`, `0 MinIO writes`, `0 runtime worker posts`

Sample outcomes:

| Chapter | Title | Status | Notes |
| --- | --- | --- | --- |
| `toc-0003` | `1.1 Different types of numbers` | PASS | 3/3 image refs preserved |
| `toc-0024` | `4.1 Colectingand classifyingdata` | PASS | 2/2 image refs preserved |
| `toc-0017` | `3.1 Lines and angles` | PASS | 71/71 image refs preserved; previous split-marker issue resolved |
| `toc-0042` | `7.3 Surface areas and volumes of solids` | NEEDS_REVIEW | image placement uncertainty only; 38/38 image refs preserved |
| `toc-0061` | `11.3 Understandingsimilarshapes` | NEEDS_REVIEW | OCR ambiguity / formula formatting; 81/81 image refs preserved |
| `toc-0145` | `Glossary` | PASS | no visual false-positive; 0 visual requirements |
| `toc-0064` | `12.1 Differenttypesof averages` | NEEDS_REVIEW | severe OCR garbling in source text |
| `toc-0117` | `19.4 Anglerelationshipsincircles` | NEEDS_REVIEW | likely corrupted formulas / OCR math |

## Interpretation

The Luceon pack-layer defects found in the traceback are resolved for this batch:

- no duplicated grouped Popo rows surfaced as repeated RawCode blocks;
- no `<|txt_split|>` / `<|txt_contd|>` leaked into RawCode or CleanCode;
- Glossary visual keyword false-positive is gone;
- image/table assets are physically present and preserved;
- visual anchors are carried through `linked_source_block_ids`.

Remaining `NEEDS_REVIEW` cases are content-quality issues, primarily OCR corruption, formula ambiguity, and occasional image placement uncertainty. These should be treated as the next CleanCode quality frontier, not as MinerU-Popo structure failure or pack boundary failure.

## Secret Check

Searched the UAT evidence root for the provided API key and common authorization strings. No API key or authorization header was found in the generated evidence.
