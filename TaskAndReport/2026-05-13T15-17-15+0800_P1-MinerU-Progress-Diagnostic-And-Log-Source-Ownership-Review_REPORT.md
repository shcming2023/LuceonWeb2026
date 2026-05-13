# Architect Report: P1 MinerU Progress Diagnostic And Log Source Ownership Review

- Task ID: `TASK-20260513-151715-P1-MinerU-Progress-Diagnostic-And-Log-Source-Ownership-Review`
- Report time: `2026-05-13T15:34:00+0800`
- Role: `Architect`
- Task brief: `TaskAndReport/2026-05-13T15-17-15+0800_P1-MinerU-Progress-Diagnostic-And-Log-Source-Ownership-Review_TASK.md`
- Recommendation: `MIXED_CODE_AND_OPS_GAP_WITH_CODE_FIRST_PLAN`

## 1. Scope And Boundary

This report is based on the Director task brief. I performed read-only inspection only.

No code, production config, DB rows, MinIO objects, Docker volumes, model files, sample files, task states, or runtime services were changed. No upload, retry, repair, cleanup, restart, L3, pressure validation, or release-readiness claim was performed.

## 2. Facts Inspected

Read:

- Architect task brief for Task 92.
- TestAcceptanceEngineer report for Task 90.
- Director review for Task 90.
- Architect role contract, team contract, test matrix, production runtime ownership document, and current task ledger.
- Source paths relevant to MinerU observation and UI display:
  - `server/lib/ops-mineru-log-parser.mjs`
  - `server/services/mineru/local-adapter.mjs`
  - `server/upload-server.mjs`
  - `server/services/queue/task-worker.mjs`
  - `src/app/utils/taskView.ts`
  - `server/tests/mineru-log-progress-smoke.mjs`

Task 90 observed:

- task `task-1778655375028`;
- material `validation-postfix-1778655374`;
- MinerU task `5cc6acce-061f-4418-a29b-b862af8306a6`;
- MinerU completed and stored 21 parsed artifacts;
- task metadata had `progressSemantics.activityLevel=log-observation-unreadable`;
- material metadata had `progressSemantics.activityLevel=fast-complete-no-business-signal`;
- production log source was `/host/mineru-logs/mineru-api.err.log`, existing but unreadable or empty with size `0`;
- UI showed the diagnostic text `MinerU 已提交/正在处理，但暂无可归因业务日志`;
- AI failure is a separate P0 terminal-state issue and must not be mixed into MinerU progress acceptance.

## 3. Direct Answers

1. The remaining gap is mixed, but code-first. There is an ops/log ownership signal because the container-visible log source is empty or unreadable, but the operator-facing mismatch is also a code/data-contract issue: task UI reads task-level `metadata.mineruObservedProgress`, while completion diagnostics can later produce a better terminal diagnostic that may not replace the stale task-level in-flight diagnostic in all surfaces.

2. The mismatch is explainable from two observation paths. During processing, `parseLatestMineruProgress()` returned `log-observation-unreadable` from the configured log source. On completion, `buildCompletionObservation()` can call `createFastCompleteMineruObservation()` when no business signal was captured, producing `fast-complete-no-business-signal`. Task-level UI still uses the task's `mineruObservedProgress`, so it can preserve the earlier unreadable-log diagnostic while material or completion metadata records the later fast-complete diagnostic.

3. Yes. After MinerU completion is confirmed, the task page should prefer a terminal, completion-aware diagnostic over a stale or unreadable in-flight diagnostic, as long as it does not fabricate page/batch progress. For this case, `MinerU 已完成，但本次未捕获可归因业务进度日志` is more truthful than `MinerU 已提交/正在处理...`.

4. Do not make a production log ownership change as the first fix. The production ownership contract already says MinerU logs are host-owned and upload-server reads mounted paths. Because short 3-page tasks may finish before meaningful business logs appear, Luceon should rely less on host log files for terminal short-task semantics. Log mount/readability should still get a separate ops check, but not as a blocker for truthful task-page terminal messaging.

5. The smallest safe plan is to make completion diagnostics authoritative for terminal MinerU display, keep unreadable-log diagnostics as evidence, and add tests that prevent terminal completed MinerU tasks from showing an in-flight "submitted/processing" message when a completion diagnostic exists.

6. Before another upload validation, require code-level tests for terminal diagnostic precedence plus the existing MinerU log progress smoke. If Director also wants to validate the log mount itself, add a read-only runtime check of container-visible `/host/mineru-logs/mineru-api.log` and `.err.log` size/mtime/readability before upload, but do not mutate logs.

## 4. Root-Cause Hypothesis

Confidence: `medium-high`.

Primary hypothesis:

- `parseLatestMineruProgress()` correctly exposes log-channel failure as `log-observation-unreadable` when no readable content exists in the selected log source.
- `createFastCompleteMineruObservation()` correctly creates `fast-complete-no-business-signal` for fast terminal completion without captured business progress.
- The architecture gap is that task-page display relies on one task-level observation object and does not consistently prefer the newer terminal completion diagnostic over older in-flight diagnostic text.

Secondary hypothesis:

- The configured production log mount/path may be incomplete for the task 90 timing window, especially because `/host/mineru-logs/mineru-api.err.log` existed with size `0`. However, the parser also checks the normal log path, and fast short tasks can still produce no attributable business progress even when the log path is valid. This makes an ops-only fix insufficient.

## 5. Recommended Implementation Tasks

Code task, P1:

- Define a terminal MinerU display precedence contract:
  - If `mineruStatus=completed` and parsed artifact evidence exists, display terminal completion semantics over stale/unreadable in-flight log semantics.
  - If `fast-complete-no-business-signal` exists, show it as a completed diagnostic.
  - Preserve prior `log-observation-unreadable` under diagnostic detail fields for operators and reports.
- Apply the contract in the backend task/material metadata update path or in a shared frontend formatter, but avoid a frontend-only wording patch if API state remains misleading.
- Keep AI failure display separate: final task may be `failed` at AI stage while MinerU line says completed diagnostic.

Ops/read-only task, optional P2:

- Add or run a read-only log-source ownership check that reports host log paths, container mount paths, file size, mtime, and readability for both `mineru-api.log` and `mineru-api.err.log`.
- Do not restart MinerU, change mount paths, truncate logs, or alter config without a later Director task.

## 6. Risk Level

Risk: `medium`.

Reason:

- The user-visible status can mislead operators by saying MinerU is still submitted/processing after MinerU has completed.
- The risk is observability and operator trust, not data loss: Task 90 showed MinerU artifact ingestion succeeded.
- A careless fix could fabricate progress or hide real log-source failures, so the implementation must preserve diagnostic evidence while improving terminal precedence.

## 7. Acceptance Criteria For DevelopmentEngineer

A future DevelopmentEngineer task should pass if:

- A terminal task/material with `mineruStatus=completed`, parsed artifact pointers, and a completion diagnostic displays completed MinerU semantics even if an earlier task observation was `log-observation-unreadable`.
- The display/API does not fabricate page, batch, phase, or percentage when no business signal exists.
- AI terminal failure remains visible and separate from MinerU completion.
- `node server/tests/mineru-log-progress-smoke.mjs` passes, including fast-complete diagnostic coverage.
- A focused regression test covers the Task 90 shape: previous unreadable log observation plus completion diagnostic.
- `git diff --check`, relevant syntax checks, TypeScript, and build pass if code is changed.

## 8. Director/User Decisions Needed

Director decision needed:

- Dispatch a code-first DevelopmentEngineer task for terminal MinerU diagnostic precedence.
- Decide whether to also dispatch a separate read-only ops check for production log-source ownership.

User decision not required unless Director wants to change production log ownership, mount configuration, or validation-upload scope.

## 9. Recommended Next Actor

Next Actor: `Director`.

Director should review this report and, if accepted, issue a scoped DevelopmentEngineer task. A separate ops/log-source task can wait unless Director wants to prove the log mount before the next upload validation.
