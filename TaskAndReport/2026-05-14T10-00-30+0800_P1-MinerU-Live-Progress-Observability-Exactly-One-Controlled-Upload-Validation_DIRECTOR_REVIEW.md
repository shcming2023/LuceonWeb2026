# Director Review: P1 MinerU Live Progress Observability Exactly One Controlled Upload Validation

- Task ID: `TASK-20260514-093805-P1-MinerU-Live-Progress-Observability-Exactly-One-Controlled-Upload-Validation`
- Review time: 2026-05-14T10:00:30+0800
- Reviewed report: `TaskAndReport/2026-05-14T09-38-05+0800_P1-MinerU-Live-Progress-Observability-Exactly-One-Controlled-Upload-Validation_REPORT.md`
- Result: `ACCEPTED_ONE_UPLOAD_PASS_WITH_LIVE_PROGRESS_OBSERVABILITY_GAP_CONFIRMED`

## Decision

Accepted at the exact one-upload validation boundary.

The TestAcceptanceEngineer followed the authorized scope: preflight first, exactly one small/medium PDF upload from `/Users/concm/prod_workspace/Luceon2026/testpdf`, observation until terminal state, no second upload, no pressure, no cleanup, no repair/reparse/re-AI, no MinerU/Ollama/supervisor mutation, and no readiness claim.

The main runtime path passed for this one sample:

- task `task-1778723642905` reached `review-pending`;
- material `task115-live-progress-1778723642` reached `reviewing`;
- MinerU task `7a6f3b04-0bf3-493c-96d8-6eed86250331` completed;
- parsed artifacts were produced with `parsedFilesCount=21`;
- AI job `ai-job-1778723655852-cdb7` reached `review-pending`;
- browser list/detail semantics were understandable and did not show a false terminal failure.

## Observability Finding

The live MinerU progress observability target remains unresolved.

Accepted evidence shows:

- `/ops/mineru/log-channel-ownership` stayed `summaryState=empty`;
- `luceon-sidecar` stayed `observed-recent`;
- configured stdout/stderr logs remained empty/readable;
- `/ops/mineru/global-observation` continued to use stale fallback content from `uat/scratch/mineru-api.log`;
- the final material diagnostic was `fast-complete-no-business-signal`;
- the task page correctly communicated that MinerU completed but no attributable business-progress log was captured.

This means the current issue is no longer "sidecar not running." The sharper diagnosis is: Luceon now has a live observer process, but the actual MinerU process/log-writer path is not feeding the configured log channel.

## Director Spot Check

Director rechecked read-only production surfaces after the report:

- `/ops/mineru/log-channel-ownership`: `summaryState=empty`, configured logs empty, sidecar `observed-recent`;
- `/ops/mineru/global-observation`: stale fallback `uat/scratch/mineru-api.log`, stale/unattributed;
- `/ops/mineru/active-task`: no active/current/queued/drift/takeover tasks;
- `/ops/mineru/admission-circuit`: closed/open=false;
- production HEAD: `a516546`.

The production workspace also showed additional local modified source files during Director spot-check. These were not part of this validation acceptance and must not be overwritten or normalized silently. Any future restart/rebuild/deploy task must explicitly account for the dirty production worktree.

## Boundary

No production readiness, L3, pressure PASS, release-readiness, go-live readiness, or production上线 is claimed.

## Next Step

Do not run another upload yet.

Issue a read-only Architect task to produce a remediation route for MinerU log-source ownership and stale fallback handling. The next plan must distinguish:

- code-only stale fallback exclusion or semantics hardening;
- sidecar/log-path retargeting;
- controlled MinerU process ownership normalization so MinerU writes to the configured log files;
- supervisor integration as a later or separate concern;
- the dirty production worktree risk before any rebuild/restart.

No runtime mutation is authorized by this review.
