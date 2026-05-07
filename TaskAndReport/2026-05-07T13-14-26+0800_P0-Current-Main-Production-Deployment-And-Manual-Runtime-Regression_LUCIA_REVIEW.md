# Lucia Review

Task ID: `TASK-20260507-125133-P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression`

Task name: P0 Current Main Production Deployment And Manual Runtime Regression

Review time: `2026-05-07T13:14:26+0800`

Reviewer: Lucia

Result: `ACCEPTED_READY_WITH_KNOWN_LIMITATIONS`

## Reviewed Inputs

- Task brief: `TaskAndReport/2026-05-07T12-51-33+0800_P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression_TASK.md`
- Lucode report: `TaskAndReport/2026-05-07T13-03-21+0800_P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression_REPORT.md`
- Lucode supplemental report: `TaskAndReport/2026-05-07T13-11-08+0800_P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression_SUPPLEMENTAL_REPORT.md`
- Deployed production HEAD: `a4fcb05a95d59847b6218cb7a8d2f590097fb4e0`

## Accepted Deployment Facts

- Production workspace was fast-forwarded to current GitHub `main`.
- Runtime is reachable at `http://localhost:8081/cms/`.
- Docker services were reported healthy after rebuild.
- Dependency health is non-blocking with MinIO, MinerU health, MinerU submit probe, and Ollama passing.
- Tier 2 Standard and UAT smoke passed against `http://localhost:8081`.
- Controlled sample upload reached `review-pending` with MinerU, MinIO artifact, Ollama, and AI metadata evidence.
- Strict no-skeleton behavior remains preserved; the observed AI result used provider `ollama`, not skeleton.

## Lucia Read-Only Recheck

- `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`: PASS; `blocking=false`, `mineru.submitProbe.ok=true`, `ollama.ok=true`.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status`: PASS; supervisor reachable, sidecar session present, Ollama service reachable.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task`: PASS; no active or queued task at review time.
- `curl -fsS http://localhost:8081/__proxy/db/tasks/task-1778130398304`: PASS; task is `review-pending`, MinerU completed, parsed files recorded, AI metadata recorded.
- `curl -fsS http://localhost:8081/__proxy/db/ai-metadata-jobs/ai-job-1778130435700-d611`: PASS; job is `review-pending`, provider `ollama`, deterministic repair succeeded.

## Known Limitations

- MinerU live log display remains unreliable in the current production runtime. Host logs contain business progress, but task-level live observation can still show low-signal or stale observation during manual review.
- Completed-window attribution can reject a valid observation when log timestamps are second-granularity and `mineruStartedAt` includes sub-second precision.
- UI/diagnostic wording can describe `schema_invalid -> deterministic repair succeeded -> review-pending` too broadly as AI recognition being blocked, even when Ollama returned a usable draft and final provider is `ollama`.
- Ops status can show missing Ollama/MinerU tmux sessions while the actual services are reachable; this should be shown as an ops-session warning, not a dependency failure.

## Decision

The deployment task is accepted as `READY_WITH_KNOWN_LIMITATIONS` and closed.

Follow-up tasks are issued:

- `TASK-20260507-131426-P0-MinerU-Log-Observation-Transport-And-Attribution-Robustness`
- `TASK-20260507-131426-P1-AI-Deterministic-Repair-UI-And-Ops-Status-Semantics`

This review does not claim production release readiness, staging readiness, L3 readiness, large-PDF soak readiness, security readiness, or full-site acceptance.
