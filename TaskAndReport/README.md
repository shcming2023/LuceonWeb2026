# Luceon2026 Task And Report Registry

Last updated: 2026-05-07

`TaskAndReport/` is the mandatory handoff folder for Lucia-issued task briefs and Lucode completion reports.

## Purpose

This folder provides traceable project execution records. Lucia no longer relies on Director to relay task briefs or Lucode reports through chat. Lucode reads assigned task briefs from this folder, writes completion reports back into this folder, and Lucia reviews reports from this folder.

## Required Files

- `TASK_TRACKING_LIST.md`: ordered task ledger and status list.
- `*_TASK.md`: Lucia task brief files.
- `*_REPORT.md`: Lucode completion report files.
- `*_LUCIA_REVIEW.md`: Lucia review records when a report is accepted, rejected, or returned for correction.

## File Naming Rule

Use timestamp plus task name:

```text
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_TASK.md
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_REPORT.md
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_LUCIA_REVIEW.md
```

Task names must use ASCII-safe hyphenated words. Example:

```text
2026-05-07T06-32-38+0800_P0-MinerU-Submit-Path-Health-Probe_TASK.md
```

## Status Vocabulary

Use these status values in `TASK_TRACKING_LIST.md`:

- `下达待执行`: Lucia has issued the task; Lucode is the next actor.
- `执行中`: Lucode has started execution.
- `已回报待审`: Lucode has submitted a report; Lucia is the next actor.
- `退回待修正`: Lucia has returned the task for correction; Lucode is the next actor.
- `修正中`: Lucode has started the correction work.
- `修正回报待审`: Lucode has submitted a correction report; Lucia is the next actor.
- `完成关闭`: Lucia has accepted the report and closed the task.
- `失败关闭`: Lucia has reviewed the report and closed the task as failed.
- `取消`: Lucia or Director has canceled the task before completion.
- `挂起`: the task is intentionally paused pending dependency, decision, or evidence.

## Tracking Columns

`TASK_TRACKING_LIST.md` must include these execution-control columns:

- `Status`: current workflow state.
- `Next Actor`: `Lucia`, `Lucode`, `Director`, or `None`.
- `Next Action`: the next concrete action required.
- `Required Output`: the next required artifact, such as `*_REPORT.md` or `*_LUCIA_REVIEW.md`.

These fields are mandatory. A non-closed task must always have a non-empty `Next Actor`, `Next Action`, and `Required Output`.

## Workflow

1. Lucia writes the task brief file in this folder.
2. Lucia appends or updates the task row in `TASK_TRACKING_LIST.md` with status `下达待执行`, `Next Actor=Lucode`, and a concrete `Next Action`.
3. Lucode reads the task file from this folder before starting.
4. Lucode writes the report file in this folder using the same task name and a report timestamp.
5. Lucode updates the task row with report path, GitHub branch/HEAD, status `已回报待审` or `修正回报待审`, and `Next Actor=Lucia`.
6. Lucia reads the report file from this folder, reviews the evidence, and updates status, next actor, next action, and required output.

## Check Task Shortcut

When Director says `Lucia, check task`, Lucia must:

1. Read `TaskAndReport/TASK_TRACKING_LIST.md`.
2. Find rows with `Next Actor=Lucia`.
3. If a Lucia-owned action exists, perform the `Next Action` according to `docs/codex/roles/lucia.md`.
4. If a report review is required, write a `*_LUCIA_REVIEW.md` file and update the row.
5. If no row has `Next Actor=Lucia`, state that no new Lucia task/report is available and wait for the next instruction.

When Director says `Lucode, check task`, Lucode must:

1. Read `TaskAndReport/TASK_TRACKING_LIST.md`.
2. Find rows with `Next Actor=Lucode`.
3. If a Lucode-owned action exists, execute the `Next Action`; do not stop at reporting branch or workspace state.
4. Read the matching `*_TASK.md` and any `*_LUCIA_REVIEW.md` files before execution.
5. Write the required `*_REPORT.md` or blocked report, then update the row.
6. If no row has `Next Actor=Lucode`, state that no new Lucode task is available and wait for the next instruction.

If the next actor cannot execute the next action, that actor must write a report explaining the blocker and update the task to `挂起` with the appropriate next actor. Silence or state-only replies are not valid when a row names that role as `Next Actor`.

Do not store secrets, API tokens, raw credentials, generated build outputs, UAT screenshots, large artifacts, or machine-only files in this folder.
