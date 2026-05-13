# Director Review: P1 MinerU Progress Observability Ownership Review

- Review time: 2026-05-14T06:07:35+0800
- Role: Director
- Reviewed task: `TaskAndReport/2026-05-14T05-42-35+0800_P1-MinerU-Progress-Observability-Ownership-Review_TASK.md`
- Reviewed report: `TaskAndReport/2026-05-14T05-42-35+0800_P1-MinerU-Progress-Observability-Ownership-Review_REPORT.md`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Production HEAD observed: `159d80e Accept MinerU log observation hardening`
- Result: `ACCEPTED_ANALYSIS_OBSERVABILITY_OWNERSHIP_GAP_CONFIRMED`

## Decision

Task 106 is accepted.

Architect stayed within the read-only boundary and correctly separated two concerns:

- false-failure adjudication: Task 101/104 already improved this path for the controlled sample;
- progress-rich observability: still not proven, because the expected MinerU business-progress log channel is not live/attributable.

The key conclusion is accepted: the residual diagnostic-only behavior is primarily a sidecar/log-source ownership gap, with a secondary small/fast-PDF timing factor. It should not be treated as a UI-only problem, and it should not be papered over by fabricated progress.

## Evidence Reviewed

Architect reported:

- lifecycle truth currently comes from MinerU API and Luceon task/material state;
- rich business progress is expected to come from structured MinerU log observation persisted as `metadata.mineruObservedProgress`;
- production host log files `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log` existed but were 0 bytes;
- the upload-server container saw the mounted MinerU log files as 0 bytes as well;
- `/ops/mineru/global-observation` returned null;
- no `mineru-log-observer` sidecar process was running;
- MinerU itself was running as a conda `mineru-api --port 8083 --host 0.0.0.0` process;
- current UI behavior is honest diagnostic behavior, but not sufficient as a broader validation boundary.

Director spot-checks during review confirmed:

- host MinerU log files are still 0 bytes;
- `/ops/mineru/global-observation` still returns `{"observation":null}`;
- active-task has no current work and only historical AI failures;
- admission circuit is closed/open=false.

## Accepted Boundary

Accepted:

- read-only architecture analysis;
- signal map from MinerU runtime/source to task UI;
- classification of current limitation as sidecar/log-source ownership gap;
- recommendation to dispatch a scoped DevelopmentEngineer diagnostics/ownership task before broader validation.

Not accepted or not evidenced:

- production readiness, release readiness, L3, pressure PASS, or production上线;
- any upload, pressure, restart, rebuild, cleanup, repair, or data mutation;
- a claim that progress-rich observability is fixed.

## Next Step

Director issued Task 107 to DevelopmentEngineer.

Task 107 is scoped to code/test/docs/runbook-level ownership diagnostics. It does not authorize production restart/rebuild, upload validation, pressure testing, destructive operations, sample mutation, model/config/secret changes, or readiness claims.
