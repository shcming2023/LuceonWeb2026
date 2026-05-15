# Task: P1 CleanService Product State And Workflow Decisions

Assignee:
ProductManager

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
TaskAndReport/2026-05-16T07-46-08+0800_P1-CleanService-Product-State-And-Workflow-Decisions_TASK.md

Expected report:
TaskAndReport/2026-05-16T07-46-08+0800_P1-CleanService-Product-State-And-Workflow-Decisions_REPORT.md

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/product-manager.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- `docs/contracts/CleanService-Protocol-v1.md`
- `docs/codex/decisions/2026-05-15_clean-pipeline-foundation.md`
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`
- `TaskAndReport/2026-05-15T20-21-23+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_REPORT.md`
- `TaskAndReport/2026-05-16T07-46-08+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_DIRECTOR_REVIEW.md`

## Background

Architect completed and Director accepted the Luceon-side CleanServiceWorker implementation plan at planning level only.

Before any DevelopmentEngineer implementation task is safe, ProductManager must clarify product/workflow semantics that should not be guessed in code.

## Objective

Produce a ProductManager decision report that answers or frames the product decisions needed before CleanServiceWorker implementation planning can become implementation tasks.

## Required Decisions / Analysis

Address each item explicitly:

1. Should `toc-rebuild` gate all AI metadata, or only future chapter-level AI/enrichment workflows?
2. What exact operator-facing labels should be used for clean-stage states?
3. How should the `¥5` soft-limit pause appear in task detail, task list, and task ledger?
4. Is future hash-based `materialId` global, or scoped only to new CleanService-enabled assets?
5. How should legacy assets be labeled in library and task views?
6. Should partial output with unresolved anchors map to `review-pending`, a new clean-specific review state, or a folded diagnostic under existing task state?
7. Who should own cross-repo byte-identical CleanService protocol sync: Director manually, paired task briefs, or a future GitHub workflow?
8. Which decisions can ProductManager recommend now, and which still require explicit User/Director decision?

## Non-Goals

- Do not implement code.
- Do not edit production files.
- Do not mutate runtime, Docker, DB, MinIO, MinerU, Ollama, models, secrets, configs, samples, or external repositories.
- Do not run submit-probe, upload, pressure, retry, reparse, re-AI, cleanup, repair, or validation uploads.
- Do not claim CleanService implementation acceptance, production readiness, release readiness, L3, pressure PASS, production上线, or go-live.
- Do not edit role contracts, `PROJECT_STATE`, or `HANDOFF`.
- Do not edit the external Mineru2Table2026 repository.

## Allowed Files

- Required report under `TaskAndReport/`.
- `TaskAndReport/TASK_TRACKING_LIST.md`.

If ProductManager believes the CleanService PRD addendum needs revision, do not edit it in this task. Record the proposed revision and reason in the report.

## Required Checks

- `git status --short --branch`
- `rg -n "\\| ProductManager \\|" TaskAndReport/TASK_TRACKING_LIST.md`
- Read all required files listed above.

No build, TypeScript, runtime, production, upload, pressure, or submit-probe checks are required for this product-decision task.

## Required Evidence In Report

The report must include:

- confirmation that this Director task brief was followed;
- branch and HEAD;
- files changed;
- decision table for the 8 required items;
- recommended default path for DevelopmentEngineer implementation;
- User/Director decisions still required, if any;
- product acceptance criteria for the first mock/disabled CleanService foundation;
- risks and product tradeoffs;
- commands run and exit codes;
- skipped checks and reasons;
- GitHub sync status;
- whether Director review is required.

## Completion

Write:

`TaskAndReport/2026-05-16T07-46-08+0800_P1-CleanService-Product-State-And-Workflow-Decisions_REPORT.md`

Update this task row in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Branch / HEAD populated;
- Notes summarize product decisions and any User/Director decision points.

## GitHub Sync Requirements

- Before starting: run `git status --short --branch`.
- Do not automatically fetch/pull unless the task ledger or Director explicitly requires it, or GitHub sync is needed to resolve a ledger mismatch.
- If repository files are changed, commit and push to GitHub `main`.
- Do not overwrite unrelated worktree changes.

## Acceptance Criteria

Director can accept the task if:

- the report is standalone and grounded in current PRD/addendum/architecture plan;
- it gives practical product defaults rather than only repeating open questions;
- it separates ProductManager recommendations from User-owned decisions;
- it preserves current Phase 1 runtime and no-silent-fallback boundaries;
- it does not implement or mutate runtime;
- all residual decisions and risks are explicit.
