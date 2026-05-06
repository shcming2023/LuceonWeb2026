# Luceon2026 Task And Report Registry

Last updated: 2026-05-07

`TaskAndReport/` is the mandatory handoff folder for Lucia-issued task briefs and Lucode completion reports.

## Purpose

This folder provides traceable project execution records. Lucia no longer relies on Director to relay task briefs or Lucode reports through chat. Lucode reads assigned task briefs from this folder, writes completion reports back into this folder, and Lucia reviews reports from this folder.

## Required Files

- `TASK_TRACKING_LIST.md`: ordered task ledger and status list.
- `*_TASK.md`: Lucia task brief files.
- `*_REPORT.md`: Lucode completion report files.

## File Naming Rule

Use timestamp plus task name:

```text
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_TASK.md
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_REPORT.md
```

Task names must use ASCII-safe hyphenated words. Example:

```text
2026-05-07T06-32-38+0800_P0-MinerU-Submit-Path-Health-Probe_TASK.md
```

## Status Vocabulary

Use these status values in `TASK_TRACKING_LIST.md`:

- `下达`: Lucia has issued the task and Lucode may execute it.
- `完成关闭`: Lucia has accepted the report and closed the task.
- `失败关闭`: Lucia has reviewed the report and closed the task as failed.
- `取消`: Lucia or Director has canceled the task before completion.
- `挂起`: the task is intentionally paused pending dependency, decision, or evidence.
- `退回修正`: Lucia has reviewed the report and returned the task for correction.

## Workflow

1. Lucia writes the task brief file in this folder.
2. Lucia appends or updates the task row in `TASK_TRACKING_LIST.md` with status `下达`.
3. Lucode reads the task file from this folder before starting.
4. Lucode writes the report file in this folder using the same task name and a report timestamp.
5. Lucode updates the task row with report path and GitHub branch/HEAD when available.
6. Lucia reads the report file from this folder, reviews the evidence, and updates status.

Do not store secrets, API tokens, raw credentials, generated build outputs, UAT screenshots, large artifacts, or machine-only files in this folder.
