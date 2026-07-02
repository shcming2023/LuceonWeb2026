# Math 8A Assignment BBox Exact Locator V0 - 2026-07-01

Purpose:

```text
Use Raw block assignment text/page/bbox evidence to recover high-confidence source locations for Math 8A formula visual review packets that still lacked page/bbox, without closing any visual outcomes or promoting math_textbook.
```

## Inputs

Standard artifact before this loop:

```text
runtime/backend/pipeline-work/audits/math-profile-selector-v1-rerun-20260701/standard-final
```

Raw assignment evidence:

```text
runtime/backend/pipeline-work/raw2clean/run-42-pdf-aadfa33fb0485c1a-job-20260610083901-844ae522da/raw_input/raw_block_assignments.jsonl
```

Audit artifact:

```text
runtime/backend/pipeline-work/audits/math8a-formula-assignment-bbox-audit-20260701/math_formula_assignment_bbox_audit.json
runtime/backend/pipeline-work/audits/math8a-formula-assignment-bbox-audit-20260701/math_formula_assignment_bbox_audit.html
runtime/backend/pipeline-work/audits/math8a-formula-assignment-bbox-audit-20260701/sample_crops/sample_contact_sheet.png
```

Applied Standard artifact:

```text
runtime/backend/pipeline-work/audits/math-profile-assignment-bbox-exact-rerun-20260701/standard-final
```

## Audit Result

The audit considered the `557` formula visual packets that still lacked source page/bbox after local source-PDF crop generation.

| Bucket | Count |
| --- | ---: |
| missing formula packets audited | `557` |
| Raw assignment rows loaded | `1641` |
| located exact | `282` |
| located containment | `116` |
| ambiguous exact | `1` |
| ambiguous containment | `10` |
| unlocated no assignment match | `148` |

## Apply Boundary

Only `located_exact` records were applied.

| Field | Value |
| --- | ---: |
| applied source bboxes | `282` |
| skipped records | `0` |
| applied statuses | `located_exact` only |

Policy:

```text
apply_high_confidence_source_location_only_no_outcome_closure
```

The `located_containment`, ambiguous, and unlocated buckets remain review inputs. They are not accepted by rule.

## Post-Apply Source Crops

After applying exact source bboxes and generating source crops:

| Status | Count |
| --- | ---: |
| source crops created | `882` |
| source crop required | `1157` |
| still needs page/bbox | `275` |
| rendered source pages | `64` |

Visual review outcomes after the apply step:

| Outcome state | Count |
| --- | ---: |
| total outcomes | `1157` |
| open outcomes | `1157` |
| open blocking outcomes | `1157` |
| closed outcomes | `0` |
| needs layout fix | `882` |
| needs page/bbox | `275` |
| source evidence ready | `882` |
| source evidence not ready | `275` |

## Gate Interpretation

This closes neither the math profile contract nor the formula/table visual review outcomes.

Current gate facts:

- Standard acceptance remains `review`;
- quality score remains `86`;
- profile coverage remains `review`;
- review outcomes remain `review`;
- `math_visual_contract` remains `review`;
- all `1157` formula/table outcomes remain open and blocking.

The only validated progress is source-location evidence:

```text
600 -> 882 source-crop-ready formula/table visual packets
557 -> 275 packets still needing page/bbox
```

## Verdict

```text
math_formula_assignment_exact_locator_partial_source_evidence_only
```

This is useful evidence plumbing for the math profile track. It is not a Basic Print pass, not a math_textbook promotion, and not an authorization to close formula outcomes by text match alone.
