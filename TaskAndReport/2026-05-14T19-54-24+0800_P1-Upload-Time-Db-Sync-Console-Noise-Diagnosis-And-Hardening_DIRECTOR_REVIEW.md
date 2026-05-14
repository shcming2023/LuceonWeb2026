# Director Review: P1 Upload-Time Db-Sync Console Noise Diagnosis And Hardening

## Review Result

`ACCEPTED_CODE_TEST_LEVEL_PRODUCTION_DEPLOYMENT_DECISION_REQUIRED`

## Reviewed Materials

- Task brief: `TaskAndReport/2026-05-14T19-39-27+0800_P1-Upload-Time-Db-Sync-Console-Noise-Diagnosis-And-Hardening_TASK.md`
- DevelopmentEngineer report: `TaskAndReport/2026-05-14T19-39-27+0800_P1-Upload-Time-Db-Sync-Console-Noise-Diagnosis-And-Hardening_REPORT.md`
- Prior validation report: `TaskAndReport/2026-05-14T19-25-26+0800_P1-Post-Terminal-Diagnostic-Cleanup-Exactly-One-Controlled-Upload-Validation_REPORT.md`
- Prior Director review: `TaskAndReport/2026-05-14T19-39-27+0800_P1-Post-Terminal-Diagnostic-Cleanup-One-Upload-Validation_DIRECTOR_REVIEW.md`

## Director Findings

Task 146 is accepted at code/test level.

The diagnosis is plausible and correctly scoped. Task 145's residual warnings were produced by frontend db-sync mirror writes after a successful upload:

- `ADD_MATERIAL` triggered material persistence;
- generated `assetDetails[materialId]` triggered asset-detail persistence;
- canonical upload/task/material creation had already happened through `POST /__proxy/upload/tasks`;
- the warnings appeared during upload/polling navigation and disappeared on post-terminal refresh with HTTP 5xx count `0`.

The implementation is narrow:

- `src/store/appContext.tsx` now tracks page lifecycle ending through `pagehide` and `beforeunload`;
- only transient fetch-cancellation signatures during that lifecycle-ending window are downgraded to `console.debug`;
- the lifecycle-cancelled path returns before incrementing the db failure counter;
- normal silent and non-silent warning paths remain present for real db-sync write failures.

The new focused smoke `server/tests/db-sync-page-lifecycle-noise-smoke.mjs` checks the intended source-level behavior: lifecycle cancellation is classified narrowly, returns before `dbFailCount++`, and normal warning paths remain.

## Director Verification

Director replayed the scoped patch in a clean GitHub sync clone and ran:

- `node server/tests/db-sync-page-lifecycle-noise-smoke.mjs` -> pass;
- `node --check server/tests/db-sync-page-lifecycle-noise-smoke.mjs` -> pass;
- `git diff --check` -> pass;
- `npx pnpm@10.4.1 exec tsc --noEmit` -> pass.

The accepted code delta is limited to:

- `src/store/appContext.tsx`;
- `server/tests/db-sync-page-lifecycle-noise-smoke.mjs`;
- Task/report/ledger files.

## Boundaries

This review does not accept or perform production deployment.

This review does not prove browser-runtime behavior after deployment. Runtime proof requires a separately authorized scoped production deployment and validation task.

No production upload, production deployment, pressure/batch/soak/broader serial validation, cleanup/repair/reparse/re-AI, destructive DB/MinIO/Docker volume/data mutation, Docker/service mutation, settings/secrets/config/model/sample mutation, broad warning suppression, readiness/L3/pressure PASS/release-readiness/production-readiness/go-live claim was performed or accepted.

## Residual Risk

The fix is intentionally conservative and only quiets transient fetch cancellation when the page is leaving. If `[db-sync] POST /materials` or `[db-sync] PUT /asset-details/...` warnings occur during a normal visible page lifecycle, they remain real warnings and should still be investigated.

## Next Step

Record a User decision for scoped production deployment and validation.

Director recommendation: Option A. Authorize only minimum necessary frontend production deployment plus read-only post-deploy checks and exactly one controlled fresh upload validation, because the defect only manifests during upload/navigation. Keep pressure/batch/soak and readiness claims out of scope.
