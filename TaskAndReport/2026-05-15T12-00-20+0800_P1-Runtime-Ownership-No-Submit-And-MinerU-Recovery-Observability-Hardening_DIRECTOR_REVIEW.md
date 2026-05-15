# Director Review: P1 Runtime Ownership No-Submit And MinerU Recovery Observability Hardening

- Task ID: `TASK-20260515-114704-P1-Runtime-Ownership-No-Submit-And-MinerU-Recovery-Observability-Hardening`
- Reviewed report: `TaskAndReport/2026-05-15T11-47-04+0800_P1-Runtime-Ownership-No-Submit-And-MinerU-Recovery-Observability-Hardening_REPORT.md`
- Review time: 2026-05-15T12:00:20+0800
- Reviewer: `Director`
- Result: `ACCEPTED_CODE_DOCS_LEVEL_PRODUCTION_SYNC_DECISION_REQUIRED`

## Judgment

Accepted at code/docs level.

DevelopmentEngineer implemented the requested no-submit default for `ops/runtime-ownership-status.sh` and clarified the distinction between read-only health/status checks and side-effecting MinerU submit-path verification. The implementation stays inside the task boundary: no live submit-probe, no upload, no production deployment, no service restart, and no readiness claim.

This review does not claim production deployment. The production workspace may still have the older helper until a scoped production source sync is explicitly authorized.

## Evidence Reviewed

Changed files:

- `ops/runtime-ownership-status.sh`
- `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`
- `docs/codex/TEST_MATRIX.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-15T11-47-04+0800_P1-Runtime-Ownership-No-Submit-And-MinerU-Recovery-Observability-Hardening_REPORT.md`

Confirmed behavior from source review:

- default helper calls `GET /ops/dependency-health` without `mineruSubmitProbe=true`;
- side-effecting submit-probe is gated behind `RUN_MINERU_SUBMIT_PROBE=1` or `--submit-probe`;
- default output includes `MinerU submit probe skipped`;
- submit-probe output is labeled as side-effecting and warns that it creates a synthetic MinerU task and may update admission circuit.

Director reran:

- `bash -n ops/runtime-ownership-status.sh` -> passed;
- `git diff --check` -> passed;
- `bash ops/runtime-ownership-status.sh /Users/concm/prod_workspace/Luceon2026 | rg -n "dependency health without MinerU submit probe|MinerU submit probe skipped|RUN_MINERU_SUBMIT_PROBE=0|SIDE EFFECT|mineruSubmitProbe=true"` -> passed and matched only the read-only/no-submit default lines:
  - `dependency health without MinerU submit probe (read-only)`;
  - `MinerU submit probe skipped`;
  - `RUN_MINERU_SUBMIT_PROBE=0; no synthetic MinerU task was created by this helper`.

Director did not run `--submit-probe` or `RUN_MINERU_SUBMIT_PROBE=1`.

## Residual Boundary

This code/docs hardening is useful immediately in the development workspace and GitHub main after integration. However, future runtime operators may still run the production workspace copy of `ops/runtime-ownership-status.sh`. Because this task did not authorize production source sync or deployment, the next decision is whether to apply the accepted helper/docs change to the production workspace with no service restart and no submit-probe.

## Next Step

Record a User decision row:

- recommended Option A: scoped production workspace source sync for the accepted no-submit helper/docs only, with no Docker Compose, no rebuild, no restart, no upload, no submit-probe, and verification limited to `bash -n`, `--help`, and default helper output showing submit-probe skipped;
- hold if the user wants to keep production workspace untouched for now.

No production readiness, L3, pressure PASS, release-readiness, or go-live claim is made by this review.
