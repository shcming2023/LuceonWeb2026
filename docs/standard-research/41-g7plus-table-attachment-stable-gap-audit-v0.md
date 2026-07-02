# G7+ Table Attachment Stable Gap Audit V0 - 2026-07-01

Purpose:

```text
Review the 15 low/medium orphan-table gaps that stayed stable after the paired-vocabulary rerun, without closing them by inspection or authorizing a broad table-attachment rule.
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
python3 backend/scripts/audit_standard_workbook_table_attachment_stable_gaps.py --base-standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --contract-audit runtime/backend/pipeline-work/audits/g7plus-table-attachment-contract-audit-20260701/workbook_table_attachment_contract_audit.json --source-pdf runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf --out-dir runtime/backend/pipeline-work/audits/g7plus-table-attachment-stable-gap-audit-20260701
```

Artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-stable-gap-audit-20260701/workbook_table_attachment_stable_gap_audit.json
runtime/backend/pipeline-work/audits/g7plus-table-attachment-stable-gap-audit-20260701/workbook_table_attachment_stable_gap_audit.html
runtime/backend/pipeline-work/audits/g7plus-table-attachment-stable-gap-audit-20260701/source_context_crops/
```

## Result

Summary:

| Metric | Count |
| --- | ---: |
| stable gaps audited | `15` |
| narrow contract candidates requiring compiler rerun | `9` |
| keep review | `6` |

Decision counts:

| Decision | Count |
| --- | ---: |
| `contract_candidate_requires_rule_rerun` | `9` |
| `keep_review_needs_source_visual_contract` | `3` |
| `keep_review_no_contract_signal` | `2` |
| `keep_review_requires_multi_table_grouping` | `1` |

Contract-family counts:

| Family | Count |
| --- | ---: |
| `example_pattern_or_rate_table` | `2` |
| `exercise_scatter_plot_data_table` | `2` |
| `example_statistics_summary_table` | `2` |
| `unclassified_question_like_table` | `3` |
| `unclassified_stable_table_gap` | `2` |
| `example_bar_diagram_table_model` | `1` |
| `single_table_vocabulary_review` | `1` |
| `example_frequency_table_explanation` | `1` |
| `paired_or_adjacent_sample_tables` | `1` |

Gate implications:

```text
can_close_stable_table_gaps = false
can_add_contract_without_compiler_rerun = false
can_add_broad_table_attachment_rule = false
can_promote_exercise_workbook_profile = false
```

## Interpretation

These 15 records are not equivalent to the earlier removed table gaps. They remained `orphan_table_question` real profile gaps after the comparison run, even though their visual outcomes are already `accepted_by_rule`.

The useful signal is narrower:

- `9` records look like candidate rule families, but they require an explicit compiler/profile rule plus a rerun before any gate closure.
- `6` records remain review because they are unclassified, require a source visual contract, or involve adjacent multi-table grouping risk.
- `accepted_by_rule` for the table visual outcome does not close the workbook relation gap.

## Boundary

This audit is a rule-design input only. It does not change G7+ status:

```text
standard_review_pressure_run
```

The next safe step is to encode only narrow candidate rules, rerun G7+, and compare relation deltas. If a rule introduces new gaps or hides multi-table/question grouping errors, stop at review rather than forcing pass.
