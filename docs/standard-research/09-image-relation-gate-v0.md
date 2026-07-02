# Workbook Image Relation Gate V0 - 2026-06-29

## Decision

For workbook-like Standard output, image handling must be reviewed as a semantic relation problem before any visual polishing.

The V0 gate separates workbook figures into:

```text
helper_icon:
  small auxiliary icon, compress and keep near nearby text

exercise_key_figure:
  content-bearing figure tied to an exercise/question group

explanation_key_figure:
  content-bearing figure tied to grammar explanation or rule text

decorative:
  low-priority image with no detected exercise/explanation role

needs_dimension_review:
  image dimensions could not be read
```

The gate does not drop media. It classifies relation intent and records which images still need source-PDF visual confirmation.

## Implementation

Implemented in `backend/scripts/standard_from_clean.py`:

- `image_relation_report.json`
- block-level `image_relation` metadata for `captioned_figure` blocks
- `image_relation_integrity` acceptance gate
- `image_relation_report` entry in manifest outputs and deliverable checks

Service publishing support was added in `backend/app/services/clean_to_standard.py`.

## Classification Evidence

GF6 image size distribution showed a clear small-icon cluster:

```text
helper icon examples:
  42 x 95
  46 x 95
  45 x 95
  79 x 85

exercise/explanation figures:
  roughly 689 x 345 and larger
  large opener/explanation images often exceed 1,000,000 px area
```

V0 helper icon threshold:

```text
area <= 20000 or max(width, height) <= 160
```

This is intentionally conservative to avoid compressing content-bearing figures.

## GF6 Rerun Evidence

Output:

- `runtime/backend/pipeline-work/audits/gf6-image-relation-v0-rerun-20260629/standard-final/`

Result:

```text
status: review
quality_score: 87
profile: grammar_workbook
pdf_page_count: 144
visible_artifact_count: 0
image_relation_count: 213
image_relation_source_visual_check_count: 170
```

Profile structure:

```text
profile_coverage: pass
question_groups: 146
questions: 711
answer_blanks: 157
table_questions: 26
figure_relation_candidates: 213
```

Image relation gate:

```text
image_relation_integrity: review

category_counts:
  helper_icon: 43
  exercise_key_figure: 162
  explanation_key_figure: 8

action_counts:
  compress_keep_near: 43
  keep_with_exercise: 162
  keep_with_explanation: 8

review_reasons:
  - source_visual_check_required
```

## Interpretation

The split is now clean:

- workbook structural coverage is good enough for V0;
- PDF rendering, source fidelity, visible artifacts, and source PDF evidence pass;
- Basic Print is still blocked by image relation verification, not by generic profile failure.

This is the right next baseline for GF6.

## Next Work

1. Add page/bbox-backed source visual packets for `exercise_key_figure` and `explanation_key_figure`. Completed in `10-image-visual-confirmation-packets-v0.md`.
2. Let helper icons use compact inline/nearby rendering rules.
3. Add review tooling that samples each image category, not all images uniformly.
4. Only after visual relation review closes should workbook CSS be tightened.
