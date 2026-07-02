# Math 8A Source Evidence Plumbing V0 - 2026-07-01

Purpose:

```text
Use the existing local Math 8A source PDF to test whether the current math_textbook blocker is missing source evidence plumbing, missing bbox evidence, or math-profile contract readiness.
```

## Inputs

Math 8A run:

```text
runtime/backend/pipeline-work/audits/math-profile-review-v0-rerun-20260630/standard-final
```

Local source PDF evidence:

```text
runtime/backend/pipeline-work/popo2raw/run-25-pdf-aadfa33fb0485c1a-job-20260610083901-844ae522da/rebuild_input/pdf-aadfa33fb0485c1a_origin.pdf
```

Observed source PDF:

| Field | Value |
| --- | --- |
| size | `1,658,503` bytes |
| sha256 | `b1de38dbdc1a53f4ca223775d48e2bfacec91935f12d756c045adb689ce894cc` |

The same local source PDF hash is present in the checked run-23/run-24/run-25 Popo2Raw rebuild inputs.

## Source Crop Run

Command:

```text
python3 backend/scripts/generate_standard_visual_source_crops_fast.py \
  --standard-dir runtime/backend/pipeline-work/audits/math-profile-review-v0-rerun-20260630/standard-final \
  --source-pdf runtime/backend/pipeline-work/popo2raw/run-25-pdf-aadfa33fb0485c1a-job-20260610083901-844ae522da/rebuild_input/pdf-aadfa33fb0485c1a_origin.pdf
```

Result:

| Metric | Count |
| --- | ---: |
| visual review outcomes | `1157` |
| formula visual review outcomes | `1153` |
| table visual review outcomes | `4` |
| source crops created | `600` |
| still needs page/bbox | `557` |
| rendered source pages | `67` |

Artifact:

```text
runtime/backend/pipeline-work/audits/math-profile-review-v0-rerun-20260630/standard-final/visual_source_crop_audit.json
```

Contact sheet:

```text
runtime/backend/pipeline-work/audits/math-profile-review-v0-rerun-20260630/standard-final/math_visual_source_crop_contact_sheet.png
```

## Raw Bbox Fallback Audit

Command:

```text
python3 backend/scripts/backfill_standard_visual_bbox_from_raw.py \
  --standard-dir runtime/backend/pipeline-work/audits/math-profile-review-v0-rerun-20260630/standard-final
```

Result:

| Status | Count |
| --- | ---: |
| `formula_visual_review:unlocated` | `557` |

No Raw fallback bbox candidates were found for the remaining formula blockers.

## Current Outcome State

After source crop generation:

| Outcome decision | Count |
| --- | ---: |
| `needs_layout_fix` | `600` |
| `needs_page_bbox` | `557` |

All `1157` outcomes remain open/blocking. The source crops are review evidence only and do not close formula/table outcomes.

## Interpretation

This loop narrows the Math 8A blocker:

- source PDF is locally available even though the Standard run manifest has an empty `source_pdf`;
- `600/1157` visual outcomes now have source crops for manual/layout review;
- `557/1157` still lack page/bbox evidence and cannot be located by the current Raw fallback;
- selected profile remains `reading_textbook`, so `profile_coverage=pass` is not meaningful for math readiness;
- Math 8A remains `math_profile_blocked_review`.

## Connection To G7+

G7+ exposed math-heavy table/figure/model relation families inside an `exercise_workbook` pressure run. Math 8A exposes the same broader boundary from the formula-heavy side: formula/table evidence and math-specific profile selection are not solved by `reading_textbook` or generic `exercise_workbook` gates.

## Next Loop

Shortest safe next loop:

```text
Define a math-heavy profile contract boundary that covers Math 8A formula/table visual evidence and G7+ math-heavy table/figure relation families, before attempting any profile promotion or compiler rerun.
```

Stop condition:

- do not treat source crop generation as visual acceptance;
- do not close `557` page/bbox gaps without new locator evidence;
- do not treat the current Math 8A `reading_textbook` selected profile as a valid math_textbook pass.
