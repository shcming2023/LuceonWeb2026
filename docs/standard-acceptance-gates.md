# Standard Acceptance Gates

This document defines how to review a `standard-final/` output package.

The `standard` node turns a Clean material package into a source-faithful, evidence-corrected, printable, and auditable basic textbook master. Review must be based on files, reports, rendered output, and lineage evidence. Do not judge by visual impression alone.

## Review Inputs

A complete review should inspect:

- `manifest.json`
- `standard_document.json`
- `standard.md`
- `standard.html`
- `standard.pdf`
- `images/`
- `standard_acceptance_report.json`
- `standard_issue_candidates.json`
- `correction_log.json`
- `layout_report.json`
- `workbook_profile_report.json`, `workbook_profile.html`, `workbook_relation_audit.json`, and `workbook_relation_audit.html` for workbook profiles
- `image_relation_report.json`, `image_visual_confirmation_packets.json`, `image_outcome_rule_audit.json`, `image_outcome_rule_audit.html`, `standard_review_outcomes.json`, `review_outcomes.html`, `visual_outcome_review.json`, and `visual_outcome_review.html` when present
- `basic_print_closure_report.json`, `basic_print_closure.html`, `clean_review_scope_report.json`, and source crop directories such as `source_crops/` or `visual_source_crops/` when closure scripts have run
- `print_qa_report.json`
- `review.html`
- upstream Clean reports when available: `acceptance_report.json`, `media_report.json`, `structure_report.json`, `loss_audit.json`, `render_report.json`
- upstream Raw evidence when available: `manifest.json`, `image_semantics.json`, source maps, block assignments, page/bbox evidence

## Core Definition

`standard` is successful only if it produces a reusable textbook master that is:

- faithful to the original source, not a rewrite of Clean;
- structurally aligned to the Clean/Raw outline;
- complete enough for reading, printing, and downstream editing;
- conservative about corrections and media removal;
- auditable through machine-readable reports and review HTML.

Allowed changes are limited to evidence-backed repair and minimal layout/read-order reconstruction. Unverified invention, rewriting, summarizing, or expansion is a failure.

## Status Levels

Use three statuses:

```text
pass
review
fail
```

`pass` means all hard gates pass and review findings are below threshold.

`review` means hard gates pass, but there are recorded issues that need another iteration or human/model review.

`fail` means at least one hard gate fails, or the package cannot be trusted as a source-faithful printable master.

## Hard Gates

Any failed hard gate makes the package `fail`.

| Gate | Pass Standard | Evidence |
| --- | --- | --- |
| output_completeness | All required files exist | filesystem, `manifest.json` |
| pdf_render | `standard.pdf` exists, is non-empty, and page count is readable | `print_qa_report.json` |
| media_integrity | Referenced images exist; `missing_images = 0` | `print_qa_report.json`, `images/` |
| outline_lock | Standard outline does not drift from Clean/Raw outline | `standard_acceptance_report.json`, `standard_document.json` |
| source_fidelity | No unlogged text additions, deletions, or rewrites | text hash/diff, `correction_log.json` |
| correction_evidence | Every applied correction has evidence | `correction_log.json` |
| no_invention | No unsupported content invention, rewriting, summary, or expansion | correction audit, source comparison |
| dropped_media_evidence | Dropped media has documented evidence or upstream decision | `media_report.json`, `standard_acceptance_report.json` |
| structured_auditability | Blocks, outline, relations, and evidence exist in structured form | `standard_document.json` |

## Review Gates

Review gates do not automatically fail the package. They identify the next iteration targets.

| Gate | Review Trigger | Meaning |
| --- | --- | --- |
| context_integrity | Many isolated short blocks, split questions, split options, or loose captions | grouping rules need improvement |
| block_classification | High `unknown` or `needs_review` block ratio | profile/rules need improvement |
| table_integrity | Tables are preserved but not reconstructed or visually checked | table review needed |
| formula_integrity | Formulas/math are preserved but not verified against source evidence | formula review needed |
| figure_caption_relation | Image, caption, and surrounding text are not confidently linked | relation logic needs improvement |
| workbook_profile_relation | Workbook question groups, fill blanks, options, tables, or figures are not parented to an exercise/explanation context | workbook profile rules need improvement |
| image_visual_confirmation | Workbook key figures have source crops but unresolved review outcomes | source visual confirmation needed |
| layout_sanity | Large blank pages, severe page breaks, oversized media, or unreadable text | template/layout rules need improvement |
| print_usability | HTML/PDF renders but has visible rough edges | printable but not polished |

Simple source-faithful text tables can close table review as `accepted_by_rule` only when Standard table content exactly matches Raw `content_list` after normalized comparison, source page/bbox exists, and a source PDF crop is generated or reused. This is not valid for formula-heavy, math, chart-hybrid, nested, cross-page tables, or image outcomes. Missing source page/bbox remains `needs_page_bbox`; text mismatch with crop evidence remains `needs_layout_fix`.

Workbook key-figure image outcomes can close as `accepted_by_rule` only when the Standard image file exists, the source crop was generated or reused from the same Raw image reference and page/bbox evidence, Standard/source aspect ratios agree within the rule threshold, image dimensions are sufficient for Basic Print, and question or explanation context exists. Images that fail these checks stay open as `needs_reconstruction`, `needs_source_crop`, or `needs_page_bbox`; decorative/helper images should be excluded or marked `non_blocking`, not silently treated as key figures.

Simple formula/text visual review outcomes can close as `accepted_by_rule` only when the Standard text exactly matches Raw `content_list` after normalized comparison, source page/bbox exists, and a source PDF crop is generated or reused. A conservative formula semantic-key match may also close only when operators, exponents, digits, formula commands, source page/bbox, and generated/reused crop evidence are preserved; Markdown emphasis markers such as `**bold**` and `__bold__` do not change the semantic key. Deterministic formula semantic-equivalent closure is allowed only when the semantic key is exactly equal and the source-location rule is one of: Raw content-list formula semantic-key match, math-normalized same-unit unique match, math-normalized same-unit ordinal duplicate match, compact-exact same-unit Raw context, high-confidence Raw context, or short option-formula compact-exact Raw context. Short-procedure context evidence is source-location evidence only and does not close formula review by itself. Near-equivalent or mismatched formula keys remain manual review. Formula-heavy or visually ambiguous math still requires manual visual review or reconstruction.

Raw context-window or page-level compact containment may backfill source page/bbox and generate a source crop only as manual-review evidence. It must not close formula/table outcomes as `accepted_by_rule` when the source crop covers a larger Raw context, when the Standard block is only a substring of the Raw row/window, or when the source-location rule ends in `_for_manual_review`.

Markdown or HTML image-only blocks must not create `formula_visual_review` outcomes merely because their alt text contains math notation. They should stay in image relation or image visual confirmation review, while mixed text+image blocks with formula-bearing surrounding text may still require formula/table review.

## Quality Score

In addition to `pass/review/fail`, assign a 100-point quality score when performing a full review.

### 1. Source Fidelity - 25 Points

| Item | Points |
| --- | ---: |
| No unlogged text change | 8 |
| All corrections have evidence | 6 |
| OCR/formula/table doubts are recorded | 4 |
| No invention, rewriting, summary, or expansion | 5 |
| Special characters, blanks, and punctuation are not visibly damaged | 2 |

### 2. Structure Recovery - 20 Points

| Item | Points |
| --- | ---: |
| Outline aligns to Clean/Raw | 6 |
| Unit, lesson, passage, exercise, and review areas are classified correctly | 5 |
| Block order follows reading order | 4 |
| Heading hierarchy is stable | 3 |
| Blocks are traceable to clean lines or raw evidence | 2 |

### 3. Context Integrity - 20 Points

| Item | Points |
| --- | ---: |
| Figures, captions, and explanatory text stay together | 4 |
| Question stems, options, tables, and images stay together | 5 |
| Passage, footnote, and line-number relations are understandable | 3 |
| Vocabulary boxes, notes, and sidebars are grouped | 3 |
| Issue candidates are below threshold | 3 |
| Isolated short blocks are controlled | 2 |

### 4. Media And Visual Integrity - 15 Points

| Item | Points |
| --- | ---: |
| All referenced media exists | 4 |
| Decorative media removal is evidence-backed | 3 |
| Educational media is not wrongly removed | 3 |
| Figure placement is reasonable | 2 |
| Tables, diagrams, and formulas are not visibly broken | 3 |

### 5. Print Layout - 15 Points

| Item | Points |
| --- | ---: |
| PDF renders successfully and page count is readable | 3 |
| No obvious blank pages or severe page breaks | 3 |
| Reading passages use appropriate layout, such as two columns when useful | 2 |
| Figures, tables, and question groups use keep-together rules where possible | 3 |
| Font size, line height, and margins are printable | 2 |
| HTML is simple and stable, with no app framework dependency | 2 |

### 6. Auditability And Iteration - 5 Points

| Item | Points |
| --- | ---: |
| Manifest records lineage | 2 |
| `review.html` supports direct review | 1 |
| Issue candidates can drive the next iteration | 1 |
| Reports are machine-readable | 1 |

## Score To Status

```text
pass:
  score >= 90
  and all hard gates pass
  and review findings are below threshold

review:
  score 75-89
  and all hard gates pass
  and remaining issues are recorded

fail:
  any hard gate fails
  or score < 75
  or there is unsupported correction, missing media, outline drift, or PDF failure
```

## Review Output Format

Each Standard review should report:

1. Overall status: `pass`, `review`, or `fail`.
2. Quality score if a full review was performed.
3. Hard gate results, with evidence file paths.
4. Review gate findings, ordered by severity.
5. Source-fidelity risks, especially unlogged corrections or suspected OCR damage.
6. Context-integrity risks, especially split question groups, loose captions, and isolated short blocks.
7. Media/table/formula risks.
8. Print-layout risks.
9. Next iteration priorities.
10. Responsibility hints: whether each issue belongs mainly to Raw structure, Clean cleaning, or Standard grouping/rendering.

## RE1 Historical MVP Baseline

The first RE1 Standard MVP was expected to be `review`, not `pass`. RE1 review outcome V0 was later promoted as the first official Basic Print golden after table review outcomes were closed by the accepted rule.

Known baseline shape:

```text
outline_count: 69
image_refs: 162
missing_images: 0
unknown_blocks: 0
status: review
```

The expected review causes are:

- isolated short blocks that need grouping or visual review;
- tables and formulas preserved conservatively but not fully source-verified;
- simple print layout that is usable but not final-polished;
- TOC and page-break rules that may need template refinement.

This baseline proves the node shape is working. It does not prove the package is a final high-quality textbook master.
