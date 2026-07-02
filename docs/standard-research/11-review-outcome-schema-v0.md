# Review Outcome Schema V0 - 2026-06-29

## Decision

Standard review findings must close through an independent review layer, not by editing Standard content directly.

V0 introduces:

- `standard_review_outcomes.json`
- `review_outcomes.html`
- `review_outcomes` acceptance gate
- optional closure script: `backend/scripts/close_standard_review_outcomes.py`

The layer records whether visual/table/image review packets are still blocking Basic Print.

## Outcome Semantics

Each outcome records:

- packet source and packet type;
- block id and clean lines;
- heading path;
- source page and bbox when available;
- optional source crop;
- decision;
- open/closed status;
- whether it blocks Basic Print;
- reviewer/method and evidence.

Allowed decisions:

```text
accepted
accepted_by_rule
non_blocking
needs_page_bbox
needs_source_crop
needs_layout_fix
needs_reconstruction
rejected
```

Default Standard generation writes all outcomes as:

```text
decision: pending
status: open
basic_print_blocking: true
```

Closure requires either human/vision review or a deterministic evidence rule.

## Deterministic Rule V0

For table visual packets, `accepted_by_rule` is allowed when all are true:

1. The Standard table text exactly matches the Raw `content_list` table after normalized HTML/text comparison.
2. The packet has source PDF page/bbox evidence.
3. A source PDF crop was generated or reused.

This closes table source-fidelity/visual-evidence risk. It does not authorize invented content or decorative redesign.

## RE1 Closure Evidence

Output:

- `runtime/backend/pipeline-work/audits/re1-review-outcome-v0-rerun-20260629/standard-final/`

Result after closure:

```text
standard_acceptance: pass
quality_score: 97
closure_status: basic_print_accepted
profile: reading_textbook
pdf_page_count: 141
visible_artifact_count: 0
image_refs: 162
missing_images: 0
issue_candidate_count: 0
visual_review_packet_count: 15
review_outcome_closed_count: 15
review_outcome_open_blocking_count: 0
visual_review_source_crop_count: 15
```

All review outcomes:

```text
accepted_by_rule: 15
open_blocking_count: 0
```

All gates in `standard_acceptance_report.json` are now `pass` after closure.

## Promotion Decision

The project accepts deterministic `accepted_by_rule` table closure as sufficient for RE1's first Basic Print golden.

Promoted golden:

- `corpus/golden/accepted/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.golden.json`

This is still a Basic Print sample, not a polished edition.

## Next Work

1. Add the closure script to the async review-artifact UI/job path.
2. Extend outcome closure to image source crops for GF6 only after workbook helper-icon layout is stable.
3. Keep style/color/polish outside Basic Print promotion.
