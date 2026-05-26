# Stage 4 Evidence - Fault Injection And Self-Healing

Collected at: `2026-05-26T15:32:27+0800`

Scope: script truthfulness fix and no-mutation ledger entry. No Docker kill, MinerU stop, service restart, upload, submit-probe, DB write, MinIO write, or destructive fault injection was performed.

Full-UAT supplement collected at: `2026-05-26T16:18:00+0800` after user authorization for real fault injection and submit-probe.

## Gate Semantics Fixed

- `uat/release-gate.sh --with-fault --non-interactive` now blocks instead of treating endpoint reachability as a fault-injection pass.
- `uat/release-gate.sh --with-fault` now routes admission testing to `fault-injection-admission.sh --mode mineru-down`, matching the checklist.
- `uat/fault-injection-worker-crash.sh` now fails if the candidate task reaches terminal state before crash injection, instead of skipping as success.
- `uat/fault-injection-worker-crash.sh` now fails if no accepted recovery event is observed.
- `uat/fault-injection-admission.sh --mode mineru-down` now fails if PDF or Markdown samples are missing, instead of treating missing samples as harmless skips.

## Validation

- Shell syntax check passed for release gate and fault-injection scripts.
- `git diff --check` passed.
- Real fault gate command passed with fixture directories:
  - `TEST_PDF_DIR=/tmp/luceon-uat-fault/pdf`
  - `TEST_MD_DIR=/tmp/luceon-uat-fault/md`
  - `BASE_URL=http://127.0.0.1:8081 bash uat/release-gate.sh --with-fault`
- Worker crash case used task `task-1779782412432`; after `docker kill cms-upload-server` and restart, recovery event `parse-restart-mineru-resumed` was observed and the task reached `review-pending`.
- MinerU-down admission case returned PDF `503` with `MINERU_ADMISSION_CIRCUIT_OPEN`, while Markdown bypass succeeded with task `task-1779782921754`.
- Recovery submit-probe passed three consecutive checks after MinerU restart.

## UAT Findings And Corrections

- MinerU `/health` was initially healthy while `/tasks` returned 500; restarting the host MinerU API restored submit-path behavior.
- `uat/release-gate.sh` ignored `TEST_PDF_DIR` and `TEST_MD_DIR`; it now respects those overrides.
- Upload dependency gating incorrectly blocked Markdown when MinerU was down; `server/upload-server.mjs` now gates Markdown on MinIO but not MinerU submit admission.

## Status

- Stage 4 fake-pass prevention: `PASS`
- Real fault injection evidence: `PASS`

## Authorization Required

Stage 4 was performed under explicit UAT authorization. This is fault-injection evidence only, not readiness or go-live approval.
