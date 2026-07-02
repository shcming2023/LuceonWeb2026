# Standard Quality Levels

## Purpose

Standard status must separate artifact production from textbook usability. A generated `standard-final/` directory is a run result, not proof of a usable textbook.

## Levels

### artifact_only

The Standard stage produced files, but the package cannot be treated as a printable textbook.

Typical evidence:

- required files exist;
- PDF may render;
- hard quality blockers remain;
- visible markup, audit comments, missing images, missing PDF page count, or missing evidence may exist.

This level is useful for debugging and regression, not for users.

### review

The package preserves much of the source content and may be readable, but unresolved structure, evidence, or layout issues remain.

Typical evidence:

- source fidelity and outline lock may pass;
- media references may resolve;
- unresolved visual review packets remain;
- table/formula/source crop verification is incomplete;
- some profile relations are uncertain;
- output is not yet safe to call directly printable.

This is the expected state for many early Standard MVP runs.

### basic_print

The package is the minimum acceptable printable textbook edition.

Requirements:

- source-faithful content;
- no unsupported invention or rewrite;
- source evidence available for layout-sensitive repairs and unresolved visual checks;
- no visible machine artifacts;
- profile-critical learning structures are represented;
- figures, captions, tables, formulas, question groups, options, and answer areas are readable and kept in context;
- PDF renders with readable page count and no severe print defects.

This is the first level that can be called usable as a direct print edition.

### polished

The package is beyond basic print. It is visually refined and closer to a publication-quality or branded edition.

Polish can include:

- theme and brand styling;
- richer typography;
- color palettes;
- cover/frontmatter design;
- more faithful page composition;
- editorial refinements.

Polish must not be required for `basic_print`.

## Status Mapping

Existing Standard `pass/review/fail` reports are not enough by themselves. They should be mapped into this quality model.

```text
fail -> artifact_only or failed_run
review -> review
pass -> candidate for basic_print, subject to hard basic_print gates
```

`standard_done` in the database should mean publication of a Standard artifact to storage, not quality acceptance.

## Required Separation

Use separate fields for:

- stage publication status: whether Standard artifacts were emitted and published;
- quality level: `artifact_only`, `review`, `basic_print`, or `polished`;
- human acceptance: whether a reviewer accepted the output for the intended use.

This prevents the recurring failure mode where mechanical success is treated as final acceptance.
