# Luceon Review v2 - Task 261 Existing v3 No-POST Reconciliation

Review time: 2026-05-24T14:28:48+0800

Task:

```text
TASK-20260524-135419-P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime
```

Reviewed branch:

```text
origin/lucode/TASK-20260524-135419-P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime@7218318b6b020d5e613a0c0d6e731976b2f3e1ed
```

Verdict:

```text
ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_INTEGRATION
```

## Review Boundary

This review used the Lucode branch-handoff rule. `origin/main` still showed
Task 261 as `Next Actor=Lucode`, while the matching Lucode branch had
branch-local `Status=Lucode 已回报待 Luceon 审查` and `Next Actor=Luceon`.

Acceptance is mock-safe code/test level only. It does not accept runtime
success, live `v3` validation, DB metadata apply, worker/scheduler activation,
UAT, L3, pressure PASS, readiness, production online, or go-live.

No runtime POST, live Mineru2Table query, DB/MinIO/Docker/env/model/sample
mutation, job-store edit, or real DB apply was performed by Luceon.

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
/tmp/luceon-task261-rereview.FQuLu2
```

Checks:

```text
node --check server/services/cleanservice/raw-material-adapter.mjs: exit 0
node --check server/services/cleanservice/cleanservice-worker.mjs: exit 0
node --check server/services/cleanservice/orchestration-runner.mjs: exit 0
node --check server/tests/cleanservice-raw-material-adapter-smoke.mjs: exit 0
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs: exit 0
node server/tests/cleanservice-raw-material-adapter-smoke.mjs: exit 0
node server/tests/cleanservice-orchestration-runner-smoke.mjs: exit 0, 26/26
node server/tests/cleanservice-output-verifier-smoke.mjs: exit 0, 9/9
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs: exit 0
mock-safe cleanservice-*.mjs loop excluding Task 256 runtime harness: exit 0
npx pnpm@10.4.1 exec tsc --noEmit: exit 0
```

Independent Luceon return-fix probes:

```text
materialId=mat.260 accepts only mineru/mat.260/v12/content_list_v2.json: passed
materialId=mat.260 rejects mineru/matX260/v12/content_list_v2.json: passed
materialId=mat.260 rejects mineru/mat.260/vABC/content_list_v2.json: passed
legacy parsed-only evidence still throws legacy-parsed-evidence-skipped: passed
```

The Task 256 runtime harness was intentionally skipped because Task 261
forbids running that runtime harness.

## Accepted Findings

The return blocker is closed:

- `raw-material-adapter.mjs` now validates source-input object paths by splitting
  path segments and comparing literal materialId/version/file segments instead
  of interpolating dynamic values into a regex.
- Version segments are constrained to numeric `vN`.
- Regression tests cover material IDs with regex metacharacters and reject
  wrong-material paths such as `mineru/matX260/...` for `materialId=mat.260`.
- Regression tests reject non-numeric versions such as `vABC`.

The original Task 261 objectives are accepted at code/test level:

- canonical `metadata.rawMaterial.mineru.contentListV2` remains first priority;
- completed clean-job `sourceInput` fallback is bounded, traceable, and requires
  `eduassets-raw`, `mineru/<materialId>/vN/content_list_v2.json`, and SHA256;
- pure legacy parsed evidence is not silently promoted into raw material;
- existing `v3` no-POST reconciliation bypasses `submitJob` and `queryJob` in
  the mock-safe test;
- explicit `allowProbeJobIdSuffix=true` is required for `-probe` acceptance;
- default/implicit probe policy rejects `-probe`;
- real apply and mismatch/failed/one-sided/missing-jobId histories remain
  blocked by existing tests.

## Integration

Luceon integrated the reviewed Lucode branch into `main` with the acceptance
review and ledger closure in the merge commit.

## Acceptance Boundary

Task 261 is accepted only as:

```text
Mock-safe product code/test evidence for source-input compatibility and
existing-v3 no-POST product reconciliation.
```

Acceptance does not mean:

- Task 256 is retroactively runtime-successful;
- any runtime POST or live Mineru2Table query was run;
- live `v3` artifacts were revalidated in runtime;
- DB metadata is updated to `v3`;
- `v4`, fresh sample, or DB apply is authorized;
- CleanService worker/scheduler/upload-server integration is activated;
- UAT, L3, pressure PASS, production readiness, release readiness, production
  online, or go-live.
