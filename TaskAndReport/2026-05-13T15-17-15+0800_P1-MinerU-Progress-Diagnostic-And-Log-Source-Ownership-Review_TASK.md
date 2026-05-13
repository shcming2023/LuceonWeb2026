# Task: P1 MinerU Progress Diagnostic And Log Source Ownership Review

Assignee:
Architect

Issued by:
Director

Issued at:
2026-05-13T15:17:15+0800

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-13T15-17-15+0800_P1-MinerU-Progress-Diagnostic-And-Log-Source-Ownership-Review_TASK.md

Expected report:
TaskAndReport/2026-05-13T15-17-15+0800_P1-MinerU-Progress-Diagnostic-And-Log-Source-Ownership-Review_REPORT.md

## Required Reading Before Execution

- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/architect.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- docs/codex/TEST_POLICY.md
- docs/codex/TEST_MATRIX.md
- docs/codex/REPOSITORY_STRUCTURE.md
- docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md
- TaskAndReport/README.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-13T14-46-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment_REPORT.md
- TaskAndReport/2026-05-13T15-17-15+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment_DIRECTOR_REVIEW.md

## Objective

Produce a read-only architecture/ops review of MinerU progress observability after Task 90.

The user specifically cares that the task page can show useful MinerU log/progress semantics, not merely final terminal state. Task 90 showed that the system now surfaces diagnostics, but not meaningful page/batch progress.

## Facts To Analyze

Task 90 observed:

- task `task-1778655375028`;
- material `validation-postfix-1778655374`;
- MinerU task `5cc6acce-061f-4418-a29b-b862af8306a6`;
- MinerU completed and stored 21 artifacts;
- task list showed `MinerU 已提交/正在处理，但暂无可归因业务日志`;
- task metadata had `progressSemantics.activityLevel=log-observation-unreadable`;
- material metadata had `progressSemantics.activityLevel=fast-complete-no-business-signal`;
- production log source was reported as `/host/mineru-logs/mineru-api.err.log`, exists, unreadable or empty, size 0;
- a transient false failed MinerU state was self-corrected after MinerU completion was confirmed.

## Scope

This is read-only analysis and implementation planning. Do not modify code or production config.

You may inspect:

- source code in development workspace;
- production runtime state with non-destructive read-only commands;
- task/material/event API state;
- local process/log ownership facts for MinerU if read-only.

Do not restart services, change files, upload samples, repair tasks, clean logs, mutate DB/MinIO/Docker/model/sample files, or change runtime config.

## Required Analysis Questions

Answer these directly:

1. Is the primary remaining gap an ops/log ownership issue, a parser/observer code issue, a UI wording issue, or a mixed issue?
2. Why does task metadata show `log-observation-unreadable` while material metadata shows `fast-complete-no-business-signal`?
3. Should the task page prefer terminal fast-complete diagnostics over stale/unreadable in-flight diagnostics after MinerU completion?
4. Should production MinerU log ownership/path be changed, or should Luceon rely less on host log files for short tasks?
5. What is the smallest safe implementation plan to make the task page operator semantics trustworthy?
6. What tests or runtime checks should be required before another upload validation?

## Required Report

Write:

`TaskAndReport/2026-05-13T15-17-15+0800_P1-MinerU-Progress-Diagnostic-And-Log-Source-Ownership-Review_REPORT.md`

The report must include:

- facts inspected;
- root-cause hypothesis with confidence;
- recommended implementation tasks, split by code vs ops if needed;
- risk level;
- acceptance criteria for a future DevelopmentEngineer task;
- any blocked questions that require Director or user decision.

Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, status, next actor `Director`, and required output.

Commit and push only the report and task-ledger changes if possible.

## Acceptance Criteria

- The report gives Director enough clarity to dispatch a scoped implementation or ops task.
- It does not mutate production state.
- It keeps AI terminal failure separate from MinerU progress observability.
