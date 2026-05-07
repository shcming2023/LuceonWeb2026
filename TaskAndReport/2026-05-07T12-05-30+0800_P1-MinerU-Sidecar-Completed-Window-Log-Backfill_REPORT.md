# Lucode Task Report

Task ID: `TASK-20260507-105616-P1-MinerU-Sidecar-Completed-Window-Log-Backfill`

Task brief: `TaskAndReport/2026-05-07T10-56-16+0800_P1-MinerU-Sidecar-Completed-Window-Log-Backfill_TASK.md`

Assignee: Lucode

Branch: `lucode/p0-ai-repair-and-mineru-backfill`

Implementation commit: `ca639e82487b58dc7853f51690fd0eeb06d19ba5`

Status: Development and focused testing completed; ready for Lucia review. Not merged to `main`.

## Files Changed

- `server/upload-server.mjs`
- `server/tests/mineru-sidecar-completed-window-smoke.mjs`

## Implementation Summary

- Preserved the existing exact-one live active task attribution path as `attributionMode=live-active`.
- Added safe completed-window backfill selection when there are zero live MinerU tasks and exactly one recently completed local-MinerU task matches the observation window.
- Completed-window candidates require local MinerU engine, non-canceled task, `mineruTaskId`, `mineruStartedAt`, completion time from `parsedAt` / `metadata.parsedAt` / `mineruLastStatusAt`, current time within five-minute completion grace, and observation time between start and completion plus grace.
- Ambiguous cases remain unattributed: zero candidates, multiple completed candidates, multiple live tasks, missing observation time, before-start observations, after-grace observations, and canceled tasks.
- The observer writes only task metadata observation fields and global observation; it does not change ParseTask state/stage, Material rows, MinIO objects, DB task terminal state, or MinerU runtime.

## Evidence

- Passing completed-window mock:
  - `node server/tests/mineru-sidecar-completed-window-smoke.mjs`
  - Evidence line: `Case 2 Pass: exactly one recently completed task can receive backfill`
  - Asserted result `mode=completed-window-backfill` and selected the single matching task.
- Ambiguous / unsafe mock cases:
  - Same command.
  - Evidence lines:
    - `Case 3 Pass: multiple completed candidates remain unattributed`
    - `Case 4 Pass: observations before task start remain unattributed`
    - `Case 5 Pass: observations after grace window remain unattributed`
    - `Case 7 Pass: canceled tasks are excluded`
- Existing live attribution preserved:
  - Same command.
  - Evidence line: `Case 1 Pass: exactly one live active task remains preferred`

## Commands Run

- `git status --short --branch` -> exit `0`; branch `lucode/p0-ai-repair-and-mineru-backfill`, modified source files before commit.
- `node --check server/upload-server.mjs` -> exit `0`.
- `node --check server/tests/mineru-sidecar-completed-window-smoke.mjs` -> exit `0`.
- `node server/tests/mineru-sidecar-completed-window-smoke.mjs` -> exit `0`.
- `node server/tests/mineru-sidecar-smoke.mjs` -> exit `0`; final line `All Sidecar tests passed`.
- `node server/tests/mineru-log-source-live-smoke.mjs` -> exit `0`; final line `MinerU Log Source Live Smoke Test (Patch 16.2.6) Passed`.
- `node server/tests/mineru-log-progress-smoke.mjs` -> exit `1`; existing Test 4 expects `failed-confirmed`, but current parser returns `log-error-signal`. This file/imports `server/lib/ops-mineru-log-parser.mjs`, which is outside the allowed files for this task, so Lucode did not repair it under this brief.
- `npx pnpm@10.4.1 exec tsc --noEmit` -> exit `0`.
- `npx pnpm@10.4.1 run build` -> exit `0`; Vite build succeeded with existing chunk-size warning.
- `git diff --check` -> exit `0`.

## Skipped Checks

- No live task mutation or production/runtime validation was run. The task brief requested a safe attribution patch and explicitly forbids state-changing production/data operations; focused mock evidence is provided instead.

## Risks / Residuals

- Existing `server/tests/mineru-log-progress-smoke.mjs` has a failing historical expectation around `failed-confirmed` vs `log-error-signal`. This appears outside the completed-window backfill scope and needs Lucia triage before a separate task changes parser semantics or test truth.
- The completed-window grace is fixed at five minutes in code; Lucia may decide whether it should later become an environment-controlled policy.

## Review Needed

Lucia review is required before merge to `main` or any project-ledger promotion.
