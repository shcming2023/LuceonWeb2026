# TASK-20260524-144759-P0-CleanService-PostTask261-Existing-v3-Live-Evidence-ReadOnly-Revalidation-NoPost-NoDBWrite Report

Report time: 2026-05-24T14:57:03+0800

## 1. Final Classification

```text
COMPLETED_READONLY_LIVE_EVIDENCE_REHEARSAL_EXISTING_V3_NOPOST_NO_DBWRITE
```

Task 263 is accepted as a Luceon read-only live-evidence rehearsal.

Current `origin/main` product code can consume the live-shaped task/material
payload, the accepted completed-job `sourceInput` fallback, existing
job-store/MinIO `v3` evidence, and explicit `allowProbeJobIdSuffix=true` to
reach a no-POST dry-run product result:

```text
classification = DRY_RUN_SUCCESS
jobId = luceon-task-1779085089451-toc-rebuild-v3
assetVersion = v3
submitJob calls = 0
queryJob calls = 0
DB update calls = 0
```

This is not runtime success, not DB apply, not CleanService activation, not UAT,
not L3, not pressure PASS, not production readiness, not release readiness, and
not go-live.

## 2. Baseline And Required Checks

Git baseline after sync:

```text
HEAD = origin/main = 74ecdddb11e8b6612b9e0113eac14f90dd4bdb45
```

Required command summary:

| Command | Exit | Evidence |
| --- | ---: | --- |
| `git status --short --branch` | 0 | `## main...origin/main` |
| `git fetch origin --prune --tags` | 0 | no output |
| `git pull --ff-only origin main` | 0 | already up to date |
| `git rev-parse HEAD origin/main` | 0 | both `74ecdddb11e8b6612b9e0113eac14f90dd4bdb45` |
| `git diff --check` | 0 | no output |
| read-only DB GET via `docker exec -i cms-upload-server node --input-type=module` | 0 | task/material HTTP `200` |
| read-only MinIO `listObjectsV2`/`getObject` via `cms-upload-server` | 0 | raw plus seven `v3` artifacts hash-verified |
| read-only job-store file read | 0 | jobs.json size/hash/key summary captured |
| local product-code rehearsal | 0 | `DRY_RUN_SUCCESS`; submit/query/DB-write tripwires untouched |
| focused `node --check` for CleanService modules | 0 | no output |
| `node server/tests/cleanservice-raw-material-adapter-smoke.mjs` | 0 | `PASS raw material adapter smoke` |
| `node server/tests/cleanservice-orchestration-runner-smoke.mjs` | 0 | `ALL ... PASSED! (26/26)` |

## 3. Read-Only DB Evidence

Command shape:

```text
docker exec -i cms-upload-server node --input-type=module
GET http://cms-db-server:8789/tasks/task-1779085089451
GET http://cms-db-server:8789/materials/1842780526581841
```

Observed:

| Target | Value |
| --- | --- |
| Task HTTP status | `200` |
| Material HTTP status | `200` |
| Task id | `task-1779085089451` |
| Task state | `review-pending` |
| Task materialId | `1842780526581841` |
| Task `mineruStatus` | `completed` |
| Canonical `metadata.rawMaterial.mineru.contentListV2` | absent |
| Legacy parsed evidence | present |
| Existing task clean job | `toc-rebuild`, completed, `assetVersion=v2` |
| Existing task clean job id | `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230` |
| Existing `sourceInput` | `eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json` |
| Existing `sourceInput` SHA256 | `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db` |
| Existing `sourceInput` size | `31543` |
| Material status | `reviewing` |
| Material clean material | completed, `latestVersion=v2`, prefix `toc-rebuild/1842780526581841/v2/` |

Interpretation: the live-shaped payload still lacks canonical `rawMaterial`,
but Task 261's completed-job `sourceInput` fallback is present and traceable.

## 4. Read-Only MinIO Evidence

Command shape:

```text
docker exec -i cms-upload-server node --input-type=module
MinIO listObjectsV2/getObject only:
  eduassets-raw/mineru/1842780526581841/
  eduassets-clean/toc-rebuild/1842780526581841/
```

Observed:

| Prefix | Count |
| --- | ---: |
| `eduassets-raw/mineru/1842780526581841/` | 1 |
| `eduassets-clean/toc-rebuild/1842780526581841/` | 21 |
| `toc-rebuild/.../v1/` | 7 |
| `toc-rebuild/.../v2/` | 7 |
| `toc-rebuild/.../v3/` | 7 |

Raw input:

| Object | Size | SHA256 |
| --- | ---: | --- |
| `mineru/1842780526581841/v1/content_list_v2.json` | 31543 | `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db` |

Current `v3` artifact hashes:

| Artifact | Size | SHA256 |
| --- | ---: | --- |
| `flooded_content.json` | 20054 | `e1a8355a80a5014b5a616ed441a4d0851c47d6a3d6092711ce765ffe11eea7b7` |
| `logic_tree.json` | 375 | `b61ee669b63bccb597f9ff31e5773ac1cc53a7bf6d6ef7a5ba73d467c7267665` |
| `metrics.json` | 129 | `add72cb0a0c0dcb2fe051961795da8c151181022df79770583d5fb75c7ed9718` |
| `provenance.json` | 2072 | `fc0cfd7bd417eb558f2793826a1718ae8ab04a96cd3d9a7291cf9ea33cc452ee` |
| `readable_tree.md` | 106 | `bba5cf360fa7c0d92a9489ce84dfc40458de6072f812d7ab5d381b8e828946d7` |
| `skeleton.json` | 21160 | `c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e` |
| `unresolved_anchors.json` | 2 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |

`v3` provenance and metrics:

| Field | Value |
| --- | --- |
| Provenance job id | `luceon-task-1779085089451-toc-rebuild-v3-probe` |
| Provenance asset version | `v3` |
| Provenance input object | `mineru/1842780526581841/v1/content_list_v2.json` |
| Provenance input SHA256 | `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db` |
| Provenance input size | `0` |
| Metrics total tokens | `6266` |
| Metrics prompt/completion tokens | `6212` / `54` |

Interpretation: physical `v3` evidence is present and hash-stable relative to
Task 260. The provenance `input size_bytes=0` residual remains.

## 5. Read-Only Job-Store Evidence

Command shape:

```text
node --input-type=module
read /Users/concm/prod_workspace/Mineru2Tables/data/jobs.json
```

Observed:

```text
sizeBytes = 12198
sha256 = 45ad98bc88cf99b54ca5323f5aa6cd59789609e00efbae629818811e6e14b370
keyCount = 5
```

Relevant job keys:

| Job key | Status | Version | Artifact refs |
| --- | --- | --- | ---: |
| `luceon-task-1779085089451-toc-rebuild-v3` | completed | `v3` | 7 |
| `luceon-task-1779085089451-toc-rebuild-v3-probe` | completed | `v3` | 7 |
| `luceon-task242-toc-rebuild-1842780526581841-v1-20260522025136` | completed | `v1` | 7 |
| `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230` | completed | `v2` | 7 |

Interpretation: existing `v3` remains diagnostic dual-key evidence, not a
pristine exactly-one-POST success record.

## 6. Product-Code Rehearsal

Command shape:

```text
node --input-type=module
import runCleanServiceTocRebuildOnce from current local main
fetch live task/material through GET-only docker exec
read canonical v3 job from jobs.json
read seven artifacts through MinIO getObject-only artifactReader
config:
  intent=create-new-version
  reconcileExistingJob=true
  allowProbeJobIdSuffix=true
tripwire:
  submitJob throws if called
  queryJob throws if called
  dbClient.updateTask/updateMaterial throw if called
```

Observed request:

| Field | Value |
| --- | --- |
| `job_id` | `luceon-task-1779085089451-toc-rebuild-v3` |
| `material_id` | `1842780526581841` |
| `parse_task_id` | `task-1779085089451` |
| `asset_version` | `v3` |
| Input bucket/object | `eduassets-raw` / `mineru/1842780526581841/v1/content_list_v2.json` |
| Input SHA256 | `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db` |
| Input size | `31543` |
| Sink | `eduassets-clean/toc-rebuild/1842780526581841/v3/` |

Tripwire/call summary:

| Dependency | Calls |
| --- | ---: |
| `submitJob` | 0 |
| `queryJob` | 0 |
| `getExistingCompletedJob` | 1 |
| `dbClient.updateTask` | 0 |
| `dbClient.updateMaterial` | 0 |
| Artifact reads | 7 |

Product result:

| Field | Value |
| --- | --- |
| `ok` | `true` |
| `classification` | `DRY_RUN_SUCCESS` |
| `jobId` | `luceon-task-1779085089451-toc-rebuild-v3` |
| `assetVersion` | `v3` |
| `dryRun` | `true` |
| `audit.cleanState` | `completed` |
| `audit.tokensTotal` | `6266` |
| `audit.newVersionIntent.previousAssetVersion` | `v2` |
| `audit.newVersionIntent.previousJobId` | `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230` |
| `audit.newVersionIntent.newAssetVersion` | `v3` |
| `verificationSummary.ok` | `true` |
| `verificationSummary.cleanState` | `completed` |
| `verificationSummary.errors` | `[]` |
| `verificationSummary.warnings` | `provenance-job-id-probe-suffix-accepted`, `input-size-bytes-zero` |
| `verificationSummary.inputSizeBytes` | `31543` |
| `verificationSummary.canonicalJobId` | `luceon-task-1779085089451-toc-rebuild-v3` |
| `verificationSummary.provenanceJobId` | `luceon-task-1779085089451-toc-rebuild-v3-probe` |
| `verificationSummary.provenanceJobIdPolicy` | `accepted-probe-suffix` |

Interpretation: Task 261's product fix holds against current live-shaped
evidence. The runner no longer requires harness injection of
`metadata.rawMaterial.mineru.contentListV2`; it uses the accepted completed-job
`sourceInput` fallback and keeps the `-probe` suffix behind explicit policy.

## 7. Accepted Facts

- Current `main` product code can perform the existing-`v3` no-POST
  reconciliation against live-shaped DB payload and live MinIO/job-store
  evidence.
- The live task still has no canonical rawMaterial branch, and that is handled
  by the bounded completed-job `sourceInput` fallback instead of legacy parsed
  evidence promotion.
- Seven `v3` artifacts are present and hash-verified.
- Product verification accepts the observed provenance `-probe` job id only
  under explicit `allowProbeJobIdSuffix=true`.
- The dry-run path compensated provenance `input size_bytes=0` from expected
  source input and reported `inputSizeBytes=31543`.
- No submit/query/runtime POST, DB write, MinIO write, job-store edit, source
  edit, Docker/Compose mutation, worker activation, or readiness/go-live action
  occurred.

## 8. Residual Risks And Non-Claims

Residual risks:

1. Current DB accepted state remains `toc-rebuild v2`; `v3` is not DB-applied.
2. Existing `v3` remains diagnostic dual-key evidence because canonical and
   `-probe` job-store keys both point to the same prefix.
3. Provenance quality debt remains: `input size_bytes=0`.
4. This task did not run runtime POST, live Mineru2Table query, DB apply, worker
   activation, `v4`, or a fresh sample.

Non-claims:

- Task 256 is not retroactively accepted as runtime success.
- This is not runtime success.
- This is not DB apply success.
- This is not UAT, L3, pressure PASS, production readiness, release readiness,
  production online, or go-live.

## 9. Recommended Next Step

The next decision should be a Director decision, not an automatic runtime run.

Recommended options:

1. Authorize a narrowly scoped no-write runtime observation target only if the
   Director wants live Mineru2Table query/transport evidence for the existing
   `v3` diagnostic job without DB apply.
2. Prefer a mock-safe `v4`/version-override planning task first if the project
   wants cleaner future runtime evidence that is not tied to the dual-key `v3`
   diagnostic record.
3. Defer DB apply until the Director explicitly accepts the diagnostic nature of
   `v3` or authorizes a cleaner new-version path.

Luceon recommendation: choose option 2 before any DB apply, because it preserves
the accepted `v2` DB state and avoids elevating the contaminated `v3` dual-key
record into durable Clean Material metadata.
