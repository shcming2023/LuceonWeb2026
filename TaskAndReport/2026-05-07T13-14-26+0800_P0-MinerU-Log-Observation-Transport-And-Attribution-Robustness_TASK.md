# Lucia Task Brief

Task ID: `TASK-20260507-131426-P0-MinerU-Log-Observation-Transport-And-Attribution-Robustness`

Task name: P0 MinerU Log Observation Transport And Attribution Robustness

Issued at: `2026-05-07T13:14:26+0800`

Issuer: Lucia

Assignee: Lucode

Priority: P0

## Background

Production manual review after deployment showed that MinerU parsing succeeded, but task-level live log display remained unreliable.

Observed task: `task-1778130398304`, file `向树叶学习：人工光合作用.pdf`.

Accepted facts:

- MinerU completed and produced parsed artifacts.
- Host MinerU logs contained business progress lines for the run.
- Task-level observation during manual review could show no useful business signal or stale observation.
- A later observation could be rejected or delayed because task start timestamps include sub-second precision while log timestamps are second-granularity.
- Current diagnostics also mix host-side log source, container bind mount checks, and observer-side source-of-truth, which makes the operator signal hard to interpret.

## Objective

Make MinerU task-level log observation reliable enough for manual review by fixing or redesigning the log-observation transport and by making attribution tolerant to the accepted timestamp precision boundary.

## Non-Goals

- Do not change MinerU parse semantics, MinIO storage semantics, AI metadata semantics, task terminal states, or material acceptance semantics.
- Do not repair historical failed tasks.
- Do not clean, reset, delete, truncate, or migrate production DB, MinIO buckets, Docker volumes, or user data.
- Do not claim release readiness.

## Allowed Files, Modules, Or Operations

- `ops/mineru-log-observer.mjs`
- `ops/start-luceon-runtime.sh`
- `ops/start-mineru-api.sh`
- `server/lib/ops-mineru-log-parser.mjs`
- `server/upload-server.mjs`
- Focused tests under `server/tests/`
- `docker-compose.yml` only if the accepted fix requires a compose-level log-source change
- `TaskAndReport/` report and tracking-list updates

Production validation is allowed only through non-destructive runtime checks and one controlled sample upload if preflight confirms no active task is running.

## Required Work

1. Determine and document the actual log-observation source of truth:
   - host observer path
   - upload-server/container path
   - tmux session path
   - mounted path if any
2. Fix the transport so task-level observation reads the current MinerU log inode/content during live runs.
3. Make diagnostics label the real failing boundary accurately. Do not call a host-side observer problem a Docker mount problem unless the observer actually depends on that mount.
4. Add a small, explicit attribution tolerance around `mineruStartedAt` for completed-window observations where log timestamps are second-granularity.
5. Preserve the existing safety rule: ambiguous attribution remains unattributed.
6. Add focused regression tests for:
   - live attribution still wins when exactly one live task exists
   - completed-window attribution allows a small before-start tolerance
   - observations outside tolerance remain unattributed
   - multiple candidates remain unattributed
   - stale or missing log-source diagnostics are accurate
7. Validate on production runtime with a controlled sample only after all preflight gates are green.

## Forbidden Changes

- Do not run `git reset --hard`, `git clean`, `docker compose down -v`, `docker volume rm`, MinIO cleanup, DB cleanup, or equivalent destructive commands.
- Do not overwrite `.env`, `docker-compose.override.yml`, local credentials, or machine-specific runtime overrides.
- Do not use `.skip`, assertion weakening, or broad error suppression.
- Do not configure silent degradation.
- Do not restart services if active production parse or AI work is detected; write a blocked report instead.

## Required Checks

Lucode must run and report exit codes for:

```bash
git status --short --branch
git fetch origin
git pull --ff-only origin main
node server/tests/mineru-sidecar-completed-window-smoke.mjs
node server/tests/mineru-log-progress-smoke.mjs
node server/tests/mineru-log-source-live-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
git diff --check
```

If a new focused test is added, include it in the report.

For production validation, report read-only health checks and the controlled sample evidence if executed.

## Required Evidence

- Exact diff summary and files changed.
- Explanation of the accepted log-observation source of truth.
- Before/after evidence for log-source freshness and attribution.
- Controlled sample task id, final state, MinerU status, parsed artifact fields, and task-level `mineruObservedProgress` fields if sample validation is executed.
- Confirmation that no production cleanup, DB mutation beyond controlled sample, MinIO cleanup, or Docker volume operation occurred.

## GitHub Sync Requirements

- Use branch `lucode/p0-mineru-log-observation-transport-attribution`.
- Commit and push branch if repository files are changed.
- Store completion report under `TaskAndReport/`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch, HEAD, status, next actor, next action, and required output.
- Do not merge before Lucia review.

## Acceptance Criteria

- Live and completed-window MinerU log observation produce useful, current task-level signals for a controlled sample, or a precise blocker is documented.
- Timestamp precision tolerance is implemented without allowing ambiguous attribution.
- Existing sidecar, log progress, build, and type checks pass.
- No destructive production operation is performed.
