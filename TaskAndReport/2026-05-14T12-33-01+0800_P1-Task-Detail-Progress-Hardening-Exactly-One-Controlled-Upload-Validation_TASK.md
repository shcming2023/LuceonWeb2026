# Task Brief: P1 Task Detail Progress Hardening Exactly One Controlled Upload Validation

- Task ID: `TASK-20260514-123301-P1-Task-Detail-Progress-Hardening-Exactly-One-Controlled-Upload-Validation`
- Created: 2026-05-14T12:33:01+0800
- Created by: Director
- Assigned role: `TestAcceptanceEngineer`
- Expected report: `TaskAndReport/2026-05-14T12-33-01+0800_P1-Task-Detail-Progress-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-14T12-29-44+0800_P1-Task-Detail-Progress-Hardening-One-Upload-Validation-Authorization_DECISION.md`
- Based on Director review: `TaskAndReport/2026-05-14T12-29-44+0800_P1-Task-Detail-Progress-Hardening-Production-Deployment-And-Read-Only-Runtime-Validation_DIRECTOR_REVIEW.md`

## Context

Task 123 implemented task-detail MinerU progress hardening:

- task detail now uses the same shared progress semantics as the task list;
- the task detail overview label is now `当前进展`;
- semantic MinerU progress should be preferred over raw task message, while raw message is still preserved as secondary evidence when different;
- read-only `/__proxy/upload/ops/dependency-repair/status` now returns HTTP 200 with structured `SUPERVISOR_UNAVAILABLE` when the optional supervisor is absent.

Task 124 deployed this code path to production and passed read-only runtime validation at production HEAD `5ca2615`:

- frontend `/cms/` HTTP 200;
- upload health OK;
- dependency-health `ok=true`, `blocking=false`;
- MinerU admission circuit closed;
- active task idle;
- direct MinerU healthy;
- `luceon-mineru` and `luceon-sidecar` present;
- port `8083` owned by the production MinerU process with configured ops log file descriptors;
- dependency-repair status route returned HTTP 200 with structured `SUPERVISOR_UNAVAILABLE`.

The remaining evidence gap is user-facing behavior during a real fresh MinerU parse:

- whether the task detail page now shows fine-grained MinerU progress under `当前进展`;
- whether task list and task detail progress semantics agree during processing;
- whether browser console noise related to dependency-repair status polling is reduced;
- whether final task/material/AI state remains clean after the deployed hardening.

User approved Option A: exactly one controlled upload validation. Do not broaden this scope.

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
12. `TaskAndReport/2026-05-14T12-17-02+0800_P1-Task-Detail-Progress-Hardening-Production-Deployment-And-Read-Only-Runtime-Validation_REPORT.md`
13. `TaskAndReport/2026-05-14T12-29-44+0800_P1-Task-Detail-Progress-Hardening-Production-Deployment-And-Read-Only-Runtime-Validation_DIRECTOR_REVIEW.md`

## Workspaces And Runtime Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production UI: `http://localhost:8081/cms/`
- Test PDF source directory: `/Users/concm/prod_workspace/Luceon2026/testpdf`
- MinerU endpoint: `http://127.0.0.1:8083`
- Upload proxy base: `http://localhost:8081/__proxy/upload`

Treat `/Users/concm/prod_workspace/Luceon2026/testpdf` as read-only. Do not copy samples into the repository.

## Objective

Run exactly one controlled small/medium PDF upload in production and validate the deployed task-detail progress hardening during the real processing window.

This is not a pressure test, release-readiness test, L3 test, or go-live test.

## Mandatory Preflight

Before uploading, run and record:

- production `git status --short --branch`;
- production `git log -1 --oneline`;
- `docker compose ps`;
- frontend `/cms/` HTTP 200;
- upload health;
- dependency-health with Ollama chat probe:
  - `ok=true`;
  - `blocking=false`;
  - Ollama model present/resident or otherwise non-blocking as reported;
- MinerU admission circuit through `/__proxy/upload/ops/mineru/admission-circuit`;
  - must be closed / `open=false`;
- active task through `/__proxy/upload/ops/mineru/active-task`;
  - must have no active/current/queued/takeover-required work;
  - historical AI failures may be recorded separately and are not a blocker by themselves;
- direct MinerU `/health`;
  - must be healthy;
  - queued and processing counts must be 0;
- `tmux ls`;
  - must include `luceon-mineru` and `luceon-sidecar`;
- `lsof -nP -iTCP:8083 -sTCP:LISTEN`;
  - must show exactly one listener;
- `lsof -a -p <8083 PID> -d cwd,1,2`;
  - cwd should be `/Users/concm/prod_workspace/Luceon2026`;
  - stdout/stderr should point to `/Users/concm/ops/logs/mineru-api.log` and `.err.log`;
- `/__proxy/upload/ops/dependency-repair/status`;
  - record HTTP status and body summary;
  - expected unavailable-supervisor status is HTTP 200 with structured `SUPERVISOR_UNAVAILABLE`.

Stop and write a blocked report if:

- active parse/AI work exists;
- admission circuit is open;
- dependency-health is blocking;
- Docker core services are unhealthy;
- direct MinerU is unhealthy;
- `luceon-mineru` or `luceon-sidecar` ownership is absent/ambiguous;
- port `8083` ownership is ambiguous or not production-owned;
- running the validation would require restart/rebuild/repair/reparse/re-AI/cleanup, destructive mutation, or more than one upload.

## Sample Selection

Use exactly one small/medium PDF from:

`/Users/concm/prod_workspace/Luceon2026/testpdf`

Record:

- chosen absolute path;
- file size;
- SHA-256 hash;
- why it was considered small/medium enough for this controlled validation.

Do not modify, move, rename, copy, delete, or truncate the sample file.

## Execution Scope

Allowed:

- open production UI;
- upload exactly one PDF;
- observe task list, task detail, task/status APIs, log-channel/global-observation endpoints, and browser console;
- wait for terminal state or clear systemic failure;
- write the required report and update the task ledger row.

Forbidden:

- second upload;
- pressure, batch, soak, long-run, or concurrent validation;
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

1. Does the task detail page overview label show `当前进展`?
2. During MinerU processing, does task detail show fine-grained MinerU progress rather than only generic status or stale text?
3. Does task list show consistent progress semantics for the same task?
4. Do the task detail and task list converge cleanly at terminal state?
5. Does browser console still show repeated dependency-repair status HTTP 503 noise?
6. Does `/__proxy/upload/ops/dependency-repair/status` remain HTTP 200 structured status while the UI is open?
7. Do log-channel/global-observation surfaces capture fresh attributable MinerU progress during processing?
8. Does final task/material/AI state reach a clean terminal state, or is there a systemic failure?

Recommended read-only endpoints to observe:

- `/__proxy/upload/ops/mineru/active-task`
- `/__proxy/upload/ops/mineru/admission-circuit`
- `/__proxy/upload/ops/mineru/log-channel-ownership`
- `/__proxy/upload/ops/mineru/global-observation`
- `/__proxy/upload/ops/dependency-health?ollamaChatProbe=true`
- `/__proxy/upload/ops/dependency-repair/status`

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
- whether any historical failures were created or unchanged;
- whether the browser UI stayed understandable to an operator.

## GitHub / Repository Rules

Do not run `git fetch`, `git pull`, or `git push` unless Director separately instructs you to do so.

Because this is a role-thread validation task in a shared workspace, write the report and update `TaskAndReport/TASK_TRACKING_LIST.md` locally. Director will handle GitHub synchronization after review if needed.

If local task ledger does not contain this task, report `本地任务列表未更新/疑似不同步` and stop rather than guessing.

## Required Report

Write:

`TaskAndReport/2026-05-14T12-33-01+0800_P1-Task-Detail-Progress-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`

The report must include:

- exact task brief path;
- required reading completed;
- preflight evidence;
- chosen sample path, size, SHA-256;
- exact upload count: must be 1;
- task/material/MinerU/AI identifiers;
- observations from task list and task detail during processing;
- whether `当前进展` appears and whether it contains fine-grained MinerU progress;
- browser console evidence, especially whether dependency-repair status polling still produces HTTP 503;
- endpoint observations during processing and at terminal state;
- final task/material/AI outcome;
- commands run and exit codes;
- skipped checks and exact reasons;
- risks/blockers/residual debt;
- explicit statement that no second upload, pressure/batch/soak, repair/reparse/re-AI, cleanup, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, model/config/secret/sample mutation, readiness, L3, pressure PASS, release-readiness, or go-live claim was made.

Update row 126 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated.
