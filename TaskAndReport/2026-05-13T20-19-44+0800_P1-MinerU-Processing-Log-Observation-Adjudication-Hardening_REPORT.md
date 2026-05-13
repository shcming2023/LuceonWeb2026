# DevelopmentEngineer Report: P1 MinerU Processing Log Observation Adjudication Hardening

- Report time: 2026-05-13T20:31:21+0800
- Role: DevelopmentEngineer
- Based on Director task brief: `TaskAndReport/2026-05-13T20-19-44+0800_P1-MinerU-Processing-Log-Observation-Adjudication-Hardening_TASK.md`
- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- HEAD: `0671827`
- Production actions: none
- GitHub sync/push: not performed

## Files Changed

- `server/services/mineru/local-adapter.mjs`
- `server/tests/mineru-log-observation-adjudication-smoke.mjs`
- `server/tests/mineru-timeout-adjudication-smoke.mjs`

Note: this workspace already contained many unrelated modified/untracked files before this task. They were not reverted or included in this implementation scope.

## Implementation Summary

- Removed the terminal early-fail path that threw a generic `Error` when MinerU API was still `processing` but host log observation was stale/unreadable.
- Added `buildNonTerminalMineruLogObservationWarning()` in the local MinerU adapter.
- `queued` / `pending` / `processing` / `running` MinerU API states plus unreadable/stale/no-business log observation now produce diagnostic warning metadata:
  - `metadata.mineruLogObservationWarning.kind = mineru-log-observation-diagnostic-only`
  - task remains `running`
  - `mineruObservedProgress` remains available for operator visibility
- Applied the same adjudication in both normal local MinerU processing and resume/takeover paths.
- Preserved explicit failure semantics:
  - MinerU API `failed` / `error` still throws terminal failure evidence.
  - confirmed failure log signals are not downgraded into diagnostic-only warnings.
  - timeout/result-fetch handling remains unchanged.
- Added a focused smoke test proving:
  - `processing + log-observation-unreadable/stale` completes without terminal failure and records warning metadata.
  - explicit MinerU API failure still fails with preserved error detail.

## Commands Run And Exit Codes

- `git status --short --branch` -> 0
- `node server/tests/mineru-log-observation-adjudication-smoke.mjs` -> 0
- `git diff --check` -> 0
- `node --check server/services/mineru/local-adapter.mjs && node --check server/tests/mineru-timeout-adjudication-smoke.mjs && node --check server/tests/mineru-log-observation-adjudication-smoke.mjs` -> 0
- `node server/tests/mineru-timeout-adjudication-smoke.mjs` -> 0
- `node server/tests/mineru-log-progress-smoke.mjs` -> 0
- `node server/tests/mineru-diagnostics-smoke.mjs` -> 0
- `node server/tests/ops-mineru-active-task-classification-smoke.mjs` -> 0
- `node server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs` -> 0
- `node server/tests/dependency-health-smoke.mjs` -> 0
- `npx pnpm@10.4.1 exec tsc --noEmit` -> 0
- `npx pnpm@10.4.1 run build` -> 0

## Skipped Checks And Reasons

- No production deployment or runtime upload validation was run. The task brief assigned code/test hardening only and explicitly excluded production deployment, upload, pressure/batch/soak, cleanup, destructive mutation, model operation, restart/rebuild, L3, production readiness, release readiness, and go-live claims.
- No GitHub push was performed. DevelopmentEngineer role instructions prohibit push unless Director/task explicitly authorizes it.

## Evidence

- Focused smoke result: `Results: 6 passed, 0 failed`.
- Timeout adjudication smoke result: `Results: 59 passed, 0 failed`.
- MinerU log progress smoke result: `Results: 144 passed, 0 failed`.
- Dependency health smoke result: `Results: 65 passed, 0 failed`.
- Build completed with Vite output and only the existing chunk-size warning.

## Risks / Blockers / Residual Debt

- This is code/test-level evidence only. Production runtime still needs Director-dispatched deployment and controlled validation before any runtime acceptance.
- The fix preserves warning metadata, but final operator-facing clarity should still be validated in the task page after deployment.
- Existing unrelated dirty workspace files remain outside this task scope and may affect later review if not separated by Director.

## Review Need

- Director review required: yes.
- Suggested next actor: Director.
- Suggested next decision: accept this code/test-level hardening or dispatch a scoped production deployment/runtime validation task.
- Need follow-up production validation or user decision: production validation required before broader validation/release decisions.
