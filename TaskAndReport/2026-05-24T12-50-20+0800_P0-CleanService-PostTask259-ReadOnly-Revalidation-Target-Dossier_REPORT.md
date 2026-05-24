# TASK-20260524-125020-P0-CleanService-PostTask259-ReadOnly-Revalidation-Target-Dossier Report

Report time: 2026-05-24T13:38:00+0800

## 1. Final Classification

```text
COMPLETED_READ_ONLY_TARGET_DOSSIER_RECOMMEND_EXISTING_V3_NO_POST_WITH_SOURCE_INPUT_PREREQUISITE
```

This dossier performed only read-only control, code, DB GET, MinIO list/get,
job-store read, and local product-code rehearsal checks.

No runtime POST, submit-probe, DB write, MinIO write/delete, Docker/Compose
mutation, env/credential/model/sample mutation, Task 256 harness rerun,
cleanup/reset/rollback, worker activation, real DB apply, UAT, L3, pressure
PASS, readiness, production online, or go-live claim was performed.

## 2. Baseline And Required Checks

Baseline:

```text
HEAD = origin/main = fc502ad9df2241beac5eb43691ff4ca0d4ff07b2
```

Required checks:

```text
git status --short --branch
exit 0
output: ## main...origin/main

git fetch origin --prune --tags
exit 0
output: no output

git pull --ff-only origin main
exit 0
output:
From https://github.com/shcming2023/Luceon2026
 * branch            main       -> FETCH_HEAD
Already up to date.

git rev-parse HEAD origin/main
exit 0
output:
fc502ad9df2241beac5eb43691ff4ca0d4ff07b2
fc502ad9df2241beac5eb43691ff4ca0d4ff07b2

git diff --check
exit 0
output: no output
```

Read paths:

- `TaskAndReport/TASK_TRACKING_LIST.md`
- Task 245 report
- Task 253 report
- Task 256 corrected report
- Task 256 Luceon review v3
- Task 259 Luceon review v2
- `server/services/cleanservice/asset-version.mjs`
- `server/services/cleanservice/orchestration-runner.mjs`
- `server/services/cleanservice/cleanservice-worker.mjs`
- `server/services/cleanservice/raw-material-adapter.mjs`
- `server/services/cleanservice/output-verifier.mjs`
- `server/services/cleanservice/metadata-apply-executor.mjs`
- `server/tests/cleanservice-*.mjs`

## 3. Current Accepted v2 State

Read-only DB GET command shape:

```text
docker exec cms-upload-server node --input-type=module -e '<GET only:
  http://cms-db-server:8789/tasks/task-1779085089451
  http://cms-db-server:8789/materials/1842780526581841
  print bounded cleanServiceJobs / cleanMaterials / raw-material keys>'
```

Exit code: `0`. HTTP statuses: both `200`. Read-only: yes.

Observed current DB state:

| Target | Current state |
| --- | --- |
| Task | `task-1779085089451`, state `review-pending`, `mineruStatus=completed`, `materialId=1842780526581841` |
| Task clean job | `toc-rebuild` completed, `assetVersion=v2`, job `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230` |
| Material | `1842780526581841`, status `reviewing` |
| Material clean material | `toc-rebuild` completed, `latestVersion=v2`, prefix `toc-rebuild/1842780526581841/v2/` |
| Persisted source input | bucket `eduassets-raw`, object `mineru/1842780526581841/v1/content_list_v2.json`, SHA256 `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`, size `31543` |
| Canonical rawMaterial branch | absent: `task.metadata.rawMaterial` is `null` |

Important nuance: the live task has legacy parsed evidence
(`parsedPrefix`, `artifactManifestObjectName`, `markdownObjectName`) and the
accepted CleanService v2 `sourceInput`, but it does not have
`metadata.rawMaterial.mineru.contentListV2`. Current
`buildCanonicalRawMaterialRef()` only accepts the canonical `rawMaterial`
branch for request planning.

## 4. Current MinIO Physical State

Read-only MinIO command shape:

```text
docker exec -i cms-upload-server node --input-type=module <<'NODE'
list/get only:
  s3://eduassets-raw/mineru/1842780526581841/
  s3://eduassets-clean/toc-rebuild/1842780526581841/
compute SHA256 from read streams
NODE
```

Exit code: `0`. Read-only: yes. It used `listObjectsV2` and `getObject` only.

Observed object counts:

| Prefix | Object count |
| --- | ---: |
| `eduassets-raw/mineru/1842780526581841/` | `1` |
| `eduassets-clean/toc-rebuild/1842780526581841/` | `21` |

Raw input:

```text
eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
size=31543
sha256=f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
```

Clean prefix summary:

| Version | Count | Interpretation |
| --- | ---: | --- |
| `v1` | `7` | Locked earlier contaminated/failed-run evidence; not a reuse target. |
| `v2` | `7` | Accepted Task 245/253/251 DB-applied artifact set. |
| `v3` | `7` | Task 256 diagnostic artifact set exists physically; not DB-applied. |

Current `v3` seven-artifact hashes:

| Artifact | Size | SHA256 |
| --- | ---: | --- |
| `flooded_content.json` | `20054` | `e1a8355a80a5014b5a616ed441a4d0851c47d6a3d6092711ce765ffe11eea7b7` |
| `logic_tree.json` | `375` | `b61ee669b63bccb597f9ff31e5773ac1cc53a7bf6d6ef7a5ba73d467c7267665` |
| `metrics.json` | `129` | `add72cb0a0c0dcb2fe051961795da8c151181022df79770583d5fb75c7ed9718` |
| `provenance.json` | `2072` | `fc0cfd7bd417eb558f2793826a1718ae8ab04a96cd3d9a7291cf9ea33cc452ee` |
| `readable_tree.md` | `106` | `bba5cf360fa7c0d92a9489ce84dfc40458de6072f812d7ab5d381b8e828946d7` |
| `skeleton.json` | `21160` | `c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e` |
| `unresolved_anchors.json` | `2` | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |

Read-only provenance/metrics summary:

| Version | Provenance job_id | Input size in provenance | Tokens total |
| --- | --- | ---: | ---: |
| `v2` | `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230` | `0` | `6266` |
| `v3` | `luceon-task-1779085089451-toc-rebuild-v3-probe` | `0` | `6266` |

The `v3` physical prefix is reusable for read-only verification only if the
next task explicitly treats the canonical job id
`luceon-task-1779085089451-toc-rebuild-v3` and observed provenance job id
`luceon-task-1779085089451-toc-rebuild-v3-probe` under the Task 259
`allowProbeJobIdSuffix: true` policy.

## 5. Current Mineru2Table Job-Store State

Read-only job-store command shape:

```text
node --input-type=module -e '<read only
  /Users/concm/prod_workspace/Mineru2Tables/data/jobs.json
  compute size/SHA256/key counts and print bounded job summaries>'
```

Exit code: `0`. Read-only: yes.

Observed file state:

```text
path=/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json
sizeBytes=12198
sha256=45ad98bc88cf99b54ca5323f5aa6cd59789609e00efbae629818811e6e14b370
keyCount=5
```

Relevant keys:

| Job key | Status | Asset version | Artifact refs |
| --- | --- | --- | --- |
| `luceon-task242-toc-rebuild-1842780526581841-v1-20260522025136` | `completed` | `v1` | seven refs |
| `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230` | `completed` | `v2` | seven refs |
| `luceon-task-1779085089451-toc-rebuild-v3` | `completed` | `v3` | seven refs under `toc-rebuild/1842780526581841/v3/` |
| `luceon-task-1779085089451-toc-rebuild-v3-probe` | `completed` | `v3` | seven refs under the same `v3` prefix |

This means the current `v3` evidence is not a pristine single-job record:
the job store contains both canonical and `-probe` completed keys, and both
point to the same physical `v3` prefix.

## 6. Current Product-Code Read-Only Rehearsals

### 6.1 Full Runner With Live DB Payload

Read-only command shape:

```text
node --input-type=module <<'NODE'
GET task/material through cms-upload-server -> cms-db-server
run runCleanServiceTocRebuildOnce() with intent=create-new-version
inject tripwire deps for submitJob/queryJob/artifactReader/dbClient
NODE
```

Exit code: `0`. Read-only: yes. Runtime POST: no. DB/MinIO write: no.

Result:

```json
{
  "outcome": "threw",
  "message": "legacy-parsed-evidence-skipped",
  "code": "skipped-policy",
  "calls": []
}
```

Interpretation: with the current live DB payload unchanged, the full runner
does not reach `submitJob`, `queryJob`, artifact reads, or DB writes. It throws
while planning the request because the task lacks
`metadata.rawMaterial.mineru.contentListV2`. This is a newly confirmed
precondition gap for any direct same-job or new-version runtime target.

### 6.2 Verifier-Only Existing v3 Artifact Check

Read-only command shape:

```text
node --input-type=module <<'NODE'
read job-store key luceon-task-1779085089451-toc-rebuild-v3
use current verifyCleanServiceOutputArtifacts()
artifactReader performs MinIO getObject only through cms-upload-server
expected jobId=luceon-task-1779085089451-toc-rebuild-v3
allowProbeJobIdSuffix=true
rawInput expected from accepted sourceInput
NODE
```

Exit code: `0`. Read-only: yes.

Result:

```json
{
  "ok": true,
  "cleanState": "completed",
  "errors": [],
  "warnings": [
    "provenance-job-id-probe-suffix-accepted",
    "input-size-bytes-zero"
  ],
  "inputSizeBytes": 31543,
  "tokensTotal": 6266,
  "canonicalJobId": "luceon-task-1779085089451-toc-rebuild-v3",
  "provenanceJobId": "luceon-task-1779085089451-toc-rebuild-v3-probe",
  "provenanceJobIdPolicy": "accepted-probe-suffix"
}
```

Interpretation: Task 259's product verifier can consume the existing physical
`v3` artifacts without harness provenance mutation, provided the probe suffix
is explicitly allowed and the raw input expectation is supplied from accepted
source-input evidence. This is useful but is not a full runner or runtime
success proof.

## 7. Target Decision Matrix

| Candidate | Evidence value | Safety | Current blocker / contamination risk | Decision |
| --- | --- | --- | --- | --- |
| Existing `v3` read-only verification only | Verifies current product verifier/candidate boundary against real `v3` artifacts and Task 259 `-probe` policy. | No POST, no DB write, no MinIO write. | Not full runtime; full runner currently stops at source-input planning without canonical `rawMaterial`. | Recommended immediate target, but only as no-POST evidence and paired with a source-input prerequisite. |
| Same `v3` idempotent submit/query | Could test runtime idempotency of canonical `v3` job. | Requires `POST /api/v1/jobs` or live job API call; not authorized in this dossier. | Job-store already has both canonical and `-probe` `v3` jobs pointing to the same prefix; current DB payload cannot build request without source-input fix; evidence would remain hard to call pristine exactly-one-POST. | Not recommended now. |
| New `v4` explicit new-version runtime dry-run | Would produce cleaner new target if request planning and authorization were ready. | Requires new runtime POST and new clean prefix writes. | Current allocator sees DB-applied `v2` and would plan `v3`, not `v4`, unless DB state changes or explicit version override policy is added; DB lacks canonical rawMaterial branch. | Not recommended now. |
| Fresh-sample runtime dry-run | Avoids existing v2/v3/probe history on this sample. | Requires sample selection and runtime POST; may require new raw-material evidence audit. | Wider scope and not needed before fixing/proving current product request planning and source-input policy. | Defer. |

## 8. Recommended Next Task Boundary

Recommended next task:

```text
P0 CleanService Existing-v3 No-POST Product Reconciliation And Source-Input Compatibility MockSafe NoRuntime
```

Recommended actor: `Lucode`, after Director approval.

Mainline objective:

- make the product path able to use the current live task shape without the Task
  256 harness injecting `metadata.rawMaterial`;
- prove, mock-safe and no-runtime, that the current product runner can reach
  an existing `v3` dry-run success path using the accepted source input and
  current Task 259 verifier policy.

Required boundary:

- no runtime POST or submit-probe;
- no live Mineru2Table query unless separately authorized as GET-only and
  proven non-mutating;
- no DB PATCH/POST/PUT/DELETE;
- no MinIO put/copy/move/delete/write/delete-marker;
- no Docker/Compose restart/recreate/build/down/up/volume/prune;
- no job-store edit;
- no env/credential/model/sample mutation;
- no cleanup/reset/rollback/reparse/re-AI;
- no UAT/L3/pressure/readiness/go-live wording.

Likely allowed code surface for the next task:

- `server/services/cleanservice/raw-material-adapter.mjs`
- `server/services/cleanservice/cleanservice-worker.mjs`
- `server/services/cleanservice/orchestration-runner.mjs`
- focused `server/tests/cleanservice-*.mjs`

Acceptance target:

- current live-shaped task payload without `metadata.rawMaterial` is handled by
  an explicit, traceable source-input policy rather than ad hoc harness
  injection;
- existing `v3` canonical job id plus observed `-probe` provenance is accepted
  only under explicit policy;
- runner reaches `DRY_RUN_SUCCESS` in a mock-safe/no-runtime rehearsal using
  injected read-only artifact/job fixtures;
- all default/false `-probe` cases remain rejected;
- real apply and mismatch cases remain blocked.

Stop rule:

- stop and report blocked if passing the rehearsal requires POST, real job
  submit/query, DB write, MinIO write, direct `jobs.json` edit, Docker/env
  mutation, or sample/data cleanup.

## 9. Not Recommended Paths

- Do not proceed directly to real DB apply from Task 256 or current `v3`
  evidence. `v3` is still diagnostic and not DB-applied.
- Do not run a same-`v3` idempotent submit yet. The canonical/probe dual job
  keys and shared prefix make the evidence non-pristine, and the live DB payload
  still lacks the request-planning rawMaterial branch.
- Do not try to force `v4` by DB cleanup or metadata mutation. That would widen
  scope and contaminate the accepted `v2` state.
- Do not switch to a fresh sample before closing the source-input compatibility
  gap; otherwise the same request-planning ambiguity may reappear under a wider
  evidence surface.

## 10. Skipped Checks

Skipped intentionally:

- Task 256 runtime harness: forbidden by this task.
- `POST /api/v1/jobs` and `POST /api/v1/jobs:from-storage`: forbidden.
- live Mineru2Table job API query: not needed for this decision and could
  blur the no-runtime boundary.
- DB PATCH/POST/PUT/DELETE: forbidden.
- MinIO write/delete/copy/move: forbidden.
- Docker/Compose restart/recreate/build/down/up/volume/prune: forbidden.
- real DB apply: forbidden.

## 11. Safety Statement And Residual Risk

This dossier is a read-only target decision audit only. It is not runtime
validation, UAT, L3, pressure PASS, production readiness, release readiness,
production online, or go-live.

Residual risks:

1. The current accepted DB state remains `v2`; `v3` is physical diagnostic
   evidence only.
2. `v3` has canonical and `-probe` completed job-store keys pointing to the
   same prefix, so it must be treated as diagnostic/reconciliation evidence,
   not pristine exactly-one-POST success evidence.
3. Both `v2` and `v3` provenance still record `input size_bytes=0`; product
   compensation can recover `31543` from expected source-input evidence, but
   service provenance quality remains debt.
4. Current live task metadata lacks `metadata.rawMaterial.mineru.contentListV2`;
   without a product-level source-input compatibility policy, direct runner
   runtime validation would still require harness-like injection.
