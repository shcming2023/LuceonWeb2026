# P0 CleanService Raw Material Canonical Adapter And AssetVersion Allocator

- Task ID: `TASK-20260519-160753-P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator`
- Issued at: `2026-05-19T16:07:53+0800`
- Issuer: `Luceon`
- Next Actor: `Lucode`
- Status: `待执行`
- Priority: `P0`
- Scope type: code/test implementation, mock-safe only

## 1. Background

Task 220 is accepted at documentation level and establishes:

```text
PDF -> Raw Material -> Clean Material
```

Task 221 is accepted at design level only. It authorizes the first implementation step from the sequence: Task A, the Raw Material canonical adapter and assetVersion allocator inside the disabled CleanService foundation.

This task does not authorize real Mineru2Table dispatch, runtime startup wiring, production deployment, data migration, legacy backfill, or RawMaterial2CleanMaterial implementation.

## 2. Current Evidence

Current Luceon review/merge anchor:

- `origin/main` before Task 221 merge: `b7ab250ecbf7dcb77a9fb78f7553a62a95c6c7c2`
- accepted Task 221 branch: `origin/lucode/task-221-mineru2table-design`
- accepted Task 221 HEAD: `1b364c2b5f1c2677a40434ab1da900237b076fc6`

Relevant source facts:

- `server/services/cleanservice/cleanservice-worker.mjs` exists and is disabled by default through `CLEANSERVICE_ENABLED=false`.
- The current worker-shell input builder accepts legacy parsed evidence: `artifactManifestObjectName`, `markdownObjectName`, or `parsedPrefix`.
- The accepted Task 220/221 direction requires canonical Raw Material input for Mineru2Table: `eduassets-raw/mineru/{materialId}/{assetVersion}/content_list_v2.json`.
- The current worker-shell defaults `assetVersion` to metadata or `v1`; there is no accepted Luceon-owned allocator.
- `CleanServiceWorker` is not wired into `server/upload-server.mjs`.
- Real external Mineru2Table protocol support remains unaccepted.
- Task 219 remains open and separate; do not modify or close it.

## 3. Objective

Implement the mock-safe Task A foundation:

1. define and test a canonical Raw Material input adapter for Mineru2Table;
2. reject or classify legacy parsed-only evidence without pseudo-provenance;
3. implement and test Luceon-owned monotonic `assetVersion` allocation;
4. keep CleanService disabled by default and free of real network, runtime, DB, MinIO, Docker, model, sample, or external repository effects.

The outcome should make future Task B/C work safer by ensuring only canonical Raw Material ObjectRefs can enter a CleanService job request.

## 4. Write Boundary

Allowed source/test files:

- `server/services/cleanservice/cleanservice-worker.mjs`
- `server/services/cleanservice/metadata-summary.mjs`
- `server/services/cleanservice/config.mjs`
- optional new `server/services/cleanservice/raw-material-adapter.mjs`
- optional new `server/services/cleanservice/asset-version.mjs`
- `server/tests/cleanservice-worker-shell-smoke.mjs`
- optional new `server/tests/cleanservice-raw-material-adapter-smoke.mjs`
- optional new `server/tests/cleanservice-asset-version-smoke.mjs`

Allowed control-plane files:

- `TaskAndReport/2026-05-19T16-07-53+0800_P0-CleanService-Raw-Material-Canonical-Adapter-And-AssetVersion-Allocator_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Read-only inspection is allowed for:

- accepted Task 220/221 files;
- `docs/prd/Luceon2026-PRD-v0.4.md`;
- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`;
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`;
- `docs/contracts/CleanService-Protocol-v1.md`;
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`;
- `/Users/concm/prod_workspace/Mineru2Tables` for protocol naming or shape confirmation only.

Forbidden files and areas:

- `server/upload-server.mjs`
- `server/lib/**`
- `src/**`
- `package.json`
- `pnpm-lock.yaml`
- `pnpm-workspace.yaml`
- `docker-compose*.yml`
- `.env*`, secrets, runtime overrides, local config
- `AGENTS.md`
- `.agents/**`
- external Mineru2Table repository edits, commits, pushes, service restarts, or deployments
- sample files, MinIO objects, DB rows, Docker volumes, model files, production data
- PRD/architecture/contract rewrites outside the TaskAndReport evidence required here

## 5. Required Implementation

### 5.1 Canonical Raw Material Adapter

Add a pure adapter/classifier that can determine whether a task has valid canonical Raw Material evidence for `toc-rebuild`.

Accepted canonical evidence shape:

```json
{
  "metadata": {
    "rawMaterial": {
      "version": "v1",
      "mineru": {
        "contentListV2": {
          "bucket": "eduassets-raw",
          "object": "mineru/<materialId>/v1/content_list_v2.json",
          "sha256": "optional-sha256",
          "size_bytes": 12345
        }
      }
    }
  }
}
```

The resulting CleanService input ObjectRef must use:

```json
{
  "role": "mineru-content",
  "source": {
    "type": "minio",
    "bucket": "eduassets-raw",
    "object": "mineru/<materialId>/<assetVersion>/content_list_v2.json"
  }
}
```

Rules:

- Do not synthesize canonical object existence from `materialId` alone.
- Do not silently convert `artifactManifestObjectName`, `markdownObjectName`, or `parsedPrefix` into canonical Raw Material evidence.
- If only legacy parsed evidence exists, classify it as `skipped-policy` or `not-applicable` and do not submit a job.
- If canonical object evidence has the wrong bucket, missing object, wrong filename, or mismatched material/version path, reject it with a deterministic reason.

### 5.2 AssetVersion Allocator

Implement a pure Luceon-owned allocator for CleanService asset versions.

Required semantics:

- accepted version format is `v<number>`, for example `v1`, `v2`, `v12`;
- if there is no prior clean summary, allocate `v1`;
- if bounded task/material metadata already records completed terminal clean versions, allocate `max(vN) + 1` for a new clean job;
- if an active clean job already exists for the service (`pending`, `running`, `review-pending-partial`, `cost-decision`), preserve its existing `jobId` and `assetVersion` and do not create a duplicate request;
- invalid version strings must not become the next version by accident;
- allocation must be deterministic from the passed task/material metadata and must not query DB, MinIO, filesystem, Docker, or external services.

### 5.3 Job Request Shape

Update `buildCleanServiceJobRequest` or the surrounding request builder so the mock-safe request uses the canonical adapter and allocator:

- `job_id`: deterministic, for example `luceon-${parseTaskId}-${serviceName}-${assetVersion}`;
- `material_id`, `parse_task_id`, `asset_version`;
- `inputs[0].role = "mineru-content"`;
- input bucket/object from canonical Raw Material evidence only;
- sink bucket/prefix under `eduassets-clean/toc-rebuild/{materialId}/{assetVersion}/`;
- `options.max_cost_cny` uses the existing hard limit default `8`.

### 5.4 Bounded Metadata Summary

Where this task touches submitted-job or mock-result metadata summaries, keep only bounded fields:

- `jobId`, `serviceName`, `protocolVersion`, `materialId`, `parseTaskId`, `assetVersion`;
- input role/bucket/object/hash when known;
- sink bucket/prefix;
- status/cleanState, timestamps, error code, retriable flag;
- provenance/output ObjectRefs after completion.

Do not persist large content, JSON tree bodies, Markdown bodies, model-generated free text, or copied artifact payloads in DB metadata.

### 5.5 Disabled Worker Safety

Preserve current disabled behavior:

- with `CLEANSERVICE_ENABLED=false`, `tickOnce()` must not scan tasks;
- it must not submit jobs;
- it must not persist metadata;
- it must return `disabled-noop`.

## 6. Mandatory Data Governance Red Lines

Because this task concerns AI data processing, educational assets, and future clean outputs, preserve these red lines:

1. ID-only extraction: service/model outputs that select source content must reference stable Block IDs or source references. They must not invent, rewrite, or hallucinate free text as source truth.
2. Asset hash locking: image/audio/resource assets must preserve original hash names through the pipeline. Services must not rename original resource hashes by convenience.
3. Pure layout/code-generation boundary: if later LaTeX/TikZ or code-like clean output is introduced, it must use standard packages and avoid custom commands/macros unless a future task explicitly authorizes otherwise.

## 7. Acceptance Criteria

Positive acceptance:

- canonical `rawMaterial.mineru.contentListV2` evidence builds a `mineru-content` ObjectRef and valid job request;
- legacy parsed-only evidence is not eligible for dispatch and is classified as `skipped-policy` or `not-applicable`;
- assetVersion allocation covers `v1`, next `vN`, invalid-version ignore/reject behavior, and active-job idempotency;
- metadata summaries remain bounded and contain no large artifact content;
- disabled worker no-op behavior is preserved;
- all changed source files pass syntax checks and focused smoke tests.

Negative acceptance:

- no real HTTP transport or external network call;
- no `server/upload-server.mjs` wiring;
- no production service startup, deployment, upload, submit-probe, pressure, retry, reparse, re-AI, DB/MinIO/Docker/model/sample mutation;
- no external Mineru2Table edits or runtime changes;
- no legacy asset migration, backfill, reparse, deletion, or pseudo-provenance;
- no Task 219 ledger/report/status mutation;
- no readiness, L3, UAT, pressure PASS, release, production-ready, or go-live claim.

## 8. Required Verification

Lucode must run and record exact commands, outputs where meaningful, and exit codes:

```bash
git diff --check origin/main..HEAD
node --check server/services/cleanservice/cleanservice-worker.mjs
node --check server/services/cleanservice/metadata-summary.mjs
node --check server/services/cleanservice/config.mjs
node server/tests/cleanservice-worker-shell-smoke.mjs
```

If new source or test files are added, run `node --check` on each new `.mjs` file and run the new focused smoke tests.

If TypeScript/front-end files are not touched, `npx pnpm@10.4.1 exec tsc --noEmit` is optional. If any TypeScript or shared type surface is touched despite the boundary above, run it and explain why that scope was necessary.

## 9. Report Requirements

The report must include:

- final branch name and full final branch HEAD;
- exact files changed;
- exact `git diff --name-status origin/main..HEAD` output;
- exact verification commands and exit codes;
- a statement that no runtime, data, production, sample, external Mineru2Table, `AGENTS.md`, or `.agents/**` mutation occurred;
- any implementation decision that differs from this task brief, labeled as a Lucode recommendation rather than adopted project fact.

After completion, update the Task 222 ledger row to `Ready for luceon Review`, set `Next Actor=Luceon`, and push the branch.
