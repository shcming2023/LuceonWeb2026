# P0 Mineru2Table Integration Pre-Implementation Design Report

- Task ID: `TASK-20260519-152658-P0-Mineru2Table-Integration-PreImplementation-Design`
- Issued at: `2026-05-19T15:26:58+0800`
- Executed by: `Lucode`
- Date: `2026-05-19`
- Final Branch: `lucode/task-221-mineru2table-design`
- Final HEAD: `6ad2a08ddb9c06ef5af9ee08d2ba91e73f6c2ffa` (Base for this report)

## 1. Execution Summary

Based on the Task 221 return review feedback, I have completely revised the Pre-Implementation Design artifact for the Mineru2Table CleanService integration. The updated design rigorously addresses all Luceon blocking findings (F1-F6).

Key corrections:
- **F1 (Data Contract)**: Provided exact JSON-like bounded shapes for the job request, task/material metadata summaries, outputs, and event payloads. Clarified DB vs MinIO persistence.
- **F2 (Red Lines)**: Added explicit, mandatory governance rules for ID-only extraction, asset hash locking, and pure layout boundaries, to be verified by Task D.
- **F3 (Implementation Gates)**: Expanded Tasks A-F to include feature-flag posture, negative acceptance criteria, minimum test scope, and explicit non-goals for every task.
- **F4 (Cost Semantics)**: Corrected the semantics to ensure hard limit (`¥8`) explicitly maps to non-retriable failure, entirely separated from the soft limit (`¥5`) `cost-decision` pause.
- **F5 (Legacy ObjectRef)**: Reworded the legacy compatibility drop as a recommendation pending Luceon acceptance, clearly defining the safe `skipped-policy` fallback.

## 2. Implementation Sequence Proposed

The design strictly sequences mock-tested, feature-flagged work:
- **Task A**: Raw Material Canonical Adapter (Mock-Safe)
- **Task B**: Real HTTP Transport & Admission Circuit (Mock-Safe)
- **Task C**: Webhook Callback Route (Mock-Safe)
- **Task D**: Strict Output Verifier Update (Mock-Safe)
- **Task E**: Cross-Boundary Safety & State Contracts (Mock-Safe)
- **Task F**: UI State Surface (Read-Only)

## 3. Files Changed

- `TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_DESIGN.md` (Revised)
- `TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_REPORT.md` (This Report)
- `TaskAndReport/TASK_TRACKING_LIST.md` (Ledger Updated)

## 4. Mandatory Safety Assertions

- **No Source/Runtime/Data Mutation**: This task remained strictly limited to generating the design blueprint within `TaskAndReport/`. Absolutely no changes were made to `src/**`, `server/**`, `package.json`, `.env`, Docker configs, or any other implementation code.
- **No External/Environment Impact**: No MinIO objects, database rows, or external `Mineru2Table` repositories were mutated. The `.agents` directory and `AGENTS.md` were strictly untouched.
- **No Execution/Dispatch**: No actual `CleanServiceWorker` interactions, E2E validations, or real Mineru2Table dispatch occurred.
- **Task 219 Unaffected**: Task 219 remains explicitly separate and open.

## 5. Validation Evidence

**Path Audit (`git diff origin/main --name-status`)**:
Output:
```text
A       TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_DESIGN.md
A       TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
```
Exit code: `0`.
*Conclusion based on output:* Only the exact, authorized TaskAndReport files were added or modified. The exit code proves successful command execution, while the output strictly verifies the write boundary.

**Syntax Audit (`git diff origin/main --check`)**:
Output: (none)
Exit code: `0`.

## 6. Ledger Update

The TASK_TRACKING_LIST row for Task 221 has been marked:
- Status: `Ready for luceon Review`
- Next Actor: `Luceon`
- Next Action: Review revised design addressing F1-F6 and authorize future Task A implementation.
- Branch/HEAD: Updated to reflect `lucode/task-221-mineru2table-design`.

## 7. Open Questions for Luceon / Director

1. **Asset Version Allocator**: Luceon needs to define the semantic algorithm for allocating `assetVersion` to CleanService jobs before Task A execution.
2. **Legacy Parsed Skip Recommendation**: Confirmation is requested to accept the recommendation to treat legacy parsed assets as `skipped-policy`.
3. **Hard Cost Limit Resolution**: If Director wants an override flow post-`quota_exceeded`, a product definition is needed (but cannot bypass the ¥8 hard stop in-flight).
