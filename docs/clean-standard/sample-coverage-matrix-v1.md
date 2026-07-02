# Clean Standard Sample Coverage Matrix V1

Purpose:

```text
Verify that Luceon Clean Standard Document v1 can express the current Standard research samples without sample-specific fields.
```

This matrix is an abstraction audit, not a promotion decision.

## Coverage Summary

| Sample | Corpus status | Profile contract | V1 representation status | Boundary |
| --- | --- | --- | --- | --- |
| RE1 | `basic_print_accepted` | `reading_textbook` | covered | accepted path requires source-backed closure and golden record |
| GF6 | `basic_print_candidate` | `grammar_workbook` | covered | candidate only, not accepted golden |
| GF4 | `basic_print_candidate` | `grammar_workbook` | covered | candidate only; source typo correction must remain evidenced |
| GIC | `basic_print_candidate` | `grammar_workbook` | covered | candidate only; Clean review scoped/closed by ledgers, not mutated to Clean pass |
| G7+ | `standard_review_pressure_run` | `exercise_workbook` plus math-heavy boundary | covered with blockers | not candidate; unresolved relation/formula/table/source-lineage blockers |
| Math 8A | `math_profile_blocked_review` | `math_textbook` | covered with blockers | not candidate; formula visual/source-location blockers remain |

## RE1 Reading Textbook

Evidence:

- case: `docs/standard-research/corpus/cases/pdf-e71fe159994b50f3.case.json`
- run: `docs/standard-research/corpus/runs/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.run.json`
- artifact: `runtime/backend/pipeline-work/audits/re1-review-outcome-v0-rerun-20260629/standard-final`

Relevant facts:

- upstream Clean is `pass`;
- `clean_review_scope_report.json` is `clean_pass_no_scope_needed`;
- Standard acceptance is `pass`, quality score `97`;
- PDF page count `141`;
- missing images `0`;
- issue candidates `0`;
- review outcomes `15/15` closed;
- accepted rule is exact normalized Raw table match plus page/bbox plus generated source crop.

Required v1 primitives:

- blocks: `unit`, `lesson`, `section`, `reading_passage`, `question`, `option`, `answer_blank`, `table`, `figure`, `caption`, `paragraph`;
- relations: `contains`, `belongs_to_passage`, `has_option`, `has_answer_blank`, `has_table`, `has_figure`, `has_caption`, `source_equivalent_to`;
- source evidence: table Raw content match, page/bbox, source crop;
- review flags: none required for current accepted path after closure.

Representation verdict:

```text
covered_for_accepted_reading_textbook_path
```

Promotion boundary:

V1 can express why RE1 is eligible for accepted golden, but Clean Standard itself does not grant accepted status. The accepted status lives in corpus/golden records.

## GF6 Grammar Workbook

Evidence:

- case: `docs/standard-research/corpus/cases/pdf-ff4c7f59964ad54f.case.json`
- run: `docs/standard-research/corpus/runs/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.run.json`

Relevant facts:

- Standard acceptance is `pass`;
- review outcomes are fully closed;
- image outcomes close by Raw image reference plus source crop, aspect ratio, dimensions, and context evidence;
- helper icons are compact-rendered/excluded from source visual confirmation;
- page-level spot check passed with notes;
- status remains candidate, not accepted.

Required v1 primitives:

- blocks: `grammar_box`, `exercise_group`, `question`, `option`, `answer_blank`, `table`, `figure`, `icon`, `paragraph`;
- relations: `contains`, `belongs_to_exercise`, `has_option`, `has_answer_blank`, `has_table`, `has_figure`, `needs_review_against`;
- assets: `educational`, `helper_icon`, `decorative`;
- review flags: `decorative_media_decision`, `candidate_only_not_accepted`.

Representation verdict:

```text
covered_for_grammar_workbook_candidate
```

Promotion boundary:

Candidate status is representable as corpus state, but v1 must not encode GF6 as accepted.

## GF4 Grammar Workbook

Evidence:

- case: `docs/standard-research/corpus/cases/pdf-8ada74dfc6d2d66c.case.json`
- run: `docs/standard-research/corpus/runs/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.run.json`

Relevant facts:

- v2 exposed missing grammar-workbook rules: Change/Rewrite instructions, grammar paradigm tables, numbered grammar equivalence lines;
- v3 validates grammar paradigm table rendering for the three Review 5 layout failures;
- all review outcomes closed;
- `b-01544` source typo correction is accepted only because it is explicit and evidence-backed;
- status remains candidate.

Required v1 primitives:

- blocks: `grammar_box`, `key_concept`, `exercise_group`, `question`, `answer_blank`, `table`, `paragraph`;
- relations: `explains`, `belongs_to_exercise`, `has_table`, `source_equivalent_to`;
- source evidence: correction evidence for source typo;
- review flags: `candidate_only_not_accepted`.

Representation verdict:

```text
covered_for_grammar_paradigm_and_candidate_boundary
```

Promotion boundary:

The schema supports evidence-backed correction records through source refs and review flags, but accepted-golden promotion remains separate.

## GIC Grammar Workbook

Evidence:

- case: `docs/standard-research/corpus/cases/pdf-01ae095f5a0f2dc7.case.json`
- run: `docs/standard-research/corpus/runs/pdf-01ae095f5a0f2dc7.gic-workbook-relation-rule-v8-20260630.run.json`
- profile-ready decision: `docs/standard-research/35-grammar-workbook-profile-ready-v0.md`

Relevant facts:

- non-Grammar-Friends grammar workbook candidate;
- Standard v8 gates pass;
- workbook relation contract passes with real profile gap count `0`;
- `377/377` review outcomes closed;
- Clean v3 was review, with media and LLM rollback risks later closed/scoped by ledgers;
- candidate only, not accepted golden.

Required v1 primitives:

- blocks: `grammar_box`, `exercise_group`, `question`, `option`, `answer_blank`, `table`, `figure`, `icon`;
- relations: `contains`, `belongs_to_exercise`, `has_option`, `has_answer_blank`, `has_table`, `has_figure`;
- review flags: `clean_review_scoped`, `candidate_only_not_accepted`, `decorative_media_decision`;
- blockers: none after scoped closure for the Standard artifact.

Representation verdict:

```text
covered_for_non_gf_grammar_workbook_candidate
```

Promotion boundary:

Clean review scoping is representable, but it must not rewrite Clean acceptance history.

## G7+ Exercise Workbook Pressure Run

Evidence:

- case: `docs/standard-research/corpus/cases/pdf-58860644b15e909c.case.json`
- run: `docs/standard-research/corpus/runs/pdf-58860644b15e909c.g7plus-non-gf-workbook-pressure-v0-20260630.run.json`
- blocker audit: `docs/standard-research/26-g7plus-exercise-workbook-blocker-audit-v0.md`
- contract boundary: `docs/standard-research/46-g7plus-contract-family-decision-audit-v0.md`

Relevant facts:

- Standard generation and PDF render succeeded;
- media integrity passes after table image-ref collection;
- open blocking review outcomes remain;
- source lineage mismatch risk remains for local PDF vs raw manifest object;
- exercise relation gaps exposed grouping/state-machine limits;
- remaining 18 source-context contract-review packets are all math-heavy boundary cases;
- generic exercise workbook rerun candidates: `0`.

Required v1 primitives:

- blocks: `exercise_group`, `question`, `option`, `answer_blank`, `word_bank`, `vocabulary_item`, `table`, `worked_example`, `figure`, `diagram`, `formula`;
- relations: `belongs_to_exercise`, `continues`, `has_word_bank`, `has_table`, `has_figure`, `needs_review_against`, `blocks_promotion`;
- review flags: `uncertain_relation`, `math_heavy_boundary`, `source_lineage_mismatch`, `formula_visual_review_open`, `table_visual_review_open`, `needs_reconstruction`;
- blockers: `unresolved_relation_gaps`, `formula_page_bbox_gap`, `table_reconstruction_needed`, `source_lineage_unresolved`.

Representation verdict:

```text
covered_as_review_pressure_with_math_heavy_boundary
```

Promotion boundary:

The sample must remain `standard_review_pressure_run`. V1 can express the gaps without making `exercise_workbook` broader.

## Math 8A Math Textbook

Evidence:

- case: `docs/standard-research/corpus/cases/pdf-aadfa33fb0485c1a.case.json`
- latest run: `docs/standard-research/corpus/runs/pdf-aadfa33fb0485c1a.math-remaining-exact-surface-closure-v0-20260701.run.json`
- blocker boundary: `docs/standard-research/56-math8a-remaining-formula-blocker-boundary-v0.md`

Relevant facts:

- selector now chooses `math_textbook`;
- total formula/table visual outcomes: `1157`;
- closed accepted_by_rule: `879`;
- remaining open formula outcomes: `278`;
- open table outcomes: `0`;
- remaining blockers: `159` page/bbox stop-boundary, `116` containment-context review, `3` digit-spacing review.

Required v1 primitives:

- blocks: `chapter`, `lesson`, `section`, `formula`, `table`, `worked_example`, `example`, `question`, `diagram`;
- relations: `contains`, `has_formula`, `has_table`, `explains`, `needs_review_against`, `source_equivalent_to`, `blocks_promotion`;
- source evidence: exact match, raw assignment exact, raw assignment containment, page/bbox, source crop;
- review flags: `formula_visual_review_open`, `missing_page_bbox`, `source_crop_context_too_wide`, `manual_visual_review_needed`;
- blockers: `formula_page_bbox_gap`, `formula_containment_context_gap`, `digit_spacing_review`, `math_profile_contract_missing`.

Representation verdict:

```text
covered_as_math_textbook_blocked_review
```

Promotion boundary:

V1 can express Math 8A without lowering thresholds. It remains blocked/review until math visual and source-location contracts close the blocker buckets.

## Abstraction Result

No sample requires a sample-specific schema field.

The required general additions beyond simple Markdown are:

- first-class `relations`;
- explicit `source_map`;
- asset roles;
- review flags;
- blocker taxonomy;
- profile candidates as advisory signals;
- promotion status outside Clean Standard.
