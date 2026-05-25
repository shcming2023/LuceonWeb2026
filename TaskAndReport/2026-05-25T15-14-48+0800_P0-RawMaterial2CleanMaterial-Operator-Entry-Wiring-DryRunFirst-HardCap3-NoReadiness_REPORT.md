# P0 RawMaterial2CleanMaterial Operator Entry Wiring DryRunFirst HardCap3 NoReadiness Report

Reported at: 2026-05-25T15:14:48+0800

Task ID: TASK-20260525-151020-P0-RawMaterial2CleanMaterial-Operator-Entry-Wiring-DryRunFirst-HardCap3-NoReadiness

Result: `SUCCESS_OPERATOR_ENTRY_DRYRUN_WIRING`

## Summary

Implemented a minimal CLI operator entry for the existing
RawMaterial2CleanMaterial operator runner.

The entry is intentionally narrow:

- manifest input is required;
- dry-run is the default;
- hard cap cannot be raised above 3;
- real mode requires `--confirm-real`;
- default processor is fixture-backed;
- authorized `task288-live` processor is available for the subsequent
  controlled real-run task;
- output includes run-level evidence and per-sample evidence;
- `readinessClaimed=false` is preserved.

## Changed Files

- `scripts/raw2clean-operator-runner.mjs`
- `server/tests/fixtures/raw2clean-operator-manifest.json`
- `server/tests/fixtures/raw2clean-operator-task288-live-manifest.json`
- `server/tests/rawmaterial2cleanmaterial-operator-entry-smoke.mjs`
- `server/tests/rawmaterial2cleanmaterial-bounded-mini-batch-pilot.mjs`
- `TaskAndReport/2026-05-25T15-10-20+0800_P0-RawMaterial2CleanMaterial-Operator-Entry-Wiring-DryRunFirst-HardCap3-NoReadiness_TASK.md`
- `TaskAndReport/2026-05-25T15-14-48+0800_P0-RawMaterial2CleanMaterial-Operator-Entry-Wiring-DryRunFirst-HardCap3-NoReadiness_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Operator Entry Behavior

Command shape:

```bash
node scripts/raw2clean-operator-runner.mjs \
  --manifest server/tests/fixtures/raw2clean-operator-manifest.json \
  --operator-id local-operator \
  --out /tmp/raw2clean-operator-entry-evidence.json
```

Observed dry-run summary:

```json
{
  "ok": true,
  "mode": "dry-run",
  "realRunExecuted": false,
  "completed": 3,
  "counts": {
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

The written evidence file includes:

- `runId`;
- `operatorId`;
- requested mode;
- hard cap;
- manifest path and SHA256;
- sample order/material/task summary;
- per-sample raw seed, CleanService, candidate, DB patch, product surface, and
  operation-count fields;
- `liveSideEffectsEnabled=false`;
- `readinessClaimed=false`.

After Director authorization in the same turn, the entry was extended with an
explicit `--processor task288-live` path for the controlled real-run task. The
default remains fixture/dry-run, and unsupported processors are blocked.

## Checks

| Check | Exit |
| --- | ---: |
| `node --check scripts/raw2clean-operator-runner.mjs` | 0 |
| `node --check server/tests/rawmaterial2cleanmaterial-operator-entry-smoke.mjs` | 0 |
| `node --check server/services/rawmaterial2cleanmaterial/operator-runner.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-operator-entry-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-operator-runner-smoke.mjs` | 0 |
| `node server/tests/rawmaterial2cleanmaterial-bounded-mini-batch-pilot.mjs` | 0 |
| `npx tsc --noEmit` | 0 |
| `npm run build` | 0 |
| `git diff --check` | 0 |

Note: plain `tsc --noEmit` is not available as a global command in this shell
(`zsh:1: command not found: tsc`), so the project-local `npx tsc --noEmit`
check was used and passed.

## Explicitly Not Done

- No live real-mode run.
- No DB write.
- No MinIO write/list/delete/copy/move/cleanup.
- No CleanService POST.
- No Docker/Compose mutation.
- No scheduler, daemon, worker, auto-scan, queue, retry, repair, reject, or
  broad batch behavior.
- No final quality acceptance.
- No readiness, UAT, L3, pressure PASS, release-readiness, production-readiness,
  go-live, or deployment claim.

## Next Mainline Task

Proceed to a separately authorized controlled real runner invocation only after
reviewing this operator entry.

Recommended next task:

`P0 RawMaterial2CleanMaterial Controlled Real Runner Invocation SingleBatch HardCap3 StopOnFirstFailure`

Boundary for the next task:

- use this operator entry path, not the older harness;
- dry-run must pass first;
- max three samples;
- stop on first failure;
- at most one CleanService POST per sample;
- no extra diagnostic MinIO writes;
- no readiness/go-live claim.
