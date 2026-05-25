# TASK-20260525-113138 Luceon Report

Report time: 2026-05-25T11:31:38+0800

Decision:

```text
DIAGNOSIS_COMPLETE_STALE_CLEAN_ARTIFACT_OBJECTREFS_OR_MISSING_CLEAN_OBJECTS
```

## Scope

This Luceon task performed a read-only diagnosis for the Task 277 blocker:

```text
task/material metadata record accepted toc-rebuild v4 ObjectRefs, but exact
proxy GET for the first required artifact returns key-not-found.
```

Execution anchor:

```text
main@e7dd1ca6d479562098aee12928505dac6f8bfc8e
```

Canonical sample:

```text
materialId = 1842780526581841
taskId = task-1779085089451
serviceName = toc-rebuild
assetVersion = v4
jobId = luceon-task-1779085089451-toc-rebuild-v4
```

## Read-Only Probes

### Material And Task

| Probe | Status | Result |
| --- | ---: | --- |
| `GET /__proxy/db/materials/1842780526581841` | 200 | Material reachable; `cleanMaterials.toc-rebuild.latestVersion=v4`; status completed |
| `GET /__proxy/db/tasks/task-1779085089451` | 200 | Task reachable; `cleanServiceJobs.toc-rebuild.assetVersion=v4`; status completed |

Relevant metadata signals agree:

```text
material latestVersion = v4
task assetVersion = v4
task jobId = luceon-task-1779085089451-toc-rebuild-v4
operatorDecision.state = accepted
operatorDecision.artifactSnapshot.assetVersion = v4
operatorDecision.artifactSnapshot.jobId = luceon-task-1779085089451-toc-rebuild-v4
```

Source input metadata also agrees across task/material/operator snapshot:

```text
bucket = eduassets-raw
object = mineru/1842780526581841/v1/content_list_v2.json
sha256 = f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
size_bytes = 31543
```

## ObjectRef Comparison

Task metadata and `operatorDecision.artifactSnapshot.artifactRefs` agree for
all seven v4 artifact roles:

| Role | Object | Task/Snapshot Agreement |
| --- | --- | --- |
| `readable_tree` | `toc-rebuild/1842780526581841/v4/readable_tree.md` | yes |
| `logic_tree` | `toc-rebuild/1842780526581841/v4/logic_tree.json` | yes |
| `skeleton` | `toc-rebuild/1842780526581841/v4/skeleton.json` | yes |
| `flooded_content` | `toc-rebuild/1842780526581841/v4/flooded_content.json` | yes |
| `metrics` | `toc-rebuild/1842780526581841/v4/metrics.json` | yes |
| `provenance` | `toc-rebuild/1842780526581841/v4/provenance.json` | yes |
| `unresolved_anchors` | `toc-rebuild/1842780526581841/v4/unresolved_anchors.json` | yes |

Material-level `cleanMaterials.toc-rebuild.artifacts` is absent; the durable
artifact refs are in the task summary and accepted operator snapshot.

## Exact Artifact GET Results

All seven recorded v4 artifact refs returned key-not-found through the existing
read-only proxy:

| Role | Bucket | Status | Result |
| --- | --- | ---: | --- |
| `readable_tree` | `eduassets-clean` | 500 | `The specified key does not exist.` |
| `logic_tree` | `eduassets-clean` | 500 | `The specified key does not exist.` |
| `skeleton` | `eduassets-clean` | 500 | `The specified key does not exist.` |
| `flooded_content` | `eduassets-clean` | 500 | `The specified key does not exist.` |
| `metrics` | `eduassets-clean` | 500 | `The specified key does not exist.` |
| `provenance` | `eduassets-clean` | 500 | `The specified key does not exist.` |
| `unresolved_anchors` | `eduassets-clean` | 500 | `The specified key does not exist.` |

The wrong query parameter shape was also confirmed:

```text
/__proxy/upload/proxy-file?bucket=eduassets-clean&object=<object>
=> 400 {"error":"缺少 objectName 参数"}
```

The correct query parameter shape is:

```text
/__proxy/upload/proxy-file?objectName=<object>&bucket=eduassets-clean
```

and it still returns key-not-found for the v4 clean refs.

## Proxy Resolver Control Probes

The proxy itself is not generally broken. It can read current raw/parsed
objects for the same material:

| Probe | Status | Result |
| --- | ---: | --- |
| `originals/1842780526581841/source.pdf` default bucket | 200 | 86884 bytes, SHA256 `2230acbb40524e1de80f1ebe57a13c5f41db353e15c6727f5ebb97383154e16c` |
| `originals/1842780526581841/source.pdf` bucket=`raw` | 200 | same SHA256 |
| `parsed/1842780526581841/full.md` default bucket | 200 | 3867 bytes, SHA256 `df941904aca8b4882d076994e3f6aefa23db49ffac0bf620e657a7cac737bb3f` |
| `parsed/1842780526581841/full.md` bucket=`parsed` | 200 | same SHA256 |
| `parsed/1842780526581841/artifact-manifest.json` bucket=`parsed` | 200 | 3246 bytes, SHA256 `fe547a6cd71aba48041eb3b05d6da34fa3e98a27ee99e780b6c98c1b1d25321e` |

Clean bucket exact controls:

| Probe | Status | Result |
| --- | ---: | --- |
| `toc-rebuild/1842780526581841/v2/readable_tree.md` bucket=`eduassets-clean` | 500 | key-not-found |
| `toc-rebuild/1842780526581841/v3/readable_tree.md` bucket=`eduassets-clean` | 500 | key-not-found |
| `toc-rebuild/1842780526581841/v4/readable_tree.md` bucket=`eduassets-clean` | 500 | key-not-found |

For the v4 readable-tree object, all exact bucket resolver variants also
returned key-not-found:

```text
bucket=eduassets-clean
bucket=clean
default bucket
bucket=parsed
bucket=raw
```

## Classification

The most likely blocker is:

```text
STALE_CLEAN_ARTIFACT_OBJECTREFS_OR_MISSING_CLEAN_OBJECTS
```

More specifically:

- not a task/material metadata disagreement: task and operator snapshot agree;
- not a wrong `objectName` query parameter after correction: correct query still
  fails;
- not a general proxy outage: raw and parsed material objects read successfully;
- not likely a simple clean bucket alias issue: `eduassets-clean` and `clean`
  both fail for the same exact v4 object;
- the live DB currently points to clean artifact ObjectRefs whose corresponding
  objects are not available in the current MinIO clean bucket.

This could be due to missing clean objects, storage state drift after prior v4
runtime evidence, stale DB metadata, or a prior v4 artifact persistence/import
gap. This task did not run bucket listing, MinIO stat outside proxy, DB
correction, or any object repair, so it does not distinguish those storage-layer
causes further.

## Boundary Confirmation

No DB POST/PATCH/PUT/DELETE/apply, MinIO write/delete/list/bucket scan, runtime
POST, service execution, Docker/Compose operation, job-store edit, source/sample
mutation, model/env/secret mutation, production deployment, production
validation, UAT, L3, pressure PASS, release readiness, production readiness,
production online, or go-live claim was performed or made.

## Recommended Next Mainline Step

The fastest next step is a separately authorized, narrow repair decision:

```text
P0 CleanMaterial Canonical-v4 Artifact Availability Repair Decision
```

Recommended options for the Director:

1. Read-only deeper storage diagnosis with exact MinIO `statObject` for the
   seven recorded refs, still no list and no write.
2. Re-run or re-import the canonical v4 CleanService output under an explicit
   one-sample repair task, if writes are authorized.
3. Patch metadata back to an actually available clean version only if an exact
   available clean output is proven.

Do not proceed to RawMaterial2CleanMaterial artifact-backed draft success or
raw2clean output apply until the required clean artifact bodies are actually
retrievable.

