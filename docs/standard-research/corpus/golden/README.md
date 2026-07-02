# Golden Standard Outputs

This directory tracks official Basic Print golden samples and candidate comparators.

## Official Basic Print Golden Samples

Current official Basic Print golden:

- `accepted/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.golden.json`

Why RE1 is promoted:

- Standard acceptance status is `pass`;
- score is 97;
- issue candidates are zero;
- visible artifact count is zero;
- all gates are `pass`;
- all 15 table visual packets are closed as `accepted_by_rule`;
- source PDF crops exist for the 15 table packets.

Accepted rule:

```text
accepted_by_rule = exact normalized Raw table match + source PDF page/bbox + generated or reused source PDF crop
```

## Candidate Golden Samples

Candidate golden samples are useful comparators, but they are not accepted `basic_print` outputs.

Promoted candidate:

- `candidates/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.candidate.json`

Why RE1 review outcome V0 is a stronger candidate:

- Standard acceptance status is `pass` after review outcome closure;
- score is 97;
- issue candidates are zero;
- visible artifact count is zero;
- all 15 table visual packets are closed as `accepted_by_rule`;
- source PDF crops exist for the 15 table packets.

Promotion status:

- promoted to official Basic Print golden on 2026-06-29.

Previous candidate:

- `candidates/pdf-e71fe159994b50f3.re1-audit-mvp-20260627.candidate.json`

Why RE1 is a candidate:

- source PDF evidence is available;
- PDF renders with readable page count;
- outline, source fidelity, media integrity, context integrity, and auditability pass;
- issue candidates are zero;
- remaining review scope is narrow and visible: table visual verification.

Why it is not promoted:

- status is still `review`;
- table visual review is unresolved;
- the older package does not yet include the new `visible_artifacts` report gate.

Workbook candidate:

- `candidates/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.candidate.json`
- `candidates/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.candidate.json`
- `candidates/pdf-01ae095f5a0f2dc7.gic-workbook-clean-closure-v3-20260701.candidate.json`

Why GF6 is a candidate:

- Standard acceptance status is `pass`;
- score is 100;
- all 197 review outcomes are closed as `accepted_by_rule`;
- all 213 `missing_raw_image_semantics` issue candidates are dispositioned;
- unresolved blocking issue count is zero;
- page-level spot check is `pass_with_notes` with zero blocking findings.

Why GF6 is not promoted:

- it is the first positive workbook-profile candidate, so the rule should not yet be generalized from one sample;
- `accepted_by_rule` is deterministic evidence closure, not human visual final approval;
- the page spot check has non-blocking notes about a table instruction page break and source-PDF handwritten marks;
- source annotation handling remains a Clean/source-fidelity policy decision.

Why GF4 is a candidate:

- Standard acceptance status is `pass`;
- score is 100;
- all 133 review outcomes are closed;
- three Review 5 grammar paradigm table layout failures are resolved by the rendering rule;
- one source typo correction is explicit and evidence-backed in `correction_log.json`;
- unresolved blocking issue count is zero.

Why GF4 is not promoted:

- it is still only the second Grammar Friends workbook sample;
- its candidate status depends on a newly defined source-fidelity correction policy;
- the source typo correction is manually accepted, not `accepted_by_rule`;
- the correction policy must be tested on more samples before becoming a broad Standard rule.

Workbook consolidation:

- current workbook consolidation record: `../../19-workbook-candidate-consolidation-v0.md`;
- workbook promotion checklist: `../../20-workbook-promotion-checklist-v0.md`;
- corpus status audit: `../../29-corpus-status-consistency-audit-v1.md`;
- workbook promotion review draft: `../../22-workbook-promotion-review-draft-v0.md`;
- third workbook pressure sample selection: `../../23-third-workbook-pressure-sample-selection-v0.md`;
- Basic Print readiness matrix: `../../24-basic-print-readiness-matrix-v0.md`;
- current promotion hard-stop matrix: `../../30-promotion-hard-stop-matrix-v1.md`;
- GF6/GF4/GIC are enough for `grammar_workbook_profile_ready_v0`;
- none of GF6/GF4/GIC are accepted golden.

Third workbook candidate:

- `candidates/pdf-01ae095f5a0f2dc7.gic-workbook-clean-closure-v3-20260701.candidate.json`
- `../cases/pdf-01ae095f5a0f2dc7.case.json`

Current status:

```text
basic_print_candidate
```

Why GIC is a candidate:

- Standard v8 gates pass with quality score `100`;
- workbook profile, exercise relation, image relation, review outcomes, source evidence, and PDF render gates pass;
- `377/377` Standard review outcomes are closed as `accepted_by_rule`;
- Clean media review is closed by purpose/role ledger;
- Clean LLM rollback review is closed by fallback ledger;
- closure policy v3 is `clean_review_closure_policy_pass`.

Why GIC is not promoted:

- it is a candidate only, not an accepted golden;
- Clean acceptance remains `review` on disk and is resolved by separate closure ledgers;
- it contributes to `grammar_workbook_profile_ready_v0`, but does not become accepted golden.

Grammar workbook profile:

- `../../35-grammar-workbook-profile-ready-v0.md`
- profile verdict: `grammar_workbook_profile_ready_v0`
- scope: grammar workbook Basic Print compiler/profile contract only

Non-Grammar-Friends pressure run:

- `../cases/pdf-58860644b15e909c.case.json`
- `../runs/pdf-58860644b15e909c.g7plus-non-gf-workbook-pressure-v0-20260630.run.json`

Current status:

```text
standard_review_pressure_run
```

Why it is not a candidate golden:

- Standard acceptance is `review`;
- latest main quality score is `94`;
- open blocking review outcomes are `162`;
- remaining formula page-bbox gaps are `148`;
- paired-vocabulary compiler/source table ids match, but source blank-box blockers remain `b-03276` and `b-09582`;
- completed paired-vocabulary formal compiler run is PDF-stubbed and is not real visual regression evidence;
- it is math-heavy `exercise_workbook` pressure evidence, not grammar_workbook profile-ready evidence.

Math profile blocker:

- `../cases/pdf-aadfa33fb0485c1a.case.json`
- `../runs/pdf-aadfa33fb0485c1a.math-profile-review-v0-20260630.run.json`

Current status:

```text
math_profile_blocked_review
```

Why it is not a candidate golden:

- selected Standard profile is `reading_textbook`, not `math_textbook`;
- Standard acceptance is `review`;
- quality score is `86`;
- formula/table visual outcomes open: `1157`;
- source PDF evidence is missing from the Standard run.
