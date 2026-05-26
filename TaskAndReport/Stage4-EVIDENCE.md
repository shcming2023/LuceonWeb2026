# Stage 4 Evidence - Fault Injection And Self-Healing

Collected at: `2026-05-26T15:32:27+0800`

Scope: script truthfulness fix and no-mutation ledger entry. No Docker kill, MinerU stop, service restart, upload, submit-probe, DB write, MinIO write, or destructive fault injection was performed.

## Gate Semantics Fixed

- `uat/release-gate.sh --with-fault --non-interactive` now blocks instead of treating endpoint reachability as a fault-injection pass.
- `uat/release-gate.sh --with-fault` now routes admission testing to `fault-injection-admission.sh --mode mineru-down`, matching the checklist.
- `uat/fault-injection-worker-crash.sh` now fails if the candidate task reaches terminal state before crash injection, instead of skipping as success.
- `uat/fault-injection-worker-crash.sh` now fails if no accepted recovery event is observed.
- `uat/fault-injection-admission.sh --mode mineru-down` now fails if PDF or Markdown samples are missing, instead of treating missing samples as harmless skips.

## Validation

- Shell syntax check passed for release gate and fault-injection scripts.
- `git diff --check` passed.

## Status

- Stage 4 fake-pass prevention: `PASS`
- Real fault injection evidence: `PENDING_EXPLICIT_DESTRUCTIVE_AUTHORIZATION`

## Authorization Required

Real Stage 4 still requires explicit authorization for:

- stopping MinerU or otherwise inducing the `mineru-down` condition;
- `docker kill` / service restart for worker crash recovery;
- any upload task needed to observe recovery events.
