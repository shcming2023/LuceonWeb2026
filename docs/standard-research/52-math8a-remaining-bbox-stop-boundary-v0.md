# Math 8A Remaining BBox Stop Boundary V0 - 2026-07-01

Purpose:

```text
Classify the remaining Math 8A formula visual packets that still lack source page/bbox after exact and containment Raw assignment locator passes, and test whether Popo content_list can safely recover more locations.
```

## Inputs

Assignment audit:

```text
runtime/backend/pipeline-work/audits/math8a-formula-assignment-bbox-audit-20260701/math_formula_assignment_bbox_audit.json
```

Content list:

```text
runtime/backend/pipeline-work/popo2raw/run-25-pdf-aadfa33fb0485c1a-job-20260610083901-844ae522da/rebuild_input/pdf-aadfa33fb0485c1a_content_list.json
```

Stop-boundary artifact:

```text
runtime/backend/pipeline-work/audits/math8a-remaining-bbox-stop-boundary-20260701/math_remaining_bbox_stop_boundary_audit.json
runtime/backend/pipeline-work/audits/math8a-remaining-bbox-stop-boundary-20260701/math_remaining_bbox_stop_boundary_audit.html
```

## Result

Remaining source page/bbox gaps after exact and containment passes:

| Bucket | Count |
| --- | ---: |
| remaining records | `159` |
| assignment unlocated | `148` |
| ambiguous containment | `10` |
| ambiguous exact | `1` |

Pattern split:

| Pattern | Count |
| --- | ---: |
| option choice | `52` |
| numbered subitem | `33` |
| numbered question | `64` |
| long or mixed formula text | `9` |
| short formula fragment | `1` |

Content-list fallback:

| Status | Count |
| --- | ---: |
| content unlocated | `158` |
| content ambiguous exact | `1` |
| content fallback located | `0` |

## Interpretation

The remaining set is not a simple missing-source-list problem.

The content list does not add safe source-location evidence beyond the Raw assignment locator:

```text
content_list_fallback_located_count = 0
```

The one content-list exact match is still ambiguous across pages, matching the existing assignment ambiguity.

## Stop Boundary

Do not lower thresholds for these records.

Reasons:

- many records are short option choices or formula fragments;
- repeated exercise patterns create cross-page ambiguity;
- a wider content-list scan does not locate additional safe candidates;
- source-location evidence would need stronger page/line context, not looser text matching.

Current safe locator ladder remains:

1. `located_exact`: source bbox evidence only;
2. `located_containment`: wider source-context bbox evidence only;
3. ambiguous and content-list-unlocated records: keep review/pending.

## Gate Impact

No gate is closed by this audit.

- Standard acceptance remains `review`;
- math profile remains blocked/review;
- all formula/table visual outcomes remain open;
- remaining page/bbox gaps stay `159`;
- no Basic Print promotion is allowed.

## Verdict

```text
math_remaining_bbox_stop_boundary_confirmed
```

The next math-profile work should not be another text-threshold locator pass. It should move to either stronger source-lineage/page-context evidence or formula/table visual review/closure rules.
