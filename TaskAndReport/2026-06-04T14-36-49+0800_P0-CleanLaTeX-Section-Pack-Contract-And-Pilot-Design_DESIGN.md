# CleanLaTeX Section Pack Contract And Pilot Design

Task ID: TASK-20260604-143649-P0-CleanLaTeX-Section-Pack-Contract-And-Pilot-Design

## 1. Design Position

CleanLaTeX must not decide the whole-book structure.

The upstream contract is:

```text
MinerU
  -> parsed artifacts, markdown, images/formulas/tables/source evidence
MinerU-Popo
  -> official structural normalization tree
Luceon Layer 3 deterministic rules
  -> canonical_toc.json
  -> chapter_spans.json
  -> rawlatex_scaffold.json
CleanLaTeX
  -> clean inside source-bound section/exercise packs only
```

Therefore the next generator should not send a whole book, whole chapter, or plain Markdown dump to an LLM. It should send **bounded section/exercise packs** whose source scope is already fixed by `canonical_toc` and `chapter_spans`.

## 2. Cleaning Unit

Primary LLM unit:

```text
section
```

Secondary LLM unit:

```text
exercise
```

Aggregation unit:

```text
chapter
```

Rules:

- A `chapter` is an assembly container, not the default LLM cleaning unit.
- A `section` is the default semantic cleaning unit.
- An `exercise` may be cleaned inside its parent section when small, or as a child pack when large/noisy.
- A `unit` only groups chapters and should not be directly cleaned by LLM.

Rationale:

- Whole chapters are often too large and invite boundary drift.
- Sections usually match textbook reading order and instructional coherence.
- Exercises often need separate validation because they contain numbered questions, diagrams, formulas, and answer-like structures.

## 3. Artifact Layout

For each canonical section:

```text
cleanlatex-packs/<material_id>/<asset_version>/sections/<node_id>/
  section_pack.json
  prompt.md
  source_excerpt.md
  assets_manifest.json
  validation_manifest.json
```

For each separately cleaned exercise:

```text
cleanlatex-packs/<material_id>/<asset_version>/exercises/<node_id>/
  exercise_pack.json
  prompt.md
  source_excerpt.md
  assets_manifest.json
  validation_manifest.json
```

`pack.json` is the truth source. `prompt.md` is a derived human-readable view for LLM input and must be regenerable from `pack.json`.

## 4. Section Pack Schema

Schema id:

```text
luceon-cleanlatex-section-pack/v1
```

Required shape:

```json
{
  "schema": "luceon-cleanlatex-section-pack/v1",
  "pack_id": "section:toc-0002",
  "material_id": "4134323036518274",
  "asset_version": "v327-conservative-chapter-inference-a800-math-2022-prod-uat",
  "node": {
    "node_id": "toc-0002",
    "kind": "section",
    "title": "1.1 Different types of numbers",
    "number": "1.1",
    "parent_id": "toc-0001",
    "parent_title": "1 Review of number concepts",
    "ancestor_path": [
      {"kind": "unit", "title": "Unit 1", "node_id": "toc-0000"},
      {"kind": "chapter", "title": "1 Review of number concepts", "node_id": "toc-0001"}
    ]
  },
  "source_span": {
    "source_order_range": [12, 19],
    "source_page_range": [16, 17],
    "source_block_ids": ["191", "193"],
    "source_tree": {
      "bucket": "eduassets-clean",
      "object": "toc-rebuild/.../official_popo_tree.json"
    },
    "canonical_toc": {
      "bucket": "eduassets-clean",
      "object": "toc-rebuild/.../canonical_toc.json"
    },
    "chapter_spans": {
      "bucket": "eduassets-clean",
      "object": "toc-rebuild/.../chapter_spans.json"
    }
  },
  "content_blocks": [],
  "child_packs": [],
  "assets": {
    "images": [],
    "tables": [],
    "formulas": [],
    "audio": []
  },
  "cleaning_contract": {
    "unit": "section",
    "may_clean_ocr_text": true,
    "may_normalize_math_latex": true,
    "may_reorder_within_pack": true,
    "may_create_latex_section_commands": true,
    "must_not_change_node_id": true,
    "must_not_change_parent_id": true,
    "must_not_create_or_delete_chapter_or_section": true,
    "must_not_move_blocks_outside_pack": true,
    "must_preserve_source_block_ids": true,
    "must_preserve_asset_hash_names": true,
    "must_report_unresolved_items": true
  },
  "expected_output": {
    "schema": "luceon-cleanlatex-output/v1",
    "output_role": "section_cleanlatex",
    "path": "cleanlatex/sections/toc-0002_section_1-1.tex"
  },
  "warnings": []
}
```

## 5. Content Block Schema

`content_blocks[]` must preserve source order. Each block must carry stable source references.

Common fields:

```json
{
  "block_id": "191",
  "source_order": 12,
  "page": 16,
  "bbox": [0.1, 0.2, 0.3, 0.4],
  "type": "text",
  "raw_text": "...",
  "normalized_text": null,
  "source_hash": "sha256:...",
  "warnings": []
}
```

Allowed `type` values:

- `title`
- `text`
- `formula`
- `table`
- `image`
- `list`
- `question`
- `example`
- `caption`
- `footnote`
- `unknown`

Formula block:

```json
{
  "block_id": "formula-001",
  "type": "formula",
  "raw_text": "...",
  "latex": "...",
  "source_format": "mineru",
  "page": 16,
  "bbox": [],
  "source_hash": "sha256:..."
}
```

Image block:

```json
{
  "block_id": "image-001",
  "type": "image",
  "asset_hash_name": "895209977cd9d86867c07fcfc6f709604e029c454984782838f2809ad876be0.jpg",
  "object": "parsed/4134323036518274/images/895209977cd9d86867c07fcfc6f709604e029c454984782838f2809ad876be0.jpg",
  "caption": "...",
  "page": 17,
  "bbox": [],
  "source_hash": "sha256:..."
}
```

Table block:

```json
{
  "block_id": "table-001",
  "type": "table",
  "raw_markdown": "| ... |",
  "raw_html": null,
  "cells": [],
  "page": 17,
  "bbox": [],
  "source_hash": "sha256:..."
}
```

## 6. Exercise Pack Schema

Schema id:

```text
luceon-cleanlatex-exercise-pack/v1
```

Required shape:

```json
{
  "schema": "luceon-cleanlatex-exercise-pack/v1",
  "pack_id": "exercise:toc-0145",
  "material_id": "4134323036518274",
  "asset_version": "v327-conservative-chapter-inference-a800-math-2022-prod-uat",
  "node": {
    "node_id": "toc-0145",
    "kind": "exercise",
    "title": "Exercise 1.1",
    "number": "1.1",
    "parent_id": "toc-0002",
    "parent_title": "1.1 Different types of numbers",
    "ancestor_path": []
  },
  "source_span": {
    "source_order_range": [20, 32],
    "source_page_range": [17, 18],
    "source_block_ids": []
  },
  "question_blocks": [],
  "assets": {
    "images": [],
    "tables": [],
    "formulas": []
  },
  "cleaning_contract": {
    "unit": "exercise",
    "may_clean_ocr_text": true,
    "may_normalize_math_latex": true,
    "may_group_subquestions": true,
    "must_preserve_question_order": true,
    "must_not_answer_questions": true,
    "must_not_move_questions_to_other_sections": true,
    "must_preserve_source_block_ids": true,
    "must_preserve_asset_hash_names": true
  },
  "expected_output": {
    "schema": "luceon-cleanlatex-output/v1",
    "output_role": "exercise_cleanlatex",
    "path": "cleanlatex/exercises/toc-0145_exercise_1-1.tex"
  },
  "warnings": []
}
```

## 7. Prompt Contract

`prompt.md` is derived from `pack.json` and must not become a source of truth.

Required prompt sections:

```text
# CleanLaTeX Pack

## Identity
You clean exactly one source-bound section/exercise pack.

## Structural Boundary
- Node id:
- Kind:
- Title:
- Parent:
- Source pages:
- Source block ids:

## Non-Negotiable Rules
- Do not create, delete, reorder, or rename chapters/sections.
- Do not move content outside this pack.
- Do not invent textbook content.
- Preserve image hash names exactly.
- Preserve source block id references.
- Do not answer exercises.

## Source Blocks
...

## Required Output
Return JSON matching luceon-cleanlatex-output/v1.
```

The LLM may:

- fix OCR spacing and obvious character noise;
- normalize inline/display math into LaTeX;
- convert tables into standard LaTeX tabular/array where possible;
- emit image placeholders using original hash names;
- improve local reading order inside the pack.

The LLM must not:

- decide whole-book TOC;
- create new chapters or sections;
- delete source blocks silently;
- rename asset hashes;
- replace diagrams with descriptions only;
- answer questions;
- use custom LaTeX commands.

## 8. CleanLaTeX Output Contract

Schema id:

```text
luceon-cleanlatex-output/v1
```

Required output envelope:

```json
{
  "schema": "luceon-cleanlatex-output/v1",
  "pack_id": "section:toc-0002",
  "node_id": "toc-0002",
  "kind": "section",
  "title": "1.1 Different types of numbers",
  "source_block_ids_consumed": ["191", "193"],
  "source_block_ids_unresolved": [],
  "asset_hashes_used": [],
  "latex": "\\section*{1.1 Different types of numbers}\\n...",
  "unresolved_items": [],
  "warnings": [],
  "quality_self_check": {
    "no_structure_change": true,
    "no_asset_rename": true,
    "no_unreferenced_source_blocks": true,
    "no_exercise_answers_added": true
  }
}
```

LaTeX constraints:

- Use standard LaTeX only.
- Do not define custom commands.
- Use stable placeholders for images:

```tex
\includegraphics{895209977cd9d86867c07fcfc6f709604e029c454984782838f2809ad876be0.jpg}
```

- Preserve math as LaTeX where available.
- Mark unresolved blocks explicitly instead of inventing content.

## 9. Source Preservation Rules

1. Every emitted CleanLaTeX pack must reference `pack_id` and `node_id`.
2. Every source block must be either:
   - consumed;
   - intentionally omitted with reason;
   - unresolved with reason.
3. `source_block_ids_consumed + source_block_ids_unresolved + source_block_ids_omitted` must equal input source block ids.
4. Page and bbox evidence must remain in `validation_manifest.json`; it does not need to be repeated in LaTeX.
5. LLM must not generate free-standing source claims without block IDs.
6. If source order is changed within the pack, output must report `reordered_block_ids`.

## 10. Asset Hash Preservation Rules

1. Image/audio/resource filenames are immutable.
2. Asset references must use original hash names exactly.
3. No normalized, shortened, translated, or descriptive asset names.
4. If an asset cannot be placed, it must be listed in `unresolved_items`.
5. A validation step must compare:

```text
input asset_hash_names == output asset_hashes_used + unresolved asset_hashes
```

6. The pack generator must not copy assets to new hash names.

## 11. Validation Manifest

Each pack should include:

```json
{
  "schema": "luceon-cleanlatex-validation-manifest/v1",
  "pack_id": "section:toc-0002",
  "input_counts": {
    "blocks": 12,
    "images": 1,
    "formulas": 3,
    "tables": 0
  },
  "output_checks": {
    "source_block_coverage": "pending",
    "asset_hash_preservation": "pending",
    "latex_parse": "pending",
    "forbidden_custom_commands": "pending",
    "structure_boundary": "pending"
  }
}
```

## 12. Pilot Selection

Pilot A:

```text
1.1 Different types of numbers
```

Reason:

- early section;
- likely contains explanatory text, basic math notation, and at least one exercise relation;
- good for validating clean text/math without overwhelming size.

Pilot B:

```text
4.1 Colectingand classifyingdata
```

Reason:

- exercises the newly inferred Chapter 4 container;
- likely contains data/statistics/table/chart material;
- tests whether source-bound pack can preserve table/chart/image evidence.

Pilot should generate:

- `section_pack.json`
- optional child `exercise_pack.json`
- `prompt.md`
- LLM output JSON
- `.tex`
- validation result

## 13. Acceptance For Future Implementation

Pack generator acceptance:

- Builds packs for `1.1` and `4.1` from v327 artifacts without rerunning MinerU-Popo.
- Keeps source block IDs and asset hashes.
- Produces deterministic `prompt.md` from `pack.json`.
- Fails closed if source blocks cannot be resolved.

CleanLaTeX pilot acceptance:

- LLM output validates against `luceon-cleanlatex-output/v1`.
- No chapter/section boundary changes.
- No missing image hash without unresolved warning.
- No missing formula block without unresolved warning.
- No exercise answers are invented.
- LaTeX uses standard packages/commands only.
- Output is reviewable by a human against original source blocks.

## 14. Non-Goals

- Full-book CleanLaTeX automation.
- Full title/OCR correction for all chapters.
- Final PDF rendering.
- Answer generation.
- Replacing MinerU-Popo official structure.
- Hiding source defects with LLM guesses.

## 15. Next Implementation Task

Recommended next task:

```text
P0 Source-Bound Section Pack Generator For CleanLaTeX Pilot
```

Narrow goal:

- Implement pack generation for `1.1` and `4.1` only.
- Use v327 `canonical_toc`, `chapter_spans`, `official_popo_tree`, and MinerU parsed artifacts.
- Produce pack artifacts and validation manifests.
- Do not call LLM yet unless separately authorized.
