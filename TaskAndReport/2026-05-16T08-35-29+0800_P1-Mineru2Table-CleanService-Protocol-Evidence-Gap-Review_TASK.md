# Task: P1 Mineru2Table CleanService Protocol Evidence Gap Review

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

Related external service:
Mineru2Table2026 / Mineru2Tables, expected GitHub direction `shcming2023/Mineru2Table2026`

TaskAndReport record:
TaskAndReport/2026-05-16T08-35-29+0800_P1-Mineru2Table-CleanService-Protocol-Evidence-Gap-Review_TASK.md

Expected report:
TaskAndReport/2026-05-16T08-35-29+0800_P1-Mineru2Table-CleanService-Protocol-Evidence-Gap-Review_REPORT.md

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
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`
- `TaskAndReport/2026-05-15T20-21-23+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_REPORT.md`
- `TaskAndReport/2026-05-16T07-46-08+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_DIRECTOR_REVIEW.md`
- `TaskAndReport/2026-05-16T08-35-29+0800_P1-CleanService-Worker-Eligibility-InputRef-Correction_DIRECTOR_REVIEW.md`

## Background

Luceon now has code/test-level mock CleanService foundations:

- disabled-by-default CleanService protocol helpers;
- isolated worker shell;
- input ObjectRef eligibility correction.

These are not real runtime capabilities. Real Mineru2Table dispatch remains blocked until the external service evidence is clear.

## Objective

Perform a read-only architecture evidence/gap review of Mineru2Table as a future CleanService implementation against Luceon's `CleanService-Protocol-v1`.

The goal is to decide what must be built or proven outside Luceon before Luceon may safely proceed toward callback/polling, runtime wiring, or real dispatch.

## Scope

Read-only only.

Architect should inspect available evidence in this repository first, then inspect the external service only if it is locally available or publicly reachable in a non-mutating way.

Candidate local paths to check read-only if they exist:

- `/Users/concm/prod_workspace/Mineru2Tables`
- `/Users/concm/prod_workspace/Mineru2Table2026`
- `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/Mineru2Table2026`
- `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/Mineru2Tables`

If no local checkout exists, report that fact and use repository/document evidence only. Do not clone, install, build, start, stop, restart, or modify the external service unless a later Director task explicitly authorizes it.

## Required Evidence Matrix

The report must classify each item as `supported`, `missing`, `partial`, or `unknown`, with evidence paths/commands:

1. `/health` shape and service identity/version/protocol fields.
2. `POST /api/v1/jobs` or equivalent ObjectRef job submission.
3. `GET /api/v1/jobs/{job_id}` or equivalent persistent job status query.
4. Persistent job state across process restart.
5. Idempotency by `job_id`.
6. MinIO ObjectRef input support.
7. MinIO ObjectRef output support.
8. Required artifacts: `flooded_content`, `logic_tree`, `readable_tree`, `skeleton`, `provenance`.
9. Provenance fields matching service name, protocol version, material id, asset version, input object, output objects, and cost/token stats.
10. Callback/webhook support or clear polling-only contract.
11. Structured errors matching `CleanService-Protocol-v1`.
12. Cost limit support: Luceon soft `¥5` decision signal and service hard `¥8` stop semantics.
13. Timeout and retry semantics.
14. Security/auth shape: API key and callback signature, if applicable.
15. Current gaps that block Luceon real dispatch.

## Non-Goals / Forbidden Actions

- Do not implement code.
- Do not edit the external Mineru2Table repository.
- Do not edit Luceon source code.
- Do not mutate production, Docker, DB, MinIO, MinerU, Ollama, models, secrets, configs, samples, or external repositories.
- Do not run upload, pressure/batch/soak validation, submit-probe, retry, reparse, re-AI, cleanup, repair, reset, or task-state reconciliation.
- Do not start, stop, restart, build, install, migrate, or deploy Mineru2Table.
- Do not run destructive Git commands.
- Do not claim production acceptance, production readiness, release readiness, L3, pressure PASS, production上线, or go-live.

## Allowed Files

- Required report under `TaskAndReport/`.
- `TaskAndReport/TASK_TRACKING_LIST.md`.

Do not edit architecture docs in this task. If docs need revision, propose exact follow-up changes in the report.

## Required Checks / Commands

Run and record exit codes:

- `git status --short --branch`
- `rg -n "\\| Architect \\|" TaskAndReport/TASK_TRACKING_LIST.md`
- Read all required Luceon files above.
- Read-only checks for candidate external paths, such as `test -d`, `git -C <path> status --short --branch`, `rg`, `sed`, or `find`.

Optional: If an already-running local Mineru2Table service is discovered, Architect may run read-only `curl`/health checks only. Do not start or restart anything.

No build, TypeScript, runtime, production, upload, pressure, or submit-probe checks are required.

## Required Report

Write:

`TaskAndReport/2026-05-16T08-35-29+0800_P1-Mineru2Table-CleanService-Protocol-Evidence-Gap-Review_REPORT.md`

The report must include:

- confirmation that this Director task brief was followed;
- branch and HEAD;
- external path/repository evidence found or not found;
- protocol evidence matrix;
- blockers for Luceon real dispatch;
- recommended next tasks, separated into external-service work vs Luceon work;
- commands run and exit codes;
- skipped checks and exact reasons;
- explicit non-readiness boundary;
- whether Director review is required.

## Completion

Update this task row in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Branch / HEAD populated;
- Notes summarize external evidence/gaps and recommended next actor.

## GitHub Sync Requirements

- Before starting: run `git status --short --branch`.
- Do not overwrite unrelated worktree changes.
- If repository files are changed, commit and push to GitHub `main`.

## Acceptance Criteria

Director can accept the task if:

- it is read-only and evidence-grounded;
- it clearly separates supported, missing, partial, and unknown external-service capabilities;
- it identifies blockers before real Luceon dispatch;
- it recommends concrete next tasks without claiming readiness;
- it does not mutate runtime, production, external repositories, data, models, configs, or samples.

