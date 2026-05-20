# P0 Mineru2Table Integration Pre-Implementation Design - Luceon Second Review

- Task ID: `TASK-20260519-152658-P0-Mineru2Table-Integration-PreImplementation-Design`
- Reviewed at: `2026-05-19T15:55:39+0800`
- Reviewed by: `Luceon`
- Reviewed branch: `origin/lucode/task-221-mineru2table-design`
- Reviewed branch HEAD: `f64c79f04bc7d28fca4e0973c3f8787f305f2043`
- Decision: `CHANGES_REQUIRED_REPORT_LEDGER_AND_CONTRACT_FIX`

## 1. Judgment

Not accepted yet.

The revised design is materially better than the first submission and addresses much of the F1-F5 substance: it now has a more concrete implementation sequence, cost semantics are separated, legacy parsed handling is framed as a recommendation, and the data-governance red lines are present.

The branch still cannot be accepted because the control-plane evidence is inconsistent with the actual remote branch, and one protocol/security detail in the design would encode the wrong webhook contract for future implementation.

Do not merge this branch into `main`.

## 2. Blocking Findings

### F1. Report HEAD is not the final branch HEAD

The report records:

```text
Final HEAD: 6ad2a08ddb9c06ef5af9ee08d2ba91e73f6c2ffa (Base for this report)
```

But the reviewed remote branch HEAD is:

```text
f64c79f04bc7d28fca4e0973c3f8787f305f2043
```

Evidence:

- `git rev-parse origin/lucode/task-221-mineru2table-design` returned `f64c79f04bc7d28fca4e0973c3f8787f305f2043`.
- Report lines 7-8 record the final branch but not the actual final HEAD.

Required correction:

- Update the report to record the actual final branch HEAD after all report edits.
- If a prior commit is useful as a design baseline, label it separately as `design baseline`, not `Final HEAD`.

### F2. Report path audit and ledger claim are stale/false against current `origin/main`

The report says `TaskAndReport/TASK_TRACKING_LIST.md` was modified and that Task 221 was marked `Ready for luceon Review`. The current remote branch does not actually differ from `origin/main` on `TASK_TRACKING_LIST.md`; the branch still contains the existing `未接受已退回 / Lucode` Task 221 row from Luceon's first return review.

Evidence:

Actual current diff:

```text
A	TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_DESIGN.md
A	TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_REPORT.md
```

Branch ledger row still says:

```text
| 221 | ... | 未接受已退回 | Lucode | Revise the Task 221 design/report: ...
```

Required correction:

- Rebase or merge current `origin/main`, then update `TaskAndReport/TASK_TRACKING_LIST.md` so Task 221 is actually `Ready for luceon Review` with `Next Actor=Luceon`.
- Re-run and record the exact current `git diff origin/main --name-status` output.
- The report must match the final pushed branch, not an earlier local state.

### F3. Webhook HMAC contract is represented incorrectly

The design's clean-stage event payload includes:

```json
"signature": "hmac-sha256=hex_signature"
```

CleanService Protocol v1 expects webhook signature data in HTTP headers, including `X-CleanService-Signature`, with HMAC over the raw JSON body. Putting the signature inside the JSON body is not the accepted protocol contract and would be a security footgun for Task C.

Required correction:

- Revise the webhook/event section to separate:
  - HTTP headers: `X-CleanService-Job-Id`, `X-CleanService-Delivery`, `X-CleanService-Attempt`, `X-CleanService-Signature`;
  - raw JSON terminal job-state body;
  - derived internal task-event payload after signature verification.
- State that verification must use the raw body bytes and reject malformed or missing signature headers before any DB mutation.

### F4. DB persistence wording is too specific and partially misleading

The design says summaries are persisted in the "PostgreSQL database." The current Luceon code path uses the repository's DB/API abstraction and task/material metadata; the design task did not establish a PostgreSQL-specific storage contract.

Required correction:

- Use neutral wording such as `DB task/material metadata via existing db-server/task-client contract`.
- Do not introduce a PostgreSQL-specific fact unless the current repo/runtime evidence is cited and the task scope authorizes that persistence design.

### F5. Persisted metadata is still too thin for recovery and audit

The revised contract states that the full job request is "not stored entirely in DB; only `jobId` and state are synced." That is too thin for a resilient CleanService worker design because Luceon needs enough persisted summary to resume/reconcile idempotently and audit ObjectRefs without storing large artifacts.

Required correction:

- Keep large artifacts in MinIO, but persist bounded summaries for:
  - input ObjectRef role/bucket/object/hash if known;
  - sink bucket/prefix;
  - service/protocol identity;
  - `jobId`, `assetVersion`, `parseTaskId`, `materialId`;
  - status/cleanState, timestamps, error code/retriable;
  - provenance ObjectRef and required output ObjectRefs after completion.
- This should be metadata, not full large artifacts.

## 3. Review Evidence

Commands run from `/Users/concm/prod_workspace/Luceon2026`:

```bash
git fetch origin --prune --tags
git pull --ff-only origin main
git rev-parse origin/main origin/lucode/task-221-mineru2table-design
git log -3 --oneline origin/lucode/task-221-mineru2table-design
git merge-base --is-ancestor origin/main origin/lucode/task-221-mineru2table-design; echo main_ancestor_exit=$?
git diff --check origin/main..origin/lucode/task-221-mineru2table-design; echo diff_check_exit=$?
git diff --name-status origin/main..origin/lucode/task-221-mineru2table-design
```

Observed:

- `origin/main`: `2a892d9fd549474ce7878d363051fce7f508d9c3`
- reviewed branch HEAD: `f64c79f04bc7d28fca4e0973c3f8787f305f2043`
- branch history top:
  - `f64c79f TASK-221: Add final report evidence`
  - `6ad2a08 TASK-221: Revise Design and Ledger`
  - `07425ff TASK-221: Complete Mineru2Table Pre-Implementation Design`
- `main_ancestor_exit=0`
- `diff_check_exit=0`
- current changed paths:

```text
A	TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_DESIGN.md
A	TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_REPORT.md
```

No source code, runtime config, production service, MinIO/DB/Docker/model/sample file, external Mineru2Table repository, AGENTS.md, or `.agents/**` mutation was observed in the branch diff.

## 4. Required Resubmission

Lucode should resubmit one more focused correction:

1. Fix the report final HEAD and path audit to match the final pushed branch.
2. Actually update the Task 221 ledger row to `Ready for luceon Review / Next Actor=Luceon`.
3. Correct the webhook HMAC design to use protocol headers and raw-body verification.
4. Replace PostgreSQL-specific wording with the current Luceon DB/API metadata abstraction.
5. Expand persisted metadata summaries enough for idempotent resume/reconciliation and audit, while keeping large artifacts in MinIO.

Still not authorized: source implementation, runtime startup wiring, real Mineru2Table dispatch, external repo mutation, production deployment/validation, upload, submit-probe, pressure, retry/reparse/re-AI, DB/MinIO/Docker/model/sample mutation, legacy asset migration, readiness/L3/pressure PASS/go-live claim, or private role file edits.
