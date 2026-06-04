# P0 Source-Bound Cleaning Unit Pack Generator For CleanLaTeX Pilot

Task ID: TASK-20260604-145530-P0-Source-Bound-Cleaning-Unit-Pack-Generator-For-CleanLaTeX-Pilot

## Mainline Goal

Implement the first structure-level CleanLaTeX pack generator for pilot nodes `1.1` and `4.1`.

The generator must consume existing v327 canonical artifacts and official Popo source tree, then produce source-bound `cleaning_unit_pack` artifacts for downstream CleanLaTeX pilot work.

This task must not call LLM and must not generate final CleanLaTeX.

## Write Boundary

Allowed files:

- `luceon_service/service.py`
- `luceon_service/tests/test_popo_invocation_boundary.py`
- Task/report/ledger files under `TaskAndReport/`

Forbidden actions:

- Do not modify MinerU or MinerU-Popo upstream code.
- Do not call LLM.
- Do not generate CleanLaTeX.
- Do not rerun MinerU/MinerU-Popo inference as part of validation.
- Do not mutate production DB, MinIO, or product metadata in this implementation task.
- Do not rename image/audio/resource hash names.
- Do not embed full pack body content into DB metadata.
- Do not touch local private role files.

## Required Behavior

- Add `luceon-cleanlatex-cleaning-unit-pack/v1` pilot pack generation.
- Add pack selection policy artifact `luceon-cleanlatex-pack-selection-policy/v1`.
- Generate packs for pilot numbers `1.1` and `4.1`.
- Use structure-level boundary metadata:
  - `pack_level`
  - `pack_role`
  - `boundary_basis=structure-level`
  - `semantic_kind_is_boundary_driver=false`
- Preserve source block IDs and unresolved source block IDs.
- Build derived prompts from pack JSON.
- Build validation manifests with pending checks.
- Upload/store pack artifacts as additional CleanService artifact references, not replacing existing seven-artifact compatibility outputs.

## Positive Acceptance

- Focused Python tests pass.
- New test proves `1.1` and `4.1` packs are structure-level and source-bound.
- Real Math 2022 evidence replay produces:
  - pack count `2`;
  - `1.1` parent `1 Review of number concepts`;
  - `4.1` parent `4 Collectingorganisingand displayingdata`;
  - unresolved source block count `0`;
  - prompts derived for both packs.
- CleanService verifier/apply smoke tests still pass.

## Negative Acceptance

- No LLM output.
- No CleanLaTeX claim.
- No full-book automation claim.
- No production deployment/UAT claim.
