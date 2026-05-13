# TASK-20260514-054235-P1-MinerU-Progress-Observability-Ownership-Review

Task:
P1 MinerU Progress Observability Ownership Review

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
`TaskAndReport/2026-05-14T05-42-35+0800_P1-MinerU-Progress-Observability-Ownership-Review_TASK.md`

Expected completion report:
`TaskAndReport/2026-05-14T05-42-35+0800_P1-MinerU-Progress-Observability-Ownership-Review_REPORT.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/architect.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- This task brief
- Task 100 report and Director review:
  - `TaskAndReport/2026-05-13T19-50-02+0800_P0-Small-Stage-Queued-Validation-After-AI-JSON-Repair_REPORT.md`
  - `TaskAndReport/2026-05-13T20-19-44+0800_P0-Small-Stage-Queued-Validation-After-AI-JSON-Repair_DIRECTOR_REVIEW.md`
- Task 101 report and Director review:
  - `TaskAndReport/2026-05-13T20-19-44+0800_P1-MinerU-Processing-Log-Observation-Adjudication-Hardening_REPORT.md`
  - `TaskAndReport/2026-05-14T04-53-38+0800_P1-MinerU-Processing-Log-Observation-Adjudication-Hardening_DIRECTOR_REVIEW.md`
- Task 104 report and Director review:
  - `TaskAndReport/2026-05-14T05-21-59+0800_P1-MinerU-Observation-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`
  - `TaskAndReport/2026-05-14T05-40-51+0800_P1-MinerU-Observation-Hardening-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`
- User decision:
  - `TaskAndReport/2026-05-14T05-40-51+0800_P1-Next-Step-After-MinerU-Observation-Hardening-Validation_DECISION.md`

## Background

Task 104 accepted the exactly-one controlled upload validation after MinerU observation hardening. The targeted false-failed defect did not recur: `log-observation-unreadable` appeared while MinerU API was processing, but remained `mineru-log-observation-diagnostic-only`, and the task reached `review-pending`.

The residual limitation is different: MinerU progress is still diagnostic-only for the observed sample. The task page honestly says `MinerU 已完成，但本次未捕获可归因业务进度日志`, which avoids false failure but does not give operators rich page/batch/business progress. The user explicitly chose to govern MinerU progress observability before any pressure testing.

## Objective

Produce a read-only architecture report that answers:

1. Where should authoritative MinerU business-progress signals come from in the current Luceon deployment?
2. Why did Task 104 still end with diagnostic-only / no attributable business progress?
3. Is the limitation primarily:
   - a code parsing/normalization issue,
   - a sidecar/log-source ownership issue,
   - a MinerU runtime/API capability issue,
   - a UI/product semantics issue,
   - or an expected behavior for small/fast PDFs?
4. What is the safest next implementation or ops-governance task to improve operator-visible MinerU progress without reintroducing false failure or fabricated progress?
5. What evidence should be required before broader serial validation or any pressure test resumes?

## Scope

This is a read-only architecture / observability ownership review.

You may inspect:

- relevant repository source files and tests;
- existing TaskAndReport reports and reviews;
- production runtime health/status surfaces using non-destructive commands;
- production logs using read-only commands when useful;
- screenshots already created by Task 104 if they still exist.

Suggested code areas to inspect, adjusting as needed based on actual repository structure:

- MinerU local adapter and status ingestion;
- MinerU log parser / progress parser;
- MinerU sidecar observer;
- active-task and admission-circuit surfaces;
- task/material metadata persistence surfaces;
- task list/detail UI semantics and `progressSemantics` rendering;
- focused tests around MinerU progress, diagnostic precedence, and log observation adjudication.

## Allowed Operations

In the development workspace:

- `git status --short --branch`;
- `rg`, `sed`, `nl`, `git diff`, `git log`, `node --check` only if needed for read-only syntax orientation;
- read repo files and task reports;
- write the Architect completion report;
- update only Task 106 in `TaskAndReport/TASK_TRACKING_LIST.md` to `已回报待 Director 审查` or `挂起`.

In the production deployment path:

- `git status --short --branch`;
- `git log -1 --oneline`;
- `docker compose ps`;
- read-only `curl` checks for upload health, dependency-health, admission-circuit, active-task, and task/material surfaces;
- read-only log inspection such as `docker logs` or existing log files;
- inspect current process/service ownership without restarting or changing it.

## Forbidden Operations

- Do not upload any PDF.
- Do not run pressure, batch-concurrent, soak, broad stress, or long-run tests.
- Do not modify source code.
- Do not modify PRD truth, role contracts, release docs, environment files, secrets, model settings, Docker Compose files, DB, MinIO, sample files, or production data.
- Do not repair, reparse, re-AI, retry, clean up, delete, rename, or mutate historical tasks/materials/artifacts.
- Do not run `docker compose up`, `docker compose down`, `docker compose down -v`, rebuilds, restarts, rollbacks, DB reset, MinIO cleanup, model pull/delete/replace, or destructive commands.
- Do not push to GitHub.
- Do not declare L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.

## Report Requirements

Write the report to:

`TaskAndReport/2026-05-14T05-42-35+0800_P1-MinerU-Progress-Observability-Ownership-Review_REPORT.md`

The report must include:

- concise executive conclusion;
- current MinerU progress signal map from runtime/source to UI;
- evidence from Task 100/101/104 and current read-only checks;
- root-cause classification for diagnostic-only progress;
- whether the current behavior is acceptable as a product boundary or needs improvement before broader validation;
- recommended next task, including assignee role, scope, allowed files/areas, forbidden operations, and acceptance criteria;
- risks of going straight to pressure testing now;
- commands run and exit codes;
- skipped checks and exact reasons.

After writing the report, update only Task 106 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- `Status=已回报待 Director 审查` if completed;
- `Status=挂起` if blocked;
- `Next Actor=Director`;
- include the recommended next step and key evidence.

## Acceptance Criteria

Director can accept this task if the report:

- stays read-only;
- clearly distinguishes false-failure adjudication from progress-rich observability;
- maps the current signal ownership path;
- gives a concrete next task recommendation;
- explains why pressure testing should or should not wait;
- records evidence and commands without overclaiming readiness.
