# P0 Asset Pipeline PRD Iteration: PDF -> Raw Material -> Clean Material Traceability

- Task ID: `TASK-20260519-143047-P0-Asset-Pipeline-PRD-Iteration-PDF-Raw-Clean-Traceability`
- Issued at: `2026-05-19T14:30:47+0800`
- Executed by: `Lucode`
- Date: `2026-05-19`
- Branch: `lucode/task-220-asset-pipeline-prd-iteration` (HEAD `caeda22c26649afeb532ea81ead616937fe0b249`)

## 1. Execution Summary

Based on the Task 220 directive, I have updated the PRD and architecture contracts to formally establish the `PDF -> Raw Material -> Clean Material` traceable asset chain. The following key product decisions were encoded:

1. **Asset Chain**: Explicitly set the next direction as `PDF -> Raw Material -> Clean Material`.
2. **Raw Material Durability**: Raw Material (MinerU artifacts + initial AI metadata) is now defined as a durable, prerequisite asset layer. It is never treated as a temporary buffer or overwritten.
3. **Mineru2Table Role**: Positioned as the *first* Clean Material preparation service. It consumes Raw Material to reconstruct logical structure (TOC, chapter, table boundaries).
4. **RawMaterial2CleanMaterial Role**: Explicitly declared as a distinct, subsequent cleaning stage that consumes both the Raw Material and the Mineru2Table structural outputs to generate final, normalized Clean Material. It is not collapsed into Mineru2Table.
5. **Traceability**: Emphasized that every stage and output must preserve strict provenance (source object refs, hashes, task IDs, service versions, and options).

## 2. Files Changed

- `docs/prd/Luceon2026-PRD-v0.4.md`: Added the "第三次演进" direction specifying the asset chain and the prep/clean separation. Excluded business implementation from current scope.
- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`: Detailed the asset chain, explicit durable Raw Material status, and separated the `RawMaterial2CleanMaterial` stage.
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`: Updated the Asset Layers table with `CleanMaterial (Prep)` for Mineru2Table and `CleanMaterial (Final)` for RawMaterial2CleanMaterial.
- `docs/contracts/CleanService-Protocol-v1.md`: Clarified that `toc-rebuild` is a preparation step for the subsequent cleaning stage.
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`: Updated role definitions.
- `docs/codex/PROJECT_STATE.md`: Noted the new PRD v0.4 architecture contract in non-blocking residuals.
- `.gitignore`: Added ignore rules for `.agents/` and `AGENTS.md`.
- `AGENTS.md` and `.agents/**`: Removed from Git tracking (kept as untracked local private files).
- `TaskAndReport/TASK_TRACKING_LIST.md`: Updated Task 220 ledger row and resolved merge conflict with `origin/main`.
- `TaskAndReport/2026-05-19T14-30-47+0800_P0-Asset-Pipeline-PRD-Iteration-PDF-Raw-Clean-Traceability_REPORT.md` (this file)

## 3. Mandatory Safety Assertions

- **No Code/Runtime/Data Mutation**: This task remained strictly limited to documentation and PRD contract updates. No changes were made to `src/`, `server/`, `Docker` configs, MinIO data, DB records, models, or any production assets.
- **No Implementation Claims**: The PRD updates do not imply that CleanServiceWorker, Mineru2Table dispatch, or RawMaterial2CleanMaterial are currently implemented or ready for production.

## 4. Validation

- `git diff origin/main --check` exited with code `0`.
- Path audit (`git diff origin/main --name-status`) verified only PRD documentation, reports, `.gitignore`, and the de-tracking of local agents files were included in the commit.
- Markdown syntax in updated files is valid.
- Branch has been successfully merged/rebased with the latest `origin/main`.

## 5. Ledger Update

The TASK_TRACKING_LIST row for Task 220 will be marked:
- Status: `Ready for luceon Review`
- Next Actor: `Luceon`
- Branch/HEAD: `lucode/task-220-asset-pipeline-prd-iteration`

## 6. Open Questions for Luceon / Director

None at this time. The documentation conforms exactly to the decisions specified in the Task 220 directive. All future implementation will require separate, explicit authorization.
