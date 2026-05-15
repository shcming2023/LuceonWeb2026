# Director Review: P0 MinerU Only Runtime Relaunch And Read-Only Verification

- Review time: 2026-05-15T20:21:23+0800
- Reviewed task: `TASK-20260515-201231-P0-MinerU-Only-Runtime-Relaunch-And-Read-Only-Verification`
- Reviewed report: `TaskAndReport/2026-05-15T20-12-31+0800_P0-MinerU-Only-Runtime-Relaunch-And-Read-Only-Verification_REPORT.md`
- Reviewer: Director
- Result: `ACCEPTED_MINERU_RUNTIME_RESTORED_SUBMIT_PATH_AND_PRESSURE_RECONCILIATION_PENDING_USER_DECISION`

## Evidence Reviewed

The DevelopmentEngineer report confirms the task followed Task 185 Option A: one canonical MinerU relaunch plus read-only verification.

Reported authorized runtime action:

```bash
tmux new-session -d -s luceon-mineru "cd '/Users/concm/prod_workspace/Luceon2026' && bash ops/start-mineru-api.sh"
```

Reported post-relaunch evidence:

- `luceon-mineru` tmux session present;
- `python3.1` listening on TCP `8083`;
- direct MinerU `/health` returned healthy;
- dependency-health with `mineruSubmitProbe=false` returned `ok=true`, `blocking=false`;
- admission circuit remained closed;
- no manual submit-probe, upload, retry/reparse/re-AI, repair, DB/MinIO cleanup, Docker cleanup, or broad restart was run.

Director live spot-check confirmed:

- `luceon-mineru: 1 windows`;
- `python3.1 ... TCP *:8083 (LISTEN)`;
- direct MinerU `/health` healthy with zero queued/processing/completed/failed tasks in the restored in-memory runtime;
- dependency-health no-submit `ok=true`, `blocking=false`;
- admission circuit closed;
- active-task diagnostics show no active/queued/takeover-required task and 18 `submitRetryableTasks`;
- current pressure task distribution: 5 `review-pending/review`, 18 `failed/submit-failed-retryable`, 1 `failed/mineru-processing`.

Director also observed that `/ops/mineru/log-channel-ownership` has aged to `summaryState=stale` and `sidecar.runningState=not-observed` after the relaunch logs became idle. This does not invalidate MinerU process restoration, but it means durable log-observer ownership remains a residual operational gap.

## Judgment

Accepted for scoped MinerU runtime restoration and read-only verification.

This review does not accept the pressure run as PASS. It does not verify submit-path readiness because Task 187 explicitly forbade submit-probe. It does not authorize failed-task reconciliation, retry, reparse, re-AI, repair, cleanup, reset, or another pressure run.

## Residual Risks

- Submit path is still not freshly verified after the relaunch because submit-probe was not authorized.
- The 24-PDF pressure state remains mixed: 5 review-pending and 19 failed.
- The one `failed/mineru-processing` task appears to have lost its MinerU in-memory task record after runtime loss/relaunch.
- Long-term ownership mismatch remains: the canonical tmux session is restored, but the host LaunchAgent path and service-owner contract are still not fully normalized.
- Log-channel observability is not a stable always-on signal after idle; sidecar was not observed in the live spot-check.

## Next Action

Director recorded a user decision row:

- `TASK-20260515-202123-P0-MinerU-Submit-Probe-And-Pressure-State-Reconciliation-Decision`

Director recommendation is Option A: authorize exactly one submit-probe-only validation first, without failed-task reconciliation. Pressure-task reconciliation should remain a separate decision after submit-path evidence is known.

