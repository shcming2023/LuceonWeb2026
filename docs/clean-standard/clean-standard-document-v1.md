# Luceon Clean Standard Document V1

Purpose:

```text
Define the canonical Clean-stage JSON contract that the Standard compiler can consume without re-discovering textbook structure from plain Markdown.
```

This document abstracts the current Standard research samples into one finite, general intermediate representation. It is not a Reading Explorer format, Grammar Friends format, G7+ format, or Math 8A format. Those samples are evidence for the same structural language.

## Product Position

The pipeline target is:

```text
PDF/Raw evidence -> Clean Standard Document -> Standard Basic Print compiler -> profile gates -> review outcomes -> corpus/golden decisions
```

The Clean stage must output two complementary artifacts:

| Artifact | Audience | Role |
| --- | --- | --- |
| `clean.md` | humans and editors | readable body master |
| `clean_standard.json` | Standard compiler | canonical structured contract |

Markdown remains useful, but it is not the compiler contract. The JSON document is the contract.

## Design Principles

1. Use one finite structural vocabulary for reading textbooks, grammar workbooks, exercise workbooks, math textbooks, image-heavy material, and formula/table-heavy material.
2. Keep sample identity out of the schema. No field may depend on filename, material id, sample title, or page number patterns.
3. Model structure and evidence separately from style. Color, cover design, typography polish, and decorative layout are not Clean Standard requirements.
4. Preserve uncertainty explicitly with `review_flags` and `blockers`; never hide uncertainty by forcing a block type or relation.
5. Every educational block should be traceable to Raw/PDF evidence when available. Missing evidence is allowed only if recorded.
6. Profile contracts are validation overlays. They do not change the JSON shape.

## Required Artifact Set

A Clean package that claims this contract should contain:

```text
clean.md
clean_standard.json
clean_contract_report.json
manifest.json
media_report.json
structure_report.json
images/
```

Recommended evidence artifacts:

```text
source_map.json
asset_manifest.json
raw_evidence_refs.json
```

`clean_standard.json` may embed the essential source map and asset records directly. Separate files are useful only when the package is large.

## Top-Level Shape

```json
{
  "schema": "luceon-clean-standard-document/v1",
  "material_id": "pdf-...",
  "source": {},
  "document": {},
  "outline": [],
  "blocks": [],
  "relations": [],
  "assets": [],
  "source_map": [],
  "contract": {}
}
```

The Standard compiler can rely on:

- stable block ids;
- explicit block types and subtypes;
- outline paths;
- relation edges;
- asset records;
- source references;
- review flags and blockers.

## Structural Blocks

The first version intentionally keeps the block vocabulary finite.

| Type | Meaning | Sample pressure |
| --- | --- | --- |
| `document_title` | book/title metadata rendered as body content when present | RE/GF/GIC |
| `front_matter` | contents, credits, intro, non-lesson book matter | G7+ front-matter classifier pressure |
| `unit` | large instructional division | RE/GF/GIC/G7+ |
| `chapter` | large instructional division for books that use chapters | Math 8A |
| `lesson` | teachable section inside unit/chapter | RE/GF/GIC/Math |
| `section` | named local section | all samples |
| `reading_passage` | continuous reading text | RE |
| `paragraph` | ordinary body paragraph | all samples |
| `explanation` | explanatory prose or instruction | grammar/math/workbook |
| `key_concept` | highlighted conceptual rule or summary | grammar/math |
| `grammar_box` | grammar rule/paradigm block | GF/GIC |
| `worked_example` | step/model/example explanation unit | G7+ math-heavy boundary, Math 8A |
| `example` | non-step example | grammar/math/workbook |
| `exercise_group` | prompt or instruction that owns questions | GF/GIC/G7+ |
| `question` | question or exercise item | RE/GF/GIC/G7+ |
| `option` | answer option | RE/GF/GIC/G7+ |
| `answer_blank` | blank line, checkbox, fill-in area, answer-space marker | GF/GIC/G7+ |
| `word_bank` | list of words/options used by an exercise | G7+ paired vocabulary |
| `vocabulary_item` | vocabulary term, definition, or use-in-writing item | RE/G7+ |
| `table` | semantic table preserved as table-like structure | all workbook/math samples |
| `formula` | display formula or formula-bearing standalone block | Math 8A |
| `figure` | educational image/diagram/photo | RE/GF/GIC/G7+ |
| `caption` | caption or local figure label | RE/G7+ |
| `diagram` | visual diagram with instructional semantics | math-heavy boundary |
| `note` | local note or callout | RE/GF |
| `sidebar` | side content that should stay attached to context | RE/GF |
| `icon` | helper/decorative marker, usually non-blocking | GF6 helper icons |
| `answer_key` | answer/reference content | workbooks |
| `metadata` | non-rendered or low-render-priority metadata | all samples |

Each block has:

```json
{
  "id": "b-000123",
  "type": "question",
  "subtype": "multiple_choice",
  "text": "What is the main idea?",
  "markdown": "1. What is the main idea?",
  "outline_path": ["Unit 1", "1A", "Reading Comprehension"],
  "source_refs": [],
  "asset_refs": [],
  "review_flags": [],
  "blockers": []
}
```

## Relations

Many sample failures are relation failures, not text extraction failures. Relations are first-class.

| Relation | Meaning | Sample pressure |
| --- | --- | --- |
| `contains` | parent contains child | all samples |
| `continues` | block continues previous block | G7+ question continuation |
| `has_option` | question owns option | RE/GF/GIC |
| `has_answer_blank` | question/example owns blank | GF/G7+ |
| `has_word_bank` | exercise owns word bank | G7+ paired vocabulary |
| `has_table` | exercise/example/explanation owns table | GF/G7+/Math |
| `has_formula` | block owns formula | Math 8A |
| `has_figure` | block owns figure | RE/GF/GIC/G7+ |
| `has_caption` | figure/table owns caption | RE/G7+ |
| `belongs_to_exercise` | item belongs to exercise group | GF/GIC/G7+ |
| `belongs_to_passage` | question belongs to reading passage or section | RE |
| `explains` | explanation/key concept explains target | grammar/math |
| `source_equivalent_to` | Clean block equivalent to source block | RE table closure, formula closure |
| `needs_review_against` | block needs comparison to source evidence | G7+/Math |
| `blocks_promotion` | relation or block blocks candidate/accepted promotion | G7+/Math |

Relation records are simple graph edges:

```json
{
  "id": "r-000123",
  "type": "has_option",
  "from": "b-000200",
  "to": "b-000201",
  "confidence": 0.98,
  "evidence_refs": ["src-000456"],
  "review_flags": []
}
```

## Source Evidence

Clean Standard must distinguish text structure from evidence.

```json
{
  "id": "src-000456",
  "block_id": "b-000123",
  "stage": "raw",
  "source_block_id": "content-list-000456",
  "page_index": 12,
  "page_number": 13,
  "bbox": [120, 210, 620, 260],
  "source_text": "source text when available",
  "source_image": "images/source-crop.png",
  "match": {
    "method": "exact_normalized_text",
    "status": "matched",
    "confidence": 1.0
  }
}
```

For Basic Print promotion, source evidence matters most for:

- tables;
- formula-bearing blocks;
- key figures/diagrams;
- corrections;
- dropped media;
- relation-sensitive table/figure groups.

## Assets

Assets are separate from blocks. A figure block references an asset; it is not the binary asset itself.

```json
{
  "id": "asset-000123",
  "kind": "image",
  "path": "images/photo.jpg",
  "role": "educational",
  "width": 640,
  "height": 420,
  "source_refs": ["src-000456"],
  "review_flags": []
}
```

Asset roles:

```text
educational
diagram
table_image
formula_image
helper_icon
decorative
unknown
```

Decorative/helper assets may be compactly rendered or excluded from visual confirmation, but this must be explicit.

## Review Flags And Blockers

Uncertainty is part of the contract.

Common `review_flags`:

```text
uncertain_block_type
uncertain_relation
missing_source_ref
missing_page_bbox
source_lineage_mismatch
source_crop_needed
source_crop_context_too_wide
manual_visual_review_needed
formula_visual_review_open
table_visual_review_open
image_visual_review_open
needs_reconstruction
decorative_media_decision
clean_review_scoped
math_heavy_boundary
candidate_only_not_accepted
accepted_golden_requires_promotion_record
```

Common `blockers`:

```text
hard_gate_failed
missing_required_artifact
missing_educational_media
outline_drift
source_fidelity_unverified
unresolved_blocking_review_outcomes
unresolved_relation_gaps
formula_page_bbox_gap
formula_containment_context_gap
digit_spacing_review
table_reconstruction_needed
math_profile_contract_missing
source_lineage_unresolved
```

## Profile Candidates

The Clean document may include profile candidates, but they are advisory. They do not alter the JSON shape.

```json
{
  "profile_candidates": [
    {
      "profile": "reading_textbook",
      "confidence": 0.94,
      "evidence": [
        {"signal": "reading_passage_count", "value": 24},
        {"signal": "comprehension_question_count", "value": 180}
      ]
    }
  ]
}
```

The Standard compiler applies profile contracts from `profile-contracts-v1.md`.

## Contract Status

`contract` summarizes whether Clean has produced a trustworthy intermediate document.

```json
{
  "status": "pass",
  "version": "v1",
  "required_artifacts": {
    "clean_md": "pass",
    "clean_standard_json": "pass",
    "images": "pass",
    "source_map": "review"
  },
  "blocker_count": 0,
  "review_flag_count": 12
}
```

Allowed statuses:

```text
pass
review
fail
```

`pass` means the Clean Standard document can be compiled directly by Standard.

`review` means Standard may produce a conservative review draft, but promotion requires scoping or closure.

`fail` means Standard must stop before Basic Print compilation.

## Completion Boundary

This standard is complete for v1 when every current research sample can be represented without sample-specific fields:

- RE1 as accepted reading textbook evidence;
- GF6/GF4/GIC as grammar workbook candidate/profile-ready evidence;
- G7+ as exercise workbook pressure evidence with math-heavy relation gaps;
- Math 8A as math textbook blocked evidence with formula/table/source evidence gaps.

Promotion status is not stored as a Clean truth. Promotion remains a corpus/golden decision.
