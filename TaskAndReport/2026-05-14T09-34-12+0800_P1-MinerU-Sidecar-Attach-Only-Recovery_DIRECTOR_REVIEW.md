# Director Review: P1 MinerU Sidecar Attach Only Recovery

- Task ID: `TASK-20260514-091558-P1-MinerU-Sidecar-Attach-Only-Recovery`
- Review time: 2026-05-14T09:34:12+0800
- Reviewed report: `TaskAndReport/2026-05-14T09-15-58+0800_P1-MinerU-Sidecar-Attach-Only-Recovery_REPORT.md`
- Result: `ACCEPTED_SIDECAR_ATTACHED_IDLE_BUSINESS_PROGRESS_PROOF_REQUIRED`

## Decision

Accepted at scoped recovery level.

The DevelopmentEngineer followed the Task 113 boundary: strict preflight first, then only attached `luceon-sidecar` with the exact authorized tmux command, then ran read-only post-checks. The report provides enough evidence that the sidecar transport is now present and observed by `/ops/mineru/log-channel-ownership`.

This acceptance does not mean MinerU business-progress observability is proven. It only means the sidecar attach recovery succeeded while the system was idle.

## Evidence Accepted

- Preflight reported Docker services healthy, upload health OK, dependency-health non-blocking, MinerU submit probe accepted, admission circuit closed, and active/current/queued/takeover tasks empty.
- Before attach, `/ops/mineru/log-channel-ownership` reported `summaryState=empty` and `sidecar.runningState=not-observed`.
- The authorized command started `luceon-sidecar` in tmux and exited 0.
- After attach, `tmux ls` showed `luceon-sidecar` present.
- After attach, `/ops/mineru/log-channel-ownership` reported `sidecar.runningState=observed-recent` and `runningObserved=true`.
- No upload, pressure/batch/soak, Docker mutation, DB/MinIO/Docker volume cleanup, MinerU restart, Ollama mutation, supervisor attach, config/secret/model/sample mutation, or failed-task repair/reparse/re-AI was performed.

## Boundary And Residual Risk

The important remaining gap is semantic, not transport-only:

- Configured production MinerU stdout/stderr logs remain empty.
- `/ops/mineru/global-observation` saw stale fallback log content from `uat/scratch/mineru-api.log`, marked unattributed/stale, so it must not be treated as current business-progress proof.
- MinerU still runs as an unmanaged conda process rather than an owned `luceon-mineru` session.
- `luceon-supervisor` remains absent.
- Ollama dual-listener ownership risk remains, although dependency-health was healthy during this task.

Therefore, the next validation should either prove live business-progress observability with one controlled upload, or first harden stale fallback log hygiene. The Director recommendation is to run one controlled upload now, because sidecar transport has been restored and only a real parse can answer whether live MinerU progress becomes observable.

## Next Step

Record a User decision row for a narrowly scoped TestAcceptanceEngineer validation:

- Option A, recommended: authorize exactly one controlled PDF upload from `/Users/concm/prod_workspace/Luceon2026/testpdf`, observe task page/list semantics plus MinerU observability endpoints until terminal state or clear failure, then stop.
- Option B: first dispatch a read-only/stale-log-hygiene analysis before any upload.
- Option C: hold all runtime validation and continue only code-level diagnostics.

No production readiness, L3, pressure PASS, release-readiness, or go-live claim is made.
