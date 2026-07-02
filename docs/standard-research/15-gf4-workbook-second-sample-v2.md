# GF4 Workbook Second Sample V2 - 2026-06-30

GF4 is the second `grammar_workbook` sample used after GF6.

The purpose of this run is not to promote another golden. It tests whether the workbook profile rules learned from GF6 survive a nearby but separate workbook sample.

## Inputs

Clean package:

```text
runtime/backend/pipeline-work/raw2clean/run-35-pdf-8ada74dfc6d2d66c-popo-20260616234840-staged_popo_20260617_batch06_sma-d552836a--003-popo_8ada74dfc6d2d66c_003/clean-final
```

Raw package:

```text
runtime/backend/pipeline-work/raw2clean/run-35-pdf-8ada74dfc6d2d66c-popo-20260616234840-staged_popo_20260617_batch06_sma-d552836a--003-popo_8ada74dfc6d2d66c_003/raw_input
```

Source PDF:

```text
runtime/backend/pipeline-work/popo2raw/run-34-pdf-8ada74dfc6d2d66c-popo-20260616234840-staged_popo_20260617_batch06_sma-d552836a--003-popo_8ada74dfc6d2d66c_003/rebuild_input/pdf-8ada74dfc6d2d66c_origin.pdf
```

Final V2 Standard package:

```text
runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v2-rerun-20260630/standard-final
```

Corpus records:

```text
docs/standard-research/corpus/cases/pdf-8ada74dfc6d2d66c.case.json
docs/standard-research/corpus/runs/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v2-20260630.run.json
```

## Commands

```bash
python3 backend/scripts/standard_from_clean.py \
  --clean-dir runtime/backend/pipeline-work/raw2clean/run-35-pdf-8ada74dfc6d2d66c-popo-20260616234840-staged_popo_20260617_batch06_sma-d552836a--003-popo_8ada74dfc6d2d66c_003/clean-final \
  --raw-dir runtime/backend/pipeline-work/raw2clean/run-35-pdf-8ada74dfc6d2d66c-popo-20260616234840-staged_popo_20260617_batch06_sma-d552836a--003-popo_8ada74dfc6d2d66c_003/raw_input \
  --source-pdf runtime/backend/pipeline-work/popo2raw/run-34-pdf-8ada74dfc6d2d66c-popo-20260616234840-staged_popo_20260617_batch06_sma-d552836a--003-popo_8ada74dfc6d2d66c_003/rebuild_input/pdf-8ada74dfc6d2d66c_origin.pdf \
  --profile grammar_workbook \
  --out-dir runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v2-rerun-20260630/standard-final \
  --generate-source-crops \
  --force

python3 backend/scripts/close_standard_image_outcomes.py \
  --standard-dir runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v2-rerun-20260630/standard-final \
  --apply

python3 backend/scripts/close_standard_review_outcomes.py \
  --standard-dir runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v2-rerun-20260630/standard-final
```

Closure scripts must run serially. They both write review outcome state; running them in parallel can overwrite closure results.

## Rule Feedback From GF4

GF4 V0 exposed two real profile gaps that GF6 did not expose strongly enough:

- workbook instruction detection missed `Change` and `Rewrite`;
- some grammar explanation tables were misread as orphan table questions.

GF4 V1 reduced the real profile gaps from 36 to 4:

- `real_profile_gap_count`: 36 -> 4;
- `orphan_table_questions`: 2 -> 0;
- `question_groups`: 132 -> 139.

The remaining four gaps were grammar explanation lines such as:

```text
1 = one time once
2 = two times twice
```

GF4 V2 classifies those as `explanation_artifact`, not workbook exercise items.

During table closure, two table outcomes exposed harmless Raw OCR spacing differences:

```text
Possessive adjectives -> Possessiveadjectives
Possessive pronouns   -> Possessivepronouns
-y + -ily             -> -y+ -ily
```

The closure rule now accepts length-gated compact exact Raw table matches plus source PDF crop evidence. It does not accept fuzzy matches.

The table source evidence fallback decision is recorded in:

```text
docs/standard-research/16-table-source-evidence-fallback-v0.md
```

Implemented general rules in `backend/scripts/standard_from_clean.py`:

- `Change` and `Rewrite` are workbook instruction verbs;
- grammar paradigm tables such as possessive adjective/pronoun tables and affirmative/short form/negative tables are explanation tables;
- numbered grammar equivalence lines are explanation artifacts in relation audit.
- Raw table visual closure can use compact exact matching for OCR spacing differences when source page/bbox and source crop are available.

Tests were added in `backend/tests/test_standard_from_clean.py` for those cases.

## V2 Result

Acceptance remains `review`, not `pass`.

Key files:

```text
runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v2-rerun-20260630/standard-final/standard_acceptance_report.json
runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v2-rerun-20260630/standard-final/workbook_profile_report.json
runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v2-rerun-20260630/standard-final/workbook_relation_audit.json
runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v2-rerun-20260630/standard-final/visual_outcome_review.json
```

Acceptance summary:

```text
status: review
quality_score: 97
profile_coverage: pass
image_relation_integrity: pass
image_visual_confirmation: pass
review_outcomes: review
formula_table_integrity: review
print_render: pass
pdf_page_count: 99
```

Workbook profile summary:

```text
status: review
exercise_relation_contract: pass
image_relation_contract: pass
basic_print_blockers: table_visual_review_outcomes_open
question_groups: 139
questions: 611
grouped_questions: 607
ungrouped_questions: 4
table_questions: 25
parented_table_questions: 25
orphan_table_questions: 0
figure_relation_candidates: 138
real_profile_gap_count: 0
```

Image outcome summary:

```text
issue_candidate_count: 138
covered_by_visual_outcome: 103
helper_icon_compact_rendering: 35
unresolved_blocking_count: 0
image_review_outcome_open_blocking_count: 0
```

Visual outcome summary:

```text
review_outcome_closed_count: 130
review_outcome_open_blocking_count: 3
accepted_by_rule: 130
needs_reconstruction: 3
visual_review_source_crop_count: 30
```

Closed by compact exact Raw table match:

```text
visual:table_visual_review:b-00344  source page 23  bbox [118, 324, 482, 600]
visual:table_visual_review:b-00405  source page 26  bbox [85, 326, 663, 411]
```

Open blockers:

```text
table_visual_review needs_reconstruction: 3
```

Open table outcomes:

```text
visual:table_visual_review:b-01544  table_question  Review 5  page 79  bbox [70, 541, 885, 648]   needs_reconstruction
visual:table_visual_review:b-01548  table_question  Review 5  page 80  bbox [37, 89, 890, 195]   needs_reconstruction
visual:table_visual_review:b-01550  table_question  Review 5  page 80  bbox [38, 283, 930, 388]   needs_reconstruction
```

Manual visual review evidence:

```text
visual_source_crops/0026-b-01544-image.png
visual_source_crops/0028-b-01548-image.png
visual_source_crops/0029-b-01550-image.png
manual_visual_review/standard-page-98.png
manual_visual_review/standard-page-99.png
```

Review finding:

```text
Source crops preserve line-by-line grammar paradigm tables.
Standard rendering collapses those line-by-line entries into run-together table-cell text.
This is not Basic Print acceptable and requires reconstruction or line-break-preserving table rendering.
```

## Conclusion

GF4 should not be promoted to a Basic Print candidate yet.

What is validated:

- GF6 image disposition rules generalize to a second Grammar Friends sample.
- The grammar_workbook relation contract can pass on GF4 after non-sample-specific profile rule hardening.
- The next blocker is table reconstruction or line-break-preserving table rendering for three Review 5 grammar paradigm tables, not workbook exercise relation structure.

What is not validated:

- GF4 visual Basic Print acceptance.
- Generalization beyond the Grammar Friends series.
- Workbook layout polish or style quality beyond Basic Print gates.

Next small closure:

1. Implement a narrow table reconstruction/rendering rule that preserves line breaks inside grammar paradigm table cells.
2. Rerun GF4 and verify the three outcomes against the same source crops.
3. Only after the three table outcomes close should GF4 be considered for candidate review.

## V3 Follow-up - Grammar Paradigm Table Rendering

The narrow table rendering rule was implemented and documented in:

```text
docs/standard-research/17-grammar-paradigm-table-rendering-v0.md
```

V3 Standard package:

```text
runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final
```

Key evidence:

```text
standard.html
standard.pdf
manual_visual_review/standard-page-98.png
manual_visual_review/standard-page-99.png
visual_source_crops/0026-b-01544-image.png
visual_source_crops/0028-b-01548-image.png
visual_source_crops/0029-b-01550-image.png
```

The V3 HTML/PDF render no longer contains the collapsed fragments that caused the V2 failure:

```text
playingyou: 0
playedyou: 0
am.Yes: 0
have.Yes: 0
was.Yes: 0
grammar-paradigm-table: 3
```

V3 acceptance summary:

```text
status: review
quality_score: 97
review_outcome_closed_count: 132
review_outcome_open_blocking_count: 1
table_formula_review_outcome_open_blocking_count: 1
visual_review_source_crop_count: 30
review_outcomes: review
formula_table_integrity: review
```

V3 visual outcome summary:

```text
accepted_by_rule: 130
accepted: 2
needs_reconstruction: 1
open_blocking_count: 1
```

Closed by manual visual review after grammar paradigm rendering:

```text
visual:table_visual_review:b-01548  accepted
visual:table_visual_review:b-01550  accepted
```

Still open:

```text
visual:table_visual_review:b-01544
decision: needs_reconstruction
next_action: resolve_source_fidelity_mismatch
```

Reason:

```text
Layout is fixed by grammar-paradigm-table reflow, but source crop shows "Yes, they aren’t." while Clean/Standard renders "Yes, they are."
```

Intermediate conclusion:

GF4 no longer had three grammar paradigm table layout blockers. The rendering rule was validated for this failure mode. At this point GF4 remained `review`, not Basic Print candidate, because one source-fidelity blocker remained.

## V3 Final Closure - Source Typo Correction

The remaining source-fidelity blocker was closed under:

```text
docs/standard-research/18-source-fidelity-correction-policy-v0.md
```

Correction artifact:

```text
runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final/correction_log.json
```

Final V3 status:

```text
acceptance_status: pass
quality_score: 100
closure_status: basic_print_candidate
review_outcome_closed_count: 133
review_outcome_open_blocking_count: 0
table_formula_review_outcome_open_blocking_count: 0
correction_count: 1
decision_counts: accepted_by_rule=130, accepted=3
```

The source typo correction:

```text
source crop:   Yes, they aren’t.
Clean/Standard: Yes, they are.
```

Final conclusion:

GF4 V3 is a Basic Print candidate, not an accepted golden. Its promotion depends on three separate validated elements: workbook profile contracts, grammar paradigm table rendering, and one explicit evidence-backed source typo correction.
