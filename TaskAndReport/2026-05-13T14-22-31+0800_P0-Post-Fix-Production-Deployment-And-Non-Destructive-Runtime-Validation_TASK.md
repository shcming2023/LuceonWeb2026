# Task: P0 Post Fix Production Deployment And Non Destructive Runtime Validation

Assignee:
DevelopmentEngineer

Issued by:
Director

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-13T14-22-31+0800_P0-Post-Fix-Production-Deployment-And-Non-Destructive-Runtime-Validation_TASK.md

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
- TaskAndReport/2026-05-13T13-58-10+0800_P0-Post-Validation-Ollama-And-MinerU-Progress-Blockers_TASK.md
- TaskAndReport/2026-05-13T13-58-10+0800_P0-Post-Validation-Ollama-And-MinerU-Progress-Blockers_REPORT.md
- TaskAndReport/2026-05-13T14-18-12+0800_P0-Post-Validation-Ollama-And-MinerU-Progress-Blockers_DIRECTOR_REVIEW.md
- TaskAndReport/2026-05-13T14-18-12+0800_P0-Post-Fix-Production-Deployment-And-One-Upload-Validation-Authorization_DECISION.md

## Background

Task 87 was accepted at code/test level and merged to GitHub `main` at:

`8d99ca5 Review Ollama MinerU blocker fixes`

Accepted code/test facts:

- Ollama real metadata inference timeout now aligns headers/body/abort deadlines to provider `timeoutMs`.
- Dependency-health smoke remains a separate short bounded check.
- MinerU adapters import the real shared log parser path.
- Fast completed tasks can expose structured `fast-complete-no-business-signal` diagnostics without fabricated page/batch/phase progress.
- Director independently reran focused checks in a clean detached worktree.

The user approved Option A at `2026-05-13T14:22:31+0800`: scoped production deployment plus exactly one later controlled upload validation. This task is only the deployment and non-destructive runtime-validation half. The later upload validation must be separately dispatched after this task reports back and Director reviews it.

## Objective

Apply the accepted Task 87 code path to the production deployment with the minimum necessary production change, then verify non-destructive runtime surfaces are healthy enough to authorize a later one-upload validation task.

## Non-Goals

- Do not perform a validation upload.
- Do not run pressure testing or 24-PDF retry.
- Do not repair, retry, reparse, re-AI, mutate, or clean up historical failed tasks.
- Do not delete or mutate DB rows, MinIO objects, Docker volumes, logs, or sample files.
- Do not restart MinerU, Ollama, MinIO, or DB unless a preflight blocker proves the task cannot proceed and Director separately authorizes it.
- Do not pull, delete, replace, reload, or change models.
- Do not change secrets, production overrides, PRD truth, role contracts, or release judgments.
- Do not claim production release readiness, L3, pressure PASS, or full acceptance.

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
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
curl -sS --max-time 10 http://127.0.0.1:11434/api/ps
```

Stop and write a blocked report if preflight shows active/queued parse work, active/queued AI work, takeover-required work, dependency blocking, or an unsafe production state.

## Allowed Production Operations

Only after preflight is safe:

- synchronize production path to GitHub `main` using non-destructive Git commands:

```bash
git fetch origin
git pull --ff-only origin main
git log -1 --oneline
```

- rebuild/recreate only the minimum necessary service for the Task 87 server code path, expected:

```bash
docker compose up -d --build cms-upload-server
```

If local compose naming differs, use the minimum equivalent command and report it.

Do not run `docker compose down`, `docker compose down -v`, volume removal, prune, broad stack restart, model operations, DB/MinIO cleanup, or sample-file operations.

## Required Post-Deployment Validation

After deployment, collect:

```bash
git status --short --branch
git log -1 --oneline
docker compose ps
curl -fsS http://localhost:8081/__proxy/upload/health
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
curl -sS --max-time 10 http://127.0.0.1:11434/api/ps
```

Also verify production runtime has the accepted Task 87 source behavior available, for example by checking the deployed production source or container image build context for:

- `headersTimeoutMs` aligned to provider timeout rather than hard `30000`;
- `fast-complete-no-business-signal` diagnostic code present;
- MinerU adapter parser import path uses `../../lib/ops-mineru-log-parser.mjs`.

Do not create a new upload for this verification.

## Required Evidence

Report must include:

- confirmation that work was based on this Director task brief;
- development HEAD and GitHub `main` HEAD observed;
- production HEAD before and after deployment;
- production local override status before and after deployment;
- exact production commands and exit codes;
- runtime health/dependency/admission/active-task/Ollama evidence before and after deployment;
- proof that only the minimum necessary service was rebuilt/recreated;
- proof that DB, MinIO, MinerU, Ollama, Docker volumes, sample files, and historical failed tasks were not mutated by this task;
- skipped checks and reasons;
- risks, blockers, residual debt;
- recommendation whether Director should issue the follow-up one-upload TestAcceptanceEngineer validation task.

## GitHub Sync Requirements

- Do not create implementation code changes in this task.
- If only the report and task ledger are changed, commit and push those report records to GitHub.
- Do not overwrite unrelated dirty files in the development workspace.

## Completion Report Storage Requirements

- Write the completion report into `TaskAndReport/` using this naming rule:
  `2026-05-13T14-22-31+0800_P0-Post-Fix-Production-Deployment-And-Non-Destructive-Runtime-Validation_REPORT.md`
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, production HEAD, deployment evidence, status, `Next Actor=Director`, next action, and required output.

## Acceptance Criteria

- Production path is fast-forwarded to the accepted Task 87 code path.
- Minimum necessary service rebuild/recreate is completed without broad restart or destructive operations.
- Runtime health, dependency-health with MinerU submit probe, admission circuit, active-task diagnostics, and Ollama residency/readiness surfaces are non-blocking after deployment.
- No upload, pressure test, failed-task repair, cleanup, destructive mutation, model operation, L3, pressure PASS, or release-readiness claim occurs.
- Report gives Director enough evidence to decide whether to dispatch exactly one controlled TestAcceptanceEngineer upload validation.
