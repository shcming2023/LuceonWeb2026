# Task Brief: P1 Task Detail Progress Hardening Production Deployment And Read-Only Runtime Validation

- Task ID: `TASK-20260514-121702-P1-Task-Detail-Progress-Hardening-Production-Deployment-And-Read-Only-Runtime-Validation`
- Created: 2026-05-14T12:17:02+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-14T12-17-02+0800_P1-Task-Detail-Progress-Hardening-Production-Deployment-And-Read-Only-Runtime-Validation_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-14T12-17-02+0800_P1-Task-Detail-MinerU-Progress-And-Console-Noise-Hardening_DIRECTOR_REVIEW.md`

## Context

Task 123 was accepted at code/test level. The accepted code:

- makes the task detail overview use the same shared MinerU progress helpers as the task list;
- changes the overview progress label to `当前进展`;
- preserves raw task message as secondary text when a semantic MinerU progress line is present;
- changes the read-only `/ops/dependency-repair/status` unavailable-supervisor response from HTTP `503` to HTTP `200` with structured `SUPERVISOR_UNAVAILABLE` status;
- keeps POST repair-action HTTP `503` semantics for real action failures.

The code is now integrated into `origin/main` by the Director review commit, but it has not been deployed to production.

## Objective

Deploy the accepted Task 123 code path to production with the minimum necessary service rebuild, then run read-only runtime validation.

This task must not create uploads or claim readiness. It only validates that the deployed runtime surfaces are healthy and that the supervisor-status read-only route no longer produces an HTTP `503` for expected supervisor absence.

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
11. `TaskAndReport/2026-05-14T11-59-22+0800_P1-Task-Detail-MinerU-Progress-And-Console-Noise-Hardening_REPORT.md`
12. `TaskAndReport/2026-05-14T12-17-02+0800_P1-Task-Detail-MinerU-Progress-And-Console-Noise-Hardening_DIRECTOR_REVIEW.md`

## Allowed Scope

In production:

- inspect status and active work;
- fast-forward production to current `origin/main`;
- rebuild/recreate only the minimum necessary services for the accepted frontend/upload-server code path:

```bash
docker compose up -d --build upload-server cms-frontend
```

If Compose recreates dependency containers as a side effect, record it. Do not use Docker down/down-v or volume/data cleanup.

## Mandatory Preflight

Stop and write a blocked report if:

- production worktree cannot fast-forward cleanly;
- active parse or AI work exists;
- admission circuit is open;
- dependency-health is blocking;
- Docker core services are unhealthy;
- direct MinerU health is unhealthy;
- `luceon-mineru` or `luceon-sidecar` ownership is absent or ambiguous;
- completion would require PDF upload, data mutation, Docker down/down-v, volume cleanup, MinerU/Ollama/supervisor mutation, model/config/secret/sample mutation, repair/reparse/re-AI, or broad rollback.

## Required Validation

After deployment, verify and report:

- production `git status --short --branch` and `git log -1 --oneline`;
- `docker compose ps`;
- upload health;
- frontend `/cms/` HTTP 200;
- dependency-health `ok=true`, `blocking=false`;
- admission circuit closed through `/__proxy/upload/ops/mineru/admission-circuit`;
- active-task idle through `/__proxy/upload/ops/mineru/active-task`;
- direct MinerU `/health` healthy;
- `tmux ls` still includes `luceon-mineru` and `luceon-sidecar`;
- port `8083` still has exactly one listener with cwd/log fd evidence matching production/ops logs;
- `/__proxy/upload/ops/dependency-repair/status` returns HTTP `200` with structured `SUPERVISOR_UNAVAILABLE` when the supervisor is absent, or HTTP `200` with real status if it is running;
- POST repair-action failure semantics are not changed by runtime validation; do not invoke POST actions unless explicitly authorized. They are not authorized by this task.

Optional, read-only browser validation:

- Open an existing task detail page and confirm the overview label is `当前进展`.
- Do not create a new upload for this task.

## Forbidden Scope

Do not:

- upload any PDF;
- run pressure, batch, soak, or long-run validation;
- repair, reparse, re-AI, cleanup, or mutate historical tasks/materials;
- mutate DB/MinIO records directly;
- run Docker down/down-v or Docker volume/data cleanup;
- mutate MinerU/Ollama/supervisor state;
- attach/start `luceon-supervisor`;
- change secrets, config, models, samples, PRD truth, role contracts, project state, or handoff;
- delete, truncate, rename, or edit log files;
- declare L3, production readiness, release readiness, pressure PASS, go-live readiness, or production上线.

## Required Report

Write the expected report with:

- exact task brief path;
- production preflight evidence;
- deployment command and exit code;
- production HEAD after deployment;
- services recreated by Compose;
- runtime validation evidence;
- supervisor-status route HTTP status/body summary;
- skipped checks and exact reasons;
- residual risk/debt;
- explicit statement that no upload, pressure/batch/soak, cleanup, repair/reparse/re-AI, DB/MinIO data mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, readiness, L3, pressure PASS, or go-live claim was made.

Update `TaskAndReport/TASK_TRACKING_LIST.md` so this row becomes `已回报待 Director 审查` with `Next Actor=Director`, and include the report path.
