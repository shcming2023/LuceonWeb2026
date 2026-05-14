# Task Brief: P1 Small Serial Validation After Task Detail Progress Pass

- Task ID: `TASK-20260514-125814-P1-Small-Serial-Validation-After-Task-Detail-Progress-Pass`
- Created: 2026-05-14T12:58:14+0800
- Created by: Director
- Assigned role: `TestAcceptanceEngineer`
- Expected report: `TaskAndReport/2026-05-14T12-58-14+0800_P1-Small-Serial-Validation-After-Task-Detail-Progress-Pass_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-14T12-54-36+0800_P1-Next-Validation-Scope-After-Task-Detail-Progress-Pass_DECISION.md`
- Based on Director review: `TaskAndReport/2026-05-14T12-54-36+0800_P1-Task-Detail-Progress-Hardening-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`

## Context

Task 126 passed exactly-one production upload validation after task-detail progress hardening:

- task `task-1778733717808`;
- material `2820074763593700`;
- MinerU task `9d5a39b1-d098-40d4-a277-a853433bd006`;
- AI job `ai-job-1778733759504-ed73`;
- final task state `review-pending`;
- material `reviewing`;
- MinerU completed;
- AI analyzed;
- parsed files `25`;
- task detail `当前进展` appeared in `39/39` observations;
- task detail/list both showed fine-grained MinerU progress in `29/39` observations;
- dependency-repair status polling produced HTTP 200 only, with no HTTP 503 and no browser warning/error events.

Task 126 is still one-sample evidence. The next conservative step is a small serial validation pass, not pressure testing.

User approved Option A: up to 3 additional PDFs, strictly serial, one terminal state before the next upload, stop on systemic failure.

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
12. `TaskAndReport/2026-05-14T12-33-01+0800_P1-Task-Detail-Progress-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`
13. `TaskAndReport/2026-05-14T12-54-36+0800_P1-Task-Detail-Progress-Hardening-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`

## Workspaces And Runtime Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production UI: `http://localhost:8081/cms/`
- Test PDF source directory: `/Users/concm/prod_workspace/Luceon2026/testpdf`
- MinerU endpoint: `http://127.0.0.1:8083`
- Upload proxy base: `http://localhost:8081/__proxy/upload`

Treat `/Users/concm/prod_workspace/Luceon2026/testpdf` as read-only. Do not copy samples into the repository.

## Objective

Run a small serial production validation pass with up to 3 additional PDFs.

The validation should answer whether the stabilized pipeline holds across a few more documents while still respecting single-machine resource constraints:

- task detail `当前进展`;
- list/detail fine-grained MinerU progress consistency;
- browser console/dependency-repair HTTP 503 noise;
- admission/active-task cleanliness before and after each upload;
- final task/material/MinerU/AI states.

This is not a pressure test, concurrent batch test, soak test, release-readiness test, L3 test, or go-live test.

## Mandatory Global Preflight

Before any upload, run and record:

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
  - expected unavailable-supervisor status is HTTP 200 with structured `SUPERVISOR_UNAVAILABLE`.

Stop and write a blocked report if any preflight condition is unsafe.

## Per-Upload Rules

For each PDF:

1. Recheck admission circuit and active-task immediately before upload.
2. Upload exactly one PDF.
3. Observe task list, task detail, browser console, and canonical endpoints until terminal state or clear systemic failure.
4. Recheck admission circuit, active-task, direct MinerU health, and dependency-health at terminal state.
5. Do not start the next upload until the prior task has reached terminal state and runtime surfaces are clean.

Maximum uploads: `3`.

Minimum uploads: stop early if:

- no safe additional PDF exists;
- preflight fails;
- any upload hits systemic failure;
- runtime no longer becomes clean after a terminal state;
- completing another upload would require forbidden operations.

## Sample Selection

Select up to 3 PDFs from:

`/Users/concm/prod_workspace/Luceon2026/testpdf`

Prefer samples distinct from Task 126's sample (`走向成功_英语_二模卷16篇.pdf`) unless the directory lacks enough suitable alternatives.

For each selected sample, record:

- absolute path;
- file size;
- SHA-256 hash;
- why it is suitable for small serial validation.

Do not modify, move, rename, copy, delete, or truncate sample files.

## Required Observations For Each Upload

Capture enough evidence to answer:

1. Does task detail show `当前进展`?
2. During MinerU processing, does task detail show fine-grained MinerU progress?
3. Does task list show consistent fine-grained MinerU progress for the same task?
4. Does browser console show warning/error events or dependency-repair HTTP 503 responses?
5. Does `/__proxy/upload/ops/dependency-repair/status` stay HTTP 200 structured status?
6. Do log-channel/global-observation surfaces capture fresh attributable progress during processing?
7. Does final task/material/MinerU/AI state become coherent?
8. Does runtime return to clean idle state before any next upload?

Recommended read-only endpoints:

- `/__proxy/upload/ops/mineru/active-task`
- `/__proxy/upload/ops/mineru/admission-circuit`
- `/__proxy/upload/ops/mineru/log-channel-ownership`
- `/__proxy/upload/ops/mineru/global-observation`
- `/__proxy/upload/ops/dependency-health?ollamaChatProbe=true`
- `/__proxy/upload/ops/dependency-repair/status`

## Forbidden Scope

Do not:

- upload more than 3 PDFs;
- run concurrent uploads;
- run pressure, batch-concurrent, soak, or long-run validation;
- repair failed tasks;
- reparse or re-AI;
- cleanup, delete, or mutate historical tasks/materials/files;
- directly mutate DB/MinIO;
- run `docker compose down`, `docker compose down -v`, or Docker volume/data cleanup;
- start, stop, restart, kill, attach, or mutate MinerU/Ollama/supervisor;
- pull/delete/replace models;
- mutate config, secrets, samples, PRD truth, role contracts, project state, or handoff;
- declare L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.

## GitHub / Repository Rules

Do not run `git fetch`, `git pull`, or `git push` unless Director separately instructs you to do so.

Because this is a role-thread validation task in a shared workspace, write the report and update `TaskAndReport/TASK_TRACKING_LIST.md` locally. Director will handle GitHub synchronization after review if needed.

If local task ledger does not contain this task, report `本地任务列表未更新/疑似不同步` and stop rather than guessing.

## Required Report

Write:

`TaskAndReport/2026-05-14T12-58-14+0800_P1-Small-Serial-Validation-After-Task-Detail-Progress-Pass_REPORT.md`

The report must include:

- exact task brief path;
- required reading completed;
- global preflight evidence;
- per-sample path, size, SHA-256;
- exact upload count, maximum 3;
- per-upload task/material/MinerU/AI identifiers;
- per-upload task list/detail progress observations;
- per-upload `当前进展` evidence;
- per-upload browser console and HTTP 503 evidence;
- per-upload endpoint observations during processing and terminal state;
- final runtime idle evidence after the last upload or stop condition;
- commands run and exit codes;
- skipped checks and exact reasons;
- stop condition if fewer than 3 uploads were run;
- risks/blockers/residual debt;
- explicit statement that no concurrent upload, pressure/batch/soak, cleanup, repair/reparse/re-AI, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, model/config/secret/sample mutation, readiness, L3, pressure PASS, release-readiness, or go-live claim was made.

Update row 128 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated.
