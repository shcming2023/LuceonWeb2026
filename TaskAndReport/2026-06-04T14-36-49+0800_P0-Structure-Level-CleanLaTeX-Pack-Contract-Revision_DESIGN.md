# Structure-Level CleanLaTeX Pack Contract Revision

Task ID: TASK-20260604-143649-P0-Structure-Level-CleanLaTeX-Pack-Contract-Revision

## 1. Core Correction

The previous design was directionally correct about source-bound packs, but too likely to become textbook-type specific by naming the primary pack as `section` and the secondary pack as `exercise`.

The revised principle is:

```text
Pack boundaries are chosen by structure and source-span stability, not by semantic labels.
```

Semantic labels such as `section`, `lesson`, `topic`, `grammar focus`, `exercise`, `activity`, `课`, or `节` may guide prompts and validation, but they must not be the primary boundary rule.

## 2. Upstream And Downstream Contract

Upstream remains:

```text
MinerU
  -> parsed artifacts, markdown, images/formulas/tables/source evidence
MinerU-Popo
  -> official structural normalization tree
Luceon Layer 3 deterministic rules
  -> canonical_toc.json
  -> chapter_spans.json
  -> rawlatex_scaffold.json
```

Downstream becomes:

```text
canonical node tree
  -> structure-level cleaning unit selection
  -> cleaning_unit_pack.json
  -> derived prompt.md
  -> bounded CleanLaTeX output
  -> chapter/book assembly
```

CleanLaTeX must clean inside selected source-bound structural units only. It must not decide whole-book structure.

## 3. Cleaning Unit Model

Primary object:

```text
cleaning_unit_pack
```

Schema id:

```text
luceon-cleanlatex-cleaning-unit-pack/v1
```

The pack has both structural and semantic metadata:

```json
{
  "schema": "luceon-cleanlatex-cleaning-unit-pack/v1",
  "pack_id": "cleaning-unit:toc-0002",
  "material_id": "4134323036518274",
  "asset_version": "v327-conservative-chapter-inference-a800-math-2022-prod-uat",
  "node": {
    "node_id": "toc-0002",
    "canonical_kind": "section",
    "semantic_label": "section",
    "title": "1.1 Different types of numbers",
    "number": "1.1",
    "parent_id": "toc-0001",
    "parent_title": "1 Review of number concepts",
    "ancestor_path": [
      {"node_id": "toc-unit-1", "canonical_kind": "unit", "title": "Unit 1"},
      {"node_id": "toc-chapter-1", "canonical_kind": "chapter", "title": "1 Review of number concepts"}
    ]
  },
  "pack_boundary": {
    "pack_level": 3,
    "pack_role": "primary_cleaning_unit",
    "boundary_basis": "structure-level",
    "selection_reason": [
      "stable_parent",
      "continuous_source_span",
      "content_size_within_limit",
      "children_can_inline_or_split"
    ],
    "semantic_kind_is_boundary_driver": false
  },
  "source_span": {},
  "content_blocks": [],
  "child_units": [],
  "assets": {},
  "cleaning_contract": {},
  "expected_output": {}
}
```

## 4. Pack Level

`pack_level` is derived from canonical tree depth after excluding root.

Example:

```text
level 1: unit / part / volume-level grouping
level 2: chapter / lesson-group / major topic
level 3: section / lesson / topic / text / grammar focus
level 4: exercise / activity / worked example / question group
level 5+: subquestion / fragment / small content cluster
```

The names are examples only. The decision uses the level, source span, and size, not the English or Chinese title.

## 5. Pack Selection Policy

Schema id:

```text
luceon-cleanlatex-pack-selection-policy/v1
```

Default policy:

```json
{
  "schema": "luceon-cleanlatex-pack-selection-policy/v1",
  "primary_candidate_levels": [3, 4],
  "assembly_levels": [1, 2],
  "inline_child_levels": [4, 5],
  "hard_limits": {
    "max_pages": 8,
    "max_blocks": 120,
    "max_chars": 18000,
    "max_images": 12,
    "max_tables": 8,
    "max_formulas": 80
  },
  "soft_targets": {
    "target_pages": 1,
    "target_blocks": 40,
    "target_chars": 6000
  },
  "selection_order": [
    "source_span_continuity",
    "stable_parent_boundary",
    "content_size",
    "child_count",
    "asset_density",
    "semantic_hint"
  ]
}
```

Selection rules:

1. Exclude root.
2. Prefer mid-level structural nodes whose source span is continuous and whose size fits limits.
3. Treat upper-level nodes as assembly containers when they are too large.
4. Treat tiny child nodes as inline content when they are too small to clean alone.
5. Split large child nodes into child packs only when size/asset density requires it.
6. Use semantic kind only as a hint for prompt rules, never as the main boundary decision.

## 6. Split Policy

Split a candidate node when any hard limit is exceeded:

```text
page count > max_pages
or block count > max_blocks
or text chars > max_chars
or image/table/formula density exceeds limits
or child count is too large for one prompt
```

Split order:

1. Prefer existing child structural nodes.
2. If child nodes are absent, split by contiguous source-order windows.
3. Preserve page/source-order continuity where possible.
4. Every split pack keeps the same parent node and records `split_from_node_id`.
5. Do not split across asset-caption or formula-context pairs when detectable.

Split metadata:

```json
{
  "split": {
    "split_from_node_id": "toc-0002",
    "split_index": 1,
    "split_count": 3,
    "reason": "max_blocks_exceeded",
    "source_order_range": [120, 160]
  }
}
```

## 7. Merge Policy

Merge tiny nodes into their parent or adjacent sibling when:

```text
block count < 3
and no independent asset/table/formula group
and no stable child structure
and parent pack remains within hard limits
```

Merge rules:

1. Preserve the original node as a `merged_child_unit`.
2. Keep its `node_id`, title, and source block IDs.
3. Do not erase the canonical tree node.
4. Do not merge across chapter/major parent boundaries.
5. Do not merge if the node is an important assessment unit and would become ambiguous.

Merge metadata:

```json
{
  "merged_child_units": [
    {
      "node_id": "toc-0145",
      "canonical_kind": "exercise",
      "title": "Exercise 1.1",
      "source_block_ids": []
    }
  ]
}
```

## 8. Cleaning Contract

The cleaning contract is boundary-first:

```json
{
  "unit": "cleaning_unit",
  "may_clean_ocr_text": true,
  "may_normalize_math_latex": true,
  "may_reorder_within_pack": true,
  "must_not_change_node_id": true,
  "must_not_change_parent_id": true,
  "must_not_create_or_delete_book_structure": true,
  "must_not_move_blocks_outside_pack": true,
  "must_preserve_source_block_ids": true,
  "must_preserve_asset_hash_names": true,
  "must_report_unresolved_items": true,
  "semantic_guidance": {
    "canonical_kind": "section",
    "do_not_answer_questions": true
  }
}
```

Semantic guidance affects cleaning behavior but not pack boundary selection.

For example:

- `exercise` may set `do_not_answer_questions=true`.
- `table`-heavy packs may request standard LaTeX table output.
- `grammar focus` may request examples and rules to be preserved.
- Chinese `课文` may request paragraph/dialogue preservation.

These are prompt constraints, not boundary authority.

## 9. Content Block Schema

`content_blocks[]` must preserve source order and stable references:

```json
{
  "block_id": "191",
  "source_order": 12,
  "page": 16,
  "bbox": [0.1, 0.2, 0.3, 0.4],
  "type": "text",
  "raw_text": "...",
  "source_hash": "sha256:...",
  "warnings": []
}
```

Allowed `type` values are deliberately structural/content-oriented, not curriculum-specific:

- `title`
- `text`
- `formula`
- `table`
- `image`
- `list`
- `caption`
- `footnote`
- `question_like`
- `example_like`
- `unknown`

## 10. Prompt Contract

`prompt.md` is derived from `cleaning_unit_pack.json` and is not source truth.

Required prompt framing:

```text
You clean exactly one source-bound structural cleaning unit.
The node semantic label is only guidance.
You must not alter book structure or pack boundaries.
You must preserve source block ids and asset hash names.
Return JSON matching luceon-cleanlatex-output/v1.
```

The prompt must include:

- node id;
- pack level;
- parent/ancestor path;
- source page range;
- source block IDs;
- content blocks in source order;
- asset hash names;
- unresolved warnings;
- forbidden operations.

## 11. CleanLaTeX Output Contract

Schema id:

```text
luceon-cleanlatex-output/v1
```

Required shape:

```json
{
  "schema": "luceon-cleanlatex-output/v1",
  "pack_id": "cleaning-unit:toc-0002",
  "node_id": "toc-0002",
  "pack_level": 3,
  "canonical_kind": "section",
  "title": "1.1 Different types of numbers",
  "source_block_ids_consumed": [],
  "source_block_ids_unresolved": [],
  "source_block_ids_omitted": [],
  "asset_hashes_used": [],
  "latex": "...",
  "unresolved_items": [],
  "warnings": [],
  "quality_self_check": {
    "no_structure_change": true,
    "no_asset_rename": true,
    "no_unreferenced_source_blocks": true
  }
}
```

LaTeX constraints:

- Use standard LaTeX only.
- Do not define custom commands.
- Preserve original asset hash names in image references.
- Mark unresolved blocks explicitly instead of inventing content.

## 12. Source Preservation Rules

1. Every pack has stable `pack_id` and `node_id`.
2. Every source block is consumed, unresolved, or omitted with reason.
3. Consumed/unresolved/omitted block IDs must cover input block IDs.
4. Source order changes must be reported.
5. Page/bbox evidence stays in validation manifests.
6. LLM must not create source claims without block IDs.

## 13. Asset Hash Preservation Rules

1. Image/audio/resource filenames are immutable.
2. Asset references must use original hash names exactly.
3. No descriptive, shortened, translated, or normalized asset filenames.
4. Unplaced assets must be listed in unresolved items.
5. Validation compares input asset hash names with output used/unresolved hash names.
6. The pack generator must not copy assets to new hash names.

## 14. Validation Manifest

Each pack should emit:

```json
{
  "schema": "luceon-cleanlatex-validation-manifest/v1",
  "pack_id": "cleaning-unit:toc-0002",
  "pack_level": 3,
  "selection_policy": "luceon-cleanlatex-pack-selection-policy/v1",
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

## 15. Pilot Selection

Pilot A:

```text
1.1 Different types of numbers
```

Pilot B:

```text
4.1 Colectingand classifyingdata
```

They are selected because:

- both are mid-level structural nodes under stable chapter parents;
- both have bounded source spans;
- both are expected to fit one cleaning unit pack;
- they exercise different source conditions;
- `4.1` confirms the newly inferred Chapter 4 boundary works for downstream pack selection.

They are not selected merely because they are called `section`.

## 16. Cross-Genre Robustness

This design should support:

- math textbooks;
- Chinese textbooks;
- English grammar textbooks;
- science textbooks;
- workbooks;
- exam-prep books.

It does so by relying on:

- tree depth;
- parent/child stability;
- source span continuity;
- block/page/asset counts;
- split/merge rules.

It does not require all books to use `section` or `exercise` labels.

## 17. Next Implementation Task

Recommended next task:

```text
P0 Source-Bound Cleaning Unit Pack Generator For CleanLaTeX Pilot
```

Narrow goal:

- Implement pack generation for the two pilot nodes `1.1` and `4.1`.
- Use v327 `canonical_toc`, `chapter_spans`, `official_popo_tree`, and MinerU parsed artifacts.
- Produce `cleaning_unit_pack.json`, derived `prompt.md`, source excerpt, asset manifest, and validation manifest.
- Do not call LLM until separately authorized.
