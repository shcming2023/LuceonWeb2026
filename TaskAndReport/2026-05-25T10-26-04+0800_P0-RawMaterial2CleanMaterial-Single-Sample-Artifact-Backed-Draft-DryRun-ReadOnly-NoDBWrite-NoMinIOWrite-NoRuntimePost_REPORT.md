# TASK-20260525-102604 Lucode Report

## Task

- Task: `TASK-20260525-102604-P0-RawMaterial2CleanMaterial-Single-Sample-Artifact-Backed-Draft-DryRun-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost`
- Branch: `lucode/TASK-20260525-102604-P0-RawMaterial2CleanMaterial-Single-Sample-Artifact-Backed-Draft-DryRun-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost`
- Branch base before changes: `318bd775afb94fd69dc7535323760908f431494f`
- Report authoring HEAD: `dd1783c36ec8f34235928f9eeec77e285728b46d`
- Final pushed branch HEAD: see the pushed branch tip and Lucode final response. This report avoids a self-referential commit-hash loop because updating a report with its own final commit hash changes that commit hash.
- Status: Lucode implemented the mock-safe artifact-backed dry-run bridge and returned the task for Luceon review. The read-only canonical runtime rehearsal is blocked by missing required artifact object evidence.

## Changed Files

- `src/app/utils/rawMaterial2CleanMaterialArtifactBackedDraft.ts`
- `server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-25T10-26-04+0800_P0-RawMaterial2CleanMaterial-Single-Sample-Artifact-Backed-Draft-DryRun-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost_REPORT.md`

## Implementation Summary

- Added a pure `buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun()` helper.
- The helper accepts material/task metadata, an accepted input bundle, or a request object.
- The helper builds/reuses the Task 273 bundle, Task 275 request, and Task 276 draft skeleton.
- The helper requires an injected `artifactBodyReader` and reads only these required roles, in order:
  - `readable_tree`
  - `logic_tree`
  - `skeleton`
  - `flooded_content`
- The helper does not read optional artifacts such as `metrics`, `provenance`, or `unresolved_anchors`.
- The helper returns structured evidence for roles read, artifact refs read, source input, source clean material, section/block counts, sample source refs, and explicit false boundary flags for DB writes, MinIO writes, runtime POST, and optional artifact reads.
- Blocked outcomes cover missing input, missing reader, unsupported request kind, bundle/request blocking, artifact read failure, draft build failure, and live dependency markers.

## Mock-Safe Evidence

`node server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs` passed with:

- accepted bundle plus fake read-only reader produces `MOCK_ALGORITHM_DRAFT_READY`;
- request input is accepted directly;
- missing input returns `MISSING_INPUT`;
- missing reader returns `MISSING_ARTIFACT_READER`;
- injected read failure returns `ARTIFACT_READ_FAILED`;
- invalid injected body returns `DRAFT_BUILD_BLOCKED`;
- live dependency markers return `LIVE_DEPENDENCY_NOT_ALLOWED`;
- optional `metrics` artifact is not read;
- source refs preserve numeric IDs as strings in the mock proof: `101`, `logic-sec-2`, `201`, `301`, `blk-302`.

## Read-Only Canonical Rehearsal Evidence

Only task-authorized exact read-only GETs were attempted. No runtime POST, DB write, MinIO write/delete/list, Docker, job-store edit, upload, retry, reparse, or Re-AI operation was performed.

### Material And Task GETs

- `GET http://localhost:8081/__proxy/db/materials/1842780526581841`
  - Exit code: 0
  - HTTP status: 200
  - Evidence: canonical material was reachable and reports `metadata.cleanMaterials.toc-rebuild.latestVersion=v4`.
- `GET http://localhost:8081/__proxy/db/tasks/task-1779085089451`
  - Exit code: 0
  - HTTP status: 200
  - Evidence: canonical task was reachable and reports `metadata.cleanServiceJobs.toc-rebuild.assetVersion=v4`, `status=completed`, and the expected v4 artifact refs.

### Required Artifact GETs

The first required artifact read blocked before any draft body could be built:

- Role: `readable_tree`
- Bucket: `eduassets-clean`
- ObjectRef object: `toc-rebuild/1842780526581841/v4/readable_tree.md`
- Expected SHA-256 from task metadata: `bba5cf360fa7c0d92a9489ce84dfc40458de6072f812d7ab5d381b8e828946d7`
- Attempt 1:
  - URL shape: `/__proxy/upload/proxy-file?bucket=eduassets-clean&object=toc-rebuild%2F1842780526581841%2Fv4%2Freadable_tree.md`
  - Exit code: 0
  - HTTP status: 400
  - Response summary: `{"error":"缺少 objectName 参数"}`
- Attempt 2:
  - URL shape: `/__proxy/upload/proxy-file?bucket=eduassets-clean&objectName=toc-rebuild%2F1842780526581841%2Fv4%2Freadable_tree.md`
  - Exit code: 0
  - HTTP status: 500
  - Response summary: `{"error":"The specified key does not exist."}`

Helper result from the canonical rehearsal:

```json
{
  "ok": false,
  "code": "ARTIFACT_READ_FAILED",
  "reason": "read-only artifact body reader failed for readable_tree",
  "details": {
    "role": "readable_tree",
    "object": "toc-rebuild/1842780526581841/v4/readable_tree.md",
    "error": "GET /__proxy/upload/proxy-file?bucket=eduassets-clean&objectName=toc-rebuild%2F1842780526581841%2Fv4%2Freadable_tree.md failed with HTTP 500: {\"error\":\"The specified key does not exist.\"}"
  },
  "readLog": []
}
```

Because the first required artifact body is not retrievable through the read-only proxy, the real canonical rehearsal stopped under the task Stop Rule. `logic_tree`, `skeleton`, and `flooded_content` were not fetched after the missing `readable_tree` object blocked the run.

## Commands

- `node server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs`
  - Exit code: 0
- `node server/tests/rawmaterial2cleanmaterial-protocol-runner-smoke.mjs`
  - Exit code: 0
- `node server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs`
  - Exit code: 0
- `node server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs`
  - Exit code: 0
- `npx pnpm@10.4.1 exec tsc --noEmit`
  - Exit code: 0
- `npx pnpm@10.4.1 run build`
  - Exit code: 0
  - Note: Vite emitted the existing chunk-size warning.
- `git diff --check origin/main...HEAD`
  - Exit code: 0

## Boundary Confirmation

- DB POST/PATCH/PUT/DELETE/apply: not performed.
- DB reads: only the two task-authorized material/task GETs were performed.
- MinIO write/delete/list/bucket scan: not performed.
- Artifact body reads: attempted only exact required ObjectRef proxy GET for `readable_tree`; blocked before any further artifact body read.
- Runtime POST, endpoint/service/worker execution: not performed.
- Docker/Compose operations: not performed.
- Job-store edits: not performed.
- Upload/retry/reparse/Re-AI/repair/reset/cancel: not performed.
- UI workflow work: not performed.
- Readiness, UAT, L3, pressure PASS, production, or go-live claim: not made.

## Residual Debt / Next Step

- The code-level bridge is ready for Luceon review at mock-safe helper/test level.
- The canonical artifact-backed rehearsal is blocked because `eduassets-clean/toc-rebuild/1842780526581841/v4/readable_tree.md` is referenced in task metadata but is not retrievable through the read-only proxy.
- A Luceon-side follow-up should decide whether this is an artifact availability issue, bucket/config mismatch, or metadata/ObjectRef mismatch before any downstream RawMaterial2CleanMaterial real artifact-body proof is attempted.
