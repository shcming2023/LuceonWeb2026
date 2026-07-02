# Corpus Status Consistency Audit V0 - 2026-06-30

Purpose:

```text
Align corpus case, run, candidate, and accepted-golden records so stale review fields do not get mistaken for current Basic Print status.
```

Scope:

```text
docs/standard-research/corpus/cases/*.case.json
docs/standard-research/corpus/runs/*.run.json
docs/standard-research/corpus/golden/**
runtime/backend/pipeline-work/audits/*/standard-final reports
```

## Authority Order

When records disagree, use this order:

1. Current artifact reports in `standard-final/`.
2. Current run manifest under `corpus/runs/`.
3. Candidate or accepted-golden manifest under `corpus/golden/`.
4. Case manifest under `corpus/cases/`.
5. Historical candidate/run records, only if they are explicitly marked `superseded_by`.

## Findings

### RE1

Current authoritative status:

```text
basic_print_accepted
```

Evidence:

- artifact: `runtime/backend/pipeline-work/audits/re1-review-outcome-v0-rerun-20260629/standard-final`
- run: `corpus/runs/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.run.json`
- golden: `corpus/golden/accepted/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.golden.json`
- acceptance: `pass`
- quality score: `97`
- review outcomes: `15` closed, `0` open blocking, all `accepted_by_rule`

Correction:

- case status changed from `review` to `basic_print_accepted`;
- `golden` changed from `false` to `true`;
- old audit MVP run/candidate marked as superseded historical review evidence.

### GF6

Current authoritative status:

```text
basic_print_candidate
```

Evidence:

- artifact: `runtime/backend/pipeline-work/audits/gf6-workbook-profile-regression-v1-rerun-20260629/standard-final`
- run: `corpus/runs/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.run.json`
- candidate: `corpus/golden/candidates/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.candidate.json`
- acceptance: `pass`
- quality score: `100`
- review outcomes: `197` closed, `0` open blocking, all `accepted_by_rule`
- issue candidates: `213`, unresolved blocking `0`

Correction:

- case profile changed from `workbook` to `grammar_workbook`;
- case status changed from `review` to `basic_print_candidate`;
- old blocker list cleared from current case state;
- earlier GF6 review runs marked as superseded by the workbook regression V1 run.

### GF4

Current authoritative status:

```text
basic_print_candidate
```

Evidence:

- artifact: `runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final`
- run: `corpus/runs/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.run.json`
- candidate: `corpus/golden/candidates/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.candidate.json`
- acceptance: `pass`
- quality score: `100`
- review outcomes: `133` closed, `0` open blocking
- decisions: `130` accepted_by_rule, `3` accepted
- correction count: `1`, evidence-backed

Correction:

- case quality score changed from `97` to `100`;
- latest run and candidate pointers added;
- GF4 V2 run marked as superseded by V3.

### Math Sample

Current authoritative status:

```text
math_profile_blocked_review
```

Evidence:

- case: `corpus/cases/pdf-aadfa33fb0485c1a.case.json`
- run: `corpus/runs/pdf-aadfa33fb0485c1a.math-profile-review-v0-20260630.run.json`
- artifact: `runtime/backend/pipeline-work/audits/math-profile-review-v0-rerun-20260630/standard-final`
- acceptance: `review`
- quality score: `86`
- PDF page count: `64`
- formula/table visual outcomes: `1157` open blocking

Correction:

- case status changed from `review` to `math_profile_blocked_review`;
- latest run pointer added;
- blockers now distinguish profile selector, source evidence, and formula/table review gaps.

### Third Workbook Candidate

Current status:

```text
standard_gates_pass_clean_review_not_promoted
```

Evidence:

- case: `corpus/cases/pdf-01ae095f5a0f2dc7.case.json`
- raw artifact: `runtime/backend/pipeline-work/popo2raw/run-8-pdf-01ae095f5a0f2dc7-popo-20260617014256-staged_popo_20260617_batch07_sma-1369cfec--005-popo_01ae095f5a0f2dc7_005/body-final`
- clean artifact: `runtime/backend/pipeline-work/audits/gic-clean-v3-20260630/clean-final`
- latest Standard artifact: `runtime/backend/pipeline-work/audits/gic-standard-workbook-relation-rule-v8-20260630/standard-final`
- title: `Grammar in Context Baisic (Seventh).pdf`
- raw QA: body pages `30-317`, assigned blocks `4921`, unassigned blocks `0`, source image refs `396`, markdown image refs `152`, table source images `244`
- Clean v3 status: `review`, hard failures `0`, review gates `media_review_threshold` and `llm_structure_revert_threshold`
- Standard v8 status: `pass`, quality score `100`, PDF page count `303`
- Standard v8 review outcomes: `377/377` closed as `accepted_by_rule`, open blocking `0`
- Standard v8 profile gates: workbook profile `pass`, exercise relation contract `pass`, image relation contract `pass`

Correction:

- upgraded from raw-only selection record to Standard gate candidate evidence;
- not counted as accepted golden or profile-ready evidence;
- promotion remains blocked by upstream Clean review status.

### Third Workbook Pressure Run

Current status:

```text
standard_review_pressure_run
```

Evidence:

- case: `corpus/cases/pdf-58860644b15e909c.case.json`
- run: `corpus/runs/pdf-58860644b15e909c.g7plus-non-gf-workbook-pressure-v0-20260630.run.json`
- artifact: `runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final`
- title: `(7)G7+.pdf`
- profile: `exercise_workbook`
- acceptance: `review`
- quality score: `85`
- PDF page count: `734`
- issue candidates: `2661`, unresolved blocking `276` after image source evidence closure
- review outcomes: `940` open blocking after `1201` image outcomes, `2198` table/formula outcomes were closed by rule, and one near-match table was manually accepted
- remaining open visual outcomes: `661` formula page-bbox gaps, `2` table page-bbox gaps, `1` table reconstruction blocker, and `276` image reconstruction
- source crop evidence: `1477/1477` image crops and `2200/2863` table/formula crops generated; `663` table/formula outcomes still need page/bbox

Correction:

- registered as a review pressure run only;
- not counted as Basic Print candidate;
- not eligible for accepted golden promotion.

## Remaining Consistency Caveats

- Historical run manifests use mixed field names such as `path`, `output_dir`, and `standard_output`; this audit does not normalize schema fields beyond status pointers.
- `accepted_by_rule` still means deterministic evidence closure, not human visual final approval.
- GF6 and GF4 remain candidates only; no workbook accepted-golden promotion was made.
- The new third workbook case now has Clean v3 and Standard v8 artifacts, but remains not promoted because Clean v3 is still `review`.

## Verdict

The current corpus now has aligned case statuses for RE1, GF6, GF4, GIC, G7+, and math, and historical GF6/GF4/RE1 records are explicitly marked as superseded where needed. `Grammar in Context` is registered as a non-Grammar-Friends `grammar_workbook` Standard gate candidate blocked by Clean review, while `(7)G7+` is registered as a non-Grammar-Friends `exercise_workbook` review pressure run, not as candidate/golden evidence.
