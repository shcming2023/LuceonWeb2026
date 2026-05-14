# P1 Pressure Residue MinerU Continuation Read-Only Monitoring

Issued at: 2026-05-15T06:23:37+0800

Task ID: `TASK-20260515-062337-P1-Pressure-Residue-MinerU-Continuation-Read-Only-Monitoring`

Assigned role: `TestAcceptanceEngineer`

Expected report: `TaskAndReport/2026-05-15T06-23-37+0800_P1-Pressure-Residue-MinerU-Continuation-Read-Only-Monitoring_REPORT.md`

## Context

Task 153 proved the pressure residue task was still running but had advanced in raw MinerU logs. Director accepted that report but spot-checks still show the task has not reached terminal state.

Target:

- Parse task: `task-1778765417422`
- Material: `2274129919986463`
- File: `06第六章 长期股权投资与合营安排.pdf`
- MinerU task: `dcdb27f3-fac6-4ede-b456-a96fe358b0da`

Current concern:

- Direct MinerU still reports `processing`.
- Luceon still reports `running/mineru-processing`.
- Luceon metadata has recorded `localTimeoutOccurred=true`.
- Active-task summary/log observation may be stale compared with raw MinerU logs.

## Objective

Perform one more bounded read-only monitoring window and report whether the task:

- reached terminal success;
- reached terminal failure;
- is still processing with fresh raw-log or direct-status evidence of advancement;
- is still processing with no new raw-log progress after the prior observed progress point and should be classified as possible stall;
- cannot be observed reliably and must be escalated as blocked.

## Required Reading

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/test-acceptance-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- Task 153 task/report/Director review
- this task brief

## Allowed Actions

Read-only only:

- inspect production UI pages if useful;
- inspect upload read-only health/ops endpoints;
- inspect DB read-only task/material/AI job state;
- inspect direct MinerU task status and health;
- tail raw MinerU logs;
- compare snapshot timestamps and log mtimes.

Take at least two snapshots unless the task has already reached terminal state on the first snapshot. A 20-30 minute interval is sufficient.

## Forbidden Actions

Do not:

- upload any file;
- cancel, stop, cleanup, repair, retry, reparse, or re-AI any task;
- mutate DB, MinIO, Docker volumes, samples, settings, secrets, models, or local config;
- run Docker down/restart/rebuild or service ownership changes;
- declare pressure PASS, L3 PASS, release-readiness, production-readiness, or go-live.

## Required Report

Report:

- exact snapshot times;
- direct MinerU task status;
- Luceon task/material/AI job state;
- whether `localTimeoutOccurred` is present;
- raw MinerU log last-progress evidence and mtime;
- active-task/sidecar summary and whether it diverges from raw logs;
- clear outcome classification;
- commands/endpoints used with status/exit codes;
- skipped checks and reasons;
- explicit no-mutation statement.

Then update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查`
- Next Actor: `Director`
- Report / Review: link to your report

