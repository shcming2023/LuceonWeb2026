# G7+ Exercise Workbook Blocker Audit V0 - 2026-06-30

Purpose:

```text
Classify the current `exercise_workbook` blocker surface using the non-Grammar-Friends G7+ pressure run, without trying to force the run to pass.
```

Sample:

- material: `pdf-58860644b15e909c / (7)G7+.pdf`
- profile: `exercise_workbook`
- run: `docs/standard-research/corpus/runs/pdf-58860644b15e909c.g7plus-non-gf-workbook-pressure-v0-20260630.run.json`
- artifact: `runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final`

## Current Status

```text
standard_review_pressure_run
```

This is not a Basic Print candidate and not a negative verdict on all workbook support.

## What Passes

- Standard artifact generation succeeded.
- Current PDF render succeeded: `747` pages, `64,136,385` bytes.
- media integrity passes after HTML table image-ref collection: `2664` image refs, `0` missing images.
- outline lock passes: Clean and Standard outline count `127`.
- source fidelity passes: Clean and Standard text hash match.
- correction evidence passes: correction count `276`, all with evidence.
- upstream Clean is `pass`; `clean_review_scope_report.json` says `clean_pass_no_scope_needed`.

## Main Blocker Classes

| Blocker class | Count / evidence | Meaning |
| --- | ---: | --- |
| Review outcomes open | `162/4340` open blocking | Image, exact/compact/semantic-match table/formula evidence, image-only formula reclassification, formula semantic-equivalent closure, and one manual table acceptance closed many outcomes; formula layout review, formula page-bbox gaps, table layout review, and one table reconstruction remain open |
| Formula visual review | `2493` accepted_by_rule, `3` non_blocking, `11` needs_layout_fix with source crops, `148` needs_page_bbox | Exact/compact/semantic source matches with crops are closed; image-only duplicate formula packets are non-blocking; 11 source-crop-backed formula outcomes remain manual visual/layout review |
| Table visual review | `204` accepted_by_rule, `1` accepted, `2` needs_layout_fix with source crops, `1` needs_reconstruction | Exact source matches with crops are closed; near-match review accepted one table, two table source-locator blockers now have crops for manual layout review, and one table still needs answer-blank reconstruction |
| Image source visual confirmation | `1477` accepted_by_rule, `0` open | Key figures now have source crops and source-crop-backed replacements where needed |
| Issue candidates unresolved blocking | `0` | Image issue candidates are now covered by visual outcomes |
| Exercise relation real profile gaps | `1811` | Includes `1725` ungrouped questions and `84` orphan table questions |
| Source evidence throughput | `1477/1477` image crops and `2712/2860` required table/formula crops generated | Source crop generation is no longer the main blocker for the backfilled table/formula outcomes; remaining blockers are manual formula/table layout review, formula missing bbox, or table reconstruction |

## Source PDF Evidence

The Standard run manifest has an empty `source_pdf` field, but a local PDF exists:

```text
runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf
```

Observed local source PDF:

- pages: `740`
- size: `234,093,495` bytes
- sha256: `ebe143e8d8424cdbb2cd78b96c2257f314d26d590541834075936bb39fcbc803`

Raw manifest source object:

- input object: `(7)G7+.pdf`
- recorded sha256: `58860644b15e909ccb03bb8ec32af14dc523ee418216080c4c4e17cc5e5ad84d`
- recorded size: `234,140,607` bytes

Risk:

```text
The local origin PDF is usable for source crops, but its hash/size differ from the raw manifest source object. Treat it as local rebuilt source evidence, not as proof of exact input-object identity, until the lineage is reconciled.
```

## Crop Generation Attempts

Command attempted:

```text
python3 backend/scripts/generate_standard_source_crops.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --source-pdf runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf
```

Historical result from the first visual-crop closure pass:

- manually interrupted with exit code `130`;
- partial output: `258` files in `source_crops/`, about `63M`;
- no `visual_source_crops/` were produced before interruption.

Interpretation:

```text
This first attempt proved the original generic crop path was too slow for the G7+ scale.
```

Second command:

```text
python3 backend/scripts/generate_standard_image_source_crops_fast.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --source-pdf runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf
```

Result:

- image source crop generation completed;
- `1477/1477` image crops generated;
- first full fast run rendered `451` pages and took `1730.75` seconds;
- subsequent resume/reuse run reused `1477` crops in `0.006` seconds.

Interpretation:

```text
Image source evidence throughput is no longer blocked for this sample, but it is still expensive enough to require async/review-artifact treatment.
```

Third command:

```text
python3 backend/scripts/generate_standard_visual_source_crops_fast.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --source-pdf runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf
```

Result:

- table/formula visual source crop generation completed for every outcome with page/bbox;
- `2198/2863` visual crops generated or reused in the first full run;
- after Raw near-match bbox backfill, `2200/2863` visual crops are generated or reused;
- `663` visual outcomes remained `needs_page_bbox` at that point;
- first full visual crop run rendered `454` pages and took `1509.274` seconds;
- subsequent resume/reuse run reused `2198` crops in `0.013` seconds.

Interpretation:

```text
Table/formula source crop evidence is now available where page/bbox exists. It enables a separate deterministic closure audit, but it is not itself a Basic Print pass.
```

## Table/Formula Outcome Audit And Closure

This section records the first exact-match table/formula closure pass. Later formula bbox backfill and formula semantic-key closure reduced the current open count further; see the formula source-location section below for current counts.

Audit command:

```text
python3 backend/scripts/audit_standard_table_formula_outcomes.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Audit result:

| Bucket | Count |
| --- | ---: |
| `deterministic_closure_candidate_exact_match` | `2198` |
| `needs_page_bbox` | `663` |
| `needs_manual_visual_review_source_mismatch` | `2` |

Closure command:

```text
python3 backend/scripts/close_standard_table_formula_outcomes_from_audit.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Closure result:

| Outcome class | Closed | Open blocking |
| --- | ---: | ---: |
| `formula_visual_review` | `1994` | `661` |
| `table_visual_review` | `204` | `4` |

Historical interpretation:

```text
The 2198 table/formula closures are accepted_by_rule, not human visual final approval. They are allowed only because each item has exact normalized source content match plus generated/reused source crop evidence. At this historical checkpoint, G7+ remained review because 663 table/formula outcomes still lacked page/bbox or source-location evidence and 1 table outcome needed answer-blank reconstruction.
```

## Missing Bbox Fallback Audit

Audit/apply command:

```text
python3 backend/scripts/backfill_standard_visual_bbox_from_raw.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --apply
```

Result:

| Backfill status | Count |
| --- | ---: |
| `formula_visual_review:unlocated` | `661` |
| `table_visual_review:unlocated` | `2` |
| `table_visual_review:located` | `2` |

The two located table items use:

```text
raw_content_list.table_near_match_for_manual_review
```

This is source-location evidence only. It creates source crops and keeps the outcomes open as manual visual review blockers.

## Outcome Evidence Breakdown

Current state from `standard_review_outcomes.json`:

| Packet type | Has page+bbox | Missing page/bbox | Total |
| --- | ---: | ---: | ---: |
| `formula_visual_review` | `2507` | `148` | `2655` |
| `table_visual_review` | `208` | `0` | `208` |
| `image_source_visual_confirmation` | `1477` | `0` | `1477` |

Implications:

- image locator evidence was sufficient for `1477/1477` image crops;
- table/formula locator evidence is sufficient for `2712/2860` required visual crops;
- `148` formula outcomes still need page/bbox or alternate evidence;
- `2697` table/formula outcomes are closed as `accepted_by_rule` by exact, compact, or formula semantic-key rules;
- `11` formula source-review/layout-review outcomes, `2` table layout-review outcomes, and `1` table reconstruction outcome remain open with source crops.

## Image Outcome Closure

After image crop generation and source-crop-backed image replacement:

| Image outcome decision | Count |
| --- | ---: |
| `accepted_by_rule` | `1477` |
| `needs_reconstruction` | `0` |

Closed image issues:

| Issue | Count |
| --- | ---: |
| `standard_source_aspect_ratio_mismatch` | `229` |
| `standard_image_too_small_for_basic_print` | `47` |

Image closure reduces unresolved issue candidates from `1477` to `0` and closes all `1477` image outcomes as `accepted_by_rule`. Later table/formula, formula semantic-key, context-window evidence, image-only reclassification, formula semantic-equivalent closure, refined formula-token source-location, same-unit ordinal duplicate, compact-exact Raw context, short-procedure context, short option-formula context, and one compact-containment context pass reduce page-bbox blockers further, but `162` open review outcomes remain: `148` formula page-bbox gaps, `11` source-crop-backed formula layout/source-review items, `2` table layout-review items, and `1` table reconstruction blocker.

## Relation Evidence Breakdown

From `workbook_relation_audit.json`:

| Kind | Disposition | Count |
| --- | --- | ---: |
| `ungrouped_question` | `real_profile_gap` | `1725` |
| `orphan_table_question` | `real_profile_gap` | `84` |
| `orphan_figure_relation_candidate` | `real_profile_gap` | `2` |
| `orphan_figure_relation_candidate` | `helper_icon_artifact` | `764` |
| `orphan_figure_relation_candidate` | `explanation_artifact` | `483` |
| `unparented_explanation_table` | `explanation_artifact` | `1` |

This means `exercise_workbook` has real grouping failures that cannot be solved by source crops or image replacement alone.

## Relation Gap Pattern Audit

Audit command:

```text
python3 backend/scripts/audit_standard_workbook_relation_gap_patterns.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Audit artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/workbook_relation_gap_pattern_audit.json
```

Current pattern summary:

| Pattern | Count |
| --- | ---: |
| real profile gaps | `1811` |
| ungrouped questions | `1725` |
| ungrouped question runs | `1030` |
| orphan table questions | `84` |
| question gaps behind known section labels | `584` |
| question gaps behind instruction paragraphs | `156` |
| question gaps with unknown/manual boundary | `981` |

Interpretation:

```text
The dominant exercise_workbook blocker is profile grouping/state-machine design. A narrow section-label/instruction rule would explain 740 question gaps, but 981 question gaps still require deeper boundary logic because figures, answer blanks, formulas, options, and partial question context interrupt the numbered runs. This is not a source-crop problem and should not be forced green by suppressing relation gaps.
```

## Grouping State-Machine Simulation

Simulation command:

```text
python3 backend/scripts/audit_standard_workbook_grouping_state_machine_simulation.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Simulation artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/workbook_grouping_state_machine_simulation.json
```

Simulation results:

| Model | Covered gaps | Remaining gaps | Risk |
| --- | ---: | ---: | --- |
| conservative starter-run grouping | `752` | `1059` | safer, but leaves most interrupted runs unresolved |
| persistent virtual group until section/new starter | `1805` | `6` | high risk: `448` long paragraphs inside active groups, `82` tables attached only to active group |
| guarded virtual group with long-paragraph reset and table requires active question | `1674` | `137` | lower grouping risk, but leaves all `84` table gaps unresolved |

Decision:

```text
The persistent state-machine is promising profile-engineering evidence but not compiler-ready. Guarded grouping reduces the long-paragraph/table-group-only risk but still leaves 137 gaps, including all 84 table gaps. The next profile-engineering loop should isolate table attachment policy instead of merging the persistent model into the compiler. This simulation does not change G7+ acceptance, corpus status, or Basic Print readiness.
```

## Table Attachment Policy Simulation

Simulation command:

```text
python3 backend/scripts/audit_standard_workbook_table_attachment_policy_simulation.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Simulation artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/workbook_table_attachment_policy_simulation.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/workbook_table_attachment_policy_simulation.html
```

Policy bucket results:

| Bucket | Count |
| --- | ---: |
| `auto_attach_instruction_table_candidate` | `8` |
| `auto_attach_adjacent_question_candidate` | `1` |
| `paired_vocabulary_table_needs_layout_rule` | `8` |
| `question_like_paragraph_table_needs_visual_review` | `12` |
| `explanation_or_step_table_keep_review` | `17` |
| `manual_review_or_compiler_boundary_gap` | `38` |

Risk and shape summary:

| Metric | Count |
| --- | ---: |
| table gaps | `84` |
| auto-attach candidates | `9` |
| special paired-layout rule candidates | `8` |
| visual/manual review cases | `75` |
| high-risk cases | `55` |
| medium-risk cases | `28` |
| low-risk cases | `1` |
| data tables | `31` |
| blank-answer tables | `30` |
| math tables | `12` |
| vocabulary/definition tables | `11` |

Decision:

```text
The table policy is not compiler-ready. Only 9/84 orphan table gaps have a generic auto-attach signal, while 8 need paired-table/vocabulary layout semantics and 75 still need visual/manual review or stronger grouping boundaries. This confirms that guarded grouping plus a simple table-attach rule is insufficient for exercise_workbook promotion. The simulation is audit-only and does not change G7+ acceptance, corpus status, or Basic Print readiness.
```

## Paired Vocabulary Table Layout Audit

Audit command:

```text
python3 backend/scripts/audit_standard_workbook_paired_vocabulary_table_layout.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Audit artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/workbook_paired_vocabulary_table_layout_audit.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/workbook_paired_vocabulary_table_layout_audit.html
```

Layout buckets:

| Layout bucket | Count | Meaning |
| --- | ---: | --- |
| `two_table_vocabulary_definition_pair` | `1` | A `Vocabulary Word` table followed by a matching `Definition` table; likely needs horizontal paired-table rendering |
| `word_bank_paragraphs_plus_definition_table` | `7` | Short preceding word-bank paragraphs plus a `Definition/Example` table; likely needs word-bank grouping plus table rendering |

Decision:

```text
The paired/vocabulary subset has two stable subrule shapes, but this is still not a compiler change. The next safe step is source visual confirmation for these 8 records, because the rule must preserve the original vocabulary matching layout and must not silently absorb unrelated short paragraphs into an exercise group. These 8 records remain relation-gap evidence, not closed gaps.
```

## Paired Vocabulary Source Confirmation

Confirmation command:

```text
python3 backend/scripts/build_standard_paired_vocabulary_source_confirmation.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --source-pdf runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf
```

Confirmation artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_source_confirmation.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_source_confirmation.html
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_source_context_contact_sheet.png
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_source_context_crops/
```

Result:

| Evidence | Count |
| --- | ---: |
| source context crop ready | `8/8` |
| source layout visually confirmed | `8/8` |
| two-table vocabulary/definition pair confirmed | `1` |
| word-bank plus Definition/Example table confirmed | `7` |
| known content reconstruction blockers retained | `1` |

Decision:

```text
The source visual confirmation supports two real layout subrules for this subset. At this point it did not close relation gaps or change G7+ acceptance. In particular, b-03276 remained a table reconstruction blocker because visual source evidence showed answer-blank boxes that must be preserved for Basic Print. The blank-preservation part is superseded by the later real PDF rerun; the pass-promotion boundary remains unchanged.
```

## Paired Vocabulary Renderer Contract Audit

Contract audit command:

```text
python3 backend/scripts/audit_standard_paired_vocabulary_renderer_contract.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Contract artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_renderer_contract_audit.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_renderer_contract_audit.html
```

Current render gaps:

| Gap | Count |
| --- | ---: |
| `two_table_pair_not_rendered_as_horizontal_pair_group` | `1` |
| `word_bank_and_definition_table_not_rendered_as_single_group` | `7` |
| `empty_example_cells_need_printable_answer_space` | `7` |
| `inline_underscore_blanks_need_preserved_blank_width` | `3` |

Contract requirements:

| Requirement | Meaning |
| --- | --- |
| `paired_vocab_group_boundary` | Source-confirmed instruction, word bank/table pair, definition table, and immediate follow-up label must become one reviewable exercise group |
| `two_table_horizontal_pair` | Vocabulary Word and Definition tables must render as a side-by-side matching pair only when source bbox evidence supports that layout |
| `word_bank_definition_table` | Short word-bank paragraphs must stay visually tied to the Definition/Example table |
| `blank_box_preservation` | Empty example cells, underline blanks, and source blank boxes must remain printable answer spaces |

Decision:

```text
The paired vocabulary subset was ready for a compiler prototype contract, not for gate closure at this point in the audit. This section is superseded for blank-box preservation by the later real PDF rerun recorded in `36-g7plus-paired-vocabulary-blank-preservation-v0.md`; the broader rule remains that no relation gap or reconstruction outcome may close unless rendered Standard HTML/PDF preserves source-confirmed grouping, layout, and answer spaces.
```

## Paired Vocabulary Renderer Prototype

Prototype command:

```text
python3 backend/scripts/prototype_standard_paired_vocabulary_renderer.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Prototype artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_renderer_prototype_report.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_renderer_prototype.html
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_renderer_prototype_screenshot.png
```

Prototype result:

| Metric | Count |
| --- | ---: |
| source-confirmed records rendered | `8` |
| two-table pair renders | `1` |
| word-bank/table renders | `7` |
| prototype answer spaces | `24` |
| prototype inline blanks | `13` |
| reconstruction blockers retained | `1` |

Visual sanity:

```text
The prototype renders the source-confirmed paired vocabulary layouts and visible answer spaces. A first screenshot check also caught and fixed a prototype-only math autowrap regression in table cells. At this point, b-03276 remained reconstruction-sensitive because source blank boxes inside definition text were not automatically reconstructed from Standard table text. That prototype did not mutate standard.html, close relation gaps, or change G7+ acceptance; the later real PDF rerun closes only the blank-preservation subrule.
```

## Paired Vocabulary Compiler-Adjacent Patch

Patch command:

```text
python3 backend/scripts/apply_standard_paired_vocabulary_compiler_patch.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Patch artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_compiler_patch/paired_vocabulary_compiler_patch_report.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_compiler_patch/patched_standard_document.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_compiler_patch/patched_standard.html
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_compiler_patch/patched_groups_preview.html
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_compiler_patch/patched_groups_preview_screenshot.png
```

Patch result:

| Metric | Count |
| --- | ---: |
| source-confirmed paired vocabulary groups | `8` |
| patched table blocks | `9` |
| projected orphan table gaps removed | `9` |
| remaining original orphan table gaps | `75` |
| projected real profile gaps after patch | `1802` |
| reconstruction blockers retained | `1` |

Decision:

```text
The compiler-adjacent patch proves that the source-confirmed paired vocabulary subset covers 9 orphan table gaps, not 8, because the first layout is a two-table vocabulary/definition pair. The patch is scope-contained: it writes isolated patched document/html/preview artifacts, leaves main standard_document.json and standard.html unchanged, and limits answer-space rendering to paired vocabulary group tables. It was ready for a main compiler integration experiment; the later real PDF rerun closes the blank-preservation subrule, while broader G7+ gates remain review.
```

## Paired Vocabulary Formal Compiler Integration Attempt

Compiler changes:

```text
backend/scripts/standard_from_clean.py
backend/tests/test_standard_from_clean.py
backend/scripts/audit_standard_paired_vocabulary_compiler_evidence.py
```

Validation artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_report.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_compiler_evidence_audit.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_compiler_delta_source_confirmation.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_compiler_delta_source_confirmation.html
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_source_context_crops/b-09582-word_bank_paragraphs_plus_definition_table.png
```

Run boundary:

```text
The real Chrome PDF rerun wrote partial Standard artifacts but was interrupted inside render_pdf after several minutes. Therefore the completed evidence is the no-pdf-stub-v2 run: it validates document structure, HTML, paired-vocabulary reporting, relation/profile metrics, and source-crop delta evidence, but it is not a real PDF visual regression or release-quality Standard run.
```

Stub-v2 result:

| Metric | Count / status |
| --- | ---: |
| acceptance status | `review` |
| quality score | `85` |
| paired vocabulary groups | `9` |
| paired vocabulary table blocks | `10` |
| compiler/source-confirmed table ids | `9` |
| compiler-only table ids needing source confirmation | `1` (`b-09582`) |
| source-only table ids missed by compiler | `0` |
| real profile gaps | `560` |
| orphan table question metric | `36` |
| PDF evidence | `stubbed_pdf_render_for_relation_and_html_validation` |

Compiler evidence audit:

```text
The first formal rule pass exposed a generic-window bug: b-11020 had eight preceding word-bank entries, so the old context window excluded the Vocabulary label/review context. The rule was corrected by widening the generic look-back window, and a regression test now covers long word banks without using block IDs, page numbers, filenames, or material IDs.
```

Source delta result:

```text
The compiler found b-09582 as an additional real Vocabulary Review word-bank plus Definition/Example table. A generated expanded source crop confirms the source layout, but visual inspection also shows inline blank boxes inside the Definition cells. Those blank boxes are missing from Standard table text, so b-09582 joins b-03276 as a reconstruction-sensitive blocker. This moves the paired-vocabulary problem from grouping/layout only to blank-box reconstruction plus real PDF visual regression.
```

Decision:

```text
The formal compiler integration was promising but not gate-closing. It covers the old source-confirmed paired-vocabulary table set, fixes the long-word-bank miss, and discovers one additional valid source layout. At this point, both b-03276 and b-09582 required reconstruction-sensitive source blank-box preservation and the completed run used a PDF stub. This is superseded for the narrow blank-preservation subrule by the later real PDF rerun; G7+ remains a review pressure sample, not a candidate golden or exercise_workbook profile pass.
```

## Paired Vocabulary Blank-Box Reconstruction Audit

Audit command:

```text
python3 backend/scripts/audit_standard_paired_vocabulary_blank_box_reconstruction.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2 --source-report runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/paired_vocabulary_source_confirmation.json --source-report runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_compiler_delta_source_confirmation.json
```

Audit artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_blank_box_reconstruction_audit.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_blank_box_reconstruction_audit.html
```

Result:

| Metric | Count |
| --- | ---: |
| compiler paired-vocabulary table ids | `10` |
| source-confirmed paired-vocabulary table ids | `10` |
| source-confirmed records | `9` |
| known blank-box reconstruction blockers | `2` |

Known blockers:

```text
b-03276
b-09582
```

Decision:

```text
This closed the evidence mismatch between compiler grouping and source confirmation: the compiler table set and source-confirmed table set matched. It did not close the profile. At this point, the remaining hard stop was source blank-box reconstruction because source visual evidence showed inline blank boxes absent from Standard table text/rendering. That hard stop is now superseded for paired-vocabulary by the real PDF blank-preservation rerun below; it is not a profile promotion.
```

## Paired Vocabulary Blank Reconstruction Prototype

Prototype command:

```text
python3 backend/scripts/prototype_standard_paired_vocabulary_blank_reconstruction.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2
```

Prototype artifacts:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_blank_reconstruction_prototype/paired_vocabulary_blank_reconstruction_prototype_report.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-paired-vocab-compiler-rerun-20260701/standard-final-no-pdf-stub-v2/paired_vocabulary_blank_reconstruction_prototype/paired_vocabulary_blank_reconstruction_prototype.html
```

Prototype result:

| Metric | Count |
| --- | ---: |
| reconstruction blocker records | `2` |
| pattern-reconstructable records | `2` |
| reconstructed blank boxes | `6` |
| reconstructed table cells | `6` |

Candidate rules:

```text
leading_you_when
leading_a_is
leading_the_states
use_the_to
terminal_is_an
```

Decision:

```text
The prototype showed that the two known G7+ paired-vocabulary blank-box blockers were recoverable by a very small conservative text-pattern surface, and the rendered prototype preserved comparison symbols by escaping cell text before inserting visual blanks. The later cross-sample audit kept this as a narrow paired-vocabulary subrule, and the later real PDF rerun closed only that subrule, not the exercise_workbook profile.
```

## Formula Bbox Candidate Audit

After image closure, the largest remaining visual blocker class is formula source location:

```text
Before same-unit formula bbox backfill, 661 formula_visual_review outcomes needed page/bbox.
```

Audit command:

```text
python3 backend/scripts/audit_standard_formula_bbox_candidates.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Audit artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/formula_bbox_candidate_audit.json
```

Result:

| Bucket | Count |
| --- | ---: |
| `source_location_candidate_math_exact_unique_same_unit` | `443` |
| `source_location_candidate_math_exact_unique_global` | `26` |
| `ambiguous_math_normalized_match` | `13` |
| `ambiguous_short_global_match_needs_manual` | `2` |
| `no_math_normalized_raw_match` | `167` |
| `too_short_for_location_rule` | `7` |
| `non_formula_image_alt_or_empty_after_normalization` | `3` |

Interpretation:

```text
Math-normalized matching can locate 469 formula outcomes as source-location candidates. Joining `raw_block_assignments.jsonl` by `content_list_index + 1` with type/page/bbox cross-check gives unit evidence for 443 same-unit candidates, but this is still audit-only source-location evidence and not automatic accepted_by_rule closure.
```

Decision:

```text
The 443 same-unit candidates and 26 global-only candidates have now been backfilled as manual-review source evidence and generated source crops. Later audits closed 93 compact deterministic closure candidates and 374 conservative formula semantic-key matches as accepted_by_rule. Two same-unit/global backfilled formulas stayed open as needs_layout_fix/manual visual review; a later context-window pass added 5 more source-crop-backed manual-review formulas, of which 4 deterministic semantic-equivalent formulas were then closed by explicit rule. This is not a blanket closure of the backfilled set, and global-only or context-window source-location evidence does not prove exercise grouping correctness.
```

Backfill and crop evidence:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/formula_bbox_backfill_report.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/formula_bbox_global_backfill_report.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/formula_source_mismatch_audit.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/visual_source_crop_audit.json
```

Refined formula-token locator follow-up:

```text
python3 backend/scripts/audit_standard_formula_bbox_candidates.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
python3 backend/scripts/backfill_standard_formula_bbox_candidates.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --candidate-bucket source_location_candidate_math_exact_unique_same_unit --apply
python3 backend/scripts/generate_standard_visual_source_crops_fast.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --source-pdf runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf --only-ready-for-source-crop
python3 backend/scripts/close_standard_review_outcomes.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --skip-source-crop-refresh
```

The formula source-location key now preserves semantic LaTeX command tokens such as `sqrt`, `pi`, `ge/le`, `approx`, and `stackrel?=`. This converted `12` previously ambiguous formula bbox blockers into same-unit unique source-location candidates. They were backfilled and cropped as manual review evidence only, so `needs_page_bbox` fell from `184` to `172`, while formula `needs_layout_fix` rose from `3` to `15`. This is not an accepted_by_rule closure.

Same-unit ordinal duplicate locator follow-up:

```text
python3 backend/scripts/backfill_standard_formula_ordinal_bbox_candidates.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --apply
python3 backend/scripts/generate_standard_visual_source_crops_fast.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --source-pdf runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf --only-ready-for-source-crop
python3 backend/scripts/close_standard_review_outcomes.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --skip-source-crop-refresh
```

This locator only accepts duplicate formulas when same-unit open outcome count equals same-unit Raw candidate count, then maps clean block order to Raw `source_order`. It backfilled `5` additional formula bboxes and generated crops as manual review evidence only, reducing `needs_page_bbox` from `172` to `167` and increasing formula `needs_layout_fix` from `15` to `20`. Cross-unit, count-mismatch, and short-formula cases remain review.

Compact-exact Raw context follow-up:

```text
python3 backend/scripts/backfill_standard_raw_context_exact_bbox_candidates.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --apply
python3 backend/scripts/generate_standard_visual_source_crops_fast.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --source-pdf runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf --only-ready-for-source-crop
python3 backend/scripts/close_standard_review_outcomes.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --skip-source-crop-refresh
```

This locator only accepts same-unit Raw context windows whose compact normalized text exactly equals the clean block compact text. It backfilled `10` additional formula/text bboxes and generated crops as manual review evidence only, reducing `needs_page_bbox` from `167` to `157` and increasing formula `needs_layout_fix` from `20` to `30`. Similar-but-not-exact, weak, no-candidate, and ambiguous context cases remain review.

Short-procedure Raw context follow-up:

```text
python3 backend/scripts/backfill_standard_raw_context_short_procedure_bbox_candidates.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --apply
python3 backend/scripts/generate_standard_visual_source_crops_fast.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --source-pdf runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf --only-ready-for-source-crop
python3 backend/scripts/close_standard_review_outcomes.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --skip-source-crop-refresh
```

This locator only accepts short procedure text whose compact key starts with `step`, has a unique same-unit Raw row, and is not a short formula. It backfilled `5` additional step bboxes and generated crops as manual review evidence only, reducing `needs_page_bbox` from `157` to `152` and increasing formula `needs_layout_fix` from `30` to `35`.

Short option-formula Raw context follow-up:

```text
python3 backend/scripts/backfill_standard_raw_context_short_option_formula_bbox_candidates.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --apply
python3 backend/scripts/generate_standard_visual_source_crops_fast.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --source-pdf runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf --only-ready-for-source-crop
python3 backend/scripts/close_standard_review_outcomes.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --skip-source-crop-refresh
```

This locator only accepts short option-letter formula text with a unique same-unit compact-exact Raw context window. It backfilled `3` additional option-formula bboxes and generated crops as manual review evidence only, reducing `needs_page_bbox` from `152` to `149` and increasing formula `needs_layout_fix` from `35` to `38`.

Refined follow-up evidence:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/formula_bbox_precision_token_backfill_report.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/formula_bbox_ordinal_backfill_report.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/raw_context_exact_bbox_backfill_report.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/raw_context_short_procedure_bbox_backfill_report.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/raw_context_short_option_formula_bbox_backfill_report.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/formula_bbox_candidate_audit.json
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/visual_source_crop_audit.json
```

Current post-backfill state:

| Bucket | Count |
| --- | ---: |
| `formula_visual_review accepted_by_rule` | `2493` |
| `formula_visual_review non_blocking image-only duplicate` | `3` |
| `formula_visual_review needs_layout_fix with source crop` | `11` |
| `formula_visual_review needs_page_bbox` | `148` |
| `table_visual_review accepted_by_rule` | `204` |
| `table_visual_review accepted` | `1` |
| `table_visual_review needs_layout_fix with source crop` | `2` |
| `table_visual_review needs_reconstruction` | `1` |

## Remaining Bbox Blocker Audit

Audit command:

```text
python3 backend/scripts/audit_standard_remaining_bbox_blockers.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Audit artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/remaining_bbox_blocker_audit.json
```

Current remaining `needs_page_bbox` blockers:

| Class | Count | Next action |
| --- | ---: | --- |
| `no_math_normalized_raw_match` | `143` | requires Raw text-sequence or context-window locator; no unique formula source-location candidate exists |
| `ambiguous_math_normalized_match` | `1` | requires manual candidate selection or a disambiguation rule |
| `too_short_for_location_rule` | `2` | requires context-window locator or manual crop review |
| `ambiguous_short_global_match_needs_manual` | `2` | requires manual review of short global candidate |

Interpretation:

```text
The remaining 148 page-bbox blockers are formula-only and are not one homogeneous bbox problem. No remaining formula item has a deterministic source-location candidate after preserving semantic formula tokens, applying same-unit ordinal duplicate matching, compact-exact Raw context matching, short-procedure context matching, short option-formula context matching, and same-unit page compact-containment matching, so the next safe work is stricter context-window/source-sequence locator design plus formula/manual disambiguation, not another broad formula backfill.
```

## Raw Context-Window Locator Audit

Audit command:

```text
python3 backend/scripts/audit_standard_raw_context_bbox_candidates.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Audit artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/raw_context_bbox_candidate_audit.json
```

Current result for the `143` no-match formula/text items:

| Context-window bucket | Count |
| --- | ---: |
| `context_window_candidate_review` | `1` |
| `context_window_candidate_weak` | `39` |
| `no_context_candidate` | `103` |

Interpretation:

```text
The context-window locator can surface a small number of plausible source bbox candidates, but it is not yet a closure or broad backfill rule. High-confidence candidates are review evidence only until source crops and visual/semantic checks confirm them. Weak and no-candidate items remain blocking.
```

Post-backfill state:

```text
The 5 high-confidence context-window candidates, 10 compact-exact same-unit context candidates, 5 short-procedure context candidates, 3 short option-formula context candidates, and 1 same-unit page compact-containment candidate were backfilled as manual-review source evidence and source crops were generated. They remain open as needs_layout_fix/manual review, not accepted_by_rule. The remaining raw context-window audit now covers 143 no-match formula/text blockers: 1 review candidate, 39 weak candidates, and 103 no-candidate items.
```

## Raw Context Containment Backfill

Audit/apply command:

```text
python3 backend/scripts/backfill_standard_raw_context_containment_bbox_candidates.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --apply
```

Backfill artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/raw_context_containment_bbox_backfill_report.json
```

Result:

```text
The rule requires exactly one same-unit page whose compact Raw text contains the clean compact text. It found 1 candidate, b-11634, and backfilled page/bbox/source crop as manual review evidence only. This reduced formula needs_page_bbox from 149 to 148 and increased formula needs_layout_fix from 10 to 11. It did not close the outcome because the source crop covers the larger Raw question context.
```

## Raw Context Rule-Stop Audit

At this point, the remaining raw-context candidates are not safe to advance by lowering similarity thresholds. The audit is explicit and non-closing:

```text
python3 backend/scripts/audit_standard_raw_context_rule_stop.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final
```

Artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/raw_context_rule_stop_audit.json
```

Current rule-stop buckets:

| Stop bucket | Count | Meaning |
| --- | ---: | --- |
| `no_candidate_requires_manual_or_source_reconstruction` | `86` | no deterministic same-unit Raw context-window candidate |
| `weak_false_positive_different_numbers` | `33` | similar wording but formula/numeric content differs |
| `no_candidate_near_mismatch_different_numbers` | `17` | near text exists but numeric content differs |
| `weak_false_positive_or_context_gap` | `5` | weak match is insufficient for automatic source-location evidence |
| `weak_formula_spacing_or_tokenization_review` | `1` | near OCR/tokenization issue, still not a general rule |
| `review_candidate_token_overlap_only` | `1` | token overlap is high but sequence/location evidence is insufficient |

Decision:

```text
Stop expanding Raw context locator rules by threshold. Remaining weak/no-candidate items must stay review/blocking unless a future deterministic rule with exact source evidence is introduced. This protects Basic Print fidelity from formula/number substitutions that look superficially similar.
```

## Image-Only Formula Packet Classification

The remaining bbox audit exposed 3 `formula_visual_review` packets whose clean block is a Markdown image-only line and whose math appears only inside image alt text:

| Outcome | Clean shape |
| --- | --- |
| `visual:formula_visual_review:b-00936` | image-only Markdown, alt includes `6 ft × 8 \frac{1}{2} ft` |
| `visual:formula_visual_review:b-01409` | image-only Markdown, alt includes `${12}^{3}$ cubic inches` |
| `visual:formula_visual_review:b-07917` | image-only Markdown, alt describes a transformation diagram |

Compiler rule:

```text
Image-only Markdown/HTML blocks should not create formula_visual_review packets merely because alt text contains math notation. They belong to image relation or image visual confirmation review. Mixed text+image blocks with formula-bearing surrounding text may still require formula/table review.
```

Validation artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-image-only-formula-rule-v0-20260701/standard-final
```

Validation and closure result:

```text
The rule validation run reduced visual packets from 2863 to 2860 and removed b-00936, b-01409, and b-07917 from standard_visual_review_packets.json. The validation run itself remains fail because it does not inherit the main run's source-crop/outcome closure artifacts and print_render failed, so it is rule evidence only, not a candidate or promotion run.

The main G7+ artifact was then closed with backend/scripts/close_image_only_formula_outcomes.py. The script closed exactly 3 formula_visual_review outcomes as non_blocking only because each block is image-only and has a paired closed accepted_by_rule image_source_visual_confirmation outcome with source crop evidence. This reduces open blockers from 197 to 194 and page-bbox blockers from 189 to 186, without promoting the sample.
```

## Formula Semantic-Equivalent Closure

After image-only formula reclassification and later source-location backfills, 38 source-crop-backed formula layout/source-review outcomes remained. Formula semantic-equivalent closure now has two evidence-backed layers: first, allowed source-location rules closed deterministic formula semantic-key matches; second, Markdown emphasis markers are stripped from the semantic key, which closed 3 compact-exact same-unit false positives where `**bold**` markup was the only mismatch.

Closure command:

```text
python3 backend/scripts/close_standard_formula_semantic_equivalent_outcomes.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --apply
```

Closure artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/formula_semantic_equivalent_closure_report.json
```

Closure result:

```text
Cumulative formula semantic-equivalent closure now covers 32 outcomes as accepted_by_rule. The current closure report is a dry-run with 0 closable candidates and 5 skipped deterministic semantic-key matches because short-procedure source-location evidence is intentionally not an allowed closure rule. The rule requires deterministic semantic-key equality, an allowed source-location rule, source page/bbox, and a generated/reused source crop. The allowed source-location rules are exact Raw content-list formula semantic-key match, math-normalized same-unit unique/ordinal duplicate matches, compact-exact same-unit Raw context, high-confidence Raw context, and short option-formula compact-exact Raw context. The current post-containment `formula_source_mismatch_audit.json` has 11 remaining items: 5 deterministic semantic-key matches blocked by short-procedure source-location policy, 4 near-equivalent manual-review items, and 2 semantic mismatches.
```

## Table Source-Locator Backfill

The remaining bbox audit also had 2 `table_visual_review` page-bbox blockers. Both matched Raw table bodies after extracting the HTML `<table>...</table>` body and comparing compact table text.

Backfill command:

```text
python3 backend/scripts/backfill_standard_table_source_candidates.py --standard-dir runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final --apply
```

Backfill artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final/table_source_candidate_backfill_report.json
```

Crop result:

```text
2 table source crops were generated. The table bbox blockers are now manual layout-review items, not accepted_by_rule. This is important because b-01584's source crop shows answer boxes while the Standard HTML table has empty cells, so visual/layout reconstruction may still be needed.
```

Remaining formula layout-review items:

| Outcome | Reason to keep review |
| --- | --- |
| `visual:formula_visual_review:b-01945` | near-equivalent context-window source match; keep manual review until the context-window rule is promoted beyond source-location evidence |
| `visual:formula_visual_review:b-09622` | semantic key differs: clean `20^2+b^2=29^2`, source key `202+b^2=292`; source crop needed for visual confirmation before any closure |
| `visual:formula_visual_review:b-09824` | near-equivalent key with suspected extra OCR symbol `nabla`; keep manual review rather than treating it as deterministic |

This table is illustrative rather than exhaustive; the authoritative current list is `formula_source_mismatch_audit.json`.

## Decision

```text
G7+ remains review pressure evidence.
```

It should not be promoted to candidate or used to claim `exercise_workbook` readiness.

Current `exercise_workbook` conclusion:

```text
review pressure only, not candidate-ready
```

Primary next blockers:

1. define and validate exercise_workbook grouping/state-machine rules for dense math/exercise pages, starting from the `workbook_relation_gap_pattern_audit.json` buckets;
2. define Raw text-sequence/context-window locator and classification policy before trying to close the remaining `148` formula page-bbox outcomes;
3. review/reconstruct the table visual blockers: 2 source-crop-backed table layout items plus 1 table outcome with missing answer blanks;
4. keep image source-crop replacements as correction-evidenced closures, not as human visual final approval;
5. reconcile local source PDF lineage before using generated crops for accepted-golden promotion.

## Paired Vocabulary Blank Preservation Closure

After the isolated prototype and cross-sample audit, the paired-vocabulary blank-box preservation rule was integrated into the Standard compiler and rerun with real PDF rendering.

Rerun artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-paired-vocab-blank-preservation-rerun-20260701/standard-final
```

Closure audit:

```text
runtime/backend/pipeline-work/audits/g7plus-paired-vocab-blank-preservation-rerun-20260701/standard-final/paired_vocabulary_blank_box_reconstruction_audit.json
```

Result:

| Metric | Value |
| --- | ---: |
| compiler/source paired-vocabulary table ids match | `true` |
| real PDF render ok | `true` |
| PDF page count | `736` |
| source blank spans preserved in prior blockers | `6` |
| resolved blocker table ids | `b-03276`, `b-09582` |
| remaining paired-vocabulary blank-box blockers | `0` |

Decision:

```text
Close the paired-vocabulary blank-box subrule only.
```

This does not change the G7+ profile status. The rerun acceptance status remains `review` with quality score `85`, source crops were not regenerated in that rerun, and the broader G7+ blockers remain relation grouping, table attachment, formula/table visual review, source PDF lineage, and math-heavy exercise behavior.

## Exercise Relation Delta Audit

After the paired-vocabulary blank-preservation rerun, relation metrics improved enough to require a separate delta audit.

Audit artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-relation-delta-audit-20260701/workbook_relation_delta_audit.json
```

Comparison:

| Metric | Base pressure run | Paired-blank rerun | Delta |
| --- | ---: | ---: | ---: |
| real profile gaps | `1811` | `560` | `-1251` |
| removed real profile gaps |  |  | `1251` |
| added real profile gaps |  |  | `0` |
| removed ungrouped-question gaps |  |  | `1210` |
| removed orphan-table gaps |  |  | `40` |
| stable orphan-table gaps |  |  | `44` |

Removed table-gap buckets:

| Bucket | Count |
| --- | ---: |
| paired-vocabulary compiler rule | `9` |
| high-risk baseline buckets | `26` |
| medium-risk baseline buckets | `14` |

Decision:

```text
profile_contract_candidate_status = not_ready_high_risk_relation_delta_needs_rule_split
```

This is stronger evidence that the `exercise_workbook` profile needs real engineering, but it is not a compiler-ready rule. The safe next step is to split the delta into three contracts: paired-vocabulary, low/medium-risk instruction or adjacent-question table attachment, and high-risk explanation/manual table movement. The high-risk set must remain review until source visual evidence proves there is no semantic table/question misbinding.

## Table Attachment Contract Split

Audit artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-contract-audit-20260701/workbook_table_attachment_contract_audit.json
```

Result:

| Contract status | Count |
| --- | ---: |
| paired-vocabulary contract-ready only | `9` |
| non-paired source visual spot-audit candidates | `2` |
| visual-review-before-contract candidates | `3` |
| not-proven stable low/medium gaps | `15` |
| high-risk review-only | `55` |

Decision:

```text
can_add_paired_vocabulary_contract = true
can_add_broad_table_attachment_rule = false
can_promote_exercise_workbook_profile = false
```

The only contract-ready table attachment subset is paired vocabulary. Non-paired low/medium movement must go through source visual spot audit before any compiler/profile contract. High-risk table movement remains review-only.

## Table Attachment Source-Context Spot Audit

Audit artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-spot-audit-20260701/workbook_table_attachment_spot_audit.json
```

Result:

| Block | Contract family | Decision |
| --- | --- | --- |
| `b-04401` | `example_step_data_table_keep_with_explanation` | accepted for narrow contract by source context |
| `b-08745` | `single_table_vocabulary_review` | accepted for narrow contract by source context |

Decision:

```text
can_add_non_paired_spot_contracts = true
can_add_broad_table_attachment_rule = false
can_promote_exercise_workbook_profile = false
```

The spot audit splits the 2 non-paired candidates into two narrow source-context families. This does not authorize generic instruction-table attachment. The 3 question-like visual-review candidates, 15 stable low/medium gaps, and 55 high-risk table gaps remain outside the contract.

## Table Attachment Visual-Review Contract Audit

Audit artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-visual-review-audit-20260701/workbook_table_attachment_visual_review_audit.json
```

Result:

| Block | Contract family | Decision |
| --- | --- | --- |
| `b-06288` | `example_relative_frequency_question_table_explanation` | accepted for narrow contract by source context |
| `b-06296` | `example_relative_frequency_question_table_explanation` | accepted for narrow contract by source context |
| `b-12383` | `example_statistics_question_table_explanation` | accepted for narrow contract by source context |

Decision:

```text
can_add_visual_reviewed_example_table_contracts = true
can_add_broad_question_like_table_rule = false
can_promote_exercise_workbook_profile = false
```

The visual-review audit accepts only three narrow example-table families. It does not close the stable low/medium table gaps and does not authorize a generic question-like table attachment rule.

## Table Attachment Stable-Gap Audit

Audit artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-stable-gap-audit-20260701/workbook_table_attachment_stable_gap_audit.json
```

Result:

| Metric | Count |
| --- | ---: |
| stable low/medium gaps audited | `15` |
| narrow contract candidates requiring compiler rerun | `9` |
| keep review | `6` |

Decision:

```text
can_close_stable_table_gaps = false
can_add_contract_without_compiler_rerun = false
can_add_broad_table_attachment_rule = false
can_promote_exercise_workbook_profile = false
```

These 15 gaps are still real `orphan_table_question` relation gaps. Their table visual outcomes being `accepted_by_rule` only proves deterministic source-content/crop evidence for table rendering; it does not prove workbook relation grouping. The safe next step is to encode only narrow rule candidates, rerun G7+, and compare whether relation gaps close without new table/question misbinding.

## Table Attachment Stable-Rule Rerun

Experimental run:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-stable-rule-rerun-20260701/standard-final
```

Delta audit:

```text
runtime/backend/pipeline-work/audits/g7plus-table-attachment-stable-rule-delta-20260701/workbook_relation_delta_audit.json
```

Result:

| Metric | Base paired-blank rerun | Stable-rule rerun | Delta |
| --- | ---: | ---: | ---: |
| real profile gaps | `560` | `551` | `-9` |
| orphan table questions | `36` | `27` | `-9` |
| ungrouped questions | `600` | `600` | `0` |
| added real profile gaps |  |  | `0` |

The implemented table attachment report attaches `9` table blocks across `6` narrow source-context families. A first attempt overmatched high-risk table `b-12491`; the rule was tightened so the statistics summary family must be triggered by an explicit preceding explanation/question sentence rather than a short title. This confirms the rule needs rerun-based verification and cannot be promoted directly from review inspection.

Decision:

```text
profile_contract_candidate_status = candidate_rule_needs_full_acceptance_rerun
can_promote_exercise_workbook_profile = false
can_treat_current_run_as_basic_print_candidate = false
```

The stable-rule rerun is a valid relation-subtrack improvement, but G7+ remains review pressure because `551` real relation gaps remain and the experiment rerun does not replay the main run's source-crop/review-outcome closure chain.

## Virtual Question Group Rerun

Experimental run:

```text
runtime/backend/pipeline-work/audits/g7plus-virtual-question-group-rerun-20260701/standard-final
```

Delta audit:

```text
runtime/backend/pipeline-work/audits/g7plus-virtual-question-group-delta-20260701/workbook_relation_delta_audit.json
```

Effects audit:

```text
runtime/backend/pipeline-work/audits/g7plus-virtual-question-group-effects-audit-20260701/workbook_virtual_group_effects_audit.json
```

Result:

| Metric | Base stable-table rerun | Virtual-group rerun | Delta |
| --- | ---: | ---: | ---: |
| real profile gaps | `551` | `61` | `-490` |
| real ungrouped-question gaps removed |  |  | `490` |
| added real profile gaps |  |  | `0` |
| virtual groups with children |  | `163` |  |
| grouped question blocks |  | `570` |  |

The rule is question-only: it starts guarded virtual groups from workbook section labels, instruction paragraphs, or short colon labels; resets on hard sections and long non-instruction paragraphs; and does not attach tables, figures, options, or answer blanks.

Classifier-boundary finding:

| Prior base disposition absorbed by grouping | Count |
| --- | ---: |
| `real_profile_gap` | `490` |
| `explanation_artifact` | `80` |

The `80` absorbed prior artifact items were labeled `numbered_grammar_explanation_not_exercise_item`, but spot evidence shows many are ordinary math exercise questions. This is a classifier-boundary risk and must be reviewed before profile promotion.

Remaining relation gaps after this rerun:

| Kind | Count |
| --- | ---: |
| real ungrouped questions | `25` |
| real orphan table questions | `35` |
| real orphan figure relation candidates | `1` |

Decision:

```text
can_promote_exercise_workbook_profile = false
can_treat_virtual_grouping_as_full_acceptance = false
```

The virtual question grouping rule is a major profile-engineering improvement, but it does not make G7+ candidate-ready because remaining relation gaps, table grouping, classifier-boundary review, and full source/review closure replay are still open.

## Question Continuation Rerun

Experimental run:

```text
runtime/backend/pipeline-work/audits/g7plus-question-continuation-rerun-20260701/standard-final
```

Delta audit:

```text
runtime/backend/pipeline-work/audits/g7plus-question-continuation-delta-20260701/workbook_relation_delta_audit.json
```

Remaining gap audit:

```text
runtime/backend/pipeline-work/audits/g7plus-remaining-relation-gap-audit-v2-20260701/workbook_remaining_relation_gap_audit.json
```

Result:

| Metric | Base virtual-group rerun | Question-continuation rerun | Delta |
| --- | ---: | ---: | ---: |
| real profile gaps | `61` | `36` | `-25` |
| real ungrouped-question gaps | `25` | `0` | `-25` |
| added real profile gaps |  |  | `0` |
| continuation groups |  | `7` |  |
| grouped question blocks |  | `29` |  |

The question-continuation rule groups same-heading numbered questions across short option fragments, captioned-figure interruptions, and 3-Act modeling runs. A separate front-matter classifier downgrade removes the no-heading `TOPICS` list from real profile gaps without grouping it as an exercise.

Remaining relation gaps after this rerun:

| Kind | Count |
| --- | ---: |
| real orphan table questions | `35` |
| real orphan figure relation candidates | `1` |

Decision:

```text
can_promote_exercise_workbook_profile = false
can_treat_current_run_as_basic_print_candidate = false
```

The question side is now closed at the relation-audit level. The remaining profile blocker is table/figure relation semantics plus the unreplayed source-crop/review-outcome closure chain.

## Remaining Relation Source Context Audit

Audit artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-remaining-relation-source-context-audit-20260701/workbook_remaining_relation_source_context_audit.json
```

HTML review packet:

```text
runtime/backend/pipeline-work/audits/g7plus-remaining-relation-source-context-audit-20260701/workbook_remaining_relation_source_context_audit.html
```

Result:

| Metric | Count |
| --- | ---: |
| remaining relation records | `36` |
| records with source page/bbox | `36` |
| generated source context crops | `72` |
| contract-review packets | `18` |
| keep-review packets | `18` |

Decision:

```text
can_close_remaining_relation_gaps = false
can_promote_exercise_workbook_profile = false
```

Spot source inspection shows that the remaining gaps include math explanation diagrams, model tables, probability data/figure combinations, and unclassified table gaps. They are not safe to close as generic workbook table attachment merely because source context exists.

## Contract Family Decision Audit

Audit artifact:

```text
runtime/backend/pipeline-work/audits/g7plus-contract-family-decision-audit-20260701/workbook_contract_family_decision_audit.json
```

HTML review packet:

```text
runtime/backend/pipeline-work/audits/g7plus-contract-family-decision-audit-20260701/workbook_contract_family_decision_audit.html
```

Result:

| Metric | Count |
| --- | ---: |
| contract-review packets audited | `18` |
| math-heavy profile-boundary packets | `18` |
| generic exercise_workbook rerun candidates | `0` |

Decision:

```text
generic_exercise_workbook_rerun_recommended = false
can_add_generic_exercise_workbook_table_rule = false
```

Interpretation:

The remaining source-context contract packets are all math-heavy relation families: classification/number-system visuals, worked-example model tables, graph/data tables, frequency/probability data, transformation rule tables, and figure/table compound units. These should feed a math-heavy workbook/textbook contract decision, not a broader `exercise_workbook` rule.

## Next Loop

Shortest next loop:

```text
Define the math-heavy workbook/textbook relation contract boundary using G7+ plus the existing Math 8A blocked sample. Decide whether this is an exercise_workbook subprofile or part of math_textbook before any compiler rerun. Do not promote the sample to candidate.
```

Stop condition:

- if source PDF lineage cannot be reconciled, keep visual outcomes open for manual review;
- do not close formula outcomes by text-only rules until math/formula reconstruction policy exists.
