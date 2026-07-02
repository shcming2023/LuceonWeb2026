# Basic Print Readiness Matrix V0 - 2026-06-30

Purpose:

```text
Summarize the current Standard Basic Print validation state across profiles without confusing candidates, review pressure runs, accepted goldens, and blocked samples.
```

This document is a current-state matrix for the ongoing validation loop. It is not a release approval.

## Current Phase

```text
sample validation + corpus/golden formalization + profile blocker discovery
```

Reason:

- one accepted reading-textbook golden exists;
- `grammar_workbook` is profile-ready v0 from GF6/GF4/GIC, but no workbook sample is accepted golden;
- one non-Grammar-Friends `exercise_workbook` pressure run exists and remains review;
- math profile remains blocked because the compiler now exposes `math_textbook` and exact/surface-safe formula/table closure rules work, but `278` formula outcomes remain open behind page/bbox, containment-context, and digit-spacing blockers.

## Profile Matrix

| Profile | Current conclusion | Evidence | Blocking reason |
| --- | --- | --- | --- |
| `reading_textbook` | accepted golden exists | RE1 accepted golden, score 97, 15/15 review outcomes closed | Not enough to claim all reading textbooks, but sufficient first Basic Print golden |
| `grammar_workbook` | profile-ready v0, candidates not accepted golden | GF6/GF4/GIC candidates; GIC is non-Grammar-Friends | Accepted-golden promotion remains separate; exercise_workbook/math not covered |
| `exercise_workbook` | review pressure only, not candidate-ready | G7+ review run, score 94; paired-vocabulary blank-box subrule, stable table rule, virtual question grouping, question continuation, remaining-relation source-context packets, and contract-family decision audit all have evidence | 162 open review outcomes in main run; experimental relation reruns reduce real profile gaps `1811 -> 560 -> 551 -> 61 -> 36`; real ungrouped-question gaps are now `0`, and `36/36` remaining table/figure gaps have source-context packets; the `18` contract-review packets are `18/18` math-heavy profile-boundary cases, so no generic exercise_workbook table rerun is recommended |
| `math_textbook` | blocked/review | Math 8A selector v1 review run plus assignment bbox locators, stop audit, exact/surface-safe closures, and remaining formula blocker audit, score 86; selected profile is now `math_textbook` | `879/1157` formula/table visual outcomes are closed as `accepted_by_rule`, but `278` formula outcomes remain open: `159` page/bbox stop-boundary, `116` containment-context review, and `3` digit-spacing review |

## Case Matrix

### RE1

Status:

```text
basic_print_accepted
```

Evidence:

- case: `docs/standard-research/corpus/cases/pdf-e71fe159994b50f3.case.json`
- run: `docs/standard-research/corpus/runs/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.run.json`
- golden: `docs/standard-research/corpus/golden/accepted/pdf-e71fe159994b50f3.re1-review-outcome-v0-20260629.golden.json`
- artifact: `runtime/backend/pipeline-work/audits/re1-review-outcome-v0-rerun-20260629/standard-final`

Conclusion:

```text
Accepted Basic Print golden for reading_textbook.
```

### GF6

Status:

```text
basic_print_candidate
```

Evidence:

- case: `docs/standard-research/corpus/cases/pdf-ff4c7f59964ad54f.case.json`
- run: `docs/standard-research/corpus/runs/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.run.json`
- candidate: `docs/standard-research/corpus/golden/candidates/pdf-ff4c7f59964ad54f.gf6-workbook-regression-v1-20260629.candidate.json`
- artifact: `runtime/backend/pipeline-work/audits/gf6-workbook-profile-regression-v1-rerun-20260629/standard-final`

Conclusion:

```text
Grammar workbook candidate only; not accepted golden. It contributes to grammar_workbook profile-ready v0.
```

### GF4

Status:

```text
basic_print_candidate
```

Evidence:

- case: `docs/standard-research/corpus/cases/pdf-8ada74dfc6d2d66c.case.json`
- run: `docs/standard-research/corpus/runs/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.run.json`
- candidate: `docs/standard-research/corpus/golden/candidates/pdf-8ada74dfc6d2d66c.gf4-workbook-second-sample-v3-20260630.candidate.json`
- artifact: `runtime/backend/pipeline-work/audits/gf4-workbook-second-sample-v3-rerun-20260630/standard-final`

Conclusion:

```text
Grammar workbook candidate only; depends on evidence-backed source correction policy and remains not promoted.
```

Latest reconstruction audit:

```text
docs/standard-research/28-grammar-paradigm-table-rebuild-audit-v0.md
```

Result:

```text
The three GF4 V2 grammar-paradigm reconstruction blockers reflow under the profile-general table renderer, all collapsed fragments are removed, and GF4 V3 records the three outcomes as accepted. This validates the GF4 grammar-paradigm failure mode, but it is not a broad table rebuild rule and is separate from the later G7+ paired-vocabulary blank-preservation subrule closure.
```

### Grammar in Context

Status:

```text
basic_print_candidate
```

Evidence:

- case: `docs/standard-research/corpus/cases/pdf-01ae095f5a0f2dc7.case.json`
- run: `docs/standard-research/corpus/runs/pdf-01ae095f5a0f2dc7.gic-clean-blocked-v0-20260630.run.json`
- run: `docs/standard-research/corpus/runs/pdf-01ae095f5a0f2dc7.gic-clean-review-v3-20260630.run.json`
- run: `docs/standard-research/corpus/runs/pdf-01ae095f5a0f2dc7.gic-standard-upstream-limited-v0-20260630.run.json`
- run: `docs/standard-research/corpus/runs/pdf-01ae095f5a0f2dc7.gic-workbook-relation-rule-v8-20260630.run.json`
- raw artifact: `runtime/backend/pipeline-work/popo2raw/run-8-pdf-01ae095f5a0f2dc7-popo-20260617014256-staged_popo_20260617_batch07_sma-1369cfec--005-popo_01ae095f5a0f2dc7_005/body-final`
- clean artifact: `runtime/backend/pipeline-work/audits/gic-clean-v3-20260630/clean-final`
- standard artifact: `runtime/backend/pipeline-work/audits/gic-standard-upstream-limited-v0-rerun-20260630/standard-final`
- relation-hardening artifact: `runtime/backend/pipeline-work/audits/gic-standard-workbook-relation-rule-v8-20260630/standard-final`
- previous blocked attempts: `gic-clean-v0-20260630`, `gic-clean-v1-20260630`, and interrupted `gic-clean-v2-20260630`
- clean v3 status: `review`, hard failures `0`, review gates `media_review_threshold` and `llm_structure_revert_threshold`
- upstream-limited v0 Standard gate status after closure: `pass`, quality score `100`, PDF render `pass`, `308` pages, `0` unresolved blocking issue candidates, `377/377` review outcomes closed as `accepted_by_rule` (historical comparator, superseded for relation-hardening by v8)
- relation-hardening v8 status after source crop closure: Standard acceptance `pass`, quality score `100`, PDF render `pass`, `303` pages, workbook profile `pass`, `exercise_relation_contract` `pass`, `image_relation_contract` `pass`, `real_profile_gap_count` `0`, `question_groups` `415`, `orphan_table_questions` `0`
- v8 visual closure: `377/377` review outcomes closed as `accepted_by_rule`; image source crops `125`; table/formula visual source crops `252`; correction log records 4 source-crop-backed image replacements
- v8 Clean review scope: `clean_review_scope_report.json` generated by `backend/scripts/scope_clean_review_for_standard.py`; both Clean review gates are scoped for this Standard artifact, but not promoted to Clean pass
- v8 Clean closure policy: `runtime/backend/pipeline-work/audits/gic-clean-closure-policy-audit-v3-20260701/clean_review_closure_policy_audit.json` is `clean_review_closure_policy_pass`
- candidate record: `docs/standard-research/corpus/golden/candidates/pdf-01ae095f5a0f2dc7.gic-workbook-clean-closure-v3-20260701.candidate.json`
- cross-sample Clean scope audit: `docs/standard-research/25-clean-review-scope-cross-sample-v0.md`
- promotion boundary: GIC is candidate-only, not accepted golden; it contributes to grammar_workbook profile-ready v0

Conclusion:

```text
Preferred non-Grammar-Friends grammar workbook candidate now passes Standard gates, profile gates, and Clean closure policy. It is promoted to Basic Print candidate only, not accepted golden/profile-ready.
```

### G7+

Status:

```text
standard_review_pressure_run
```

Evidence:

- case: `docs/standard-research/corpus/cases/pdf-58860644b15e909c.case.json`
- run: `docs/standard-research/corpus/runs/pdf-58860644b15e909c.g7plus-non-gf-workbook-pressure-v0-20260630.run.json`
- artifact: `runtime/backend/pipeline-work/audits/g7plus-non-gf-workbook-pressure-v0-rerun-20260630/standard-final`
- blocker audit: `docs/standard-research/26-g7plus-exercise-workbook-blocker-audit-v0.md`
- local source PDF found: `runtime/backend/pipeline-work/popo2raw/run-29-pdf-58860644b15e909c-popo-20260618020631-staged_popo_20260618_batch13-97b1f8e5--002-popo_58860644b15e909c_002/rebuild_input/pdf-58860644b15e909c_origin.pdf`
- image source crop generation: completed with `1477/1477` image crops using `backend/scripts/generate_standard_image_source_crops_fast.py`; after source-crop-backed image replacement, image outcomes are now `1477/1477` closed as `accepted_by_rule`
- table/formula source crop generation: completed with `2712/2860` required visual crops using `backend/scripts/generate_standard_visual_source_crops_fast.py`; `3` image-only formula packets are non-blocking duplicate image-review coverage; remaining `148` formula visual outcomes still need page/bbox
- table/formula audit/closure: `2697` exact/compact/semantic-match table/formula outcomes are closed as `accepted_by_rule`; `3` image-only formula packets are closed as `non_blocking`; near-match table review split into `1` accepted and `1` needs_reconstruction; `2` table source-locator blockers now have source crops but remain manual layout review; remaining open outcomes are `162` total, including `11` formula layout-review/source-review blockers with generated source crops, `148` formula page-bbox gaps, `2` table layout-review items with source crops, and `1` table reconstruction blocker
- formula bbox/context candidate audit/backfill: `469/661` original formula page-bbox blockers had math-normalized source-location candidates; `443` same-unit and `26` global-only candidates were backfilled as source-location evidence and source crops were generated; `93` compact-match and `374` conservative semantic-key outcomes closed by rule, later context-window backfill converted `5` more formula page-bbox blockers into manual visual/layout review with source crops, and `4` deterministic formula semantic-equivalent outcomes were closed by explicit rule; preserving semantic formula tokens such as `sqrt`, `pi`, `ge/le`, `approx`, and `stackrel?=` found `12` additional same-unit source-location candidates, same-unit ordinal duplicate matching found `5` repeated-formula candidates, compact-exact Raw context matching found `10` context/formula candidates, short-procedure context matching found `5` unique step candidates, short option-formula context matching found `3` formula-option candidates, and unique same-unit page compact containment found `1` formula/text candidate; these source-location rules are manual review evidence first; cumulative formula semantic-equivalent closure now covers `32` outcomes, including `3` Markdown-emphasis-only false positives closed in the latest pass; `11` formula layout/source-review items remain open, including `5` deterministic semantic-key matches blocked by short-procedure source-location policy; `3` image-only formula packets were reclassified as non-blocking because closed image outcomes already cover them
- remaining bbox blocker audit: current `148` page-bbox blockers are formula-only, split into `143` no-match formula/text items, `3` ambiguous items, and `2` too-short items; no remaining formula item has a deterministic source-location candidate
- raw context-window locator audit: historical high-confidence/compact/short-procedure/short-option/containment candidates have been backfilled as manual-review source evidence and source crops were generated; the current remaining `143` no-match formula/text items contain `1` review context-window candidate, `39` weak candidates, and `103` no context candidate, so this is not a broad bbox closure/backfill rule
- raw context rule-stop audit: remaining `143` raw-context items are classified as unsafe for threshold-based backfill; stop buckets include no-candidate/manual reconstruction, near mismatches with different numbers/formulas, weak false positives/context gaps, and one OCR/tokenization review item
- relation gap pattern audit: `1811` real profile gaps remain; `1725` ungrouped questions form `1030` runs, with `740` question gaps behind known section labels or instruction paragraphs and `981` still requiring deeper grouping/state-machine boundary logic; `84` orphan table questions remain table grouping blockers
- grouping state-machine simulation: conservative starter-run grouping would cover `752` relation gaps and leave `1059`; persistent virtual grouping would cover `1805/1811`, but it is high-risk (`448` long paragraphs inside active groups and `82` tables attached only to active group); guarded grouping covers `1674/1811` and leaves `137`, including all `84` table gaps, so table attachment policy remains unresolved and G7+ status does not change
- table attachment policy simulation: `84` orphan table gaps split into `9` generic auto-attach candidates, `8` paired/vocabulary special layout-rule candidates, and `75` visual/manual review cases; this is audit-only evidence and confirms that a simple guarded grouping + table attach rule is not compiler-ready
- paired vocabulary table layout audit: the `8` paired/vocabulary candidates split into `1` two-table vocabulary/definition pair and `7` word-bank-plus-definition tables; these are promising subrule shapes, but require source visual confirmation before any compiler/profile rule
- paired vocabulary source confirmation: expanded source context crops confirm `8/8` paired vocabulary layouts, but this remains review evidence; `b-03276` keeps a reconstruction blocker because source blank boxes must be preserved
- paired vocabulary renderer contract audit: `8` source-confirmed records are ready for a compiler prototype contract, but current Standard render has `1` missing horizontal pair, `7` missing word-bank/table groups, `7` empty example-cell answer-space gaps, and `3` inline blank-width gaps; no gate can close before rendered HTML/PDF visual regression
- paired vocabulary renderer prototype: isolated prototype renders the `8` source-confirmed records with `24` answer spaces and `13` inline blanks, but it does not mutate main Standard output and keeps the `b-03276` reconstruction blocker
- paired vocabulary compiler-adjacent patch: isolated patched document/html covers `8` source-confirmed records and `9` orphan table gaps, projecting real profile gaps from `1811` to `1802`; its `b-03276` reconstruction sensitivity is superseded for blank preservation by the later real PDF rerun
- paired vocabulary formal compiler integration attempt: `standard-final-no-pdf-stub-v2` detects `9` groups and `10` table blocks, covering all `9` previously source-confirmed table ids and discovering `b-09582`; the delta source crop confirms the layout but shows missing inline source blank boxes, so a real PDF rerun was required before any subrule closure
- paired vocabulary blank-box preservation rerun: `g7plus-paired-vocab-blank-preservation-rerun-20260701/standard-final` preserves `6` source blank spans across `b-03276` and `b-09582`, has matching compiler/source table ids at `10/10`, and renders a real PDF with `736` pages
- paired vocabulary blank-box reconstruction audit: the narrow paired-vocabulary blank-box hard stop is closed by `36-g7plus-paired-vocabulary-blank-preservation-v0.md`, but G7+ remains review pressure because broader exercise relation, formula, table, and source-lineage blockers remain
- exercise relation delta audit: `37-g7plus-exercise-relation-delta-audit-v0.md` shows the paired-blank rerun removes `1251` real relation gaps with no added gaps, but the removed table-gap set mixes `9` paired-vocabulary tables with `26` high-risk baseline buckets, so it must be split into explicit contracts before compiler/profile promotion
- table attachment contract split: `38-g7plus-table-attachment-contract-audit-v0.md` says only `9` paired-vocabulary records are contract-ready; `2` non-paired low/medium records need source visual spot audit, `3` need visual review before contract, `15` are not proven, and `55` high-risk records stay review-only
- table attachment spot audit: `39-g7plus-table-attachment-spot-audit-v0.md` accepts the `2` non-paired source-context candidates as two narrow contract families, not as a broad instruction-table rule
- table attachment visual-review audit: `40-g7plus-table-attachment-visual-review-audit-v0.md` accepts `3` question-like table candidates as two narrow example-table families, not as a broad question-like table rule
- table attachment stable-gap audit: `41-g7plus-table-attachment-stable-gap-audit-v0.md` audits the `15` low/medium table gaps that stayed stable after the paired-vocabulary rerun; `9` are only narrow compiler-rule rerun candidates and `6` remain review, so no stable gap is closed and no broad table-attachment rule is allowed
- table attachment stable-rule rerun: `42-g7plus-table-attachment-stable-rule-rerun-v0.md` implements the `9` stable-gap candidates as narrow compiler rules, catches and removes one overbroad high-risk statistics match, and proves a clean relation delta of `560 -> 551` real profile gaps with `0` added gaps; this remains relation-rule evidence only
- virtual question grouping rerun: `43-g7plus-virtual-question-group-rerun-v0.md` implements guarded question-only virtual grouping and proves a clean relation delta of `551 -> 61` real profile gaps with `0` added gaps; it also absorbs `80` prior classifier-artifact questions, so classifier-boundary review remains required
- question continuation rerun: `44-g7plus-question-continuation-rerun-v0.md` implements same-heading numbered-question continuation across short/image interruptions and downgrades the front-matter TOPICS list; it proves a clean relation delta of `61 -> 36`, leaving real ungrouped-question gaps at `0`
- remaining relation source-context audit: `45-g7plus-remaining-relation-source-context-audit-v0.md` renders focused source-PDF context crops for all `36/36` remaining relation gaps; it splits them into `18` source-context contract-review packets and `18` keep-review packets, and confirms the next blocker is family-level table/figure relation/rendering policy rather than evidence plumbing
- contract family decision audit: `46-g7plus-contract-family-decision-audit-v0.md` classifies `18/18` source-context contract-review packets as math-heavy profile-boundary cases; it explicitly blocks a generic `exercise_workbook` table rule and redirects the next loop to math-heavy workbook/textbook relation contracts
- math-heavy profile boundary: `48-math-heavy-profile-boundary-v0.md` identifies the cross-sample boundary from G7+ and Math 8A evidence; ordinary `exercise_workbook` should not absorb math data/model/rule table families, and Math 8A needs a real math profile selector/contract before judgment
- cross-sample reconstruction audit: `5` unique reconstruction cases split into `2` G7+ blank-pattern cases and `3` GF4 grammar-paradigm table rebuild cases, so blank-box reconstruction must remain a narrow paired-vocabulary subtrack rather than a generic table reconstruction rule
- media/print refresh: HTML table `<img>` references are included in Standard media collection; current PDF render is `747` pages, `64,136,385` bytes, `2664` image refs, and `0` missing images

Conclusion:

```text
Non-Grammar-Friends exercise_workbook pressure evidence only; not candidate/golden.
```

### Math 8A

Status:

```text
math_profile_blocked_review
```

Evidence:

- case: `docs/standard-research/corpus/cases/pdf-aadfa33fb0485c1a.case.json`
- latest run: `docs/standard-research/corpus/runs/pdf-aadfa33fb0485c1a.math-remaining-exact-surface-closure-v0-20260701.run.json`
- latest artifact: `runtime/backend/pipeline-work/audits/math-profile-remaining-exact-surface-closure-rerun-20260701/standard-final`
- selector run: `docs/standard-research/corpus/runs/pdf-aadfa33fb0485c1a.math-profile-selector-v1-20260701.run.json`
- selector artifact: `runtime/backend/pipeline-work/audits/math-profile-selector-v1-rerun-20260701/standard-final`
- latest evidence artifact: `runtime/backend/pipeline-work/audits/math-profile-assignment-bbox-exact-rerun-20260701/standard-final`
- latest containment evidence artifact: `runtime/backend/pipeline-work/audits/math-profile-assignment-bbox-containment-rerun-20260701/standard-final`
- source evidence audit: `docs/standard-research/47-math8a-source-evidence-plumbing-v0.md`
- selector v1 audit: `docs/standard-research/49-math8a-profile-selector-v1-rerun.md`
- assignment bbox exact locator audit: `docs/standard-research/50-math8a-assignment-bbox-exact-locator-v0.md`
- assignment bbox containment locator audit: `docs/standard-research/51-math8a-assignment-bbox-containment-locator-v0.md`
- remaining bbox stop-boundary audit: `docs/standard-research/52-math8a-remaining-bbox-stop-boundary-v0.md`
- native exact content closure audit: `docs/standard-research/53-math8a-native-exact-content-closure-v0.md`
- raw-assignment exact safe closure audit: `docs/standard-research/54-math8a-raw-assignment-exact-safe-closure-v0.md`
- remaining exact-surface closure audit: `docs/standard-research/55-math8a-remaining-exact-surface-closure-v0.md`
- remaining formula blocker boundary audit: `docs/standard-research/56-math8a-remaining-formula-blocker-boundary-v0.md`

Conclusion:

```text
Math profile is blocked, not Basic Print candidate. The selector now chooses math_textbook, source evidence covers 998 formula/table outcomes for manual review, exact/surface-safe rules close 879 outcomes including all 4 table outcomes, and the remaining 278 formula blockers require subrow bbox, stronger source-location, or manual/vision review.
```

## Final Completion Criteria Status

| Criterion | Current status |
| --- | --- |
| RE1 / reading_textbook conclusion | satisfied for first accepted golden |
| grammar_workbook conclusion | profile-ready v0 for grammar workbook Basic Print compiler/profile contract; candidates remain not accepted golden |
| exercise_workbook conclusion | review pressure only, not candidate-ready |
| math profile conclusion | blocked/review |
| non-Grammar-Friends workbook sample | satisfied as GIC Basic Print candidate; G7+ remains exercise_workbook review pressure |
| corpus case/run/golden consistency | currently aligned by `29-corpus-status-consistency-audit-v1.md` |
| promotion hard stops | currently summarized by `30-promotion-hard-stop-matrix-v1.md`; base rules remain in `20-workbook-promotion-checklist-v0.md` |
| all conclusions have artifact paths | satisfied in this matrix |
| graphify update | must be rerun after this document changes |
| engineering release readiness | not satisfied |

## Current Overall Verdict

```text
Standard Basic Print is not ready for engineering release.
```

Why:

- only one accepted golden exists;
- `grammar_workbook` is profile-ready v0 from GF6/GF4/GIC, but none of the workbook candidates are accepted golden;
- non-Grammar-Friends exercise workbook pressure evidence remains review rather than candidate-ready;
- math profile selection is closed, but formula visual closure/reconstruction remains blocked;
- source PDF evidence and visual outcome closure remain major cross-profile risks.

## Next Best Loop

Recommended next loop:

```text
Move to exercise_workbook or math_textbook validation; grammar_workbook profile-ready v0 is closed, but accepted-golden promotion remains separate.
```

Why:

- GF6/GF4/GIC now answer grammar_workbook v0 generalization;
- G7+ now proves the exercise/math-heavy boundary: ordinary workbook question grouping improved, but the remaining table/figure relations are math-heavy worked-example/data/model cases;
- G7+ and Math 8A together now define the math-heavy boundary;
- math profile needs a separate profile engineering track before it can be fairly judged.

Stop condition:

- do not infer accepted-golden status from profile-ready v0.
