# Standard Node Design

## Purpose

`standard` is the node after `clean`. Its purpose is to turn a clean material package into a source-faithful, evidence-corrected, printable basic textbook package.

It is not a creative rewrite and not a decorative edition. It is the most basic usable edition that can be read, printed, exported to PDF, cited, and used as a stable basis for later textbook building, question-bank construction, and semantic annotation.

The guiding principle is:

> Standard is faithful to the original textbook, not mechanically faithful to every remaining mistake in Clean.

Clean may still contain upstream OCR errors, missing text, broken formulas, table damage, wrong image-caption relations, or context breaks introduced by MinerU, MinerU-Popo, Raw, or Clean processing. `standard` may repair these problems only when there is evidence from the original PDF, Raw artifacts, source maps, page crops, image semantics, or other upstream traces.

## Position in the Pipeline

```text
input PDF
  -> MinerU / MinerU-Popo
  -> Raw
  -> Clean
  -> Standard
```

Stage responsibilities:

- `Raw`: recover outline, reading order, block assignments, and source evidence from immutable MinerU / MinerU-Popo outputs.
- `Clean`: remove noise, preserve content, keep image/table/formula closure, and produce an auditable clean candidate.
- `Standard`: build a printable textbook master from Clean, with evidence-based corrections and structure-aware layout.

## Non-Goals

`standard` must not:

- rewrite the textbook in a new style;
- summarize, simplify, or expand content;
- add new knowledge, examples, questions, answers, explanations, or teaching notes;
- silently invent missing content;
- let an LLM decide the global book structure;
- use visual polish as a reason to change original content.

## Allowed Repairs

The node may perform local, evidence-backed repairs:

- OCR text repair;
- missing original text recovery;
- formula repair;
- table reconstruction;
- reading-order repair;
- image-caption relinking;
- figure/table/formula placement repair;
- question stem / option / instruction regrouping;
- vocabulary box / note / passage grouping;
- conservative removal of decorative images with evidence;
- minimal layout organization required for readable printing.

Every repair must be recorded in `correction_log.json`.

## Standard Output Package

Expected output directory:

```text
standard-final/
  standard.md
  standard.html
  standard.pdf
  images/
  manifest.json
  standard_document.json
  correction_log.json
  standard_issue_candidates.json
  layout_report.json
  print_qa_report.json
  standard_acceptance_report.json
  review.html
```

Required properties:

- `standard.md` is a readable source-faithful Markdown master.
- `standard.html` is simple, stable, printable HTML.
- `standard.pdf` is generated from `standard.html`.
- `images/` contains only referenced media.
- `standard_document.json` is the structured intermediate representation.
- `correction_log.json` records every evidence-backed correction.
- `review.html` shows Clean / Standard / evidence differences for review.

## Core Architecture

Do not implement this as "send Clean chunks to an LLM and ask for standard HTML."

Use a structured compiler architecture:

```text
clean.md
  -> CleanAST / line blocks
  -> semantic zoning
  -> StandardDocument
  -> evidence-aware local corrections
  -> template rendering
  -> standard.html / standard.pdf
  -> QA gates
```

The stable architecture has three layers:

```text
Layer 1: Deterministic Compiler
  Clean + Raw evidence -> StandardDocument

Layer 2: Evidence-Aware Model Assist
  only low-confidence classification, grouping, and local correction

Layer 3: Template Renderer + QA
  StandardDocument -> HTML/PDF + reports
```

## Semantic Zoning

The first job of `standard` is not text cleaning. It is recovering textbook semantic zones as continuous line ranges.

Example:

```json
{
  "id": "b-001",
  "type": "reading_passage",
  "line_start": 35,
  "line_end": 92,
  "heading_path": ["Unit 1", "1A Animal Intelligence"],
  "layout_hint": "two_column",
  "status": "ok"
}
```

This is more robust than arbitrary token chunks.

The node should classify line ranges into blocks, then classify relationships between blocks and child elements.

## Generic Block Types

The universal schema should support at least:

```text
section
paragraph
heading
passage
instruction
question_group
question
option
answer_blank
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

Material-specific profiles may add subtypes.

## Material Profiles

Do not hard-code RE1 into the core compiler.

Use profiles:

```text
profiles/
  reading_textbook.yaml
  math_textbook.yaml
  workbook.yaml
  bilingual_reader.yaml
```

Examples:

Reading textbook profile:

```text
unit_opener
warm_up
before_you_read
reading_passage
captioned_figure
vocabulary_box
reading_comprehension
vocabulary_practice
discussion_prompt
explore_more
review_unit
answer_key
```

Math textbook profile:

```text
concept
definition
worked_example
theorem
formula_block
practice_set
solution
diagram
```

Workbook profile:

```text
instruction
question_group
single_question
choice_group
fill_blank
matching
table_question
answer_area
```

If no profile matches confidently, fall back to generic block types and mark ambiguous blocks for review.

## Deterministic Signals

The compiler should first use rule-based evidence:

- Markdown headings;
- clean line ranges;
- source map entries;
- raw unit ids;
- raw block assignments;
- image semantics;
- page index and bbox evidence;
- image lines;
- table ranges;
- formula delimiters;
- numbered questions;
- option markers;
- caption markers such as `▲` / `▼`;
- small-title patterns such as `Before You Read`;
- exercise labels such as `A. Completion.`;
- page/order locality.

High-confidence deterministic results should not be sent to a model.

## Model Usage Boundary

External LLM / vision APIs are allowed, but only as constrained assistants.

Allowed model tasks:

- block type classification for low-confidence ranges;
- relationship judgment, such as image-caption or instruction-question grouping;
- issue detection;
- local correction from evidence packets;
- table/formula repair from PDF crops;
- layout hint suggestion.

Forbidden model tasks:

- global outline creation;
- whole-book rewriting;
- free-form HTML generation for arbitrary chunks;
- content invention when evidence is missing.

Model output must be JSON and schema-validated. Invalid, low-confidence, or conflicting output must downgrade to `needs_review`, not silently apply.

## Evidence Packets

Local correction requests should use evidence packets:

```json
{
  "block_id": "b-042",
  "problem": "formula_maybe_wrong",
  "clean_text": "...",
  "raw_text": "...",
  "nearby_blocks": "...",
  "source_pdf_page": 42,
  "bbox": [120, 80, 520, 240],
  "image_crop": "..."
}
```

The response must be a local correction proposal, not a rewrite.

## Correction Log

Every applied correction must be written to `correction_log.json`:

```json
{
  "type": "missing_text_recovered",
  "block_id": "b-042",
  "before": "...",
  "after": "...",
  "evidence": {
    "source": "pdf_page_crop",
    "page": 42,
    "bbox": [120, 80, 520, 240],
    "raw_block_refs": ["content-list-001234"]
  },
  "confidence": 0.94,
  "applied": true
}
```

No evidence means no automatic repair.

## StandardDocument Schema

The intermediate object should look like:

```json
{
  "schema": "luceon-standard-document/v1",
  "material_id": "...",
  "source_clean_manifest": "...",
  "outline": [],
  "blocks": [
    {
      "id": "b-001",
      "type": "before_you_read",
      "subtype": "",
      "heading_path": ["Unit 1", "1A Animal Intelligence"],
      "line_start": 22,
      "line_end": 34,
      "status": "ok",
      "layout": {
        "style": "exercise_box",
        "keep_together": true
      },
      "children": [],
      "evidence": {
        "clean_lines": [22, 34],
        "raw_unit_id": "unit-0002",
        "raw_block_refs": [],
        "pages": [9]
      }
    }
  ],
  "relations": [
    {"from": "fig-003", "type": "captioned_by", "to": "cap-003"}
  ]
}
```

## Block Status

Each block should have a status:

```text
ok
needs_layout
needs_grouping
needs_evidence
needs_review
failed
```

Only `needs_evidence` blocks enter evidence-backed correction. `needs_review` is preserved and reported.

## Rendering Policy

HTML should be simple and print-stable:

- semantic block wrappers;
- no app framework dependency;
- A4/Letter print CSS;
- stable font size and line height;
- `break-inside: avoid` for figures, tables, question groups, and boxes;
- optional two-column layout for reading passages;
- figure + caption kept together;
- vocabulary boxes and notes rendered as simple boxes;
- tables rendered as native HTML tables;
- formulas rendered conservatively, preferably with MathJax when needed.

The goal is a plain printable textbook master, not a designed final edition.

## Acceptance Gates

`standard_acceptance_report.json` should include:

```text
outline_lock
source_fidelity
correction_evidence
context_integrity
media_integrity
formula_table_integrity
layout_sanity
print_render
auditability
review_threshold
```

Status levels:

```text
pass
review
fail
```

Fail examples:

- outline drift;
- missing referenced media;
- PDF render failure;
- unlogged content changes;
- correction without evidence;
- question/options split incorrectly;
- formula/table loss beyond allowed evidence-backed changes.

Review examples:

- low-confidence block classification;
- suspicious OCR not repaired;
- uncertain image relation;
- complex table preserved but not rebuilt;
- formula crop unavailable.

## RE1 MVP Scope

For RE1, first implement a reading textbook profile:

- unit / lesson hierarchy;
- warm-up and before-you-read blocks;
- reading passage blocks;
- captioned image blocks;
- vocabulary practice blocks;
- comprehension question blocks;
- explore-more resource blocks;
- review units.

The MVP should generate `standard.html` and `standard.pdf` from the current accepted Clean package, then report:

- block classification counts;
- low-confidence blocks;
- remaining review blocks;
- image usage summary;
- corrections applied;
- PDF render status.

## Development Roadmap

1. Define schemas and output contract.
2. Implement Clean Markdown parser and heading tree.
3. Implement generic semantic zoning.
4. Add RE1 reading-textbook profile.
5. Build StandardDocument.
6. Render plain `standard.html`.
7. Generate `standard.pdf`.
8. Add QA reports and acceptance gates.
9. Add evidence-backed correction workflow.
10. Add review UI for Clean vs Standard vs correction log.
11. Generalize profiles for math textbook and workbook materials.

## Design Guardrails

- Preserve global structure with code.
- Let profiles extend semantics, not replace the core schema.
- Use models only for local low-confidence tasks.
- Record every repair.
- Prefer `review` over false certainty.
- Keep printed output plain, stable, and useful.
- Treat RE1 as the first profile, not the whole system.

