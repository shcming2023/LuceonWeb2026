# G7+ Contract Family Decision Audit V0 - 2026-07-01

Purpose:

```text
Decide whether the 18 source-context contract-review packets left after G7+ question continuation should become a narrow exercise_workbook compiler rerun, or remain review/profile-boundary evidence.
```

## Inputs

Source-context audit:

```text
runtime/backend/pipeline-work/audits/g7plus-remaining-relation-source-context-audit-20260701/workbook_remaining_relation_source_context_audit.json
```

Contract family decision audit:

```text
runtime/backend/pipeline-work/audits/g7plus-contract-family-decision-audit-20260701/workbook_contract_family_decision_audit.json
```

HTML review packet:

```text
runtime/backend/pipeline-work/audits/g7plus-contract-family-decision-audit-20260701/workbook_contract_family_decision_audit.html
```

Source contact sheet:

```text
runtime/backend/pipeline-work/audits/g7plus-remaining-relation-source-context-audit-20260701/contract_review_contact_sheet.png
```

## Result

| Metric | Count |
| --- | ---: |
| contract-review packets audited | `18` |
| math-heavy profile-boundary packets | `18` |
| generic exercise_workbook rerun candidates | `0` |

Decision counts:

| Decision | Count |
| --- | ---: |
| `contract_candidate_needs_math_visual_group_policy` | `2` |
| `keep_review_multi_table_or_model_unit` | `1` |
| `contract_candidate_needs_math_step_model_policy` | `4` |
| `contract_candidate_needs_data_graph_policy` | `1` |
| `contract_candidate_needs_math_frequency_policy` | `3` |
| `contract_candidate_needs_math_rule_table_policy` | `2` |
| `contract_candidate_needs_probability_example_policy` | `2` |
| `keep_review_figure_table_compound_unit` | `2` |
| `contract_candidate_needs_probability_data_policy` | `1` |

Refined families:

| Family | Count |
| --- | ---: |
| `classification_table_or_number-system_diagram` | `2` |
| `math_heavy_multi_table_model` | `1` |
| `worked_example_step_or_model_table` | `4` |
| `data_table_for_graph_or_association` | `1` |
| `frequency_table_explanation_or_response_table` | `3` |
| `transformation_rule_summary_table` | `2` |
| `probability_example_data_table` | `2` |
| `figure_table_compound_probability_or_data_unit` | `2` |
| `probability_model_data_table` | `1` |

## Decision

```text
generic_exercise_workbook_rerun_recommended = false
```

Reason:

The 18 packets are all math-heavy visual/data/model/table relation cases. They are source-adjacent and important for print usability, but they are not the same problem class as grammar-workbook question grouping, option layout, or ordinary exercise table attachment.

## Acceptance Boundary

Gate implications:

```text
can_promote_exercise_workbook_profile = false
can_close_remaining_relation_gaps = false
can_add_generic_exercise_workbook_table_rule = false
```

This audit is a profile-boundary decision. It does not close any remaining G7+ relation gap and does not change Standard acceptance status.

## Interpretation

The G7+ pressure run has exposed a boundary between:

- `exercise_workbook`: question grouping, answer blanks, options, ordinary workbook tables;
- `math_heavy_workbook` / `math_textbook`: worked examples, model tables, graph/data tables, probability data, frequency tables, transformation rule tables, and figure/table compound explanation units.

The remaining G7+ relation gaps should not be solved by making `exercise_workbook` broader. They should become evidence for a math-heavy profile relation contract, or remain review until that profile exists.

## Next Loop

Shortest safe next loop:

```text
Define a math-heavy workbook/textbook relation contract boundary using G7+ and the existing Math 8A blocked sample, then decide whether this is a subprofile of exercise_workbook or part of math_textbook.
```

Stop condition:

- do not add a generic exercise_workbook table rule for these 18 packets;
- do not close relation gaps without rerun evidence;
- do not treat math-heavy family classification as Basic Print candidate status.
