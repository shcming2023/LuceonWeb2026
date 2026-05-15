# Luceon2026 Task And Report Registry

Last updated: 2026-05-15

`TaskAndReport/` is the mandatory handoff folder for Director-issued task briefs, role completion reports, Director reviews, and user decision records.

## Purpose

This folder provides traceable project execution records. Director no longer relies on chat relay alone. ProductManager, Architect, DevelopmentEngineer, and TestAcceptanceEngineer read assigned task briefs from this folder, write completion reports back into this folder, and Director reviews reports from this folder.

## Required Files

- `TASK_TRACKING_LIST.md`: ordered task ledger and status list.
- `*_TASK.md`: Director task brief files.
- `*_REPORT.md`: role completion report files.
- `*_DIRECTOR_REVIEW.md`: Director review records when a report is accepted, rejected, returned, blocked, or escalated.
- `*_DECISION.md`: Director-authored user decision request or decision record files when owner judgment is required before the next task.

Historical `*_LUCIA_REVIEW.md` files remain valid history but are not the active review format after 2026-05-13.

## File Naming Rule

Use timestamp plus task name:

```text
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_TASK.md
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_REPORT.md
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_DIRECTOR_REVIEW.md
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_DECISION.md
```

Task names must use ASCII-safe hyphenated words. Example:

```text
2026-05-13T09-30-00+0800_P0-Release-Readiness-Scope-Decision_TASK.md
```

## Status Vocabulary

Use these status values in `TASK_TRACKING_LIST.md`:

- `下达待执行`: Director has issued the task; a role is the next actor.
- `执行中`: the assigned role has started execution.
- `已回报待 Director 审查`: the assigned role has submitted a report; Director is the next actor.
- `退回待修正`: Director has returned the task for correction; a role is the next actor.
- `修正中`: the assigned role has started correction work.
- `修正回报待 Director 审查`: the assigned role has submitted a correction report; Director is the next actor.
- `完成关闭`: Director has accepted the report and closed the task.
- `失败关闭`: Director has reviewed the report and closed the task as failed.
- `取消`: Director or the user has canceled the task before completion.
- `挂起`: the task is intentionally paused pending dependency, user decision, or evidence.

Historical rows may contain legacy statuses such as `已完成待 Lucia 审查`. New active rows should use the status values above.

## Tracking Columns

`TASK_TRACKING_LIST.md` must include these execution-control columns:

- `Status`: current workflow state.
- `Next Actor`: one of `Director`, `ProductManager`, `Architect`, `DevelopmentEngineer`, `TestAcceptanceEngineer`, `User`, or `None`.
- `Next Action`: the next concrete action required.
- `Required Output`: the next required artifact, such as `*_REPORT.md`, `*_DIRECTOR_REVIEW.md`, or `*_DECISION.md`.

These fields are mandatory. A non-closed task must always have a non-empty `Next Actor`, `Next Action`, and `Required Output`.

The ledger must not have all current rows closed with no active next actor unless the user has explicitly closed the iteration stream and the closure is recorded in the latest row notes.

When `Next Actor=User`, the row must represent a specific decision point, not a general wait. The `Next Action` must state the exact decision needed, and `Required Output` must state the expected user decision and how Director should record it. The `Notes` field must record the decision-request timestamp, decision boundary, options considered, and follow-up expectations.

## Workflow

1. Director writes the task brief file in this folder.
2. Director appends or updates the task row in `TASK_TRACKING_LIST.md` with status `下达待执行`, the assigned role as `Next Actor`, and a concrete `Next Action`.
3. The assigned role reads the task file from this folder before starting.
4. The assigned role writes the report file in this folder using the same task name and a report timestamp.
5. The assigned role updates the task row with report path, GitHub branch/HEAD when applicable, status `已回报待 Director 审查` or `修正回报待 Director 审查`, and `Next Actor=Director`.
6. Director reads the report file from this folder, reviews the evidence, writes a `*_DIRECTOR_REVIEW.md` when a formal judgment is made, and updates status, next actor, next action, and required output.
7. Director either closes the task, returns it for correction, blocks it pending evidence or user decision, or issues the next task brief.

## User Decision Rows

If a task cannot continue without user judgment, Director must update or create a task row with:

- `Status=挂起`
- `Next Actor=User`
- `Next Action=<specific decision question>`
- `Required Output=<user decision recorded by Director>`

Director must not rely on chat memory alone for user decision waits. When the user decides, Director records the decision in the task row and, when useful, in a `*_DECISION.md` file before issuing follow-up tasks.

## No-Idle Ledger Rule

At least one row must represent the current project next step until the user explicitly closes the iteration stream.

If all previous tasks are closed, Director must do one of the following:

- Add a new `*_TASK.md` and tracking row for ProductManager, Architect, DevelopmentEngineer, or TestAcceptanceEngineer when the next work can proceed safely within current PRD and project boundaries.
- Add a `*_DECISION.md` and tracking row with `Next Actor=User` when the next work requires owner judgment.
- Record the user-approved iteration closure in the latest row notes.

The valid steady states are therefore: a role executing, Director reviewing or drafting, User deciding, or user-approved closure. A silent no-task state is not valid.

## Check Task Shortcut

When the user says `Director, check task`, Director must:

1. Read `TaskAndReport/TASK_TRACKING_LIST.md`.
2. Find rows with `Next Actor=Director`.
3. If a Director-owned action exists, perform the `Next Action` according to `docs/codex/roles/director.md`.
4. If a report review is required, write a `*_DIRECTOR_REVIEW.md` file and update the row.
5. Inspect rows with `Next Actor=User` for recorded decision waits.
6. If no row has `Next Actor=Director` and no user decision is pending, create the next scoped task, record a user decision row, or report a user-approved closure.

When the user says `产品经理, check task` or `ProductManager, check task`, ProductManager must:

1. Read `TaskAndReport/TASK_TRACKING_LIST.md`.
2. Find rows with `Next Actor=ProductManager`.
3. Read the matching `*_TASK.md` before execution.
4. Execute the `Next Action` or write a blocked report.
5. Write the required `*_REPORT.md` and update the row.

When the user says `架构师, check task` or `Architect, check task`, Architect must follow the same process for rows with `Next Actor=Architect`.

When the user says `开发工程师, check task` or `DevelopmentEngineer, check task`, DevelopmentEngineer must follow the same process for rows with `Next Actor=DevelopmentEngineer`.

When the user says `测试验收工程师, check task` or `TestAcceptanceEngineer, check task`, TestAcceptanceEngineer must follow the same process for rows with `Next Actor=TestAcceptanceEngineer`.

If the next actor cannot execute the next action, that actor must write a report explaining the blocker and update the task to `挂起` with the appropriate next actor. Silence or state-only replies are not valid when a row names that role as `Next Actor`.

Do not store secrets, API tokens, raw credentials, generated build outputs, UAT screenshots, large artifacts, or machine-only files in this folder.
