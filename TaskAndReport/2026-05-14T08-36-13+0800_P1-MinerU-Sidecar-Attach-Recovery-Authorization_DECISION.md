# User Decision: P1 MinerU Sidecar Attach Recovery Authorization

- Recorded at: 2026-05-14T08:36:13+0800
- Role: Director
- Decision ID: `TASK-20260514-083613-P1-MinerU-Sidecar-Attach-Recovery-Authorization`
- Trigger: Director accepted Architect Task 111 read-only recovery plan.
- Next Actor: User

## Current Facts

Task 111 established a narrow recovery route:

- production services are healthy;
- no active/current/queued MinerU work is present;
- admission circuit is closed;
- MinerU API is healthy but unmanaged by the intended `luceon-mineru` tmux session;
- `luceon-sidecar` / `mineru-log-observer` is absent;
- `luceon-supervisor` is absent and dependency-repair status returns HTTP 503;
- `/ops/mineru/log-channel-ownership` is live and reports `summaryState=empty`, configured log files readable but empty, sidecar `not-observed`;
- Ollama is healthy for Luceon but still has a dual-listener ownership risk.

Director accepted Architect's recommendation to recover observability in layers: attach `luceon-sidecar` first, keep MinerU ownership normalization and Ollama dual-listener cleanup as separate decisions.

## Decision Needed

Decide whether to authorize a scoped runtime recovery task for DevelopmentEngineer to attach only the MinerU log observer sidecar.

## Option A: Authorize Scoped `luceon-sidecar` Attach Only (Director Recommended)

Authorize DevelopmentEngineer to run a tightly bounded task:

1. Run read-only preflight:
   - active-task clean;
   - admission circuit closed;
   - dependency-health with MinerU submit probe non-blocking;
   - Docker services healthy;
   - direct MinerU health healthy;
   - sidecar absent or clearly diagnosed;
   - Ollama dependency-health healthy despite dual-listener risk.
2. If preflight passes, start only `luceon-sidecar` with the repository-backed command:

```bash
tmux new-session -d -s luceon-sidecar "cd '/Users/concm/prod_workspace/Luceon2026' && UPLOAD_SERVER_URL=http://127.0.0.1:8081/__proxy/upload MINERU_LOG_SOURCE_CONTEXT=host-filesystem MINERU_ERR_LOG_PATH=/Users/concm/ops/logs/mineru-api.err.log MINERU_LOG_PATH=/Users/concm/ops/logs/mineru-api.log node ops/mineru-log-observer.mjs"
```

3. Run read-only post-checks:
   - `tmux ls`;
   - `/ops/mineru/log-channel-ownership`;
   - `/ops/mineru/global-observation`;
   - `bash ops/runtime-ownership-status.sh`;
   - active-task/admission/dependency surfaces.

Success boundary:

- `luceon-sidecar` is present and reporting;
- endpoint moves away from `not-observed`, or a fresh global observation is present;
- if logs remain empty because no MinerU parse is running, report that as sidecar-attached-but-idle, not as full business-progress proof.

## Option B: Authorize Sidecar Plus Supervisor Attach

Authorize sidecar attach and `luceon-supervisor` attach in one task.

Not recommended yet. This adds one more runtime process and may blur the evidence chain. Supervisor recovery can follow after sidecar attach is proven.

## Option C: Hold

Do not mutate runtime yet.

Risk: future validation remains harder to interpret because the log observer is still absent and progress semantics stay diagnostic-only.

## Director Recommendation

Choose Option A.

If this decision remains unanswered for two consecutive Director heartbeat/check-task cycles, Director may auto-issue only the scoped Option A DevelopmentEngineer task if preflight remains clean. Automatic progression must not authorize supervisor attach, MinerU restart/ownership normalization, Ollama mutation, upload, pressure testing, destructive operations, L3, production readiness, release readiness, go-live readiness, or production上线.

## Heartbeat Wait Evidence

- `2026-05-14T08:54:50+0800`: first Director heartbeat/check-task after Task 112 was recorded. No user decision was present. Director recommendation remains Option A: attach only `luceon-sidecar` with strict preflight/post-checks. No auto-progress was triggered because this is wait count 1 of 2.
