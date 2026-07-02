# G7+ Question Continuation Rerun V0 - 2026-07-01

Purpose:

```text
Close the remaining real ungrouped-question gaps after virtual question grouping by adding a narrow numbered-question continuation rule, without touching table or figure gaps.
```

## Inputs

Base comparison run:

```text
runtime/backend/pipeline-work/audits/g7plus-virtual-question-group-rerun-20260701/standard-final
```

Experimental rerun:

```text
runtime/backend/pipeline-work/audits/g7plus-question-continuation-rerun-20260701/standard-final
```

Continuation report:

```text
runtime/backend/pipeline-work/audits/g7plus-question-continuation-rerun-20260701/standard-final/workbook_question_continuation_report.json
```

Delta audit:

```text
runtime/backend/pipeline-work/audits/g7plus-question-continuation-delta-20260701/workbook_relation_delta_audit.json
```

Remaining gap audit:

```text
runtime/backend/pipeline-work/audits/g7plus-remaining-relation-gap-audit-v2-20260701/workbook_remaining_relation_gap_audit.json
```

## Compiler Rule Boundary

The implemented rule is:

```text
numbered_question_continuation_same_heading_with_short_or_image_interruptions
```

It is scoped to `exercise_workbook` and:

- groups only numbered unparented question blocks;
- requires the same heading path as a recent numbered question anchor;
- allows short answer-option fragments or captioned figures between questions;
- keeps number jumps small;
- does not group tables, figures, options, answer blanks, or front matter.

A separate classifier rule downgrades the no-heading `TOPICS` topic list artifact so it no longer counts as a real question gap in the relation audit.

## Result

Continuation report:

| Metric | Count |
| --- | ---: |
| continuation groups | `7` |
| grouped question blocks | `29` |

Trigger counts:

| Trigger | Count |
| --- | ---: |
| `three_act_question_continuation` | `10` |
| `image_interrupted_question_run` | `6` |
| `question_run_continuation` | `5` |
| `short_option_interrupted_question_run` | `1` |

Relation delta compared with the virtual-group rerun:

| Metric | Base | Current | Delta |
| --- | ---: | ---: | ---: |
| real profile gaps | `61` | `36` | `-25` |
| real ungrouped-question gaps | `25` | `0` | `-25` |
| added real profile gaps |  |  | `0` |

Remaining real relation gaps:

| Kind | Count |
| --- | ---: |
| real orphan table questions | `35` |
| real orphan figure relation candidates | `1` |

The profile metrics still show one raw `ungrouped_questions` count because the front matter topic list remains a question-shaped block structurally. The relation audit now classifies it as `front_matter_artifact`, so it is not a real profile gap.

## Acceptance Boundary

The experimental rerun remains:

```text
status = review
quality_score = 85
```

This is relation-rule evidence only. It does not replay source-crop and review-outcome closure, and it does not make G7+ a Basic Print candidate.

Gate implications:

```text
can_promote_exercise_workbook_profile = false
can_treat_current_run_as_basic_print_candidate = false
```

## Interpretation

The question side of the G7+ relation blocker is now closed at the relation-audit level: real ungrouped-question gaps are `0`.

The remaining exercise_workbook blocker has shifted to table/figure relation semantics: `35` orphan table questions and `1` figure relation candidate remain, with `18` table records classified as candidate families and `18` table/figure records kept for review.
