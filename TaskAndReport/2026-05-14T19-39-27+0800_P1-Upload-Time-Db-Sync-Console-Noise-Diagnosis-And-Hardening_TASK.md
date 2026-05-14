# Task Brief: P1 Upload-Time Db-Sync Console Noise Diagnosis And Hardening

- Task ID: `TASK-20260514-193927-P1-Upload-Time-Db-Sync-Console-Noise-Diagnosis-And-Hardening`
- Created: 2026-05-14T19:39:27+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-14T19-39-27+0800_P1-Upload-Time-Db-Sync-Console-Noise-Diagnosis-And-Hardening_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-14T19-39-27+0800_P1-Post-Terminal-Diagnostic-Cleanup-One-Upload-Validation_DIRECTOR_REVIEW.md`
- Based on validation report: `TaskAndReport/2026-05-14T19-25-26+0800_P1-Post-Terminal-Diagnostic-Cleanup-Exactly-One-Controlled-Upload-Validation_REPORT.md`

## Context

Task 145 passed exactly one fresh post-cleanup upload validation:

- task `task-1778758370859` reached `review-pending` / `review`;
- material `3380327087858932` reached `reviewing`;
- MinerU completed with `21` parsed files;
- AI job `ai-job-1778758387317-1ccb` reached `review-pending`;
- terminal task detail and list showed clean MinerU primary progress with real backend/pipeline/page progress;
- the old no-attributed-log diagnostic was not appended as terminal `最后可见进度`;
- runtime returned idle and non-blocking.

Residual browser console warnings appeared only during the upload lifecycle:

- `[db-sync] POST /materials failed (count=1): Failed to fetch`
- `[db-sync] PUT /asset-details/3380327087858932 failed (silent): Failed to fetch`

Post-terminal refresh was clean and HTTP 5xx count was 0. The residual is therefore not a functional failure of the upload, but it is a real observability/operator-noise defect to diagnose.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/development-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. This task brief
12. `TaskAndReport/2026-05-14T19-25-26+0800_P1-Post-Terminal-Diagnostic-Cleanup-Exactly-One-Controlled-Upload-Validation_REPORT.md`
13. `TaskAndReport/2026-05-14T19-39-27+0800_P1-Post-Terminal-Diagnostic-Cleanup-One-Upload-Validation_DIRECTOR_REVIEW.md`

If `docs/codex/roles/development-engineer.md` or this task row is missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`. Do not improvise from partial role context.

## Objective

Diagnose and, if safe, harden the frontend db-sync/upload lifecycle so a successful upload does not emit misleading `[db-sync] ... Failed to fetch` console warnings caused by expected navigation/polling aborts or stale local sync attempts.

The fix must preserve strict visibility of real DB sync failures. Do not hide genuine server errors, rejected writes, auth failures, or persistent data-state failures.

## Scope

Allowed files/modules:

- frontend db-sync state management and local persistence code;
- upload flow code that triggers local state sync after successful task upload;
- focused tests or smoke tests covering the changed behavior;
- the task completion report and task ledger row.

Likely files to inspect include, but are not limited to:

- `src/store/appContext.tsx`
- `src/app/hooks/useFileUpload.ts`
- `src/app/pages/TaskManagementPage.tsx`
- existing focused smoke tests under `server/tests/` or equivalent lightweight test location.

## Non-Goals / Forbidden Work

Do not:

- run a production upload;
- run pressure, batch, soak, long-run, concurrent, or broader serial validation;
- deploy to production;
- restart, stop, kill, attach, or mutate MinerU/Ollama/supervisor/Docker services;
- run cleanup/repair/reparse/re-AI;
- directly mutate production DB, MinIO, Docker volumes, data, settings, secrets, config, models, or sample files;
- change PRD truth, role contracts, project state, handoff, or release judgments;
- change public API contracts unless a narrow compatibility-preserving fix is unavoidable and documented;
- suppress all `[db-sync]` warnings broadly;
- treat skeleton fallback or silent degradation as acceptable;
- declare production readiness, release-readiness, L3, pressure PASS, or go-live readiness.

## Suggested Direction

1. Locate the code path that logs `[db-sync] POST /materials failed` and `[db-sync] PUT /asset-details/... failed`.
2. Determine whether the validation warnings were likely caused by:
   - expected browser navigation/abort/cancellation;
   - stale local material/asset-detail sync after the upload flow had already created canonical server records;
   - an actual backend/proxy failure that recovered later;
   - another race in the local app state.
3. If the warnings are benign abort/race artifacts, narrow the logic so expected abort/cancellation is either not logged as a warning or is recorded at a quieter/debug level, while real failures still warn.
4. If the warnings indicate a real sync bug, fix the root cause narrowly.
5. Add or update focused tests/smokes so the intended classification is covered.

## Required Checks

Run at minimum:

- `git diff --check`
- syntax checks for changed JS/MJS files if applicable
- the most focused relevant smoke/unit test you add or modify
- `npx pnpm@10.4.1 exec tsc --noEmit` unless clearly impossible, in which case explain the exact blocker

Do not run production runtime validation or uploads under this task.

## Required Report

Write:

`TaskAndReport/2026-05-14T19-39-27+0800_P1-Upload-Time-Db-Sync-Console-Noise-Diagnosis-And-Hardening_REPORT.md`

The report must include:

- confirmation this work was based on this Director task brief;
- branch and HEAD;
- files changed;
- diagnosis of the two upload-time db-sync warnings;
- implementation summary or explicit explanation if no code change was justified;
- commands run and exit codes;
- skipped checks and exact reasons;
- evidence from focused tests/checks;
- risks/blockers/residual debt;
- explicit statement that no production upload, deployment, service mutation, destructive mutation, settings/secrets/config/model/sample mutation, or readiness/go-live claim was made.

Update row 146 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or precise blocked status;
- Next Actor: `Director`;
- Report path populated.
