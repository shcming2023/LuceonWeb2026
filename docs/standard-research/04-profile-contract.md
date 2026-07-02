# Profile Contract

## Purpose

Profiles let Standard handle different textbook genres without fragmenting the whole system into per-book renderers.

The normalized target is always `StandardDocument`. Profiles map source-specific signals into shared semantic blocks and layout intent.

## Core Rule

Normalize the semantic structure, not the visual appearance.

Profiles must not hard-code one book title, one material id, or one source filename. A profile can target a material family such as workbook, reading textbook, math textbook, or bilingual reader.

## StandardDocument Core Blocks

All profiles should map into shared block types where possible:

```text
heading
section
paragraph
passage
instruction
question_group
question
option
answer_blank
answer_area
figure
caption
table
formula
box
note
footnote
list
unknown
```

Profiles may add subtype values, but should not invent incompatible top-level structures unless the core schema is extended.

## Shared Relations

Profiles should produce relations such as:

```text
contains
follows
belongs_to
captioned_by
explained_by
has_instruction
has_question
has_option
has_answer_area
uses_figure
uses_table
uses_formula
left_matches_right
```

These relations matter more than matching the original visual arrangement.

## Layout Intent

Profiles assign layout intent. The renderer decides the final neutral print CSS.

Common intents:

```text
keep_together
keep_with_next
page_break_before
two_column_passage
choice_inline
choice_grid
matching_two_column
table_question
answer_area
figure_with_caption
box_callout
formula_block
compact_list
```

## Profile Responsibilities

A profile is responsible for:

- identifying profile-critical semantic zones;
- grouping related blocks;
- detecting relationships between instruction, questions, media, tables, formulas, and answer areas;
- assigning layout intent;
- marking uncertain structures as `needs_review`;
- reporting coverage and risk.

A profile is not responsible for:

- visual branding;
- color themes;
- decorative design;
- rewriting content;
- global outline decisions;
- free-form HTML generation.

## Model Use Boundary

Models may assist only on constrained local tasks:

- low-confidence block classification;
- relation judgment;
- local table/formula repair from source evidence;
- local OCR correction from PDF crop evidence;
- layout intent suggestion.

Model output must be JSON and schema-validated. Low-confidence output downgrades to `needs_review`.

## Initial Profiles

### reading_textbook

Required concepts:

- unit opener;
- lesson/section heading;
- reading passage;
- captioned figure;
- vocabulary box;
- comprehension section;
- practice section;
- review unit;
- source evidence for tables and figures.

### workbook

Required concepts:

- instruction;
- question group;
- single question;
- choice group;
- fill blank;
- matching;
- table question;
- answer area;
- figure associated with question or instruction.

### math_textbook

Required concepts:

- concept;
- definition;
- worked example;
- theorem/rule;
- formula block;
- diagram;
- table;
- practice set;
- solution or answer area when present.

## Acceptance Implication

If a material selects a profile, missing profile-critical structures must block `basic_print` unless the absence is proven from source evidence.

Example:

- A workbook with zero detected question groups is not `basic_print`.
- A formula-heavy math material with unresolved formula visual packets is not `basic_print`.
- A reading textbook with unresolved tables may be `review` until table visual checks close.
