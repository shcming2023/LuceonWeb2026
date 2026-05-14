# Task Brief: P1 Task Detail MinerU Progress And Console Noise Hardening

- Task ID: `TASK-20260514-115922-P1-Task-Detail-MinerU-Progress-And-Console-Noise-Hardening`
- Created: 2026-05-14T11:59:22+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-14T11-59-22+0800_P1-Task-Detail-MinerU-Progress-And-Console-Noise-Hardening_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-14T11-59-22+0800_P1-Post-MinerU-Ownership-Normalization-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`

## Context

Task 122 validated the post-ownership-normalization flow with exactly one real UI upload:

- task `task-1778730187749`;
- material `4282929344122708`;
- MinerU task `fb5c5774-534c-4a7c-bc7a-d5546857cd1a`;
- AI job `ai-job-1778730259599-2d2f`;
- final state `review-pending`, material `reviewing`, MinerU completed, AI analyzed, `25` parsed artifacts;
- canonical global observation captured fresh attributable MinerU page/batch/phase progress during processing;
- the list page displayed real MinerU progress such as `批次 1/1，页 24/24`, `表格识别`, `模型识别`, `OCR 检测`, and `OCR 识别`.

Residual issues:

1. The task detail page did not surface fine-grained MinerU page/batch/phase progress during processing, even though the list page and canonical observability evidence had it.
2. Playwright captured repeated `503 Service Unavailable` resource errors and initial `[db-sync]` warnings. They did not block the validation, but they may confuse operators and obscure real failures.

## Objective

Implement or narrowly diagnose a code-level fix so that:

- the task detail page can display the same meaningful MinerU progress semantics already visible on the list page when progress data is available;
- repeated browser console `503`/db-sync noise is either fixed if safely localizable or precisely diagnosed with a narrow follow-up recommendation.

This is a code/test-level task only. Do not deploy to production and do not create validation uploads.

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
11. `TaskAndReport/2026-05-14T11-37-27+0800_P1-Post-MinerU-Ownership-Normalization-Exactly-One-Controlled-Upload-Validation_REPORT.md`
12. `TaskAndReport/2026-05-14T11-59-22+0800_P1-Post-MinerU-Ownership-Normalization-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`

## Allowed Scope

You may modify only the code/tests/docs needed for this narrow follow-up.

Expected likely areas:

- task detail rendering code;
- shared task progress/view helpers;
- frontend diagnostics or fetch/resource handling related to the repeated `503` noise;
- focused tests/smokes that prove the detail view can surface MinerU progress semantics and that console-noise handling does not mask real backend failures.

If the `503` source is not safely localizable within this task, do not broaden the fix. Record the exact route/resource/error evidence and propose a follow-up task.

## Acceptance Criteria

1. Detail progress parity:
   - when task/detail data contains current MinerU observed progress, the detail page has a clear human-readable MinerU progress message;
   - the detail message uses the same semantic vocabulary as the list/canonical observation path: backend, phase, batch/window, and pages where available;
   - no fabricated progress is shown when data is missing or stale;
   - terminal lifecycle truth remains authoritative.

2. Console noise:
   - repeated `503`/db-sync console noise is fixed if the source is a clear frontend/backend route mismatch or unnecessary failing request;
   - if not fixed, the report must include route/resource names, reproduction steps, and why a broader fix is out of scope;
   - do not hide or globally swallow real backend failures.

3. Strict boundaries:
   - no production deployment;
   - no upload;
   - no pressure/batch/soak;
   - no DB/MinIO data mutation;
   - no MinerU/Ollama/supervisor mutation;
   - no readiness/L3/pressure PASS/go-live claim.

## Required Validation

Run relevant focused checks. At minimum, run:

- `git diff --check`;
- syntax/type checks for changed files where applicable;
- focused smoke or unit tests covering task/detail MinerU progress display logic;
- `npx pnpm@10.4.1 exec tsc --noEmit` if frontend or shared TypeScript changes are made;
- `npx pnpm@10.4.1 run build` if frontend or build-affecting code changes are made.

If any check is skipped, report the exact reason.

## Required Report

Write the expected report with:

- exact task brief path;
- branch and HEAD;
- changed files;
- implementation summary;
- evidence for detail-page progress semantics;
- evidence for console `503`/db-sync fix or diagnosis;
- commands run and exit codes;
- skipped checks with reasons;
- residual risks/debt;
- explicit statement that no production deployment, upload, pressure/batch/soak, DB/MinIO data mutation, MinerU/Ollama/supervisor mutation, readiness, L3, pressure PASS, or go-live claim was made.

Update `TaskAndReport/TASK_TRACKING_LIST.md` so this row becomes `已回报待 Director 审查` with `Next Actor=Director`, and include the report path.
