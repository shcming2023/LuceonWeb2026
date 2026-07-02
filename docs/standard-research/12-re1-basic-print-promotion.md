# RE1 Basic Print Promotion - 2026-06-29

## Decision

RE1 review outcome V0 is promoted to the first official Basic Print golden sample.

Accepted closure rule:

```text
accepted_by_rule = exact normalized Raw table match + source PDF page/bbox + generated or reused source PDF crop
```

This rule is accepted as sufficient for RE1's 15 simple table visual review packets.

## Scope

The accepted rule applies to simple reading-textbook table packets such as:

- vocabulary word banks;
- reasons-for/reasons-against tables;
- short completion tables;
- simple text-only tables with no formulas, merged visual diagrams, or cross-page layout.

It does not automatically apply to:

- math tables;
- formula-heavy tables;
- chart/diagram hybrids;
- nested or cross-page tables;
- workbook image-question relations;
- any packet without source page/bbox or source crop evidence.

## Promoted Golden

Official golden manifest:

- `corpus/golden/accepted/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.golden.json`

Standard output:

- `runtime/backend/pipeline-work/audits/re1-review-outcome-v0-rerun-20260629/standard-final/`

Result:

```text
quality_level: basic_print
standard_acceptance: pass
quality_score: 97
closure_status: basic_print_accepted
review_outcome_closed_count: 15
review_outcome_open_blocking_count: 0
visual_review_source_crop_count: 15
```

## Boundary

This promotion means RE1 is accepted as a Basic Print baseline, not a polished publication baseline.

Style, color, cover design, brand typography, and original-PDF visual imitation remain outside this accepted level.

## Next Work

1. Treat RE1 as the positive `reading_textbook` golden comparator.
2. Keep GF6 as the negative workbook regression comparator.
3. Add async/UI support for review outcome closure and crop generation.
4. Begin helper-icon compact rendering and workbook layout V1 without forcing GF6 to pass yet.
