# GF6 Workbook Regression Loop V1 - 2026-06-29

## Decision

GF6 is now the active `grammar_workbook` negative regression baseline.

The goal of this baseline is not to force GF6 to pass. The goal is to make GF6 fail/review for explicit workbook reasons:

- exercise grouping and relation quality;
- fill-blank recognition;
- option/table attachment;
- workbook image relation and source visual confirmation;
- helper icon handling as a separate compact rendering problem.

## Implementation

Implemented in `backend/scripts/standard_from_clean.py`:

- `workbook_profile_report.json`
- `workbook_profile.html`
- `workbook_relation_audit.json`
- `workbook_relation_audit.html`
- richer workbook relation metrics in `layout_report.json`
- review outcome source-crop sync after optional crop generation
- compact rendering classes for `helper_icon` figures

Service deliverable checks were updated in `backend/app/services/clean_to_standard.py`.

Optional source crop generation now refreshes:

- `image_visual_confirmation_packets.json`
- `image_visual_confirmation.html`
- `standard_review_outcomes.json`
- `review_outcomes.html`
- `workbook_relation_audit.json`
- `workbook_relation_audit.html`
- `workbook_profile_report.json`
- `workbook_profile.html`

## GF6 V1 Run

Output:

- `runtime/backend/pipeline-work/audits/gf6-workbook-profile-regression-v1-rerun-20260629/standard-final/`

Main Standard command:

```bash
python3 backend/scripts/standard_from_clean.py \
  --clean-dir runtime/backend/pipeline-work/clean2standard/run-44-pdf-ff4c7f59964ad54f-popo-20260617014256-staged_popo_20260617_batch07_sma-1369cfec--002-popo_ff4c7f59964ad54f_002/clean_input \
  --raw-dir runtime/backend/pipeline-work/clean2standard/run-44-pdf-ff4c7f59964ad54f-popo-20260617014256-staged_popo_20260617_batch07_sma-1369cfec--002-popo_ff4c7f59964ad54f_002/raw_input \
  --source-pdf runtime/backend/pipeline-work/popo2raw/run-37-pdf-ff4c7f59964ad54f-popo-20260617014256-staged_popo_20260617_batch07_sma-1369cfec--002-popo_ff4c7f59964ad54f_002/rebuild_input/pdf-ff4c7f59964ad54f_origin.pdf \
  --profile grammar_workbook \
  --out-dir runtime/backend/pipeline-work/audits/gf6-workbook-profile-regression-v1-rerun-20260629/standard-final
```

Optional review artifact command:

```bash
python3 backend/scripts/generate_standard_source_crops.py \
  --standard-dir runtime/backend/pipeline-work/audits/gf6-workbook-profile-regression-v1-rerun-20260629/standard-final
```

## Result

```text
status: review
regression_verdict: expected_negative_regression_review
profile: grammar_workbook
source_crop_count: 170
review_outcome_open_blocking_count: 197
```

Basic Print blockers:

```text
image_relation_contract_not_pass
table_visual_review_outcomes_open
```

## Workbook Metrics

```text
question_groups: 147
questions: 710
grouped_questions: 709
ungrouped_questions: 1
fill_blank_questions: 372
answer_blanks: 157
parented_answer_blanks: 157
orphan_answer_blanks: 0
table_questions: 19
parented_table_questions: 19
orphan_table_questions: 0
figure_relation_candidates: 213
parented_figure_relation_candidates: 179
orphan_figure_relation_candidates: 34
```

Options currently remain `0` for GF6 because the source Clean text does not expose many choices as standalone `a.` / `b.` option blocks. The option detector is still part of the profile contract and is covered by synthetic regression tests.

## Relation Audit Result

The 10 ungrouped questions, 7 orphan table questions, and 34 orphan figure candidates were audited and separated into artifacts versus real profile gaps.

```text
workbook_relation_audit.count: 42
real_profile_gap_count: 0
review_item_count: 0

front_matter_artifact: 1
explanation_artifact: 21
helper_icon_artifact: 20
```

Interpretation:

- the remaining ungrouped question is a publication number line, not a workbook exercise;
- the 7 formerly orphan table questions are grammar explanation tables, not exercise tables;
- the 34 orphan figures are explanation/unit figures or helper icons, not unhandled exercise figures;
- `exercise_relation_contract` is now `pass`.

## Image Metrics

```text
image_relation_count: 213
helper_icon: 43
exercise_key_figure: 162
explanation_key_figure: 8
image_visual_confirmation_packet_count: 170
source_crop_count: 170
open_image_review_outcome_count: 170
```

This confirms the queue is not "review 213 images". It is:

- 170 key figures requiring source visual confirmation;
- 43 helper icons for compact nearby rendering;
- 34 unparented figure candidates classified as explanation/helper artifacts, not active exercise profile gaps.

Helper icons now render with compact nearby CSS:

```text
figure.image-relation-helper_icon
max-width: 13mm
max-height: 14mm
```

## Visual Outcome Closure V2

The broad visual review work is now outcome-based and closed by explicit evidence.

```text
standard_review_outcomes.count: 197
accepted_by_rule: 197
open_blocking_count: 0
closed_count: 197
```

`visual_outcome_review.json/html` now provides a side-by-side review surface:

```text
image_source_visual_confirmation: 170
table_visual_review: 26
formula_visual_review: 1

side_by_side_ready:
  image_source_visual_confirmation: 170
  table_visual_review: 26
  formula_visual_review: 1
```

The image closure script generated `image_outcome_rule_audit.json/html` and closed all 170 image outcomes as `accepted_by_rule`.

```text
image_outcome_rule_audit.count: 170
accepted_by_rule: 170
confidence.high: 164
confidence.medium: 6
```

Image closure rule:

```text
accepted_by_rule =
  Standard image exists and is readable
  + source crop was generated/reused from Raw image_ref page/bbox evidence
  + Standard/source aspect ratios agree within the rule threshold
  + Standard image dimensions are sufficient for Basic Print
  + question or explanation context exists
```

The table/formula closure script generated `visual_source_crops/` and closed all 27 table/formula outcomes as `accepted_by_rule`.

```text
table_visual_review: 26 accepted_by_rule
formula_visual_review: 1 accepted_by_rule
visual_source_crops: 27
source_evidence_backfilled: 2
```

Table/formula closure rule:

```text
accepted_by_rule =
  Standard table/formula text exactly matches Raw content_list after normalized comparison
  + source page/bbox exists
  + source PDF crop was generated or reused
```

The two previously open bbox items were resolved from Raw content_list:

```text
b-01703 table_visual_review page 87 bbox [79, 518, 886, 595]
b-00551 formula_visual_review page 30 bbox [127, 573, 487, 595]
```

This pass fixed two Standard compiler defects:

- table review packets must keep full table text, not a 1000-character preview;
- normalized table/text matching must treat curly and straight apostrophes as equivalent for Raw/Standard visual evidence closure.

Current GF6 status:

```text
workbook_profile_report.status: pass
standard_acceptance_report.status: review
remaining review gates: context_integrity, review_threshold
visual review outcomes: pass
```

## Next Work

1. Decide whether `context_integrity` and `review_threshold` should remain package-level review gates for GF6, or be split into workbook-profile-specific issue classes.
2. Audit the 213 issue candidates now that visual outcomes are closed; many may be expected image/layout review candidates rather than true Basic Print blockers.
3. Treat GF6 as a workbook-profile visual-closure positive sample, while still keeping it as a layout/context negative regression until issue-candidate handling is refined.

## 2026-06-30 Candidate Update

GF6 has moved from workbook negative regression comparator to Basic Print candidate.

Current corpus records:

```text
docs/standard-research/corpus/runs/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.run.json
docs/standard-research/corpus/golden/candidates/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.candidate.json
docs/standard-research/14-gf6-basic-print-candidate-review.md
```

Current status:

```text
standard_acceptance_report.status: pass
standard_quality_score.score: 100
standard_quality_score.status: pass
basic_print_closure_report.status: basic_print_candidate
fail_gates: []
review_gates: []
```

Issue candidate disposition:

```text
missing_raw_image_semantics: 213
covered_by_visual_outcome: 170
helper_icon_compact_rendering: 43
unresolved_blocking_count: 0
real_context_gap_count: 0
```

Gate interpretation:

```text
context_integrity / review_threshold basis =
  unresolved_blocking_issue_count
  not raw issue_candidate_count
```

Page-level spot check:

```text
status: pass_with_notes
sample_count: 5
blocking_findings: 0
```

Candidate boundary:

- GF6 is not promoted to accepted golden.
- `accepted_by_rule` remains deterministic evidence closure, not human visual final approval.
- The table-instruction page break is non-blocking but should be monitored in workbook pagination rules.
- Blue handwritten/filled marks in the source PDF remain a Clean/source-fidelity policy decision.
- Do not use GF6 alone to declare the workbook profile generally solved.
