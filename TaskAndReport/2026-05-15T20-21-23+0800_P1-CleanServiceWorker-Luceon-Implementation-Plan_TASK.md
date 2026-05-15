# Task: P1 CleanServiceWorker Luceon Implementation Plan

Assignee:
Architect

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
TaskAndReport/2026-05-15T20-21-23+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_TASK.md

Expected report:
TaskAndReport/2026-05-15T20-21-23+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_REPORT.md

## Required Reading Before Execution

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
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- `docs/contracts/CleanService-Protocol-v1.md`
- `docs/codex/decisions/2026-05-15_clean-pipeline-foundation.md`
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`
- `TaskAndReport/2026-05-15T20-21-23+0800_P1-CleanService-Canonical-Architecture-Docs-Reconciliation_DIRECTOR_REVIEW.md`

## Background

Task 186 created and reconciled the canonical CleanService planning documents. Director accepted them at documentation level only.

The next step is not implementation. The next step is a concrete Luceon-side implementation plan that can later be broken into safe DevelopmentEngineer tasks after the external Mineru2Table protocol dependency is understood.

## Current Known Facts

- Current Phase 1 runtime remains upload -> local MinerU -> MinIO -> Ollama `qwen3.5:9b` -> AI metadata -> operator review.
- CleanService / Mineru2Table is future architecture direction, not current runtime capability.
- Canonical integration must use MinIO ObjectRefs, not long-term multipart upload.
- Luceon owns material identity/version semantics.
- Failure must be explicit; no silent fallback or fake success is allowed.
- Cost policy is `¥5` Luceon soft limit and `¥8` service hard limit.
- No fixed old-version retention count and no automatic cleanup are authorized.

## Objective

Write an Architect implementation plan for Luceon-side CleanServiceWorker integration.

The plan must be specific enough for later task dispatch, but must remain architecture/planning only.

## Required Analysis

Cover at least:

- proposed Luceon modules/files likely to change;
- CleanServiceWorker lifecycle and queue ownership;
- MinIO ObjectRef input/output flow;
- DB/task/material state mapping;
- `assetVersion` and provenance storage model;
- operator-review UI state labels and evidence surfaces;
- callback/webhook or polling strategy;
- admission, backpressure, timeout, and retry boundaries;
- error taxonomy and no-silent-fallback behavior;
- cost-limit enforcement (`¥5` soft, `¥8` hard);
- migration boundary for existing materials;
- dependencies that must be completed in Mineru2Table2026 before Luceon implementation;
- test strategy split: unit, contract/mock, integration, production read-only, real E2E, and release-boundary validation;
- open questions that still require ProductManager/User decision.

## Non-Goals

- Do not implement code.
- Do not edit production files.
- Do not mutate runtime, Docker, DB, MinIO, MinerU, Ollama, models, secrets, configs, or samples.
- Do not run submit-probe, upload, pressure, retry, reparse, re-AI, cleanup, or repair.
- Do not claim implementation acceptance, production readiness, release readiness, L3, pressure PASS, production上线, or go-live.
- Do not edit PRD truth, role contracts, `PROJECT_STATE`, or `HANDOFF`.
- Do not edit the external Mineru2Table2026 repository.

## Allowed Files

- Required report under `TaskAndReport/`.
- `TaskAndReport/TASK_TRACKING_LIST.md`.

If you believe canonical docs need revision, do not edit them in this task. Record the proposed revision and reason in the report.

## Required Checks

- `git status --short --branch`
- `rg -n "\\| Architect \\|" TaskAndReport/TASK_TRACKING_LIST.md`
- Read all required files listed above.
- Optional but encouraged: `rg` targeted searches over `server/`, `src/`, `docs/`, and `TaskAndReport/` to ground module planning.

No build, TypeScript, runtime, production, upload, pressure, or submit-probe checks are required for this planning-only task.

## Required Evidence In Report

The report must include:

- confirmation that this task brief was followed;
- branch and HEAD;
- files changed;
- implementation-plan summary;
- module/file impact map;
- phased dispatch proposal with task boundaries;
- required dependency evidence from Mineru2Table2026;
- validation plan;
- open questions and user/product decisions needed;
- commands run and exit codes;
- skipped checks and reasons;
- GitHub sync status;
- whether Director review is required.

## GitHub Sync Requirements

- Before starting: run `git status --short --branch`.
- Do not automatically fetch/pull unless the task ledger or Director explicitly requires it, or GitHub sync is needed to resolve a ledger mismatch.
- If repository files are changed, commit and push to GitHub `main`.
- Do not overwrite unrelated worktree changes.

## Acceptance Criteria

Director can accept the task if:

- the report is standalone and grounded in current Luceon documents/code structure;
- it preserves the current PRD/runtime boundary;
- it breaks future work into safe, reviewable phases;
- it clearly separates Luceon-side work from Mineru2Table external dependency work;
- it does not implement or mutate runtime;
- all residual decisions and risks are explicit.

