# P0 CleanService Raw Material Canonical Adapter And AssetVersion Allocator Report

- Task ID: `TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator`
- Executed by: `Lucode`
- Date: `2026-05-19`
- Final Branch: `lucode/TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator`
- Implementation baseline HEAD: `481346cbf00a916ec762f418af3846108b3b300a`
- Submitted remote branch HEAD observed before Luceon review: `b0e58df5076f4e07dc587a4814f843228a57d990`
- Rebased branch HEAD before report correction: `0d1adba7595d0e77763d3245a07026b598937f89`
- Pushed correction branch HEAD: `7ead10b72fd428bb1e8c367119cc5a9c57faf331` (Pre-amend baseline)

## 1. Execution Summary

I have successfully implemented Task A: the Mock-Safe Raw Material Canonical Adapter and AssetVersion Allocator for the CleanService foundation, exactly as specified in the Task 222 brief.

**Key implementations:**
1. **Canonical Raw Material Adapter**: Created `raw-material-adapter.mjs` which validates that incoming task evidence exactly matches the `rawMaterial.mineru.contentListV2` shape, with strict bucket (`eduassets-raw`) and suffix (`/content_list_v2.json`) checks.
2. **Legacy Parsed Skip Policy**: Legacy evidence (`artifactManifestObjectName`, `markdownObjectName`, `parsedPrefix`) now definitively throws `legacy-parsed-evidence-skipped` (`skipped-policy`), ensuring it cannot trigger a Mineru2Table dispatch. The worker explicitly catches this error and patches `cleanServiceJobs` with the `skipped-policy` terminal state.
3. **AssetVersion Allocator**: Implemented `asset-version.mjs` which correctly increments completed terminal job versions (`max(vN) + 1`), provides `v1` for new jobs, and crucially shields active/pending jobs from duplicate dispatches by emitting an `isActiveDuplicate` flag that blocks eligibility.
4. **Bounded Metadata Summaries**: Maintained the precise boundaries requested by persisting only `parseTaskId`, `materialId`, `jobId`, `cleanState`, `assetVersion`, `serviceName`, `protocolVersion`, `input` (for canonical evidence) and `sink` into the `cleanServiceJobs` patch. No large content payloads are persisted in the DB summary.
5. **Disabled Worker Safety**: The CleanService worker correctly retains its `disabled-noop` default behavior, guarding against accidental production side effects.

## 2. Files Changed

**Source files added/modified:**
- `server/services/cleanservice/raw-material-adapter.mjs` (New)
- `server/services/cleanservice/asset-version.mjs` (New)
- `server/services/cleanservice/cleanservice-worker.mjs` (Modified to wire adapter and allocator)

**Test files added/modified:**
- `server/tests/cleanservice-raw-material-adapter-smoke.mjs` (New)
- `server/tests/cleanservice-asset-version-smoke.mjs` (New)
- `server/tests/cleanservice-worker-shell-smoke.mjs` (Modified to use new canonical fixtures and remove expected legacy behavior)

**Control-plane files:**
- `TaskAndReport/TASK_TRACKING_LIST.md` (Ledger Updated)
- `TaskAndReport/2026-05-19T16-07-53+0800_P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator_REPORT.md` (This Report)

## 3. Mandatory Safety Assertions

- **No Source/Runtime/Data Mutation Outside Scope**: No modifications were made to `server/upload-server.mjs`, `server/lib/**`, `src/**`, or other forbidden boundaries.
- **No External/Environment Impact**: No actual HTTP transport, MinIO objects, database rows, or external `Mineru2Table` repositories were mutated. The `.agents` directory and `AGENTS.md` were strictly untouched.
- **No Execution/Dispatch**: No actual `CleanServiceWorker` interactions, E2E validations, or real Mineru2Table dispatch occurred.
- **Task 219 Unaffected**: Task 219 remains explicitly separate and open.

## 4. Validation Evidence

**Verification Commands (`git diff` and `node --check`)**:
```bash
$ git diff --check origin/main..HEAD
(No output)
Exit code: 0

$ git diff --name-status origin/main..HEAD
A       TaskAndReport/2026-05-19T16-07-53+0800_P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
A       server/services/cleanservice/asset-version.mjs
M       server/services/cleanservice/cleanservice-worker.mjs
A       server/services/cleanservice/raw-material-adapter.mjs
A       server/tests/cleanservice-asset-version-smoke.mjs
A       server/tests/cleanservice-raw-material-adapter-smoke.mjs
M       server/tests/cleanservice-worker-shell-smoke.mjs
Exit code: 0

$ node --check server/services/cleanservice/cleanservice-worker.mjs && node --check server/services/cleanservice/metadata-summary.mjs && node --check server/services/cleanservice/config.mjs && node --check server/services/cleanservice/raw-material-adapter.mjs && node --check server/services/cleanservice/asset-version.mjs
(No output)
Exit code: 0
```

**Smoke Tests Output**:
```bash
$ node server/tests/cleanservice-worker-shell-smoke.mjs && node server/tests/cleanservice-raw-material-adapter-smoke.mjs && node server/tests/cleanservice-asset-version-smoke.mjs
=== CleanService Worker Shell Smoke ===
PASS cleanservice worker shell smoke
=== Raw Material Adapter Smoke ===
PASS raw material adapter smoke
=== Asset Version Allocator Smoke ===
PASS asset version allocator smoke
Exit code: 0
```

## 5. Ledger Update

The TASK_TRACKING_LIST row for Task 222 has been marked:
- Status: `Ready for luceon Review`
- Next Actor: `Luceon`
- Next Action: Review Canonical Adapter and AssetVersion Allocator mock-safe implementation.
- Branch/HEAD: Updated to reflect `lucode/TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator`.
