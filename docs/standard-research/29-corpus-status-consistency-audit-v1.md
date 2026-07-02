# Corpus Status Consistency Audit V1 - 2026-07-01

Purpose:

```text
Re-audit Standard Basic Print corpus case/run/golden status after adding GIC, G7+, math, and reconstruction subtrack evidence.
```

This is a manifest consistency audit only. It does not promote candidates, close gates, or infer profile readiness from Standard artifact generation.

## Audit

Command:

```text
python3 backend/scripts/audit_standard_corpus_status_consistency.py --corpus-dir docs/standard-research/corpus --out-dir runtime/backend/pipeline-work/audits/standard-corpus-status-consistency-20260701
```

Artifact:

```text
runtime/backend/pipeline-work/audits/standard-corpus-status-consistency-20260701/corpus_status_consistency_audit.json
```

## Result

| Metric | Count |
| --- | ---: |
| case records | `6` |
| status consistency issues | `0` |
| schema warnings | `0` |

## Current Corpus Status

| Case | Profile | Status | Golden/candidate role |
| --- | --- | --- | --- |
| RE1 | `reading_textbook` | `basic_print_accepted` | accepted golden |
| GF6 | `grammar_workbook` | `basic_print_candidate` | candidate only |
| GF4 | `grammar_workbook` | `basic_print_candidate` | candidate only |
| GIC | `grammar_workbook` | `basic_print_candidate` | non-Grammar-Friends candidate only |
| G7+ | `exercise_workbook` | `standard_review_pressure_run` | review pressure, not candidate |
| Math 8A | `math_textbook` | `math_profile_blocked_review` | blocked/review |

## Fixes Applied

```text
GIC case latest_run_record now points to gic-workbook-relation-rule-v8.
RE1 candidate records now include profile=reading_textbook for machine audit consistency.
```

Decision:

```text
Corpus manifests are currently aligned with the readiness matrix. This does not change any sample status. In particular, GF6/GF4 remain candidates only, GIC remains not promoted because Clean review is open, G7+ remains review pressure, and math remains blocked/review.
```
