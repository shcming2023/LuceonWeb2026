# Math 8A Profile Selector V1 Rerun - 2026-07-01

Purpose:

```text
Verify that Standard can select a real math_textbook profile for Math 8A without lowering gates or treating the sample as passed.
```

## Code Boundary

Implemented minimal profile support:

- `math_textbook` added to Standard profile choices;
- formula-dense auto profile detection added after workbook/exercise heuristics;
- `math_textbook` profile coverage now returns `review` unless math visual outcomes are closed;
- `workbook_profile_report.json` now includes a strict `math_visual_contract`.

This does not add formula/table closure rules and does not promote Math 8A.

## Rerun

Artifact:

```text
runtime/backend/pipeline-work/audits/math-profile-selector-v1-rerun-20260701/standard-final
```

## Result

| Field | Value |
| --- | --- |
| selected profile | `math_textbook` |
| acceptance status | `review` |
| quality score | `86` |
| profile coverage | `review` |
| source evidence | `pass` |
| review outcomes | `review` |
| PDF render | `pass` |
| PDF pages | `64` |

Visual outcomes:

| Outcome | Count |
| --- | ---: |
| formula visual review | `1153` |
| table visual review | `4` |
| open blocking outcomes | `1157` |
| closed outcomes | `0` |

Source crop evidence after rerun:

| Status | Count |
| --- | ---: |
| source crops created | `600` |
| needs page/bbox | `557` |
| Raw fallback located | `0` |

## Gate Interpretation

The old blocker is closed:

```text
selected_profile_is_reading_textbook_not_math_textbook
```

The current blockers are now more precise:

- `math_profile_contract_not_pass`;
- `1157` formula/table visual outcomes open;
- `557` formula outcomes still need page/bbox;
- no Raw fallback candidates for the missing bbox set;
- math table/figure relation contracts remain undefined.

## Verdict

```text
math_profile_selector_closed_but_math_textbook_still_review_blocked
```

This is progress from profile-selection plumbing to true math profile validation. It is not a Basic Print candidate.
