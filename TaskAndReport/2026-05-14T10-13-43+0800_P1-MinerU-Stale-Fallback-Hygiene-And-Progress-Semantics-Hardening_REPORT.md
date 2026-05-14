# DevelopmentEngineer Report: P1 MinerU Stale Fallback Hygiene And Progress Semantics Hardening

- Task ID: `TASK-20260514-101343-P1-MinerU-Stale-Fallback-Hygiene-And-Progress-Semantics-Hardening`
- Report time: 2026-05-14T10:24:00+0800
- Role: DevelopmentEngineer
- Based on Director task brief: `TaskAndReport/2026-05-14T10-13-43+0800_P1-MinerU-Stale-Fallback-Hygiene-And-Progress-Semantics-Hardening_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Result: `COMPLETED_CODE_TEST_ONLY`

## Scope Boundary

This task was executed as code/test-only fallback hygiene.

No upload, production mutation, Docker command, MinerU/Ollama/sidecar/supervisor start/stop/restart/kill, log deletion/truncation, cleanup/repair/reparse/re-AI, sample/config/secret/model mutation, GitHub push, readiness claim, L3 claim, pressure PASS, go-live claim, or production上线 claim was performed.

## Branch / HEAD / Workspace State

- Branch from `git status --short --branch`: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- Current `git log -1 --oneline`: `005ca96 Hold Task 108 auto progress on GitHub sync`
- Worktree state: dirty before and after this task in the shared multi-role workspace.
- DevelopmentEngineer task-touched files:
  - `server/lib/ops-mineru-log-parser.mjs`
  - `server/tests/mineru-log-channel-ownership-smoke.mjs`
  - `TaskAndReport/2026-05-14T10-13-43+0800_P1-MinerU-Stale-Fallback-Hygiene-And-Progress-Semantics-Hardening_REPORT.md`
  - `TaskAndReport/TASK_TRACKING_LIST.md`
- Unrelated pre-existing modified/untracked files were not reverted, normalized, or edited intentionally.

## Implementation Summary

Implemented stale workspace scratch fallback suppression in `parseLatestMineruProgress()` when explicit configured MinerU log paths are present through `MINERU_LOG_PATH` and/or `MINERU_ERR_LOG_PATH`.

Behavior after this change:

- Explicit configured stdout/stderr log channels remain authoritative for current MinerU business-progress semantics.
- Workspace scratch fallback logs, including stale `uat/scratch/mineru-api.log` content, cannot be selected as `latest-valid-business-signal` when explicit configured log paths are present.
- Suppressed scratch fallback can still be carried as `ignoredDiagnosticLogSource` with diagnostic metadata, so it remains explainable without being promoted to current progress.
- If configured logs are empty and scratch fallback contains old `Predict 99%`, the observation stays `log-observation-empty` with missing freshness semantics instead of fabricating current phase/page/batch progress.
- Fresh configured log business progress still parses as `active-progress`.
- Existing fast-complete truthful diagnostic semantics remain valid.

No `src/app/utils/taskView.ts` change was required.

## Focused Test Changes

Updated `server/tests/mineru-log-channel-ownership-smoke.mjs`:

- Added proof that fresh configured log business progress still returns `active-progress` and selects `MINERU_ERR_LOG_PATH`.
- Added proof that stale workspace scratch fallback containing `Predict 99%` cannot outrank explicit empty configured logs.
- Added assertions that no current phase/progress semantics are fabricated from that stale fallback, while diagnostic metadata records the ignored fallback.

## Commands Run And Exit Codes

| Command | Exit Code | Notes |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Required pre-check; shared dirty worktree observed. |
| `node --check server/lib/ops-mineru-log-parser.mjs` | 0 | Parser syntax OK. |
| `node server/tests/mineru-log-channel-ownership-smoke.mjs` | 0 | 8 cases passed, including new stale fallback suppression case. |
| `node server/tests/mineru-log-progress-smoke.mjs` | 0 | 144 passed, 0 failed. |
| `node server/tests/mineru-log-observation-transport-smoke.mjs` | 0 | 3 cases passed. |
| `node server/tests/mineru-log-source-live-smoke.mjs` | 0 | 21 passed, 0 failed. |
| `git diff --check` | 0 | No whitespace errors reported. |
| `git log -1 --oneline` | 0 | Current HEAD recorded as `005ca96`. |

## Skipped Checks And Reasons

- `npx pnpm@10.4.1 exec tsc --noEmit`: skipped because `src/app/utils/taskView.ts` was not changed and the task brief only required this if the frontend helper changed.
- `npx pnpm@10.4.1 run build`: skipped for the same reason.
- Runtime/UAT/browser/production validation: skipped because the task is explicitly code/test-only and forbids production/runtime mutation and upload validation.

## Evidence

Stale scratch fallback cannot outrank configured production logs:

- New smoke case creates explicit configured empty logs and a stale `uat/scratch/mineru-api.log` containing old `Predict 99%`.
- `parseLatestMineruProgress()` returns `activityLevel=log-observation-empty`.
- `progressSemantics.freshness=missing`.
- `progressSemantics.phase=null`.
- `logSource.logSourceSelectedReason=file-empty`.
- `ignoredDiagnosticLogSource.logSourceSelectedReason=workspace-scratch-fallback-ignored-when-configured-logs-explicit`.
- `ignoredDiagnosticLogSource.diagnostic.hasBusinessSignal=true`, proving the old fallback had a business-like signal but was diagnostic-only.

Fresh configured progress still parses:

- Focused smoke writes current business-progress lines to the explicitly configured err log.
- `inspectMineruLogChannelOwnership()` reports `summaryState=valid-business-progress`.
- `parseLatestMineruProgress()` reports `activityLevel=active-progress`, `signals.hasBusinessSignal=true`, and `logSource.configuredBy=MINERU_ERR_LOG_PATH`.

Empty configured logs remain diagnostic and do not fabricate progress:

- Existing empty-log cases still return `log-observation-empty`.
- In-flight empty log warning remains `mineru-log-observation-diagnostic-only`.
- Fast-complete no-signal observation remains `fast-complete-no-business-signal`, with no phase/percent fabricated.

Regression coverage:

- `mineru-log-progress-smoke.mjs` passed all 144 assertions after the parser change.
- `mineru-log-observation-transport-smoke.mjs` passed host-source and timestamp tolerance checks.
- `mineru-log-source-live-smoke.mjs` passed the static/live-source mount and script checks without runtime mutation.

## Risks / Blockers / Residual Debt

- This change prevents stale scratch fallback pollution but does not restore true live MinerU business-progress observability.
- Configured production MinerU logs can still remain empty if the active MinerU process is unmanaged and writes stdout/stderr to pipes rather than `/Users/concm/ops/logs/mineru-api*.log`.
- True live progress likely still requires a later controlled MinerU ownership normalization, which is a runtime process mutation and needs separate User/Director authorization.
- Production deployment and runtime validation are needed before this behavior can be claimed in production.

## Review / Follow-Up

- Director review required: yes.
- Production deployment/runtime validation required: yes, if Director wants this code behavior applied to production surfaces.
- User decision required now: not for this code-only task; future MinerU ownership normalization would require explicit user approval.
- GitHub sync: not performed; not authorized by this task/thread protocol.
