# G7+ Exercise Relation Delta Audit V0 - 2026-07-01

Purpose:

```text
Compare the main G7+ pressure run with the paired-vocabulary blank-preservation rerun to quantify exercise_workbook relation improvement without treating the rerun as Basic Print acceptance.
```

## Inputs

Base run:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Current comparison run:

```text
runtime/backend/pipeline-work/audits/g7plus-paired-vocab-blank-preservation-rerun-20260701/standard-final
```

Audit command:

```text
python3 backend/scripts/audit_standard_workbook_relation_delta.py --base-standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --current-standard-dir runtime/backend/pipeline-work/audits/g7plus-paired-vocab-blank-preservation-rerun-20260701/standard-final --out-dir runtime/backend/pipeline-work/audits/g7plus-relation-delta-audit-20260701
```

Artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-relation-delta-audit-20260701/workbook_relation_delta_audit.json
runtime/backend/pipeline-work/audits/g7plus-relation-delta-audit-20260701/workbook_relation_delta_audit.html
```

## Result

| Metric | Base | Current | Delta |
| --- | ---: | ---: | ---: |
| real profile gaps | `1811` | `560` | `-1251` |
| ungrouped questions | `1725` | `600` | `-1125` |
| orphan table questions | `84` | `36` | `-48` |
| orphan options | `67` | `20` | `-47` |
| orphan answer blanks | `20` | `13` | `-7` |

Set-level relation gap delta:

| Delta class | Count |
| --- | ---: |
| removed real profile gaps | `1251` |
| added real profile gaps | `0` |
| stable real profile gaps | `560` |
| removed ungrouped-question gaps | `1210` |
| removed orphan-table gaps | `40` |
| removed orphan-figure gaps | `1` |

Removed table-gap baseline buckets:

| Bucket | Count |
| --- | ---: |
| `baseline_policy:manual_review_or_compiler_boundary_gap` | `17` |
| `paired_vocabulary_compiler_rule` | `9` |
| `baseline_policy:explanation_or_step_table_keep_review` | `9` |
| `baseline_policy:question_like_paragraph_table_needs_visual_review` | `3` |
| `baseline_policy:auto_attach_instruction_table_candidate` | `2` |

Removed table-gap baseline risk:

| Risk | Count |
| --- | ---: |
| high | `26` |
| medium | `14` |

## Interpretation

The relation delta is promising, but it is not yet a safe profile contract.

What is encouraging:

- no new real relation gaps were introduced in the comparison run;
- real profile gaps dropped by `1251`;
- ungrouped-question gaps dropped by `1210`;
- `9` removed table gaps are attributable to the paired-vocabulary compiler rule;
- paired-vocabulary blank preservation is already separately closed by `36-g7plus-paired-vocabulary-blank-preservation-v0.md`.

What blocks promotion:

- the comparison run is still `review`, quality score `85`;
- it did not replay the full source-crop/review-outcome closure stack from the main pressure run;
- `560` real profile gaps remain;
- `44` orphan table relation gaps remain stable at the set level;
- `26` removed table gaps came from high-risk baseline buckets, including manual boundary and step/explanation contexts;
- high-risk table movement must be split into explicit profile contracts before compiler promotion.

## Decision

```text
profile_contract_candidate_status = not_ready_high_risk_relation_delta_needs_rule_split
```

This delta audit is useful evidence for the next `exercise_workbook` profile-engineering loop. It is not Basic Print acceptance, not G7+ candidate status, and not an accepted table-attachment rule.

## Next Safe Loop

The next loop should split the relation delta into explicit candidate contracts:

1. paired-vocabulary table attachment/rendering: already narrow and evidence-backed;
2. low/medium-risk instruction or adjacent-question table attachment: candidate contract, needs source/visual spot audit;
3. high-risk manual/explanation/step table movement: keep review until source visual evidence proves no semantic misbinding.

Stop condition:

```text
Do not implement broad table attachment from this delta while high-risk removed table gaps remain mixed with safe paired-vocabulary movement.
```
