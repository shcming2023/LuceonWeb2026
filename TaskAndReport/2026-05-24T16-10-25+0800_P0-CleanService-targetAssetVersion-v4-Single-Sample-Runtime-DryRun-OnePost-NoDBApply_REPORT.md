# TASK-20260524-161025-P0-CleanService-targetAssetVersion-v4-Single-Sample-Runtime-DryRun-OnePost-NoDBApply Report

Report time: 2026-05-24T16:30:00+0800

Actor: Luceon

Task brief:

```text
TaskAndReport/2026-05-24T16-10-25+0800_P0-CleanService-targetAssetVersion-v4-Single-Sample-Runtime-DryRun-OnePost-NoDBApply_TASK.md
```

## Classification

```text
SUCCESS_RUNTIME_DRYRUN_V4_ONEPOST_NO_DB_APPLY
```

The controlled runtime dry-run succeeded:

- preflight gates passed;
- exactly one CleanService Protocol v1 `POST /api/v1/jobs` was sent;
- the runtime job completed as `luceon-task-1779085089451-toc-rebuild-v4`;
- seven `v4` artifacts were created under `eduassets-clean/toc-rebuild/1842780526581841/v4/`;
- product verifier accepted canonical provenance with `allowProbeJobIdSuffix=false`;
- metadata persistence apply stayed dry-run only;
- DB task/material accepted metadata remained unchanged at `v2`;
- no second POST, DB apply, manual MinIO write/delete, Docker/Compose mutation, job-store edit, source-code change, worker activation, UAT/L3/readiness/pressure PASS/go-live claim was performed.

This is runtime dry-run evidence only. It is not production readiness, release readiness, L3, pressure PASS, or go-live.

## Execution Anchors

| Item | Value |
| --- | --- |
| Execution main SHA | `2611222e0da0340ebd7a3d93f8119e44d5d90b63` |
| `origin/main` SHA | `2611222e0da0340ebd7a3d93f8119e44d5d90b63` |
| Dispatch main recorded in task row | `d26c7ced359d0a0f249fd396d3195dec5b06e28a` |
| Runtime endpoint | `http://127.0.0.1:8000` |
| DB read endpoint | `http://127.0.0.1:8081/__proxy/db` |
| MinIO read method | read-only SDK calls from `cms-upload-server` container to `minio:9000` |
| Target task | `task-1779085089451` |
| Target material | `1842780526581841` |
| Target asset version | `v4` |
| Expected/runtime job id | `luceon-task-1779085089451-toc-rebuild-v4` |
| Raw input | `eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json` |
| Raw input SHA256 | `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db` |
| Raw input size | `31543` |

## Required Checks

| Command | Exit | Result |
| --- | ---: | --- |
| `git status --short --branch` | 0 | `## main...origin/main`; no tracked changes before report edits |
| `git fetch origin --prune --tags` | 0 | fetched from origin |
| `git pull --ff-only origin main` | 0 | already up to date |
| `git rev-parse HEAD origin/main` | 0 | both `2611222e0da0340ebd7a3d93f8119e44d5d90b63` |
| `git diff --check` | 0 | passed before execution |
| `node --check server/services/cleanservice/asset-version.mjs` | 0 | passed |
| `node --check server/services/cleanservice/cleanservice-worker.mjs` | 0 | passed |
| `node --check server/services/cleanservice/orchestration-runner.mjs` | 0 | passed |
| `node --check server/services/cleanservice/metadata-apply-executor.mjs` | 0 | passed |
| `node server/tests/cleanservice-asset-version-smoke.mjs` | 0 | `PASS asset version allocator smoke` |
| `node server/tests/cleanservice-orchestration-runner-smoke.mjs` | 0 | 29/29 passed, including targetAssetVersion v4 cases |
| `node server/tests/cleanservice-metadata-apply-executor-smoke.mjs` | 0 | all apply-executor smoke cases passed |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | passed |

Non-material helper note: one local job-store summary helper had a JavaScript syntax typo and exited 1 before being rerun successfully. It performed no runtime, DB, MinIO, Docker, job-store, or source mutation and was not used as acceptance evidence.

## Preflight Gate Table

| Gate | Result | Evidence |
| --- | --- | --- |
| GitHub `main` synchronized and clean | PASS | `HEAD == origin/main == 2611222e0da0340ebd7a3d93f8119e44d5d90b63`; status clean before report edits |
| Task 265 code present on `main` | PASS | targetAssetVersion request planning smoke in `cleanservice-orchestration-runner-smoke.mjs` passed; direct planner generated v4 request |
| Target task/material readable | PASS | `GET /tasks/task-1779085089451` and `GET /materials/1842780526581841` returned 200 through DB proxy |
| Existing accepted metadata aligned at `v2` | PASS | task `cleanServiceJobs.toc-rebuild.assetVersion=v2`; material `cleanMaterials.toc-rebuild.latestVersion=v2`; both completed |
| Previous task job id matches | PASS | `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230` |
| Raw input object exists and matches expected SHA/size | PASS | size `31543`, SHA256 `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db` |
| Target `v4` job id absent before POST | PASS | `GET /api/v1/jobs/luceon-task-1779085089451-toc-rebuild-v4` returned 404 `job_not_found`; local `jobs.json` job count was 5 |
| Target `v4` prefix absent before POST | PASS | MinIO list for `toc-rebuild/1842780526581841/v4/` returned count 0 |
| Product planner generates expected request without DB write | PASS | request job id `luceon-task-1779085089451-toc-rebuild-v4`, asset version `v4`, sink prefix `toc-rebuild/1842780526581841/v4/` |
| Runtime endpoint and health/status reachable | PASS | Mineru2Table `/health` healthy; `/openapi.json` exposes `/api/v1/jobs`; DB proxy health OK; MinIO health through frontend proxy OK |

Direct host `http://127.0.0.1:8789/health` is not exposed by the current Compose boundary; the accepted host read path for this task was the Nginx DB proxy at `http://127.0.0.1:8081/__proxy/db`.

## Product Request Evidence

The request was generated from current `main` product code, using:

```js
{
  intent: "create-new-version",
  newVersionReason: "director-authorized-v4-runtime-dryrun-no-db-apply",
  targetAssetVersion: "v4",
  reconcileExistingJob: false,
  allowProbeJobIdSuffix: false
}
```

Planner output:

| Field | Value |
| --- | --- |
| `versionPlan.defaultAllocatedAssetVersion` | `v3` |
| `versionPlan.targetAssetVersion` | `v4` |
| `versionPlan.previousAssetVersion` | `v2` |
| `versionPlan.previousJobId` | `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230` |
| `request.job_id` | `luceon-task-1779085089451-toc-rebuild-v4` |
| `request.asset_version` | `v4` |
| `request.inputs[0].source.bucket` | `eduassets-raw` |
| `request.inputs[0].source.object` | `mineru/1842780526581841/v1/content_list_v2.json` |
| `request.inputs[0].hash` | `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db` |
| `request.sink.bucket` | `eduassets-clean` |
| `request.sink.prefix` | `toc-rebuild/1842780526581841/v4/` |

## One-POST Evidence

`postCount` is counted before the submission call. It remained exactly `1`.

| Time | Event | Status |
| --- | --- | --- |
| 2026-05-24T08:22:42.857Z | planned | job `luceon-task-1779085089451-toc-rebuild-v4`, assetVersion `v4` |
| 2026-05-24T08:22:42.857Z | submit start | `postCount=1` |
| 2026-05-24T08:22:42.872Z | submit returned | `processing` |
| 2026-05-24T08:22:42.876Z | poll 1 | `processing` |
| 2026-05-24T08:22:47.880Z | poll 2 | `completed` |

Runtime job facts:

| Field | Value |
| --- | --- |
| `job_id` | `luceon-task-1779085089451-toc-rebuild-v4` |
| `status` | `completed` |
| `service_name` | `toc-rebuild` |
| `protocol_version` | `v1` |
| `material_id` | `1842780526581841` |
| `parse_task_id` | `task-1779085089451` |
| `asset_version` | `v4` |
| `submitted_at` | `2026-05-24T08:22:42Z` |
| `started_at` | `2026-05-24T08:22:42Z` |
| `finished_at` | `2026-05-24T08:22:44Z` |
| `error` | `null` |

## Job Store Evidence

Allowed service-side job-store write occurred as the direct consequence of the one POST.

| Moment | Size | SHA256 | Job count | Target job |
| --- | ---: | --- | ---: | --- |
| Before POST | `12198` | `45ad98bc88cf99b54ca5323f5aa6cd59789609e00efbae629818811e6e14b370` | 5 | absent |
| After POST | `15069` | `30e28a8138be29bbb9ecd719ac88cb8dc8e6bc4b271c697d6573bdd1b7f0df96` | 6 | present/completed |

After POST target job summary:

```text
job_id=luceon-task-1779085089451-toc-rebuild-v4
status=completed
asset_version=v4
material_id=1842780526581841
parse_task_id=task-1779085089451
artifactKeys=flooded_content,logic_tree,metrics,provenance,readable_tree,skeleton,unresolved_anchors
tokens.prompt=6212
tokens.completion=54
tokens.total=6266
cost_cny_estimated=0.006319999999999999
cost_cny_actual=0
```

No manual job-store edit/delete/cleanup was performed.

## v4 Artifact Inventory

Bucket: `eduassets-clean`

Prefix: `toc-rebuild/1842780526581841/v4/`

| Role | Size | SHA256 |
| --- | ---: | --- |
| `flooded_content.json` | 20054 | `e1a8355a80a5014b5a616ed441a4d0851c47d6a3d6092711ce765ffe11eea7b7` |
| `logic_tree.json` | 375 | `b61ee669b63bccb597f9ff31e5773ac1cc53a7bf6d6ef7a5ba73d467c7267665` |
| `metrics.json` | 129 | `add72cb0a0c0dcb2fe051961795da8c151181022df79770583d5fb75c7ed9718` |
| `provenance.json` | 2066 | `394b87a89375e0f403df8660de304ab9541b3276d25ba7b424f8369e5b1234c5` |
| `readable_tree.md` | 106 | `bba5cf360fa7c0d92a9489ce84dfc40458de6072f812d7ab5d381b8e828946d7` |
| `skeleton.json` | 21160 | `c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e` |
| `unresolved_anchors.json` | 2 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |

Metrics evidence:

```text
tokens.prompt=6212
tokens.completion=54
tokens.total=6266
cost_cny_estimated=0.006319999999999999
```

## Provenance Evidence

`provenance.json` records:

| Field | Value |
| --- | --- |
| `schema` | `luceon-provenance/v1` |
| `service.name` | `toc-rebuild` |
| `service.protocol_version` | `v1` |
| `asset.material_id` | `1842780526581841` |
| `asset.asset_version` | `v4` |
| `asset.prefix` | `toc-rebuild/1842780526581841/v4/` |
| `job.job_id` | `luceon-task-1779085089451-toc-rebuild-v4` |
| `job.parse_task_id` | `task-1779085089451` |
| `input.bucket` | `eduassets-raw` |
| `input.object` | `mineru/1842780526581841/v1/content_list_v2.json` |
| `input.sha256` | `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db` |
| `input.size_bytes` | `0` |

The job id is canonical and has no `-probe` suffix. The verifier accepted this with `allowProbeJobIdSuffix=false`.

Residual debt: Mineru2Table still writes `input.size_bytes=0` in provenance. Current Luceon verifier compensates this from the expected raw input fact and emits `input-size-bytes-zero`. This is a known provenance-quality debt, not a blocker for this task because the raw object was independently verified as size `31543` and SHA-matched.

## Verifier Result

Current product verifier result:

```text
ok=true
cleanState=completed
errors=[]
warnings=["input-size-bytes-zero"]
unresolvedAnchorCount=0
inputSizeBytes=31543
tokensPrompt=6212
tokensCompletion=54
tokensTotal=6266
canonicalJobId=luceon-task-1779085089451-toc-rebuild-v4
provenanceJobId=luceon-task-1779085089451-toc-rebuild-v4
provenanceJobIdPolicy=null
sourceInput.bucket=eduassets-raw
sourceInput.object=mineru/1842780526581841/v1/content_list_v2.json
sourceInput.sha256=f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
sourceInput.sizeBytes=31543
```

## Dry-Run Persistence And Apply

Candidate:

```text
ok=true
shouldPersist=true
serviceName=toc-rebuild
materialId=1842780526581841
parseTaskId=task-1779085089451
assetVersion=v4
jobId=luceon-task-1779085089451-toc-rebuild-v4
cleanState=completed
```

Plan:

```text
ok=true
shouldApply=true
dryRun=true
serviceName=toc-rebuild
materialId=1842780526581841
parseTaskId=task-1779085089451
audit.costSource=job-stats
audit.tokensTotal=6266
audit.cleanState=completed
newVersionIntent.intent=create-new-version
newVersionIntent.previousAssetVersion=v2
newVersionIntent.previousJobId=luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230
newVersionIntent.defaultAllocatedAssetVersion=v3
newVersionIntent.targetAssetVersion=v4
newVersionIntent.newAssetVersion=v4
```

Dry-run apply result:

```text
ok=true
applied=false
operationCount=0
classification=DRY_RUN_SUCCESS
reason=Dry-run verification completed successfully. No real writes performed.
dbCallCount=0
```

No DB update function was called.

## Post-Run DB Unchanged Evidence

Post-run DB reads confirmed the accepted metadata remained unchanged:

| Record | Field | Value |
| --- | --- | --- |
| Task `task-1779085089451` | `cleanServiceJobs.toc-rebuild.jobId` | `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230` |
| Task `task-1779085089451` | `cleanServiceJobs.toc-rebuild.assetVersion` | `v2` |
| Task `task-1779085089451` | `cleanServiceJobs.toc-rebuild.status` | `completed` |
| Material `1842780526581841` | `cleanMaterials.toc-rebuild.latestVersion` | `v2` |
| Material `1842780526581841` | `cleanMaterials.toc-rebuild.status` | `completed` |

## Boundary Statement

Performed:

- read-only Git, DB, MinIO, job-store, health/status checks;
- exactly one runtime `POST /api/v1/jobs` for the target v4 request;
- bounded runtime status polling;
- read-only post-run artifact, provenance, job-store, and DB verification;
- local report/ledger edits.

Not performed:

- second POST, retry POST, submit-probe, alternate endpoint POST;
- DB PATCH/POST/PUT/DELETE or real metadata apply;
- manual MinIO put/copy/move/delete/cleanup;
- manual job-store edit/delete/cleanup/reset;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- env, credential, model, secret, source sample, or local override mutation;
- worker, scheduler, or upload-server CleanService activation;
- retry/reparse/re-AI/repair/rollback;
- source-code changes;
- UAT, L3, pressure PASS, production readiness, release readiness, production online, or go-live claim.

Read-only Docker observations/container exec were used only to reach internal MinIO and inspect running service status; no container lifecycle or volume/network mutation was performed.

## Risks And Recommendation

Mainline result: the v4 runtime path is now proven for the canonical single sample up to dry-run metadata persistence.

Residual risks:

1. DB still points to accepted `v2`; no durable Luceon metadata promotion has happened.
2. Mineru2Table provenance still reports `input.size_bytes=0`; Luceon verifier compensates it, but the service-side quality debt remains.
3. This is one-sample evidence only and does not cover batch, pressure, UAT, L3, or readiness.

Recommended next task:

```text
P0 CleanService targetAssetVersion-v4 Existing-Job Metadata Apply ExactlyTwoPatch NoPost NoMinIOWrite
```

Scope recommendation: no new runtime POST; no MinIO write; preflight existing completed v4 job/artifacts; run the same verifier; then, only with explicit Director authorization, apply exactly two DB metadata PATCHes for task/material and verify DB transitions from accepted `v2` to accepted `v4`.
