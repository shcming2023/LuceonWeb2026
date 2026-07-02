# G7+ Table Attachment Contract Audit V0 - 2026-07-01

Purpose:

```text
Split the G7+ table-attachment relation delta into explicit profile-contract buckets without promoting exercise_workbook or adding a broad table-attachment rule.
```

## Inputs

Base run:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Comparison run:

```text
runtime/backend/pipeline-work/audits/g7plus-paired-vocab-blank-preservation-rerun-20260701/standard-final
```

Relation delta:

```text
runtime/backend/pipeline-work/audits/g7plus-relation-delta-audit-20260701/workbook_relation_delta_audit.json
```

Audit command:

```text
python3 backend/scripts/audit_standard_workbook_table_attachment_contract.py --base-standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --current-standard-dir runtime/backend/pipeline-work/audits/g7plus-paired-vocab-blank-preservation-rerun-20260701/standard-final --relation-delta runtime/backend/pipeline-work/audits/g7plus-relation-delta-audit-20260701/workbook_relation_delta_audit.json --out-dir runtime/backend/pipeline-work/audits/g7plus-table-attachment-contract-audit-20260701
```

Artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-contract-audit-20260701/workbook_table_attachment_contract_audit.json
runtime/backend/pipeline-work/audits/g7plus-table-attachment-contract-audit-20260701/workbook_table_attachment_contract_audit.html
```

## Result

| Contract status | Count | Decision |
| --- | ---: | --- |
| `contract_ready_paired_vocabulary_only` | `9` | narrow contract-ready, already backed by source-confirmed paired-vocabulary evidence and blank preservation |
| `candidate_needs_source_visual_spot_audit` | `2` | candidate only; needs source visual spot audit before any contract |
| `candidate_requires_visual_review_before_contract` | `3` | candidate only; baseline policy already says visual review is required |
| `not_proven_stable_gap` | `15` | not proven; remains a real relation gap in the comparison run |
| `excluded_high_risk_review` | `55` | review only; must not be promoted by generic table attachment |

Policy bucket counts:

| Policy bucket | Count |
| --- | ---: |
| `auto_attach_instruction_table_candidate` | `8` |
| `explanation_or_step_table_keep_review` | `17` |
| `question_like_paragraph_table_needs_visual_review` | `12` |
| `manual_review_or_compiler_boundary_gap` | `38` |
| `paired_vocabulary_table_needs_layout_rule` | `8` |
| `auto_attach_adjacent_question_candidate` | `1` |

Risk counts:

| Risk | Count |
| --- | ---: |
| low | `1` |
| medium | `28` |
| high | `55` |

Comparison-run delta:

| Delta | Count |
| --- | ---: |
| stable in current run | `44` |
| removed from current run | `40` |

## Decision

```text
can_add_paired_vocabulary_contract = true
can_add_broad_table_attachment_rule = false
can_promote_exercise_workbook_profile = false
```

Only the paired-vocabulary subset is currently contract-ready. It is narrow, source-confirmed, and has a separate blank-preservation closure. The non-paired low/medium movement is not ready: `2` records require source visual spot audit, `3` require visual review before contract, and `15` low/medium records remain stable gaps.

## Boundary

Do not implement a broad table-attachment rule from this evidence.

The next safe loop is:

```text
Run source visual spot audit for the 2 non-paired low/medium records that disappeared in the comparison run, and keep the 3 question-like/visual-review records separate.
```

If visual spot audit fails or is ambiguous, keep those records review-only and do not expand the compiler contract.
