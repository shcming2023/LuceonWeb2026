# TASK-20260514-100030-P1-MinerU-Log-Source-Ownership-Remediation-Route

Task:
P1 MinerU Log Source Ownership Remediation Route

Assignee:
Architect

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
`TaskAndReport/2026-05-14T10-00-30+0800_P1-MinerU-Log-Source-Ownership-Remediation-Route_TASK.md`

Expected completion report:
`TaskAndReport/2026-05-14T10-00-30+0800_P1-MinerU-Log-Source-Ownership-Remediation-Route_REPORT.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/architect.md` if present in the local workspace; if absent, do not block solely on that missing file, and follow `AGENTS.md`, `TEAM_CONTRACT`, and this task brief.
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- This task brief
- Task 111 report and Director review:
  - `TaskAndReport/2026-05-14T08-12-41+0800_P1-MinerU-Log-Observer-Runtime-Ownership-Read-Only-Recovery-Plan_REPORT.md`
  - `TaskAndReport/2026-05-14T08-36-13+0800_P1-MinerU-Log-Observer-Runtime-Ownership-Read-Only-Recovery-Plan_DIRECTOR_REVIEW.md`
- Task 113 report and Director review:
  - `TaskAndReport/2026-05-14T09-15-58+0800_P1-MinerU-Sidecar-Attach-Only-Recovery_REPORT.md`
  - `TaskAndReport/2026-05-14T09-34-12+0800_P1-MinerU-Sidecar-Attach-Only-Recovery_DIRECTOR_REVIEW.md`
- Task 115 report and Director review:
  - `TaskAndReport/2026-05-14T09-38-05+0800_P1-MinerU-Live-Progress-Observability-Exactly-One-Controlled-Upload-Validation_REPORT.md`
  - `TaskAndReport/2026-05-14T10-00-30+0800_P1-MinerU-Live-Progress-Observability-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`

## Background

Task 113 proved that `luceon-sidecar` can be attached and observed.

Task 115 proved that the main runtime path can complete for one controlled PDF after sidecar attach, but live MinerU business-progress observability still did not recover:

- configured log-channel ownership stayed `summaryState=empty`;
- configured stdout/stderr logs stayed empty/readable;
- `luceon-sidecar` stayed `observed-recent`;
- global observation still used stale fallback content from `uat/scratch/mineru-api.log`;
- final material recorded `fast-complete-no-business-signal`;
- browser semantics were understandable but still said no attributable business-progress log was captured.

Director spot-check after Task 115 confirmed the same endpoint state. The issue is now likely MinerU process/log-writer ownership or stale fallback selection, not a missing sidecar process.

## Objective

Produce a read-only architecture remediation route for restoring trustworthy MinerU progress observability.

The report must answer:

1. Why the current configured log channel remains empty despite `luceon-sidecar` being observed.
2. Whether current code should exclude or down-rank stale fallback logs from `uat/scratch/mineru-api.log`.
3. Whether a code-only improvement can make operator semantics accurate enough without claiming fabricated page/batch progress.
4. Whether true live business-progress recovery requires controlled MinerU process ownership normalization so MinerU writes to the configured log files.
5. What exact next task should be issued, to which role, with what preconditions and forbidden operations.

## Allowed Operations

Read-only only:

- read repository files and task reports;
- run `git status --short --branch` in development and production workspaces;
- run `git log -1 --oneline` in production;
- inspect process/listener ownership using read-only commands such as `ps`, `pgrep`, `lsof`, and `tmux ls`;
- inspect Docker service state with `docker compose ps`;
- inspect environment/config files without editing them;
- run read-only health and observability endpoint curls;
- inspect log file metadata and tails without modifying files;
- write this task's report;
- update only Task 116 in `TaskAndReport/TASK_TRACKING_LIST.md` to `已回报待 Director 审查` or blocked.

## Forbidden Operations

- Do not upload PDFs.
- Do not run pressure, batch, soak, or long-run validation.
- Do not restart, stop, kill, relaunch, or normalize MinerU.
- Do not start/stop/restart sidecar, supervisor, Docker services, DB, MinIO, upload-server, frontend, or Ollama.
- Do not run `docker compose up/down/restart/build`, `docker compose down -v`, volume deletion, DB reset, MinIO cleanup, model pull/delete/replace, or data cleanup.
- Do not repair, reparse, re-AI, retry, mutate, delete, or clean historical tasks/materials/artifacts.
- Do not modify source code, docs other than this report/tracking row, PRD, role contracts, configs, secrets, env, samples, models, or production files.
- Do not overwrite or normalize dirty worktree changes.
- Do not claim L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.
- Do not push to GitHub.

## Required Analysis

Your report must include:

- Current process ownership map:
  - MinerU listener PID/command/environment clues;
  - tmux sessions;
  - sidecar status;
  - supervisor status;
  - Ollama listener note only if relevant to risk;
  - production worktree dirty-state note.
- Current log-source map:
  - configured `MINERU_LOG_PATH` and `MINERU_ERR_LOG_PATH`;
  - file existence/size/mtime/readability;
  - fallback log paths considered by the observer;
  - why stale fallback is still being selected globally;
  - whether configured logs are host paths, container-mounted paths, or mismatched in practice.
- Remediation options with risk:
  - code-only stale fallback exclusion/down-ranking;
  - UI/operator semantic hardening for "completed without attributable progress";
  - sidecar/log-path retargeting without MinerU restart if feasible;
  - controlled MinerU ownership normalization with exact preflight gates;
  - supervisor integration as a later step if needed.
- Recommended next task:
  - assignee;
  - exact scope;
  - whether user approval is required;
  - proposed preflight gates;
  - forbidden operations;
  - expected evidence.

## Completion Report Requirements

Write the report to:

`TaskAndReport/2026-05-14T10-00-30+0800_P1-MinerU-Log-Source-Ownership-Remediation-Route_REPORT.md`

Then update only Task 116 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- `Status=已回报待 Director 审查` if completed;
- `Status=挂起` if blocked;
- `Next Actor=Director`;
- include concise recommended next route and whether user approval is needed.

Do not update project state docs, PRD, role contracts, release docs, or GitHub.

## Acceptance Criteria

Director can accept the report if it:

- is read-only and non-mutating;
- grounds conclusions in current code, reports, and runtime facts;
- explains why sidecar attach did not restore live progress;
- separates code semantics, log-source routing, and process ownership concerns;
- gives a concrete next task recommendation with risk/approval boundary;
- makes no readiness or上线 claim.
