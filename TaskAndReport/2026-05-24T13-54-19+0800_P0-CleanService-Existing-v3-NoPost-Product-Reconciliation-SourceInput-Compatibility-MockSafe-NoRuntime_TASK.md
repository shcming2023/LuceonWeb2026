# TASK-20260524-135419-P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime

Issued at: 2026-05-24T13:54:19+0800

Assigned actor: `Lucode`

## 1. Mainline Objective

Task 260 established the safest next target after Task 259:

```text
existing v3 no-POST product reconciliation
plus source-input compatibility
before any runtime POST, v4, fresh sample, or DB apply
```

The mainline question for this task is:

> Can the current CleanService product path consume the live-shaped canonical
> sample state without Task 256 harness injection, and reconcile existing `v3`
> diagnostic artifacts through the product chain without runtime submission?

This is a mock-safe/no-runtime implementation task. It must improve product
code and tests only. It must not create new runtime evidence.

## 2. Current Evidence

Control-plane baseline:

```text
origin/main@30f3340b5218d46d9f4bd456a0494fd1d9a736b3
```

Relevant accepted evidence:

- Task 259 accepted mock-safe product fixes for live-shaped artifact
  provenance, explicit `job_id -probe` policy, and explicit new-version
  dry-run conflict semantics.
- Task 260 confirmed current DB remains accepted `v2`:
  `task-1779085089451` / `materialId=1842780526581841` have completed
  `toc-rebuild` metadata for
  `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230`.
- Task 260 confirmed physical/job-store `v3` evidence exists but is diagnostic,
  not DB-applied:
  - canonical job key `luceon-task-1779085089451-toc-rebuild-v3`;
  - probe job key `luceon-task-1779085089451-toc-rebuild-v3-probe`;
  - both point to the same `toc-rebuild/1842780526581841/v3/` prefix.
- Task 260 confirmed current verifier can validate existing `v3` only with
  explicit `allowProbeJobIdSuffix=true`.
- Task 260 confirmed full runner with the live DB payload currently throws
  `legacy-parsed-evidence-skipped` before any side effect because
  `task.metadata.rawMaterial.mineru.contentListV2` is absent.
- Task 260 recorded accepted source input from current metadata:

```text
bucket=eduassets-raw
object=mineru/1842780526581841/v1/content_list_v2.json
sha256=f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
size_bytes=31543
```

## 3. Critical Path Scope

Implement the minimum product behavior needed for a no-runtime product-chain
reconciliation:

1. Source-input compatibility:
   - keep canonical `metadata.rawMaterial.mineru.contentListV2` as the first
     source of truth;
   - when the canonical branch is absent, allow a bounded fallback to the
     accepted CleanService `sourceInput` already present on completed
     `metadata.cleanServiceJobs[serviceName]`;
   - validate that fallback strictly: bucket must be `eduassets-raw`, object
     must be `mineru/<materialId>/vN/content_list_v2.json`, SHA256 must be
     present, and size must be propagated when available;
   - do not infer source input from legacy parsed evidence alone.
2. Existing-`v3` no-POST product reconciliation:
   - add or refine an explicit mock-safe product path for reconciling an
     existing completed CleanService job response without calling runtime
     submit;
   - this path may use injected fixture dependencies, but must not perform
     real `POST /api/v1/jobs`, live Mineru2Table query, DB write, or MinIO
     write;
   - the product chain must verify existing `v3` artifact refs, preserve
     canonical vs observed provenance job IDs, and reach dry-run success only
     under explicit probe-suffix policy.
3. Preserve existing safety behavior:
   - default/false `allowProbeJobIdSuffix` must still reject `-probe`;
   - real apply over incompatible existing metadata must remain blocked;
   - mismatch intent/version/history cases must remain blocked;
   - default current-applied `v2` noop behavior must remain intact.

## 4. True Preconditions

Lucode must begin from current `origin/main` and create a Lucode branch.

Before coding, confirm:

```bash
git status --short --branch
git fetch origin --prune --tags
git pull --ff-only origin main
git rev-parse HEAD origin/main
```

If the branch cannot remain mock-safe/no-runtime, stop and report blocked.

## 5. Deferrable Side Work

Do not include:

- runtime POST or idempotent submit;
- `POST /api/v1/jobs:from-storage`;
- live Mineru2Table query;
- direct live DB/MinIO/job-store reads to create new evidence;
- new `v4` target;
- fresh sample route;
- real DB metadata apply;
- DB/MinIO cleanup, reset, rollback, overwrite, copy, move, or delete;
- Docker/Compose restart, recreate, rebuild, down/up, volume operation, or env
  change;
- upload-server scheduler/worker activation;
- operator UI work;
- RawMaterial2CleanMaterial work;
- broader pressure, batch, UAT, L3, readiness, or go-live validation.

## 6. Environment And Write Boundary

Lucode implementation workspace:

```text
/Users/concm/Dev_workspace/Luceon2026
```

Target branch:

```text
lucode/TASK-20260524-135419-P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime
```

Allowed write files:

```text
server/services/cleanservice/raw-material-adapter.mjs
server/services/cleanservice/cleanservice-worker.mjs
server/services/cleanservice/orchestration-runner.mjs
server/services/cleanservice/output-verifier.mjs
server/services/cleanservice/metadata-summary.mjs
server/services/cleanservice/metadata-persistence.mjs
server/services/cleanservice/metadata-apply-executor.mjs
server/tests/cleanservice-*.mjs
TaskAndReport/2026-05-24T13-54-19+0800_P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

The implementation should touch the smallest subset of the allowed source
surface. Do not edit a file merely because it is listed here.

Allowed read sources:

```text
TaskAndReport/2026-05-24T12-50-20+0800_P0-CleanService-PostTask259-ReadOnly-Revalidation-Target-Dossier_REPORT.md
TaskAndReport/2026-05-24T12-39-29+0800_P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime_LUCEON_REVIEW-v2.md
TaskAndReport/2026-05-24T11-21-26+0800_P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite_LUCEON_REVIEW-v3.md
server/services/cleanservice/**
server/tests/cleanservice-*.mjs
```

Forbidden write files and operations:

```text
docs/**
src/**
docker-compose.yml
.env
.env.*
package.json
pnpm-lock.yaml
AGENTS.md
.agents/**
/Users/concm/prod_workspace/Mineru2Tables/**
```

Do not modify or run the Task 256 runtime harness:

```text
server/tests/cleanservice-task256-explicit-new-version-runtime-dryrun.mjs
```

## 7. Safety Boundary

Strictly forbidden:

- `POST /api/v1/jobs`;
- `POST /api/v1/jobs:from-storage`;
- runtime submit-probe;
- live Mineru2Table job query;
- DB PATCH/POST/PUT/DELETE;
- MinIO put/copy/move/delete/write/delete-marker operation;
- direct `jobs.json` write/edit;
- Docker/Compose restart/recreate/build/down/up/volume/prune;
- env/credential/model/sample-file mutation;
- cleanup/reset/rollback/repair/reparse/re-AI;
- worker/scheduler activation;
- real DB apply;
- UAT, L3, pressure PASS, production readiness, release readiness, production
  online, or go-live declaration.

Mock tests may use in-memory fixtures based on Task 260 evidence. They must not
fetch live DB/MinIO/job-store data.

## 8. Fast Validation Target

Minimum useful proof:

1. a focused source-input compatibility test where:
   - canonical `metadata.rawMaterial` still wins;
   - completed clean job `sourceInput` fallback works when canonical
     `rawMaterial` is absent;
   - pure legacy parsed evidence without sourceInput remains blocked/skipped;
   - invalid bucket/object/materialId/missing SHA cases are blocked.
2. a focused existing-`v3` no-POST reconciliation test where:
   - no submit dependency is invoked;
   - no runtime query dependency is invoked;
   - injected completed job fixture uses canonical job id
     `luceon-task-1779085089451-toc-rebuild-v3`;
   - provenance fixture uses observed job id
     `luceon-task-1779085089451-toc-rebuild-v3-probe`;
   - explicit probe-suffix policy yields dry-run success with preserved
     canonical/observed IDs and warning;
   - default/false probe-suffix policy still fails.
3. a regression test that real apply and mismatch history remain blocked.

## 9. Required Checks

Run and record exact commands and exit codes:

```bash
git status --short --branch
git fetch origin --prune --tags
git pull --ff-only origin main
git rev-parse HEAD origin/main
git diff --name-status origin/main...HEAD
git diff --check origin/main...HEAD
```

Run focused syntax checks for changed modules and tests, for example:

```bash
node --check server/services/cleanservice/raw-material-adapter.mjs
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/tests/<changed-cleanservice-test>.mjs
```

Run focused CleanService smokes covering this task plus regressions:

```bash
node server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
```

Run all mock-safe CleanService tests while explicitly excluding the Task 256
runtime harness:

```bash
for f in server/tests/cleanservice-*.mjs; do
  case "$f" in
    *cleanservice-task256-explicit-new-version-runtime-dryrun.mjs) continue ;;
  esac
  node "$f"
done
```

Run TypeScript if local dependencies are available without installation:

```bash
npx pnpm@10.4.1 exec tsc --noEmit
```

If dependency availability blocks `tsc`, report the exact blocker. Do not
install packages or edit package metadata.

## 10. Report Requirements

Create:

```text
TaskAndReport/2026-05-24T13-54-19+0800_P0-CleanService-Existing-v3-NoPost-Product-Reconciliation-SourceInput-Compatibility-MockSafe-NoRuntime_REPORT.md
```

The report must include:

- exact branch name and full remote HEAD;
- baseline `origin/main` SHA;
- changed-file list using three-dot diff;
- source-input compatibility policy implemented;
- existing-`v3` no-POST reconciliation behavior implemented;
- focused positive and negative test evidence;
- exact proof that no submit/runtime-query/db-write/minio-write dependencies
  were invoked in the no-POST reconciliation test;
- skipped checks with reasons;
- safety statement;
- residual risk and next recommended step.

Update `TaskAndReport/TASK_TRACKING_LIST.md` on the Lucode branch:

- mark this task as `Lucode 已回报待 Luceon 审查`;
- set `Next Actor=Luceon`;
- include report path, branch name, and full remote HEAD after push.

Push the Lucode branch to GitHub.

## 11. Positive Acceptance Criteria

Luceon may accept when:

- product code no longer requires harness injection of `metadata.rawMaterial`
  for the current accepted source-input shape;
- fallback source input is explicitly bounded and traceable;
- pure legacy parsed evidence is not silently promoted into canonical raw
  material;
- existing `v3` no-POST reconciliation reaches dry-run success through product
  code using injected fixtures and no submit/runtime-query side effects;
- canonical and `-probe` provenance job IDs are preserved and audited;
- default/false probe-suffix policy still rejects `-probe`;
- real apply and mismatch cases remain blocked;
- focused and regression checks pass;
- report and ledger evidence are GitHub-visible and current.

## 12. Negative Acceptance Criteria

Return or block if:

- any runtime POST, submit-probe, live job query, DB write, MinIO write,
  Docker/env mutation, job-store edit, cleanup/reset, `v4`, fresh sample, or
  DB apply is performed;
- code accepts `-probe` provenance by default;
- code derives raw material from legacy parsed evidence without a validated
  sourceInput;
- source-input fallback accepts missing SHA, wrong bucket, wrong materialId, or
  non-`content_list_v2.json` object paths;
- tests rely on live runtime state rather than fixtures;
- report claims runtime validation, UAT, L3, pressure PASS, readiness, or
  go-live.

## 13. Review Boundary

Acceptance of this task would mean only:

```text
Mock-safe product code/test evidence supports source-input compatibility and
existing-v3 no-POST product reconciliation.
```

It would not mean:

- Task 256 is retroactively accepted as runtime success;
- a new runtime run occurred;
- DB metadata is updated to `v3`;
- `v4` is authorized;
- a fresh sample is authorized;
- CleanService worker/scheduler/upload-server integration is activated;
- UAT, L3, pressure PASS, production readiness, release readiness, production
  online, or go-live.
