# G7+ Table Attachment Stable Rule Rerun V0 - 2026-07-01

Purpose:

```text
Turn the 9 stable-gap table-attachment candidates into narrow compiler rules, rerun G7+, and verify relation delta without promoting exercise_workbook.
```

## Inputs

Base comparison run:

```text
runtime/backend/pipeline-work/audits/g7plus-paired-vocab-blank-preservation-rerun-20260701/standard-final
```

Experimental rerun:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-stable-rule-rerun-20260701/standard-final
```

Delta audit:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-stable-rule-delta-20260701/workbook_relation_delta_audit.json
```

Compiler output:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-stable-rule-rerun-20260701/standard-final/workbook_table_attachment_report.json
```

## Compiler Rule Boundary

The implemented rule is generic but narrow:

```text
narrow_source_context_families_no_material_id_or_page_rules
```

It does not use filename, material id, page number, or block id. It attaches only orphan `exercise_workbook` table questions that match source-context families discovered by the stable-gap audit.

The first rerun overmatched one high-risk table (`b-12491`) in the statistics family. The rule was tightened so the mean/MAD summary family must be triggered by an explicit preceding explanation/question sentence, not by a short title followed by a table.

## Result

Table attachment report:

| Metric | Count |
| --- | ---: |
| attached table groups | `9` |
| attached table blocks | `9` |

Family counts:

| Family | Count |
| --- | ---: |
| `example_pattern_or_rate_table` | `2` |
| `exercise_scatter_plot_data_table` | `2` |
| `example_statistics_summary_table` | `2` |
| `example_bar_diagram_table_model` | `1` |
| `single_table_vocabulary_review` | `1` |
| `example_frequency_table_explanation` | `1` |

Relation delta compared with the paired-vocabulary blank-preservation rerun:

| Metric | Base | Current | Delta |
| --- | ---: | ---: | ---: |
| real profile gaps | `560` | `551` | `-9` |
| orphan table questions | `36` | `27` | `-9` |
| ungrouped questions | `600` | `600` | `0` |
| added real profile gaps |  |  | `0` |

The 9 attached tables are:

```text
b-01520, b-03760, b-04101, b-05602, b-06159, b-06413, b-06418, b-12474, b-12493
```

## Acceptance Boundary

The experimental rerun remains:

```text
status = review
quality_score = 85
```

This score is not comparable to the main G7+ pressure run score `94`, because the experiment rerun does not replay the later source-crop and review-outcome closure chain. Its purpose is relation-rule verification only.

Gate implications:

```text
can_promote_exercise_workbook_profile = false
can_treat_current_run_as_basic_print_candidate = false
required_next_action = turn_relation_delta_into_profile_contract_then_rerun_full_acceptance_with_source_evidence
```

## Interpretation

The stable-gap rule experiment is successful for a narrow subtrack: it closes 9 table relation gaps with no new relation gaps after the high-risk overmatch was removed.

It does not make G7+ candidate-ready because `551` real relation gaps remain, including `515` ungrouped questions, `35` orphan table questions, and `1` orphan figure relation candidate in the relation audit. The next profile-engineering task is still broader exercise grouping/state-machine logic, not more table-only closure.
