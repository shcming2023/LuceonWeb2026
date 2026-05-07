# Lucia Task Brief

Task ID: `TASK-20260507-142907-P1-Completed-Task-Observation-And-Ops-Session-Semantics`

Task name: P1 Completed Task Observation And Ops Session Semantics

Issued at: `2026-05-07T14:29:07+0800`

Issuer: Lucia

Assignee: Lucode

Priority: P1

## Background

Task `TASK-20260507-133917-P0-Deploy-Followup-Fixes-And-Manual-Validation` is accepted as manual-review ready, but Lucia review identified two residual observability issues that should be corrected before the next broader validation pass.

Evidence from production validation:

- Runtime health is green with `mineru.submitProbe.ok=true` and `ollama.ok=true`.
- Controlled sample `task-1778133327274` reached `review-pending`; MinerU completed; AI deterministic repair succeeded through Ollama.
- `dependency-repair/status` reports `sessions.mineru=false` even though MinerU is reachable and submit probing passes, because the live MinerU tmux session is named outside the expected `luceon-mineru` convention.
- Lucia read-only verification found that the completed controlled sample can still show post-completion `mineruObservedProgress` changes with `attributionMode=completed-window-backfill` and `activityLevel=active-progress` after the task has reached terminal `review-pending`.

## Objective

Tighten production observability semantics without changing the external upload, parse, artifact, or AI metadata business flow.

Required outcomes:

1. Completed local-MinerU tasks must not keep receiving misleading post-completion observation mutations from later host MinerU log activity.
2. Completed-task observation fields must remain useful for diagnostics, but wording and state must not imply the task is still processing after terminal completion.
3. Dependency repair/session status must distinguish service reachability from tmux session ownership and must not report a healthy MinerU service as a service outage.

## Non-Goals

- Do not change the core upload -> MinerU -> MinIO -> AI metadata chain.
- Do not weaken fail-fast behavior or strict no-skeleton AI semantics.
- Do not broaden this into supervisor redesign, full ops automation, or Docker/volume cleanup.
- Do not delete, reset, truncate, migrate, or repair production DB, MinIO, Docker volumes, historical tasks, or generated artifacts.
- Do not rename live production tmux sessions destructively unless the task first proves no active work can be affected; prefer code/status semantics over runtime disruption.

## Required Work

1. Inspect the completed-window backfill path and determine why terminal tasks can receive later observation changes.
2. Implement a narrow fix so terminal tasks preserve the most relevant final observation or mark later observations as non-mutating diagnostics.
3. Ensure stale or post-completion observation wording is accurate for terminal tasks and does not say or imply that MinerU API is still processing a completed task.
4. Inspect dependency repair/session status semantics for MinerU and Ollama.
5. Update status output so:
   - `mineruReachable=true` and submit-probe success remain separate from tmux session ownership.
   - Missing `luceon-mineru` session is reported as an ops-session ownership warning, not as a dependency outage.
   - Existing `mineru_api` / `mineru_gradio` sessions can be surfaced as observed unmanaged sessions when detectable.
6. Add or update focused smoke tests for both completed-task observation semantics and ops-session status semantics.
7. Preserve existing accepted tests from Tasks 11-13.

## Required Checks

Run and report exit codes for:

```bash
git status --short --branch
git fetch origin
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
node server/tests/mineru-log-observation-transport-smoke.mjs
node server/tests/mineru-sidecar-completed-window-smoke.mjs
node server/tests/mineru-log-progress-smoke.mjs
node server/tests/mineru-log-source-live-smoke.mjs
node server/tests/dependency-supervisor-smoke.mjs
BASE_URL=http://localhost:8081 bash uat/smoke-test.sh
```

If a new focused test is added, include it in the command list and report its result.

## Production Safety

- Code changes should be developed on a branch from current `origin/main`.
- Do not mutate production runtime while implementing the branch.
- If runtime validation is needed, request a follow-up deployment validation task instead of restarting production services inside this implementation task.

## Required Report

Store the completion report in `TaskAndReport/` and update `TaskAndReport/TASK_TRACKING_LIST.md`.

The report must include:

- Branch name and HEAD.
- Files changed.
- Implementation summary.
- Exact test commands and exit codes.
- Before/after semantics for completed-task observation.
- Before/after semantics for MinerU and Ollama ops-session status.
- Explicit confirmation that no destructive production operation was performed.

## Acceptance Criteria

- Terminal ParseTasks are protected from misleading post-completion observation mutation.
- Completed-task stale/progress wording is accurate and source-aware.
- Dependency repair/status output separates reachability from tmux ownership.
- Existing accepted runtime and smoke semantics remain green.
