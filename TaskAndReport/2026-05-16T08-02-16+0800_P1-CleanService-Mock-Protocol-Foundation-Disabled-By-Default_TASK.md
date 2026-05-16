# Task: P1 CleanService Mock Protocol Foundation Disabled By Default

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
TaskAndReport/2026-05-16T08-02-16+0800_P1-CleanService-Mock-Protocol-Foundation-Disabled-By-Default_TASK.md

Expected report:
TaskAndReport/2026-05-16T08-02-16+0800_P1-CleanService-Mock-Protocol-Foundation-Disabled-By-Default_REPORT.md

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md`
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
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`
- `docs/codex/decisions/2026-05-15_clean-pipeline-foundation.md`
- `TaskAndReport/2026-05-15T20-21-23+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_REPORT.md`
- `TaskAndReport/2026-05-16T07-46-08+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_DIRECTOR_REVIEW.md`
- `TaskAndReport/2026-05-16T07-46-08+0800_P1-CleanService-Product-State-And-Workflow-Decisions_REPORT.md`
- `TaskAndReport/2026-05-16T08-02-16+0800_P1-CleanService-Product-State-And-Workflow-Decisions_DIRECTOR_REVIEW.md`

## Background

Architect proposed a separate Luceon CleanService orchestration layer. ProductManager clarified the first product defaults:

- existing AI metadata must not wait for `toc-rebuild`;
- clean-stage labels focus on directory/structure rebuild;
- `¥5` soft limit pauses for Director/User decision, `¥8` hard limit fails explicitly;
- hash-based identity is scoped to new CleanService-enabled assets first;
- legacy assets stay visible as informational `历史解析资产` / `Legacy parse-only`;
- partial unresolved anchors map to existing `review-pending` with clean substatus;
- real Mineru2Table dispatch waits for protocol evidence.

This task starts only the Luceon-side mock/protocol foundation. It is not a real external-service integration task.

## Objective

Implement a disabled-by-default CleanService mock/protocol foundation that can be tested locally without changing current Phase 1 behavior.

The foundation should establish the code contracts needed for later work:

- cleanservice configuration with default disabled behavior;
- protocol response/error normalization;
- product state and label mapping helpers;
- cost policy helpers for `¥5` soft pause and `¥8` hard stop;
- bounded task/material metadata summary helpers;
- mock output/provenance verification;
- focused tests for success, partial review, cost decision, hard-limit failure, timeout, and protocol failure.

## Required Implementation Boundaries

The current mainline remains:

```text
upload -> local MinerU -> MinIO -> Ollama qwen3.5:9b -> AI metadata -> operator review
```

Do not alter that runtime path in this task.

The CleanService foundation must be disabled by default. No worker should auto-start and no real external service call should occur unless a focused test injects a mock transport.

## Allowed Files

DevelopmentEngineer may modify or add narrowly scoped files under:

- `server/services/cleanservice/**`
- `server/tests/cleanservice-*.mjs`
- existing server test helper files only if needed for focused tests
- `TaskAndReport/2026-05-16T08-02-16+0800_P1-CleanService-Mock-Protocol-Foundation-Disabled-By-Default_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

If a small export or import from an existing server module is unavoidable, record the reason in the report and keep the change minimal.

Do not edit UI, PRD truth, role contracts, `PROJECT_STATE`, `HANDOFF`, production files, Docker Compose, external repositories, or the Mineru2Table2026 repository in this task.

## Required Behavior

Implement the smallest maintainable foundation that satisfies these behaviors:

1. Feature default:
   - CleanService is disabled by default.
   - Missing endpoint/API key/callback secret must not break current startup.
   - Disabled state should be representable as `未启用` / `not-enabled`.
2. Protocol normalization:
   - Normalize mock submit/query responses into a stable Luceon job summary.
   - Normalize transport timeout and protocol error cases without throwing unclassified errors to callers.
   - Do not perform a real HTTP request unless a test explicitly injects a mock transport.
3. Product state mapping:
   - Support clean states for not-enabled, not-applicable, pending, running, review-pending partial, completed, skipped, cost-decision, hard-limit failed, timeout, and protocol failure.
   - Use product labels from Task 199.
   - Partial unresolved anchors must map to existing task-level `review-pending` intent through a clean-specific substatus, not hidden success.
4. Cost policy:
   - `¥5` soft limit produces a paused/cost-decision state that requires Director/User decision.
   - `¥8` hard limit produces explicit failure, not silent continuation.
5. Metadata summaries:
   - Build bounded summary objects suitable for `task.metadata.cleanServiceJobs` and `material.metadata.cleanMaterials`.
   - Store ObjectRefs and small stats only; do not store large clean artifacts in DB summaries.
6. Output/provenance verification:
   - Validate mock required ObjectRefs and provenance shape before representing clean success.
   - Missing provenance or required artifacts must be failure/review evidence, not success.
7. No-silent-fallback:
   - Raw MinerU output, placeholder output, or skeleton output must never be labeled as clean success.

## Non-Goals / Forbidden Actions

- Do not dispatch to real Mineru2Table.
- Do not call production services.
- Do not mutate production, Docker, DB, MinIO, MinerU, Ollama, models, secrets, configs, samples, or external repositories.
- Do not run submit-probe, upload, pressure/batch/soak validation, retry, reparse, re-AI, cleanup, repair, reset, or task-state reconciliation.
- Do not start a CleanService worker in runtime.
- Do not migrate, hide, delete, or backfill legacy assets.
- Do not globally replace material IDs with hash IDs.
- Do not change public runtime API or current task top-level status unions unless a tiny internal type/helper is necessary and explained.
- Do not claim implementation production acceptance, production readiness, release readiness, L3, pressure PASS, production上线, or go-live.

## Required Checks

Run and record exit codes:

- `git status --short --branch`
- `git diff --check`
- `node --check` for every changed `.mjs` server file
- focused CleanService tests added by this task
- `npx pnpm@10.4.1 exec tsc --noEmit`

Run `npx pnpm@10.4.1 run build` if any frontend, TypeScript app, shared type, or build-sensitive file is touched. If skipped, record the exact reason.

Do not run production checks for this task.

## Required Evidence In Report

The report must include:

- confirmation that this Director task brief was followed;
- branch and HEAD;
- files changed;
- implementation summary;
- explicit statement that feature default is disabled and no real external service is called;
- product state/cost/error mapping summary;
- commands run with exit codes;
- skipped checks and exact reasons;
- evidence that existing Phase 1 runtime path was not changed;
- residual risks and next recommended role/task;
- whether Director review is required.

## Completion

Write:

`TaskAndReport/2026-05-16T08-02-16+0800_P1-CleanService-Mock-Protocol-Foundation-Disabled-By-Default_REPORT.md`

Update this task row in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Branch / HEAD populated;
- Notes summarize implementation scope, checks, and residual risks.

## GitHub Sync Requirements

- Before starting: run `git status --short --branch`.
- Work on current `main` unless local policy or branch state requires a scoped branch.
- Do not overwrite unrelated worktree changes.
- If repository files are changed, commit and push to GitHub `main` after checks pass.

## Acceptance Criteria

Director can accept the task if:

- the foundation is disabled by default;
- existing Phase 1 flow is untouched;
- mock protocol/state/cost/error/output verification behavior is covered by focused tests;
- no real external service, production, upload, pressure, submit-probe, or cleanup operation occurred;
- no-silent-fallback is preserved;
- residual real-integration decisions remain explicit.

