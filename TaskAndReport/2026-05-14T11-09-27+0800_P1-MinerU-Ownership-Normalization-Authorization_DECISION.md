# User Decision Required: P1 MinerU Ownership Normalization Authorization

- Task ID: `TASK-20260514-110927-P1-MinerU-Ownership-Normalization-Authorization`
- Decision created: 2026-05-14T11:09:27+0800
- Created by: Director
- Current Next Actor: `User`
- Based on accepted review: `TaskAndReport/2026-05-14T11-09-27+0800_P1-MinerU-Stale-Fallback-Hygiene-Production-Deployment-And-Read-Only-Runtime-Validation_DIRECTOR_REVIEW.md`

## Current Facts

The project has now separated two issues:

- Stale fallback pollution is fixed in production: old `uat/scratch/mineru-api.log` progress no longer appears as current MinerU progress.
- True live business-progress observability is still absent: configured logs `/Users/concm/ops/logs/mineru-api.log` and `.err.log` are still empty.

The reason is process ownership:

- Current MinerU is a healthy unmanaged conda process listening on port `8083`.
- It was not launched by the production `luceon-mineru` wrapper.
- Its stdout/stderr are not being appended to `/Users/concm/ops/logs/mineru-api*.log`.
- `ops/start-mineru-api.sh` exists and is designed to launch MinerU while appending stdout/stderr to those configured log files.

## Why A User Decision Is Needed

Normalizing MinerU ownership is a runtime process mutation. It likely requires stopping or replacing the current healthy MinerU listener on `8083`, then launching a `luceon-mineru` tmux session through `ops/start-mineru-api.sh`.

That can improve observability, but it is not a purely read-only or code-only action. It must be explicitly authorized by the user.

## Options

### Option A: Recommended

Authorize a scoped DevelopmentEngineer task:

- run strict preflight first;
- stop immediately if active parse/AI work exists, admission circuit is open, dependency-health is blocking, Docker services are unhealthy, production status is ambiguous, or current MinerU cannot be safely identified;
- record current MinerU PID/command/listener;
- stop or replace only the current unmanaged MinerU process that owns port `8083`;
- start `luceon-mineru` with:

```bash
tmux new-session -d -s luceon-mineru "cd '/Users/concm/prod_workspace/Luceon2026' && bash ops/start-mineru-api.sh"
```

- ensure `luceon-sidecar` remains present or is re-attached only if needed;
- verify direct MinerU `/health`, dependency-health, admission circuit, active-task, log-channel ownership, configured log file freshness/size, and sidecar state;
- do not upload PDFs in this normalization task.

Not authorized under Option A:

- PDF upload;
- pressure, batch, soak, or long-run validation;
- Docker down/down-v/volume/data cleanup;
- DB/MinIO mutation;
- Ollama mutation;
- supervisor attach;
- model pull/delete/replace;
- sample/config/secret mutation;
- repair/reparse/re-AI or historical task/material mutation;
- L3, production-readiness, release-readiness, go-live readiness, or production上线 claim.

If Option A succeeds, a later separate one-upload validation can test whether live MinerU business progress is finally observable.

### Option B

Do not mutate MinerU ownership yet. Continue operating with truthful diagnostic-only semantics:

- main upload path can still complete;
- stale fallback no longer pollutes current progress;
- operator will still see that no attributable MinerU business-progress log was captured.

Risk: the original live-progress observability objective remains unresolved.

### Option C

Request another read-only recovery plan before any process mutation.

Risk: safer but likely redundant, because Task 111 and Task 116 already identified the process ownership gap.

## Director Recommendation

Choose Option A.

Reason: code hygiene is now deployed and validated, so the remaining blocker is the runtime owner of MinerU's stdout/stderr. The next safest step is not another upload; it is a tightly scoped ownership normalization with no upload and no data mutation. This keeps the change small enough to reverse operationally while finally aligning MinerU with the configured log channel.

No autonomous approval is granted by this decision row. If the heartbeat auto-progress rule is later invoked, it must still obey the standing restrictions and may not claim readiness or run destructive data operations.

## User Decision Recorded

- Decision recorded: 2026-05-14T11:12:19+0800
- User decision: `APPROVED_OPTION_A`
- Director action: issue a scoped DevelopmentEngineer task for controlled MinerU ownership normalization.

The approved scope is limited to strict preflight, recording the current MinerU listener, replacing only the verified unmanaged MinerU listener on port `8083` with `luceon-mineru` launched via `ops/start-mineru-api.sh`, keeping or re-attaching `luceon-sidecar` only if needed, and running health/log-channel validation.

This decision still does not authorize PDF upload, pressure/batch/soak validation, Docker down/down-v/volume/data cleanup, DB/MinIO mutation, Ollama mutation, supervisor attach, model pull/delete/replace, sample/config/secret mutation, repair/reparse/re-AI, L3, production-readiness, release-readiness, go-live readiness, or production上线 claim.
