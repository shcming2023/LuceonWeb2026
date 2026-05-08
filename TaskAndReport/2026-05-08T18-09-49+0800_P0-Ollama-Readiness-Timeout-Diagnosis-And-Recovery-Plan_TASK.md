# P0 Ollama Readiness Timeout Diagnosis And Recovery Plan

Task:
P0 Ollama Readiness Timeout Diagnosis And Recovery Plan

Task ID:
`TASK-20260508-180949-P0-Ollama-Readiness-Timeout-Diagnosis-And-Recovery-Plan`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T18:09:49+0800

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T18-09-49+0800_P0-Ollama-Readiness-Timeout-Diagnosis-And-Recovery-Plan_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/deploy/DEPLOY.md`
- `TaskAndReport/2026-05-08T17-31-00+0800_P0-Adaptive-Evidence-Pack-Scoped-Production-Validation_TASK.md`
- `TaskAndReport/2026-05-08T17-41-06+0800_P0-Adaptive-Evidence-Pack-Scoped-Production-Validation_REPORT.md`
- `TaskAndReport/2026-05-08T18-09-49+0800_P0-Adaptive-Evidence-Pack-Scoped-Production-Validation_LUCIA_REVIEW.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Task 34 applied accepted `main` code to production and rebuilt upload-server, but stopped before the controlled large-PDF validation upload because pre-upload dependency health reported Ollama `qwen3.5:9b` chat smoke timeout:

- `ollama.ok=false`
- `ollama.chatOk=false`
- `ollama.error="Smoke test failed: The operation was aborted due to timeout"`
- `ollama.durationMs=15006`

This task is a diagnosis and recovery-plan task only.

## Objective

Determine why production Ollama readiness for `qwen3.5:9b` is timing out, whether the condition is transient or persistent, and what minimum safe recovery action should be requested next.

## Authorized Scope

Lucode may perform read-only or non-mutating diagnosis only:

1. Inspect development and production git status and synchronize metadata with `git fetch origin`.
2. Inspect production service state using read-only commands such as `docker compose ps`.
3. Run read-only CMS, DB, and dependency-health checks.
4. Run direct Ollama reachability checks against the configured host endpoint, including lightweight `/api/tags` and one minimal chat/generate readiness probe if needed.
5. Inspect host listener/process state for Ollama with read-only commands such as `lsof`, `ps`, `pgrep`, or `launchctl list`.
6. Inspect model availability with read-only `ollama list` / `ollama ps` if the CLI is available.
7. Record resource observations that may explain timeout, such as CPU/memory pressure, using read-only commands.
8. Produce a recovery recommendation with explicit Director-approval boundaries.

If Ollama becomes ready during read-only diagnosis without mutation, record that fact but do not create the large-PDF validation upload. Lucia will decide whether to re-issue validation.

## Forbidden

- Do not claim production release readiness.
- Do not create any production validation upload.
- Do not restart, start, stop, kill, or reload Ollama or any production service.
- Do not run `docker compose up`, `down`, `restart`, `pull`, `build`, or any Docker mutation.
- Do not pull, delete, change, or switch models.
- Do not change timeout policy.
- Do not change secrets or production-local override values.
- Do not delete DB rows, MinIO objects, Docker volumes, tasks, artifacts, or logs.
- Do not add skeleton fallback or silent degradation.

## Required Checks

Run and report exact commands and exit codes where applicable:

- `git status --short --branch` in development and production workspaces.
- `git fetch origin` in development and production workspaces.
- Production HEAD and `origin/main` HEAD.
- `docker compose ps` in production.
- CMS reachability.
- DB health.
- Dependency health with `mineruSubmitProbe=true`.
- Direct Ollama tags/list reachability.
- Direct minimal Ollama readiness probe result, including timeout duration if it fails.
- Host listener/process/model observations for Ollama.
- Active parse/task states and active AI metadata jobs.

## Required Output

Write report to:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Ollama-Readiness-Timeout-Diagnosis-And-Recovery-Plan_REPORT.md`

The report must include:

- Result classification: `DIAGNOSED`, `BLOCKED`, or `INCONCLUSIVE`.
- Exact commands, exit codes, and concise outputs.
- Whether Ollama timeout appears persistent or transient.
- Whether `qwen3.5:9b` is installed and idle/busy if observable.
- Whether the upload-server dependency-health result matches direct Ollama probes.
- Recommended next action:
  - no action needed and re-issue validation, or
  - Director approval needed for a scoped recovery operation, or
  - return for deeper investigation.
- Confirmation that no production upload, service mutation, model/timeout change, data deletion, secret change, or release-readiness claim occurred.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status `已回报待审`
- `Next Actor=Lucia`
- Report path
- Branch/HEAD
- Summary notes

Commit and push report/task-list changes to GitHub `main`.
