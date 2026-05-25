# TASK-20260525-123633-P0-RawMaterial2CleanMaterial-Real-Artifact-Shape-Compatibility-MockSafe-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost

Issued at: 2026-05-25T12:36:33+0800

Actor: Luceon

## Mainline Objective

Convert the latest real evidence into the next narrow implementation step:

```text
accepted canonical toc-rebuild v4 metadata
+ readable real clean artifact bodies
+ RawMaterial2CleanMaterial artifact-backed draft helper
=> MOCK_ALGORITHM_DRAFT_READY
```

Task 279 repaired the stale upload-server runtime image and proved all seven
canonical v4 clean artifact ObjectRefs are now readable through exact proxy
GETs with matching size/SHA. The next blocker is no longer MinIO/proxy access.
It is the RawMaterial2CleanMaterial draft skeleton's inability to consume the
real artifact body shapes.

The mainline question for this task is:

```text
Can the current RawMaterial2CleanMaterial draft dry-run consume the real
canonical v4 logic_tree/skeleton/flooded_content/readable_tree artifact shapes
without inventing source truth and without any DB/MinIO/runtime mutation?
```

This is a phase-breakthrough task. Do not turn it into final cleaning quality,
approval workflow, broad schema design, service runtime wiring, or cleanup.

## Critical Path Scope

Make the existing mock-safe draft skeleton shape-compatible with the real
canonical v4 artifacts only.

1. Adapt the parser/extractor in:

   ```text
   src/app/utils/rawMaterial2CleanMaterialAlgorithm.ts
   ```

   so it can consume real non-array artifact shapes in addition to the existing
   fixture arrays.

2. Preserve the existing artifact-backed composition boundary in:

   ```text
   src/app/utils/rawMaterial2CleanMaterialArtifactBackedDraft.ts
   ```

   Edit this file only if needed for evidence reporting or safe warning/count
   propagation.

3. Support the real `logic_tree.json` object shape observed after Task 279.
   The root may be a single JSON object, not an array. It may use fields such as
   `node_id`, `title`, `level`, `status`, and child-node containers. Traverse
   bounded child structures when present and keep stable node/source refs.

4. Support real nested `flooded_content.json` shapes, including nested arrays
   and nested records. Extract only source-referenced items. Do not promote
   unreferenced source-derived text into draft output.

5. Support real `skeleton.json` shapes without assuming only
   `nodes`/`sections`/`items` top-level arrays.

6. Keep `readable_tree.md` as injected string content and retain the existing
   summary role.

7. If a text-bearing item has no stable source reference, do not invent one.
   Either skip it with a warning/counter or block with
   `MISSING_SOURCE_REFERENCE` if skipping would make the resulting draft
   misleading. Prefer a narrow, explicit warning for safely skipped
   unreferenced fragments when there are still source-referenced sections or
   blocks.

8. Add focused tests using real-shaped fixtures derived from the canonical v4
   body structure. Fixture contents may be minimized, but the shape must match
   the real observed structures closely enough to prevent this regression.

9. Run a read-only canonical artifact-backed rehearsal if the local Luceon
   runtime is reachable. It may only use exact GETs for material/task and exact
   artifact ObjectRefs. It must not use POST/PATCH/PUT/DELETE, MinIO writes or
   lists, Docker, service execution, job submission, or DB mutation.

## True Preconditions

- `origin/main` is the source of truth.
- Task 277 accepted the artifact-backed draft composition helper but stopped on
  unreadable canonical ObjectRefs.
- Task 279 repaired the stale upload-server clean-bucket proxy runtime and
  proved all seven canonical v4 clean artifacts now return 200 with matching
  recorded size/SHA.
- Task 279's follow-up probe reached the new blocker:

  ```text
  DRAFT_BUILD_BLOCKED
  INVALID_ARTIFACT_BODY
  artifact body has no supported item array: logic_tree
  ```

Current main anchor at task issuance:

```text
main@10b31f427cc8828b16fde81b1cdfa2f7732be365
```

Canonical single-sample target:

```text
materialId = 1842780526581841
taskId = task-1779085089451
serviceName = toc-rebuild
assetVersion = v4
jobId = luceon-task-1779085089451-toc-rebuild-v4
```

## Environment And Write Boundary

Luceon implements code in the development workspace:

```text
/Users/concm/Dev_workspace/Luceon2026
```

Luceon keeps control-plane, acceptance, and explicitly authorized production
operations in the production/control workspace:

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed runtime interaction is read-only only:

- GET canonical material record;
- GET canonical task record;
- GET exact required artifact ObjectRefs through the upload proxy.

Preferred exact artifact path:

```text
/__proxy/upload/proxy-file?bucket=eduassets-clean&object=<object>
```

Do not use broad MinIO listing, direct bucket scans, upload-server rebuilds, or
runtime mutation in this task.

## Deferrable Side Work

Defer:

- final RawMaterial2CleanMaterial cleaning semantics and quality;
- writing `raw2clean` output artifacts;
- DB metadata persistence for raw2clean output;
- RawMaterial2CleanMaterial independent service repo/container;
- endpoint, worker, scheduler, transport, registry, or service API;
- product UI surface for raw2clean results;
- operator approval workflow expansion;
- batch/multi-sample support;
- broad artifact schema normalization;
- technical-debt cleanup outside the touched parser/dry-run boundary.

## Fast Validation Target

Minimum useful proof:

```text
canonical accepted CleanMaterial v4
-> exact read-only artifact GETs
-> real-shaped logic_tree/skeleton/flooded_content/readable_tree bodies
-> buildRawMaterial2CleanMaterialArtifactBackedDraftDryRun
-> MOCK_ALGORITHM_DRAFT_READY
```

Expected evidence should include:

- artifact roles read;
- exact ObjectRefs read;
- draft status;
- section count and block count;
- representative source refs from real bodies;
- warnings or skipped-unreferenced counts if applicable;
- preserved sourceInput and artifact ObjectRefs/hashes;
- explicit boundary flags showing no DB writes, no MinIO writes, no runtime
  POST, and no Docker operation.

## Stop Rule

Stop and report blocked instead of widening scope if:

- the canonical material/task read-only GETs fail;
- any required artifact ObjectRef becomes unreadable again;
- real artifact bodies lack enough stable source references to build a truthful
  draft without inventing refs;
- supporting the shape would require final cleaning logic rather than bounded
  extraction;
- implementation would require DB writes, MinIO writes/deletes/lists, runtime
  POST, service execution, Docker, job-store edits, source asset mutation,
  model/env/secret mutation, or broad UI/workflow work.

## Review Boundary

Acceptance means only:

```text
the existing RawMaterial2CleanMaterial mock-safe artifact-backed draft can
consume the real canonical v4 artifact body shapes and produce a truthful
read-only draft evidence object for one sample
```

Acceptance does not mean:

- final RawMaterial2CleanMaterial output exists;
- raw2clean DB/MinIO apply is approved;
- raw2clean service/runtime exists;
- content cleaning quality is accepted;
- all future Mineru2Table artifact shapes are supported;
- product UI is complete;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live is approved.

## Red Lines For Data Processing

1. ID-only / reference-backed extraction: source-derived draft items must keep
   stable Block IDs, node IDs, or source references when available.
2. No source invention: do not synthesize refs from array index, text position,
   or generated labels for source-derived content.
3. Asset hash locking: accepted sourceInput and artifact ObjectRef hashes must
   be preserved, not rewritten.
4. Pure dry-run boundary: do not create durable final clean artifacts, teaching
   material, or DB metadata.

## Allowed Files

Allowed implementation files:

- `src/app/utils/rawMaterial2CleanMaterialAlgorithm.ts`
- `src/app/utils/rawMaterial2CleanMaterialArtifactBackedDraft.ts` only if
  needed for evidence/warning propagation

Allowed tests:

- `server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs`
- `server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs`
- one new focused real-shape smoke test under `server/tests/` if useful

Allowed control-plane files:

- Luceon implementation/validation report under `TaskAndReport/`
- update to `TaskAndReport/TASK_TRACKING_LIST.md`

## Forbidden Files And Operations

Forbidden files unless Luceon issues a separate task:

- `server/upload-server.mjs`
- `server/db-server.mjs`
- `server/services/cleanservice/**`
- endpoint, worker, scheduler, transport, Docker, Compose, package, or service
  deployment files
- UI pages/components
- PRD/architecture docs
- local private role files: `AGENTS.md`, `.agents/**`

Forbidden operations:

- DB POST/PATCH/PUT/DELETE or apply;
- MinIO put/copy/move/delete/write/delete-marker/cleanup/list/bucket scan;
- runtime POST, submit-probe, Mineru2Table POST/query/probe, raw2clean service
  execution, or job submission;
- Docker/Compose build/up/down/restart/recreate/volume/prune/network mutation;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test;
- model, env, secret, sample, source asset, or local override mutation;
- production deployment or production validation;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claim.

## Acceptance Criteria

Positive acceptance:

1. Real-shaped `logic_tree.json` object bodies are accepted without requiring a
   top-level item array.
2. Real-shaped `skeleton.json` and nested `flooded_content.json` bodies are
   traversed in a bounded way.
3. Source-derived draft items keep stable refs; unreferenced text is not
   promoted as source truth.
4. Existing mock fixture behavior remains compatible.
5. Focused smoke tests pass, including a real-shape fixture regression.
6. If local runtime is reachable, the report includes a read-only canonical
   rehearsal that reaches `MOCK_ALGORITHM_DRAFT_READY`.
7. If the rehearsal still blocks, the report gives the next exact real shape or
   source-reference blocker without broadening scope.
8. `npx pnpm@10.4.1 exec tsc --noEmit` passes.
9. `npx pnpm@10.4.1 run build` passes, allowing only pre-existing chunk-size
   warnings.
10. `git diff --check origin/main...HEAD` passes on the Luceon dev branch if a
    branch is used.

Negative acceptance:

1. No DB write/apply or mutating DB method.
2. No MinIO write/delete/list/bucket scan.
3. No runtime POST, service execution, Docker/Compose operation, job-store edit,
   upload/retry/reparse/Re-AI/rollback, or batch action.
4. No broad UI/workflow/registry/worker/service implementation.
5. No final raw2clean output asset or DB metadata persistence.
6. No invented source references.
7. No readiness/go-live/UAT/L3/pressure PASS language.

## Required Report

Luceon must report:

- branch name and exact full HEAD;
- changed files;
- implementation summary;
- exact commands and exit codes;
- focused real-shape fixture evidence;
- read-only canonical rehearsal evidence or exact blocked reason;
- artifact roles and ObjectRefs read;
- draft status, section/block counts, representative source refs, and warnings;
- proof that no DB write, MinIO write/list/delete, runtime POST, Docker,
  job-store edit, source mutation, model/secret/env mutation, or readiness claim
  occurred;
- residual debt and recommended next mainline step.

After implementation/validation, update the ledger row to either closed or an
explicit blocked state. If a dev branch is used, the expected branch pattern is:

```text
codex/*TASK-20260525-123633*
```
