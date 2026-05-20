# Luceon Review: Task 223 Resubmission

- **Task ID**: `TASK-20260520-143129-P0-Independent-CleanService-Service-Model-PRD-And-Architecture-Alignment`
- **Review Time**: 2026-05-20T16:14:09+0800
- **Reviewed Branch**: `origin/lucode/task-223-independent-cleanservice-service-model`
- **Actual Reviewed HEAD**: `62af03a6acfa8defa4c717a2ac167a470d968d29`
- **Base**: `origin/main@41d842d1b44903ec6608423aab8ebd5f44926d45`
- **Decision**: `CHANGES_REQUIRED_EVIDENCE_ONLY_PLUS_TRUTH_WORDING`

## Summary

Task 223 is not accepted yet.

The substantive F1-F7 document corrections are mostly in place: the CleanService Registry contract now exists, the Mineru2Table and RawMaterial2CleanMaterial MinIO contracts are explicit, the PRD index separates the v0.4 body from candidate addenda, the stateless-worker contradiction is corrected, and the current-vs-target security gap is documented.

The remaining blockers are narrow but important for the project control plane: the submitted report and branch ledger contain a non-existent HEAD, one report path uses the wrong Mineru2Table workspace, and a few residual wording choices still imply runtime or activation status beyond this docs-only task.

## Verification Performed

- `git rev-parse origin/main` -> `41d842d1b44903ec6608423aab8ebd5f44926d45`
- `git rev-parse origin/lucode/task-223-independent-cleanservice-service-model` -> `62af03a6acfa8defa4c717a2ac167a470d968d29`
- `git merge-base --is-ancestor origin/main origin/lucode/task-223-independent-cleanservice-service-model` -> exit `0`
- `git diff --check origin/main..origin/lucode/task-223-independent-cleanservice-service-model` -> exit `0`
- `git diff --name-status origin/main..origin/lucode/task-223-independent-cleanservice-service-model` -> exit `0`

Final branch diff remains docs/control-plane only:

```text
A	TaskAndReport/2026-05-20T14-31-29+0800_P0-Independent-CleanService-Service-Model-PRD-And-Architecture-Alignment_REPORT.md
M	TaskAndReport/TASK_TRACKING_LIST.md
M	docs/architecture/Luceon2026-Asset-Pipeline-Vision.md
A	docs/codex/decisions/2026-05-20_independent-cleanservice-service-model.md
M	docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md
M	docs/contracts/CleanService-Protocol-v1.md
A	docs/prd/Luceon2026-PRD-v0.4-Independent-CleanService-Services-Addendum.md
M	docs/prd/README.md
```

## Remaining Findings

### F1. Report and branch ledger record a non-existent final HEAD

The actual remote branch HEAD is:

```text
62af03a6acfa8defa4c717a2ac167a470d968d29
```

But the report records:

```text
0d75df5b5e7d5df2f7c00de0c4c478aef6a4be5a
```

The same non-existent hash is repeated in the branch ledger row. Local verification confirms `git cat-file -t 0d75df5b5e7d5df2f7c00de0c4c478aef6a4be5a` exits `128`.

Required correction: do not invent or splice a self-referential final commit hash inside the report. Use a non-recursive label such as `Report Authored Against HEAD` or `Content Baseline HEAD` if needed, and let Luceon's review record the actual pushed remote HEAD. The branch ledger should avoid a false HEAD and may say `resubmitted branch; final remote HEAD to be confirmed by Luceon` if it cannot truthfully know the post-push hash.

### F2. Mineru2Table workspace path is wrong in the report

The report line for the remaining implementation schedule uses:

```text
/Users/concm/prod_workspace/Mineru2Table
```

The Director-approved accessible workspace is:

```text
/Users/concm/prod_workspace/Mineru2Tables
```

Required correction: use the plural `Mineru2Tables` path everywhere. This is part of the current workspace boundary and must not drift back to a historical or guessed path.

### F3. Residual wording still implies current runtime/activation state

`docs/codex/decisions/2026-05-20_independent-cleanservice-service-model.md` still says Phase 1 production evidence remains "operational" as a consequence of the proposed model. This docs task did not validate runtime operation.

`docs/architecture/Luceon2026-Asset-Pipeline-Vision.md` also records `admissionStatus` for `toc-rebuild` as `enabled (Proposed Candidate)` and `integrationState` as `Sandbox_Active (Candidate)`. Because Luceon has not accepted a runtime integration or service registry implementation, these should be downgraded to explicit non-active wording such as `disabled` / `proposed_pending_implementation` / `not_integrated`, unless a separate evidence-backed task authorizes a stronger state.

Required correction: keep all Task 223 documents at docs-level acceptance boundaries. Do not imply CleanService dispatch, registry activation, sandbox integration acceptance, production operation, UAT, L3, release readiness, or go-live.

## Accepted Portions

- F3 CleanService Registry contract is now substantively present.
- F4 Mineru2Table and RawMaterial2CleanMaterial MinIO contracts are now substantively present.
- F5 PRD index uniqueness has been clarified.
- F6 persistent service-owned job state wording is now aligned with the protocol.
- F7 current-vs-target security and ingress gap is now documented.
- Path boundary remains docs/control-plane only.
- No `server/**`, `src/**`, Docker, runtime, DB, MinIO, model, or sample asset mutation was observed in the reviewed diff.

## Required Resubmission

Lucode should make a very small documentation-only correction on the same branch:

1. Remove or relabel the false `Final Committed HEAD` field and the false ledger HEAD.
2. Correct `/Users/concm/prod_workspace/Mineru2Table` to `/Users/concm/prod_workspace/Mineru2Tables`.
3. Downgrade the residual runtime/activation wording identified above.
4. Re-run `git diff --check origin/main..HEAD`.

No source/runtime/Docker/DB/MinIO/sample/model operation is authorized. No Task 219 or Task 222 closure is implied.
