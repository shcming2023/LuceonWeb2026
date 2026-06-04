# P0 Structure-Level CleanLaTeX Pack Contract Revision

Task ID: TASK-20260604-143649-P0-Structure-Level-CleanLaTeX-Pack-Contract-Revision

## Mainline Goal

Revise Task 328 from a section/exercise semantic pack design into a structure-level CleanLaTeX pack contract.

The pack boundary must be selected by structural level, source-span stability, and size/split rules, not by textbook-specific semantic labels such as `section`, `lesson`, `topic`, `grammar focus`, or `exercise`.

## Required Revision

- Generalize `section_pack` into `cleaning_unit_pack`.
- Add `pack_level`.
- Add `pack_selection_policy`.
- Add split/merge policy.
- Treat semantic `kind` as metadata and prompt guidance only, not as the primary boundary driver.
- Keep pilots `1.1` and `4.1`, but explain they are selected because their structural level and source span size are suitable, not because they are called `section`.

## Write Boundary

Allowed files:

- `TaskAndReport/*Structure-Level-CleanLaTeX-Pack-Contract-Revision_TASK.md`
- `TaskAndReport/*Structure-Level-CleanLaTeX-Pack-Contract-Revision_DESIGN.md`
- `TaskAndReport/*Structure-Level-CleanLaTeX-Pack-Contract-Revision_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden actions:

- Do not modify business code.
- Do not call LLM.
- Do not generate CleanLaTeX.
- Do not run MinerU, MinerU-Popo, GPU, or MPS jobs.
- Do not mutate DB, MinIO, or product metadata.
- Do not alter official MinerU-Popo outputs.
- Do not rename asset hash names.
- Do not touch local private role files.

## Positive Acceptance

- Design defines `luceon-cleanlatex-cleaning-unit-pack/v1`.
- Design defines structural pack selection using `pack_level`, source span continuity, block count, page count, child count, and asset/formula/table density.
- Design includes split/merge rules.
- Design keeps semantic kind as metadata only.
- Design preserves source block IDs, page/bbox/source order, image hash names, formulas, and tables.
- Design keeps pilots `1.1` and `4.1` under structural justification.

## Negative Acceptance

- No implementation code.
- No LLM output.
- No full-book CleanLaTeX claim.
- No source truth invention.
