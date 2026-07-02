# Grammar Paradigm Table Rendering V0 - 2026-06-30

Decision:

```text
Render grammar paradigm tables as aligned multi-row tables when Clean contains a single body row whose cells preserve multiple grammar forms as run-together text.
```

## Why

GF4 exposed a Standard rendering problem after source evidence plumbing was complete.

The three Review 5 table outcomes already had source crops:

```text
b-01544  visual_source_crops/0026-b-01544-image.png
b-01548  visual_source_crops/0028-b-01548-image.png
b-01550  visual_source_crops/0029-b-01550-image.png
```

The source crops show line-by-line grammar paradigm tables, but Clean contained one HTML body row with run-together cell text such as:

```text
I’m playingyou’re playingit’s playingwe’re playingthey’re playing
I've playedyou've playedit's playedwe've playedthey've played
I was playingyou were playingit was playingwe were playingthey were playing
```

Leaving that text as-is is not Basic Print acceptable because it destroys the visual grammar paradigm relation between affirmative, negative, questions, and short answers.

## Rule Boundary

The rendering rule is profile-general and not tied to GF4 block ids.

It only applies when:

- the table has exactly one header row and one body row;
- the header text matches the grammar paradigm pattern:

```text
Affirmative + Negative + Questions + Short answers
```

- every body cell can be split into the same number of grammar lines;
- the common row count is at least 3.

If any of those checks fail, the table is rendered unchanged.

The rule does not edit Clean, Raw, or `standard_document.json`. It only changes Standard HTML/PDF rendering.

## Implementation

Implemented in:

```text
backend/scripts/standard_from_clean.py
```

The renderer parses simple HTML tables, detects grammar paradigm headers, splits cells using:

- explicit line breaks;
- question marks for question columns;
- sentence boundaries for `Yes, ...` / `No, ...` short-answer columns;
- pronoun/form boundaries for affirmative and negative columns.

It then reconstructs a printable table with one row per grammar form.

Test coverage was added in:

```text
backend/tests/test_standard_from_clean.py
```

The test checks the three GF4 table shapes and verifies that collapsed fragments such as `playingyou`, `playedyou`, `am.Yes`, `have.Yes`, and `was.Yes` no longer appear in rendered output.

## GF4 V3 Verification

V3 run:

```text
runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final
```

Manual visual review evidence:

```text
manual_visual_review/standard-page-98.png
manual_visual_review/standard-page-99.png
```

PDF text extraction from pages 98-99 confirms that all three grammar paradigm tables render as aligned rows.

Initial V3 result before source-fidelity policy closure:

```text
accepted_by_rule: 130
accepted: 2
needs_reconstruction: 1
open_blocking_count: 1
```

Closed by manual visual review:

```text
visual:table_visual_review:b-01548  accepted
visual:table_visual_review:b-01550  accepted
```

Still open:

```text
visual:table_visual_review:b-01544  needs_reconstruction
next_action: resolve_source_fidelity_mismatch
```

For `b-01544`, layout is fixed, but the source crop shows:

```text
Yes, they aren’t.
```

Clean/Standard renders:

```text
Yes, they are.
```

That is a source-fidelity mismatch, so the outcome must remain blocking until a source-fidelity policy decision or reconstruction is made.

## Source-Fidelity Follow-up

The remaining blocker was closed under:

```text
docs/standard-research/18-source-fidelity-correction-policy-v0.md
```

Final V3 result:

```text
accepted_by_rule: 130
accepted: 3
open_blocking_count: 0
correction_count: 1
acceptance_status: pass
closure_status: basic_print_candidate
```

The correction is recorded in:

```text
runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final/correction_log.json
```

## Conclusion

The grammar paradigm table rendering rule is validated for the GF4 table-layout failure mode.

GF4 V3 is now a Basic Print candidate, not an accepted golden. Its candidate status depends on both the grammar paradigm rendering rule and one explicit evidence-backed source typo correction.
