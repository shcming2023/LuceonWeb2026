# Clean Standard Profile Contracts V1

Purpose:

```text
Define profile validation overlays for Clean Standard Document v1 without changing the JSON shape.
```

Profiles are not formats. A profile is a set of expectations applied to the same `clean_standard.json` structure.

## Shared Gates

Every profile starts with the same Clean Standard gates:

| Gate | Required evidence |
| --- | --- |
| artifact completeness | `clean.md`, `clean_standard.json`, `manifest.json`, `images/`, reports |
| outline integrity | outline blocks and paths are stable |
| source fidelity | educational text is not rewritten without evidence |
| media integrity | referenced educational assets exist; dropped/compact media decisions are recorded |
| relation auditability | important instructional relations are explicit or flagged |
| source evidence auditability | source refs exist for visual-sensitive blocks when available |
| uncertainty preservation | unresolved issues appear as `review_flags` or `blockers` |

If these shared gates fail, Standard must stop or produce only a failed/review artifact.

## `reading_textbook`

Evidence sample:

- RE1 / `pdf-e71fe159994b50f3`

Required structural coverage:

- `unit`, `lesson`, `section`;
- `reading_passage`;
- comprehension/vocabulary `question`, `option`, `answer_blank`;
- educational `figure` and `caption`;
- `table` when present.

Required relations:

- `contains`;
- `belongs_to_passage`;
- `has_option`;
- `has_answer_blank`;
- `has_figure`;
- `has_caption`;
- `has_table`.

Promotion-sensitive evidence:

- tables must have source-equivalence evidence when they create visual review outcomes;
- source page/bbox and source crop are required for deterministic visual closure;
- missing images must be zero;
- open blocking review outcomes must be zero.

Allowed product statuses:

| Condition | Product layer |
| --- | --- |
| shared gates pass and profile review outcomes close | profile certified output |
| shared gates pass but visual evidence is incomplete | standard review draft |
| source fidelity/media/outline hard gate fails | blocked / needs reconstruction |

Accepted-golden status requires corpus/golden promotion records. Clean Standard cannot grant it.

## `grammar_workbook`

Evidence samples:

- GF6 / `pdf-ff4c7f59964ad54f`;
- GF4 / `pdf-8ada74dfc6d2d66c`;
- GIC / `pdf-01ae095f5a0f2dc7`.

Required structural coverage:

- `grammar_box`, `key_concept`, `explanation`;
- `exercise_group`;
- `question`, `option`, `answer_blank`;
- grammar paradigm `table`;
- `figure`, `icon`, and helper/decorative media roles.

Required relations:

- `contains`;
- `explains`;
- `belongs_to_exercise`;
- `has_option`;
- `has_answer_blank`;
- `has_table`;
- `has_figure`.

Promotion-sensitive evidence:

- real relation gap count must be zero for profile-certified output;
- helper icons may be compact/excluded only when explicitly recorded;
- table/formula visual outcomes must close with accepted rules or manual review;
- Clean review scoping is allowed only as an explicit review flag/ledger, not as mutation of Clean history.

Current status boundary:

```text
grammar_workbook profile-ready v0; samples remain candidate-only, not accepted golden.
```

## `exercise_workbook`

Evidence sample:

- G7+ / `pdf-58860644b15e909c` as review pressure.

Required structural coverage:

- `exercise_group`;
- `question`, `option`, `answer_blank`;
- `word_bank`, `vocabulary_item`;
- ordinary exercise `table`;
- `figure`, `caption`, `icon`.

Required relations:

- `belongs_to_exercise`;
- `continues`;
- `has_option`;
- `has_answer_blank`;
- `has_word_bank`;
- `has_table`;
- `has_figure`;
- `needs_review_against`.

Profile boundary:

`exercise_workbook` should cover ordinary workbook grouping, options, blanks, non-math-heavy exercise tables, and image/helper decisions that do not require formula/model/diagram semantics.

It must not absorb:

- worked-example model tables;
- graph/data tables;
- frequency/probability data tables;
- transformation/rule summary tables;
- figure/table compound math explanation units;
- formula-heavy visual review.

Those belong to `math_heavy_workbook` or `math_textbook`.

Current status boundary:

```text
G7+ remains review pressure. It cannot promote exercise_workbook to candidate-ready.
```

## `math_textbook`

Evidence sample:

- Math 8A / `pdf-aadfa33fb0485c1a`.

Required structural coverage:

- `chapter`, `lesson`, `section`;
- `formula`;
- `table`;
- `worked_example`;
- `example`;
- `question`;
- `diagram`.

Required relations:

- `contains`;
- `has_formula`;
- `has_table`;
- `explains`;
- `source_equivalent_to`;
- `needs_review_against`;
- `blocks_promotion`.

Promotion-sensitive evidence:

- formula/table visual outcomes must be closed or explicitly reviewed;
- source page/bbox is required for deterministic formula/table closure;
- raw-assignment containment is source evidence only unless a separate closure rule accepts it;
- digit-spacing risks require manual/vision review or stronger OCR/token evidence;
- source crops are evidence, not acceptance by themselves.

Current status boundary:

```text
math_textbook remains blocked/review. Math 8A still has 278 open formula outcomes.
```

## `math_heavy_workbook`

Status:

```text
boundary profile, not release-ready v1 compiler target
```

Evidence:

- G7+ remaining 18 contract-review packets;
- Math 8A formula/table source evidence blockers.

Required structural families:

- `worked_example`;
- `table`;
- `diagram`;
- `formula`;
- figure/table compound units;
- data/model/probability/frequency/rule-summary structures.

This profile exists to prevent two mistakes:

1. broadening `exercise_workbook` until math-heavy cases look green;
2. treating math visual/source evidence as normal reading/workbook table evidence.

## Promotion Status Rules

Clean Standard may express evidence and blockers, but not final corpus status.

| Corpus status | Required external record |
| --- | --- |
| Standard Review Draft | Standard run record |
| Blocked / Needs Reconstruction | Standard run record plus blocker report |
| Basic Print Candidate | candidate record and promotion decision |
| Basic Print Accepted | accepted golden record and accepted-golden promotion decision |

The compiler may produce `profile_certified_output`, but cannot produce `basic_print_candidate` or `basic_print_accepted` by itself.
