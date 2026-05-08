# Lucia Review: P1 Active-Task Historical AI Failure Classification Fix

- Review time: 2026-05-09T07:47:37+0800
- Reviewer: Lucia
- Task: `TASK-20260509-063709-P1-Active-Task-Historical-AI-Failure-Classification-Fix`
- Task brief: `TaskAndReport/2026-05-09T06-37-09+0800_P1-Active-Task-Historical-AI-Failure-Classification-Fix_TASK.md`
- Lucode report: `TaskAndReport/2026-05-09T06-48-17+0800_P1-Active-Task-Historical-AI-Failure-Classification-Fix_REPORT.md`
- Implementation branch: `lucode/p1-active-task-historical-ai-failure-classification-fix`
- Implementation HEAD reviewed: `fffb22a`
- Integration method: `git cherry-pick --no-commit fffb22a`, then Lucia restored focused diagnostics smoke coverage for log observation structure before committing.

## Decision

`ACCEPTED_CODE_LEVEL`

The implementation is accepted at code level and integrated into `main` in this Lucia review update. This does not claim production release readiness and does not by itself authorize production deployment, restart, rebuild, Docker mutation, production task mutation, retry, reparse, cleanup, model/config/secret/override change, or validation artifact creation.

## Accepted Scope

- `/ops/mineru/active-task` and `/ops/mineru/diagnostics` now share `classifyMineruActiveTasks()`.
- Historical terminal AI failures with completed MinerU status and parsed artifacts are separated into `historicalAiFailureTasks`.
- Actionable completed-but-not-ingested or running-completed MinerU cases remain visible in `takeoverRequiredTasks`.
- The new focused active-task classification smoke covers the historical-AI-failure bucket and the actionable takeover bucket.

## Lucia Review Notes

- The implementation branch was behind the main report commit, so Lucia integrated only the implementation commit `fffb22a` and avoided carrying any stale TaskAndReport state from the branch.
- Lucia observed that the branch removed a previous direct `logObservation.phase` assertion from `server/tests/mineru-diagnostics-smoke.mjs`. The old exact phase assertion is no longer structurally stable because current log observation can be sourced through the richer observation object; Lucia restored coverage by asserting `source === 'mineru-log'` and a populated `activityLevel`.
- No production runtime was mutated during this review.

## Independent Checks

Passed:

```bash
git show --check --stat --oneline fffb22a
node server/tests/ops-mineru-active-task-classification-smoke.mjs
node server/tests/mineru-diagnostics-smoke.mjs
node server/tests/mineru-no-resubmit-smoke.mjs
git diff --check main..fffb22a
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Additional post-integration checks passed after Lucia restored smoke coverage:

```bash
node server/tests/mineru-diagnostics-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Build emitted the existing Vite chunk-size warning only.

## Residual Boundary

Production still needs a separate Director decision before this diagnostic classification fix is deployed or validated in production. This is a diagnostics/ops visibility correction, not production release readiness.
