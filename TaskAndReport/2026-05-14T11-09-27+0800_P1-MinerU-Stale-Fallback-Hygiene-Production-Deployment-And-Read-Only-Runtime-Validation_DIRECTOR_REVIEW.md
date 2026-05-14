# Director Review: P1 MinerU Stale Fallback Hygiene Production Deployment And Read-Only Runtime Validation

- Task ID: `TASK-20260514-104322-P1-MinerU-Stale-Fallback-Hygiene-Production-Deployment-And-Read-Only-Runtime-Validation`
- Review time: 2026-05-14T11:09:27+0800
- Reviewed report: `TaskAndReport/2026-05-14T10-43-22+0800_P1-MinerU-Stale-Fallback-Hygiene-Production-Deployment-And-Read-Only-Runtime-Validation_REPORT.md`
- Result: `ACCEPTED_SCOPED_DEPLOYMENT_AND_STALE_FALLBACK_HYGIENE_RUNTIME_PASS`

## Decision

Accepted.

The DevelopmentEngineer followed the scoped production boundary:

- production was already at `416a963`;
- preflight showed no active/current/queued/drift/takeover parse work;
- admission circuit was closed;
- dependency-health was non-blocking;
- dirty production files were recorded and did not include Task 117 deployment-critical paths;
- `docker compose up -d --build upload-server` completed successfully;
- only `luceon-sidecar` was restarted/re-attached;
- no PDF upload, MinerU restart/kill/ownership normalization, Ollama mutation, supervisor attach, cleanup, repair/reparse/re-AI, log deletion/truncation, sample/config/secret/model mutation, or readiness claim was performed.

## Evidence Accepted

Director spot-check matched the report:

- `/ops/mineru/global-observation` now returns `activityLevel=log-observation-empty` with reason `configured log file exists but is empty; workspace scratch fallback ignored as non-authoritative diagnostic`;
- stale scratch `uat/scratch/mineru-api.log` is present only under `ignoredDiagnosticLogSource` and is not promoted as current `Predict 99%` progress;
- `/ops/mineru/log-channel-ownership` reports configured logs empty/readable and sidecar `observed-recent`;
- `/ops/mineru/active-task` is clean except historical AI failures;
- `/ops/mineru/admission-circuit` is closed/open=false;
- production HEAD is `416a963`;
- `luceon-sidecar` is present in tmux.

## Boundary

This closes the stale fallback pollution defect at the deployed runtime-surface level.

It does not restore true live MinerU business-progress logs. Configured MinerU stdout/stderr logs remain empty because the active MinerU process is still not owned by the production `luceon-mineru` wrapper.

No production readiness, L3, pressure PASS, release-readiness, go-live readiness, or production上线 is claimed.

## Next Step

Record a User decision row for controlled MinerU ownership normalization.

Director recommendation: approve a separate scoped DevelopmentEngineer task that, only after strict preflight, stops/replaces the current unmanaged MinerU listener and starts `luceon-mineru` through `ops/start-mineru-api.sh`, then performs read-only health/log-channel verification. Do not combine that process mutation with upload validation; if ownership normalization succeeds, a later one-upload validation can prove live business-progress observability.
