# DevelopmentEngineer Report: P1 Runtime Ownership No-Submit And MinerU Recovery Observability Hardening

- Task ID: `TASK-20260515-114704-P1-Runtime-Ownership-No-Submit-And-MinerU-Recovery-Observability-Hardening`
- Based on Director task brief: `TaskAndReport/2026-05-15T11-47-04+0800_P1-Runtime-Ownership-No-Submit-And-MinerU-Recovery-Observability-Hardening_TASK.md`
- Based on Director review: `TaskAndReport/2026-05-15T11-47-04+0800_P1-MinerU-Only-Recovery-And-Submit-Path-Verification_DIRECTOR_REVIEW.md`
- Based on prior blocker evidence: `TaskAndReport/2026-05-15T11-12-51+0800_P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack_DIRECTOR_REVIEW.md`
- Report time: 2026-05-15T11:56:00+0800
- Role: `DevelopmentEngineer`
- Branch / HEAD: `main` / `212474b`

## Summary

Implemented scoped runtime-ownership hardening so `ops/runtime-ownership-status.sh` is read-only/no-submit by default.

The MinerU submit-probe now requires explicit opt-in through either:

```bash
RUN_MINERU_SUBMIT_PROBE=1 bash ops/runtime-ownership-status.sh
bash ops/runtime-ownership-status.sh --submit-probe
```

Default helper execution now calls dependency health without `mineruSubmitProbe=true`, prints a `MinerU submit probe skipped` section, and states that no synthetic MinerU task was created by the helper.

## Files Changed

- `ops/runtime-ownership-status.sh`
- `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`
- `docs/codex/TEST_MATRIX.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-15T11-47-04+0800_P1-Runtime-Ownership-No-Submit-And-MinerU-Recovery-Observability-Hardening_REPORT.md`

## Implementation Details

`ops/runtime-ownership-status.sh`:

- Added argument parsing for:
  - `--submit-probe`
  - `--no-submit-probe`
  - `--help` / `-h`
- Added `RUN_MINERU_SUBMIT_PROBE`, defaulting to `0`.
- Changed default dependency health call to:
  - `$UPLOAD_BASE/ops/dependency-health`
- Moved the side-effecting call:
  - `$UPLOAD_BASE/ops/dependency-health?mineruSubmitProbe=true`
  behind explicit opt-in.
- Added clear output labels:
  - `dependency health without MinerU submit probe (read-only)`
  - `MinerU submit probe skipped`
  - `MinerU submit probe (SIDE EFFECT: creates synthetic MinerU task and may update admission circuit)`

Documentation:

- `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md` now separates read-only status checks from side-effecting submit-path verification.
- It documents that submit-probe creates a bounded synthetic MinerU task and may open or close the durable admission circuit.
- It documents both opt-in command forms for the helper.
- `docs/codex/TEST_MATRIX.md` now lists dependency-health without submit-probe as the read-only production-line check and labels dependency-health with submit-probe as side-effecting and explicitly authorization-bound.

## Commands Run And Exit Codes

- `git status --short --branch` -> exit 0.
- `rg -n "\\| [0-9]+ \\| .*\\| (下达待执行|执行中|退回待修正|修正中) \\| DevelopmentEngineer \\|" TaskAndReport/TASK_TRACKING_LIST.md` -> exit 0.
- `sed`/`rg` required-reading and source-inspection commands for task brief, role docs, related reports/reviews, helper, and docs -> exit 0.
- `bash -n ops/runtime-ownership-status.sh` -> exit 0.
- `git diff --check` -> exit 0.
- `bash ops/runtime-ownership-status.sh /Users/concm/prod_workspace/Luceon2026 | rg -n "dependency health without MinerU submit probe|MinerU submit probe skipped|RUN_MINERU_SUBMIT_PROBE=0|SIDE EFFECT|mineruSubmitProbe=true"` -> exit 0.
  - Observed lines:
    - `== dependency health without MinerU submit probe (read-only) ==`
    - `== MinerU submit probe skipped ==`
    - `RUN_MINERU_SUBMIT_PROBE=0; no synthetic MinerU task was created by this helper.`

## Skipped Checks And Reasons

- Did not run `RUN_MINERU_SUBMIT_PROBE=1 bash ops/runtime-ownership-status.sh`: submit-probe is side-effecting and not authorized for validation in this task.
- Did not run `bash ops/runtime-ownership-status.sh --submit-probe`: same reason.
- Did not run any live `dependency-health?mineruSubmitProbe=true`: explicitly forbidden by task boundary.
- Did not run TypeScript, build, or `node --check`: no TypeScript or `.mjs` files changed.
- Did not add tests: task scope was a shell helper plus docs hardening, and `bash -n`, `git diff --check`, and default-helper output verification covered the changed behavior.

## Evidence

Default helper output verification found the new no-submit labels and did not match `mineruSubmitProbe=true` or the side-effect warning label.

The default helper therefore no longer performs the side-effecting synthetic MinerU submit-probe path during normal status collection.

## Risks / Blockers / Residual Debt

- The helper's explicit submit-probe mode still intentionally creates a synthetic MinerU task and may update the admission circuit. This is by design and remains authorization-bound.
- This task did not change upload-server API behavior or admission-circuit semantics.
- This task did not deploy changes to production.
- Existing historical docs outside the allowed scope may still mention old validation patterns; this task updated the active runtime ownership and test-matrix guidance only.

## Forbidden Operations Confirmation

No forbidden operation was performed.

Specifically, I did not run live submit-probe, upload files, create validation artifacts, deploy, pull/fast-forward production, rollback, rebuild, mutate Docker/DB/MinIO/Ollama/supervisor/sidecar state, cleanup/cancel/repair/retry/reparse/re-AI/takeover/requeue tasks, mutate settings/secrets/config/models/samples, change PRD truth/role contract/project state/handoff, weaken skeleton fallback, or claim pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Director Review Needed

Yes.

Director should review and decide whether to accept this hardening before future read-only runtime evidence tasks use `ops/runtime-ownership-status.sh` as a safe default helper.
