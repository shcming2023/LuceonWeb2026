# Task Brief: P1 Production Source Drift And Override Boundary Read-Only Classification

- Task ID: `TASK-20260515-085508-P1-Production-Source-Drift-And-Override-Boundary-Read-Only-Classification`
- Created: 2026-05-15T08:55:08+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-15T08-55-08+0800_P1-Production-Source-Drift-And-Override-Boundary-Read-Only-Classification_REPORT.md`
- Based on Architect report: `TaskAndReport/2026-05-15T08-46-31+0800_P1-Release-Readiness-Consolidation-And-Gap-Refresh_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-15T08-55-08+0800_P1-Release-Readiness-Consolidation-And-Gap-Refresh_DIRECTOR_REVIEW.md`

## Context

Task 162 accepted a `CONDITIONAL_GO_AFTER_SPECIFIC_TASKS` release-readiness boundary. The first concrete blocker is production source/runtime drift.

Production currently reports these local modified files:

- `.gitignore`
- `docker-compose.override.yml`
- `server/db-server.mjs`
- `server/tests/worker-smoke.mjs`
- `src/app/components/BatchUploadModal.tsx`
- `src/app/pages/SourceMaterialsPage.tsx`

Architect observed that some diffs appear line-ending-only, while `docker-compose.override.yml` contains meaningful local runtime override changes. Director spot-check confirmed the same six-file drift and `git diff --stat` of `6 files changed, 134 insertions(+), 130 deletions(-)`.

Before a final release/go-live decision, each dirty production file must be classified and assigned a minimum next action. This task is read-only classification only.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/development-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/prd/Luceon2026-Stability-PRD-v0.1.md` if present
8. `docs/codex/TEST_POLICY.md`
9. `docs/codex/REPOSITORY_STRUCTURE.md`
10. `TaskAndReport/README.md`
11. `TaskAndReport/TASK_TRACKING_LIST.md`
12. Task 162 report and Director review
13. This task brief

If the task row, role file, or Task 162 report/review is missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`.

## Objective

Classify production source/runtime drift read-only.

For each of the six modified files, determine:

- whether the diff is line-ending-only, whitespace-only, meaningful source change, expected production-local override, or unknown;
- whether it affects runtime behavior;
- whether it blocks a clean release-readiness decision;
- the minimum recommended next action:
  - record as expected production-local override;
  - normalize line endings in a later scoped task;
  - port/commit an intentional source change in a later scoped task;
  - revert/restore in a later approved task;
  - hold as blocker needing user/Director decision.

## Allowed Operations

Allowed read-only operations:

- development and production `git status --short --branch`;
- production `git log -1 --oneline`;
- production `git diff --stat`, `git diff --name-only`, `git diff --numstat`;
- production `git diff -- <file>`;
- whitespace-aware comparisons such as:
  - `git diff --ignore-space-at-eol -- <file>`;
  - `git diff -w -- <file>`;
  - `git diff --check`;
- read-only file inspection with `sed`, `rg`, `file`, `wc`, or similar;
- read-only Docker/health checks only if needed to confirm current runtime still healthy;
- write the DevelopmentEngineer report and update row 163 locally.

## Forbidden Operations

Forbidden:

- modifying, normalizing, reverting, staging, committing, or deleting any production file;
- `git checkout`, `git restore`, `git reset`, `git clean`, or any equivalent mutation in production;
- production fast-forward, pull, rebuild, restart, deploy, rollback, or config mutation;
- Docker down, volume/data cleanup, prune;
- upload, pressure/batch/soak/fresh serial validation;
- cleanup/cancel/repair/retry/reparse/re-AI;
- destructive DB/MinIO/Docker volume/data mutation;
- service start/stop/restart/rebuild, including MinerU/Ollama/supervisor mutation;
- settings/secrets/config/model/sample mutation;
- automatic retry/requeue;
- skeleton fallback weakening;
- PRD truth, role contract, project state, or handoff changes;
- declaring pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Required Report

Write:

`TaskAndReport/2026-05-15T08-55-08+0800_P1-Production-Source-Drift-And-Override-Boundary-Read-Only-Classification_REPORT.md`

The report must include:

1. Confirmation this work was based on this Director task brief.
2. Required reading completed.
3. Exact production branch/HEAD and dirty-file list.
4. A table for all six files:
   - file path;
   - diff type;
   - runtime impact;
   - release-readiness impact;
   - recommended next action;
   - whether Director/User decision is needed.
5. Evidence snippets or command summaries sufficient to support each classification.
6. Overall recommendation:
   - `SOURCE_DRIFT_BLOCKER`;
   - `SOURCE_DRIFT_CONDITIONAL_CLEAR_AFTER_RECORD`;
   - or `SOURCE_DRIFT_CLEAR`.
7. Explicit statement that no production mutation, cleanup, deploy, restart, upload, retry/reparse/re-AI, destructive operation, or readiness/go-live claim was made.

Update row 163 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or precise blocked status;
- Next Actor: `Director`;
- Report path populated.
