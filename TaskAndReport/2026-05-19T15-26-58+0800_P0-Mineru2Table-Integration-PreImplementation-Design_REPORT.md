# P0 Mineru2Table Integration Pre-Implementation Design Report

- Task ID: `TASK-20260519-152658-P0-Mineru2Table-Integration-PreImplementation-Design`
- Issued at: `2026-05-19T15:26:58+0800`
- Executed by: `Lucode`
- Date: `2026-05-19`
- Branch: `lucode/task-221-mineru2table-design`

## 1. Execution Summary

Based on the Task 221 directive, I have created the Pre-Implementation Design artifact for the Mineru2Table CleanService integration. The design explicitly reconciles the accepted Task 220 asset-chain contract with the existing disabled CleanService foundation.

Key accomplishments:
- Identified gaps in legacy ObjectRef selection, HTTP transport, webhook routing, output verifier, and UI surface.
- Proposed a safe sequence of mock-tested, implementation-level tasks to construct the CleanService capability.
- Established strict canonical layout requirements (`content_list_v2.json`) and disallowed legacy parsed bucket bridging.
- Defined safety gates, including default disabled behavior and strict pre-flight admission circuit checks.

## 2. Implementation Sequence Proposed

The design breaks future work into the following sequence of isolated tasks:
- **Task A**: Raw Material Canonical Adapter (Mock-Safe)
- **Task B**: Real HTTP Transport & Admission Circuit (Mock-Safe)
- **Task C**: Webhook Callback Route (Mock-Safe)
- **Task D**: Cross-Boundary Safety (Re-AI & Reparse Interactions)
- **Task E**: UI State Surface (Read-Only)
- **Task F**: Real Mineru2Table Integration (Currently Blocked by external protocol support)

## 3. Files Changed

- `TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_DESIGN.md` (New Design Artifact)
- `TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_REPORT.md` (This Report)
- `TaskAndReport/TASK_TRACKING_LIST.md` (Ledger Updated)

## 4. Mandatory Safety Assertions

- **No Source/Runtime/Data Mutation**: This task remained strictly limited to generating the design blueprint. Absolutely no changes were made to `src/**`, `server/**`, `package.json`, `.env`, Docker configs, or any other implementation code.
- **No External/Environment Impact**: No MinIO objects, database rows, or external `Mineru2Table` repositories were mutated. The `.agents` directory and `AGENTS.md` were strictly untouched.
- **No Execution/Dispatch**: No actual `CleanServiceWorker` interactions, E2E validations, or real Mineru2Table dispatch occurred.
- **Task 219 Unaffected**: Task 219 remains explicitly separate and open.

## 5. Validation

- `git diff origin/main --name-status` exited with code `0`, confirming only the expected TaskAndReport files were added or modified.
- `git diff origin/main --check` exited with code `0`.

## 6. Ledger Update

The TASK_TRACKING_LIST row for Task 221 has been marked:
- Status: `Ready for luceon Review`
- Next Actor: `Luceon`
- Next Action: Review design and authorize future Task A implementation.
- Branch/HEAD: Updated to reflect `lucode/task-221-mineru2table-design`.

## 7. Open Questions for Luceon / Director

1. **Asset Version Allocator**: Luceon needs to define the semantic algorithm for allocating `assetVersion` to CleanService jobs (e.g., monotonic integer, mapping to Mineru version, etc.).
2. **Hard Cost Limit Authorization**: Director must define the product user-flow for resolving jobs that halt in the `cost-decision` state due to exceeding the configured hard cost limit.
