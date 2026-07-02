# Math-Heavy Profile Boundary V0 - 2026-07-01

Purpose:

```text
Define the current boundary between exercise_workbook, math-heavy workbook/textbook, and math_textbook validation, using G7+ and Math 8A evidence.
```

This is a research/profile-boundary decision. It is not a compiler implementation and does not promote any sample.

## Evidence Inputs

G7+ contract family decision audit:

```text
runtime/backend/pipeline-work/audits/g7plus-contract-family-decision-audit-20260701/workbook_contract_family_decision_audit.json
```

Math 8A source evidence audit:

```text
runtime/backend/pipeline-work/audits/math-profile-review-v0-rerun-20260630/standard-final/visual_source_crop_audit.json
```

Math 8A bbox fallback audit:

```text
runtime/backend/pipeline-work/audits/math-profile-review-v0-rerun-20260630/standard-final/visual_bbox_backfill_audit.json
```

## Facts

G7+:

| Metric | Count |
| --- | ---: |
| remaining source-context contract-review packets | `18` |
| math-heavy profile-boundary packets | `18` |
| generic exercise_workbook rerun candidates | `0` |

Math 8A:

| Metric | Count |
| --- | ---: |
| formula/table visual outcomes | `1157` |
| source crops generated | `600` |
| still needs page/bbox | `557` |
| Raw bbox fallback located | `0` |
| selected profile | `reading_textbook` |
| expected profile | `math_textbook` |

## Boundary Decision

`exercise_workbook` should cover:

- ordinary workbook question grouping;
- options and answer blanks;
- non-math-heavy exercise tables that behave as question components;
- image/helper icon relation decisions that do not require formula/model/diagram semantics.

`math_heavy_workbook` / `math_textbook` must cover:

- worked-example model tables;
- graph/data tables;
- frequency/probability data tables;
- transformation/rule summary tables;
- figure/table compound explanation units;
- formula-heavy visual review and source-crop evidence;
- math-specific profile selection rather than `reading_textbook` fallback.

## Promotion Boundary

Current gate implications:

```text
can_promote_exercise_workbook_profile = false
can_promote_math_textbook_profile = false
can_add_generic_exercise_workbook_table_rule = false
can_treat_math8a_as_profile_evaluated = false
```

The G7+ remaining relation gaps should not be solved by broadening `exercise_workbook`; Math 8A cannot be judged from a run that selected `reading_textbook`.

## Next Engineering Boundary

Before compiler work, the project needs a profile contract decision:

1. Add an explicit `math_textbook` or `math_heavy_workbook` profile selector target.
2. Define math visual evidence gates separately from reading/workbook gates.
3. Define relation contracts for math data/model/rule tables separately from ordinary exercise table attachment.
4. Keep source crops as review evidence unless exact/semantic visual closure rules are defined and rerun.

## Stop Conditions

- Do not make G7+ green by absorbing math-heavy tables into generic `exercise_workbook`.
- Do not make Math 8A green by accepting `reading_textbook` profile coverage.
- Do not treat source crop existence as visual acceptance.
- Do not close missing-bbox formula outcomes without new source-location evidence.

## Current Verdict

```text
math-heavy profile boundary identified; profile contract not implemented; release readiness remains blocked.
```
