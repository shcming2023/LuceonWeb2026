# P0 Luceon Lucode Local Dual Thread And Subagent Assistance Decision

- Timestamp: 2026-05-24T10:19:08+0800
- Decision owner: User
- Recorded by: Luceon

## Decision

Luceon2026 keeps the active `Luceon` / `Lucode` two-role collaboration model, but moves Lucode back onto the user's local project machine as a separate local thread/worktree.

## Active Workspaces

| Role | Active workspace | Private role settings |
| --- | --- | --- |
| `Luceon` | `/Users/concm/prod_workspace/Luceon2026` | Local `AGENTS.md` / `.agents/**`, ignored by Git |
| `Lucode` | `/Users/concm/Dev_workspace/Luceon2026` | Local `AGENTS.md` / `.agents/**`, ignored by Git |

The former external IDE workspace `/Users/caoming/Documents/Luceon2026` is no longer the active Lucode workspace.

## Trigger Model

Initial operating mode remains manual:

1. Luceon writes or updates a task brief and task-ledger row.
2. The user manually sends `Lucode, check task` in the Lucode thread.
3. Lucode syncs GitHub, reads `TaskAndReport/TASK_TRACKING_LIST.md`, executes the earliest open `Next Actor=Lucode` row, writes a report, updates the ledger to `Next Actor=Luceon`, and pushes its branch.
4. The user or Luceon then triggers Luceon review.

A Lucode heartbeat automation may be added later only after the manual flow is stable.

## Subagent Boundary

Luceon may explicitly use Codex subagents for bounded exploration, tests, log analysis, evidence extraction, and review assistance when the user authorizes subagent or parallel-agent work for the current task.

Subagents are Luceon-internal assistants, not project roles. They do not own task-ledger rows, acceptance decisions, readiness wording, production authorization, or final project facts. Luceon remains responsible for summarizing, verifying, and deciding.

## Safety Boundary

This decision does not authorize production mutation, deployment, upload, pressure test, submit-probe, DB/MinIO/Docker volume cleanup, model operation, secret/config mutation, sample-file mutation, automated Lucode heartbeat creation, or readiness/go-live claim.
