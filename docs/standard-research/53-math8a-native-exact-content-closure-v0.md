# Math 8A Native Exact Content Closure V0 - 2026-07-01

Purpose:

```text
Close only Math 8A formula/table visual outcomes whose Standard text exactly matches native Raw content evidence and has generated source PDF crop evidence, while keeping Raw-assignment and containment evidence as review-only.
```

## Boundary

Input artifact:

```text
runtime/backend/pipeline-work/audits/math-profile-assignment-bbox-containment-rerun-20260701/standard-final
```

Closure artifact:

```text
runtime/backend/pipeline-work/audits/math-profile-native-exact-closure-rerun-20260701/standard-final
```

Closure report:

```text
runtime/backend/pipeline-work/audits/math-profile-native-exact-closure-rerun-20260701/standard-final/math_native_exact_content_closure_report.json
```

## Closure Rule

An outcome is closable only when all are true:

- `table_formula_outcome_audit.json` bucket is `deterministic_closure_candidate_exact_match`;
- packet has no `source_match_rule`;
- `source_raw_type` is one of `text`, `equation`, or `table`;
- source page/bbox exists;
- source crop status is `created` or `reused`;
- closure remains `accepted_by_rule`, not human visual final approval.

Explicitly not closed:

- `raw_assignment.located_exact` compact matches;
- `raw_assignment.located_containment` wider source-context matches;
- ambiguous source-location records;
- records still missing page/bbox.

## Result

| Field | Value |
| --- | ---: |
| native exact closure candidates | `600` |
| newly closed | `600` |
| skipped exact bucket | `0` |
| open blocking before closure | `1157` |
| open blocking after closure | `557` |

Closed by packet type:

| Packet type | Count |
| --- | ---: |
| formula visual review | `596` |
| table visual review | `4` |

Closed source raw types:

| Source raw type | Count |
| --- | ---: |
| text | `569` |
| equation | `27` |
| table | `4` |

## Post-Closure Outcome State

| Outcome state | Count |
| --- | ---: |
| closed accepted_by_rule | `600` |
| open needs_layout_fix | `398` |
| open needs_page_bbox | `159` |
| total open blocking | `557` |

Post-closure profile facts:

| Field | Value |
| --- | --- |
| Standard acceptance | `review` |
| quality score | `86` |
| profile | `math_textbook` |
| workbook profile status | `review` |
| open formula visual outcomes | `557` |
| open table visual outcomes | `0` |

## Remaining Review Split

After closure:

- `191` formula outcomes are deterministic semantic-equivalent by text key but have `raw_assignment.located_exact` source-location evidence, which is not currently an allowed closure rule;
- `48` formula outcomes are near-equivalent and need manual review;
- `159` formula outcomes are semantic mismatch/manual review or still need page/bbox depending on the audit layer;
- `159` source page/bbox gaps remain after the stop-boundary audit.

The `raw_assignment` exact and containment locators remain source evidence only. They are not promoted to accepted closure rules in this loop.

## Verdict

```text
math_native_exact_content_closure_partial_pass_math_still_review
```

This closes the safe native Raw content exact-match subset and removes all table visual review blockers. It does not close the math profile because `557` formula visual outcomes remain open and blocking.
