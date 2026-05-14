# Director Review: P1 MinerU Ownership Normalization Scoped Runtime Recovery

- Review time: 2026-05-14T11:34:11+0800
- Reviewed task: `TASK-20260514-111219-P1-MinerU-Ownership-Normalization-Scoped-Runtime-Recovery`
- Reviewed report: `TaskAndReport/2026-05-14T11-12-19+0800_P1-MinerU-Ownership-Normalization-Scoped-Runtime-Recovery_REPORT.md`
- Reviewer: Director
- Result: `ACCEPTED_SCOPED_PROCESS_OWNERSHIP_NORMALIZATION_UPLOAD_VALIDATION_DECISION_REQUIRED`

## Scope Judgment

Accepted at scoped runtime-recovery level.

DevelopmentEngineer stayed within the authorized process-ownership scope: one verified unmanaged MinerU listener on port `8083` was gracefully terminated, `luceon-mineru` was started through `ops/start-mineru-api.sh`, and no PDF upload, pressure validation, DB/MinIO mutation, Docker down/volume cleanup, Ollama mutation, supervisor attach, repair/reparse/re-AI, readiness, L3, pressure PASS, or go-live claim was made.

This acceptance does not establish production readiness or end-to-end user-upload validation. It only accepts the MinerU process/log ownership normalization.

## Evidence Accepted

DevelopmentEngineer reported:

- production HEAD `b98735c`;
- old sole 8083 listener PID `72358`, running from the development workspace with stdout/stderr as pipes;
- no `luceon-mineru` tmux session before the mutation;
- one graceful `kill 72358`;
- new `luceon-mineru` tmux session started with `ops/start-mineru-api.sh`;
- new sole 8083 listener PID `61436`;
- PID `61436` cwd `/Users/concm/prod_workspace/Luceon2026`;
- PID `61436` stdout/stderr attached to `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log`;
- direct MinerU health, upload health, dependency health, admission, and log-channel checks passed;
- `luceon-sidecar` remained present.

Director spot-check at review time confirmed:

- `tmux ls` shows `luceon-mineru` and `luceon-sidecar`;
- port `8083` has one listener, PID `61436`;
- `lsof -a -p 61436 -d cwd,1,2` shows cwd in the production workspace and fd1/fd2 attached to the configured ops log files;
- direct MinerU `/health` is healthy with `queued_tasks=0` and `processing_tasks=0`;
- upload health is OK;
- canonical admission route `/__proxy/upload/ops/mineru/admission-circuit` is closed;
- canonical active-task route `/__proxy/upload/ops/mineru/active-task` has no active task/current processing/queued/takeover work, with only historical AI failures listed;
- dependency-health via `/__proxy/upload/ops/dependency-health` is `ok=true`, `blocking=false`, Ollama `qwen3.5:9b` resident, and `keepAlive.value=24h`;
- configured log files are non-empty and recently written by the new process.

## Evidence Corrections

Two command-path details in the report need a Director correction for future use:

- `/__proxy/upload/mineru/admission-circuit` returned 404 during Director spot-check.
- `/__proxy/db/tasks/active-task` returned 404 during Director spot-check.

The canonical routes are:

- `/__proxy/upload/ops/mineru/admission-circuit`
- `/__proxy/upload/ops/mineru/active-task`

This route correction does not invalidate the task outcome, because Director independently verified the canonical routes and the core process/log ownership evidence.

## Residual Boundary

The log channel is now connected to the configured ops files, but at review time `/ops/mineru/log-channel-ownership` reported `summaryState=stale` and `/ops/mineru/global-observation` reported `log-observation-stale`. This is expected after the short synthetic/health-probe activity becomes idle. It means the system has log ownership evidence, not a fresh user-upload progress proof.

Therefore the next project decision is whether to authorize exactly one controlled real upload from `/Users/concm/prod_workspace/Luceon2026/testpdf` to validate that the newly normalized MinerU log channel produces useful page/progress semantics during a real task.

## Not Accepted

This review does not accept or authorize:

- production readiness;
- release readiness;
- L3;
- pressure PASS;
- pressure, batch, soak, or long-run validation;
- second or repeated upload;
- failed-task repair, reparse, re-AI, cleanup, or historical task mutation;
- destructive DB/MinIO/Docker volume/data operation;
- Ollama mutation;
- supervisor attach;
- model/config/secret/sample mutation;
- go-live or production上线 claim.

## Next Step

Task 120 is closed as accepted. Director records Task 121 as a User decision: whether to authorize exactly one controlled small/medium PDF upload by TestAcceptanceEngineer to validate live MinerU progress semantics after ownership normalization.
