# TASK-20260514-045338-P1-MinerU-Observation-Hardening-Production-Deployment-And-Runtime-Validation

Task:
P1 MinerU Observation Hardening Production Deployment And Runtime Validation

Assignee:
DevelopmentEngineer

Issued by:
Director

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-14T04-53-38+0800_P1-MinerU-Observation-Hardening-Production-Deployment-And-Runtime-Validation_TASK.md`

Expected completion report:
`TaskAndReport/2026-05-14T04-53-38+0800_P1-MinerU-Observation-Hardening-Production-Deployment-And-Runtime-Validation_REPORT.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- This task brief
- Task 101 report and Director review:
  - `TaskAndReport/2026-05-13T20-19-44+0800_P1-MinerU-Processing-Log-Observation-Adjudication-Hardening_REPORT.md`
  - `TaskAndReport/2026-05-14T04-53-38+0800_P1-MinerU-Processing-Log-Observation-Adjudication-Hardening_DIRECTOR_REVIEW.md`

## Background

Task 101 was accepted at code/test level. It hardens the local MinerU adapter so unreadable/stale log observation while MinerU API is still queued/pending/processing/running is recorded as diagnostic warning metadata instead of causing a terminal failed state.

Production is not yet validated on this code path. The current production deployment previously ran at `de2d23f`; the development repository now includes the accepted Task 101 code and this task record.

## Objective

Apply the accepted Task 101 code path to the production deployment with the minimum necessary scope and perform non-destructive runtime validation.

## Allowed Operations

- In the development workspace:
  - inspect branch/status/HEAD;
  - verify that the accepted Task 101 commit is present.
- In the production deployment path:
  - check for active parse/AI work before any deployment;
  - `git status --short --branch`;
  - `git fetch origin`;
  - `git pull --ff-only origin main`;
  - run the minimum necessary upload-server deployment command, expected:
    - `docker compose up -d --build upload-server`
  - inspect `docker compose ps`;
  - read logs only as needed.
- Runtime checks:
  - upload health;
  - dependency-health with `mineruSubmitProbe=true` and Ollama chat probe when available;
  - `/ops/mineru/admission-circuit`;
  - `/ops/mineru/active-task`;
  - source/container marker checks proving `buildNonTerminalMineruLogObservationWarning` and `mineruLogObservationWarning` are present in the deployed upload-server code.

## Forbidden Operations

- Do not upload validation PDFs.
- Do not run pressure, batch-concurrent, soak, broad stress, or long-run tests.
- Do not repair, reparse, re-AI, retry, clean up, delete, rename, or mutate historical tasks/materials/artifacts.
- Do not mutate DB/MinIO/Docker volumes/data or sample files.
- Do not run `docker compose down`, `docker compose down -v`, volume deletion, DB reset, MinIO cleanup, model pull/delete/replace, broad restart, or rollback.
- Do not change PRD truth, role contracts, release docs, secrets, model settings, environment settings, or unrelated files.
- Do not declare L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.

## Pre-deployment Stop Conditions

Before deployment, stop and write a blocked report if:

- active parse or AI work exists;
- admission circuit is open;
- dependency-health is blocking;
- core Docker services are unhealthy;
- production worktree cannot fast-forward cleanly;
- deployment would require destructive cleanup, restart beyond the scoped upload-server rebuild, or manual repair.

## Required Checks And Evidence

Record commands and exit codes for:

- development workspace `git status --short --branch` and `git log -1 --oneline`;
- production workspace `git status --short --branch` and `git log -1 --oneline` before and after pull;
- pre-deployment active-task and admission-circuit checks;
- pre-deployment dependency-health;
- exact deployment command and exit code;
- `docker compose ps`;
- post-deployment upload health;
- post-deployment dependency-health with MinerU submit probe and Ollama chat probe if available;
- post-deployment admission-circuit and active-task checks;
- source/container marker checks for Task 101 code path.

## Completion Report Requirements

Write the report to:

`TaskAndReport/2026-05-14T04-53-38+0800_P1-MinerU-Observation-Hardening-Production-Deployment-And-Runtime-Validation_REPORT.md`

Then update only Task 102 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- `Status=已回报待 Director 审查` if completed;
- `Status=挂起` if blocked;
- `Next Actor=Director`;
- include production HEAD, deployment command, health/admission/active-task result, and whether source/container markers were confirmed.

Do not push to GitHub from the production workspace. If repository files are changed in the development workspace, report them exactly; no additional development code change is expected.

## Acceptance Criteria

Task 102 can be accepted if:

- production fast-forwards cleanly to the accepted Task 101 code path;
- the scoped upload-server deployment succeeds;
- post-deployment health and dependency checks are non-blocking;
- admission circuit and active-task surfaces are clean;
- Task 101 code markers are present in deployed source/container code;
- no forbidden operation or readiness claim is performed.
