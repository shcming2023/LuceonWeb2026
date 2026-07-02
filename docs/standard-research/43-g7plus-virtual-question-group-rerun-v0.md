# G7+ Virtual Question Group Rerun V0 - 2026-07-01

Purpose:

```text
Turn the guarded exercise_workbook grouping simulation into a compiler rule, rerun G7+, and verify relation delta without promoting the sample.
```

## Inputs

Base comparison run:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-stable-rule-rerun-20260701/standard-final
```

Experimental rerun:

```text
runtime/backend/pipeline-work/audits/g7plus-virtual-question-group-rerun-20260701/standard-final
```

Virtual group report:

```text
runtime/backend/pipeline-work/audits/g7plus-virtual-question-group-rerun-20260701/standard-final/workbook_virtual_question_group_report.json
```

Delta audit:

```text
runtime/backend/pipeline-work/audits/g7plus-virtual-question-group-delta-20260701/workbook_relation_delta_audit.json
```

Effects audit:

```text
runtime/backend/pipeline-work/audits/g7plus-virtual-question-group-effects-audit-20260701/workbook_virtual_group_effects_audit.json
```

## Compiler Rule Boundary

The implemented rule is:

```text
guarded_virtual_group_long_paragraph_reset_questions_only_no_table_attachment
```

It is scoped to `exercise_workbook` and:

- starts virtual groups from known workbook section labels, instruction paragraphs, or short colon labels;
- resets on hard section boundaries and long non-instruction paragraphs;
- groups only unparented question blocks;
- does not attach tables, figures, options, or answer blanks.

## Result

Virtual grouping report:

| Metric | Count |
| --- | ---: |
| virtual groups with children | `163` |
| grouped question blocks | `570` |
| instruction starters observed | `674` |
| section-label starters observed | `445` |
| colon-label starters observed | `4` |
| long-paragraph resets | `448` |
| hard-section resets | `127` |

Relation delta compared with the stable table-rule rerun:

| Metric | Base | Current | Delta |
| --- | ---: | ---: | ---: |
| real profile gaps | `551` | `61` | `-490` |
| ungrouped questions | `600` | `30` | `-570` metric |
| real ungrouped-question gaps removed |  |  | `490` |
| added real profile gaps |  |  | `0` |

Remaining relation gaps:

| Kind | Count |
| --- | ---: |
| real ungrouped questions | `25` |
| real orphan table questions | `35` |
| real orphan figure relation candidates | `1` |

## Classifier Boundary Risk

The effects audit shows:

| Grouped base disposition | Count |
| --- | ---: |
| `real_profile_gap` | `490` |
| `explanation_artifact` | `80` |

Those `80` absorbed blocks were previously classified as:

```text
numbered_grammar_explanation_not_exercise_item
```

Manual spot evidence in the audit output shows many are ordinary math exercise questions, so this is likely a profile-classifier boundary problem rather than a virtual-grouping failure. It must still remain documented because the rule changes what the relation audit can see.

## Acceptance Boundary

The experimental rerun remains:

```text
status = review
quality_score = 85
```

The score is not comparable to the main G7+ pressure run score `94`, because this experiment does not replay the source-crop and review-outcome closure chain. Its purpose is relation-rule verification only.

Gate implications:

```text
can_promote_exercise_workbook_profile = false
can_treat_virtual_grouping_as_full_acceptance = false
required_next_action = document_classifier_boundary_then_audit_remaining_61_relation_gaps
```

## Interpretation

The virtual question grouping rule is a major profile-engineering improvement: it removes `490` real ungrouped-question gaps with no added real relation gaps.

It does not make G7+ candidate-ready because `61` real relation gaps remain, table grouping is still unresolved, one figure relation remains open, and visual/source/review closure has not been replayed on this experimental run.
