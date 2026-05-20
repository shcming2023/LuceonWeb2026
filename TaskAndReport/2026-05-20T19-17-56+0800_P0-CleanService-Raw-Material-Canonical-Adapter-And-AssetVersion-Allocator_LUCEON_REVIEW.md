# P0 CleanService Raw Material Canonical Adapter And AssetVersion Allocator Luceon Review

- **Task ID**: `TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator`
- **Review Time**: `2026-05-20T19:17:56+0800`
- **Reviewed Branch**: `origin/lucode/TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator`
- **Reviewed Branch HEAD**: `4be1aeadc0efb724ccc141b720d8baf6eef8c368`
- **Base Main Before Review Merge**: `26da1b0800f2bbbe331e001fa4c9f78f93754be5`
- **Decision**: `ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_EVIDENCE_CORRECTION`

## Acceptance Boundary

Accepted at code/test level only.

The accepted scope is the mock-safe CleanService foundation for canonical Raw Material dispatch eligibility and Luceon-owned asset version allocation:

- `server/services/cleanservice/raw-material-adapter.mjs`
- `server/services/cleanservice/asset-version.mjs`
- `server/services/cleanservice/cleanservice-worker.mjs`
- focused CleanService smoke tests

This review does not accept production deployment, runtime activation, real Mineru2Table dispatch, live MinIO reads/writes, DB migration, legacy backfill, UAT, L3, pressure PASS, release readiness, or go-live.

## Evidence Correction

The submitted report and ledger still referenced the pre-amend correction HEAD `7ead10b72fd428bb1e8c367119cc5a9c57faf331`.

Luceon fetched the remote branch and confirmed the actual final remote branch HEAD:

```text
4be1aeadc0efb724ccc141b720d8baf6eef8c368
```

Because the code/test boundary passed and the remaining problem was a control-plane evidence mismatch, Luceon corrected the report and ledger during acceptance instead of returning the task again.

## Path Audit

Command:

```bash
git diff --name-status origin/main..origin/lucode/TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator
```

Output:

```text
A       TaskAndReport/2026-05-19T16-07-53+0800_P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
A       server/services/cleanservice/asset-version.mjs
M       server/services/cleanservice/cleanservice-worker.mjs
A       server/services/cleanservice/raw-material-adapter.mjs
A       server/tests/cleanservice-asset-version-smoke.mjs
A       server/tests/cleanservice-raw-material-adapter-smoke.mjs
M       server/tests/cleanservice-worker-shell-smoke.mjs
```

Exit code: `0`.

## Luceon Verification

Commands run from `/Users/concm/prod_workspace/Luceon2026` after fast-forward integration:

```bash
node --check server/services/cleanservice/cleanservice-worker.mjs && node --check server/services/cleanservice/raw-material-adapter.mjs && node --check server/services/cleanservice/asset-version.mjs && node --check server/tests/cleanservice-worker-shell-smoke.mjs && node --check server/tests/cleanservice-raw-material-adapter-smoke.mjs && node --check server/tests/cleanservice-asset-version-smoke.mjs
```

Exit code: `0`.

```bash
node server/tests/cleanservice-worker-shell-smoke.mjs && node server/tests/cleanservice-raw-material-adapter-smoke.mjs && node server/tests/cleanservice-asset-version-smoke.mjs
```

Observed result:

```text
=== CleanService Worker Shell Smoke ===
PASS cleanservice worker shell smoke
=== Raw Material Adapter Smoke ===
PASS raw material adapter smoke
=== Asset Version Allocator Smoke ===
PASS asset version allocator smoke
```

Exit code: `0`.

```bash
npx pnpm@10.4.1 exec tsc --noEmit
```

Exit code: `0`.

Luceon also ran a focused legacy parsed-only reproducer and confirmed:

- `status = skipped-policy`
- `submitted = 0`
- `persisted = 1`
- `submitJob` was not called
- persisted `cleanServiceJobs.toc-rebuild.input = null`

Exit code: `0`.

## Accepted Findings

- `CLEANSERVICE_ENABLED=false` still returns `disabled-noop` and does not scan, submit, or persist.
- Canonical Raw Material input is restricted to `metadata.rawMaterial.mineru.contentListV2` with bucket `eduassets-raw` and `/content_list_v2.json` object suffix.
- Legacy parsed-only evidence is not upgraded into dispatch eligibility; it is captured as `skipped-policy` with zero submit.
- Asset version allocation increments from existing terminal versions and blocks active duplicate jobs.
- The implementation does not wire `upload-server`, production traffic, real HTTP transport, external Mineru2Table state, MinIO, DB, Docker volumes, models, or samples.

## Residual Boundary

Task 224 should inspect `/Users/concm/prod_workspace/Mineru2Tables` and freeze the real Mineru2Table standalone API/runtime contract before any Luceon-side bridge implementation is authorized.
