# Task Brief: P1 Post Terminal Diagnostic Cleanup Exactly One Controlled Upload Validation

- Task ID: `TASK-20260514-192526-P1-Post-Terminal-Diagnostic-Cleanup-Exactly-One-Controlled-Upload-Validation`
- Created: 2026-05-14T19:25:26+0800
- Created by: Director
- Assigned role: `TestAcceptanceEngineer`
- Expected report: `TaskAndReport/2026-05-14T19-25-26+0800_P1-Post-Terminal-Diagnostic-Cleanup-Exactly-One-Controlled-Upload-Validation_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-14T19-21-07+0800_P1-Next-Validation-Scope-After-Terminal-Diagnostic-Cleanup_DECISION.md`
- Based on Director review: `TaskAndReport/2026-05-14T19-21-07+0800_P1-MinerU-Terminal-Diagnostic-Cleanup-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`

## Context

Task 143 deployed the accepted Task 141 terminal diagnostic cleanup to production and passed scoped read-only runtime/browser validation:

- production was fast-forwarded to `58f1437`;
- services were healthy;
- dependency-health was non-blocking;
- MinerU admission was closed;
- active MinerU state was idle;
- existing successful terminal task details no longer appended the old no-attributed-log diagnostic as `最后可见进度`;
- real backend/pipeline/page progress remained visible where present.

Task 143 intentionally did not perform a fresh upload. The remaining evidence gap is one new post-cleanup PDF lifecycle proving that a newly submitted PDF now presents clean MinerU progress semantics from upload through terminal state.

User approved Option A at `2026-05-14T19:25:26+0800`: exactly one controlled fresh upload from `/Users/concm/prod_workspace/Luceon2026/testpdf`.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/test-acceptance-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. This task brief
12. `TaskAndReport/2026-05-14T19-08-58+0800_P1-MinerU-Terminal-Diagnostic-Cleanup-Production-Deployment-And-Read-Only-Validation_REPORT.md`
13. `TaskAndReport/2026-05-14T19-21-07+0800_P1-MinerU-Terminal-Diagnostic-Cleanup-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`

If `docs/codex/roles/test-acceptance-engineer.md` or this task row is missing in the local development workspace, stop and report `本地任务列表或角色文档未更新/疑似不同步`. Do not improvise from partial role context.

## Workspaces And Runtime Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production UI: `http://localhost:8081/cms/`
- Test PDF source directory: `/Users/concm/prod_workspace/Luceon2026/testpdf`
- MinerU endpoint: `http://127.0.0.1:8083`
- Upload proxy base: `http://localhost:8081/__proxy/upload`

Treat `/Users/concm/prod_workspace/Luceon2026/testpdf` as read-only. Do not copy samples into the repository. Do not modify, move, rename, delete, truncate, or pollute sample files.

## Objective

Run exactly one controlled small/medium PDF upload in production and validate the deployed terminal diagnostic cleanup during a real fresh processing lifecycle.

This is not a pressure test, batch test, soak test, L3 test, release-readiness test, go-live test, or broad production-readiness test.

## Mandatory Preflight

Before uploading, run and record:

- development workspace `git status --short --branch`;
- production `git status --short --branch`;
- production `git log -1 --oneline`;
- `docker compose ps` in production;
- frontend `/cms/` HTTP 200;
- upload health;
- dependency-health with Ollama chat probe and MinerU submit probe if safe:
  - `ok=true`;
  - `blocking=false`;
  - MinerU admission remains closed after submit probe settles;
  - Ollama is non-blocking as reported;
- MinerU admission circuit through `/__proxy/upload/ops/mineru/admission-circuit`;
  - must be closed / `open=false`;
- active task through `/__proxy/upload/ops/mineru/active-task`;
  - must have no active/current/queued/takeover-required work;
  - historical AI failures may be recorded separately and are not a blocker by themselves;
- direct MinerU `/health`;
  - must be healthy;
  - queued and processing counts must be 0 after any submit-probe activity settles.

Stop and write a blocked report if:

- active parse/AI work exists;
- admission circuit is open;
- dependency-health is blocking;
- Docker core services are unhealthy;
- direct MinerU is unhealthy or not idle after safe probe settlement;
- running the validation would require restart/rebuild/repair/reparse/re-AI/cleanup, destructive mutation, or more than one upload;
- the test PDF source directory is missing or contains no reasonable small/medium PDF.

## Sample Selection

Use exactly one small/medium PDF from:

`/Users/concm/prod_workspace/Luceon2026/testpdf`

Record:

- chosen absolute path;
- file size;
- SHA-256 hash;
- why it was considered small/medium enough for this controlled validation.

## Execution Scope

Allowed:

- open production UI;
- upload exactly one PDF;
- observe task list, task detail, task/status APIs, MinerU admission/active-task endpoints, direct MinerU health, and browser console/network;
- wait for terminal state or clear systemic failure;
- write the required report and update the task ledger row.

Forbidden:

- second upload;
- batch, intake, pressure, soak, long-run, concurrent, or broader serial validation;
- failed-task repair;
- reparse or re-AI;
- cleanup or deletion of historical tasks/materials/files;
- direct DB/MinIO mutation;
- `docker compose down`, `docker compose down -v`, Docker volume/data cleanup;
- MinerU/Ollama/supervisor start/stop/restart/kill/attach/mutation;
- model pull/delete/replace;
- config/secret/sample mutation;
- PRD truth, role contract, project state, or handoff changes;
- declaring L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.

## Required Observations During Processing

Capture enough evidence to answer these questions:

1. Does the upload create exactly one new task/material?
2. Does the task detail page show understandable `当前进展` during MinerU processing?
3. During MinerU processing, does the UI show real backend/pipeline/page or otherwise attributable progress when available?
4. Does the task list show consistent progress semantics for the same task?
5. At terminal success, does the primary progress line avoid appending the old no-attributed-log diagnostic as `最后可见进度`?
6. If the upload fails, is the failure explicit and attributable rather than silently masked?
7. Do task/material/MinerU/AI states converge coherently at terminal state?
8. Does browser console/network show relevant `[db-sync]`, `/settings`, `/secrets`, `Failed to fetch`, HTTP 5xx, or non-stream request-failed noise?

Recommended read-only endpoints to observe:

- `/__proxy/upload/ops/mineru/active-task`
- `/__proxy/upload/ops/mineru/admission-circuit`
- `/__proxy/upload/ops/dependency-health?ollamaChatProbe=true`
- direct `http://127.0.0.1:8083/health`

## Terminal-State Evidence

At the end, record:

- task id;
- material id if visible;
- MinerU task id if visible;
- AI job id if visible;
- final task state/stage/message;
- final material state/status;
- parsed artifact count if available;
- AI metadata state;
- final active-task/admission/direct MinerU health;
- whether any new historical failures were created;
- whether the browser UI stayed understandable to an operator.

## GitHub / Repository Rules

Do not run `git fetch`, `git pull`, or `git push` unless Director separately instructs you to do so.

Because this is a role-thread validation task in a shared workspace, write the report and update `TaskAndReport/TASK_TRACKING_LIST.md` locally. Director will handle GitHub synchronization after review if needed.

If the local task ledger does not contain this task, report `本地任务列表未更新/疑似不同步` and stop rather than guessing.

## Required Report

Write:

`TaskAndReport/2026-05-14T19-25-26+0800_P1-Post-Terminal-Diagnostic-Cleanup-Exactly-One-Controlled-Upload-Validation_REPORT.md`

The report must include:

- exact task brief path;
- required reading completed;
- preflight evidence;
- chosen sample path, size, SHA-256;
- exact upload count: must be 1;
- task/material/MinerU/AI identifiers;
- observations from task list and task detail during processing;
- whether `当前进展` appears and whether it contains useful MinerU progress;
- browser console/network evidence;
- endpoint observations during processing and at terminal state;
- final task/material/AI outcome;
- commands run and exit codes;
- skipped checks and exact reasons;
- risks/blockers/residual debt;
- explicit statement that no second upload, batch/intake/pressure/soak, repair/reparse/re-AI, cleanup, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, model/config/secret/sample mutation, readiness, L3, pressure PASS, release-readiness, production-readiness, or go-live claim was made.

Update row 145 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated.
