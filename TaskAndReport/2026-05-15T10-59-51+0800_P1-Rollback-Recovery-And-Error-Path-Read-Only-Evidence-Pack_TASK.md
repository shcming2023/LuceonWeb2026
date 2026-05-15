# Task Brief: P1 Rollback Recovery And Error Path Read-Only Evidence Pack

- Task ID: `TASK-20260515-105951-P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack`
- Created: 2026-05-15T10:59:51+0800
- Created by: Director
- Assigned role: `TestAcceptanceEngineer`
- Expected report: `TaskAndReport/2026-05-15T10-59-51+0800_P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack_REPORT.md`
- Based on Architect report: `TaskAndReport/2026-05-15T10-10-39+0800_P1-Rollback-Recovery-And-Error-Path-Evidence-Gap-Plan_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-15T10-59-51+0800_P1-Rollback-Recovery-And-Error-Path-Evidence-Gap-Plan_DIRECTOR_REVIEW.md`

## Context

Task 168 concluded that the remaining rollback/recovery and error-path blocker is primarily an evidence-quality gap, not a known implementation failure. Before Director asks the user to approve controlled rollback/failure-injection rehearsal or accept residual operational risk, TestAcceptanceEngineer should collect the maximum useful evidence that can be gathered without mutating production state.

This task is read-only. It must not perform upload, rollback, restart, failure injection, cleanup, retry, reparse, re-AI, restore/import, destructive operation, service mutation, config/secret/model/sample mutation, or readiness/go-live declaration.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/test-acceptance-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. Task 168 report and Director review
12. This task brief

If the task row, report, review, or role file is missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`. Do not improvise from partial context.

## Objective

Create a read-only evidence pack that classifies the remaining rollback/recovery and error-path gaps as:

- `closed by read-only evidence`;
- `requires user-approved rehearsal`;
- `accepted operational risk candidate`;
- `blocked/inconclusive`.

The evidence pack should allow Director and the user to make the next release-boundary decision without guessing.

## Allowed Operations

Allowed read-only operations:

- inspect repository docs, source code, task reports, task ledger, deploy docs, and runbooks;
- run `git status --short --branch`, `git log -1 --oneline`, and read-only file inspection in development and production paths;
- inspect Docker status with `docker compose ps`;
- perform read-only HTTP GET checks through production frontend proxy:
  - `/cms/`
  - `/cms/tasks`
  - `/__proxy/upload/health`
  - `/__proxy/upload/ops/dependency-health`
  - `/__proxy/upload/ops/mineru/admission-circuit`
  - `/__proxy/upload/ops/mineru/active-task`
  - `/__proxy/upload/audit/consistency`
  - DB health/export-shape endpoints if available, without import or restore;
- perform direct read-only MinerU `/health` check on the running host endpoint;
- inspect existing task/material/API records for representative `review-pending`, `failed/ai`, and completed/review states without invoking retry/reparse/re-AI/cancel/repair;
- inspect MinIO object inventory/counts or selected object metadata only if the command is read-only and does not download large content, delete, rewrite, import, restore, or mutate buckets/objects;
- use browser read-only navigation to capture operator-facing wording on task list/detail pages if needed.

## Forbidden Operations

Forbidden:

- rollback, fast-forward, deploy, rebuild, restart, stop, kill, attach, service mutation, or broad runtime recovery;
- failure injection;
- PDF upload, Markdown upload, pressure/batch/soak/fresh serial validation, or any new validation artifact;
- cleanup, cancel, repair, retry, reparse, re-AI, takeover, or automatic retry/requeue;
- destructive DB, MinIO, Docker volume, Docker data, or local filesystem mutation;
- DB import/restore, MinIO restore, full-backup import, object deletion, object overwrite, or Docker prune/down/down -v;
- MinerU/Ollama/supervisor mutation;
- settings, secrets, config, model, sample-library mutation, model pull/delete/replace;
- PRD truth, role contract, project state, or handoff changes;
- skeleton fallback weakening or silent degradation;
- declaring pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Required Evidence

Report must include:

1. **Runtime Snapshot**
   - development HEAD/status;
   - production HEAD/status;
   - Docker service status;
   - CMS, upload health, dependency-health, admission circuit, active-task diagnostics, direct MinerU health.

2. **Rollback / Recovery Evidence Pack**
   - source rollback evidence and missing rehearsal;
   - Docker/service recovery evidence and missing rehearsal;
   - production-local override preservation evidence;
   - DB backup/export evidence and restore boundary;
   - MinIO artifact inventory/preservation evidence and restore boundary;
   - task-state recovery / failed-task handling evidence.

3. **Error-Path Evidence Pack**
   - upload dependency failure surfaces;
   - MinerU health/submit/long-running/local-timeout surfaces;
   - MinIO unavailable/object failure surfaces;
   - DB unavailable/proxy failure surfaces;
   - Ollama missing/tags/cold/warm/chat-failure surfaces;
   - strict no-skeleton AI failure and manual retry semantics;
   - UI/task-page partial success and failed AI residual semantics.

4. **Representative Existing Task Evidence**
   - at least one `review-pending` or completed-success example if safely discoverable;
   - at least one `failed/ai` example if safely discoverable;
   - visible task/detail semantics for the above, without changing state.

5. **Gap Classification Matrix**
   - each remaining gap classified as `closed by read-only evidence`, `requires user-approved rehearsal`, `accepted operational risk candidate`, or `blocked/inconclusive`;
   - precise risk statement for every non-closed gap.

6. **Recommended Next Decision**
   - recommend one of:
     - `READY_FOR_USER_RISK_ACCEPTANCE_DECISION`;
     - `CONTROLLED_STAGING_REHEARSAL_RECOMMENDED`;
     - `CONTROLLED_PRODUCTION_REHEARSAL_REQUIRES_USER_APPROVAL`;
     - `NO_GO_UNTIL_IMPLEMENTATION_FIX`;
   - include the exact decision Director should present to the user.

7. **Forbidden Operations Confirmation**
   - explicitly list that no forbidden operation was performed.

## GitHub Sync

Do not fetch, pull, push, merge, or create commits unless Director explicitly instructs you. Work in the current synchronized workspace. Write the report and update the task row locally; Director will review and handle GitHub synchronization.

## Completion

Write:

`TaskAndReport/2026-05-15T10-59-51+0800_P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack_REPORT.md`

Update row 170 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Notes include the highest-priority remaining release-boundary decision.
