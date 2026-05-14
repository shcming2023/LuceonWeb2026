# Task Brief: P1 Post MinerU Ownership Normalization Exactly One Controlled Upload Validation

- Task ID: `TASK-20260514-113727-P1-Post-MinerU-Ownership-Normalization-Exactly-One-Controlled-Upload-Validation`
- Created: 2026-05-14T11:37:27+0800
- Created by: Director
- Assigned role: `TestAcceptanceEngineer`
- Expected report: `TaskAndReport/2026-05-14T11-37-27+0800_P1-Post-MinerU-Ownership-Normalization-Exactly-One-Controlled-Upload-Validation_REPORT.md`
- Decision authorization: `TaskAndReport/2026-05-14T11-34-11+0800_P1-Post-MinerU-Ownership-Normalization-One-Upload-Validation-Authorization_DECISION.md`

## Context

Task 120 accepted scoped MinerU process/log ownership normalization:

- MinerU now runs under the `luceon-mineru` tmux session;
- the sole listener on port `8083` was verified as PID `61436` at Director review time;
- MinerU process cwd is `/Users/concm/prod_workspace/Luceon2026`;
- stdout/stderr are attached to `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log`;
- `luceon-sidecar` is present;
- upload health, dependency-health, admission circuit, and active-task surfaces were healthy/nonblocking/idle.

The remaining proof gap is user-facing: whether a real upload now produces fresh, attributable MinerU progress semantics on the task page and observability endpoints.

The user approved Option A at 2026-05-14T11:37:27+0800: exactly one controlled small/medium PDF upload validation from `/Users/concm/prod_workspace/Luceon2026/testpdf`.

## Objective

Run one and only one controlled production upload validation to determine whether MinerU live progress semantics are observable after process/log ownership normalization.

This task is validation only. It must not declare production readiness, L3, pressure PASS, release readiness, or go-live readiness.

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
11. `TaskAndReport/2026-05-14T11-12-19+0800_P1-MinerU-Ownership-Normalization-Scoped-Runtime-Recovery_REPORT.md`
12. `TaskAndReport/2026-05-14T11-34-11+0800_P1-MinerU-Ownership-Normalization-Scoped-Runtime-Recovery_DIRECTOR_REVIEW.md`
13. `TaskAndReport/2026-05-14T11-34-11+0800_P1-Post-MinerU-Ownership-Normalization-One-Upload-Validation-Authorization_DECISION.md`

## Workspaces And Local Runtime

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Sample source: `/Users/concm/prod_workspace/Luceon2026/testpdf`
- MinerU: host service on `8083`, expected owner `luceon-mineru`, logs at `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log`
- MinerU log sidecar: `luceon-sidecar`
- Ollama: `qwen3.5:9b`, expected dependency-health keep_alive `24h`
- MinIO and CMS services: Docker Compose in the production workspace

Treat sample files as read-only. Do not copy, move, rename, edit, delete, or commit them.

## Mandatory Preflight

Run preflight before any upload. Stop and write a blocked report if any mandatory gate fails.

Required preflight evidence:

- production `git status --short --branch` and `git log -1 --oneline`;
- `docker compose ps`;
- `tmux ls` includes `luceon-mineru` and `luceon-sidecar`;
- port `8083` has exactly one listener;
- the MinerU listener cwd/log fd evidence still points to `/Users/concm/prod_workspace/Luceon2026` and `/Users/concm/ops/logs/mineru-api*.log`;
- direct MinerU `/health` is healthy;
- upload health is OK;
- dependency-health canonical route is `GET /__proxy/upload/ops/dependency-health` and must return `blocking=false`;
- admission canonical route is `GET /__proxy/upload/ops/mineru/admission-circuit` and must be closed;
- active-task canonical route is `GET /__proxy/upload/ops/mineru/active-task` and must show no active parse/AI work;
- `/__proxy/upload/ops/mineru/log-channel-ownership` is reachable;
- `/__proxy/upload/ops/mineru/global-observation` is reachable;
- sample directory exists and contains at least one small/medium PDF.

Important route note:

- Use `/__proxy/upload/ops/mineru/admission-circuit`.
- Use `/__proxy/upload/ops/mineru/active-task`.
- Do not use the old short routes `/__proxy/upload/mineru/admission-circuit` or `/__proxy/db/tasks/active-task`; Director spot-check showed those return 404.

## Upload Scope

After preflight passes:

- choose exactly one small/medium PDF from `/Users/concm/prod_workspace/Luceon2026/testpdf`;
- record its absolute path, file size, and SHA-256;
- upload exactly once through the production CMS/task UI if possible, because this task must validate page semantics;
- if UI upload is impossible before creating the upload, stop and report blocked rather than using a second path silently;
- after upload is created, do not create another upload for any reason, including failure, timeout, bad sample, or ambiguous result.

## Required Observations

Observe and report:

- task list page semantics during MinerU processing;
- task detail page semantics during MinerU processing;
- final task/material state;
- MinerU task ID;
- AI job ID if one is created;
- parsed artifact count if available;
- canonical `/ops/mineru/log-channel-ownership` during processing and after terminal state;
- canonical `/ops/mineru/global-observation` during processing and after terminal state;
- whether progress is fresh/stale, attributed/unattributed, and whether it reflects real page/window/batch semantics;
- whether the page gives a human-understandable state instead of false failure or misleading progress;
- whether strict no-skeleton behavior remains intact if AI fails.

If processing is too fast to catch an in-flight page state, still report:

- the polling cadence used;
- the first observed post-upload task state;
- final state;
- endpoint evidence showing whether any fresh business progress was captured.

## Pass / Fail Interpretation

Pass boundary:

- exactly one upload was created;
- no forbidden mutation occurred;
- task reaches a coherent terminal state or clear review-pending state;
- the UI/list/detail state is understandable;
- configured MinerU logs and observability endpoints provide fresh, non-scratch progress semantics for the real upload, or the report clearly proves the upload was too fast and provides honest residual evidence.

Failure or blocked boundary:

- preflight fails;
- upload cannot be created through the UI;
- task enters false failure or misleading progress state;
- configured log channel does not capture attributable real-upload progress;
- endpoint/page semantics conflict with task lifecycle;
- AI/MinerU/MinIO/Ollama failure occurs.

Any failure is still useful evidence. Do not compensate by creating a second upload.

## Forbidden Scope

Do not:

- upload more than one PDF;
- run pressure, batch, soak, or long-run validation;
- clean up, repair, reparse, re-AI, or mutate historical tasks/materials;
- mutate DB/MinIO records directly;
- run Docker down/down-v or Docker volume/data cleanup;
- mutate MinerU ownership, restart MinerU, or start/stop/kill MinerU;
- mutate Ollama, pull/delete/replace models, or change model configuration;
- attach/start `luceon-supervisor`;
- change source code, PRD truth, role contracts, project state, handoff, secrets, config, samples, or model settings;
- delete, truncate, rename, or edit log files;
- commit sample files or machine-only artifacts;
- declare L3, production readiness, release readiness, pressure PASS, go-live readiness, or production上线.

## Required Report

Write the expected report with:

- exact task brief path;
- development branch/HEAD and production HEAD;
- all commands/actions run with exit codes where applicable;
- preflight evidence;
- selected sample path, size, and SHA-256;
- upload method and proof that exactly one upload was created;
- task/material/MinerU/AI IDs;
- UI task list/detail observations;
- endpoint observations during processing and after terminal state;
- final state and pass/fail/block judgment;
- skipped checks and exact reasons;
- risks/blockers/residual debt;
- explicit statement that no pressure/batch/soak, second upload, cleanup, repair/reparse/re-AI, DB/MinIO mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, model/config/secret/sample mutation, readiness, L3, pressure PASS, or go-live claim was made.

Update `TaskAndReport/TASK_TRACKING_LIST.md` so this row becomes `已回报待 Director 审查` with `Next Actor=Director`, and include the report path.
