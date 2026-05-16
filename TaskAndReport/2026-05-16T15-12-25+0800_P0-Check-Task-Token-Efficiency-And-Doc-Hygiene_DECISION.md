# P0 Check Task Token Efficiency And Documentation Hygiene Decision

- Timestamp: 2026-05-16T15:12:25+0800
- Decision owner: User
- Recorded by: Luceon

## Decision

`check task` should be a lightweight wakeup, not a full-context reread.

On every `check task`, Luceon should first synchronize GitHub and read only `TaskAndReport/TASK_TRACKING_LIST.md`. If there is no open `Next Actor=Luceon` row, Luceon should briefly report that there is no pending task and then sleep until the next user instruction, heartbeat, or GitHub-visible task update.

Only when a matching task exists should Luceon read the referenced task brief, report, branch, evidence, and task-relevant docs.

## Documentation Hygiene

Luceon should keep active project docs concise and organized:

- summarize durable truth in active docs;
- keep detailed evidence in `TaskAndReport/`;
- archive stale workflow instructions;
- avoid broad doc rewrites when a small targeted update is enough;
- update `PROJECT_STATE.md` and `HANDOFF.md` only when project truth or workflow state changes.

## Boundary

This decision changes workflow discipline only. It does not authorize production mutation, deployment, validation upload, pressure test, submit-probe, DB/MinIO/Docker volume operation, model change, secret/config change, or readiness/go-live claim.
