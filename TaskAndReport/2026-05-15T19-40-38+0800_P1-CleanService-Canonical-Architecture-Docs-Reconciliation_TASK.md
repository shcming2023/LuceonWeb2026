# Task: P1 CleanService Canonical Architecture Docs Reconciliation

- Task ID: `TASK-20260515-194038-P1-CleanService-Canonical-Architecture-Docs-Reconciliation`
- Assignee: `Architect`
- Issued by: `Director`
- Issued at: 2026-05-15T19:40:38+0800
- Priority: P1
- Project: Luceon2026
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- GitHub: `https://github.com/shcming2023/Luceon2026`
- Task brief: `TaskAndReport/2026-05-15T19-40-38+0800_P1-CleanService-Canonical-Architecture-Docs-Reconciliation_TASK.md`
- Expected report: `TaskAndReport/2026-05-15T19-40-38+0800_P1-CleanService-Canonical-Architecture-Docs-Reconciliation_REPORT.md`

## Required Reading

Before execution, read:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/architect.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-15T19-21-13+0800_P1-CleanService-Mineru2Table-Docs-Absorption_REPORT.md`
- `TaskAndReport/2026-05-15T19-29-28+0800_P1-CleanService-Mineru2Table-Docs-Absorption_DIRECTOR_REVIEW.md`
- `TaskAndReport/2026-05-15T19-29-28+0800_P1-CleanService-Mineru2Table-PRD-Addendum_REPORT.md`
- `TaskAndReport/2026-05-15T19-40-38+0800_P1-CleanService-Mineru2Table-PRD-Addendum_DIRECTOR_REVIEW.md`

## Objective

Write reconciled canonical architecture/contract documents for the future CleanService/Mineru2Table direction, based on the accepted PRD addendum and Architect absorption report.

Allowed docs to create:

- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- `docs/contracts/CleanService-Protocol-v1.md`
- `docs/codex/decisions/2026-05-15_clean-pipeline-foundation.md`
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`

Also write the required Architect report and update the task ledger.

## Required Reconciliation

The canonical docs must not be raw copies of the zip drafts. They must incorporate:

- PRD addendum product boundary;
- Q-1: legacy data retained; new tasks use new layout only after implementation;
- Q-2: Luceon assigns `assetVersion`;
- Q-3: no fixed old-version retention count in this phase;
- Q-4: no automatic cleanup in this phase;
- Q-5: old multipart routes deprecated but retained for at least one version cycle;
- Q-6: Luceon soft cost limit `¥5`, service hard limit `¥8`;
- explicit failure/no silent fallback;
- MinIO object-reference handoff;
- byte-identical shared protocol obligation with Mineru2Table2026;
- statement that these docs are future architecture direction, not current production readiness.

## Non-Goals

Do not:

- edit source code, runtime, production files, Docker, DB, MinIO, MinerU, Ollama, role contracts, `PROJECT_STATE`, or `HANDOFF`;
- copy the raw zip into the repository;
- implement CleanServiceWorker or Mineru2Table API changes;
- mutate production or run validation;
- claim implementation acceptance, pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

## Completion Report

Write:

`TaskAndReport/2026-05-15T19-40-38+0800_P1-CleanService-Canonical-Architecture-Docs-Reconciliation_REPORT.md`

Report must include:

- confirmation that work was based on this Director task brief;
- branch and HEAD;
- files changed;
- summary of each canonical doc;
- commands/checks run;
- skipped checks and reasons;
- unresolved architecture questions;
- recommended next role task;
- GitHub sync status.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查`
- Next Actor: `Director`
- Next Action: Director reviews canonical architecture docs and decides whether to accept, return for revision, or dispatch implementation planning.
- Required Output: Director review.

Commit and push the docs, report, and ledger update to GitHub `main`.

## Acceptance Criteria

Director can accept this task only if the docs are internally consistent, reflect the PRD addendum, resolve the stale draft issues, and avoid claiming implementation/runtime readiness.
