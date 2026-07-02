# Workbook Candidate Consolidation V0 - 2026-06-30

Superseding note:

```text
For current grammar_workbook profile status, see 35-grammar-workbook-profile-ready-v0.md.
```

Purpose:

```text
Compare GF6 and GF4 as grammar_workbook Basic Print candidates and decide what can be solidified without over-promoting the workbook profile.
```

## Candidate Set

Current workbook candidates:

```text
GF6  pdf-ff4c7f59964ad54f  Grammar Friends 6  candidate only
GF4  pdf-8ada74dfc6d2d66c  Grammar Friends 4  candidate only
```

Candidate records:

```text
docs/standard-research/corpus/golden/candidates/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.candidate.json
docs/standard-research/corpus/golden/candidates/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.candidate.json
```

Run records:

```text
docs/standard-research/corpus/runs/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.run.json
docs/standard-research/corpus/runs/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.run.json
```

## Shared Facts

Both candidates are:

- `grammar_workbook` profile runs;
- Standard acceptance `pass`;
- quality score `100`;
- Basic Print candidate closure status;
- zero open blocking review outcomes;
- zero unresolved blocking issue candidates;
- workbook relation/profile contract pass;
- image relation contract pass;
- not accepted golden samples.

## Candidate Comparison

```text
GF6:
  review_outcomes: 197 closed / 0 open
  accepted_by_rule: 197
  image_refs: 213
  issue_candidates: 213
  correction_count: 0
  special caveat: page spot check has non-blocking page-break and source annotation notes

GF4:
  review_outcomes: 133 closed / 0 open
  accepted_by_rule: 130
  accepted: 3
  image_refs: 138
  issue_candidates: 138
  correction_count: 1
  special caveat: one evidence-backed source typo correction
```

## Rules Validated Across Both

The following workbook profile rules now have evidence in at least two Grammar Friends samples:

- exercise grouping can pass without suppressing issue candidates;
- ungrouped apparent questions can be classified as front matter or explanation artifacts when evidence supports it;
- explanation tables must not be treated as orphan table questions;
- helper icons can use compact rendering/disposition instead of requiring source visual confirmation;
- content-bearing figures still require source visual outcome closure;
- table/formula visual outcomes must be closed by explicit source evidence or manual outcome review;
- Standard artifact generation does not equal Basic Print acceptance.

## Rules Validated Only By GF4

The following rules are currently GF4-specific evidence, not broad workbook proof:

- grammar paradigm tables with a single run-together body row can be rendered as aligned multi-row tables;
- Raw text-cell bbox union can locate a table source crop for manual review when Raw does not expose a table object;
- a source typo correction can be accepted only when recorded in `correction_log.json` with source crop evidence.

These rules can remain in the compiler/gates because they are profile-general, but they should stay monitored in the next workbook sample.

## Rules Validated Only By GF6

The following rules are currently GF6-specific evidence:

- large-scale image outcome closure over 170 key figures;
- 43 helper icon compact rendering dispositions;
- non-blocking table-instruction page break handling;
- source-PDF handwritten/filled marks treated as a Clean/source-fidelity policy issue rather than a Standard image-relation hard fail.

These are useful workbook evidence, but should not be overgeneralized to all workbook families.

## Promotion Readiness

Current recommendation:

```text
Do not promote grammar_workbook to accepted golden/profile-complete status yet.
```

Reason:

- both workbook candidates are from the same Grammar Friends series;
- GF4 required a newly defined source correction policy;
- GF6 still has source annotation caveats;
- neither candidate proves broader workbook families such as math workbooks, bilingual worksheets, test prep, or diagram-heavy exercise books;
- `accepted_by_rule` and manual `accepted` outcomes have different evidence meanings and must remain separated.

What can be solidified now:

- candidate corpus format for workbook samples;
- review outcome closure schema;
- image relation gate;
- helper icon compact disposition;
- grammar paradigm table rendering rule;
- source correction evidence gate.

What should remain candidate-only:

- the full `grammar_workbook` Basic Print profile as an accepted universal standard;
- using GF6 or GF4 as official accepted golden without a separate promotion decision;
- broad source typo correction beyond explicit evidence-backed cases.

## Next Small Closures

Recommended next steps:

1. Create a workbook promotion checklist that distinguishes candidate, accepted golden, and profile-ready status. Completed in `20-workbook-promotion-checklist-v0.md`.
2. Add a third workbook pressure sample outside the Grammar Friends series.
3. Keep math profile separate; do not use GF4/GF6 to infer math workbook readiness.

Acceptance for the next workbook sample:

- Standard acceptance `pass`;
- workbook profile contract `pass`;
- no open blocking outcomes;
- all corrections, if any, recorded with evidence;
- no sample-specific hardcoding by filename, title, material_id, page, or block id;
- page spot check or equivalent visual review completed.

## Conclusion

GF6 and GF4 together move `grammar_workbook` from a single-sample candidate to a two-sample candidate track. They are strong enough to solidify gates and corpus mechanics, but not strong enough to declare the workbook profile generally solved.
