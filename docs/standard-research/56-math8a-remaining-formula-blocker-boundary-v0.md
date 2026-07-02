# Math 8A Remaining Formula Blocker Boundary V0 - 2026-07-01

Purpose:

```text
Classify the remaining Math 8A formula visual blockers after all currently accepted exact/surface-safe closure rules have run, and define the stop boundary for the current math profile loop.
```

## Artifact

Standard artifact:

```text
runtime/backend/pipeline-work/audits/math-profile-remaining-exact-surface-closure-rerun-20260701/standard-final
```

Remaining blocker audit:

```text
runtime/backend/pipeline-work/audits/math8a-remaining-formula-blocker-audit-20260701/math_remaining_formula_blocker_audit.json
runtime/backend/pipeline-work/audits/math8a-remaining-formula-blocker-audit-20260701/math_remaining_formula_blocker_audit.html
```

## Current Outcome State

| Field | Count |
| --- | ---: |
| total formula/table visual outcomes | `1157` |
| closed accepted_by_rule | `879` |
| open formula outcomes | `278` |
| open table outcomes | `0` |

Open formula decision split:

| Decision | Count |
| --- | ---: |
| `needs_layout_fix` | `119` |
| `needs_page_bbox` | `159` |

## Remaining Blocker Buckets

| Bucket | Count | Meaning |
| --- | ---: | --- |
| `needs_page_bbox_stop_boundary` | `159` | no safe source page/bbox after assignment/content-list fallback; requires stronger page-line locator or manual review |
| `containment_context_review` | `116` | source crop is a wider Raw assignment context containing neighboring subitems; not sufficient for accepted_by_rule closure |
| `digit_spacing_review` | `3` | source text has spaced digits such as `9 0 0` or `0.665 6`; semantic key equality is not enough |

## Stop Boundary

No additional formula outcome should be closed by the current rule set.

Forbidden promotions:

- do not treat `raw_assignment.located_containment` as closure evidence;
- do not close digit-spacing records by semantic key alone;
- do not lower text thresholds for the `159` page/bbox gaps;
- do not promote `math_textbook` while `278` formula outcomes remain open.

## Next Required Math Work

The next math-profile loop is no longer simple closure.

It needs one of:

1. subrow/subitem bbox reconstruction for containment-context crops;
2. stronger page-line source locator for the `159` page/bbox gaps;
3. explicit manual/vision review of digit-spacing and formula rendering risks;
4. a math-heavy visual contract that decides when formula blocks need reconstruction rather than text closure.

## Gate Impact

No gate is closed by this audit.

- Standard acceptance remains `review`;
- quality score remains `86`;
- profile coverage remains `review`;
- review outcomes remain `review`;
- `math_visual_contract` remains `review`;
- `math_textbook` remains blocked/review.

## Verdict

```text
math_formula_closure_current_rule_boundary_reached
```

This is a useful math-profile conclusion: exact and surface-safe source-fidelity closures are exhausted for Math 8A. The remaining work is profile/visual reconstruction policy, not more threshold matching.
