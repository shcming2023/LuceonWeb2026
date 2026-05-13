# Task: P0 Exactly One Controlled Upload Validation After Task 87 Deployment

Assignee:
TestAcceptanceEngineer

Issued by:
Director

Issued at:
2026-05-13T14:46:20+0800

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

Production test PDF directory:
/Users/concm/prod_workspace/Luceon2026/testpdf

Exact authorized sample file:
/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-13T14-46-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment_TASK.md

Expected report:
TaskAndReport/2026-05-13T14-46-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment_REPORT.md

## Required Reading Before Execution

- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/test-acceptance-engineer.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- docs/codex/TEST_POLICY.md
- docs/codex/TEST_MATRIX.md
- docs/codex/REPOSITORY_STRUCTURE.md
- docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md
- TaskAndReport/README.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-13T13-41-16+0800_P0-Controlled-Live-Task-Progress-Semantics-Validation-With-Prod-Testpdf-Source_REPORT.md
- TaskAndReport/2026-05-13T13-58-10+0800_P0-Controlled-Live-Task-Progress-Semantics-Validation-With-Prod-Testpdf-Source_DIRECTOR_REVIEW.md
- TaskAndReport/2026-05-13T14-22-31+0800_P0-Post-Fix-Production-Deployment-And-Non-Destructive-Runtime-Validation_REPORT.md
- TaskAndReport/2026-05-13T14-46-20+0800_P0-Post-Fix-Production-Deployment-And-Non-Destructive-Runtime-Validation_DIRECTOR_REVIEW.md

## Background

Task 86 performed one controlled upload using the same sample file. MinerU completed and stored parsed artifacts, but the task page/API did not expose `mineruObservedProgress.progressSemantics`, and the AI stage failed because Ollama requests hit `UND_ERR_HEADERS_TIMEOUT` around 30 seconds despite a longer job timeout.

Task 87 fixed the accepted code-level blockers:

- Ollama real metadata inference now aligns headers/body/abort deadlines to provider `timeoutMs`;
- MinerU adapters import the real shared log parser;
- fast completed MinerU tasks can expose structured `fast-complete-no-business-signal` diagnostics without fabricating page/batch progress.

Task 89 deployed that code path to production and Director accepted non-destructive runtime validation. Production is at `51f21d0`, upload-server is healthy, dependency-health with MinerU submit probe and Ollama chat probe is non-blocking, admission circuit is closed, active-task diagnostics are empty, and `qwen3.5:9b` is resident.

The user approved Option A: one controlled upload after deployment validation. This task is that one upload validation.

## Objective

Run exactly one controlled production upload using the authorized sample file, then observe whether the deployed Task 87 fixes allow the task to progress through MinerU and AI with usable task-page/runtime semantics.

The most important validation target is not only final success. You must capture whether the task page/API exposes meaningful MinerU progress semantics or the new fast-complete diagnostic, and whether the Ollama AI stage avoids the previous `UND_ERR_HEADERS_TIMEOUT` failure.

## Local Runtime Context For TestAcceptanceEngineer

Production UI/API:

- UI base: `http://localhost:8081/cms/`
- upload proxy health: `http://localhost:8081/__proxy/upload/health`
- dependency health: `http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=1&ollamaChatProbe=1`
- admission circuit: `http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit`
- active task: `http://localhost:8081/__proxy/upload/ops/mineru/active-task`

Local dependencies:

- MinerU API is a host-side service reached from production upload-server as `http://host.docker.internal:8083`; from host checks, use `http://localhost:8083` when needed.
- Ollama is on `http://127.0.0.1:11434`; expected model is `qwen3.5:9b`; current keep-alive expectation is 24h.
- MinIO runs under Docker as `cms-minio`; console binding is local-only `127.0.0.1:19001:9001`.
- Docker compose production services include `cms-frontend`, `cms-upload-server`, `cms-db-server`, and `cms-minio`.

Use the production deployment path for production checks:

`/Users/concm/prod_workspace/Luceon2026`

Use the development workspace only for reading task records and writing the report:

`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

## Non-Goals And Hard Limits

- Do not upload any file except the exact authorized sample file.
- Do not upload more than once.
- Do not run pressure testing or 24-PDF retry.
- Do not repair, retry, reparse, re-AI, delete, mutate, or clean up historical failed tasks.
- Do not mutate DB rows, MinIO objects outside the single upload's natural artifacts, Docker volumes, logs, model files, secrets, production overrides, or sample files.
- Do not restart MinerU, Ollama, MinIO, DB, or the whole stack unless a blocker is found and Director separately authorizes it.
- Do not run `docker compose down`, `docker compose down -v`, volume removal, prune, model pull/delete/replace/reload, broad rollback, or cleanup.
- Do not claim production release readiness, L3, pressure PASS, or full acceptance.

## Required Preflight

In development workspace:

```bash
git status --short --branch
git log -1 --oneline
git ls-remote origin refs/heads/main
```

In production deployment path:

```bash
git status --short --branch
git log -1 --oneline
docker compose ps
curl -fsS http://localhost:8081/__proxy/upload/health
curl -sS --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=1&ollamaChatProbe=1'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
curl -sS --max-time 10 http://127.0.0.1:11434/api/ps
ls -lh '/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf'
```

Stop and write a blocked report if preflight shows dependency blocking, admission circuit open, active/current/queued/takeover-required parse or AI work, sample file unavailable, production not at `51f21d0` or later `main`, or any unsafe production state.

## Required Execution

Perform exactly one upload of:

`/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`

Prefer observing through the task page at `http://localhost:8081/cms/` because the user's concern is task-page progress semantics and whether MinerU log output has useful page/operator meaning. API/curl evidence may be used to supplement or automate observation, but the report must include task-page-visible behavior when possible.

Record the created task/material id(s). Then observe until one of these happens:

- terminal success/review-needed state;
- terminal failed state;
- a clear blocker or regression;
- 30 minutes elapsed.

During observation, capture:

- whether MinerU progress appears on the task page/API as meaningful page/batch/stage semantics;
- if the task completes too quickly for page/batch semantics, whether the new `fast-complete-no-business-signal` diagnostic appears;
- whether parsed artifacts are created;
- whether AI metadata reaches a real terminal result or fails;
- whether any Ollama timeout/error appears, especially `UND_ERR_HEADERS_TIMEOUT`;
- whether admission circuit remains closed and active-task diagnostics return to clean state after terminal completion.

## Required Report

Write the report at:

`TaskAndReport/2026-05-13T14-46-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment_REPORT.md`

The report must include:

- confirmation that work was based on this task brief;
- branch/HEAD in development workspace and production path;
- exact sample file path and size;
- exact upload method, timestamp, and evidence that it was exactly one upload;
- created task/material id(s);
- task-page-visible observations, including screenshots or concise descriptions if screenshots are impractical;
- API observations for task state, MinerU progress semantics/diagnostic, parsed artifacts, and AI metadata;
- dependency-health/admission/active-task/Ollama evidence before, during if relevant, and after;
- final state or 30-minute timeout state;
- explicit list of commands run with exit codes;
- skipped checks and exact reasons;
- risks/blockers/residual debt;
- recommendation to Director: accept, fail with follow-up required, or keep observing.

Update `TaskAndReport/TASK_TRACKING_LIST.md` with status, report path, next actor `Director`, next action, required output, created ids, and boundary notes.

Commit and push only the report and task-ledger changes if possible. Do not stage unrelated files.

## Acceptance Criteria

- Exactly one authorized sample upload is performed.
- Task-page/API MinerU progress semantics or fast-complete diagnostic is observed and reported.
- Ollama AI stage behavior is observed and previous 30-second `UND_ERR_HEADERS_TIMEOUT` regression is specifically checked.
- No pressure test, second upload, historical repair, cleanup, destructive operation, model operation, broad restart, sample mutation, L3, pressure PASS, or release-readiness claim occurs.
- Evidence is sufficient for Director to decide the next project step.
