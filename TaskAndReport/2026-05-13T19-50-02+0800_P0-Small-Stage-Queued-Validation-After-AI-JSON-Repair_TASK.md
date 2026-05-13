# TASK-20260513-195002-P0-Small-Stage-Queued-Validation-After-AI-JSON-Repair

Task:
P0 Small Stage-Queued Validation After AI JSON Repair

Assignee:
TestAcceptanceEngineer

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
`TaskAndReport/2026-05-13T19-50-02+0800_P0-Small-Stage-Queued-Validation-After-AI-JSON-Repair_TASK.md`

Expected completion report:
`TaskAndReport/2026-05-13T19-50-02+0800_P0-Small-Stage-Queued-Validation-After-AI-JSON-Repair_REPORT.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/test-acceptance-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- This task brief
- Task 98 report and Director review:
  - `TaskAndReport/2026-05-13T19-33-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-AI-JSON-Repair_REPORT.md`
  - `TaskAndReport/2026-05-13T19-45-57+0800_P0-Exactly-One-Controlled-Upload-Validation-After-AI-JSON-Repair_DIRECTOR_REVIEW.md`

## Background

Task 98 proved that one controlled production upload at HEAD `de2d23f` can complete the current path:

upload -> local MinerU -> MinIO parsed artifacts -> Ollama `qwen3.5:9b` -> deterministic AI JSON repair -> non-skeleton metadata -> `review-pending`.

The accepted validation task was:

- task `task-1778672291622`
- material `validation-json-repair-1778672290`
- MinerU task `4affdec7-13aa-4a28-806d-07e71aad536d`
- AI job `ai-job-1778672312564-0b2f`

Residual P1 issue remains: MinerU progress semantics can still be diagnostic-only, and transient false failed/corrected events can occur due `log-observation-unreadable`. This must be observed and reported, not hidden.

The user approved Option A at 2026-05-13T19:50:02+0800: perform up to three small serial validations from `/Users/concm/prod_workspace/Luceon2026/testpdf`, one at a time, terminal state before the next, stop on systemic failure, no pressure, no cleanup, no上线声明.

## Objective

Validate whether the just-accepted single-sample success repeats across a very small serial sample set without treating the run as pressure, batch, soak, L3, release readiness, or production readiness.

## Scope

Use PDFs from:

`/Users/concm/prod_workspace/Luceon2026/testpdf`

Execution rules:

1. Enumerate available PDFs first and record every candidate filename, size, and SHA-256 in the report.
2. If there are 1 to 3 PDFs, validate all available PDFs.
3. If there are more than 3 PDFs, validate the first 3 PDFs in lexicographic filename order unless there is a clear filesystem reason to skip a file; record any skip exactly.
4. Upload exactly one PDF at a time.
5. Wait for that task to reach terminal state before uploading the next PDF.
6. Stop immediately on a dependency-blocking signal, admission-circuit open state, upload failure, terminal failed state, unresolved active-task drift, or other systemic failure evidence.
7. After every sample, verify task page semantics, DB/API terminal state, material state, AI job state when applicable, active-task state, and admission circuit state.

If the folder has no PDFs, write a blocked report and update the tracking row to `挂起` with `Next Actor=Director`.

## Allowed Operations

- Read files and metadata under the development workspace and production deployment path.
- Use read-only production checks:
  - `git status --short --branch`
  - `git log -1 --oneline`
  - `docker compose ps`
  - `curl` health, dependency-health, active-task, admission-circuit, task/material/AI-job endpoints
  - read-only logs such as `docker compose logs --tail=...`
  - browser or Playwright reads of `/cms/tasks` and task detail pages
- Perform up to 3 authorized PDF uploads through the existing production upload path.
- Create validation task/material records naturally produced by those authorized uploads.
- Write the completion report and update only the matching Task 100 row in `TaskAndReport/TASK_TRACKING_LIST.md`.

## Forbidden Operations

- Do not run pressure, batch-concurrent, soak, broad stress, or long-run tests.
- Do not upload more than 3 PDFs.
- Do not upload the next PDF until the previous upload has reached terminal state.
- Do not repair, reparse, re-AI, clean up, delete, rename, or mutate historical tasks/materials/artifacts.
- Do not mutate sample files under `/Users/concm/prod_workspace/Luceon2026/testpdf`.
- Do not copy sample files into the repository.
- Do not run destructive DB, MinIO, Docker volume, filesystem, or data cleanup commands.
- Do not run `docker compose down`, `docker compose down -v`, volume deletion, DB reset, MinIO cleanup, model pull/delete/replace, or service restart/rebuild.
- Do not change source code, PRD truth, role contracts, task scope, release judgments, secrets, credentials, environment settings, or model settings.
- Do not declare L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.
- Do not push to GitHub. Director will review and synchronize the report/ledger if accepted.

## Preflight Requirements

Before the first upload, record:

- development workspace branch/status;
- production workspace branch/status and HEAD;
- sample folder existence and candidate PDF inventory;
- production service health:
  - upload-server health;
  - dependency-health with `mineruSubmitProbe=true` and Ollama chat probe if available;
  - MinerU admission circuit;
  - MinerU active-task;
  - Docker service health from `docker compose ps`;
  - Ollama residency from `/api/ps` when reachable.

If preflight shows active parse/AI work, admission circuit open, dependency blocking, unhealthy core service, or ambiguous existing validation activity, do not upload. Write a blocked report and update the tracking row accordingly.

## Per-Sample Evidence Requirements

For each attempted PDF, report:

- sample filename, size, SHA-256;
- material ID and task ID created;
- upload request endpoint and HTTP result;
- task state/stage/progress/message timeline summary;
- final task state;
- final material status, `mineruStatus`, `aiStatus`, parsed artifact count;
- AI job ID and final state, provider, model, confidence, `needsReview`, and whether metadata is non-skeleton;
- whether first pass, repair pass, or deterministic repair occurred;
- task page and task list semantics visible to the operator;
- admission circuit and active-task state after terminal completion;
- any transient false failed/corrected MinerU events or diagnostic-only progress language.

Use screenshots only as temporary local evidence under `/tmp` if useful. Do not commit screenshots or large artifacts.

## Stop Conditions

Stop the run and write the report if any of these occur:

- dependency-health becomes blocking;
- MinerU admission circuit opens;
- upload request fails or returns non-2xx;
- any validation task reaches terminal `failed`;
- a task remains non-terminal beyond a reasonable observation window and no safe progress can be established;
- active-task or admission-circuit state remains dirty after terminal completion;
- the task page semantics become misleading in a way that prevents acceptance-boundary judgment;
- any operation would require restart, rebuild, cleanup, repair, model change, or destructive mutation.

## Required Checks

At minimum, run and record exit codes for:

- `git status --short --branch` in the development workspace;
- `git status --short --branch` and `git log -1 --oneline` in the production workspace;
- sample `stat` and `shasum -a 256`;
- production health/API checks listed above;
- per-sample task/material/AI/admission/active-task API checks.

No source-code build, lint, or typecheck is required unless you unexpectedly modify repository code, which is forbidden by this task.

## Completion Report Requirements

Write the report to:

`TaskAndReport/2026-05-13T19-50-02+0800_P0-Small-Stage-Queued-Validation-After-AI-JSON-Repair_REPORT.md`

Then update only Task 100 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- if completed: `Status=已回报待 Director 审查`, `Next Actor=Director`;
- if blocked: `Status=挂起`, `Next Actor=Director`;
- include report path, production HEAD, sample count attempted, task IDs, material IDs, AI job IDs, terminal states, and concise recommendation.

Do not push to GitHub. Director will review and synchronize.

## Acceptance Criteria

Task 100 can be accepted if the report proves:

- preflight was safe before uploading;
- no more than 3 PDFs were uploaded;
- uploads were strictly serial;
- every attempted sample has complete task/material/AI/runtime evidence;
- no forbidden operation was performed;
- final recommendation clearly separates the small serial validation boundary from production readiness, L3, pressure PASS, release readiness, and go-live readiness.
