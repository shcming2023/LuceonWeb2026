# GF6 Basic Print Candidate Review - 2026-06-30

## Decision

GF6 is registered as a `grammar_workbook` Basic Print candidate, not an accepted golden.

This closes the GF6 workbook regression loop enough to preserve it as a positive workbook-profile candidate, while keeping the corpus boundary clear:

- `case`: Grammar Friends 6 workbook pressure sample;
- `run`: `gf6-workbook-regression-v1-20260629`;
- `candidate`: `corpus/golden/candidates/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.candidate.json`;
- `golden`: not promoted.

## Evidence Paths

Standard output:

```text
runtime/backend/pipeline-work/audits/gf6-workbook-profile-regression-v1-rerun-20260629/standard-final/
```

Corpus records:

```text
docs/standard-research/corpus/runs/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.run.json
docs/standard-research/corpus/golden/candidates/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.candidate.json
```

Primary review artifacts:

```text
standard_acceptance_report.json
standard_quality_score.json
standard_review_outcomes.json
visual_outcome_review.json
image_outcome_rule_audit.json
issue_candidate_disposition_audit.json
basic_print_closure_report.json
page_spot_check/page_spot_check_report.json
page_spot_check/page_spot_check.html
```

## Current Status

```text
standard_acceptance_report.status: pass
standard_quality_score.score: 100
standard_quality_score.status: pass
basic_print_closure_report.status: basic_print_candidate
fail_gates: []
review_gates: []
```

This is stronger than the earlier GF6 negative regression state, but it is still candidate evidence rather than corpus acceptance.

## Issue Candidate Disposition

GF6 still has 213 raw `missing_raw_image_semantics` issue candidates. They are no longer treated as a single unresolved count. Each item now has a disposition in `issue_candidate_disposition_audit.json`.

```text
issue_candidate_count: 213
unresolved_blocking_count: 0
real_context_gap_count: 0

covered_by_visual_outcome: 170
helper_icon_compact_rendering: 43
```

Interpretation:

- 170 key figures are covered by closed image visual outcomes;
- 43 helper icons are handled by compact nearby rendering;
- no issue candidate remains a blocking context gap in this run.

Gate rule:

```text
context_integrity / review_threshold basis =
  unresolved_blocking_issue_count
  not raw issue_candidate_count
```

This is not a count suppression rule. It requires every issue candidate to be classified.

## Review Outcome Closure

```text
standard_review_outcomes.count: 197
accepted_by_rule: 197
open_blocking_count: 0
closed_count: 197

image_source_visual_confirmation: 170
table_visual_review: 26
formula_visual_review: 1
```

Image closure rule:

```text
accepted_by_rule =
  Standard image exists and is readable
  + source crop from Raw image_ref page/bbox evidence
  + Standard/source aspect ratios agree within threshold
  + Standard image dimensions are sufficient for Basic Print
  + question or explanation context exists
```

Table/formula closure rule:

```text
accepted_by_rule =
  Standard table/formula text exactly matches Raw content_list after normalized comparison
  + source page/bbox exists
  + source PDF crop was generated or reused
```

Important boundary:

```text
accepted_by_rule != human visual final approval
```

## Page-Level Spot Check

Spot check status:

```text
page_spot_check.status: pass_with_notes
blocking_findings: 0
sample_count: 5
```

Samples checked:

```text
explanation_key_figure_starter: pass
exercise_key_figure_conversations: pass
table_question_sentences: pass_with_note
formula_review_tree_house: pass
explanation_table_wish: pass
```

Risk coverage:

- explanation key figure plus helper icons;
- exercise key figure inside a question group;
- table question across a page break;
- formula/superscript answer blank;
- explanation figure plus explanation table context.

Notes:

- Exercise 4 instruction appears at the bottom of Standard page 6 and its table begins at the top of Standard page 7. The table header is retained and the reading order is continuous, so this is non-blocking for Basic Print but should be monitored in workbook pagination rules.
- The source PDF contains blue handwritten/filled answer marks. Whether to preserve those marks is a Clean/source-fidelity policy question, not a Standard image-relation hard fail.

## What This Proves

Verified for this GF6 run:

- workbook relation profile can classify GF6 exercise/table/image structures without remaining real profile gaps;
- key workbook figures can be closed by source crop plus context evidence;
- helper icons can be separated from key figures and handled as compact nearby rendering;
- `context_integrity` and `review_threshold` can be driven by dispositioned unresolved blockers rather than raw issue count;
- page-level spot check did not find a blocking image/table/formula/context failure in the sampled high-risk pages.

## What This Does Not Prove

Not proven:

- GF6 is an accepted Basic Print golden;
- the GF6 workbook rules generalize to other workbook series;
- every page in GF6 has received human visual final approval;
- `accepted_by_rule` can replace human review for all future samples;
- handwritten source annotations should be preserved or removed in all cases.

## Candidate Policy

GF6 should remain in `corpus/golden/candidates/` until a separate promotion decision is made.

Do not move it to `corpus/golden/accepted/` unless all of the following are explicitly accepted:

- candidate-only scope notes are reviewed;
- page spot-check notes are accepted as non-blocking;
- source annotation policy is separated from Standard Basic Print;
- at least one additional workbook sample is considered, or the team explicitly accepts GF6 as a single-sample workbook golden.

## Next Decision

Recommended next step:

```text
Choose whether to find a second workbook sample for the same issue-disposition and page-spot-check loop.
```

Do not use GF6 alone to declare the workbook profile generally solved.
