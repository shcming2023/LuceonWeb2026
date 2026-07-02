# G7+ Table Attachment Spot Audit V0 - 2026-07-01

Purpose:

```text
Source-context spot audit the 2 non-paired low/medium table-attachment candidates from the G7+ contract split, without promoting broad table attachment.
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

Source PDF:

```text
runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf
```

Audit command:

```text
python3 backend/scripts/audit_standard_workbook_table_attachment_spot.py --base-standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --contract-audit runtime/backend/pipeline-work/audits/g7plus-table-attachment-contract-audit-20260701/workbook_table_attachment_contract_audit.json --source-pdf runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf --out-dir runtime/backend/pipeline-work/audits/g7plus-table-attachment-spot-audit-20260701
```

Artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-spot-audit-20260701/workbook_table_attachment_spot_audit.json
runtime/backend/pipeline-work/audits/g7plus-table-attachment-spot-audit-20260701/workbook_table_attachment_spot_audit.html
runtime/backend/pipeline-work/audits/g7plus-table-attachment-spot-audit-20260701/source_context_crops/
```

## Result

| Block | Contract family | Decision |
| --- | --- | --- |
| `b-04401` | `example_step_data_table_keep_with_explanation` | accepted for narrow contract by source context |
| `b-08745` | `single_table_vocabulary_review` | accepted for narrow contract by source context |

Summary:

| Metric | Count |
| --- | ---: |
| candidates audited | `2` |
| contract-ready by source context | `2` |
| needs visual review | `0` |

Gate implications:

```text
can_add_non_paired_spot_contracts = true
can_add_broad_table_attachment_rule = false
can_promote_exercise_workbook_profile = false
```

## Interpretation

The two candidates are not the same rule:

- `b-04401` is an example data table embedded in a teaching flow between a Look for Relationships prompt and STEP explanations.
- `b-08745` is a single-table Vocabulary Review matching table under an explicit instruction and before Use Vocabulary in Writing.

Both can be recorded as narrow source-context contract families. Neither supports a broad instruction-table attachment rule.

## Boundary

This is still a G7+ sample-level spot audit. Before compiler promotion beyond these two narrow families, the rule should either:

- stay limited to these exact source-context families and rerun G7+ full acceptance with source evidence; or
- be tested on another `exercise_workbook` pressure sample.

Do not use this audit to promote G7+, `exercise_workbook`, or generic table attachment.
