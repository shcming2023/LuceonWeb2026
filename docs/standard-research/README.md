# Standard Basic Print Research

This directory defines and tracks Luceon's Standard Basic Print research track.

Start here:

1. `00-kickoff.md`
2. `01-current-state-audit.md`
3. `03-basic-print-definition.md`
4. `06-next-implementation-plan.md`
5. `07-gf6-rerun-review.md`
6. `08-profile-v0.md`
7. `09-image-relation-gate-v0.md`
8. `10-image-visual-confirmation-packets-v0.md`
9. `11-review-outcome-schema-v0.md`
10. `12-re1-basic-print-promotion.md`
11. `13-gf6-workbook-regression-loop-v1.md`
12. `14-gf6-basic-print-candidate-review.md`
13. `15-gf4-workbook-second-sample-v2.md`
14. `16-table-source-evidence-fallback-v0.md`
15. `17-grammar-paradigm-table-rendering-v0.md`
16. `18-source-fidelity-correction-policy-v0.md`
17. `19-workbook-candidate-consolidation-v0.md`
18. `20-workbook-promotion-checklist-v0.md`
19. `21-corpus-status-consistency-audit-v0.md`
20. `22-workbook-promotion-review-draft-v0.md`
21. `23-third-workbook-pressure-sample-selection-v0.md`
22. `24-basic-print-readiness-matrix-v0.md`
23. `25-clean-review-scope-cross-sample-v0.md`
24. `26-g7plus-exercise-workbook-blocker-audit-v0.md`
25. `27-blank-reconstruction-cross-sample-audit-v0.md`
26. `28-grammar-paradigm-table-rebuild-audit-v0.md`
27. `29-corpus-status-consistency-audit-v1.md`
28. `30-promotion-hard-stop-matrix-v1.md`
29. `31-gic-clean-promotion-blocker-audit-v0.md`
30. `32-gic-clean-closure-policy-audit-v0.md`
31. `33-gic-clean-media-purpose-ledger-v0.md`
32. `34-gic-basic-print-candidate-promotion-v0.md`
33. `35-grammar-workbook-profile-ready-v0.md`
34. `36-g7plus-paired-vocabulary-blank-preservation-v0.md`
35. `37-g7plus-exercise-relation-delta-audit-v0.md`
36. `38-g7plus-table-attachment-contract-audit-v0.md`
37. `39-g7plus-table-attachment-spot-audit-v0.md`
38. `40-g7plus-table-attachment-visual-review-audit-v0.md`
39. `41-g7plus-table-attachment-stable-gap-audit-v0.md`
40. `42-g7plus-table-attachment-stable-rule-rerun-v0.md`
41. `43-g7plus-virtual-question-group-rerun-v0.md`
42. `44-g7plus-question-continuation-rerun-v0.md`
43. `45-g7plus-remaining-relation-source-context-audit-v0.md`
44. `46-g7plus-contract-family-decision-audit-v0.md`
45. `47-math8a-source-evidence-plumbing-v0.md`
46. `48-math-heavy-profile-boundary-v0.md`
47. `49-math8a-profile-selector-v1-rerun.md`
48. `50-math8a-assignment-bbox-exact-locator-v0.md`
49. `51-math8a-assignment-bbox-containment-locator-v0.md`
50. `52-math8a-remaining-bbox-stop-boundary-v0.md`
51. `53-math8a-native-exact-content-closure-v0.md`
52. `54-math8a-raw-assignment-exact-safe-closure-v0.md`
53. `55-math8a-remaining-exact-surface-closure-v0.md`
54. `56-math8a-remaining-formula-blocker-boundary-v0.md`
55. `57-global-readiness-checkpoint-after-math-boundary-v0.md`
56. `58-final-validation-verdict-v0.md`

Core rule:

```text
Do not treat Standard artifact publication as Basic Print acceptance.
```

Current baseline:

- verified `basic_print` samples: `1`
- first official Basic Print golden: RE1 review outcome V0
- initial research cases: RE1, Grammar Friends 6, and 中学生世界 八上 数学
- current positive reading-textbook comparator: RE1 Basic Print golden
- current workbook Basic Print candidate: GF6 workbook regression loop V1 rerun 2026-06-29
- current workbook second sample candidate: GF4 workbook second sample V3 rerun 2026-06-30
- current workbook candidate status: GF6, GF4, and GIC are candidates only, not accepted golden
- current GF4 caveat: candidate status depends on one explicit evidence-backed source typo correction recorded in `correction_log.json`
- current GF4 grammar paradigm rebuild audit: `28-grammar-paradigm-table-rebuild-audit-v0.md` confirms the three GF4 V2 reconstruction blockers are reflowed by the profile-general grammar paradigm renderer and accepted in GF4 V3; this validates the GF4 failure mode, not broad table rebuild
- current workbook consolidation: GF6/GF4/GIC are enough for `grammar_workbook_profile_ready_v0`, but not accepted-golden or release readiness
- current workbook promotion rule: use `20-workbook-promotion-checklist-v0.md` before promoting any workbook candidate or profile
- current corpus status audit: RE1/GF6/GF4/GIC/G7+/Math case records are aligned with current run/golden records; see `29-corpus-status-consistency-audit-v1.md`
- current promotion hard stops: `30-promotion-hard-stop-matrix-v1.md` is the active promotion guardrail; GF6/GF4/GIC remain candidate-only, G7+ remains review pressure, and math remains blocked/review
- current GIC Clean promotion audit: `31-gic-clean-promotion-blocker-audit-v0.md` is superseded by the closure ledgers and `34-gic-basic-print-candidate-promotion-v0.md`
- current GIC Clean media purpose ledger: `33-gic-clean-media-purpose-ledger-v0.md` closes `media_review_threshold` by reusable ledger for GIC; the later LLM fallback ledger closes the remaining Clean review gate
- current GIC LLM fallback ledger: `clean_llm_fallback_ledger.json` closes `llm_structure_revert_threshold`; the v3 closure policy audit passes
- current GIC candidate promotion: `34-gic-basic-print-candidate-promotion-v0.md` records `Grammar in Context Baisic (Seventh)` as the first non-Grammar-Friends `grammar_workbook` Basic Print candidate; it is still not accepted golden
- current grammar_workbook profile status: `35-grammar-workbook-profile-ready-v0.md` records `grammar_workbook_profile_ready_v0` for the Basic Print compiler/profile contract only; GF6/GF4/GIC remain candidate-only, not accepted golden
- current Clean review scope audit: RE1/GF6/GF4 are `clean_pass_no_scope_needed`; GIC is `review_scoped_not_promoted`; see `25-clean-review-scope-cross-sample-v0.md`
- current non-Grammar-Friends pressure run: `(7)G7+.pdf` has an `exercise_workbook` Standard review run with quality score 94 and open blockers; it is not a candidate golden
- current exercise_workbook blocker audit: G7+ remains review pressure; image source crops completed for `1477/1477` key figures, table/formula source crops completed for `2712/2860` required visual outcomes, `2697` exact/compact/semantic-match table/formula outcomes are closed as `accepted_by_rule`, `3` image-only formula packets are closed `non_blocking`, and near-match table review split into `1` accepted plus `1` `needs_reconstruction`; refined formula-token source-location backfilled `12` additional formula crops, same-unit ordinal duplicate matching backfilled `5` more formula crops, compact-exact Raw context matching backfilled `10` context/formula crops, short-procedure context matching backfilled `5` step crops, short option-formula context matching backfilled `3` formula-option crops, and unique same-unit page compact containment backfilled `1` formula crop as manual review evidence; cumulative formula semantic-equivalent closure now covers `32` outcomes, including `3` Markdown-emphasis-only false positives closed in the latest pass; remaining blockers are `11` formula layout-review/source-review items with source crops, `148` formula page-bbox gaps, `2` table layout-review items with source crops, `1` table reconstruction blocker, and `1811` real profile gaps; see `26-g7plus-exercise-workbook-blocker-audit-v0.md`
- current G7+ raw-context stop boundary: `143` remaining raw-context items are classified by `raw_context_rule_stop_audit.json`; do not lower similarity thresholds for weak/no-candidate matches because most remaining items are no-candidate/manual reconstruction or near false positives with different numbers/formulas
- current G7+ relation blocker boundary: `workbook_relation_gap_pattern_audit.json` shows `1725` ungrouped questions across `1030` runs and `84` orphan table questions; `740` question gaps sit behind known section labels or instruction paragraphs, but `981` still require deeper grouping/state-machine boundary logic, so G7+ must remain review pressure
- current G7+ grouping simulation: `workbook_grouping_state_machine_simulation.json` is promising but not compiler-ready; conservative starter-run grouping covers `752` relation gaps, persistent virtual grouping covers `1805/1811` but has high-risk signals (`448` long paragraphs inside active groups and `82` tables attached only to active group), and guarded grouping covers `1674/1811` while leaving `137` gaps including all `84` table gaps
- current G7+ table attachment simulation: `workbook_table_attachment_policy_simulation.json` classifies the `84` orphan table gaps into `9` generic auto-attach candidates, `8` paired/vocabulary special layout-rule candidates, and `75` visual/manual review cases, so table attachment remains audit-only and not compiler-ready
- current G7+ paired vocabulary table audit: `workbook_paired_vocabulary_table_layout_audit.json` narrows the `8` paired/vocabulary candidates into `1` two-table vocabulary/definition pair and `7` word-bank-plus-definition tables; these are layout subrule candidates pending source visual confirmation, not closed relation gaps
- current G7+ paired vocabulary source confirmation: `paired_vocabulary_source_confirmation.json` and `paired_vocabulary_source_context_contact_sheet.png` confirm `8/8` source layout shapes, but the subset remains review evidence because `b-03276` still needs reconstruction-sensitive blank preservation and no relation gaps were closed
- current G7+ paired vocabulary renderer contract: `paired_vocabulary_renderer_contract_audit.json` defines prototype requirements for source-confirmed group boundary, two-table horizontal pair rendering, word-bank-plus-table rendering, and blank-box preservation; it is contract-ready, not gate-closed
- current G7+ paired vocabulary renderer prototype: `paired_vocabulary_renderer_prototype.html` renders the `8` source-confirmed records in an isolated review artifact with visible answer spaces; its `b-03276` reconstruction blocker is superseded by the later real PDF blank-preservation rerun
- current G7+ paired vocabulary compiler-adjacent patch: `paired_vocabulary_compiler_patch/` contains isolated patched document/html artifacts covering `8` groups and `9` orphan table gaps, projecting real profile gaps from `1811` to `1802`; it is not a main Standard rerun or gate closure
- current G7+ paired vocabulary formal compiler attempt: `standard-final-no-pdf-stub-v2` detects `9` paired-vocabulary groups and `10` table blocks, fixes the long word-bank miss for `b-11020`, and discovers `b-09582`; its PDF-stubbed blank-box blocker finding is superseded for the narrow blank-preservation subrule by the real PDF rerun in `36-g7plus-paired-vocabulary-blank-preservation-v0.md`
- current G7+ paired vocabulary blank-box hard stop: superseded by `36-g7plus-paired-vocabulary-blank-preservation-v0.md` for the narrow paired-vocabulary blank-box subrule; it remains a profile boundary, not an exercise_workbook promotion
- current G7+ paired vocabulary blank reconstruction prototype: `paired_vocabulary_blank_reconstruction_prototype_report.json` reconstructs `6` visible blank boxes across the `2` known blockers with conservative text patterns; this is an isolated prototype and the next safe step is cross-sample reconstruction-pattern audit before compiler promotion
- current cross-sample reconstruction audit: `27-blank-reconstruction-cross-sample-audit-v0.md` shows `5` unique reconstruction cases split into `2` G7+ blank-pattern cases and `3` GF4 grammar-paradigm table rebuild cases; blank-box rules are not general reconstruction rules and are not compiler-ready
- current G7+ paired vocabulary blank preservation: `36-g7plus-paired-vocabulary-blank-preservation-v0.md` records a real PDF rerun where compiler/source-confirmed table ids match at `10/10`, source blanks are preserved for `b-03276` and `b-09582` with `6` `answer-line-source` spans, and the paired-vocabulary blank-box subrule closes; this does not promote G7+ or `exercise_workbook`
- current G7+ exercise relation delta: `37-g7plus-exercise-relation-delta-audit-v0.md` compares the main pressure run with the paired-vocabulary blank-preservation rerun; real profile gaps drop `1811 -> 560` with no added gaps, but `26` removed table gaps come from high-risk baseline buckets, so this is profile-engineering evidence rather than compiler-ready promotion
- current G7+ table attachment contract split: `38-g7plus-table-attachment-contract-audit-v0.md` classifies the `84` orphan table gaps into `9` paired-vocabulary contract-ready records, `2` non-paired source-visual spot-audit candidates, `3` visual-review-before-contract candidates, `15` not-proven stable gaps, and `55` high-risk review-only records; broad table attachment remains forbidden
- current G7+ table attachment spot audit: `39-g7plus-table-attachment-spot-audit-v0.md` accepts the `2` non-paired source-context candidates as two narrow families, `example_step_data_table_keep_with_explanation` and `single_table_vocabulary_review`; this still does not authorize broad table attachment or exercise_workbook promotion
- current G7+ table attachment visual-review audit: `40-g7plus-table-attachment-visual-review-audit-v0.md` accepts `3` question-like table candidates as two narrow example-table families, `example_relative_frequency_question_table_explanation` and `example_statistics_question_table_explanation`; broad question-like table attachment remains forbidden
- current G7+ table attachment stable-gap audit: `41-g7plus-table-attachment-stable-gap-audit-v0.md` audits the `15` low/medium orphan-table gaps that stayed stable after the paired-vocabulary rerun; `9` are narrow rule candidates requiring compiler rerun and `6` stay review, so stable gaps cannot be closed by inspection or `accepted_by_rule` table visual outcomes
- current G7+ table attachment stable-rule rerun: `42-g7plus-table-attachment-stable-rule-rerun-v0.md` implements the `9` stable-gap candidates as narrow compiler rules; after tightening one overbroad statistics match, the rerun reduces real profile gaps `560 -> 551` and orphan table questions `36 -> 27` with `0` added gaps, but G7+ remains review pressure
- current G7+ virtual question grouping rerun: `43-g7plus-virtual-question-group-rerun-v0.md` implements guarded exercise_workbook virtual question grouping; it removes `490` real ungrouped-question gaps with `0` added real gaps and reduces current real profile gaps `551 -> 61`, but it also absorbs `80` prior classifier-artifact questions and leaves `35` table gaps, `25` question gaps, and `1` figure gap, so G7+ remains review pressure
- current G7+ question continuation rerun: `44-g7plus-question-continuation-rerun-v0.md` implements same-heading numbered-question continuation across short/image interruptions and a front-matter topic-list downgrade; real ungrouped-question gaps are now `0`, real profile gaps drop `61 -> 36`, and remaining blockers are `35` table gaps plus `1` figure relation gap
- current G7+ remaining relation source-context audit: `45-g7plus-remaining-relation-source-context-audit-v0.md` creates source-PDF context packets for all `36/36` remaining table/figure relation gaps, split into `18` contract-review packets and `18` keep-review packets; this is evidence plumbing/review readiness, not gate closure or exercise_workbook promotion
- current G7+ contract family decision audit: `46-g7plus-contract-family-decision-audit-v0.md` classifies the `18` source-context contract-review packets as `18/18` math-heavy profile-boundary cases and recommends no generic `exercise_workbook` rerun; remaining relation gaps should feed a math-heavy workbook/textbook contract decision, not a broad exercise_workbook table rule
- Math 8A source evidence plumbing checkpoint: `47-math8a-source-evidence-plumbing-v0.md` used the local source PDF to generate the first `600/1157` formula/table source crops; this is superseded by later bbox locator and closure audits for current counts
- current math-heavy profile boundary: `48-math-heavy-profile-boundary-v0.md` combines G7+ and Math 8A evidence to define a boundary between ordinary `exercise_workbook` and math-heavy workbook/textbook contracts; no generic exercise_workbook table rule or math_textbook promotion is allowed yet
- Math 8A profile selector checkpoint: `49-math8a-profile-selector-v1-rerun.md` closes the previous reading_textbook mis-selection blocker by selecting `math_textbook`; later audits now carry the current review counts
- Math 8A assignment bbox exact locator checkpoint: `50-math8a-assignment-bbox-exact-locator-v0.md` uses Raw assignment evidence to apply `282` exact source bboxes, raising source-crop-ready formula/table packets from `600` to `882` and reducing remaining page/bbox gaps from `557` to `275`
- Math 8A assignment bbox containment locator checkpoint: `51-math8a-assignment-bbox-containment-locator-v0.md` applies `116` unique containment source bboxes as wider source-context evidence, raising source-crop-ready formula/table packets from `882` to `998` and reducing remaining page/bbox gaps to `159`
- current Math 8A remaining bbox stop boundary: `52-math8a-remaining-bbox-stop-boundary-v0.md` classifies the remaining `159` page/bbox gaps and shows Popo content-list fallback locates `0` additional safe records; do not lower text thresholds for short options/fragments or ambiguous repeated items
- Math 8A native exact content closure checkpoint: `53-math8a-native-exact-content-closure-v0.md` closes `600` native Raw content exact-match formula/table visual outcomes as `accepted_by_rule`, including all `4` table outcomes; later exact-surface audits now carry the current open count
- current Math 8A raw-assignment exact safe closure: `54-math8a-raw-assignment-exact-safe-closure-v0.md` risk-audits `191` raw_assignment exact semantic-equivalent formula outcomes, closes `188` safe surface matches, and keeps `3` digit-spacing records in review; Math 8A remains review-blocked with `369` open formula visual outcomes
- current Math 8A remaining exact-surface closure: `55-math8a-remaining-exact-surface-closure-v0.md` re-audits `94` remaining raw_assignment exact outcomes, closes `91` surface-safe records, and keeps `3` digit-spacing records in review; Math 8A remains review-blocked with `278` open formula visual outcomes
- current Math 8A remaining formula blocker boundary: `56-math8a-remaining-formula-blocker-boundary-v0.md` classifies the remaining `278` formula blockers into `159` page/bbox stop-boundary records, `116` containment-context review records, and `3` digit-spacing review records; the current exact/surface-safe closure rule set is exhausted
- current math profile status: blocked/review, because the math_textbook selector and exact/surface-safe closure rules now work, but `278` formula outcomes remain open behind page/bbox, containment-context, and digit-spacing blockers
- current global readiness checkpoint: `57-global-readiness-checkpoint-after-math-boundary-v0.md` states that Standard Basic Print is still not engineering-release-ready; the next safe loop is math-heavy workbook/textbook contract definition rather than more threshold-based Math 8A closure
- current final validation verdict: `58-final-validation-verdict-v0.md` closes the current validation task with release readiness = no, while preserving positive conclusions for RE1 and grammar_workbook
- current overall release verdict: not ready for engineering release; `grammar_workbook` is profile-ready v0, but `exercise_workbook` and `math_textbook` remain unresolved; see `24-basic-print-readiness-matrix-v0.md`
