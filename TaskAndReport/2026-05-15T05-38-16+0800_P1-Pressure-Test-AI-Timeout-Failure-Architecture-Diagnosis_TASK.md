# Task Brief: P1 Pressure Test AI Timeout Failure Architecture Diagnosis

- Task ID: `TASK-20260515-053816-P1-Pressure-Test-AI-Timeout-Failure-Architecture-Diagnosis`
- Created: 2026-05-15T05:38:16+0800
- Created by: Director
- Assigned role: `Architect`
- Expected report: `TaskAndReport/2026-05-15T05-38-16+0800_P1-Pressure-Test-AI-Timeout-Failure-Architecture-Diagnosis_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-15T05-38-16+0800_P1-Manual-Pressure-Test-Read-Only-Monitoring_DIRECTOR_REVIEW.md`

## Context

Task 151 monitored a user-submitted pressure test of `24` mixed-size PDFs. The pressure test failed by task criteria:

- `20` pressure tasks reached `review-pending/review`;
- `3` pressure tasks reached terminal `failed/ai`;
- `1` pressure task remained `running/mineru-processing` at Director review time;
- AI failures were Ollama / AI timeout failures under strict no-skeleton-fallback mode;
- strict mode correctly blocked skeleton fallback;
- MinerU remained active and direct MinerU `/health` reported no MinerU task failures;
- Docker services remained healthy enough for monitoring;
- dependency-health repeatedly timed out during monitoring, while direct Ollama `/api/version` and `/api/ps` remained reachable and `qwen3.5:9b` stayed resident.

This is a route-analysis task. Do not implement code. Do not repair failed tasks. Do not mutate production.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/PROJECT_STATE.md`
4. `docs/codex/HANDOFF.md`
5. `docs/prd/Luceon2026-PRD-v0.4.md`
6. `docs/codex/TEST_POLICY.md`
7. `docs/codex/REPOSITORY_STRUCTURE.md`
8. `TaskAndReport/README.md`
9. `TaskAndReport/TASK_TRACKING_LIST.md`
10. this task brief
11. `TaskAndReport/2026-05-14T21-20-55+0800_P1-Manual-Pressure-Test-Read-Only-Monitoring_REPORT.md`
12. `TaskAndReport/2026-05-14T21-20-55+0800_P1-Manual-Pressure-Test-Read-Only-Monitoring_NOTES.md`
13. `TaskAndReport/2026-05-15T05-38-16+0800_P1-Manual-Pressure-Test-Read-Only-Monitoring_DIRECTOR_REVIEW.md`

If `docs/codex/roles/architect.md` is missing locally, do not stop solely because of that missing file. Use this task brief plus `AGENTS.md`, `TEAM_CONTRACT.md`, and `TaskAndReport/README.md` as controlling context. Stop only if the task row or this task brief is missing locally.

## Workspaces And Runtime Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production UI: `http://localhost:8081/cms/`
- Upload proxy base: `http://localhost:8081/__proxy/upload`
- DB proxy base: `http://localhost:8081/__proxy/db`
- MinerU endpoint: `http://127.0.0.1:8083`
- Ollama endpoint: `http://127.0.0.1:11434` on host, `http://host.docker.internal:11434` from containers

## Objective

Produce a read-only architecture diagnosis and remediation plan for the pressure-test AI timeout failures.

The report must answer:

1. What exactly failed during the pressure test?
2. Which subsystem owns each failure signal: upload worker, MinerU, Ollama, AI metadata worker, dependency-health, or UI observation?
3. Why could direct Ollama `/api/ps` show the model resident while dependency-health and AI provider calls still timed out?
4. Is the current AI timeout boundary appropriate for long-run pressure execution on this single machine?
5. Is the current dependency-health semantics useful during active pressure work, or does it add noise / extra load / misleading blocking signals?
6. Does strict no-skeleton fallback behave correctly, and what retry policy is allowed without weakening that guardrail?
7. What should happen to failed AI tasks and the remaining active MinerU task after a pressure failure?
8. What implementation tasks, if any, should be dispatched next, in what order, and with what acceptance criteria?

## Scope

Allowed:

- read source code, tests, configs, task reports, and runtime evidence;
- run read-only commands in development and production workspaces;
- query read-only HTTP endpoints;
- inspect current production task/material/AI job states;
- inspect logs read-only;
- write the required architecture report and update this task row.

Forbidden:

- code changes;
- production deployment;
- failed-task repair;
- retry/reparse/re-AI;
- direct DB or MinIO mutation;
- Docker restart/rebuild/down/volume cleanup;
- MinerU/Ollama/supervisor start/stop/restart/kill/attach/mutation;
- model pull/delete/replace;
- config/secret/sample mutation;
- declaring pressure PASS, L3, release readiness, production readiness, go-live readiness, or production上线.

## Analysis Focus

Inspect at least:

- `server/services/ai/metadata-worker.mjs`
- AI provider timeout configuration and retry/error classification paths;
- Ollama provider call timeout and keep_alive behavior;
- dependency-health implementation and timeout behavior;
- parse task / AI job transition logic;
- Task 151 report and monitoring notes;
- current states for failed tasks:
  - `task-1778765409131`
  - `task-1778765412523`
  - `task-1778765415701`
- current state for remaining running task:
  - `task-1778765417422`

## Required Report

Write:

`TaskAndReport/2026-05-15T05-38-16+0800_P1-Pressure-Test-AI-Timeout-Failure-Architecture-Diagnosis_REPORT.md`

The report must include:

- exact task brief path;
- required reading completed;
- read-only commands/endpoints used and exit codes;
- current pressure-run state at analysis time;
- failure timeline and owning subsystem classification;
- root-cause hypothesis with evidence strength;
- alternative hypotheses and why they are weaker or still open;
- recommended remediation route;
- explicit implementation task proposals, if any;
- test/validation acceptance criteria for each proposal;
- risks/blockers/residual debt;
- explicit statement that no code, repair, retry, reparse, re-AI, mutation, restart, deployment, readiness, L3, pressure PASS, release, or go-live action was performed.

Update row 152 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- `Status=已回报待 Director 审查`
- `Next Actor=Director`
- report path populated.

Do not push to GitHub from the Architect thread unless Director explicitly instructs it.
