# P0 RawMaterial2CleanMaterial Third Canonical Sample Pilot Strict Preflight Report

Task ID: `TASK-20260525-143252-P0-RawMaterial2CleanMaterial-Third-Canonical-Sample-Pilot-Strict-Preflight`

Report time: 2026-05-25T14:46:18+0800

Status: `SUCCESS_THIRD_SAMPLE_STRICT_REPEATABILITY_PILOT`

Implementation branch: `codex/TASK-20260525-143252-third-sample-pilot`

Implementation HEAD: `ae0735a5cabe99070cdbf8dec24b4e3cb64bd355`

## Summary

The third canonical sample reached the durable RawMaterial2CleanMaterial closed
loop under the stricter Task 287 gates:

```text
parsed ZIP -> raw seed -> CleanMaterial artifacts -> accepted CleanMaterial ->
raw2clean candidate -> durable candidate artifact -> accepted raw2clean decision
```

Target:

- material: `589495534045014`
- task: `task-1779085091953`
- title: `出国`

Unlike Task 285, this pilot did not create a failed CleanService namespace, did
not switch to a fallback asset version, did not perform any extra diagnostic
MinIO write, and did not issue a second CleanService POST.

This supports upgrading the next decision from third-sample repeatability to a
bounded mini-batch pilot. It is not final quality acceptance, UAT, L3, pressure
PASS, release readiness, production readiness, production online, or go-live.

## Changed Files

- `server/tests/rawmaterial2cleanmaterial-third-sample-pilot.mjs`

## Strict Preflight Evidence

Dry-run command:

```bash
node server/tests/rawmaterial2cleanmaterial-third-sample-pilot.mjs
```

Exit code: `0`

Dry-run boundaries:

```json
{
  "rawSeedPutObject": 0,
  "cleanServicePost": 0,
  "raw2cleanCandidatePutObject": 0,
  "dbPatch": 0,
  "minioDelete": 0,
  "runtimePostOtherThanCleanService": 0,
  "dockerOperation": 0,
  "batch": 0
}
```

The script verifies the extracted raw seed SHA/size before any write or POST:

```json
{
  "sha256": "6dc482285a6ad529497294fc96a0f31456155f33f082debb821f8d1a8bd8920a",
  "size_bytes": 5873
}
```

## Real Apply Evidence

Real apply command:

```bash
RAW2CLEAN_THIRD_SAMPLE_REAL_APPLY=1 node server/tests/rawmaterial2cleanmaterial-third-sample-pilot.mjs
```

Exit code: `0`

Operation counts:

```json
{
  "rawSeedPutObject": 1,
  "cleanServicePost": 1,
  "raw2cleanCandidatePutObject": 1,
  "dbPatch": 2,
  "minioDelete": 0,
  "runtimePostOtherThanCleanService": 0,
  "dockerOperation": 0,
  "batch": 0
}
```

The one CleanService job was:

```text
luceon-task-1779085091953-toc-rebuild-v1
```

It completed on `assetVersion=v1` without namespace recovery.

## CleanService Artifacts

Seven artifacts were produced under:

```text
eduassets-clean/toc-rebuild/589495534045014/v1/
```

| Role | Object | Size | SHA256 |
| --- | --- | ---: | --- |
| `flooded_content` | `toc-rebuild/589495534045014/v1/flooded_content.json` | 3157 | `2d20da9b9e5c8f9f394d7d4b0f2beedfb0bcd120c0f640758df1972ac46d0a25` |
| `logic_tree` | `toc-rebuild/589495534045014/v1/logic_tree.json` | 343 | `9ccd30f9156dcc40a0a7e912ef17e364716fd250468523016acfdd51e21c7a43` |
| `readable_tree` | `toc-rebuild/589495534045014/v1/readable_tree.md` | 75 | `63749958c486d1cf97b2b6e884e71500ea66f839577b2b457454e4c01afa3dd7` |
| `skeleton` | `toc-rebuild/589495534045014/v1/skeleton.json` | 3795 | `3582954ee6739b055b673541ea6b7da07d593d32877b13caac3f75431b253d7c` |
| `unresolved_anchors` | `toc-rebuild/589495534045014/v1/unresolved_anchors.json` | 2 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| `metrics` | `toc-rebuild/589495534045014/v1/metrics.json` | 130 | `e752d236562b534d054413e91b67bdbb8cd9eaded66ab009653a66296131fbc0` |
| `provenance` | `toc-rebuild/589495534045014/v1/provenance.json` | 2061 | `c7f76c2fec368a13bb63f53296c9da432c003ac04990982422b9678305f75938` |

Raw2Clean draft evidence from the real run:

- section count: `16`
- block count: `14`

## Raw2Clean Candidate

Candidate object:

```text
eduassets-clean/raw-material-2-clean-material/589495534045014/v1/candidate.json
```

Candidate SHA/size:

```json
{
  "sha256": "8bab2dec54d608c3ba8dd5bbcabf9de894845e532501b227a2224f92dcf846b0",
  "size_bytes": 6030
}
```

Output contract preview:

```json
{
  "sha256": "36c3aab5a02eae2b8679568fa0c68f792e1a54b515d097edf4f3a7bf182b395a",
  "size_bytes": 5970
}
```

## Durable Metadata Apply

Affected DB records:

- `tasks/task-1779085091953`
- `materials/589495534045014`

Post-read evidence:

```json
{
  "cleanJobId": "luceon-task-1779085091953-toc-rebuild-v1",
  "cleanDecision": "accepted",
  "raw2cleanTaskStatus": "accepted",
  "raw2cleanDecision": "accepted"
}
```

No full candidate JSON, sections, blocks, or raw content were embedded in DB
metadata.

## Product Surface Evidence

Browser target:

```text
http://127.0.0.1:5178/cms/asset/589495534045014
```

Browser result:

```json
{
  "hasCard": true,
  "hasDecision": true,
  "hasSha": true,
  "hasCandidateJson": true,
  "hasCleanVersion": true
}
```

The page exposes the accepted raw2clean candidate, candidate SHA, candidate JSON
reference, and clean version.

## Checks

| Check | Exit |
| --- | ---: |
| `node server/tests/rawmaterial2cleanmaterial-third-sample-pilot.mjs` | 0 |
| `RAW2CLEAN_THIRD_SAMPLE_REAL_APPLY=1 node server/tests/rawmaterial2cleanmaterial-third-sample-pilot.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-candidate-view-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-candidate-decision-smoke.mjs` | 0 |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 |
| `npx pnpm@10.4.1 run build` | 0 |
| `git diff --check` | 0 |
| Browser product-surface verification | 0 |

Build emitted only the existing Vite chunk-size warning.

## Boundary Confirmation

No failed CleanService namespace was created. No fallback asset version was used.
No second CleanService POST was issued. No extra diagnostic MinIO write was
performed.

No MinIO delete/copy/move/cleanup, broad bucket listing, Docker/Compose
restart/recreate/rebuild, service mutation, job-store manual edit, source/sample
/env/secret/model mutation, batch execution, final quality acceptance, UAT, L3,
pressure PASS, release readiness, production readiness, production online, or
go-live claim was made.

## Recommendation

The third canonical sample removes the main Task 286 concern. The next mainline
step should be a bounded mini-batch pilot, with a hard cap such as 3 additional
samples, per-sample stop-on-first-failure, no automatic namespace recovery, no
cleanup, and no readiness/go-live wording.
