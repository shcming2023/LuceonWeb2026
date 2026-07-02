# Standard Profile V0 - 2026-06-29

## Decision

Basic Print Phase 1 is split into two profile tracks:

```text
reading_textbook:
  positive comparator: RE1 audit MVP

grammar_workbook / exercise_workbook:
  negative regression comparator: GF6
```

The split is semantic and structural, not visual decoration. The first goal is to make profile-critical structures measurable.

## Implementation Scope

Implemented in `backend/scripts/standard_from_clean.py`:

- `--profile auto|reading_textbook|grammar_workbook|exercise_workbook`
- automatic profile inference from title and workbook-like structure density
- workbook exercise instruction detection
- workbook numbered item detection
- table-question subtype
- figure relation candidate marking
- `profile_coverage` acceptance gate
- profile fields in `standard_document.json`, `layout_report.json`, acceptance summary, and `manifest.json`

This V0 does not yet redesign workbook rendering. It creates the structural layer needed for the next renderer iteration.

## GF6 V0 Evidence

Output:

- `runtime/backend/pipeline-work/audits/gf6-profile-v0-rerun-20260629/standard-final/`

Result:

```text
status: review
quality_score: 87
profile: grammar_workbook
pdf_page_count: 144
visible_artifact_count: 0
source_pdf_available: true
```

Profile metrics:

```text
question_groups: 146
questions: 711
answer_blanks: 157
table_questions: 26
figure_relation_candidates: 213
```

Gate result:

```text
profile_coverage: pass after image-relation gate split
blockers: []
review_reasons: []
```

Interpretation:

- The previous all-zero workbook relation failure is fixed at the structural counting level.
- GF6 remains `review`, but image review now belongs to `image_relation_integrity`, not `profile_coverage`.
- See `09-image-relation-gate-v0.md` for the active GF6 image relation baseline.

## RE1 Comparator Role

RE1 remains the first `reading_textbook` candidate golden comparator.

It should not be judged by workbook metrics. Its profile-critical concepts are reading passages, question groups, options, passage layout, media, and tables.

## Next Work

1. Add page/bbox-backed image relation checks for workbook images.
2. Let helper icons use compact workbook rendering rules.
3. Add compact workbook CSS only after the profile relation layer is stable.
4. Add `basic_print` promotion logic separately from `standard` publication.
