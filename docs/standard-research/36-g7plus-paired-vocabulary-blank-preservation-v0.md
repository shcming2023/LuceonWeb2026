# G7+ Paired Vocabulary Blank Preservation V0 - 2026-07-01

Purpose:

```text
Close only the G7+ paired-vocabulary blank-box preservation subrule after compiler integration and real Standard PDF rendering, without promoting the whole exercise_workbook profile.
```

## Evidence

Standard rerun:

```text
runtime/backend/pipeline-work/audits/g7plus-paired-vocab-blank-preservation-rerun-20260701/standard-final
```

Audit artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-paired-vocab-blank-preservation-rerun-20260701/standard-final/paired_vocabulary_blank_box_reconstruction_audit.json
runtime/backend/pipeline-work/audits/g7plus-paired-vocab-blank-preservation-rerun-20260701/standard-final/paired_vocabulary_blank_box_reconstruction_audit.html
```

Source evidence inputs:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_source_confirmation.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_compiler_delta_source_confirmation.json
```

Validation command:

```text
python3 backend/scripts/audit_standard_paired_vocabulary_blank_box_reconstruction.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-paired-vocab-blank-preservation-rerun-20260701/standard-final --source-report runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_source_confirmation.json --source-report runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_compiler_delta_source_confirmation.json
```

## Result

| Metric | Value |
| --- | ---: |
| paired-vocabulary groups | `9` |
| compiler table ids | `10` |
| source-confirmed table ids | `10` |
| compiler/source table ids match | `true` |
| real PDF render ok | `true` |
| PDF page count | `736` |
| previously blocking records with preserved source blanks | `2` |
| preserved source blank spans | `6` |
| remaining known blank-box blockers | `0` |

Resolved blocker table ids:

```text
b-03276
b-09582
```

Gate implication:

```text
can_close_paired_vocabulary_relation_gap = true
can_promote_exercise_workbook_profile = false
```

## Decision

```text
The paired-vocabulary blank-box hard stop is closed as a narrow subrule.
```

This is not a G7+ acceptance decision. The rerun status is still `review` with quality score `85`, and it did not replay the full source-crop/review-outcome closure stack from the main G7+ pressure run. It is valid evidence for the paired-vocabulary blank preservation rule only.

## Boundary

Do not infer any of the following from this closure:

- `exercise_workbook` profile readiness;
- G7+ Basic Print candidate status;
- acceptance of all table reconstruction cases;
- acceptance of math/formula source-location gaps;
- human visual final approval.

Current G7+ status remains:

```text
standard_review_pressure_run
```

The remaining blockers are broader exercise relation grouping/state-machine design, table attachment policy, formula/table visual review, source PDF lineage, and math-heavy profile behavior.
