# Luceon Review: TASK-20260523-073349-P0-CleanService-Existing-Applied-Current-State-Noop-Policy

## Verdict

Status: Accepted and Closed

Classification: ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_HEAD_CORRECTION

Task 254 is accepted at code/test level. The runner now has a bounded
current-state noop policy for aligned completed `toc-rebuild` metadata, before
new assetVersion allocation or request planning.

## Review Basis

Luceon reviewed and merged:

```text
origin/lucode/TASK-20260523-073349-P0-CleanService-Existing-Applied-Current-State-Noop-Policy@331e94e578394e53f2f9c6af53ee327c4600a0ab
```

Baseline:

```text
origin/main@a2b9178a1e4ab6e6ab478ee3d34880bc9717677c
```

Diff scope:

```text
A       TaskAndReport/2026-05-23T07-33-49+0800_P0-CleanService-Existing-Applied-Current-State-Noop-Policy_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
M       server/services/cleanservice/orchestration-runner.mjs
M       server/tests/cleanservice-orchestration-runner-smoke.mjs
```

The submitted report and ledger recorded an intermediate HEAD
`c0e3b34ec1cb4a30ff13994e43faec3b6ce18683`. Luceon corrected both to the true
remote delivery HEAD `331e94e578394e53f2f9c6af53ee327c4600a0ab` during
acceptance. No business logic was changed by Luceon during acceptance.

## Findings

### F1 Closed: Current Applied State Noop

`runCleanServiceTocRebuildOnce` now checks aligned completed task/material
metadata before `allocateAssetVersion` and `buildCleanServiceJobRequest`.

When both sides contain aligned completed `toc-rebuild` metadata with a jobId,
the runner returns:

```text
CURRENT_CLEAN_MATERIAL_NOOP
```

This prevents the default current-state path from implicitly advancing from
`v2` to `v3`.

### F2 Closed: Negative Paths Stay Blocked

The runner does not convert mismatched or invalid historical metadata into noop.
Luceon independently probed:

```text
version-mismatch -> BLOCKED_EXISTING_TOC_REBUILD_METADATA
missing-job-id   -> BLOCKED_EXISTING_TOC_REBUILD_METADATA
failed-task-job  -> BLOCKED_EXISTING_TOC_REBUILD_METADATA
```

### F3 Closed: Task 253 Shape Now Noops

Luceon independently reproduced the Task 253 real metadata shape in memory. The
runner returned:

```json
{
  "status": "CURRENT_CLEAN_MATERIAL_NOOP",
  "classification": "CURRENT_CLEAN_MATERIAL_NOOP",
  "assetVersion": "v2",
  "jobId": "luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230"
}
```

Tripwire calls were:

```json
[]
```

## Verification

Luceon ran these checks in a detached review worktree:

```text
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
for f in server/tests/cleanservice-*.mjs; do node "$f" || exit 1; done
npx pnpm@10.4.1 exec tsc --noEmit
git diff --check origin/main..origin/lucode/...
```

Results:

```text
cleanservice-orchestration-runner-smoke.mjs: PASS 16/16
all server/tests/cleanservice-*.mjs: PASS
tsc --noEmit: PASS
git diff --check: PASS
```

## Acceptance Boundary

Accepted:

- mock-safe current-state noop policy;
- zero dependency calls in the noop branch;
- preservation of existing `v2` assetVersion and historical jobId;
- blocking of mismatched, missing-jobId, and failed existing metadata;
- no new-version/rerun path inside this task.

Not accepted or claimed:

- real DB/MinIO/Mineru2Table/LLM/Docker/runtime execution;
- real `POST /api/v1/jobs`;
- real new assetVersion creation;
- worker scheduling or upload-server wiring;
- UAT, L3, production readiness, pressure PASS, release readiness, or go-live.

## Recommended Next Step

Before a real new-version end-to-end run, the next discussion/task should define
explicit authorization semantics for rerun/new-version intent, so the system can
distinguish:

```text
use current clean material -> CURRENT_CLEAN_MATERIAL_NOOP
create next version        -> explicit Director-authorized new-version run
```
