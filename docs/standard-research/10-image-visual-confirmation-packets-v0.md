# Workbook Image Visual Confirmation Packets V0 - 2026-06-29

## Decision

For workbook Standard output, source-PDF visual confirmation must not sample all workbook images uniformly.

V0 selects only content-bearing or uncertain figures:

```text
included:
  exercise_key_figure
  explanation_key_figure
  needs_dimension_review

excluded:
  helper_icon
  decorative
```

Helper icons are handled by compact/nearby rendering rules first. They are not part of the source visual confirmation queue unless later evidence shows they carry exercise meaning.

## Output Contract

Implemented in `backend/scripts/standard_from_clean.py`:

- `image_visual_confirmation_packets.json`
- `image_visual_confirmation.html`
- `image_visual_confirmation` acceptance gate
- `image_visual_confirmation_summary` in `layout_report.json`
- manifest outputs for both confirmation artifacts

Service publishing support was added in `backend/app/services/clean_to_standard.py`.

## Packet Semantics

Each selected packet records:

- image path and relation category;
- neighboring block context;
- source PDF availability;
- source page index/page number;
- source bbox when available from the Popo content list;
- source OCR/content snippet;
- `crop_status`.
- `source_crop_summary`.

Crop status values:

```text
ready_for_source_crop:
  source PDF is available and page/bbox evidence exists.

needs_page_bbox:
  source PDF is available, but page/bbox evidence is missing.

source_pdf_missing:
  key figure exists, but source PDF was not supplied.
```

By default, Standard generation does not render source PDF crops. It records `source_crop_generation: skipped` so the main Standard package stays fast and publishable.

Source crops are generated only as an optional review artifact:

```bash
python3 backend/scripts/generate_standard_source_crops.py \
  --standard-dir <standard-final>
```

The generated crops are review aids; they do not automatically promote a figure to Basic Print acceptance.

## GF6 Rerun Evidence

Main Standard output:

- `runtime/backend/pipeline-work/audits/gf6-visual-confirmation-v0-fast-rerun-20260629/standard-final/`

Result:

```text
status: review
quality_score: 87
profile: grammar_workbook
pdf_page_count: 144
visible_artifact_count: 0
image_refs: 213
image_relation_count: 213
image_relation_source_visual_check_count: 170
image_visual_confirmation_packet_count: 170
image_visual_confirmation_ready_crop_count: 170
image_visual_confirmation_source_crop_count: 170
source_crop_generation: generated
```

Image relation split:

```text
exercise_key_figure: 162
explanation_key_figure: 8
helper_icon: 43
```

Confirmation packet split:

```text
included:
  exercise_key_figure: 162
  explanation_key_figure: 8

excluded:
  helper_icon: 43

crop_status:
  ready_for_source_crop: 170

source_crop_status:
  main Standard run before optional artifact:
    not_generated: 170

  optional review artifact after generation/rerun:
    created/reused: 170
```

Optional review artifact command:

```bash
python3 backend/scripts/generate_standard_source_crops.py \
  --standard-dir runtime/backend/pipeline-work/audits/gf6-visual-confirmation-v0-fast-rerun-20260629/standard-final
```

Review artifact result:

```text
source_crop_generation: generated
source_crop_count: 170
created/reused: 170
```

## Interpretation

This confirms the next workbook acceptance problem is no longer "review all 213 images".

The actual queue is:

```text
170 source-PDF visual confirmations
43 helper icons for compact/nearby rendering strategy
```

Because all 170 selected packets can be generated as source crops by the optional review step, the next implementation step can compare source crops against the Standard output images and record human/vision review outcomes.

## Next Work

1. Add side-by-side packet review outcomes: Standard image, source crop, neighboring text, category/action.
2. Wire optional crop generation into an asynchronous UI/job path instead of the Standard publish path.
3. Add helper icon compact rendering rules and verify they do not break nearby exercise layout.
4. Promote only reviewed packet outcomes into Basic Print acceptance decisions.
