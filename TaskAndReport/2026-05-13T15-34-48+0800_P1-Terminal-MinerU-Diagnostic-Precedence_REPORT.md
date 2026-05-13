# DevelopmentEngineer Report: P1 Terminal MinerU Diagnostic Precedence

- Task: `TASK-20260513-153448-P1-Terminal-MinerU-Diagnostic-Precedence`
- Task brief: `TaskAndReport/2026-05-13T15-34-48+0800_P1-Terminal-MinerU-Diagnostic-Precedence_TASK.md`
- Role: DevelopmentEngineer
- Report time: 2026-05-13T15:48:21+0800
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Pre-report HEAD: `0b3389b Review AI guard and MinerU diagnostics`

## Root Cause And Boundary

Task 90-shaped data can contain both:

- task-level `metadata.mineruObservedProgress.activityLevel=log-observation-unreadable`, with in-flight wording like `MinerU 已提交/正在处理，但暂无可归因业务日志`;
- confirmed MinerU completion evidence, such as `metadata.mineruStatus=completed` plus parsed artifact count or artifact pointers.

`src/app/utils/taskView.ts` formatted only the task-level observation, so completed MinerU tasks could still show stale in-flight wording after parse completion. I chose a small shared frontend formatter fix because it updates both task list and task detail consumers of `deriveMineruProgressLine()` while preserving raw diagnostic evidence in task metadata.

No backend task/material mutation was performed.

## Files Changed

- `src/app/utils/taskView.ts`
- `server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs`
- `TaskAndReport/2026-05-13T15-34-48+0800_P1-Terminal-MinerU-Diagnostic-Precedence_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Implementation Summary

- Added parsed-artifact evidence detection in `taskView.ts`.
- Added terminal MinerU completion precedence:
  - if `mineruStatus=completed`;
  - and parsed artifact evidence exists;
  - and the observation is stale/unreadable/in-flight-only, or already a `fast-complete-no-business-signal`;
  - then `deriveMineruProgressLine()` returns `MinerU 已完成，但本次未捕获可归因业务进度日志`.
- Kept active progress formatting unchanged, including real phase/batch/page details when actually present.
- Did not alter AI task status derivation. A task can still display `失败` while the MinerU line truthfully says MinerU completed.

## Before / After For Task 90 Shape

Before:

- `mineruStatus=completed`, `parsedFilesCount=21`, task observation `log-observation-unreadable`
- UI/operator line: `MinerU 已提交/正在处理，但暂无可归因业务日志`
- This sounded as if MinerU was still merely submitted/processing.

After:

- same Task 90-shaped input
- UI/operator line: `MinerU 已完成，但本次未捕获可归因业务进度日志`
- `deriveTaskDisplayStatus()` still returns `失败` for the final AI failure, so AI failure remains visible separately.

## Proof No Progress Details Are Fabricated

The terminal completion line is a diagnostic sentence only. It does not include page, batch, phase, percent, or model-unit progress.

Focused test assertions verify the terminal line does not contain:

- `页 `
- `批次 `

The same focused test also verifies that active live-progress input still preserves real `Predict 14/27`, `批次 1/1`, and `页 14/27` details.

## Commands Run And Exit Codes

- `git status --short --branch` -> exit 0
- `rg -n "\| [0-9]+ \|.*\| (下达待执行|执行中|退回待修正|修正中) \| DevelopmentEngineer \|" TaskAndReport/TASK_TRACKING_LIST.md` -> exit 0
- `git diff --check` -> exit 0
- `node --check server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs` -> exit 0
- `node server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs` -> exit 0; output `MinerU terminal diagnostic precedence smoke passed`
- `node server/tests/mineru-log-progress-smoke.mjs` -> exit 0; `144 passed, 0 failed`
- `npx pnpm@10.4.1 exec tsc --noEmit` -> exit 0
- `npx pnpm@10.4.1 run build` -> exit 0; Vite build passed with existing chunk-size warning
- `git log -1 --oneline` -> exit 0; pre-report HEAD `0b3389b Review AI guard and MinerU diagnostics`

## Skipped Checks And Reasons

- No production deployment: explicitly forbidden by the task brief.
- No validation upload: explicitly forbidden by the task brief.
- No historical repair/reparse/re-AI/cleanup: explicitly forbidden by the task brief.
- No DB/MinIO/Docker/model/sample mutation or restart: explicitly forbidden by the task brief.
- No browser UAT: not requested for this code/test-level task; build and focused formatter regression cover the changed frontend utility.

## Residual Risk

- This is code/test-level evidence only and has not been deployed to production.
- Raw task metadata may still contain the older `log-observation-unreadable` object. The formatter intentionally preserves that evidence while changing operator-facing precedence.
- If future surfaces bypass `deriveMineruProgressLine()`, they may need to reuse the same precedence helper.

## Recommendation

Director should review this report. If accepted, this task can be batched with Task 91 for a single production deployment/runtime validation decision.

No production readiness, L3, pressure PASS, or release-readiness is claimed.
