# DevelopmentEngineer Report: P1 Upload-Time Db-Sync Console Noise Diagnosis And Hardening

## Based On

- Director task brief: `TaskAndReport/2026-05-14T19-39-27+0800_P1-Upload-Time-Db-Sync-Console-Noise-Diagnosis-And-Hardening_TASK.md`
- Director review: `TaskAndReport/2026-05-14T19-39-27+0800_P1-Post-Terminal-Diagnostic-Cleanup-One-Upload-Validation_DIRECTOR_REVIEW.md`
- Validation report: `TaskAndReport/2026-05-14T19-25-26+0800_P1-Post-Terminal-Diagnostic-Cleanup-Exactly-One-Controlled-Upload-Validation_REPORT.md`

## Branch / HEAD / Workspace State

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- HEAD: `005ca96 Hold Task 108 auto progress on GitHub sync`
- Workspace status: dirty shared role-thread workspace before this task, with many pre-existing modified/untracked project files. This task did not revert unrelated existing changes.

## Diagnosis

The two Task 145 residual warnings came from frontend db-sync fire-and-forget persistence in `src/store/appContext.tsx`:

- `ADD_MATERIAL` after a successful upload adds a local `Material`, which triggers the `state.materials` persistence effect and `POST /materials`.
- The reducer also creates `assetDetails[materialId]`, which triggers the `state.assetDetails` persistence effect and `PUT /asset-details/<materialId>`.
- In the upload flow, the canonical task/material records are already created by `POST /__proxy/upload/tasks`. These frontend writes are local mirror/upsert persistence, not the authoritative upload creation path.
- Task 145 observed the warnings only during upload/polling navigation, while post-terminal refresh was clean and HTTP 5xx count was `0`. This fits browser navigation/page-lifecycle cancellation of outstanding fire-and-forget mirror writes, not a persistent backend failure.

The fix therefore treats only transient fetch cancellation during page lifecycle end as non-warning debug noise. Normal page-visible failures, HTTP errors, auth/proxy failures, and persistent db-sync failures still increment the db failure counter and emit the existing `[db-sync] ... failed` warnings.

## Files Changed

- `src/store/appContext.tsx`
  - Added page lifecycle tracking for `pagehide` and `beforeunload`.
  - Added transient fetch-cancellation classification for `Failed to fetch`, abort/aborted, `NetworkError`, and load-failed style browser errors.
  - Updated `handleDbWriteError` so lifecycle-cancelled db-sync writes are logged with `console.debug` and do not poison the db failure counter.
  - Preserved existing `console.warn` paths for silent and non-silent real db-sync write failures.
- `server/tests/db-sync-page-lifecycle-noise-smoke.mjs`
  - Added a focused source-level smoke that verifies lifecycle cancellation is narrowly classified and warning/count paths still exist for real failures.
- `TaskAndReport/2026-05-14T19-39-27+0800_P1-Upload-Time-Db-Sync-Console-Noise-Diagnosis-And-Hardening_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Implementation Summary

Implemented a narrow db-sync noise hardening path:

- `pagehide` / `beforeunload` marks that the current document is leaving.
- If a db-sync write then fails with a transient fetch-cancellation signature, it is reported as `console.debug("[db-sync] ... cancelled during page lifecycle change")`.
- The path returns before `dbFailCount++`, avoiding misleading recovery/toast behavior for writes that the browser cancelled because the page was navigating away.
- The normal warning paths remain intact for real failures:
  - silent writes still warn as `[db-sync] ... failed (silent)`;
  - non-silent writes still warn as `[db-sync] ... failed (count=N)`;
  - HTTP failures are still thrown by `dbPost`/`dbPut` as `HTTP <status>` and do not match the lifecycle cancellation classifier.

## Commands Run And Exit Codes

- `git status --short --branch` — exit `0`
- `rg -n "DevelopmentEngineer|下达待执行|执行中|退回待修正|修正中" TaskAndReport/TASK_TRACKING_LIST.md` — exit `0`
- Required reading via `sed -n ...` for task brief, related report/review, and role/project docs — exit `0`
- `rg -n "\\[db-sync\\]|sync.*materials|asset-details|Failed to fetch|saveAssetDetails|materials failed|silent" src server uat` — exit `0`
- `node server/tests/db-sync-page-lifecycle-noise-smoke.mjs` — exit `0`
- `node --check server/tests/db-sync-page-lifecycle-noise-smoke.mjs` — exit `0`
- `node --check src/store/appContext.tsx` — exit `1`; Node cannot syntax-check `.tsx` modules directly (`ERR_UNKNOWN_FILE_EXTENSION`). TypeScript check below was used for TSX validation.
- First `git diff --check` — exit `2`; found one trailing whitespace introduced during editing.
- Final `git diff --check` — exit `0`
- `npx pnpm@10.4.1 exec tsc --noEmit` — exit `0`
- `git log -1 --oneline` — exit `0`, `005ca96 Hold Task 108 auto progress on GitHub sync`

## Skipped Checks And Reasons

- Production upload: skipped, explicitly forbidden by task brief.
- Production deployment/rebuild/restart: skipped, explicitly forbidden by task brief.
- Pressure, batch, soak, broader serial validation: skipped, explicitly forbidden by task brief.
- Cleanup/repair/reparse/re-AI, DB/MinIO/Docker volume/data mutation, settings/secrets/config/model/sample mutation: skipped, explicitly forbidden by task brief.
- Browser runtime validation of the new behavior: skipped because the task authorizes code/test-level work only and forbids production upload/deployment. A later TestAcceptanceEngineer/Director-authorized validation can prove the browser lifecycle behavior in production.

## Evidence

- Focused smoke passed:
  - `db-sync page lifecycle noise smoke passed`
- `git diff --check` passed after removing the trailing whitespace.
- `npx pnpm@10.4.1 exec tsc --noEmit` passed.
- Source-level evidence:
  - lifecycle-cancelled fetch failures return before `dbFailCount++`;
  - existing warning paths for `[db-sync] ... failed (silent)` and `[db-sync] ... failed (count=N)` remain present.

## Risks / Blockers / Residual Debt

- This task did not run production browser/upload validation, by design. The expected follow-up is a Director/TestAcceptanceEngineer-scoped validation if Director wants runtime proof.
- The fix addresses browser lifecycle cancellation noise. If a normal visible page still emits `POST /materials` or `PUT /asset-details` failures without navigation/unload, those failures remain visible and should be treated as real db-sync problems.
- The development workspace was already dirty with many shared role-thread changes before this task; only the scoped files listed above were intentionally changed for this task.

## Boundaries Confirmed

No production upload, production deployment, service mutation, destructive mutation, settings/secrets/config/model/sample mutation, broad warning suppression, readiness claim, L3 claim, pressure PASS, release-readiness claim, production-readiness claim, or go-live claim was made.

## Director Review

Director review is required. Suggested next actor: `Director`.
