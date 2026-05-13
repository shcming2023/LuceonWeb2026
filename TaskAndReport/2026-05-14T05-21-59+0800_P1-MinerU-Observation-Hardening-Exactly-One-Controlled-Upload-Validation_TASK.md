# TASK-20260514-052159-P1-MinerU-Observation-Hardening-Exactly-One-Controlled-Upload-Validation

Task:
P1 MinerU Observation Hardening Exactly One Controlled Upload Validation

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

Production test sample folder:
`/Users/concm/prod_workspace/Luceon2026/testpdf`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-14T05-21-59+0800_P1-MinerU-Observation-Hardening-Exactly-One-Controlled-Upload-Validation_TASK.md`

Expected completion report:
`TaskAndReport/2026-05-14T05-21-59+0800_P1-MinerU-Observation-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`

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
- Task 101 report and Director review:
  - `TaskAndReport/2026-05-13T20-19-44+0800_P1-MinerU-Processing-Log-Observation-Adjudication-Hardening_REPORT.md`
  - `TaskAndReport/2026-05-14T04-53-38+0800_P1-MinerU-Processing-Log-Observation-Adjudication-Hardening_DIRECTOR_REVIEW.md`
- Task 102 report and Director review:
  - `TaskAndReport/2026-05-14T04-53-38+0800_P1-MinerU-Observation-Hardening-Production-Deployment-And-Runtime-Validation_REPORT.md`
  - `TaskAndReport/2026-05-14T05-15-58+0800_P1-MinerU-Observation-Hardening-Production-Deployment-And-Runtime-Validation_DIRECTOR_REVIEW.md`
- User decision:
  - `TaskAndReport/2026-05-14T05-15-58+0800_P1-MinerU-Observation-Hardening-Controlled-Upload-Validation-Decision_DECISION.md`

## Background

Task 101 hardened MinerU log-observation adjudication. When MinerU API still reports queued/pending/processing/running, unreadable or stale log observation should be diagnostic warning metadata rather than a terminal failed state.

Task 102 deployed that accepted code path to production upload-server and validated non-destructive runtime surfaces at production HEAD `159d80e`. Director accepted only the deployment/runtime-surface boundary. No validation upload has yet confirmed the operator-visible task-page behavior after this deployment.

The user approved Director Option A on 2026-05-14: exactly one controlled upload validation from `/Users/concm/prod_workspace/Luceon2026/testpdf`, not a pressure test.

## Objective

Perform exactly one controlled production upload validation to answer this narrow question:

Does the deployed MinerU observation hardening prevent unreadable/stale MinerU log observation from producing terminal or operator-misleading false failed task semantics while MinerU API is still processing/running?

This task is about live task-page/list/detail behavior and terminal state evidence. It is not a throughput, pressure, L3, or release-readiness test.

## Allowed Operations

In the development workspace:

- run `git status --short --branch`;
- read the task ledger and required documents;
- write this task's completion report;
- update only Task 104 in `TaskAndReport/TASK_TRACKING_LIST.md` to `已回报待 Director 审查` or a blocked/failed status.

In the production deployment path:

- run `git status --short --branch` and `git log -1 --oneline`;
- inspect Docker service state with non-destructive commands such as `docker compose ps`;
- run read-only health/admission/active-task checks;
- inventory `/Users/concm/prod_workspace/Luceon2026/testpdf` without modifying sample files;
- select exactly one small/medium PDF from that folder;
- upload exactly one PDF through the existing production upload path;
- observe task list/detail/page semantics until terminal state or clear failure;
- read logs and API surfaces as needed for evidence.

Runtime surfaces to check before upload:

- upload health;
- dependency-health with MinerU submit probe and Ollama chat probe if available;
- `/ops/mineru/admission-circuit`;
- `/ops/mineru/active-task`;
- Docker service health.

## Forbidden Operations

- Do not upload more than one PDF.
- Do not run pressure, batch-concurrent, soak, broad stress, or long-run tests.
- Do not repair, reparse, re-AI, retry, clean up, delete, rename, or mutate historical tasks/materials/artifacts.
- Do not mutate DB/MinIO/Docker volumes/data except for the single authorized upload's normal application-created records/artifacts.
- Do not modify, delete, rename, or pollute sample files.
- Do not run `docker compose down`, `docker compose down -v`, volume deletion, DB reset, MinIO cleanup, model pull/delete/replace, broad restart, rebuild, rollback, or config/secret/env mutation.
- Do not change source code, PRD truth, role contracts, release docs, GitHub settings, secrets, model settings, or unrelated files.
- Do not declare L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.
- Do not push to GitHub. Director owns GitHub synchronization for this thread's current workflow.

## Pre-Upload Stop Conditions

Stop and write a blocked report before uploading if any of these are true:

- active parse or AI work exists;
- admission circuit is open;
- dependency-health is blocking;
- core Docker services are unhealthy;
- production upload-server is not at the Task 101 deployed code path or production HEAD cannot be identified;
- sample folder `/Users/concm/prod_workspace/Luceon2026/testpdf` is missing or contains no suitable PDF;
- the validation would require a restart/rebuild, destructive cleanup, repair, reparse, re-AI, or model/config change.

## Validation Requirements

For the single selected PDF, record:

- sample path, size, and SHA-256 hash;
- upload command or UI path used;
- created task id, material id, MinerU task id, and AI job id if available;
- observed task list/detail/page status transitions;
- whether any `log-observation-unreadable`, stale-log, or MinerU observation warning appears;
- whether such observation remains diagnostic-only while MinerU API is queued/pending/processing/running;
- whether any transient false failed/self-corrected event appears to the operator;
- parsed artifact count or parsed-file evidence if MinerU completes;
- AI metadata terminal state if the task reaches AI stage;
- final admission-circuit and active-task state.

If the task reaches `review-pending`, record that as a bounded pass for this one controlled upload. If it fails, record exact stage, reason, visible UI semantics, raw diagnostic evidence, and stop without a second upload.

## Completion Report Requirements

Write the report to:

`TaskAndReport/2026-05-14T05-21-59+0800_P1-MinerU-Observation-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`

Then update only Task 104 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- `Status=已回报待 Director 审查` if completed with pass/fail evidence;
- `Status=挂起` if blocked before upload;
- `Next Actor=Director`;
- include selected sample path/hash, task/material ids, terminal state, and whether false MinerU failed/log-observation semantics recurred.

Do not update project state docs, PRD, role contracts, release docs, or GitHub.

## Acceptance Criteria

Director can accept this task if:

- exactly one PDF was uploaded;
- all preflight evidence is recorded;
- sample identity is recorded with path, size, and hash;
- task/material/MinerU/AI identifiers are recorded where available;
- operator-visible MinerU observation semantics are explicitly assessed;
- final task state and final runtime surfaces are recorded;
- no forbidden operation or readiness claim is performed.
