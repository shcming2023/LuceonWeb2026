# Blank Reconstruction Cross-Sample Audit V0 - 2026-07-01

Purpose:

```text
Test whether the G7+ paired-vocabulary blank-box reconstruction prototype generalizes across workbook table reconstruction cases, without promoting any compiler rule or closing gates.
```

## Inputs

Audit command:

```text
python3 backend/scripts/audit_standard_blank_reconstruction_patterns_cross_sample.py --sample gf4_v2=runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v2-rerun-20260630/standard-final --sample gf4_v3=runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final --sample gf6_v1=runtime/backend/pipeline-work/audits/gf6-workbook-profile-regression-v1-rerun-20260629/standard-final --sample gic_v8=runtime/backend/pipeline-work/audits/gic-standard-workbook-relation-rule-v8-20260630/standard-final --sample g7plus_main=runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --paired-blank-audit g7plus_paired=runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_blank_box_reconstruction_audit.json --out-dir runtime/backend/pipeline-work/audits/standard-blank-reconstruction-cross-sample-20260701
```

Audit artifacts:

```text
runtime/backend/pipeline-work/audits/standard-blank-reconstruction-cross-sample-20260701/blank_reconstruction_cross_sample_audit.json
runtime/backend/pipeline-work/audits/standard-blank-reconstruction-cross-sample-20260701/blank_reconstruction_cross_sample_audit.html
```

Sample scope:

| Sample | Role |
| --- | --- |
| GF4 v2 | historical grammar_workbook reconstruction cases |
| GF4 v3 | latest GF4 candidate artifact |
| GF6 v1 | latest GF6 candidate artifact |
| GIC v8 | non-Grammar-Friends grammar_workbook Standard-gate-pass artifact, Clean-not-promoted |
| G7+ main | exercise_workbook review pressure artifact |
| G7+ paired blank audit | compiler/source-confirmed paired-vocabulary blank-box hard stop |

## Result

| Metric | Count |
| --- | ---: |
| raw audit records | `6` |
| unique reconstruction cases | `5` |
| unique blank-pattern reconstructable cases | `2` |
| unique non-blank grammar paradigm table reconstruction cases | `3` |

Verdict counts:

```text
blank_pattern_reconstructable: 2 unique cases
non_blank_grammar_paradigm_table_reconstruction: 3 unique cases
```

Interpretation:

```text
The G7+ paired-vocabulary blank rules do not generalize to all workbook table reconstruction. They cover the two known G7+ source blank-box blockers, while the GF4 v2 historical reconstruction cases are a different grammar-paradigm table problem: multi-line cell structure was flattened, not source blank boxes lost.
```

## Decision

```text
Do not promote the blank-box prototype into the main Standard compiler yet.
```

Why:

- The positive evidence is limited to `2` unique G7+ paired-vocabulary source blank-box cases.
- The cross-sample audit found `3` GF4 grammar-paradigm reconstruction cases that require a different table rebuild/rendering rule.
- The current G7+ completed formal compiler run is PDF-stubbed, not real visual regression.
- `accepted_by_rule` remains insufficient for these reconstruction cases.

## Next Loop

Recommended split:

```text
1. paired_vocabulary_blank_box_preservation:
   Keep as a candidate subrule for G7+ paired-vocabulary tables only.
   Require real PDF visual regression before compiler promotion.

2. grammar_paradigm_table_rebuild:
   Treat GF4 v2 historical reconstruction cases as a separate workbook grammar table renderer issue.
   Do not solve with blank-box rules.
```

Stop condition:

```text
If a rule cannot distinguish blank-box loss from grammar-paradigm row/line flattening, keep both tracks review-only.
```
