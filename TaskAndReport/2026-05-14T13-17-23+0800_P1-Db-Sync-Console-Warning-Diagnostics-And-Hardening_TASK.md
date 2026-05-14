# Task Brief: P1 Db Sync Console Warning Diagnostics And Hardening

- Task ID: `TASK-20260514-131723-P1-Db-Sync-Console-Warning-Diagnostics-And-Hardening`
- Created: 2026-05-14T13:17:23+0800
- Created by: Director
- Assigned role: DevelopmentEngineer
- Priority: P1
- Expected report: `TaskAndReport/2026-05-14T13-17-23+0800_P1-Db-Sync-Console-Warning-Diagnostics-And-Hardening_REPORT.md`

## Context

Task 128 accepted a bounded small serial validation pass: three PDFs from `/Users/concm/prod_workspace/Luceon2026/testpdf` were uploaded strictly one at a time and all reached `review-pending` with coherent material and AI states. MinerU progress semantics, dependency-repair status, admission state, and final runtime cleanliness were acceptable for that bounded scope.

However, the Task 128 browser evidence recorded repeated warnings during the second and third uploads:

- `[db-sync] PUT /settings/mineruConfig failed ... Failed to fetch`
- `[db-sync] PUT /settings/minioConfig failed ... Failed to fetch`
- `[db-sync] PUT /settings/aiConfig failed ... Failed to fetch`
- `[db-sync] PUT /secrets failed ... Failed to fetch`

These warnings did not block the uploads, did not produce dependency-repair 503, and did not break terminal task/material/AI states. They still need code-level diagnosis because noisy failed settings/secrets writes reduce operator trust and may hide a real synchronization issue.

## Required Reading

Read before acting:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/development-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/codex/TEST_POLICY.md`
7. `docs/prd/Luceon2026-PRD-v0.4.md`
8. `TaskAndReport/README.md`
9. `TaskAndReport/TASK_TRACKING_LIST.md`
10. This task brief
11. `TaskAndReport/2026-05-14T12-58-14+0800_P1-Small-Serial-Validation-After-Task-Detail-Progress-Pass_REPORT.md`
12. `TaskAndReport/2026-05-14T13-17-23+0800_P1-Small-Serial-Validation-After-Task-Detail-Progress-Pass_DIRECTOR_REVIEW.md`

## Scope

Diagnose and, if root cause is confirmed, implement a narrow code-level hardening for the `[db-sync]` settings/secrets PUT warnings.

Likely files to inspect include, but are not limited to:

- `src/store/appContext.tsx`
- settings/config save flows under `src/app/`
- upload-server settings/secrets routes and proxy behavior in `server/upload-server.mjs`
- db-server settings/secrets routes in `server/db-server.mjs`
- existing tests around settings, app context, upload server, and browser console noise

You must determine whether the warnings are caused by an endpoint mismatch, route/proxy failure, hidden save-on-load behavior, duplicate background sync, navigation/abort timing, unavailable secrets, CORS/fetch configuration, or another concrete cause. Do not guess.

## Acceptance Criteria

1. Root cause is documented with code references and evidence.
2. If a code change is made, it is narrowly scoped to the confirmed `[db-sync]` warning cause.
3. Real user-initiated settings/secrets save failures must remain visible. Do not simply suppress all warnings.
4. Background/no-op sync must not emit repeated warnings when nothing changed or when optional secrets are intentionally unavailable.
5. No secrets, tokens, passwords, endpoint credentials, or private values are logged or committed.
6. Add or update focused tests where practical. If a focused automated test is not practical, explain why and provide a minimal reproducible verification method.
7. Do not change PRD truth, role contracts, public business workflow, task scope, model choice, MinerU/Ollama ownership, MinIO data, DB data, or production runtime.

## Required Checks

Run all applicable checks and record commands plus exit codes in the report:

- `git diff --check`
- `node --check` for any changed server `.mjs` files
- focused smoke/unit test(s) added or affected by this change
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`

If any check is skipped, state the exact reason.

## Forbidden

This task does not authorize:

- production deployment
- PDF upload validation
- pressure, batch-concurrent, soak, L3, release-readiness, or go-live claims
- cleanup, repair, reparse, re-AI, or failed-task mutation
- destructive DB, MinIO, Docker volume, Docker down, sample, model, secret, or config mutation
- MinerU, Ollama, supervisor, or sidecar start/stop/restart/kill/ownership changes
- broad refactor, public API change, or business-logic rewrite unrelated to the confirmed warning cause

## Deliverable

Write `TaskAndReport/2026-05-14T13-17-23+0800_P1-Db-Sync-Console-Warning-Diagnostics-And-Hardening_REPORT.md` and update the task ledger row to `已回报待 Director 审查` with `Next Actor=Director`.

