# Director Review: P0 MinerU Runtime Loss And Pressure State Read-Only Diagnosis

- Task ID: `TASK-20260515-192928-P0-MinerU-Runtime-Loss-And-Pressure-State-Read-Only-Diagnosis`
- Review time: 2026-05-15T19:40:38+0800
- Reviewed by: `Director`
- Report reviewed: `TaskAndReport/2026-05-15T19-29-28+0800_P0-MinerU-Runtime-Loss-And-Pressure-State-Read-Only-Diagnosis_REPORT.md`
- Result: `ACCEPTED_DIAGNOSIS_USER_DECISION_REQUIRED_FOR_MUTATING_RECOVERY`

## Judgment

I accept the DevelopmentEngineer read-only diagnosis.

The report gives sufficient current-state evidence to decide the next recovery boundary:

- MinerU is not reachable on the expected `8083` port.
- No visible `tmux` MinerU session is active.
- `com.office.mineru` LaunchAgent exists but is `not running`.
- Production docs and host launcher disagree on ownership naming: repo docs expect `luceon-mineru`, while host script starts `mineru_api`.
- The 24 pressure tasks have drifted from the TestAcceptanceEngineer final snapshot into a more explicitly failed/blocked state.

## Director Spot-Check

I performed additional read-only spot-checks:

- `dependency-health?mineruSubmitProbe=false` still reports MinerU `connect ECONNREFUSED`, `blocking=true`;
- no visible listener exists on TCP `8083`;
- `launchctl print gui/501/com.office.mineru` still reports `state = not running`;
- no `tmux` session was visible;
- current pressure-run counts are now:
  - `review-pending`: 5
  - `failed`: 17
  - `pending`: 2
  - state/stage split: 16 `failed/submit-failed-retryable`, 1 `failed/mineru-processing`, 2 `pending/upload`, 5 `review-pending/review`.

This confirms the blocker is still active and the queue state continues to evolve while MinerU is unavailable.

## Accepted Boundaries

Accepted:

- MinerU runtime loss diagnosis.
- Ownership mismatch diagnosis.
- Pressure-state drift evidence.
- Need for a scoped mutating recovery decision before any relaunch, submit-probe, retry/reparse/re-AI, or task-state reconciliation.

Not accepted or not claimed:

- pressure PASS;
- L3;
- release readiness;
- production readiness;
- go-live;
- authorization to restart/relaunch MinerU;
- authorization to retry/reparse/re-AI/cancel/repair/reset tasks;
- authorization to clean DB/MinIO/Docker data.

## Next Action

I am recording Task 185 as a User decision row. My recommended path is Option A: approve only a scoped MinerU runtime relaunch to a single canonical owner plus read-only verification. Defer submit-probe and task-state reconciliation until after the runtime owner is restored and observed.
