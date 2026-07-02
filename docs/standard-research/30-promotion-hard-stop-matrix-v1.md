# Promotion Hard-Stop Matrix V1 - 2026-07-01

Purpose:

```text
Summarize, from current corpus manifests and runtime artifacts, which Standard Basic Print samples may be used as accepted golden, candidate, review pressure, or blocked evidence, and what hard stops prevent promotion.
```

This document does not promote any sample. It is a guardrail against treating green Standard reports, closed outcomes, or local subtrack closures as release readiness.

## Status Matrix

| Sample | Profile | Current status | Promotion ceiling | Hard stop |
| --- | --- | --- | --- | --- |
| RE1 | `reading_textbook` | `basic_print_accepted` | accepted golden | Scope limited to first reading-textbook Basic Print golden; does not prove workbook/math profiles |
| GF6 | `grammar_workbook` | `basic_print_candidate` | candidate only | Candidate remains not accepted golden; deterministic closures are not human visual final |
| GF4 | `grammar_workbook` | `basic_print_candidate` | candidate only | Candidate remains not accepted golden; source correction remains evidence-gated |
| GIC | `grammar_workbook` | `basic_print_candidate` | candidate only | Candidate remains not accepted golden; Clean closure is ledger-based |
| G7+ | `exercise_workbook` | `standard_review_pressure_run` | review pressure only | Standard acceptance remains `review`; main run still has open blocking review outcomes and formula page-bbox gaps; remaining relation contract packets are math-heavy boundary evidence, not generic exercise_workbook pass evidence |
| Math 8A | `math_textbook` | `math_profile_blocked_review` | blocked/review | Selector now chooses `math_textbook`, source crops cover `998/1157`, and exact/safe closure closes `879` outcomes; `278` formula visual outcomes remain open: `159` page/bbox gaps, `116` containment-context review items, and `3` digit-spacing review items |

## Current Evidence Paths

| Sample | Case | Latest run / golden |
| --- | --- | --- |
| RE1 | `docs/standard-research/corpus/cases/pdf-e71fe159994b50f3.case.json` | `docs/standard-research/corpus/golden/accepted/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.golden.json` |
| GF6 | `docs/standard-research/corpus/cases/pdf-ff4c7f59964ad54f.case.json` | `docs/standard-research/corpus/golden/candidates/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.candidate.json` |
| GF4 | `docs/standard-research/corpus/cases/pdf-8ada74dfc6d2d66c.case.json` | `docs/standard-research/corpus/golden/candidates/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.candidate.json` |
| GIC | `docs/standard-research/corpus/cases/pdf-01ae095f5a0f2dc7.case.json` | `docs/standard-research/corpus/runs/pdf-01ae095f5a0f2dc7.gic-workbook-relation-rule-v8-20260630.run.json` |
| G7+ | `docs/standard-research/corpus/cases/pdf-58860644b15e909c.case.json` | `docs/standard-research/corpus/runs/pdf-58860644b15e909c.g7plus-non-gf-workbook-pressure-v0-20260630.run.json` |
| Math 8A | `docs/standard-research/corpus/cases/pdf-aadfa33fb0485c1a.case.json` | `docs/standard-research/corpus/runs/pdf-aadfa33fb0485c1a.math-remaining-exact-surface-closure-v0-20260701.run.json` |

## Promotion Rules Currently Active

### Candidate

A workbook may remain or become a candidate only when all of these are true:

- Standard acceptance `pass`;
- quality score at least `90`;
- workbook profile, exercise relation, image relation, review outcomes, and PDF render are pass;
- open blocking review outcomes are `0`;
- unresolved blocking issue candidates are `0`;
- corrections are recorded with evidence;
- upstream Clean is pass, or any Clean review scope is explicitly resolved by a reusable rule.

### Accepted Golden

Additional hard stops:

- no accepted golden promotion without a dedicated promotion decision;
- no promotion if the only positive workbook evidence is one family;
- no promotion if any correction policy is newly introduced and not separately accepted;
- no promotion if visual-sensitive closures are based only on artifact existence;
- no promotion if a sample is marked review pressure or Clean-not-promoted.

### Profile-Ready

Hard stops:

- no profile-ready claim from GF6/GF4 alone;
- `grammar_workbook` profile-ready v0 requires GF6/GF4/GIC together and is limited to grammar workbook Basic Print compiler/profile contract;
- G7+ cannot count as positive `exercise_workbook` evidence while Standard is `review`;
- math-heavy table/figure/model families must not be absorbed into generic `exercise_workbook`;
- math/diagram-heavy workbooks require a separate math profile track.

## Updated Hard Stops By Sample

### GF6

```text
candidate only
```

Hard stops:

- same family as GF4;
- deterministic `accepted_by_rule` closure only;
- page spot check notes and source annotation policy are not accepted golden evidence.

### GF4

```text
candidate only
```

Hard stops:

- same family as GF6;
- candidate depends on `18-source-fidelity-correction-policy-v0.md`;
- `b-01544` correction is explicit and evidence-backed, but still a manual correction policy, not broad source-fidelity approval.

Validated subtrack:

```text
grammar_paradigm_table_rebuild validated for GF4 failure mode only.
```

### GIC

```text
basic_print_candidate
```

Current facts:

- Standard v8 acceptance `pass`;
- quality score `100`;
- workbook profile `pass`;
- real profile gap count `0`;
- review outcomes `377/377` closed;
- open blocking Standard review outcomes `0`.
- clean promotion blocker audit: `docs/standard-research/31-gic-clean-promotion-blocker-audit-v0.md`
- clean closure policy audit: `docs/standard-research/32-gic-clean-closure-policy-audit-v0.md`
- clean media purpose ledger: `docs/standard-research/33-gic-clean-media-purpose-ledger-v0.md`
- candidate promotion: `docs/standard-research/34-gic-basic-print-candidate-promotion-v0.md`

Hard stop:

```text
Do not promote GIC from candidate to accepted golden without a separate accepted-golden promotion review.
```

Clarification:

```text
The media and LLM review gates are closed by reusable ledgers for GIC. This resolves the Clean-not-promoted blocker but does not mutate Clean `acceptance_report.json` and does not make GIC accepted golden.
```

### G7+

```text
review pressure only
```

Current facts:

- latest main Standard quality score `94`;
- Standard review outcomes `4340`;
- open blocking review outcomes `162`;
- remaining formula page-bbox gaps `148`;
- paired-vocabulary blank-box subrule is closed only for its narrow real-PDF rerun;
- remaining source-context contract-review packets are `18/18` math-heavy profile-boundary cases, so no generic exercise_workbook table rule is allowed.

Hard stop:

```text
Do not promote any G7+ subtrack closure to exercise_workbook candidate. The main run remains review pressure because formula source evidence, visual/review replay, table/figure relation families, and math-heavy profile boundaries are not closed.
```

### Math 8A

```text
math profile blocked/review
```

Hard stop:

```text
Do not judge math_textbook profile readiness from selector success, source-location recovery, or partial exact-match closure alone. Local source crops now exist for 998 outcomes and 879 outcomes are closed, but 278 formula outcomes remain open behind page/bbox, containment-context, and digit-spacing blockers.
```

## Current Overall Verdict

```text
Standard Basic Print is not ready for engineering release.
```

Why:

- only RE1 is accepted golden;
- GF6/GF4/GIC make `grammar_workbook` profile-ready v0, but none are accepted golden;
- G7+ remains exercise_workbook review pressure;
- math-heavy profile boundary is identified but not implemented;
- math profile is blocked/review;
- profile-ready evidence is still insufficient across exercise_workbook/math layouts.
