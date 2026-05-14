# User Decision: P1 MinerU Log Observer And Runtime Ownership Recovery

- Recorded at: 2026-05-14T08:07:47+0800
- Role: Director
- Decision ID: `TASK-20260514-080747-P1-MinerU-Log-Observer-And-Runtime-Ownership-Recovery-Decision`
- Trigger: Task 109 deployed the MinerU log-channel ownership diagnostics and confirmed the production log channel is empty with sidecar not observed.
- Next Actor: User

## Current Facts

The production diagnostic endpoint is now live and reports:

- `summaryState=empty`;
- configured MinerU stdout/stderr log files exist and are readable but empty;
- fallback host log files are missing;
- `mineru-log-observer` sidecar is `not-observed`;
- lifecycle authority remains with MinerU API and Luceon task state;
- log-channel diagnostics must not fabricate progress.

The runtime ownership script also showed no `mineru_api`, `luceon-mineru`, `luceon-sidecar`, or `luceon-supervisor` tmux sessions, and showed two Ollama listeners. No runtime ownership mutation was performed.

## Decision Needed

Decide whether to authorize a scoped recovery task for MinerU log observer/runtime ownership, now that the diagnostic endpoint can verify the result.

## Options

### Option A: Scoped Read-Only Recovery Plan First (Director Recommended)

Assign Architect or DevelopmentEngineer to produce a concrete recovery plan and preflight checklist without starting, stopping, or restarting services.

The plan must identify:

- the authoritative owner for MinerU API, `mineru-log-observer`, and `luceon-supervisor`;
- exact commands that would be needed later to start or attach the sidecar;
- expected log file path and ownership contract;
- how to verify `summaryState` moves from `empty/not-observed` to an observable state;
- how to handle the observed dual Ollama listener risk without mutating Ollama in this step.

### Option B: Authorize Scoped Sidecar/Supervisor Recovery

Authorize a carefully bounded DevelopmentEngineer task to start or restore only the minimum MinerU log observer/supervisor process needed for progress observability, then verify the deployed endpoint.

Risk: this is runtime process mutation. It may be appropriate, but it needs explicit boundaries and active-task preflight.

### Option C: Hold

Do not recover the sidecar yet. Keep using lifecycle state only and avoid broader validation.

Risk: future uploads remain harder to observe because progress semantics will still lack attributable MinerU business-progress signals.

## Director Recommendation

Choose Option A first. It is the clean next step because Task 109 gave us observability of the gap, but not enough authority to mutate process ownership safely in an unattended step.

No option authorizes upload, pressure/batch/soak validation, destructive DB/MinIO/Docker volume/data mutation, model mutation, secrets changes, L3, production readiness, release readiness, go-live readiness, or production上线.

## User Approval

- `2026-05-14T08:12:41+0800`: User approved Option A: do a read-only recovery plan/preflight first, and clarify sidecar/supervisor/MinerU/Ollama ownership plus later executable commands.
- Director issued `TASK-20260514-081241-P1-MinerU-Log-Observer-Runtime-Ownership-Read-Only-Recovery-Plan`.
