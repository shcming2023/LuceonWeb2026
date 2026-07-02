# GIC Basic Print Candidate Promotion V0 - 2026-07-01

Purpose:

```text
Record Grammar in Context as a non-Grammar-Friends grammar_workbook Basic Print candidate after Clean review closure policy passes.
```

This does not promote GIC to accepted golden. The later profile decision is recorded in `35-grammar-workbook-profile-ready-v0.md`.

## Evidence

Standard v8:

| Field | Value |
| --- | ---: |
| acceptance | `pass` |
| quality score | `100` |
| workbook profile | `pass` |
| exercise relation contract | `pass` |
| image relation contract | `pass` |
| review outcomes | `377/377` closed |
| open blocking Standard outcomes | `0` |
| PDF page count | `303` |

Clean closure:

| Gate | Closure evidence | Verdict |
| --- | --- | --- |
| `media_review_threshold` | `clean_media_purpose_ledger.json` | `can_close_clean_review_gate` |
| `llm_structure_revert_threshold` | `clean_llm_fallback_ledger.json` | `can_close_clean_review_gate` |

Closure policy:

```text
overall_verdict = clean_review_closure_policy_pass
promotion_eligible = true
```

## Artifacts

Standard:

```text
runtime/backend/pipeline-work/audits/gic-standard-workbook-relation-rule-v8-20260630/standard-final
```

Clean closure:

```text
runtime/backend/pipeline-work/audits/gic-clean-media-purpose-ledger-20260701/clean_media_purpose_ledger.json
runtime/backend/pipeline-work/audits/gic-clean-llm-fallback-ledger-20260701/clean_llm_fallback_ledger.json
runtime/backend/pipeline-work/audits/gic-clean-closure-policy-audit-v3-20260701/clean_review_closure_policy_audit.json
```

Candidate manifest:

```text
docs/standard-research/corpus/golden/candidates/pdf-01ae095f5a0f2dc7.gic-workbook-clean-closure-v3-20260701.candidate.json
```

## Decision

```text
GIC is promoted from standard_gates_pass_clean_review_not_promoted to basic_print_candidate.
```

Reason:

- Standard gates pass;
- Clean review gates are closed by reusable closure ledgers;
- this is the first non-Grammar-Friends grammar workbook candidate.

## Boundary

Do not infer:

- GIC is accepted golden;
- `grammar_workbook` is profile-ready;
- all workbook families are covered;
- Clean `acceptance_report.json` has been mutated to `pass`.

The correct status is:

```text
candidate_only_not_promoted
```
