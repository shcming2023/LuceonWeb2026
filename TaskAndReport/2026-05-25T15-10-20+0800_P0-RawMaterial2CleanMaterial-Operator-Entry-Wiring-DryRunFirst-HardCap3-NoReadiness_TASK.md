# P0 RawMaterial2CleanMaterial Operator Entry Wiring DryRunFirst HardCap3 NoReadiness

Issued at: 2026-05-25T15:10:20+0800

Task ID: TASK-20260525-151020-P0-RawMaterial2CleanMaterial-Operator-Entry-Wiring-DryRunFirst-HardCap3-NoReadiness

## Mainline Objective

Convert the accepted Task 290 operator-runner boundary into a minimal operator
entry that can be invoked deliberately with a manifest, dry-run by default,
hard cap 3, stop-on-first-failure behavior, and run-level evidence.

This task is the bridge from harness-only proof to controlled operator use. It
does not authorize live DB/MinIO/CleanService writes.

## Critical Path Scope

- Add a minimal CLI entry for RawMaterial2CleanMaterial operator runs.
- Accept a manifest file containing up to three material/task samples.
- Default to `dry-run`.
- Require explicit confirmation for `real` mode.
- Preserve hard cap `<= 3`.
- Emit per-sample evidence and a run-level evidence surface.
- Keep the processor mock-safe/fixture-backed for this task.

## True Preconditions

- Reuse the existing accepted runner in
  `server/services/rawmaterial2cleanmaterial/operator-runner.mjs`.
- Do not bypass runner validation.
- Do not wire live DB, MinIO, CleanService, Docker, scheduler, worker, or
  background queue dependencies.

## Deferrable Side Work

- Live processor wiring.
- Controlled real single-batch execution.
- Operator UI/dashboard.
- Retry, repair, reject, queue, scheduler, auto-scan, or large-batch behavior.
- Production deployment/readiness validation.

## Fast Validation Target

Run the CLI against a fixture manifest and prove:

- dry-run is the default;
- three samples complete through the operator entry;
- operation counts remain zero for DB/MinIO/CleanService writes;
- run-level evidence includes run id, operator id, manifest SHA, sample summary,
  operation counts, and `readinessClaimed=false`;
- hard cap overflow and unconfirmed real mode are blocked.

## Stop Rule

Stop and report blocked instead of widening scope if:

- live processor wiring is required to make the CLI useful;
- validation requires DB/MinIO/CleanService writes;
- UI/product workflow work becomes necessary;
- hard cap, confirmation, or readiness boundaries cannot be preserved.

## Review Boundary

Acceptance means the operator entry exists and is mock-safe/dry-run verified.
It does not mean a live real-mode run, production readiness, UAT, L3, pressure
PASS, release readiness, or go-live.
