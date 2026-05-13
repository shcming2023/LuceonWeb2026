# Task: P0 AI JSON Repair Production Deployment And Runtime Validation

Assignee:
DevelopmentEngineer

Issued by:
Director

Issued at:
2026-05-13T19:26:01+0800

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-13T19-26-01+0800_P0-AI-JSON-Repair-Production-Deployment-And-Runtime-Validation_TASK.md

Expected report:
TaskAndReport/2026-05-13T19-26-01+0800_P0-AI-JSON-Repair-Production-Deployment-And-Runtime-Validation_REPORT.md

## Required Reading Before Execution

- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/development-engineer.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- docs/codex/TEST_POLICY.md
- docs/codex/TEST_MATRIX.md
- docs/codex/REPOSITORY_STRUCTURE.md
- docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md
- TaskAndReport/README.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-13T19-13-44+0800_P0-AI-Metadata-JSON-Repair-And-Schema-Reliability_REPORT.md
- TaskAndReport/2026-05-13T19-26-01+0800_P0-AI-Metadata-JSON-Repair-And-Schema-Reliability_DIRECTOR_REVIEW.md

## Background

Task 96 is accepted at code/test level.

Accepted code path:

- deterministic repair for invalid JSON string escapes inside provider/worker JSON parsing;
- specifically covers Task 95's LaTeX evidence escape shape such as `\sqcap`, `\angle`, and `\circ`;
- strict no-skeleton semantics remain unchanged.

Production currently does not yet have this accepted code path deployed.

This task deploys the accepted Task 96 code path to production and verifies non-destructive runtime surfaces only.

## Objective

Fast-forward production to the accepted GitHub `main` code path and rebuild/recreate only the minimum service required for the AI metadata JSON repair code.

Then verify runtime health and code markers without creating a new upload.

## Required Preflight

In development workspace:

```bash
git status --short --branch
git log -1 --oneline
git ls-remote origin refs/heads/main
```

In production deployment path before deployment:

```bash
git status --short --branch
git log -1 --oneline
docker compose ps
curl -fsS http://localhost:8081/__proxy/upload/health
curl -sS --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=1&ollamaChatProbe=1'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
curl -sS --max-time 10 http://127.0.0.1:11434/api/ps
```

Stop and write a blocked report if preflight shows:

- dependency blocking;
- admission circuit open;
- active/current/queued/takeover-required parse or AI work;
- unsafe production state;
- production local overrides that would be overwritten;
- Docker services unhealthy;
- GitHub `main` not containing the accepted Task 96 code path.

## Allowed Production Operations

Only after safe preflight:

```bash
git fetch origin
git pull --ff-only origin main
git log -1 --oneline
```

Then rebuild/recreate only the minimum service needed for the accepted code path:

```bash
docker compose up -d --build upload-server
```

If Docker Compose recreates dependency services as a side effect, report the exact services and post-health evidence. Do not broaden the command yourself.

Do not run `docker compose down`, `docker compose down -v`, volume removal, prune, broad stack restart, rollback, model operations, DB/MinIO cleanup, sample-file operations, failed-task repair, reparse, re-AI, or upload.

## Required Post-Deployment Validation

After deployment, collect:

```bash
git status --short --branch
git log -1 --oneline
docker compose ps
curl -fsS http://localhost:8081/__proxy/upload/health
curl -sS --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=1&ollamaChatProbe=1'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
curl -sS --max-time 10 http://127.0.0.1:11434/api/ps
```

Also verify production source/container markers:

- `repairInvalidJsonStringEscapes` exists in `server/services/ai/providers/base.mjs`;
- `metadata-worker.mjs` imports and uses `repairInvalidJsonStringEscapes`;
- `server/tests/ai-metadata-repair-hardening-smoke.mjs` includes the invalid LaTeX escape regression case;
- upload-server container includes the same markers under `/app/server/services/ai/...`.

Do not create a validation upload in this task.

## Required Evidence

Report must include:

- confirmation that work was based on this Director task brief;
- development HEAD and GitHub `main` HEAD observed;
- production HEAD before and after deployment;
- production local override status before and after deployment;
- exact production commands and exit codes;
- runtime health/dependency/admission/active-task/Ollama evidence before and after deployment;
- proof that only the minimum necessary service was targeted;
- any Compose dependency side effects, if present;
- proof that DB, MinIO, MinerU, Ollama, Docker volumes, sample files, and historical failed tasks were not mutated by this task;
- skipped checks and reasons;
- risks, blockers, residual debt;
- recommendation whether Director should issue a later exactly-one controlled upload validation task.

## Completion Report Storage Requirements

Write:

`TaskAndReport/2026-05-13T19-26-01+0800_P0-AI-JSON-Repair-Production-Deployment-And-Runtime-Validation_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, production HEAD, deployment evidence, status, `Next Actor=Director`, next action, and required output.

Do not push to GitHub from the DevelopmentEngineer thread unless the task report and task ledger need to be recorded and the current Director/role convention explicitly permits it. Director can synchronize after review if needed.

## Forbidden Actions

Do not perform:

- upload;
- pressure/batch/soak/24-PDF validation;
- failed-task repair, reparse, or re-AI;
- DB, MinIO, Docker volume/data cleanup or mutation;
- Docker `down`, `down -v`, prune, broad restart, rollback;
- model pull/delete/replace/restart/reload;
- secret, timeout, override, PRD, role-contract, release truth, or public API mutation;
- sample mutation or sample copy into the repository;
- L3, pressure PASS, production-readiness, or release-readiness claim.

## Acceptance Criteria

- Production path is fast-forwarded to the accepted Task 96 code path.
- Minimum necessary upload-server rebuild/recreate completes without broad destructive operations.
- Upload health, dependency-health with MinerU submit probe and Ollama chat probe, admission circuit, active-task diagnostics, and Ollama residency/chat readiness are non-blocking after deployment.
- Accepted code markers are present in production source/container.
- No upload, pressure test, failed-task repair, cleanup, destructive mutation, model operation, L3, pressure PASS, or release-readiness claim occurs.
- Report gives Director enough evidence to decide whether to dispatch exactly one controlled upload validation later.
