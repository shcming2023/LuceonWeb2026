# Regression Corpus

## Purpose

The corpus separates source cases from Standard run attempts. Current bad Standard outputs must not become golden samples.

## Object Model

### Case

A case is the source material and evidence needed to compile Standard.

```text
case = source PDF + Raw package + Clean package + manifests + evidence
```

The case records what profile should be attempted and what minimum quality level is expected.

### Run

A run is one Standard attempt.

```text
run = standard-final + acceptance report + issue report + review verdict
```

Runs can be failed, review, or accepted. They are evidence, not necessarily standards.

### Golden

A golden sample is a run that has passed the required gates for its target level.

Current project state has one accepted `basic_print` golden sample: RE1 review outcome V0.

## Initial Cases

### GF6 Workbook Case

```text
material_id: pdf-ff4c7f59964ad54f
title: Grammar Friends 6 (Students Book) (Flannigan E.) (Z-Library).pdf
profile: workbook
role: grammar exercises / workbook counterexample
current_score: 85
current_status: review
target_level: basic_print
```

Current active negative regression:

```text
runtime/backend/pipeline-work/audits/gf6-workbook-profile-regression-v1-rerun-20260629/standard-final/
```

Known blockers after workbook regression V1:

- exercise relation contract is still `review`;
- 10 questions are not grouped under an exercise group;
- 7 table questions are not parented to an exercise context;
- 34 figure relation candidates are not parented to an exercise/explanation context;
- 170 key figures have source crops but still need source visual confirmation;
- 26 table visual review outcomes remain open.

Historical blockers that V0/V1 narrowed:

- visible markup leakage;
- audit comment leakage;
- source PDF unavailable in published Standard run;
- question group and workbook structure coverage too weak;
- table/formula visual review not closed.

### RE1 Reading Textbook Case

```text
material_id: pdf-e71fe159994b50f3
title: Reading Explorer 1 Students Book.pdf
profile: reading_textbook
role: closest candidate
published_current_score: 86
audit_mvp_score: 97
current_status: basic_print golden after review outcome V0 promotion
target_level: basic_print
```

Historical blockers before promotion:

- published clean-to-standard runs lack source PDF in Standard script context;
- audit MVP has source PDF and high score, but still has unresolved table visual review packets;
- visible leak hits still need investigation and closure.

Accepted golden:

```text
docs/standard-research/corpus/golden/accepted/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.golden.json
```

### Math Formula-Heavy Case

```text
material_id: pdf-aadfa33fb0485c1a
title: 中学生世界 八上 数学 上册.pdf
profile: math_textbook
role: formula-heavy counterexample
current_score: 84
current_status: review
target_level: review first, then basic_print
```

Known blockers:

- very high formula visual review packet count in current runs;
- source PDF unavailable in published Standard run;
- math profile and formula verification need dedicated work.

This should not be the first closure case.

## Corpus Directory Proposal

Future durable corpus files should follow:

```text
docs/standard-research/corpus/
  cases/
    pdf-ff4c7f59964ad54f.case.json
    pdf-e71fe159994b50f3.case.json
    pdf-aadfa33fb0485c1a.case.json
  runs/
    pdf-e71fe159994b50f3.audit-mvp-20260627.run.json
    pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.run.json
  golden/
    README.md
```

The initial research phase records the policy here before adding machine-readable corpus manifests.

## Verdict Policy

Current Standard outputs should be assigned:

```text
verdict: review
golden: false
```

If a run has visible machine artifacts or missing evidence required by its profile, it may be downgraded to:

```text
verdict: artifact_only
golden: false
```

Only runs that have explicit promotion evidence should be entered into `golden/`. GF6 V1 remains a negative regression comparator, not a golden sample.
