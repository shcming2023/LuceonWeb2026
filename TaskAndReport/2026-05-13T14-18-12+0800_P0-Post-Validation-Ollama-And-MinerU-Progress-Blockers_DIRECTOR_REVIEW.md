# Director Review: P0 Post Validation Ollama And MinerU Progress Blockers

Task:
`TASK-20260513-135810-P0-Post-Validation-Ollama-And-MinerU-Progress-Blockers`

Reviewer:
Director

Review file:
`TaskAndReport/2026-05-13T14-18-12+0800_P0-Post-Validation-Ollama-And-MinerU-Progress-Blockers_DIRECTOR_REVIEW.md`

Reviewed report:
`TaskAndReport/2026-05-13T13-58-10+0800_P0-Post-Validation-Ollama-And-MinerU-Progress-Blockers_REPORT.md`

Review result:
`ACCEPTED_CODE_TEST_LEVEL_PRODUCTION_VALIDATION_DECISION_REQUIRED`

## Evidence Reviewed

- DevelopmentEngineer report for Task 87.
- Branch diff from `origin/main` to `development-engineer/p0-post-validation-ollama-mineru-blockers`.
- Implementation files:
  - `server/services/ai/providers/ollama.mjs`
  - `server/lib/ops-mineru-log-parser.mjs`
  - `server/services/mineru/local-adapter.mjs`
  - `server/services/mineru/v4-online-adapter.mjs`
  - `server/tests/ai-metadata-real-sample-smoke.mjs`
  - `server/tests/mineru-log-progress-smoke.mjs`
- Clean detached worktree review at implementation HEAD `36a30bb`.

## Independent Checks Run By Director

Director created a clean detached worktree from `36a30bb` and reused the existing local `node_modules` symlink only for dependency resolution. The repository files under review were clean branch files, not the dirty development working tree.

Checks:

- `git diff --check origin/main...HEAD` -> exit `0`
- `node --check server/services/ai/providers/ollama.mjs` -> exit `0`
- `node --check server/services/mineru/local-adapter.mjs` -> exit `0`
- `node --check server/services/mineru/v4-online-adapter.mjs` -> exit `0`
- `node --check server/lib/ops-mineru-log-parser.mjs` -> exit `0`
- `node server/tests/ai-metadata-real-sample-smoke.mjs` -> exit `0`
- `node server/tests/mineru-log-progress-smoke.mjs` -> exit `0`, `144 passed / 0 failed`
- `node server/tests/dependency-health-smoke.mjs` -> exit `0`, `65 passed / 0 failed`
- `node server/tests/mineru-diagnostics-smoke.mjs` -> exit `0`
- `npx pnpm@10.4.1 exec tsc --noEmit` -> exit `0`
- `npx pnpm@10.4.1 run build` -> exit `0`, with only the existing Vite large-chunk warning

## Scope Judgment

Accepted. DevelopmentEngineer stayed within the assigned code/test scope:

- no production deployment;
- no production upload;
- no pressure retry/test;
- no failed-task repair, reparse, re-AI, cleanup, destructive DB/MinIO/Docker volume/data mutation, model operation, PRD/role/release-truth change, L3, pressure PASS, or release-readiness claim.

## Validation Judgment

Accepted at code/test level only.

The patch directly addresses the two blockers from Task 86:

1. Ollama real metadata inference no longer has a hard 30-second `headersTimeout` while the job-level provider timeout is larger. `headersTimeout`, `bodyTimeout`, and `AbortSignal.timeout` now align to the provider request timeout.
2. MinerU fast-complete/no-business-signal cases now produce a structured diagnostic observation instead of silently omitting `mineruObservedProgress`, while real structured progress semantics remain preserved when parser data exists.

## Accepted Facts

- `server/services/ai/providers/ollama.mjs` now reports `headersTimeoutMs` and `bodyTimeoutMs` as the provider request timeout rather than a fixed `30000`.
- Dependency-health remains a separate bounded smoke path and was not widened by this provider change.
- Strict no-skeleton semantics remain covered by the AI metadata smoke suite.
- `server/services/mineru/local-adapter.mjs` and `server/services/mineru/v4-online-adapter.mjs` now import the shared log parser from the real `../../lib/ops-mineru-log-parser.mjs` path.
- Fast completed MinerU tasks can now receive a diagnostic observation with:
  - `activityLevel=fast-complete-no-business-signal`
  - UI-safe message `MinerU 已完成，但本次未捕获可归因业务进度日志`
  - no fabricated page, batch, or phase progress.

## Rejected Or Pending Claims

Still rejected/pending:

- production deployment success;
- real production upload success after the fix;
- proof that a production task now reaches `review-pending`;
- production task-page/API progress semantics validation;
- pressure PASS, L3, release readiness, or production readiness.

## Required Follow-Up

The next step requires owner authorization because it would deploy this accepted code path to production and create another controlled validation task/material. The previous user authorization allowed exactly one upload, and that upload has already been consumed by Task 86.

Director recorded:

- `TASK-20260513-141812-P0-Post-Fix-Production-Deployment-And-One-Upload-Validation-Authorization`

## Next Actor

`User`

## Next Action

Decide whether to approve the recommended scoped follow-up:

- deploy the accepted code path to production with minimum necessary rebuild/restart;
- run non-destructive runtime checks;
- then perform exactly one controlled upload from `/Users/concm/prod_workspace/Luceon2026/testpdf` to verify the two fixed blockers.

## Required Output

User decision recorded by Director, followed by a scoped task brief if approved.
