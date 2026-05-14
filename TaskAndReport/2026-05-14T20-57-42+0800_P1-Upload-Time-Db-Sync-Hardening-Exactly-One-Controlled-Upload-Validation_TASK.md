# Task Brief: P1 Upload-Time Db-Sync Hardening Exactly One Controlled Upload Validation

- Task ID: `TASK-20260514-205742-P1-Upload-Time-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation`
- Created: 2026-05-14T20:57:42+0800
- Created by: Director
- Assigned role: `TestAcceptanceEngineer`
- Expected report: `TaskAndReport/2026-05-14T20-57-42+0800_P1-Upload-Time-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-14T19-54-24+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-Decision_DECISION.md`
- Based on deployment review: `TaskAndReport/2026-05-14T20-57-42+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`

## Context

Task 146 implemented narrow frontend hardening for upload-time db-sync lifecycle cancellation noise.

Task 148 deployed that hardening to production and passed read-only validation:

- production HEAD is `89271a1`;
- accepted markers are present in production source;
- core Docker services are healthy;
- upload health is OK;
- dependency-health is OK and non-blocking;
- MinerU admission is closed;
- active-task is idle;
- direct MinerU health is idle;
- read-only `/cms/tasks` browser pass showed no relevant db-sync/settings/secrets/Failed-to-fetch/5xx/non-stream-failure noise.

The remaining proof is the actual runtime condition where the defect was observed: exactly one fresh upload lifecycle.

User already approved Option A in Task 147. This task is the second role-safe step under that approval.

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
12. `TaskAndReport/2026-05-14T20-38-00+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-And-Read-Only-Validation_REPORT.md`
13. `TaskAndReport/2026-05-14T20-57-42+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`

If `docs/codex/roles/test-acceptance-engineer.md` or this task row is missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`. Do not improvise from partial role context.

## Workspaces And Runtime Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production UI: `http://localhost:8081/cms/`
- Test PDF source directory: `/Users/concm/prod_workspace/Luceon2026/testpdf`
- Upload proxy base: `http://localhost:8081/__proxy/upload`
- MinerU endpoint: `http://127.0.0.1:8083`

Treat `/Users/concm/prod_workspace/Luceon2026/testpdf` as read-only. Do not copy samples into the repository. Do not modify, move, rename, delete, truncate, or pollute sample files.

## Objective

Run exactly one controlled small/medium PDF upload in production to validate the deployed Task 146 db-sync lifecycle hardening under the real upload/navigation condition.

This is not a pressure test, batch test, soak test, L3 test, release-readiness test, go-live test, or broad production-readiness test.

## Mandatory Preflight

Before uploading, run and record:

- development workspace `git status --short --branch`;
- production `git status --short --branch`;
- production `git log -1 --oneline`;
- production `docker compose ps`;
- frontend `/cms/` HTTP status;
- upload health;
- dependency-health with Ollama chat probe and MinerU submit probe if safe;
- MinerU admission circuit;
- active task through `/__proxy/upload/ops/mineru/active-task`;
- direct MinerU `/health`;
- a marker check confirming production source contains `dbSyncPageLifecycleEnding` and `cancelled during page lifecycle change`.

Stop and write a blocked report if:

- production is not at a Task-148-accepted deployment state;
- active parse/AI work exists;
- MinerU admission circuit is open;
- dependency-health is blocking;
- Docker core services are unhealthy;
- direct MinerU is unhealthy or not idle after safe probe settlement;
- the test PDF source directory is missing or contains no reasonable small/medium PDF;
- running the validation would require restart/rebuild/repair/reparse/re-AI/cleanup, destructive mutation, or more than one upload.

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
- batch/intake/pressure/soak/broader serial validation;
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

## Required Observations

Capture enough evidence to answer these questions:

1. Does the upload create exactly one new task/material?
2. During upload and navigation/polling, do `[db-sync] POST /materials failed` or `[db-sync] PUT /asset-details/... failed` warnings recur?
3. Are any lifecycle-cancelled db-sync messages downgraded to debug rather than warning, if visible in the console capture?
4. Does browser console/network show relevant `/settings`, `/secrets`, `Failed to fetch`, HTTP 5xx, or non-stream request-failed noise?
5. Do task/material/MinerU/AI states converge coherently at terminal state?
6. Does terminal task detail/list primary progress stay clean and avoid appending the old no-attributed-log diagnostic as `最后可见进度`?
7. Does runtime return to idle/non-blocking after terminal state?

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

`TaskAndReport/2026-05-14T20-57-42+0800_P1-Upload-Time-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`

The report must include:

- exact task brief path;
- required reading completed;
- preflight evidence;
- chosen sample path, size, SHA-256;
- exact upload count: must be 1;
- task/material/MinerU/AI identifiers;
- observations from upload lifecycle, task list, and task detail;
- explicit db-sync console/network evidence during upload and after terminal refresh;
- endpoint observations during processing and at terminal state;
- final task/material/AI outcome;
- commands run and exit codes;
- skipped checks and exact reasons;
- risks/blockers/residual debt;
- explicit statement that no second upload, batch/intake/pressure/soak, repair/reparse/re-AI, cleanup, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, model/config/secret/sample mutation, readiness, L3, pressure PASS, release-readiness, production-readiness, or go-live claim was made.

Update row 149 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated.
