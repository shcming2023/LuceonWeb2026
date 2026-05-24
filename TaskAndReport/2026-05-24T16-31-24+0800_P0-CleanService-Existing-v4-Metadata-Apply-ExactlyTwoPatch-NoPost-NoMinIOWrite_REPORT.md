# TASK-20260524-163124-P0-CleanService-Existing-v4-Metadata-Apply-ExactlyTwoPatch-NoPost-NoMinIOWrite Report

Report time: 2026-05-24T16:35:17+0800

Actor: Luceon

Task brief:

```text
TaskAndReport/2026-05-24T16-31-24+0800_P0-CleanService-Existing-v4-Metadata-Apply-ExactlyTwoPatch-NoPost-NoMinIOWrite_TASK.md
```

## Classification

```text
SUCCESS_EXISTING_V4_METADATA_APPLIED_EXACTLY_TWO_PATCH_NO_POST_NO_MINIOWRITE
```

The stage-mainline apply succeeded. The already completed `toc-rebuild v4`
CleanService output is now durable Luceon DB product truth for the canonical
single sample.

Summary:

- no runtime POST was sent in this task;
- no new Mineru2Table job was created;
- no MinIO write/delete/cleanup occurred;
- product verifier accepted the existing `v4` artifacts with
  `allowProbeJobIdSuffix=false`;
- dry-run apply returned `DRY_RUN_SUCCESS` with zero DB calls;
- exactly two DB metadata PATCHes were executed:
  - `PATCH /tasks/task-1779085089451`
  - `PATCH /materials/1842780526581841`
- post-read confirms task/material now point to accepted `toc-rebuild v4`.

This is a single-sample durable Clean Material promotion. It is not scheduler
activation, batch validation, pressure PASS, UAT, L3, production readiness,
release readiness, production online, or go-live.

## Execution Anchors

| Item | Value |
| --- | --- |
| Task issue commit | `1de228c4c7ed667510b0c5848f0bdab4f74c5885` |
| Execution `origin/main` | `1de228c4c7ed667510b0c5848f0bdab4f74c5885` |
| DB endpoint | `http://127.0.0.1:8081/__proxy/db` |
| Mineru2Table endpoint | `http://127.0.0.1:8000` |
| Target task | `task-1779085089451` |
| Target material | `1842780526581841` |
| Previous accepted job | `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230` |
| Target job | `luceon-task-1779085089451-toc-rebuild-v4` |
| Target prefix | `eduassets-clean/toc-rebuild/1842780526581841/v4/` |
| Evidence file | `/tmp/luceon-task267-apply.json` |

## Preflight Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| GitHub main synced | PASS | `HEAD == origin/main == 1de228c4c7ed667510b0c5848f0bdab4f74c5885` |
| DB before-state aligned at v2 | PASS | task job `v2` completed; material latestVersion `v2` completed |
| Existing v4 job completed | PASS | `job_id=luceon-task-1779085089451-toc-rebuild-v4`, `status=completed`, `asset_version=v4` |
| No runtime POST in this task | PASS | `postCount=0` |
| Raw input SHA/size | PASS | size `31543`, SHA256 `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db` |
| v4 seven artifacts | PASS | seven required artifact roles present |
| Verifier accepts v4 without probe suffix | PASS | `ok=true`, `errors=[]`, `provenanceJobIdPolicy=null` |
| Candidate persistable | PASS | `ok=true`, `shouldPersist=true`, `assetVersion=v4` |
| Plan targets v4 metadata only | PASS | task/material patch roots are metadata only |
| Dry-run apply | PASS | `DRY_RUN_SUCCESS`, `operationCount=0`, `dryDbCallCount=0` |
| Real apply patch count | PASS | exactly two PATCHes |
| Post DB v4 aligned | PASS | task `assetVersion=v4`; material `latestVersion=v4` |

## Existing v4 Job And Artifact Evidence

Runtime job:

| Field | Value |
| --- | --- |
| `job_id` | `luceon-task-1779085089451-toc-rebuild-v4` |
| `status` | `completed` |
| `material_id` | `1842780526581841` |
| `parse_task_id` | `task-1779085089451` |
| `asset_version` | `v4` |
| `submitted_at` | `2026-05-24T08:22:42Z` |
| `started_at` | `2026-05-24T08:22:42Z` |
| `finished_at` | `2026-05-24T08:22:44Z` |
| `error` | `null` |

MinIO inventory:

| Role | Size | SHA256 |
| --- | ---: | --- |
| `flooded_content.json` | 20054 | `e1a8355a80a5014b5a616ed441a4d0851c47d6a3d6092711ce765ffe11eea7b7` |
| `logic_tree.json` | 375 | `b61ee669b63bccb597f9ff31e5773ac1cc53a7bf6d6ef7a5ba73d467c7267665` |
| `metrics.json` | 129 | `add72cb0a0c0dcb2fe051961795da8c151181022df79770583d5fb75c7ed9718` |
| `provenance.json` | 2066 | `394b87a89375e0f403df8660de304ab9541b3276d25ba7b424f8369e5b1234c5` |
| `readable_tree.md` | 106 | `bba5cf360fa7c0d92a9489ce84dfc40458de6072f812d7ab5d381b8e828946d7` |
| `skeleton.json` | 21160 | `c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e` |
| `unresolved_anchors.json` | 2 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |

Job-store after apply remains unchanged from Task 266 post-run:

```text
jobs.json size=15069
jobs.json sha256=30e28a8138be29bbb9ecd719ac88cb8dc8e6bc4b271c697d6573bdd1b7f0df96
jobCount=6
target.status=completed
target.asset_version=v4
```

## Verifier And Plan

Verifier:

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
sourceInput.sha256=f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
```

Persistence plan:

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
newVersionIntent.previousAssetVersion=v2
newVersionIntent.previousJobId=luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230
newVersionIntent.defaultAllocatedAssetVersion=v3
newVersionIntent.targetAssetVersion=v4
newVersionIntent.newAssetVersion=v4
```

Dry-run apply:

```text
classification=DRY_RUN_SUCCESS
applied=false
operationCount=0
dryDbCallCount=0
```

## Real Apply

Apply method:

```text
controlled-direct-two-patch-from-verified-product-plan
```

Reason: the current apply executor already validates this explicit new-version
plan in dry-run. For stage breakthrough, Luceon executed the two metadata PATCHes
directly from the verified product plan instead of broadening source code in
this task.

Patch evidence:

| Order | Target | Result |
| ---: | --- | --- |
| 1 | `PATCH /tasks/task-1779085089451` | `ok=true`, id `task-1779085089451` |
| 2 | `PATCH /materials/1842780526581841` | `ok=true`, id `1842780526581841` |

Counts:

```text
postCount=0
minioWriteCount=0
patchCount=2
patchTargets=["/tasks/task-1779085089451","/materials/1842780526581841"]
```

## Post-Apply DB Evidence

Task metadata now records:

| Field | Value |
| --- | --- |
| `cleanServiceJobs.toc-rebuild.jobId` | `luceon-task-1779085089451-toc-rebuild-v4` |
| `cleanServiceJobs.toc-rebuild.assetVersion` | `v4` |
| `cleanServiceJobs.toc-rebuild.status` | `completed` |
| artifact roles | seven required roles present |
| `sourceInput.object` | `mineru/1842780526581841/v1/content_list_v2.json` |
| `sourceInput.sha256` | `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db` |
| `sourceInput.size_bytes` | `31543` |
| `stats.tokensTotal` | `6266` |

Material metadata now records:

| Field | Value |
| --- | --- |
| `cleanMaterials.toc-rebuild.latestVersion` | `v4` |
| `cleanMaterials.toc-rebuild.status` | `completed` |
| `cleanMaterials.toc-rebuild.provenanceObjectName` | `toc-rebuild/1842780526581841/v4/provenance.json` |
| `sourceInput.object` | `mineru/1842780526581841/v1/content_list_v2.json` |
| `sourceInput.sha256` | `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db` |
| `sourceInput.size_bytes` | `31543` |
| `stats.tokensTotal` | `6266` |

Material `prefix` is currently `null` because the live job response used by the
candidate builder does not expose `sink.prefix`. This does not block the durable
v4 promotion because the task metadata contains full artifact refs and material
metadata contains the v4 provenance object. It should be handled by the next
product read-surface task or later planner/candidate normalization, not by an
extra ad hoc DB PATCH here.

## Boundary Statement

Performed:

- Git sync and TaskAndReport task issuance;
- read-only DB/API, Mineru2Table job, job-store, and MinIO verification;
- verifier, candidate builder, persistence planner, and dry-run apply;
- exactly two DB metadata PATCHes;
- post-apply DB reads;
- TaskAndReport report/ledger writes.

Not performed:

- runtime POST, retry POST, submit-probe, or alternate endpoint POST;
- new Mineru2Table job creation;
- MinIO put/copy/move/delete/write/delete-marker/cleanup;
- manual job-store edit/delete/cleanup/reset;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- env, credential, model, secret, source sample, or local override mutation;
- worker, scheduler, or upload-server CleanService activation;
- retry/reparse/re-AI/repair/rollback;
- source-code changes;
- batch processing, fresh sample selection, pressure test, UAT, L3, production
  readiness, release readiness, production online, or go-live claim.

## Residuals

1. Material clean summary has `prefix=null`; task artifact refs and material
   provenance ref are present, so this is a product read-surface normalization
   issue, not a blocker for this apply.
2. Mineru2Table provenance still records `input.size_bytes=0`; verifier
   compensates from the independently verified raw input size and emits
   `input-size-bytes-zero`.
3. The controlled direct two-PATCH path should be folded into product-owned
   apply semantics later, but not before the current stage breakthrough.

## Next Recommendation

Proceed to the second mainline task:

```text
P0 CleanMaterial Minimal Product Read Surface NoRuntime
```

Goal: make the now-durable `toc-rebuild v4` state visible and consumable through
the product/API surface with minimal scope: current clean version, job id,
artifact refs, provenance object, sourceInput, tokens, warnings, and unresolved
anchor count. Avoid UI redesign, registry governance, scheduler activation, and
batch work in that task.
