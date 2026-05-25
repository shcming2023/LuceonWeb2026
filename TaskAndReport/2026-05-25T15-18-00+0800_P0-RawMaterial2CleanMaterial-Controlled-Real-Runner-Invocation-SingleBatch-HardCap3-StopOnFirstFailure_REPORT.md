# P0 RawMaterial2CleanMaterial Controlled Real Runner Invocation SingleBatch HardCap3 StopOnFirstFailure Report

Reported at: 2026-05-25T15:18:00+0800

Task ID: TASK-20260525-151800-P0-RawMaterial2CleanMaterial-Controlled-Real-Runner-Invocation-SingleBatch-HardCap3-StopOnFirstFailure

Result: `SUCCESS_OPERATOR_ENTRY_REAL_IDEMPOTENT_EXISTING_ACCEPTED_3_OF_3`

## Authorization

The Director explicitly authorized immediate controlled real small-batch
execution after the operator entry task:

> 不用等下一张了，现在就授权真实小批量执行

## Scope

The run used the new CLI operator entry, not the old direct harness:

```bash
node scripts/raw2clean-operator-runner.mjs \
  --manifest server/tests/fixtures/raw2clean-operator-task288-live-manifest.json \
  --operator-id Luceon \
  --processor task288-live \
  --mode real \
  --confirm-real \
  --out /tmp/raw2clean-operator-task288-live-real.json
```

Boundary:

- hard cap 3;
- dry-run preflight first;
- sequential stop-on-first-failure;
- at most one CleanService POST per sample;
- no extra diagnostic MinIO writes;
- no readiness/go-live claim.

## Execution Result

Run id:

```text
raw2clean-real-Luceon-20260525T071734548Z-ca01e9ca51a1
```

Summary:

```json
{
  "ok": true,
  "mode": "real",
  "realRunExecuted": true,
  "completed": 3,
  "stopped": null,
  "operationCounts": {
    "rawSeedPutObject": 0,
    "cleanServicePost": 0,
    "raw2cleanCandidatePutObject": 0,
    "dbPatch": 0,
    "minioDelete": 0,
    "runtimePostOtherThanCleanService": 0,
    "dockerOperation": 0,
    "batch": 0
  },
  "readinessClaimed": false
}
```

Preflight counts were also all zero:

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

## Per-Sample Evidence

| Material | Task | Stage | Candidate SHA | Decision | POST | Raw Put | Candidate Put | DB Patch |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `3884430250123676` | `task-1779085090064` | `real-idempotent-existing-accepted` | `56f1384f17c02df845ff3b6ad4c322b637e9c42877252cf70502cc36b740d24e` | `accepted` | 0 | 0 | 0 | 0 |
| `696446087521346` | `task-1779010154264` | `real-idempotent-existing-accepted` | `2ba9692e9987e6df21469c2eb5e3e0abb7fa23c29d786de7c687aa67803dc26f` | `accepted` | 0 | 0 | 0 | 0 |
| `3228822025029647` | `task-1779085087347` | `real-idempotent-existing-accepted` | `5dae747154d834f8a88546d6d3c5396a5ba6039842839a8c68e624d6741da2f4` | `accepted` | 0 | 0 | 0 | 0 |

The real invocation found all three selected Task 288 samples already in
accepted raw2clean state. The operator entry therefore returned
idempotent-existing-accepted success instead of creating a new CleanService
version or rewriting metadata.

## Checks

| Check | Exit |
| --- | ---: |
| `node --check server/tests/rawmaterial2cleanmaterial-bounded-mini-batch-pilot.mjs` | 0 |
| `node --check scripts/raw2clean-operator-runner.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-operator-entry-smoke.mjs` | 0 |
| `node scripts/raw2clean-operator-runner.mjs --manifest server/tests/fixtures/raw2clean-operator-task288-live-manifest.json --operator-id Luceon --processor task288-live --out /tmp/raw2clean-operator-task288-live-dryrun.json` | 0 |
| `node scripts/raw2clean-operator-runner.mjs --manifest server/tests/fixtures/raw2clean-operator-task288-live-manifest.json --operator-id Luceon --processor task288-live --mode real --confirm-real --out /tmp/raw2clean-operator-task288-live-real.json` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-bounded-mini-batch-pilot.mjs` | 0 |
| `npx tsc --noEmit` | 0 |
| `npm run build` | 0 |
| `git diff --check` | 0 |

## Execution Deviation And Interpretation

An initial real invocation stopped on sample 1 before the idempotent-existing
branch was added. The legacy single-sample processing path attempted to build a
next-version CleanService request for an already accepted sample and blocked on
version mismatch. Read-only DB checks confirmed the current task/material facts
were already `toc-rebuild v1` and raw2clean `accepted`.

The correction was intentionally narrow: in real mode, when a sample is already
accepted and the candidate ObjectRef is readable and matches metadata SHA/size,
the live processor returns `real-idempotent-existing-accepted` with zero side
effects rather than creating a new version.

## Explicitly Not Done

- No new CleanService POST was sent.
- No DB patch was applied in the successful controlled invocation.
- No MinIO object was written, listed broadly, deleted, copied, moved, or
  cleaned.
- No Docker/Compose mutation.
- No scheduler, daemon, worker, auto-scan, queue, retry, repair, reject, or
  broad batch behavior.
- No final quality acceptance.
- No readiness, UAT, L3, pressure PASS, release-readiness, production-readiness,
  go-live, or deployment claim.

## Next Mainline Reading

The operator entry can now drive a controlled real invocation safely, but this
specific run was an idempotent existing-accepted run. If the next goal is to
prove new-sample mutation through the operator entry, the next task should pick
one fresh eligible sample and run the same entry with hard cap 1 first.
