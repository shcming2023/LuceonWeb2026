# Workbook Promotion Review Draft V0 - 2026-06-30

Purpose:

```text
Prevent GF6 or GF4 from being promoted from Basic Print candidate to accepted golden or profile-ready status without a separate evidence review.
```

This document is a draft review scaffold, not a promotion decision.

## Current Decision

```text
Do not promote GF6 or GF4 yet.
```

Reason:

- both workbook candidates are from the Grammar Friends series;
- GF4 includes one evidence-backed source typo correction;
- GF6 closures are all deterministic `accepted_by_rule`;
- GF4 has three manual `accepted` outcomes after grammar paradigm rendering and correction review;
- the non-Grammar-Friends GIC run is now a Basic Print candidate after Clean closure policy v3, while the math-heavy G7+ `exercise_workbook` run remains review pressure.

## Candidate Evidence

### GF6

Evidence paths:

- candidate: `docs/standard-research/corpus/golden/candidates/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.candidate.json`
- run: `docs/standard-research/corpus/runs/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.run.json`
- artifact: `runtime/backend/pipeline-work/audits/gf6-workbook-profile-regression-v1-rerun-20260629/standard-final`

Known decision shape:

- acceptance `pass`;
- quality score `100`;
- review outcomes `197` closed, `0` open blocking;
- all outcomes are `accepted_by_rule`;
- issue candidates `213`, unresolved blocking `0`;
- page spot check is `pass_with_notes`, not a polished layout sign-off.

Promotion hard stops still active:

- no second workbook family evidence;
- source annotation / handwritten marks remain a source-fidelity policy caveat;
- deterministic closure cannot be described as human final visual acceptance.

### GF4

Evidence paths:

- candidate: `docs/standard-research/corpus/golden/candidates/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.candidate.json`
- run: `docs/standard-research/corpus/runs/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.run.json`
- artifact: `runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final`

Known decision shape:

- acceptance `pass`;
- quality score `100`;
- review outcomes `133` closed, `0` open blocking;
- decisions: `130` accepted_by_rule and `3` accepted;
- correction count `1`;
- correction is allowed only through `docs/standard-research/18-source-fidelity-correction-policy-v0.md` and `correction_log.json`.

Promotion hard stops still active:

- same workbook family as GF6;
- correction policy is newly defined;
- manual `accepted` outcomes are not equivalent to `accepted_by_rule`;
- this cannot prove broad workbook source-correction behavior.

## Required Questions Before Any Promotion

1. Is the proposed promotion for one sample, a profile rule, or profile-ready status?
2. Which exact closure rule is being accepted?
3. Which evidence path proves each visual-sensitive closure?
4. Which outcomes are `accepted_by_rule`, and which are manual `accepted`?
5. Are corrections present, and does each have source crop evidence?
6. Does the claim generalize beyond Grammar Friends?
7. Is any code or rule tied to filename, title, material_id, page number, or block id?
8. What would make the next non-Grammar-Friends sample fail?

## Draft Promotion Stop Policy

Keep promotion blocked if any of these are true:

- no non-Grammar-Friends workbook Standard review run exists;
- any review gate remains `review`;
- any correction lacks evidence;
- any visual-sensitive closure is based only on artifact existence;
- any claim says `profile-ready` while evidence comes only from Grammar Friends;
- any rule depends on sample-specific identifiers.

## Next Evidence Needed

Preferred next sample:

```text
pdf-01ae095f5a0f2dc7 / Grammar in Context Baisic (Seventh).pdf
```

Why:

- grammar/workbook-like;
- outside Grammar Friends;
- existing Popo2Raw, Clean, and Standard v8 evidence;
- Standard gates pass and Clean closure policy v3 passes, so it can be counted as a candidate; it is still not accepted golden/profile-ready without a separate promotion decision.

Non-Grammar-Friends pressure run:

```text
pdf-58860644b15e909c / (7)G7+.pdf
```

Why:

- Clean package exists and passes Clean gates;
- outside Grammar Friends;
- math-heavy, image-heavy, table-heavy.
- Standard review run exists and remains `review` with quality score `85`.

Limit:

- use only as `exercise_workbook` or math-heavy pressure evidence;
- do not use it to declare `grammar_workbook` profile-ready.

Evidence:

- run: `docs/standard-research/corpus/runs/pdf-58860644b15e909c.g7plus-non-gf-workbook-pressure-v0-20260630.run.json`
- artifact: `runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final`
- promotion hard stops: `docs/standard-research/30-promotion-hard-stop-matrix-v1.md`

## Draft Verdict

GF6, GF4, and GIC remain Basic Print candidates, not accepted golden. The grammar_workbook profile now has enough candidate evidence for `grammar_workbook_profile_ready_v0`; the next real promotion work should target accepted-golden selection or the unresolved `exercise_workbook` / math tracks without lowering Basic Print standards.
