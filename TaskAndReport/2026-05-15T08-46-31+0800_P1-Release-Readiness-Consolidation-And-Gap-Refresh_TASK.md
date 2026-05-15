# Task Brief: P1 Release Readiness Consolidation And Gap Refresh

- Task ID: `TASK-20260515-084631-P1-Release-Readiness-Consolidation-And-Gap-Refresh`
- Created: 2026-05-15T08:46:31+0800
- Created by: Director
- Assigned role: `Architect`
- Expected report: `TaskAndReport/2026-05-15T08-46-31+0800_P1-Release-Readiness-Consolidation-And-Gap-Refresh_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-15T08-19-40+0800_P1-Next-Step-After-Pressure-Semantics-Acceptance_DECISION.md`
- Based on accepted pressure-semantics review: `TaskAndReport/2026-05-15T08-19-40+0800_P1-Pressure-Semantics-Production-Read-Only-Acceptance-Review_DIRECTOR_REVIEW.md`

## Context

The pressure-semantics stream has reached a bounded acceptance point:

- Task 157 implemented pressure-result and task-page semantic corrections.
- Task 159 deployed those corrections to production and passed read-only deployment validation.
- Task 160 independently accepted the deployed semantics within read-only scope.
- The recent manual pressure window is now understood as mixed task outcomes rather than whole-run/systemic failure:
  - `24` pressure-window tasks;
  - `21 review-pending/review`;
  - `3 failed/ai`.

The project still needs a consolidated release-readiness/gap refresh before any owner-level decision about production readiness or go-live. This task is intentionally read-only and analytical.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/architect.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/prd/Luceon2026-Stability-PRD-v0.1.md` if present
8. `docs/codex/TEST_POLICY.md`
9. `docs/codex/REPOSITORY_STRUCTURE.md`
10. `TaskAndReport/README.md`
11. `TaskAndReport/TASK_TRACKING_LIST.md`
12. Task 157 task/report/Director review
13. Task 159 task/report/Director review
14. Task 160 task/report/Director review
15. This task brief

If the task row, Architect role file, or required Task 157/159/160 evidence is missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`.

## Objective

Produce a read-only release-readiness consolidation/gap refresh that answers:

1. What evidence is currently accepted for the mainline flow `upload -> MinerU -> MinIO -> Ollama qwen3.5:9b -> AI metadata -> operator review`?
2. What remains blocking before production readiness can be considered?
3. What items are optional polish or technical debt rather than blockers?
4. What runtime/source-drift risks remain on the production machine?
5. What is the Architect's recommended next step: `NO_GO`, `CONDITIONAL_GO_AFTER_SPECIFIC_TASKS`, or `READY_FOR_USER_RELEASE_DECISION`?

The report must be explicit that the Architect recommendation is not itself a release-readiness declaration. Director/User own final readiness decisions.

## Allowed Operations

Allowed:

- read repository docs, code, task reports, and task ledger;
- run read-only Git status/HEAD checks in development and production;
- run read-only production HTTP checks only if useful:
  - upload health;
  - canonical dependency-health;
  - admission circuit;
  - active-task diagnostics;
  - direct MinerU `/health`;
  - `/cms/` or `/cms/tasks` HTTP status;
- inspect Docker status read-only with `docker compose ps`;
- write the Architect report and update row 162 locally.

## Forbidden Operations

Forbidden:

- PDF upload or any new validation artifact;
- pressure/batch/soak/fresh serial validation;
- cleanup, cancel, repair, retry, reparse, or re-AI;
- destructive DB, MinIO, Docker volume, Docker data, or local filesystem mutation;
- `docker compose down`, `docker compose down -v`, Docker volume/data cleanup, prune;
- service start/stop/restart/rebuild, including MinerU/Ollama/supervisor mutation;
- production deployment, fast-forward, rebuild, rollback, or config mutation;
- settings, secrets, config, model, or sample-library mutation;
- automatic retry/requeue;
- skeleton fallback weakening;
- PRD truth, role contract, project state, or handoff changes;
- declaring pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Required Analysis Structure

The report must include:

1. **Accepted Evidence Matrix**
   - code/test evidence;
   - production deployment evidence;
   - runtime read-only evidence;
   - controlled upload/serial/pressure evidence;
   - AI/Ollama evidence;
   - MinerU evidence;
   - MinIO/DB/frontend evidence.

2. **Current Release Blockers**
   - items that must be resolved before readiness can be claimed;
   - evidence gaps that prevent a final go/no-go decision.

3. **Non-Blocking Residual Debt / Polish**
   - items such as generic failed-AI wording or lack of dedicated pressure dashboard, if judged non-blocking.

4. **Production Source/Runtime Drift**
   - explicitly discuss known local modified files in production:
     - `.gitignore`
     - `docker-compose.override.yml`
     - `server/db-server.mjs`
     - `server/tests/worker-smoke.mjs`
     - `src/app/components/BatchUploadModal.tsx`
     - `src/app/pages/SourceMaterialsPage.tsx`
   - classify whether each is blocker, risk, expected override, or needs follow-up investigation.

5. **Go/No-Go Boundary**
   - one of:
     - `NO_GO`
     - `CONDITIONAL_GO_AFTER_SPECIFIC_TASKS`
     - `READY_FOR_USER_RELEASE_DECISION`
   - with concise reasons and specific next tasks if needed.

6. **Forbidden Operations Confirmation**
   - explicitly state no upload, pressure/batch/soak/fresh serial validation, cleanup/repair/reparse/re-AI, destructive mutation, service/config/secret/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, or readiness/go-live claim was made.

## Required Report

Write:

`TaskAndReport/2026-05-15T08-46-31+0800_P1-Release-Readiness-Consolidation-And-Gap-Refresh_REPORT.md`

Update row 162 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or precise blocked status;
- Next Actor: `Director`;
- Report path populated.
