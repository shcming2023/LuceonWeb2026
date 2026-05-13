# DevelopmentEngineer Report: P0 Post-Validation Ollama And MinerU Progress Blockers

- Task ID: `TASK-20260513-135810-P0-Post-Validation-Ollama-And-MinerU-Progress-Blockers`
- Report time: `2026-05-13T14:10:27+0800`
- Role: `DevelopmentEngineer`
- Task brief: `TaskAndReport/2026-05-13T13-58-10+0800_P0-Post-Validation-Ollama-And-MinerU-Progress-Blockers_TASK.md`
- Result: `IMPLEMENTED_CODE_TEST_LEVEL`

## Basis And Scope

This work was based on the Director task brief above and the accepted Task 86 failed-validation evidence.

Implemented only code/test changes for:

1. Ollama real metadata inference timeout semantics.
2. MinerU progress observation / fast-complete diagnostic semantics.

No production deployment, validation upload, pressure retry, failed-task repair, DB/MinIO/Docker volume cleanup, model mutation, PRD truth change, role-contract change, L3 claim, pressure PASS, or release-readiness claim was performed.

## Branch And HEAD

- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- Implementation commit: branch HEAD for `development-engineer/p0-post-validation-ollama-mineru-blockers`.
- GitHub sync before work: `git fetch origin` passed; `git pull --ff-only origin main` reported `Already up to date`.
- GitHub push status: branch pushed to `origin/development-engineer/p0-post-validation-ollama-mineru-blockers`.
- Worktree note: the workspace already contained many unrelated modified/untracked files before this task. They were preserved and not reverted.

## Files Changed By This Task

- `server/services/ai/providers/ollama.mjs`
- `server/lib/ops-mineru-log-parser.mjs`
- `server/services/mineru/local-adapter.mjs`
- `server/services/mineru/v4-online-adapter.mjs`
- `server/tests/ai-metadata-real-sample-smoke.mjs`
- `server/tests/mineru-log-progress-smoke.mjs`
- `TaskAndReport/2026-05-13T13-58-10+0800_P0-Post-Validation-Ollama-And-MinerU-Progress-Blockers_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Implementation Summary

### Ollama timeout contract

Before:

- Real non-streaming `/api/chat` calls used `headersTimeoutMs=30000`.
- `bodyTimeoutMs` and `AbortSignal.timeout` followed the provider `timeoutMs`.
- This could make the first-byte/header timeout the effective generation deadline.

After:

- `headersTimeoutMs`, `bodyTimeoutMs`, and `AbortSignal.timeout` all use the provider `timeoutMs`.
- Error details still expose `timeoutKind`, `headersTimeoutMs`, `bodyTimeoutMs`, `durationMs`, provider model, and base URL.
- Dependency-health smoke remains separate and bounded by its own short health-check path.

### MinerU progress semantics

- Fixed MinerU adapter dynamic imports from the missing `server/services/lib/...` path to the real `server/lib/ops-mineru-log-parser.mjs` path.
- Added a fast-complete diagnostic observation for completed MinerU tasks when no attributable business progress signal was captured.
- Preserved real structured progress semantics when parser data exists.
- The new diagnostic is explicitly `fast-complete-no-business-signal`; it does not fabricate page, batch, or phase progress.
- UI-safe `progressSemantics.message` avoids host log paths and states: `MinerU 已完成，但本次未捕获可归因业务进度日志`.

## Evidence

- Strict no-skeleton remained covered by `node server/tests/ai-metadata-real-sample-smoke.mjs`; repair timeout still records skeleton fallback under strict test conditions and keeps timeout details.
- Fast-complete/no-business-signal behavior is covered by `node server/tests/mineru-log-progress-smoke.mjs` Test 31.
- Adapter import-path regression is covered by `node server/tests/mineru-log-progress-smoke.mjs` Test 32.
- Existing structured progress behavior remains covered by the same smoke suite, including pipeline batch/page/phase semantics.

## Commands Run

| Command | Exit | Result |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Showed existing dirty workspace on previous DevelopmentEngineer branch. |
| `git fetch origin` | 0 | Completed. |
| `git pull --ff-only origin main` | 0 | `Already up to date.` |
| `git switch -c development-engineer/p0-post-validation-ollama-mineru-blockers` | 0 | Created scoped branch. |
| `node --check server/services/ai/providers/ollama.mjs` | 0 | Syntax OK. |
| `node --check server/services/mineru/local-adapter.mjs` | 0 | Syntax OK. |
| `node --check server/services/mineru/v4-online-adapter.mjs` | 0 | Syntax OK. |
| `node --check server/lib/ops-mineru-log-parser.mjs` | 0 | Syntax OK. |
| `node --check server/tests/ai-metadata-real-sample-smoke.mjs` | 0 | Syntax OK. |
| `node --check server/tests/mineru-log-progress-smoke.mjs` | 0 | Syntax OK. |
| `node server/tests/ai-metadata-real-sample-smoke.mjs` | 0 | Passed. |
| `node server/tests/mineru-log-progress-smoke.mjs` | 0 | `144 passed, 0 failed`. |
| `node server/tests/dependency-health-smoke.mjs` | 0 | `65 passed, 0 failed`. |
| `node server/tests/mineru-diagnostics-smoke.mjs` | 0 | Passed. |
| `git diff --check` | 0 | No output. |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | Passed. |
| `npx pnpm@10.4.1 run build` | 0 | Passed; Vite emitted only the existing large-chunk warning. |

## Skipped Checks

None of the task-required developer checks were skipped.

Production deployment, production upload validation, pressure retry, and failed-task repair were intentionally not run because the task brief forbids them.

## Risks And Residual Debt

- This is code/test-level evidence only. It does not prove the fix in production runtime.
- A follow-up `TestAcceptanceEngineer` production validation task is required to verify a real upload now reaches visible MinerU semantics or the fast-complete diagnostic, and to verify real Ollama metadata inference no longer fails at the unintended 30-second boundary.
- The workspace had unrelated dirty files before this task. They remain outside this task scope.

## Director Review Required

Yes. Director should review this report, the scoped diff, and decide whether to issue a follow-up production validation task.
