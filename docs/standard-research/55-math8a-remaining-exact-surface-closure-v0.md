# Math 8A Remaining Exact Surface Closure V0 - 2026-07-01

Purpose:

```text
Re-audit the remaining raw_assignment.located_exact formula outcomes after the first safe closure pass, and close only surface-safe exact-assignment rows while keeping digit-spacing and containment evidence in review.
```

## Inputs

Base artifact:

```text
runtime/backend/pipeline-work/audits/math-profile-raw-assignment-safe-closure-rerun-20260701/standard-final
```

Risk audit:

```text
runtime/backend/pipeline-work/audits/math8a-remaining-exact-surface-risk-audit-20260701/math_remaining_exact_surface_risk_audit.json
runtime/backend/pipeline-work/audits/math8a-remaining-exact-surface-risk-audit-20260701/math_remaining_exact_surface_risk_audit.html
```

Closure artifact:

```text
runtime/backend/pipeline-work/audits/math-profile-remaining-exact-surface-closure-rerun-20260701/standard-final
```

Closure report:

```text
runtime/backend/pipeline-work/audits/math-profile-remaining-exact-surface-closure-rerun-20260701/standard-final/math_remaining_exact_surface_safe_closure_report.json
```

## Risk Audit

The audit considered only remaining `raw_assignment.located_exact` formula outcomes.

| Field | Count |
| --- | ---: |
| remaining exact-assignment outcomes audited | `94` |
| closure candidates | `91` |
| kept review | `3` |

Risk split:

| Bucket | Count | Decision |
| --- | ---: | --- |
| `compact_surface_safe` | `77` | closeable |
| `short_option_surface_safe` | `14` | closeable |
| `digit_spacing_review` | `3` | keep review |

Formula audit split before this closure:

| Formula bucket | Count |
| --- | ---: |
| semantic mismatch/manual review | `45` |
| near-equivalent/manual review | `46` |
| deterministic semantic equivalent | `3` |

The `semantic mismatch` and `near-equivalent` labels here were caused by conservative formula-key behavior. The surface audit confirms `91` of them are exact-assignment surface-safe after punctuation/spacing normalization.

## Closure Boundary

Closed only:

- `raw_assignment.located_exact`;
- surface-safe risk buckets;
- generated/reused source crop present;
- source page/bbox present.

Kept open:

- `digit_spacing_review`;
- `raw_assignment.located_containment`;
- page/bbox gaps;
- any record with actual surface difference.

## Result

| Field | Count |
| --- | ---: |
| newly closed | `91` |
| skipped | `3` |
| open blocking before closure | `369` |
| open blocking after closure | `278` |

Post-closure outcome state:

| Outcome state | Count |
| --- | ---: |
| closed accepted_by_rule | `879` |
| open needs_layout_fix | `119` |
| open needs_page_bbox | `159` |
| total open blocking | `278` |

Closed reviewer split:

| Reviewer | Count |
| --- | ---: |
| `system:math_native_raw_content_exact_closure` | `600` |
| `system:math_raw_assignment_exact_safe_closure` | `188` |
| `system:math_remaining_exact_surface_safe_closure` | `91` |

## Remaining Review

Post-closure formula source mismatch audit:

| Bucket | Count |
| --- | ---: |
| semantic mismatch manual review | `114` |
| deterministic semantic equivalent | `3` |
| near-equivalent manual review | `2` |

Plus:

```text
159 formula outcomes still need page/bbox.
```

The remaining `119` source-crop-backed review outcomes are not safe exact-assignment closures. Most are containment-context crops or digit-spacing risk records.

## Gate Impact

No profile promotion:

- Standard acceptance remains `review`;
- quality score remains `86`;
- profile coverage remains `review`;
- review outcomes remain `review`;
- `math_visual_contract` remains `review`;
- open formula visual outcomes remain `278`;
- open table visual outcomes remain `0`.

## Verdict

```text
math_remaining_exact_surface_closure_partial_pass_math_still_review
```

This closes the remaining surface-safe exact-assignment subset. Math 8A remains blocked/review because containment-context review and page/bbox gaps remain.
