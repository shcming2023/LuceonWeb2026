# P0 RawMaterial2CleanMaterial Second Canonical Sample Pilot Durable Closed Loop Report

Task ID: `TASK-20260525-140710-P0-RawMaterial2CleanMaterial-Second-Canonical-Sample-Pilot-Durable-Closed-Loop`

Report time: 2026-05-25T14:20:56+0800

Status: `SUCCESS_SECOND_SAMPLE_CLOSED_LOOP_WITH_EXECUTION_DEVIATION_RECORDED`

Implementation branch: `codex/TASK-20260525-140710-second-sample-pilot`

Implementation HEAD: `f71caceef510e1c5bd6d8f9616a7aae160ecc69e`

## Summary

The second canonical sample reached the same durable RawMaterial2CleanMaterial
closed loop as the first sample:

```text
parsed ZIP -> raw seed -> CleanMaterial artifacts -> accepted CleanMaterial ->
raw2clean candidate -> durable candidate artifact -> accepted raw2clean decision
```

Target:

- material: `2241872074049025`
- task: `task-1779085090677`
- title: `蓝月、血月、橙月？月亮为啥还会变色？`

The product surface for `/cms/asset/2241872074049025` shows
`Decision: accepted`, the candidate SHA, and the candidate JSON preview.

This validates repeatability at the second-sample pilot level. It is not final
quality acceptance, batch readiness, UAT, L3, pressure PASS, release readiness,
production readiness, production online, or go-live.

## Execution Deviation

There was one execution deviation during development of the harness:

1. An early dry-run version of the script incorrectly allowed a CleanService
   runtime POST before the raw seed was written.
2. That created failed job
   `luceon-task-1779085090677-toc-rebuild-v1` with `NoSuchKey` for
   `eduassets-raw/mineru/2241872074049025/v1/content_list_v2.json`.
3. The harness was corrected so dry-run preflight no longer POSTs.
4. The successful CleanService output therefore used
   `luceon-task-1779085090677-toc-rebuild-v2`.

No cleanup or deletion was performed.

An additional 4-byte diagnostic object was written while verifying the internal
container MinIO write path:

```text
eduassets-raw/tmp/codex-test.txt
```

This object is unrelated to product metadata and was not deleted because delete
was outside the authorized boundary.

## Changed Files

- `src/app/utils/rawMaterial2CleanMaterialAlgorithm.ts`
- `server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs`
- `server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs`
- `server/tests/rawmaterial2cleanmaterial-second-sample-pilot.mjs`

## Mainline Compatibility Fix

The second sample exposed a real shape difference: `flooded_content.json`
contained 29 text fragments without stable source references.

The raw2clean skeleton now treats unreferenced `flooded_content` text as
skippable warning evidence instead of blocking the entire draft. Logic tree and
skeleton source items still require stable references. This keeps the ID-only
boundary intact while allowing the draft to proceed with zero flooded blocks.

Observed draft:

- section count: `30`
- block count: `0`
- warning class: skipped unreferenced flooded content / no flooded blocks

## Raw Seed

Parsed ZIP:

```text
eduassets-parsed/parsed/2241872074049025/mineru-result.zip
```

Extracted `_content_list_v2.json`:

```json
{
  "size_bytes": 15822,
  "sha256": "1f8f7ea04d2c69253fc80282535624e29354f272087cb268b165b3f6fc326c0d"
}
```

Raw seed object:

```text
eduassets-raw/mineru/2241872074049025/v1/content_list_v2.json
```

Final verification showed the raw seed as already present with the same SHA and
size.

## CleanService Evidence

Successful CleanService job:

```text
luceon-task-1779085090677-toc-rebuild-v2
```

Clean asset version: `v2`

Seven artifacts were produced under:

```text
eduassets-clean/toc-rebuild/2241872074049025/v2/
```

Artifact summary:

| Role | Object | Size | SHA256 |
| --- | --- | ---: | --- |
| `flooded_content` | `toc-rebuild/2241872074049025/v2/flooded_content.json` | 8409 | `7ac5c9e5253876c99db4f3a635aa3b7c285a25ae410cf7dcd7e3526723a35686` |
| `logic_tree` | `toc-rebuild/2241872074049025/v2/logic_tree.json` | 138 | `135e32777cd03442827110e179a7c95868c600a3b919d0b3b4aa2830ea2fb2ef` |
| `readable_tree` | `toc-rebuild/2241872074049025/v2/readable_tree.md` | 39 | `4dce26d3b9c196b3b7003502eebadbc64ffae62a1bb942c5aacb85960d0f0b60` |
| `skeleton` | `toc-rebuild/2241872074049025/v2/skeleton.json` | 11150 | `23805b4be4480a5ec2a9c0555692c0b8a8d37a98768115750c8364321cdf4d60` |
| `unresolved_anchors` | `toc-rebuild/2241872074049025/v2/unresolved_anchors.json` | 2 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| `metrics` | `toc-rebuild/2241872074049025/v2/metrics.json` | 116 | `f9292edbcec5e7d2bb368311293fac8dfbc56d63dcae42b606a88e25f9deca30` |
| `provenance` | `toc-rebuild/2241872074049025/v2/provenance.json` | 2051 | `96e2be689afa7f8a3b9890710765819b39aef4b69608499a6c448c15f51fc5fd` |

## Raw2Clean Candidate

Candidate object:

```text
eduassets-clean/raw-material-2-clean-material/2241872074049025/v1/candidate.json
```

Candidate SHA/size:

```json
{
  "sha256": "6849ea4ddda0cbf8f2a3b720417bfdcd69d1806ce8ceff970c59ef36ffd5dbb5",
  "size_bytes": 9396
}
```

Output contract preview:

```json
{
  "sha256": "b1358cb6a7121aa35bf2dcfcfcd10e6aafb633defc44a5446ddb811116020964",
  "size_bytes": 9336
}
```

## Durable Metadata Apply

Affected DB records:

- `tasks/task-1779085090677`
- `materials/2241872074049025`

Final post-read evidence:

```json
{
  "cleanVersion": "v2",
  "cleanDecision": "accepted",
  "raw2cleanDecision": "accepted",
  "taskCleanJob": "luceon-task-1779085090677-toc-rebuild-v2",
  "taskRaw2clean": "accepted"
}
```

## Product Surface Evidence

Browser target:

```text
http://127.0.0.1:5177/cms/asset/2241872074049025
```

Playwright result:

```json
{
  "hasCard": true,
  "hasDecision": true,
  "hasSha": true,
  "hasCandidateJson": true,
  "hasCleanVersion": true,
  "errors": [],
  "badResponses": [],
  "screenshotPath": "/tmp/luceon-task285-second-sample-product-surface.png"
}
```

## Checks

| Check | Exit |
| --- | ---: |
| `node server/tests/rawmaterial2cleanmaterial-second-sample-pilot.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-candidate-view-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-candidate-decision-smoke.mjs` | 0 |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 |
| `npx pnpm@10.4.1 run build` | 0 |
| `git diff --check` | 0 |
| Playwright product-surface verification | 0 |

Build emitted only the existing Vite chunk-size warning.

## Operation Counts

Final successful state includes:

```json
{
  "rawSeedPutObject": 1,
  "cleanServicePostFailedV1": 1,
  "cleanServicePostSuccessfulV2": 1,
  "raw2cleanCandidatePutObject": 1,
  "dbPatch": 2,
  "minioDelete": 0,
  "dockerRestartOrRecreate": 0,
  "batch": 0
}
```

The final harness verification run reconciled the already completed v2 job and
therefore did not issue another CleanService POST.

## Boundary Confirmation

No Docker/Compose restart/rebuild/recreate, MinIO delete/list-bucket
cleanup/copy/move, batch processing, source/env/secret/model mutation, final
quality acceptance, readiness, UAT, L3, pressure PASS, release readiness,
production readiness, production online, or go-live claim was made.

The task did perform more runtime POST activity than the ideal task boundary
because of the failed v1 dry-run bug. This deviation is recorded above and
should not be repeated.

## Residual Debt

- `luceon-task-1779085090677-toc-rebuild-v1` remains a failed job-store entry.
- `eduassets-raw/tmp/codex-test.txt` remains as an unrelated diagnostic object.
- Second sample candidate has zero flooded blocks because source-less text was
  skipped.
- No batch runner exists.
- No repair/reject path exists.
- Metadata schema consolidation is still deferred.

## Recommended Next Mainline Step

The current phase should not go into cleanup yet. The next mainline step should
be a minimal runtime entrypoint design/implementation for the now-proven
single-sample closed loop, with hard preflight gates that prevent dry-run paths
from submitting runtime jobs.
