# P0 CleanService Raw Material Canonical Adapter And AssetVersion Allocator - Luceon Review

- Task ID: `TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator`
- Reviewed at: `2026-05-19T20:51:56+0800`
- Reviewed by: `Luceon`
- Reviewed branch: `origin/lucode/TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator`
- Reviewed branch HEAD: `b0e58df5076f4e07dc587a4814f843228a57d990`
- Decision: `CHANGES_REQUIRED_REPORT_EVIDENCE_ONLY`

## 1. Judgment

Not accepted yet.

The implementation appears close: the changed paths are inside the Task 222 source/test/report boundary, focused syntax checks pass, all submitted smoke tests pass, and Luceon reproduced that a legacy parsed-only task is classified as `skipped-policy` without calling `submitJob`.

However, Task 222 required the report to carry exact final branch/HEAD and exact path-audit output. The submitted report still has control-plane evidence defects. This return is report/ledger correction only; do not change source code unless the correction itself exposes a new evidence mismatch.

No production deployment, runtime startup, upload, submit-probe, real HTTP transport, real Mineru2Table dispatch, DB/MinIO/Docker/model/sample mutation, external Mineru2Table mutation, legacy migration/backfill/reparse, Task 219 change, UAT/L3/readiness/pressure PASS/go-live claim, or private role-file edit was performed during this review.

## 2. Blocking Findings

### F1. Report does not record a concrete final submitted HEAD

The report states:

```text
Final HEAD: *(Matches the ultimate commit of this branch on remote)*
```

The reviewed remote branch HEAD is:

```text
b0e58df5076f4e07dc587a4814f843228a57d990
```

Task 222 required final branch name and full final branch HEAD. A placeholder is not a durable audit anchor.

Required correction:

- Replace the placeholder with concrete commit evidence.
- If Lucode wants to avoid the self-referential commit-hash problem, split the wording honestly, for example:
  - `Implementation baseline HEAD: 481346cbf00a916ec762f418af3846108b3b300a`
  - `Submitted remote branch HEAD observed before Luceon review: b0e58df5076f4e07dc587a4814f843228a57d990`
  - if a report-only correction creates a new commit, record the new pushed branch HEAD in the final handoff and ledger.

### F2. Report path audit output is incomplete against the actual final branch

The report's `git diff --name-status origin/main` output lists only source and test paths. The actual reviewed branch diff also includes the report and ledger files.

Actual path audit observed by Luceon:

```text
A	TaskAndReport/2026-05-19T16-07-53+0800_P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator_REPORT.md
M	TaskAndReport/TASK_TRACKING_LIST.md
A	server/services/cleanservice/asset-version.mjs
M	server/services/cleanservice/cleanservice-worker.mjs
A	server/services/cleanservice/raw-material-adapter.mjs
A	server/tests/cleanservice-asset-version-smoke.mjs
A	server/tests/cleanservice-raw-material-adapter-smoke.mjs
M	server/tests/cleanservice-worker-shell-smoke.mjs
```

Task 222 required exact `git diff --name-status origin/main..HEAD` output. The report must match the final pushed branch, including control-plane files.

Required correction:

- Update the report's path audit to include the report and ledger files.
- Use the exact command form requested by Task 222: `git diff --name-status origin/main..HEAD`.
- Record exit code `0` separately from the path-audit conclusion.

## 3. Accepted Technical Evidence So Far

The following review checks were run from `/Users/concm/prod_workspace/Luceon2026` and a temporary detached worktree at the reviewed HEAD:

```bash
git fetch origin --prune --tags
git rev-parse origin/main origin/lucode/TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator
git log --oneline --decorate -5 origin/lucode/TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator
git merge-base --is-ancestor origin/main origin/lucode/TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator
git diff --name-status origin/main..origin/lucode/TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator
git diff --check origin/main..origin/lucode/TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator
node --check server/services/cleanservice/cleanservice-worker.mjs
node --check server/services/cleanservice/metadata-summary.mjs
node --check server/services/cleanservice/config.mjs
node --check server/services/cleanservice/raw-material-adapter.mjs
node --check server/services/cleanservice/asset-version.mjs
node server/tests/cleanservice-worker-shell-smoke.mjs
node server/tests/cleanservice-raw-material-adapter-smoke.mjs
node server/tests/cleanservice-asset-version-smoke.mjs
```

Observed:

- `origin/main`: `dbd0c8a3ac6a5ec3bace69e07af8e9646e75b002`
- reviewed branch HEAD: `b0e58df5076f4e07dc587a4814f843228a57d990`
- implementation baseline parent: `481346cbf00a916ec762f418af3846108b3b300a`
- `main_ancestor_exit=0`
- `git diff --check` exit code `0`
- all `node --check` commands exited `0`
- submitted smoke tests passed:

```text
=== CleanService Worker Shell Smoke ===
PASS cleanservice worker shell smoke
=== Raw Material Adapter Smoke ===
PASS raw material adapter smoke
=== Asset Version Allocator Smoke ===
PASS asset version allocator smoke
```

Additional Luceon legacy-safety reproducer also passed:

```text
PASS luceon legacy skip no-submit reproducer
```

The reproducer asserted that a legacy parsed-only task:

- throws `legacy-parsed-evidence-skipped` from `buildCleanServiceJobRequest`;
- returns worker status `skipped-policy`;
- records `submitted=0`;
- does not call mock `submitJob`;
- persists `input: null`, not a fabricated raw ObjectRef.

## 4. Required Resubmission

Lucode should make a minimal report/ledger correction and push the same long branch again:

1. Fix the report final HEAD wording with concrete commit evidence.
2. Fix the report path audit so it exactly matches the final branch diff, including TaskAndReport files.
3. Update the Task 222 ledger row to `Ready for luceon Review / Next Actor=Luceon` with the corrected branch/HEAD.
4. Do not change implementation source/tests unless necessary to keep the report evidence truthful.

Still not authorized: `server/upload-server.mjs` wiring, real HTTP transport, production/runtime operation, real Mineru2Table dispatch, external Mineru2Table mutation, upload/submit-probe/pressure, retry/reparse/re-AI, DB/MinIO/Docker/model/sample mutation, legacy migration/backfill, Task 219 mutation, UAT/L3/readiness/pressure PASS/go-live claim, or private role file edits.
