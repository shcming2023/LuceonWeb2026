# GF6 Standard Rerun Review - 2026-06-29

## Scope

Material:

- `material_id`: `pdf-ff4c7f59964ad54f`
- `filename`: `Grammar Friends 6 (Students Book) (Flannigan E.) (Z-Library).pdf`

Rerun output:

- `runtime/backend/pipeline-work/audits/gf6-standard-rerun-20260629/standard-final/`

Inputs:

- Clean: `runtime/backend/pipeline-work/clean2standard/run-44-pdf-ff4c7f59964ad54f-popo-20260617014256-staged_popo_20260617_batch07_sma-1369cfec--002-popo_ff4c7f59964ad54f_002/clean_input/`
- Raw: `runtime/backend/pipeline-work/clean2standard/run-44-pdf-ff4c7f59964ad54f-popo-20260617014256-staged_popo_20260617_batch07_sma-1369cfec--002-popo_ff4c7f59964ad54f_002/raw_input/`
- Source PDF: `runtime/backend/pipeline-work/popo2raw/run-37-pdf-ff4c7f59964ad54f-popo-20260617014256-staged_popo_20260617_batch07_sma-1369cfec--002-popo_ff4c7f59964ad54f_002/rebuild_input/pdf-ff4c7f59964ad54f_origin.pdf`

## Result

The rerun remains `review`, not `pass`.

Later profile V0 rerun:

- `runtime/backend/pipeline-work/audits/gf6-profile-v0-rerun-20260629/standard-final/`
- see `08-profile-v0.md`

The profile V0 rerun supersedes this run as the active GF6 regression baseline.

This is a better result than the old package because the status is now evidence-bearing:

- `pdf_page_count` is readable: `144`.
- `source_pdf_available` is `true`.
- `visible_artifact_count` is `0`.
- visible `<tr>/<td>` and `source_empty_chunk` leakage were not found in `standard.html` or `standard.md`.

The old run was also `review`, but it hid important facts:

- `pdf_page_count`: `null`.
- `source_pdf_available`: `false`.
- no visible-artifact gate existed.

## Acceptance Summary

```text
status: review
quality_score: 87
block_count: 1840
outline_count: 40
image_refs: 213
missing_images: 0
issue_candidate_count: 213
visual_review_packet_count: 27
visible_artifact_count: 0
pdf_page_count: 144
```

Gate summary:

```text
pass:
  outline_lock
  source_fidelity
  correction_evidence
  media_integrity
  visible_artifacts
  layout_sanity
  print_render
  source_evidence
  auditability

review:
  context_integrity
  formula_table_integrity
  review_threshold
```

## Main Findings

### 1. Gate hardening worked

GF6 no longer fails because of raw printed HTML fragments or pipeline comments.

The previous visible-leak defect is controlled by:

- multi-line HTML table coalescing;
- pure HTML comment removal from Standard blocks;
- `visible_artifacts` detection in `print_qa_report.json` and `standard_acceptance_report.json`.

### 2. The remaining problem is not source completeness

Source-fidelity, outline-lock, PDF rendering, media existence, and source-PDF evidence all pass.

GF6 should not be treated as a raw/clean completeness failure at this point. The next problem is Standard-level context and layout reconstruction.

### 3. Image semantics are still not connected

All `213` issue candidates are `missing_raw_image_semantics`.

This means the images exist and render, but Standard cannot prove their original page/block relationship from Raw semantics. For Basic Print, this must remain a review blocker because image placement affects textbook meaning.

### 4. Exercise structure is under-classified

`layout_report.json` shows:

```text
question_groups: 0
questions: 0
options: 0
answer_blanks: 532
```

This is a strong sign that Grammar Friends needs a workbook/grammar-exercise profile rather than the current reading-textbook-biased default profile.

### 5. Visual sample confirms layout weakness

Rendered page previews:

- `runtime/backend/pipeline-work/audits/gf6-standard-rerun-20260629/page-previews/gf6-standard-p1-001.png`
- `runtime/backend/pipeline-work/audits/gf6-standard-rerun-20260629/page-previews/gf6-standard-p2-002.png`
- `runtime/backend/pipeline-work/audits/gf6-standard-rerun-20260629/page-previews/gf6-standard-p10-010.png`

Page 10 shows a representative remaining issue: small instructional images are centered as loose standalone figures, creating large blank areas and weakening their relationship to the surrounding grammar explanation.

## Root Cause Label

Primary: `qa_gate_gap`, now partially fixed.

Remaining: `final_rendering` plus `block_assignment` at the Standard semantic-layout layer.

The rerun proves that GF6 no longer mainly fails because Standard cannot render or audit. It fails because Basic Print requires exercise-aware grouping and image/text relation handling.

## Next Iteration Priorities

1. Add a `grammar_workbook` or `exercise_workbook` Standard profile.
2. Classify numbered exercise stems, fill-in blanks, option-like fragments, grammar boxes, and example rows into question groups.
3. Link small images to adjacent grammar examples or exercises instead of centering each as an independent figure.
4. Promote `missing_raw_image_semantics` from a generic issue count into actionable relation checks: image-only block, loose caption, adjacent example, page evidence missing.
5. Keep GF6 as a negative regression case: it should remain `review` until exercise grouping and image relation gates improve.
