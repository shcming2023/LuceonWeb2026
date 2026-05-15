# Task: P1 Pressure Progress Semantics Root-Cause Diagnosis

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
TaskAndReport/2026-05-16T06-07-44+0800_P1-Pressure-Progress-Semantics-Root-Cause-Diagnosis_TASK.md

Expected report:
TaskAndReport/2026-05-16T06-07-44+0800_P1-Pressure-Progress-Semantics-Root-Cause-Diagnosis_REPORT.md

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/TEST_MATRIX.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-15T20-29-08+0800_P1-Manual-Clean-24-PDF-Pressure-Monitoring_REPORT.md`
- `TaskAndReport/2026-05-16T06-01-21+0800_P1-Manual-Clean-24-PDF-Pressure-Monitoring_DIRECTOR_REVIEW.md`
- `TaskAndReport/2026-05-16T06-07-44+0800_P1-Pressure-Progress-Semantics-Root-Cause-First-Correction_DECISION.md`

## Background

Task 190 showed a successful terminal pressure-window observation with residuals: 23 `review-pending`, 1 `failed/ai`, and all 24 materials completed MinerU.

However, the same report confirmed a long-running recurring problem: during active MinerU work, operator-facing semantics can lag or conflict with backend/direct evidence. The User explicitly instructed that this must be root-caused before implementation.

## Objective

Perform a read-only root-cause diagnosis of progress semantic lag during long-running MinerU/AI pressure runs.

The goal is not to patch code in this task. The goal is to produce an evidence-grounded causal map that explains why the system can show stale/confusing state while MinerU logs or direct API still show progress.

## Investigation Scope

Inspect current code, reports, tests, and read-only runtime evidence to answer:

1. What are the authoritative sources for parse progress and terminal state?
   - DB `ParseTask` state/stage/progress/message;
   - material `mineruStatus` / `aiStatus`;
   - active-task endpoint;
   - dependency-health endpoint;
   - direct MinerU `/tasks/{id}` and `/health`;
   - MinerU stdout/stderr logs and log parser;
   - MinIO parsed output presence;
   - AI metadata jobs;
   - `/cms/tasks` UI.

2. Where are these sources merged, prioritized, or flattened?

3. Why did Task 190 observe mismatches such as:
   - UI/active-task implying stale observation while direct MinerU/logs showed progress;
   - direct MinerU completion occurring before DB/active-task caught up;
   - dependency-health no-submit timing out during active heavy work while direct MinerU continued;
   - log-channel ownership becoming `stale` after terminal/idle state;
   - one AI failure after successful MinerU completion needing distinct semantics.

4. Which mismatches are expected asynchronous lag, and which are implementation defects?

5. Which code paths should be changed later, and in what order?

## Required Code/Runtime Areas To Inspect

Use `rg` to find exact files before drawing conclusions. Likely areas include:

- upload-server task worker / MinerU adapter / polling logic;
- active-task endpoint;
- dependency-health endpoint;
- MinerU log parser and log-channel ownership endpoint;
- AI metadata worker and AI failure classification;
- task/material DB update flow;
- `/cms/tasks` page, batch/pressure summaries, and task-detail display components;
- focused tests around MinerU runtime progress, pressure semantics, dependency-health, and AI failure classification.

## Allowed Operations

- Read repository files.
- Run read-only shell commands.
- Run read-only HTTP GET requests against local production endpoints.
- Query DB-facing HTTP APIs that are read-only.
- Read logs with `tail`, `stat`, `ls`, or equivalent read-only commands.
- Run local static/test commands only if they do not mutate production data.
- Write only the required diagnosis report and update the task ledger.

## Forbidden Operations

- Do not implement code changes.
- Do not edit source, UI, tests, docs outside the report/ledger.
- Do not upload files.
- Do not run pressure tests.
- Do not run submit-probe.
- Do not retry/reparse/re-AI/cancel/repair/reset any task.
- Do not mutate DB, MinIO, Docker volumes, runtime config, secrets, models, samples, or production files.
- Do not restart, stop, kill, relaunch, rebuild, redeploy, or mutate services.
- Do not claim pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

## Required Report

Write:

`TaskAndReport/2026-05-16T06-07-44+0800_P1-Pressure-Progress-Semantics-Root-Cause-Diagnosis_REPORT.md`

The report must include:

- confirmation that this Director task brief was followed;
- branch and HEAD;
- production HEAD and dirty-file summary if production was inspected;
- commands/endpoints used and exit codes;
- all skipped checks and reasons;
- source-of-truth map for progress/terminal state;
- timeline/cause analysis from Task 190 evidence;
- exact code paths and functions likely responsible, with file paths and line references where possible;
- root-cause ranking: primary, secondary, contributing factors;
- distinction between expected async lag and actual defects;
- recommended implementation phases;
- specific proposed follow-up tasks, each small enough for DevelopmentEngineer implementation;
- residual risks and unknowns;
- GitHub sync status;
- whether Director review is required.

## Acceptance Criteria

Director can accept this task if:

- it explains the semantic-lag root cause with code and runtime evidence;
- it avoids implementation and scope drift;
- it distinguishes MinerU processing truth from UI/backend/log/dependency-health observation artifacts;
- it identifies the minimum safe implementation path;
- it preserves strict no-skeleton-fallback and explicit failure semantics.

