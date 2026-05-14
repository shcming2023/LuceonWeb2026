# Director Review: P1 Task Detail MinerU Progress And Console Noise Hardening

- Review time: 2026-05-14T12:17:02+0800
- Reviewed task: `TASK-20260514-115922-P1-Task-Detail-MinerU-Progress-And-Console-Noise-Hardening`
- Reviewed report: `TaskAndReport/2026-05-14T11-59-22+0800_P1-Task-Detail-MinerU-Progress-And-Console-Noise-Hardening_REPORT.md`
- Reviewer: Director
- Result: `ACCEPTED_CODE_TEST_LEVEL_PRODUCTION_DEPLOYMENT_REQUIRED`

## Scope Judgment

Accepted at code/test level.

DevelopmentEngineer stayed within the assigned code/test boundary: no production deployment, PDF upload, pressure/batch/soak validation, DB/MinIO data mutation, MinerU/Ollama/supervisor mutation, model/config/secret/sample mutation, readiness, L3, pressure PASS, or go-live claim was made.

Director integrated only the scoped Task 123 code changes into the clean GitHub-sync worktree:

- `src/app/pages/TaskDetailPage.tsx`
- `server/upload-server.mjs`
- `server/tests/task-detail-progress-and-supervisor-status-smoke.mjs`

The unrelated pre-existing local comment diff in `server/upload-server.mjs` from the dirty development workspace was not promoted.

## Evidence Accepted

Accepted implementation:

- Task detail overview now imports and uses the shared task-view helpers:
  - `deriveMineruProgressLine`
  - `deriveTaskDisplayStatus`
- Overview display now prefers semantic MinerU progress over generic lifecycle text and raw task message.
- The operator-facing overview label changes from `消息` to `当前进展`.
- If a semantic MinerU progress line exists and the raw message differs, the raw task message is retained as secondary text.
- Read-only `/ops/dependency-repair/status` no longer returns HTTP `503` when the optional supervisor is unavailable; it returns structured `{ ok:false, code:'SUPERVISOR_UNAVAILABLE', ... }`.
- The POST repair action route still preserves HTTP `503` semantics for real action failures.

Director rechecked in the clean GitHub-sync worktree:

- `node --check server/upload-server.mjs` passed.
- `node server/tests/task-detail-progress-and-supervisor-status-smoke.mjs` passed.
- `git diff --check -- src/app/pages/TaskDetailPage.tsx server/upload-server.mjs server/tests/task-detail-progress-and-supervisor-status-smoke.mjs` passed.
- `npx pnpm@10.4.1 exec tsc --noEmit` passed after installing clean-worktree dependencies with `npx pnpm@10.4.1 install --frozen-lockfile`.
- `npx pnpm@10.4.1 run build` passed, with the existing Vite large chunk warning only.

Director also re-ran the same focused smoke, syntax check, scoped diff-check, TypeScript, and build checks in the dirty development workspace before integration; they passed there as well.

## Residual Boundary

This is not production-deployed evidence. The fix still needs a scoped production deployment and read-only runtime validation before a follow-up browser/upload validation can be considered.

The `[db-sync]` warnings remain diagnosed but not fully fixed because Task 122 did not provide exact write route/status evidence. That should remain a narrower follow-up only if it recurs after the supervisor-status 503 reduction.

## Not Accepted

This review does not accept or authorize:

- production readiness;
- release readiness;
- L3;
- pressure PASS;
- pressure, batch, soak, or long-run validation;
- PDF upload;
- cleanup, repair, reparse, re-AI, or historical task mutation;
- destructive DB/MinIO/Docker volume/data operation;
- MinerU/Ollama/supervisor mutation;
- model/config/secret/sample mutation;
- go-live readiness or production上线.

## Next Step

Director issues Task 124 to DevelopmentEngineer for scoped production deployment and read-only runtime validation of the accepted Task 123 code path.
