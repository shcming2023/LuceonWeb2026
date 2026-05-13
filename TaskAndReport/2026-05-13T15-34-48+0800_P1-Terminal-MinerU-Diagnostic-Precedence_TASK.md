# Task: P1 Terminal MinerU Diagnostic Precedence

Assignee:
DevelopmentEngineer

Issued by:
Director

Issued at:
2026-05-13T15:34:48+0800

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-13T15-34-48+0800_P1-Terminal-MinerU-Diagnostic-Precedence_TASK.md

Expected report:
TaskAndReport/2026-05-13T15-34-48+0800_P1-Terminal-MinerU-Diagnostic-Precedence_REPORT.md

## Required Reading Before Execution

- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/development-engineer.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- docs/codex/TEST_POLICY.md
- docs/codex/TEST_MATRIX.md
- docs/codex/REPOSITORY_STRUCTURE.md
- TaskAndReport/README.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-13T15-17-15+0800_P1-MinerU-Progress-Diagnostic-And-Log-Source-Ownership-Review_TASK.md
- TaskAndReport/2026-05-13T15-17-15+0800_P1-MinerU-Progress-Diagnostic-And-Log-Source-Ownership-Review_REPORT.md
- TaskAndReport/2026-05-13T15-34-48+0800_P1-MinerU-Progress-Diagnostic-And-Log-Source-Ownership-Review_DIRECTOR_REVIEW.md

## Background

Task 90 showed a useful but still misleading MinerU operator experience:

- MinerU completed and stored 21 parsed artifacts.
- Task metadata showed `progressSemantics.activityLevel=log-observation-unreadable`.
- Material metadata showed `progressSemantics.activityLevel=fast-complete-no-business-signal`.
- The task page/list displayed `MinerU 已提交/正在处理，但暂无可归因业务日志`, even after MinerU had completed.

Architect reviewed this in Task 92 and Director accepted the code-first plan: terminal completion diagnostics should take precedence over stale or unreadable in-flight diagnostics once MinerU completion is confirmed.

## Objective

Implement a small code/test fix so task-page/API operator semantics prefer terminal MinerU completion diagnostics over stale or unreadable in-flight log diagnostics after MinerU has completed, without fabricating page, batch, phase, or percent progress.

AI failure must remain visible and separate. A task can be failed at AI stage while MinerU semantics truthfully say MinerU completed with a diagnostic.

## Scope

Allowed code areas:

- `src/app/utils/taskView.ts`
- relevant task/detail/list display code if needed
- relevant MinerU metadata/update code if API-state correction is safer than frontend-only formatting
- `server/lib/ops-mineru-log-parser.mjs` or MinerU adapter code only if needed to reuse/propagate terminal diagnostics
- focused tests under `server/tests/` or existing frontend/test utilities if available
- task report and task ledger

Prefer the smallest robust change. Avoid a frontend-only wording patch if API/task metadata remains misleading and a small backend propagation fix is feasible.

## Required Behavior

For the Task 90 shape:

- task has `mineruStatus=completed`;
- parsed artifact pointers/counts exist;
- earlier task observation is `log-observation-unreadable`;
- material or completion observation has `fast-complete-no-business-signal`;
- final task may still be `state=failed`, `stage=ai`.

Expected operator semantics:

- MinerU line should say completion diagnostic, for example `MinerU 已完成，但本次未捕获可归因业务进度日志`;
- it must not say MinerU is merely submitted/processing after completion is confirmed;
- it must not invent page/batch/phase progress;
- AI failure message must remain visible separately.

## Required Tests / Checks

Add or update focused regression coverage for terminal diagnostic precedence.

Run at minimum:

```bash
git diff --check
node server/tests/mineru-log-progress-smoke.mjs
node <focused terminal diagnostic precedence test>
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

If changed files require syntax checks, run the relevant `node --check` commands.

If any check is skipped, report exact reason.

## Non-Goals And Hard Limits

- Do not deploy to production.
- Do not upload validation samples.
- Do not repair, retry, reparse, re-AI, delete, or clean up historical tasks.
- Do not mutate DB rows, MinIO objects, Docker volumes, logs, model files, secrets, production overrides, or sample files.
- Do not restart MinerU, Ollama, MinIO, DB, or the whole stack.
- Do not change AI prompt/taxonomy behavior.
- Do not claim production readiness, L3, pressure PASS, or release-readiness.

## Required Report

Write:

`TaskAndReport/2026-05-13T15-34-48+0800_P1-Terminal-MinerU-Diagnostic-Precedence_REPORT.md`

The report must include:

- root cause and chosen implementation boundary;
- files changed;
- before/after semantics for the Task 90 shape;
- proof that no progress details are fabricated;
- commands run and exit codes;
- skipped checks and reasons;
- residual risk;
- recommendation whether Director should batch this with Task 91 for production deployment/runtime validation.

Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch/HEAD, status, next actor `Director`, and required output.

Commit and push only this scoped implementation/report if possible.

## Acceptance Criteria

- Task 90-shaped data now derives terminal MinerU completion diagnostic semantics.
- AI failed state remains separately visible.
- Existing MinerU live progress semantics are not regressed.
- Focused regression test and `server/tests/mineru-log-progress-smoke.mjs` pass.
- No production/data/model/sample mutation or upload occurs.
