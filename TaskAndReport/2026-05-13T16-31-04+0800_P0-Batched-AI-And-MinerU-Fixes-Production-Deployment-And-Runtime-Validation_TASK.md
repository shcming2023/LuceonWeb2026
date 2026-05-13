# Task: P0 Batched AI And MinerU Fixes Production Deployment And Runtime Validation

Assignee:
DevelopmentEngineer

Issued by:
Director

Issued at:
2026-05-13T16:31:04+0800

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-13T16-31-04+0800_P0-Batched-AI-And-MinerU-Fixes-Production-Deployment-And-Runtime-Validation_TASK.md

Expected report:
TaskAndReport/2026-05-13T16-31-04+0800_P0-Batched-AI-And-MinerU-Fixes-Production-Deployment-And-Runtime-Validation_REPORT.md

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
- TaskAndReport/2026-05-13T15-17-15+0800_P0-AI-Metadata-Single-Pass-Finalization-Guard_REPORT.md
- TaskAndReport/2026-05-13T15-34-48+0800_P0-AI-Metadata-Single-Pass-Finalization-Guard_DIRECTOR_REVIEW.md
- TaskAndReport/2026-05-13T15-34-48+0800_P1-Terminal-MinerU-Diagnostic-Precedence_REPORT.md
- TaskAndReport/2026-05-13T16-31-04+0800_P1-Terminal-MinerU-Diagnostic-Precedence_DIRECTOR_REVIEW.md

## Background

Task 91 was accepted at code/test level:

- AI metadata worker no longer processes the same pending job twice in one scan cycle through a stale pre-recovery snapshot.
- Strict no-skeleton behavior remains unchanged.

Task 93 was accepted at code/test level:

- task-page/operator semantics prefer terminal MinerU completion diagnostics over stale/unreadable in-flight wording when MinerU is completed and parsed artifact evidence exists.
- No page/batch/phase progress is fabricated.
- AI failure remains visible separately.

Neither accepted fix has been deployed to production yet. This task deploys both together to reduce production churn.

## Objective

Apply accepted Task 91 and Task 93 code paths to production with the minimum necessary service rebuild/recreate, then verify non-destructive runtime surfaces are healthy.

This task is deployment/runtime-validation only. It does not authorize any upload.

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

Stop and write a blocked report if preflight shows dependency blocking, admission circuit open, active/current/queued/takeover-required parse or AI work, unsafe production state, or production local overrides that would be overwritten.

## Allowed Production Operations

Only after safe preflight:

```bash
git fetch origin
git pull --ff-only origin main
git log -1 --oneline
```

Then rebuild/recreate only the minimum services needed for the accepted code paths:

- upload server, because Task 91 changes `server/services/ai/metadata-worker.mjs`;
- frontend, because Task 93 changes `src/app/utils/taskView.ts`.

Expected command:

```bash
docker compose up -d --build upload-server cms-frontend
```

If compose service names differ in production, use the minimum equivalent command and report the exact service names.

Do not run `docker compose down`, `docker compose down -v`, volume removal, prune, broad stack restart, model operations, DB/MinIO cleanup, sample-file operations, failed-task repair, reparse, re-AI, or upload.

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
curl -fsS -I http://localhost:8081/cms/
```

Also verify production source contains the accepted markers:

- `getJobById` latest-state guard and single-job return in `server/services/ai/metadata-worker.mjs`;
- `deriveTerminalMineruCompletionLine` or equivalent terminal diagnostic precedence in `src/app/utils/taskView.ts`;
- focused tests exist in production source:
  - `server/tests/ai-metadata-single-pass-guard-smoke.mjs`
  - `server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs`

Do not create a new upload for this verification.

## Required Evidence

Report must include:

- confirmation that work was based on this Director task brief;
- development HEAD and GitHub `main` HEAD observed;
- production HEAD before and after deployment;
- production local override status before and after deployment;
- exact production commands and exit codes;
- runtime health/dependency/admission/active-task/Ollama/frontend evidence before and after deployment;
- proof that only the minimum necessary services were rebuilt/recreated;
- proof that DB, MinIO, MinerU, Ollama, Docker volumes, sample files, and historical failed tasks were not mutated by this task;
- skipped checks and reasons;
- risks, blockers, residual debt;
- recommendation whether Director should issue a later exactly-one-upload validation task.

## GitHub Sync Requirements

- Do not create new implementation code changes in this task.
- If only the report and task ledger are changed, commit and push those report records to GitHub.
- Do not overwrite unrelated dirty files in the development workspace.

## Completion Report Storage Requirements

Write:

`TaskAndReport/2026-05-13T16-31-04+0800_P0-Batched-AI-And-MinerU-Fixes-Production-Deployment-And-Runtime-Validation_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, production HEAD, deployment evidence, status, `Next Actor=Director`, next action, and required output.

## Acceptance Criteria

- Production path is fast-forwarded to the accepted Task 91 and Task 93 code paths.
- Minimum necessary service rebuild/recreate is completed without broad restart or destructive operations.
- Upload health, dependency-health with MinerU submit probe and Ollama chat probe, admission circuit, active-task diagnostics, Ollama residency/chat readiness, and frontend `/cms/` surface are non-blocking after deployment.
- No upload, pressure test, failed-task repair, cleanup, destructive mutation, model operation, L3, pressure PASS, or release-readiness claim occurs.
- Report gives Director enough evidence to decide whether to dispatch exactly one controlled upload validation later.
