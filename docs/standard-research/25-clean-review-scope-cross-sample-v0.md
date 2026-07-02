# Clean Review Scope Cross-Sample V0 - 2026-06-30

Superseding note:

```text
For current GIC candidate/profile status, see 34-gic-basic-print-candidate-promotion-v0.md and 35-grammar-workbook-profile-ready-v0.md.
```

Purpose:

```text
Check whether upstream Clean review status is a promotion blocker for current Standard Basic Print samples, without changing Clean acceptance or promoting any sample.
```

This audit uses:

```text
backend/scripts/scope_clean_review_for_standard.py
```

Rule boundary:

- `clean_pass_no_scope_needed` means the upstream Clean artifact is already `pass`; no Clean review scope closure is needed for this Standard artifact.
- `review_scoped_not_promoted` means the Standard artifact contains the observed Clean review risk, but this does not convert Clean from `review` to `pass`.
- `promotion_candidate` remains `false` in this scope report. Promotion is still a separate corpus/golden decision.

## Cross-Sample Result

| Sample | Profile | Clean scope status | Standard role | Decision |
| --- | --- | --- | --- | --- |
| RE1 | `reading_textbook` | `clean_pass_no_scope_needed` | accepted golden | No Clean review blocker |
| GF6 | `grammar_workbook` | `clean_pass_no_scope_needed` | candidate only | No Clean review blocker; still not accepted golden |
| GF4 | `grammar_workbook` | `clean_pass_no_scope_needed` | candidate only | No Clean review blocker; still not accepted golden |
| GIC | `grammar_workbook` | `review_scoped_not_promoted` | Standard gate candidate | Clean review remains promotion blocker |

## Evidence

RE1:

- run: `docs/standard-research/corpus/runs/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.run.json`
- artifact: `runtime/backend/pipeline-work/audits/re1-review-outcome-v0-rerun-20260629/standard-final`
- scope report: `runtime/backend/pipeline-work/audits/re1-review-outcome-v0-rerun-20260629/standard-final/clean_review_scope_report.json`

GF6:

- run: `docs/standard-research/corpus/runs/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.run.json`
- artifact: `runtime/backend/pipeline-work/audits/gf6-workbook-profile-regression-v1-rerun-20260629/standard-final`
- scope report: `runtime/backend/pipeline-work/audits/gf6-workbook-profile-regression-v1-rerun-20260629/standard-final/clean_review_scope_report.json`

GF4:

- run: `docs/standard-research/corpus/runs/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.run.json`
- artifact: `runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final`
- scope report: `runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final/clean_review_scope_report.json`

GIC:

- run: `docs/standard-research/corpus/runs/pdf-01ae095f5a0f2dc7.gic-workbook-relation-rule-v8-20260630.run.json`
- artifact: `runtime/backend/pipeline-work/audits/gic-standard-workbook-relation-rule-v8-20260630/standard-final`
- scope report: `runtime/backend/pipeline-work/audits/gic-standard-workbook-relation-rule-v8-20260630/standard-final/clean_review_scope_report.json`
- scoped review gates: `media_review_threshold`, `llm_structure_revert_threshold`
- unscoped review gates: `0`

## Conclusion

Current evidence separates two issues:

1. GF6 and GF4 are not blocked by upstream Clean review. Their remaining limitation is promotion/generalization, not Clean acceptance.
2. GIC is a stronger non-Grammar-Friends `grammar_workbook` Standard gate candidate, but remains blocked from accepted-golden/profile-ready promotion because Clean v3 is still `review`.

This supports the current `grammar_workbook` conclusion:

```text
candidate-only, not profile-ready
```

Reason:

- GF6 and GF4 are same-series candidates with Clean pass.
- GIC proves the Standard compiler/profile rules can pass on a non-Grammar-Friends grammar workbook, but its upstream Clean review prevents accepted-golden promotion.
- `review_scoped_not_promoted` is useful evidence, not a promotion rule.

## Next Loop

The next validation loop should not re-litigate whether GF6/GF4/GIC have Clean scope reports. Instead choose one:

1. define a reusable Clean-level closure policy for GIC's `media_review_threshold` and `llm_structure_revert_threshold`; or
2. keep GIC as Standard-gate-only evidence and select another non-Grammar-Friends workbook sample with Clean `pass`.

Stop condition:

- do not promote GIC while Clean acceptance remains `review`;
- do not declare `grammar_workbook` profile-ready from GF6/GF4 plus a Clean-review-blocked GIC run;
- do not treat `clean_review_scope_report.json` as an accepted-golden promotion artifact by itself.
