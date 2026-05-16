# Task: P1 CleanService Disabled Worker Shell And Metadata Persistence

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
TaskAndReport/2026-05-16T08-15-14+0800_P1-CleanService-Disabled-Worker-Shell-And-Metadata-Persistence_TASK.md

Expected report:
TaskAndReport/2026-05-16T08-15-14+0800_P1-CleanService-Disabled-Worker-Shell-And-Metadata-Persistence_REPORT.md

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
- `TaskAndReport/2026-05-16T08-02-16+0800_P1-CleanService-Mock-Protocol-Foundation-Disabled-By-Default_TASK.md`
- `TaskAndReport/2026-05-16T08-02-16+0800_P1-CleanService-Mock-Protocol-Foundation-Disabled-By-Default_REPORT.md`
- `TaskAndReport/2026-05-16T08-15-14+0800_P1-CleanService-Mock-Protocol-Foundation-Disabled-By-Default_DIRECTOR_REVIEW.md`

## Background

Task 200 established isolated CleanService foundation helpers, default-disabled config, protocol normalization, product state/cost mapping, bounded metadata summaries, mock output/provenance verification, and no-silent-fallback coverage.

The next step is not real integration. It is a worker shell and persistence contract that proves Luceon can orchestrate a future clean stage without touching current runtime startup or calling a real external service.

## Objective

Implement an isolated, disabled-by-default `CleanServiceWorker` shell and metadata persistence contract using injected dependencies and mock tests only.

The worker shell should make the future lifecycle testable:

1. load config and no-op when disabled;
2. scan eligible parsed tasks through an injected task source;
3. avoid duplicate dispatch when a clean job is already active or terminal;
4. submit through an injected CleanService client only when enabled in a focused test;
5. persist bounded task/material metadata patches through an injected persistence adapter;
6. preserve product state/cost/error/no-silent-fallback semantics from Task 200.

## Required Implementation Boundaries

The current mainline remains:

```text
upload -> local MinerU -> MinIO -> Ollama qwen3.5:9b -> AI metadata -> operator review
```

Do not alter that runtime path in this task.

The worker shell must not be mounted, imported, or auto-started by `server/upload-server.mjs`, `ParseTaskWorker`, `AiMetadataWorker`, Docker, production config, or any runtime entrypoint.

All worker tests must use in-memory mock task sources, mock persistence adapters, and mock CleanService clients/transports.

## Allowed Files

DevelopmentEngineer may modify or add narrowly scoped files under:

- `server/services/cleanservice/**`
- `server/tests/cleanservice-*.mjs`
- existing server test helper files only if needed for focused tests
- `TaskAndReport/2026-05-16T08-15-14+0800_P1-CleanService-Disabled-Worker-Shell-And-Metadata-Persistence_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

If a small existing module import/export is unavoidable, record the reason in the report and keep the change minimal.

Do not edit UI, PRD truth, role contracts, `PROJECT_STATE`, `HANDOFF`, production files, Docker Compose, external repositories, or the Mineru2Table2026 repository in this task.

## Required Behavior

Implement the smallest maintainable worker shell that satisfies:

1. Disabled no-op:
   - default config makes `tickOnce()` return a no-op result;
   - no task scan, no submit, and no persistence call occurs when disabled.
2. Eligibility:
   - a task is eligible only when it has completed MinerU/parsed artifact evidence sufficient for future CleanService input;
   - canceled/failed tasks and tasks without parsed artifact evidence are not eligible;
   - tasks with active or terminal `metadata.cleanServiceJobs[serviceName]` are not re-submitted.
3. Mock dispatch:
   - with enabled mock config and injected mock client, the worker can submit one eligible task and produce a bounded metadata patch;
   - active concurrency remains effectively one per `tickOnce()`.
4. Metadata persistence contract:
   - task metadata patch uses `cleanServiceJobs[serviceName]`;
   - material metadata patch uses `cleanMaterials[serviceName]`;
   - summaries contain ObjectRefs and small stats only, no large artifacts/content.
5. State mapping:
   - partial unresolved anchors remain `review-pending` intent with clean substatus;
   - `¥5` soft-limit state remains decision-needed;
   - `¥8` hard-limit, timeout, protocol/output/provenance failure remain explicit failure states.
6. No real side effects:
   - no real HTTP request;
   - no production command;
   - no DB/MinIO mutation except mocked in test.

## Non-Goals / Forbidden Actions

- Do not wire the worker into production/runtime startup.
- Do not dispatch to real Mineru2Table.
- Do not call production services.
- Do not mutate production, Docker, DB, MinIO, MinerU, Ollama, models, secrets, configs, samples, or external repositories.
- Do not run submit-probe, upload, pressure/batch/soak validation, retry, reparse, re-AI, cleanup, repair, reset, or task-state reconciliation.
- Do not migrate, hide, delete, or backfill legacy assets.
- Do not globally replace material IDs with hash IDs.
- Do not change current public runtime API or task top-level status unions.
- Do not claim production acceptance, production readiness, release readiness, L3, pressure PASS, production上线, or go-live.

## Required Checks

Run and record exit codes:

- `git status --short --branch`
- `git diff --check`
- `node --check` for every changed `.mjs` server file
- existing `node server/tests/cleanservice-foundation-smoke.mjs`
- new focused worker-shell smoke test
- `npx pnpm@10.4.1 exec tsc --noEmit`

Run `npx pnpm@10.4.1 run build` if any frontend, TypeScript app, shared type, or build-sensitive file is touched. If skipped, record the exact reason.

Do not run production checks for this task.

## Required Evidence In Report

The report must include:

- confirmation that this Director task brief was followed;
- branch and HEAD;
- files changed;
- implementation summary;
- explicit evidence that the worker shell is not wired into runtime startup;
- mock dispatch and metadata persistence evidence;
- commands run with exit codes;
- skipped checks and exact reasons;
- residual risks and next recommended role/task;
- whether Director review is required.

## Completion

Write:

`TaskAndReport/2026-05-16T08-15-14+0800_P1-CleanService-Disabled-Worker-Shell-And-Metadata-Persistence_REPORT.md`

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

- default disabled behavior is a true no-op;
- worker shell is isolated and not wired into current runtime;
- eligibility, idempotency, one-at-a-time mock dispatch, and metadata persistence are covered by focused tests;
- existing CleanService foundation tests still pass;
- no real external service, production, upload, pressure, submit-probe, cleanup, or migration operation occurred;
- no-silent-fallback and product state/cost boundaries remain intact.

