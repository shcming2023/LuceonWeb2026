# Math 8A Raw Assignment Exact Safe Closure V0 - 2026-07-01

Purpose:

```text
Decide whether raw_assignment.located_exact formula semantic-equivalent outcomes may be closed by rule, without accepting digit-spacing or broader raw-assignment/containment evidence.
```

## Inputs

Base artifact:

```text
runtime/backend/pipeline-work/audits/math-profile-native-exact-closure-rerun-20260701/standard-final
```

Risk audit:

```text
runtime/backend/pipeline-work/audits/math8a-raw-assignment-exact-semantic-closure-audit-20260701/math_raw_assignment_exact_closure_risk_audit.json
runtime/backend/pipeline-work/audits/math8a-raw-assignment-exact-semantic-closure-audit-20260701/math_raw_assignment_exact_closure_risk_audit.html
runtime/backend/pipeline-work/audits/math8a-raw-assignment-exact-semantic-closure-audit-20260701/raw_assignment_exact_semantic_contact_sheet.png
```

Closure artifact:

```text
runtime/backend/pipeline-work/audits/math-profile-raw-assignment-safe-closure-rerun-20260701/standard-final
```

Closure report:

```text
runtime/backend/pipeline-work/audits/math-profile-raw-assignment-safe-closure-rerun-20260701/standard-final/math_raw_assignment_exact_safe_closure_report.json
```

## Risk Audit

The candidate set was:

```text
raw_assignment.located_exact + deterministic_formula_semantic_equivalent
```

Risk split:

| Bucket | Count | Decision |
| --- | ---: | --- |
| `compact_surface_safe` | `131` | closeable |
| `short_option_surface_safe` | `57` | closeable |
| `digit_spacing_review` | `3` | keep review |

Total:

| Field | Count |
| --- | ---: |
| audited semantic-equivalent raw-assignment exact items | `191` |
| closeable after risk split | `188` |
| kept review | `3` |

The `digit_spacing_review` cases are intentionally not closed because the source text contains spaced digits such as `9 0 0` or `0.665 6`, which can hide OCR/tokenization defects even when the semantic key is equal.

## Closure Rule

Close only when all are true:

- source rule is `raw_assignment.located_exact`;
- formula semantic key is deterministic equivalent;
- risk bucket is one of:
  - `compact_surface_safe`;
  - `short_option_surface_safe`;
  - `punctuation_spacing_safe`;
- source page/bbox exists;
- source crop is generated or reused;
- digit-spacing and surface-diff review buckets are excluded.

The rule does not apply to:

- `raw_assignment.located_containment`;
- ambiguous source-location records;
- missing page/bbox records;
- digit-spacing review records;
- near-equivalent formula records.

## Result

| Field | Count |
| --- | ---: |
| newly closed | `188` |
| skipped | `3` |
| open blocking before closure | `557` |
| open blocking after closure | `369` |

Post-closure outcome state:

| Outcome state | Count |
| --- | ---: |
| closed accepted_by_rule | `788` |
| open needs_layout_fix | `210` |
| open needs_page_bbox | `159` |
| total open blocking | `369` |

Closed reviewer split:

| Reviewer | Count |
| --- | ---: |
| `system:math_native_raw_content_exact_closure` | `600` |
| `system:math_raw_assignment_exact_safe_closure` | `188` |

## Remaining Formula Review

Post-closure formula source mismatch audit:

| Bucket | Count |
| --- | ---: |
| deterministic formula semantic equivalent | `3` |
| near-equivalent manual review | `48` |
| semantic mismatch manual review | `159` |

Plus:

```text
159 formula outcomes still need page/bbox.
```

## Gate Impact

No profile promotion:

- Standard acceptance remains `review`;
- quality score remains `86`;
- profile coverage remains `review`;
- review outcomes remain `review`;
- `math_visual_contract` remains `review`;
- open formula visual outcomes remain `369`;
- open table visual outcomes are `0`.

## Verdict

```text
math_raw_assignment_exact_safe_closure_partial_pass_math_still_review
```

This is a narrow, evidence-backed closure rule. It reduces formula visual blockers but does not make `math_textbook` profile-ready.
