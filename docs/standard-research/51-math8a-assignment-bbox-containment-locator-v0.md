# Math 8A Assignment BBox Containment Locator V0 - 2026-07-01

Purpose:

```text
Test whether unique Raw assignment containment matches can be used as wider source-context evidence for Math 8A formula visual packets, while keeping all visual outcomes open.
```

## Boundary

This loop starts from the exact-locator artifact:

```text
runtime/backend/pipeline-work/audits/math-profile-assignment-bbox-exact-rerun-20260701/standard-final
```

It applies only this candidate class:

```text
located_containment
```

A containment match means the normalized Standard packet text is contained in one Raw assignment row, or vice versa. In Math 8A, these are usually Raw assignment bboxes that contain several small formula subitems while Standard has split them into separate review packets.

This rule is source evidence only:

- it may provide a wider source crop for human/rule visual review;
- it does not close a formula visual outcome;
- it does not mark `accepted_by_rule`;
- it does not promote `math_textbook`;
- ambiguous containment remains review-only.

## Artifact

```text
runtime/backend/pipeline-work/audits/math-profile-assignment-bbox-containment-rerun-20260701/standard-final
```

Contact sheet:

```text
runtime/backend/pipeline-work/audits/math8a-formula-assignment-bbox-audit-20260701/sample_crops/containment_contact_sheet.png
```

## Result

| Field | Value |
| --- | ---: |
| containment bboxes applied | `116` |
| skipped records | `0` |
| source crops created | `998` |
| source crop required | `1157` |
| still needs page/bbox | `159` |

Visual review outcomes remain open:

| Outcome state | Count |
| --- | ---: |
| total outcomes | `1157` |
| open outcomes | `1157` |
| closed outcomes | `0` |
| open blocking outcomes | `1157` |
| needs layout fix/source review | `998` |
| needs page/bbox | `159` |

Gate facts:

| Gate | Status |
| --- | --- |
| Standard acceptance | `review` |
| quality score | `86` |
| profile coverage | `review` |
| formula/table integrity | `review` |
| review outcomes | `review` |
| source evidence | `pass` |

## Visual Spot Check

The containment contact sheet shows the expected pattern:

```text
wide Raw assignment crops containing the target formula item plus neighboring subitems.
```

That is sufficient as source-context evidence, but not sufficient as Basic Print visual closure. The wider crop helps review locate the source line; it does not prove Standard layout reconstruction quality.

## Verdict

```text
math_formula_assignment_containment_locator_partial_source_evidence_only
```

The safe source-location ladder is now:

1. `located_exact`: source bbox evidence, no outcome closure;
2. `located_containment`: wider source-context bbox evidence, no outcome closure;
3. `ambiguous_*` and unlocated records: remain review/pending.

Math 8A remains blocked/review because formula/table visual closure and math-heavy profile rules are still undefined.
