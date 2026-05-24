# TASK-20260524-215051-P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime

Issued at: 2026-05-24T21:50:51+0800

Actor: Lucode

## Mainline Objective

Bridge the current phase from accepted Clean Material into the next downstream
stage without starting the downstream service.

The mainline state is now:

```text
toc-rebuild v4 Clean Material
=> artifact inspection
=> operatorDecision.state = accepted
=> build RawMaterial2CleanMaterial input bundle
```

This task must implement only the bundle builder and mock-safe validation. It
must not implement RawMaterial2CleanMaterial execution, service transport,
runtime dispatch, DB persistence, UI workflow, batch review, or production
validation.

## Critical Path Scope

Implement a pure helper that converts an accepted Clean Material record into a
bounded downstream input bundle.

The helper must:

1. Accept material/task-like metadata objects shaped like the current product
   data.
2. Locate:

   ```text
   material.metadata.cleanMaterials[serviceName]
   task.metadata.cleanServiceJobs[serviceName]
   ```

3. Require:

   ```text
   operatorDecision.state = accepted
   serviceName = toc-rebuild
   assetVersion = v4 or caller-provided current version
   jobId present
   provenanceObjectName present
   sourceInput present with object and sha256
   required artifact refs present
   ```

4. Produce a plain JSON input bundle for future RawMaterial2CleanMaterial work.

This is the next bridge plank only:

```text
accepted Clean Material -> downstream input bundle
```

## Current Evidence Anchors

Use current `main`.

Accepted milestones:

- Task 267: canonical `toc-rebuild v4` metadata durably applied.
- Task 268: Clean Material summary product surface accepted.
- Task 269: artifact inspection surface accepted.
- Task 270: operator decision semantics accepted.
- Task 271: mock-safe operator decision UI/patch helper accepted.
- Task 272: canonical sample `operatorDecision.state=accepted` persisted by
  exactly one material PATCH.

Canonical sample for fixtures:

```text
materialId = 1842780526581841
taskId = task-1779085089451
serviceName = toc-rebuild
assetVersion = v4
jobId = luceon-task-1779085089451-toc-rebuild-v4
operatorDecision.state = accepted
```

Lucode may use this as a mock fixture shape, but must not hard-code this one
material as the only usable code path.

## Required Bundle Shape

The output bundle should be small, explicit, and traceable:

```json
{
  "kind": "raw-material-2-clean-material-input",
  "serviceName": "toc-rebuild",
  "materialId": "1842780526581841",
  "taskId": "task-1779085089451",
  "assetVersion": "v4",
  "jobId": "luceon-task-1779085089451-toc-rebuild-v4",
  "provenanceObjectName": "toc-rebuild/1842780526581841/v4/provenance.json",
  "sourceInput": {
    "bucket": "eduassets-raw",
    "object": "mineru/1842780526581841/v1/content_list_v2.json",
    "sha256": "f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db",
    "size_bytes": 31543
  },
  "artifactRefs": {
    "readable_tree": { "bucket": "eduassets-clean", "object": "..." },
    "logic_tree": { "bucket": "eduassets-clean", "object": "..." },
    "skeleton": { "bucket": "eduassets-clean", "object": "..." },
    "flooded_content": { "bucket": "eduassets-clean", "object": "..." }
  },
  "operatorDecision": {
    "state": "accepted",
    "decidedAt": "...",
    "decidedBy": "local-operator"
  }
}
```

Required artifact refs:

```text
readable_tree
logic_tree
skeleton
flooded_content
```

Optional artifact refs may be included if already present:

```text
metrics
provenance
unresolved_anchors
```

Do not include full artifact body content. ObjectRefs only.

## Required Blocking Semantics

Return a structured blocked result instead of a bundle when:

- material is missing;
- task is missing;
- clean material service summary is missing;
- clean service task summary is missing when needed for artifact refs/job id;
- `operatorDecision.state` is not `accepted`;
- service status is not completed;
- current version is missing or mismatched;
- job id is missing or mismatched;
- provenance object ref is missing;
- sourceInput object or sha256 is missing;
- any required artifact ref is missing;
- artifact refs point at a different `toc-rebuild/{materialId}/{assetVersion}/`
  prefix;
- bundle construction would require fetching artifact bodies, live DB reads, or
  MinIO reads.

Use stable reason codes. Examples:

```text
CLEAN_MATERIAL_NOT_ACCEPTED
MISSING_SOURCE_INPUT
MISSING_REQUIRED_ARTIFACT
ASSET_VERSION_MISMATCH
ARTIFACT_PREFIX_MISMATCH
```

## Allowed Files

Allowed implementation files:

- a focused helper under `src/app/utils/`, for example:
  `src/app/utils/rawMaterial2CleanMaterialInputBundle.ts`
- `src/store/types.ts` only for narrow type additions needed by the helper.

Allowed tests/checks:

- a focused mock-safe helper smoke under `server/tests/` or another existing
  lightweight test location;
- no live runtime dependency.

Allowed control-plane files:

- required Lucode report under `TaskAndReport/`;
- branch-local update to `TaskAndReport/TASK_TRACKING_LIST.md`.

## Forbidden Files And Operations

Forbidden files unless separately authorized:

- `server/upload-server.mjs`
- `server/db-server.mjs`
- CleanService runtime/orchestration files
- Mineru2Table transport/protocol files
- package files
- Docker/Compose files
- PRD/architecture docs
- UI pages/components, unless Lucode first reports blocked and Luceon issues a
  UI task
- local private role files: `AGENTS.md`, `.agents/**`

Forbidden operations:

- live DB read/write for validation;
- DB POST/PATCH/PUT/DELETE;
- MinIO get/list/put/copy/move/delete/write/delete-marker/cleanup;
- CleanService runtime run;
- RawMaterial2CleanMaterial execution, transport, service endpoint, Docker
  service, scheduler, or worker;
- Mineru2Table POST/query/probe;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test;
- production deployment or production runtime validation;
- model, env, secret, sample, source asset, or local override mutation;
- broad workflow, approval system, permission/governance work, audit export, or
  batch decision UI;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claims.

## Fast Validation Target

Use mock fixtures shaped from the current canonical accepted `toc-rebuild v4`
metadata.

Focused checks must prove:

1. accepted canonical-shape input produces a valid bundle;
2. non-accepted decision blocks;
3. missing sourceInput blocks;
4. missing each required artifact role blocks;
5. assetVersion mismatch blocks;
6. missing jobId blocks;
7. artifact prefix mismatch blocks;
8. helper performs no network, DB, MinIO, runtime, or Docker operation.

## Deferrable Side Work

Defer:

- RawMaterial2CleanMaterial service protocol;
- downstream service execution;
- DB persistence of downstream input bundles;
- UI launch button;
- batch bundle building;
- artifact body reading or content validation;
- multi-user governance;
- audit export/reporting;
- production validation/readiness.

## Stop Rule

Stop and report blocked instead of widening scope if:

- a useful bundle seems to require reading artifact bodies;
- a live DB/MinIO read is needed for validation;
- the helper requires new server routes or runtime wiring;
- RawMaterial2CleanMaterial execution details become necessary;
- UI or workflow work appears necessary.

## Acceptance Criteria

Luceon can accept this task at code/test level if:

- the helper builds a traceable input bundle only from already-present
  accepted Clean Material metadata;
- the output bundle contains material/task ids, serviceName, assetVersion, jobId,
  provenance, sourceInput, required artifact refs, and accepted decision
  snapshot;
- all blocking semantics above are covered by focused mock-safe checks;
- changed files stay inside the allowed boundary;
- report evidence includes exact remote branch and full HEAD;
- no runtime/data/production operation is performed.

Acceptance does not mean RawMaterial2CleanMaterial exists, has run, or is ready
for production.

## Required Checks

At minimum run:

```bash
git diff --check origin/main...HEAD
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Also run the focused helper smoke/check added for this task.

## Required Report

Write:

```text
TaskAndReport/2026-05-24T21-50-51+0800_P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime_REPORT.md
```

The report must include:

- task id and task brief path;
- exact remote branch and full HEAD;
- files changed;
- implementation summary;
- output bundle shape summary;
- blocking reason codes covered;
- commands run with exit codes;
- skipped checks and exact reasons;
- risks, blockers, and residual debt;
- explicit boundary statement confirming no live DB read/write, no MinIO read or
  write/delete, no runtime, no Docker/production operation, no
  RawMaterial2CleanMaterial execution, and no readiness/go-live claim;
- whether Luceon review is required.

## Handoff

After completion, update the branch-local ledger row to:

```text
Status = Lucode 已回报待 Luceon 审查
Next Actor = Luceon
```

Push a remote branch named like:

```text
lucode/TASK-20260524-215051-P0-RawMaterial2CleanMaterial-Accepted-CleanMaterial-Input-Bundle-Builder-MockSafe-NoRuntime
```

Do not merge to `main`.
