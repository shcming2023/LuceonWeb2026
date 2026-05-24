# Luceon Review - Task 261 Existing v3 No-POST Reconciliation

Review time: 2026-05-24T14:14:17+0800

Task:

```text
TASK-20260524-135419-P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime
```

Reviewed branch:

```text
origin/lucode/TASK-20260524-135419-P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime@1240e5d35e49cf0dccfb6ddf124f52f26d89c58a
```

Verdict:

```text
CHANGES_REQUIRED_SOURCE_INPUT_PATH_VALIDATION_REGEX_GAP
```

## Review Boundary

This review used the Lucode branch-handoff rule. `origin/main` still showed
Task 261 as `Next Actor=Lucode`, while the matching Lucode branch had
branch-local `Status=Lucode 已回报待 Luceon 审查` and `Next Actor=Luceon`.

No runtime POST, live Mineru2Table query, DB/MinIO/Docker/env/model/sample
mutation, job-store edit, real DB apply, UAT, L3, pressure PASS, readiness, or
go-live action was performed.

## Branch Evidence

Commands:

```bash
git diff --name-status origin/main...origin/lucode/TASK-20260524-135419-P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime
git diff --check origin/main...origin/lucode/TASK-20260524-135419-P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime
```

Observed name-status:

```text
A       TaskAndReport/2026-05-24T13-54-19+0800_P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
M       server/services/cleanservice/cleanservice-worker.mjs
M       server/services/cleanservice/orchestration-runner.mjs
M       server/services/cleanservice/raw-material-adapter.mjs
M       server/tests/cleanservice-orchestration-runner-smoke.mjs
M       server/tests/cleanservice-raw-material-adapter-smoke.mjs
```

`git diff --check` exited `0` with no output.

## Checks Run By Luceon

Review worktree:

```text
/tmp/luceon-task261-review.ooaXHj
```

Checks:

```text
node --check server/services/cleanservice/raw-material-adapter.mjs: exit 0
node --check server/services/cleanservice/cleanservice-worker.mjs: exit 0
node --check server/services/cleanservice/orchestration-runner.mjs: exit 0
node server/tests/cleanservice-raw-material-adapter-smoke.mjs: exit 0
node server/tests/cleanservice-orchestration-runner-smoke.mjs: exit 0, 26/26
node server/tests/cleanservice-output-verifier-smoke.mjs: exit 0, 9/9
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs: exit 0
mock-safe cleanservice-*.mjs loop excluding Task 256 runtime harness: exit 0
npx pnpm@10.4.1 exec tsc --noEmit: exit 0
```

The Task 256 runtime harness was intentionally skipped because Task 261
forbids running that runtime harness.

## Return Finding

### P1 - Source-input path validation uses unescaped regex input

Location:

```text
server/services/cleanservice/raw-material-adapter.mjs:27-30
```

`validateContentListV2Source()` builds a `RegExp` directly from
`task.materialId` and `rawMaterialVersion`. That means regex metacharacters in
the ID/version are interpreted as pattern syntax instead of literal source
truth.

Independent Luceon negative probe:

```js
assert.throws(
  () => buildCanonicalRawMaterialRef({
    materialId: 'mat.260',
    metadata: {
      cleanServiceJobs: {
        'toc-rebuild': {
          status: 'completed',
          sourceInput: {
            bucket: 'eduassets-raw',
            object: 'mineru/matX260/v1/content_list_v2.json',
            sha256: 'sha'
          }
        }
      }
    }
  }),
  /object path mismatch/
);
```

Observed result:

```text
AssertionError: Missing expected exception.
```

The fallback accepted `mineru/matX260/v1/content_list_v2.json` for
`materialId=mat.260`. This violates the task requirement that fallback
sourceInput strictly match `mineru/<materialId>/vN/content_list_v2.json` and
the negative acceptance criterion that wrong materialId paths are blocked.

Related observation:

```text
mineru/mat-260/vABC/content_list_v2.json
```

is accepted by the current `v[^/]+` pattern. If the intended policy is numeric
asset versions, tighten this to the same version grammar used elsewhere
(`v\\d+`) or document and test the broader grammar explicitly.

Required fix:

- avoid dynamically interpolating unescaped values into a regex, or escape all
  dynamic segments before constructing the regex;
- add negative tests for material IDs containing regex metacharacters;
- add a version-shape negative test if the policy is numeric `vN`;
- preserve all already-passing Task 261 behavior and safety boundaries.

## Accepted Partial Findings

The following parts are directionally correct and should be preserved during
the fix:

- canonical `metadata.rawMaterial.mineru.contentListV2` remains first priority;
- completed clean-job `sourceInput` fallback is constrained to completed jobs;
- pure legacy parsed evidence is not silently promoted into raw material;
- existing `v3` no-POST reconciliation bypasses `submitJob` and `queryJob` in
  the mock-safe test;
- explicit `allowProbeJobIdSuffix=true` is required for `-probe` acceptance;
- default/implicit probe policy rejects `-probe`;
- focused smoke tests, mock-safe CleanService loop, and `tsc --noEmit` passed.

## Return Boundary

This is a narrow return. Do not widen into runtime validation or evidence
beautification.

Lucode should correct the source-input path validation and tests only, update
the report/ledger, and push the same Lucode branch for Luceon re-review.

Still forbidden:

- runtime POST or submit-probe;
- live Mineru2Table query;
- DB/MinIO write;
- Docker/Compose/env/model/sample mutation;
- direct job-store edit;
- `v4`, fresh sample, or DB apply;
- UAT, L3, pressure PASS, readiness, production online, or go-live claim.
