# G7+ Table Attachment Visual Review Audit V0 - 2026-07-01

Purpose:

```text
Source-context review the 3 question-like table candidates that previously required visual review before contract, without authorizing broad question-like table attachment.
```

## Inputs

Base Standard run:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Contract split:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-contract-audit-20260701/workbook_table_attachment_contract_audit.json
```

Audit command:

```text
python3 backend/scripts/audit_standard_workbook_table_attachment_visual_review.py --base-standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --contract-audit runtime/backend/pipeline-work/audits/g7plus-table-attachment-contract-audit-20260701/workbook_table_attachment_contract_audit.json --source-pdf runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf --out-dir runtime/backend/pipeline-work/audits/g7plus-table-attachment-visual-review-audit-20260701
```

Artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-visual-review-audit-20260701/workbook_table_attachment_visual_review_audit.json
runtime/backend/pipeline-work/audits/g7plus-table-attachment-visual-review-audit-20260701/workbook_table_attachment_visual_review_audit.html
runtime/backend/pipeline-work/audits/g7plus-table-attachment-visual-review-audit-20260701/source_context_crops/
```

## Result

| Block | Contract family | Decision |
| --- | --- | --- |
| `b-06288` | `example_relative_frequency_question_table_explanation` | accepted for narrow contract by source context |
| `b-06296` | `example_relative_frequency_question_table_explanation` | accepted for narrow contract by source context |
| `b-12383` | `example_statistics_question_table_explanation` | accepted for narrow contract by source context |

Summary:

| Metric | Count |
| --- | ---: |
| candidates audited | `3` |
| contract-ready by source context | `3` |
| keep review | `0` |

Gate implications:

```text
can_add_visual_reviewed_example_table_contracts = true
can_add_broad_question_like_table_rule = false
can_promote_exercise_workbook_profile = false
```

## Interpretation

The three candidates are valid only as example-table families:

- `b-06288` and `b-06296` are relative-frequency example tables with immediate question and explanation text.
- `b-12383` is a statistics inference example table with immediate question and explanation text.

They do not justify a generic rule that any question-like paragraph followed by a table should be attached.

## Boundary

This audit adds narrow profile-contract evidence only. It does not change G7+ status:

```text
standard_review_pressure_run
```

The remaining low/medium table gaps that stayed stable, and all high-risk table movement, remain outside the contract.
