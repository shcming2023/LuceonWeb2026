# DevelopmentEngineer Report: P1 MinerU Progress Snapshot Contract And Active-Task Reconciliation

## Task Brief

- Based on Director task brief: `TaskAndReport/2026-05-16T06-20-58+0800_P1-MinerU-Progress-Snapshot-Contract-And-Active-Task-Reconciliation_TASK.md`
- Task ID: `TASK-20260516-062058-P1-MinerU-Progress-Snapshot-Contract-And-Active-Task-Reconciliation`
- Report time: `2026-05-16T06:40:25+0800`

## Branch / HEAD

- Branch: `main`
- Starting HEAD: `a96b824`
- Working tree: implementation/report/ledger changes pending at report time before commit.

## Files Changed

- `server/lib/progress-snapshot.mjs`
- `server/upload-server.mjs`
- `server/services/queue/task-worker.mjs`
- `src/app/utils/taskView.ts`
- `server/tests/progress-snapshot-contract-smoke.mjs`
- `server/tests/task-event-message-smoke.mjs`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-16T06-20-58+0800_P1-MinerU-Progress-Snapshot-Contract-And-Active-Task-Reconciliation_REPORT.md`

## Implementation Summary

- Added a normalized `progressSnapshot` backend contract with `phase`, `source`, `sourcePriority`, `observedAt`, `freshness`, `confidence`, `lagKind`, `directMineruStatus`, `dbState`, `dbStage`, `logState`, `aiState`, and `operatorMessage`.
- Updated `/ops/mineru/active-task` to perform read-only direct MinerU task checks by default, attach per-task progress snapshots, expose `diagnosticMode`, and classify direct-MinerU-completed while DB still shows running as `resultIngestionLagTasks` with `lagKind=db-behind-direct-mineru`.
- Added dependency-health `progressSnapshot` that explicitly marks readiness checks as `dependency-health-readiness-only`, preventing health green from being interpreted as task progress.
- Added terminal/idle log-channel snapshot semantics so stale logs after terminal or idle state do not imply MinerU is still processing.
- Replaced `Status changed to undefined` fallback event messages with explicit metadata/progress event messages.
- Narrowly adjusted task display status so an AI-stage failed task only receives the AI-specific display label when explicit AI failure metadata/classification exists; otherwise terminal failure remains the canonical failed label.

## Commands Run And Exit Codes

- `git status --short --branch` -> exit `0`
- `rg -n "\\| DevelopmentEngineer \\|" TaskAndReport/TASK_TRACKING_LIST.md` -> exit `0`
- `sed -n ...` / `rg ...` read-only inspections of task brief, role docs, prior reports, and relevant source files -> exit `0` except one wrong Director review filename lookup -> exit `1`, then corrected path was found and read.
- `node --check server/lib/progress-snapshot.mjs && node --check server/upload-server.mjs && node --check server/services/queue/task-worker.mjs` -> exit `0`
- `node server/tests/progress-snapshot-contract-smoke.mjs` -> exit `0`
- `node server/tests/task-event-message-smoke.mjs` -> exit `0`
- `node server/tests/ops-mineru-active-task-classification-smoke.mjs` -> exit `0`
- `git diff --check` -> exit `0`
- `node server/tests/dependency-health-smoke.mjs` -> exit `0`
- `node server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs` -> initial exit `1`; after focused display-status fix, rerun exit `0`
- `npx pnpm@10.4.1 exec tsc --noEmit` -> exit `0`
- `npx pnpm@10.4.1 run build` -> exit `0` with existing Vite chunk-size warning.

## Skipped Checks And Reasons

- No production upload, pressure test, retry, reparse, re-AI, submit-probe, restart, rebuild, redeploy, DB/MinIO/Docker mutation, or task/material mutation was run; these are explicitly outside the task brief.
- No broad frontend redesign was attempted; frontend change was limited to the existing display utility needed to satisfy terminal/AI failure semantics.

## Evidence

- Direct-completed MinerU while DB still running is represented by `lagKind=db-behind-direct-mineru`, `sourcePriority=direct-mineru`, and operator message `MinerU API 已完成，Luceon 正在同步解析结果`.
- Terminal stale logs are represented as terminal/idle log observations and do not use processing language.
- Dependency health now exposes readiness-only progress semantics and remains separate from per-task progress.
- Metadata-only progress updates now log `Progress metadata updated` instead of `Status changed to undefined`.
- Focused smoke tests and TypeScript/build checks passed after the final change.

## Risks / Blockers / Residual Debt

- This is a code-level/backend-contract implementation only. No deployed runtime validation was performed in this task.
- `/ops/mineru/active-task` direct checking is read-only but depends on MinerU endpoint reachability; when unreachable, snapshots remain DB-derived and expose that mode through diagnostics.
- Additional UI presentation work may still be useful so operators can visually compare DB-derived and direct-checked status, but this task kept the frontend scope minimal.

## Review / Next Step

- Needs Director review: yes.
- Needs later production validation or user decision: yes, Director/TestAcceptanceEngineer should decide whether and when to validate in the production deployment path.
