# Luceon Review - Task 264 v4 Version Override Planning

Review time: 2026-05-24T15:13:21+0800

Task:

```text
TASK-20260524-150104-P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite
```

Reviewed branch:

```text
origin/lucode/TASK-20260524-150104-P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite@89c339cc23fd4058451a5921e05e62550f15abb3
```

Verdict:

```text
ACCEPTED_PLANNING_LEVEL_WITH_LUCEON_HEAD_EVIDENCE_CORRECTION
```

## Review Boundary

This acceptance is planning-level only.

It accepts a task-brief-scoped `targetAssetVersion` planning direction for a
future mock-safe implementation task. It does not accept implementation,
runtime `v4`, runtime POST, live Mineru2Table query, DB apply, MinIO write,
job-store edit, worker activation, UAT, L3, pressure PASS, production readiness,
release readiness, production online, or go-live.

## Branch Handoff Evidence

`origin/main` showed Task 264 as `下达待 Lucode 执行` / `Next Actor=Lucode`.
The matching Lucode branch-local ledger row showed:

```text
Status = Lucode 已回报待 Luceon 审查
Next Actor = Luceon
```

Luceon reviewed the branch through the branch-handoff rule.

Commands:

```bash
git diff --name-status origin/main...origin/lucode/TASK-20260524-150104-P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite
git diff --check origin/main...origin/lucode/TASK-20260524-150104-P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite
git show --name-status --oneline --decorate origin/lucode/TASK-20260524-150104-P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite -1
```

Observed branch diff:

```text
A       TaskAndReport/2026-05-24T15-01-04+0800_P0-CleanService-v4-Version-Override-Planning-MockSafe-NoRuntime-NoDBWrite_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
```

`git diff --check origin/main...origin/lucode/...` exited `0` with no output.

## Evidence Correction

Lucode's report correctly explains why the final commit hash cannot be embedded
inside the report without changing the hash, but the task brief required exact
branch/HEAD evidence. Luceon records the reviewed remote branch HEAD here:

```text
89c339cc23fd4058451a5921e05e62550f15abb3
```

This is a small control-plane evidence correction and does not require returning
the planning task.

## Accepted Planning Findings

Accepted direction:

```text
Use a task-brief-scoped explicit targetAssetVersion for the next mock-safe
implementation task.
```

Accepted rationale:

- `targetAssetVersion` names the intended output version and is less ambiguous
  than a broad `assetVersionOverride`.
- The override must be valid only with explicit `create-new-version` intent and
  a non-empty `newVersionReason`.
- The override must be authorized by a concrete task brief per run, not long
  lived env/config.
- Default allocation should remain the baseline; future code should record both
  `defaultAllocatedAssetVersion=v3` and `targetAssetVersion=v4` for the current
  `v2` accepted DB state.
- Existing `v3` remains diagnostic dual-key evidence and must not be promoted
  into durable Clean Material metadata by this route.

Accepted future preconditions:

- existing task and material clean metadata are both present, completed,
  aligned, and include a previous jobId;
- target version matches numeric `vN`;
- target version is greater than the current accepted metadata version;
- target version is greater than or equal to the default allocator result;
- source input remains canonical-first with completed-job `sourceInput`
  fallback only;
- provenance `-probe` remains rejected unless explicitly allowed;
- real apply remains blocked unless separately authorized.

Accepted future implementation surface:

- `server/services/cleanservice/asset-version.mjs`
- `server/services/cleanservice/cleanservice-worker.mjs`
- `server/services/cleanservice/orchestration-runner.mjs`
- `server/services/cleanservice/metadata-apply-executor.mjs`
- focused CleanService smoke tests named in the report.

## Rejected Or Deferred Paths

Still rejected or deferred:

- env/config-scoped persistent override;
- automatic allocator change that silently skips diagnostic physical/job-store
  versions;
- runtime POST or live Mineru2Table query;
- DB apply;
- MinIO write or physical `v4` artifact creation;
- job-store edit or cleanup;
- worker/scheduler/upload-server activation;
- readiness/go-live wording.

## Checks And Review Notes

Luceon inspected the report and relevant current main source behavior in:

- `server/services/cleanservice/asset-version.mjs`
- `server/services/cleanservice/orchestration-runner.mjs`
- `server/services/cleanservice/metadata-apply-executor.mjs`

The planning recommendation matches current code shape: `allocateAssetVersion()`
is metadata-driven and currently produces `v3` from accepted `v2`; an explicit
task-scoped target is therefore the right place to model a clean `v4` path
without pretending the diagnostic `v3` is durable metadata.

No business source-code changes were accepted in this task.

## Next Recommendation

Recommended next task:

```text
P0 CleanService targetAssetVersion v4 Override MockSafe Planning-to-Code NoRuntime NoDBWrite
```

That next task should implement only mock-safe version targeting and tests. It
must still forbid runtime POST, live DB/MinIO/job-store/runtime reads, DB apply,
MinIO writes, Docker/Compose mutation, job-store edit, worker activation,
readiness, and go-live claims.
