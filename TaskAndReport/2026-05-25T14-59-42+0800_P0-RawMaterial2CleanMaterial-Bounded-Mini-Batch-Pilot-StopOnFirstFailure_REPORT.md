# P0 RawMaterial2CleanMaterial Bounded Mini Batch Pilot StopOnFirstFailure Report

Task ID: `TASK-20260525-144319-P0-RawMaterial2CleanMaterial-Bounded-Mini-Batch-Pilot-StopOnFirstFailure`

Report time: 2026-05-25T14:59:42+0800

Status: `SUCCESS_BOUNDED_MINI_BATCH_PILOT_3_OF_3`

Implementation branch: `codex/TASK-20260525-144319-mini-batch-pilot`

## Summary

The bounded mini-batch pilot processed exactly three samples sequentially and
completed all three under stop-on-first-failure rules.

Each sample reached:

```text
parsed ZIP -> raw seed -> CleanMaterial artifacts -> accepted CleanMaterial ->
raw2clean candidate -> durable candidate artifact -> accepted raw2clean decision
```

No sample required a shape fix, fallback namespace, second POST, or diagnostic
MinIO write.

This is evidence for bounded mini-batch feasibility. It is not broad batch
readiness, final quality acceptance, UAT, L3, pressure PASS, release readiness,
production readiness, production online, or go-live.

## Changed Files

- `server/tests/rawmaterial2cleanmaterial-bounded-mini-batch-pilot.mjs`

## Dry-Run Preflight

Command:

```bash
node server/tests/rawmaterial2cleanmaterial-bounded-mini-batch-pilot.mjs
```

Exit code: `0`

Dry-run totals:

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

## Real Apply

Command:

```bash
RAW2CLEAN_MINI_BATCH_REAL_APPLY=1 node server/tests/rawmaterial2cleanmaterial-bounded-mini-batch-pilot.mjs
```

Exit code: `0`

Real operation totals:

```json
{
  "rawSeedPutObject": 3,
  "cleanServicePost": 3,
  "raw2cleanCandidatePutObject": 3,
  "dbPatch": 6,
  "minioDelete": 0,
  "runtimePostOtherThanCleanService": 0,
  "dockerOperation": 0,
  "batch": 0
}
```

## Per-Sample Evidence

| Order | Material | Task | CleanService Job | Sections | Blocks | Candidate SHA256 |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 1 | `3884430250123676` | `task-1779085090064` | `luceon-task-1779085090064-toc-rebuild-v1` | 19 | 14 | `56f1384f17c02df845ff3b6ad4c322b637e9c42877252cf70502cc36b740d24e` |
| 2 | `696446087521346` | `task-1779010154264` | `luceon-task-1779010154264-toc-rebuild-v1` | 103 | 94 | `2ba9692e9987e6df21469c2eb5e3e0abb7fa23c29d786de7c687aa67803dc26f` |
| 3 | `3228822025029647` | `task-1779085087347` | `luceon-task-1779085087347-toc-rebuild-v1` | 79 | 0 | `5dae747154d834f8a88546d6d3c5396a5ba6039842839a8c68e624d6741da2f4` |

Candidate objects:

- `eduassets-clean/raw-material-2-clean-material/3884430250123676/v1/candidate.json`
- `eduassets-clean/raw-material-2-clean-material/696446087521346/v1/candidate.json`
- `eduassets-clean/raw-material-2-clean-material/3228822025029647/v1/candidate.json`

Raw seed SHA checks:

| Material | Raw seed object | SHA256 | Size |
| --- | --- | --- | ---: |
| `3884430250123676` | `mineru/3884430250123676/v1/content_list_v2.json` | `c5604562bf9e27383e922b42e8a547dbb7d8f6ac24a30a7354d9a27a428b737f` | 29392 |
| `696446087521346` | `mineru/696446087521346/v1/content_list_v2.json` | `14e1ac847c487c9960a1d5be07c89e73f87ba3354722a427b8c7579a7c6132a9` | 65276 |
| `3228822025029647` | `mineru/3228822025029647/v1/content_list_v2.json` | `6516df5be0a7d3bbfa8593a73075491800cb40f897e62b980c0354e5c6f1c8ad` | 39538 |

## Product Surface Evidence

Local browser verification checked all three asset pages:

- `/cms/asset/3884430250123676`
- `/cms/asset/696446087521346`
- `/cms/asset/3228822025029647`

Each page showed:

- Raw2Clean Candidate card;
- `Decision: accepted`;
- the expected candidate SHA;
- `candidate.json`;
- clean version `v1`.

The first browser assertion failed because it required a literal `Raw Material`
label, while the product surface correctly uses `Raw2Clean Candidate`. A follow-up
inspection confirmed all three pages expose the expected raw2clean candidate
evidence.

## Checks

| Check | Exit |
| --- | ---: |
| `node --check server/tests/rawmaterial2cleanmaterial-bounded-mini-batch-pilot.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-bounded-mini-batch-pilot.mjs` | 0 |
| `RAW2CLEAN_MINI_BATCH_REAL_APPLY=1 node server/tests/rawmaterial2cleanmaterial-bounded-mini-batch-pilot.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-algorithm-skeleton-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-artifact-backed-draft-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-candidate-view-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-candidate-decision-smoke.mjs` | 0 |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 |
| `npx pnpm@10.4.1 run build` | 0 |
| `git diff --check` | 0 |
| Browser product-surface inspection | 0 |

Build emitted only the existing Vite chunk-size warning.

## Boundary Confirmation

The pilot processed exactly the three authorized samples and stopped only after
all three succeeded.

No failed CleanService namespace was created. No fallback asset version was used.
No second CleanService POST was issued for any sample. No extra diagnostic MinIO
write was performed.

No MinIO delete/copy/move/cleanup, broad bucket scan, Docker/Compose
restart/recreate/rebuild, service mutation, job-store manual edit, source/sample
/env/secret/model mutation, pressure test, broad batch, final quality
acceptance, UAT, L3, pressure PASS, release readiness, production readiness,
production online, or go-live claim was made.

## Residual Debt

- One mini-batch sample produced zero raw2clean blocks, consistent with prior
  source-reference boundary behavior. This is acceptable for the pilot but
  should be visible in later quality review.
- The harness is still a bounded pilot script, not a durable batch service or
  operator workflow.
- Cleanup of prior Task 285 residual objects/jobs remains deferred.
- Final quality acceptance remains separate from durable candidate acceptance.

## Recommendation

The next mainline step should be a narrow bounded-batch product/control decision:
either authorize a slightly larger cap with the same stop-on-first-failure gates,
or start converting the proven harness into a minimal operator-triggered batch
runner with hard caps and explicit no-readiness wording.

