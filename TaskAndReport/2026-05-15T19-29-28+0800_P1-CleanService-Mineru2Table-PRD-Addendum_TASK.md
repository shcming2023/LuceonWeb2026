# Task: P1 CleanService Mineru2Table PRD Addendum

- Task ID: `TASK-20260515-192928-P1-CleanService-Mineru2Table-PRD-Addendum`
- Assignee: `ProductManager`
- Issued by: `Director`
- Issued at: 2026-05-15T19:29:28+0800
- Priority: P1
- Project: Luceon2026
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- GitHub: `https://github.com/shcming2023/Luceon2026`
- Task brief: `TaskAndReport/2026-05-15T19-29-28+0800_P1-CleanService-Mineru2Table-PRD-Addendum_TASK.md`
- Expected report: `TaskAndReport/2026-05-15T19-29-28+0800_P1-CleanService-Mineru2Table-PRD-Addendum_REPORT.md`

## Required Reading

Before execution, read:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/product-manager.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-15T19-21-13+0800_P1-CleanService-Mineru2Table-Docs-Absorption_REPORT.md`
- `TaskAndReport/2026-05-15T19-29-28+0800_P1-CleanService-Mineru2Table-Docs-Absorption_DIRECTOR_REVIEW.md`

## Background

Architect reviewed the user-provided CleanService/Mineru2Table source bundle and concluded that the direction is valuable but not yet canonical project truth.

Director accepted the report with this boundary:

- ProductManager PRD addendum is required before architecture/contract docs are promoted as implementation direction.
- No CleanService code implementation is authorized by this task.
- The current pressure-test blocker remains separate.

## Objective

Create a draft PRD addendum for Mineru2Table as Luceon2026's future `toc-rebuild` CleanService.

Allowed file to create or update:

- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`

Also write the required ProductManager report and update the task ledger.

## Required Addendum Content

The addendum must cover:

- product value: why Mineru2Table `toc-rebuild` matters to Luceon operators and downstream educational asset quality;
- user/operator workflow impact;
- scope and non-goals;
- relationship to current PRD v0.4 mainline;
- legacy asset policy: existing data remains legacy; new tasks use the new layout after implementation;
- cost policy: Luceon soft limit `¥5`, service hard limit `¥8`, and user/Director decision behavior;
- acceptance criteria for future CleanService/Mineru2Table integration;
- UI/review expectations for clean outputs and unresolved anchors;
- explicit failure semantics and no silent fallback;
- validation boundary: mock protocol, real Mineru2Table E2E, and operator review;
- release boundary: this addendum does not declare current production readiness.

## Non-Goals

Do not:

- edit architecture, contract, ADR, source code, runtime, production, Docker, DB, MinIO, MinerU, Ollama, or role contracts;
- copy raw zip contents into the repo;
- implement CleanServiceWorker or Mineru2Table API changes;
- mutate production or run validation;
- declare CleanService implementation accepted, pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

## Completion Report

Write:

`TaskAndReport/2026-05-15T19-29-28+0800_P1-CleanService-Mineru2Table-PRD-Addendum_REPORT.md`

Report must include:

- confirmation that work was based on this Director task brief;
- branch and HEAD;
- files changed;
- summary of PRD addendum content;
- commands/checks run;
- skipped checks and reasons;
- unresolved product questions;
- recommended next role task;
- GitHub sync status.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查`
- Next Actor: `Director`
- Next Action: Director reviews PRD addendum and decides whether to dispatch canonical architecture/contract docs reconciliation.
- Required Output: Director review.

Commit and push the addendum, report, and ledger update to GitHub `main`.

## Acceptance Criteria

Director can accept this task only if the addendum is product-scoped, reconciles the six known user decisions, and avoids claiming implementation or readiness.
