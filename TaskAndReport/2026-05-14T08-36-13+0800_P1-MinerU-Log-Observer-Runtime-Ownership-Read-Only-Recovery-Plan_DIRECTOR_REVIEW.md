# Director Review: P1 MinerU Log Observer Runtime Ownership Read-Only Recovery Plan

- Reviewed at: 2026-05-14T08:36:13+0800
- Task ID: `TASK-20260514-081241-P1-MinerU-Log-Observer-Runtime-Ownership-Read-Only-Recovery-Plan`
- Review result: `ACCEPTED_READ_ONLY_PLAN_USER_DECISION_REQUIRED`

## Accepted Evidence

Architect completed the assigned read-only plan and stayed within the task boundary.

Accepted facts:

- production remains healthy at the service level;
- `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` are healthy;
- no active/current/queued MinerU task is present;
- admission circuit is closed;
- `/ops/mineru/log-channel-ownership` remains `summaryState=empty`;
- configured MinerU stdout/stderr log files exist and are readable but empty;
- `mineru-log-observer` / `luceon-sidecar` is not observed;
- no tmux server is running for `luceon-mineru`, `luceon-sidecar`, or `luceon-supervisor`;
- MinerU is healthy on `*:8083` but appears unmanaged by the intended `luceon-mineru` session;
- Ollama is healthy for Luceon but still has the dual-listener ownership risk.

Director independently spot-checked the core claims with read-only production commands:

- `/ops/mineru/log-channel-ownership`;
- `/ops/mineru/active-task`;
- `/ops/mineru/admission-circuit`;
- `docker compose ps`;
- `lsof` listener inspection;
- `tmux ls`;
- `/ops/dependency-repair/status` returning HTTP 503.

## Review Judgment

The Architect recommendation is accepted:

1. recover the MinerU log observer first, because it is the smallest runtime mutation that can make progress observability measurable;
2. do not normalize MinerU API ownership in the same step while the current MinerU process is healthy and idle;
3. do not mutate Ollama in this step; keep dual-listener cleanup as a separate ownership decision;
4. treat `luceon-supervisor` as optional and separate unless explicitly authorized.

This review does not authorize runtime mutation by itself.

## Next Step

Record a User decision for whether to authorize a scoped DevelopmentEngineer task that only attaches `luceon-sidecar` with strict preflight and post-checks.

No upload, pressure/batch/soak validation, Docker mutation, service restart, MinerU/Ollama mutation, cleanup, repair/reparse/re-AI, destructive data operation, L3, production readiness, release readiness, go-live readiness, or production上线 is accepted or authorized by this review.
