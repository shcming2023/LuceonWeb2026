# G7+ Remaining Relation Source Context Audit V0 - 2026-07-01

Purpose:

```text
Create focused source-PDF visual review evidence for the 36 real relation gaps left after question continuation, without closing gates or promoting G7+.
```

## Inputs

Current experimental run:

```text
runtime/backend/pipeline-work/audits/g7plus-question-continuation-rerun-20260701/standard-final
```

Remaining relation gap audit:

```text
runtime/backend/pipeline-work/audits/g7plus-remaining-relation-gap-audit-v2-20260701/workbook_remaining_relation_gap_audit.json
```

Source-context audit:

```text
runtime/backend/pipeline-work/audits/g7plus-remaining-relation-source-context-audit-20260701/workbook_remaining_relation_source_context_audit.json
```

HTML review packet:

```text
runtime/backend/pipeline-work/audits/g7plus-remaining-relation-source-context-audit-20260701/workbook_remaining_relation_source_context_audit.html
```

Source crops:

```text
runtime/backend/pipeline-work/audits/g7plus-remaining-relation-source-context-audit-20260701/source_context_crops/
```

## Result

| Metric | Count |
| --- | ---: |
| remaining relation records | `36` |
| records with source page/bbox | `36` |
| generated crop files | `72` |
| source-context contract-review packets | `18` |
| source-context keep-review packets | `18` |

Source-context decision counts:

| Decision | Count |
| --- | ---: |
| `source_context_packet_ready_for_contract_review` | `18` |
| `source_context_packet_ready_keep_review` | `18` |

Family counts:

| Family | Count |
| --- | ---: |
| `classification_answer_table` | `2` |
| `step_or_method_model_table` | `5` |
| `data_table_for_graph_or_association` | `1` |
| `frequency_table_explanation` | `4` |
| `transformation_rule_table` | `2` |
| `probability_data_table` | `4` |
| `unclassified_table_gap` | `9` |
| `financial_statement_model_table` | `2` |
| `paired_or_multi_sample_tables` | `3` |
| `statistics_data_or_summary_table` | `3` |
| `probability_explanation_figure` | `1` |

## Visual Spot Findings

Spot inspection confirms that the remaining table/figure gaps are not homogeneous workbook table attachments:

- `b-00840` is part of a visual explanation/classification diagram for rational and irrational numbers, not a simple answer table.
- `b-03649` is a model/diagram table embedded in a math explanation page, not a grammar-workbook exercise table.
- `b-13076` is a probability explanation figure adjacent to formulas and explanatory text, not a missing standalone image.

## Acceptance Boundary

The audit policy is:

```text
focused_source_context_review_package_no_gate_closure
```

Gate implications:

```text
can_promote_exercise_workbook_profile = false
can_close_remaining_relation_gaps = false
```

This audit proves that every remaining relation gap now has a focused source-PDF review packet. It does not prove that any family is safe to auto-close, and it does not convert G7+ into a Basic Print candidate.

## Interpretation

The G7+ blocker has moved from missing evidence plumbing to family-level relation/rendering policy:

- the question relation side is closed at relation-audit level;
- table/figure relation gaps are source-reviewable;
- the remaining `18` contract-review packets need narrow family decisions before any compiler/profile rule;
- the remaining `18` keep-review packets should stay manual/source-visual unless later evidence establishes a profile-general rule.

The source crops also suggest that part of the G7+ surface is better treated as a math-heavy workbook/textbook profile boundary, not as a direct extension of `grammar_workbook`.

## Next Loop

Shortest safe next loop:

```text
Review the 18 source-context contract-review packets by family, choose at most one low-risk family for a compiler rerun, and leave diagram/model/probability explanation families in review unless the source visuals support a profile-general contract.
```

Stop condition:

- do not close relation gaps because a source crop exists;
- do not fold math diagram/model tables into generic `exercise_workbook` table attachment;
- do not treat a family rule as profile promotion until a rerun shows no added relation gaps and rendered HTML/PDF remains printable.
