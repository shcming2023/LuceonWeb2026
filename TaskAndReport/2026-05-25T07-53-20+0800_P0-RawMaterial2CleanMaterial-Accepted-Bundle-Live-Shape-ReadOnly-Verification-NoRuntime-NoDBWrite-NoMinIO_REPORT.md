# TASK-20260525-075041-P0-RawMaterial2CleanMaterial-Accepted-Bundle-Live-Shape-ReadOnly-Verification-NoRuntime-NoDBWrite-NoMinIO Report

Report time: 2026-05-25T07:53:20+0800

Decision:

```text
PASS_LIVE_SHAPE_BUNDLE_BUILDS
```

## Task And Baseline

Task:

```text
TASK-20260525-075041-P0-RawMaterial2CleanMaterial-Accepted-Bundle-Live-Shape-ReadOnly-Verification-NoRuntime-NoDBWrite-NoMinIO
```

Task brief:

```text
TaskAndReport/2026-05-25T07-50-41+0800_P0-RawMaterial2CleanMaterial-Accepted-Bundle-Live-Shape-ReadOnly-Verification-NoRuntime-NoDBWrite-NoMinIO_TASK.md
```

Execution baseline:

```text
main@6227cd6f0de457b908f074b41cf02989323982cf
origin/main@6227cd6f0de457b908f074b41cf02989323982cf
```

Evidence file:

```text
/tmp/luceon-task274-live-shape/evidence.json
sha256 = 139fc550d47ad55344d138ac8b76db839121de8f83ac3aecf3c329f60bd5d54e
```

## Scope Actually Executed

Read-only GETs:

```text
GET http://127.0.0.1:8081/__proxy/db/materials/1842780526581841 -> 200
GET http://127.0.0.1:8081/__proxy/db/tasks/task-1779085089451 -> 200
```

Helper compiled/imported:

```text
src/app/utils/rawMaterial2CleanMaterialInputBundle.ts
```

Helper invocation:

```text
buildRawMaterial2CleanMaterialInputBundle({
  material: <live material GET body>,
  task: <live task GET body>,
  currentAssetVersion: "v4"
})
```

## Live Shape Summary

Material Clean Material summary:

```text
status = completed
latestVersion = v4
assetVersion = null
provenanceObjectName = toc-rebuild/1842780526581841/v4/provenance.json
operatorDecision.state = accepted
operatorDecision.artifactSnapshot.assetVersion = v4
operatorDecision.artifactSnapshot.jobId = luceon-task-1779085089451-toc-rebuild-v4
```

Task CleanService job summary:

```text
status = completed
assetVersion = v4
jobId = luceon-task-1779085089451-toc-rebuild-v4
```

Task artifact roles:

```text
flooded_content
logic_tree
metrics
provenance
readable_tree
skeleton
unresolved_anchors
```

## Bundle Result

The helper returned:

```text
ok = true
kind = raw-material-2-clean-material-input
serviceName = toc-rebuild
materialId = 1842780526581841
taskId = task-1779085089451
assetVersion = v4
jobId = luceon-task-1779085089451-toc-rebuild-v4
provenanceObjectName = toc-rebuild/1842780526581841/v4/provenance.json
operatorDecision.state = accepted
operatorDecision.decidedBy = local-operator
```

Source input:

```text
bucket = eduassets-raw
object = mineru/1842780526581841/v1/content_list_v2.json
sha256 = f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
size_bytes = 31543
```

Bundle artifact refs:

```text
flooded_content
logic_tree
metrics
provenance
readable_tree
skeleton
unresolved_anchors
```

Required refs present:

```text
readable_tree
logic_tree
skeleton
flooded_content
```

All artifact refs are object references only. No artifact body content was
included in the bundle.

## Commands And Exit Codes

```text
git status --short --branch
exit 0
```

```text
git fetch origin --prune --tags
exit 0
```

```text
git pull --ff-only origin main
exit 0
```

```text
npx pnpm@10.4.1 exec tsc src/app/utils/rawMaterial2CleanMaterialInputBundle.ts --target ES2020 --module ES2020 --moduleResolution bundler --skipLibCheck --noEmit false --outDir /tmp/luceon-task274-live-shape/compiled
node --input-type=module <live-shape verification script>
exit 0
```

```text
node server/tests/rawmaterial2cleanmaterial-input-bundle-smoke.mjs
exit 0
```

```text
git diff --check
exit 0
```

## Non-Operations

Not performed by this task:

- DB POST/PATCH/PUT/DELETE;
- MinIO get/list/put/copy/move/delete/write/delete-marker/cleanup;
- CleanService runtime run;
- RawMaterial2CleanMaterial execution, transport, endpoint, worker, or Docker
  service;
- Mineru2Table POST/query/probe;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test;
- model, env, secret, sample, source asset, or local override mutation;
- source-code edit;
- production deployment or production runtime validation;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claim.

## Residual Risks

- This verifies only the canonical accepted v4 sample.
- The material summary still has `assetVersion = null`; the helper succeeds
  because other live metadata signals are aligned: `latestVersion`, task
  `assetVersion`, and operator-decision snapshot `assetVersion`.
- RawMaterial2CleanMaterial still has no accepted runtime protocol, execution
  service, output persistence path, or readiness evidence.

## Recommended Next Mainline Step

Proceed to a narrow RawMaterial2CleanMaterial single-sample protocol and
mock-safe runner boundary task. The next task should define the minimum service
request/response contract and dry-run output shape using this accepted bundle as
input, without DB apply, MinIO mutation, Docker operation, or production
readiness claims.

## Final Result

The current persisted accepted canonical sample can build a traceable
RawMaterial2CleanMaterial input bundle from live-shaped read-only DB objects.

This closes the bridge:

```text
accepted toc-rebuild v4 Clean Material metadata
=> live material/task shape
=> RawMaterial2CleanMaterial input bundle
```

It does not claim downstream service execution, output quality, production
readiness, L3, UAT, pressure PASS, release readiness, go-live, or batch
readiness.
