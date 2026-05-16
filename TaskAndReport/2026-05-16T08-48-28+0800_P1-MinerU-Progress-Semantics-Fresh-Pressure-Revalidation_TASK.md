# P1 MinerU Progress Semantics Fresh Pressure Revalidation

Task ID: TASK-20260516-084828-P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation

Assignee: TestAcceptanceEngineer

Issued by: Director

Issued at: 2026-05-16T08:48:28+0800

Project: Luceon2026

Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path: `/Users/concm/prod_workspace/Luceon2026`

GitHub: `https://github.com/shcming2023/Luceon2026`

TaskAndReport record: `TaskAndReport/2026-05-16T08-48-28+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_TASK.md`

Expected report: `TaskAndReport/2026-05-16T08-48-28+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_REPORT.md`

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
- This task brief.

## Background

The user corrected the project sequence: do not prioritize independent Mineru2Table/CleanService external service integration yet. The active concern is whether the current production UI and observability can truthfully show MinerU progress during long-running pressure work.

Known prior evidence:

- Task 190 accepted terminal pressure-monitoring evidence, not pressure PASS/L3/release/prod/go-live.
- Task 190 residuals included operator progress semantics lag behind direct MinerU/log evidence, stale log-channel interpretation risk, and one strict no-skeleton AI failure.
- Task 192 diagnosed the root cause as flattened progress semantics without source/timestamp/freshness/confidence, plus expected DB/direct-MinerU async lag and stale-log ambiguity.
- Task 193 implemented the backend `progressSnapshot` and active-task reconciliation contract.
- Task 197 deployed/read-only validated the new `progressSnapshot` surface in production.
- There is not yet a fresh long-running pressure validation proving the new deployed progress semantics under active MinerU processing.

## Objective

Validate whether the current deployed MinerU progress semantics are trustworthy during a fresh controlled, user-started pressure run.

The key question is not "are health endpoints green"; it is whether humans can correctly judge real progress from the task page and observability surfaces while MinerU is still processing, especially when UI text, stale logs, DB task state, and direct MinerU API state diverge.

## Preconditions

- The TestAcceptanceEngineer must not clear data, upload PDFs, or start a pressure run.
- If the user has already manually cleared and uploaded pressure PDFs by the time this task is executed, observe that active run.
- If no user-started active/queued pressure run exists, write a blocked report with baseline evidence and status `BLOCKED_WAITING_FOR_USER_MANUAL_UPLOAD`. Do not manufacture test input.

## Non-goals

- Do not implement code.
- Do not change UI copy, backend logic, task state, or configuration.
- Do not validate CleanService/Mineru2Table integration.
- Do not test external Mineru2Table protocol behavior.
- Do not claim pressure PASS, L3, release readiness, production readiness, production上线, or go-live.
- Do not perform broad environment recovery.

## Allowed Operations

Read-only validation and observation only:

- Inspect production CMS task page and task details if available.
- Read no-submit health/readiness endpoints.
- Read active-task/progress diagnostic endpoints already provided by Luceon.
- Read direct MinerU status/log evidence for task IDs visible through Luceon state.
- Read DB/API task/material/AI status through existing non-mutating endpoints or read-only scripts.
- Read production logs only when that does not mutate service state.
- Record timestamps, task IDs, material IDs, MinerU task IDs, AI job IDs, and status transitions.
- Use browser screenshots only if needed for evidence; do not commit large screenshots unless explicitly required.

## Forbidden Operations

- Do not upload files.
- Do not clear/reset test data.
- Do not run manual submit-probe.
- Do not retry, reparse, re-AI, repair, cancel, reset, or edit tasks.
- Do not restart/redeploy/rebuild/rollback services.
- Do not run Docker destructive operations, including `docker compose down -v`, volume deletion, prune, or DB/MinIO data cleanup.
- Do not mutate MinIO objects, DB rows, Docker volumes, model files, secrets, environment config, or sample files.
- Do not pull/delete/replace Ollama models.
- Do not write to external Mineru2Table.
- Do not synchronize sample files into the repository.

## Required Observation Focus

For each sampled observation during an active run, record:

- Wall-clock timestamp.
- Visible page/task semantic text and whether it suggests active progress, queued state, terminal success, terminal failure, stale/unknown state, or DB-behind-direct-MinerU lag.
- Luceon `progressSnapshot` fields, including source, status, freshness/staleness, confidence, message, timestamps, and any direct-MinerU reconciliation fields.
- Direct MinerU API status for the matching MinerU task when available: `status`, `error`, `completed_at`, latest known stage/progress/log step.
- Whether MinerU logs/API show continuing progress even if page semantics look stalled.
- Luceon DB/task/material state, including parse status, material `mineruStatus`, AI job status, and review state.
- Queue pressure or active-task evidence.
- Any stale log-channel or sidecar observation and how it was distinguished from real active work.

Do not declare a task failed solely because the page appears stalled if direct MinerU API or logs still show forward movement.

## Suggested Monitoring Cadence

If a fresh user-started pressure run is active:

- Capture an initial baseline immediately.
- During active MinerU processing, capture observations at a cadence that is frequent enough to show stage transitions and semantic lag. Prefer 5-10 minute snapshots while there is active movement.
- Continue until all user-started pressure tasks reach terminal states, or until there is a clear no-progress condition.
- If direct MinerU API/log evidence still shows progress, keep observing rather than calling failure.
- If the run is still active after 120 minutes, report the current state as still-running/inconclusive unless there is strong no-progress evidence.

## Required Checks

No code checks are required unless repository files are changed. This task should not change code.

Required command/evidence checks:

- `git status --short --branch` in the development workspace.
- Confirm whether production currently has active/queued pressure tasks.
- Confirm whether dependency-health is readiness-only and not used as progress truth.
- Confirm whether `progressSnapshot.version=progress-snapshot-v0.1` is visible in production before interpreting progress semantics.

## Required Evidence

The report must include:

- Whether a fresh user-started pressure run was available.
- If no run was available: baseline health/progress surface evidence and exact blocker.
- If a run was available: timeline of observations with task/material/MinerU/AI IDs.
- A comparison of page semantics versus `progressSnapshot` versus direct MinerU API/log evidence.
- Any semantic lag cases, including whether the lag was expected DB ingestion lag, stale log-channel behavior, or a new defect.
- Whether large files and small files behave differently.
- AI residual failures, if any, clearly separated from MinerU parse failures.
- A final classification:
  - `VALIDATED_PROGRESS_SEMANTICS_FOR_THIS_RUN`
  - `RESIDUAL_SEMANTIC_LAG_FOUND`
  - `BLOCKED_WAITING_FOR_USER_MANUAL_UPLOAD`
  - `INCONCLUSIVE_STILL_RUNNING`
  - `FAILED_SYSTEMIC_RUNTIME_OR_OBSERVABILITY_BLOCKER`

## GitHub Sync Requirements

- Before starting: `git status --short --branch`.
- Do not fetch/pull/push unless the task brief or Director explicitly requires it, or unless repository report/ledger changes need to be synchronized.
- If a report and tracking-list update are written, commit and push those repository changes to GitHub.
- Do not overwrite unrelated local changes.

## Completion Report Requirements

Write the completion report to:

`TaskAndReport/2026-05-16T08-48-28+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md` with:

- status,
- report path,
- branch/HEAD,
- next actor,
- next action,
- required output.

The report must include:

- Confirmation that work was based on this Director task brief.
- Branch and HEAD.
- Files changed.
- Commands run with exit codes.
- Checks skipped and exact reasons.
- Runtime evidence and observation timeline.
- Risks, blockers, and residual debt.
- GitHub sync status.
- Whether Director review is required.

## Acceptance Criteria

Director can accept this task only if the report clearly distinguishes:

- UI/page semantics from actual MinerU progress evidence.
- Readiness/health from progress truth.
- MinerU parse outcomes from AI metadata outcomes.
- Expected asynchronous DB lag from harmful stale/incorrect semantics.
- Terminal failure from still-progressing long-running work.

Acceptance of this task is not pressure PASS, L3, release readiness, production readiness, production上线, or go-live.
