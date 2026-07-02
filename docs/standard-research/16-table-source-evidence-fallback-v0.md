# Table Source Evidence Fallback V0 - 2026-06-30

Decision:

```text
Introduce Raw text-derived table source evidence as review evidence plumbing, not as an automatic accepted_by_rule closure rule.
```

## Why

GF4 exposed a table evidence gap that exact Raw table matching cannot fully solve.

In the GF4 V2 run:

```text
runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v2-rerun-20260630/standard-final
```

three Review 5 table outcomes remained open after exact and compact-exact Raw table closure:

```text
visual:table_visual_review:b-01544
visual:table_visual_review:b-01548
visual:table_visual_review:b-01550
```

The source PDF proves the tables exist, but Raw evidence differs by extraction mode:

- `b-01544`: Raw has a near table match, but Raw OCR differs from Clean/source PDF in at least one cell, so it must not be auto-accepted.
- `b-01548` and `b-01550`: Raw does not expose these source regions as table rows; it exposes them as multiple text boxes.

## Rule Boundary

`accepted_by_rule` remains strict:

```text
Raw table exact normalized match OR length-gated compact exact Raw table match
+ source page/bbox
+ generated/reused source PDF crop
```

Fallback source evidence may backfill:

```text
source_page_number
source_bbox
source_crop
source_match_rule
source_match_score
```

But fallback evidence does not close the outcome. It keeps the item open as:

```text
decision: needs_layout_fix
next_action: manual_table_visual_review
basic_print_blocking: true
```

## Fallback Types

### Raw Table Near Match

Used when Raw has a table entry with high compact similarity but not an exact match.

Current rule:

```text
raw_content_list.table_near_match_for_manual_review
```

This is source-location evidence only.

### Raw Text Cell Coverage Bbox Union

Used when Raw represents a visual table as multiple text boxes rather than a table entry.

Current rule:

```text
raw_content_list.text_cell_coverage_bbox_union_for_manual_review
```

The fallback extracts Clean HTML table cell text, compact-normalizes each cell, then requires at least 90% cell coverage and 90% character coverage on a single Raw page. It unions the matched Raw text-box bboxes to generate the source crop.

This is stricter than fuzzy matching, but still not equivalent to a Raw table structural match.

## GF4 Result

After the fallback:

```text
accepted_by_rule: 130
needs_reconstruction: 3
open_blocking_count: 3
visual_review_source_crop_count: 30
```

Open items now have source crops:

```text
b-01544  page 79  bbox [70, 541, 885, 648]  raw_content_list.table_near_match_for_manual_review
b-01548  page 80  bbox [37, 89, 890, 195]  raw_content_list.text_cell_coverage_bbox_union_for_manual_review
b-01550  page 80  bbox [38, 283, 930, 388]  raw_content_list.text_cell_coverage_bbox_union_for_manual_review
```

Manual visual review then reclassified all three open table outcomes as:

```text
decision: needs_reconstruction
next_action: reconstruct_or_render_table_with_preserved_line_breaks
basic_print_blocking: true
```

GF4 remains `review`, not Basic Print candidate.

## Risk Control

This prevents two opposite errors:

- it avoids blocking forever on missing Raw table entries when source PDF and Raw text boxes can identify the visual region;
- it avoids making the report green when the table still needs visual confirmation.

The fallback rule must not be used to mark `accepted_by_rule`.

## Next Step

The next closure is not more evidence plumbing. It is table reconstruction or line-break-preserving table rendering for grammar paradigm tables whose source crop is already available.

## Follow-up

The next closure was executed in:

```text
docs/standard-research/17-grammar-paradigm-table-rendering-v0.md
runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final
```

Result:

```text
accepted_by_rule: 130
accepted: 2
needs_reconstruction: 1
open_blocking_count: 1
```

The source evidence fallback decision still stands:

- fallback evidence can identify source page/bbox/crop for manual review;
- fallback evidence must not auto-close as `accepted_by_rule`;
- after rendering fixes, remaining blockers may become source-fidelity blockers rather than layout blockers.

GF4 `b-01544` is the first example of that distinction: layout is fixed, but the source crop and Clean/Standard disagree on one short-answer cell.

That remaining blocker was closed later under:

```text
docs/standard-research/18-source-fidelity-correction-policy-v0.md
```

Final GF4 V3 status:

```text
accepted_by_rule: 130
accepted: 3
open_blocking_count: 0
correction_count: 1
closure_status: basic_print_candidate
```
