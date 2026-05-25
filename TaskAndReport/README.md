# Luceon2026 Task And Report Registry

Last updated: 2026-05-25

`TaskAndReport/` is the active GitHub-mediated control plane and permanent
historical evidence registry for Luceon2026.

Historical task briefs, reports, reviews, decisions, and ledger rows must remain
queryable. Do not delete or rewrite them merely because the role model changed.

## Active Roles After 2026-05-25

- `Luceon`: unified project owner for planning, requirements, architecture,
  product, code implementation, tests, acceptance, control-plane closure, and
  scoped production validation/deployment coordination.
- `User`: owner decisions, scope choices, destructive-operation approvals,
  external/cloud access assistance, and release/go-live judgment.
- `None`: no next action.

`Lucode` is retired as an active project role. Existing Lucode rows, reports,
reviews, and branches remain historical evidence only. New tasks must not use
`Next Actor=Lucode`.

## Workspace Boundary

- Development workspace: `/Users/concm/Dev_workspace/Luceon2026`
- Production/control/deployment workspace: `/Users/concm/prod_workspace/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`

Implementation and developer checks should happen in the development workspace,
usually on a scoped `codex/<task-id-or-short-slug>` branch.

The production/control workspace is for current truth, task/report/decision
files, acceptance evidence, mainline closure, and explicitly authorized runtime
or deployment operations.

## Required Files

- `TASK_TRACKING_LIST.md`: ordered task ledger and status list.
- `*_TASK.md`: task briefs or scoped work instructions.
- `*_REPORT.md`: implementation, validation, diagnosis, or blocked reports.
- `*_LUCEON_REVIEW.md`: review records when a separate review artifact is useful.
- `*_DIRECTOR_REVIEW.md` and `*_LUCIA_REVIEW.md`: historical review records.
- `*_DECISION.md`: user decision request, final decision, milestone decision, or
  workflow decision records.

## File Naming Rule

Use timestamp plus task name:

```text
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_TASK.md
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_REPORT.md
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_LUCEON_REVIEW.md
YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_DECISION.md
```

Task names should use ASCII-safe hyphenated words.

## Status Vocabulary

Use these values for new active rows:

- `下达待 Luceon 执行`: task is assigned to Luceon for implementation,
  validation, planning, or control-plane work.
- `Luceon 规划中`: Luceon owns the next planning, requirement, architecture, or
  decision step.
- `Luceon 执行中`: Luceon is implementing, testing, diagnosing, or producing the
  required artifact.
- `Luceon 验收中`: Luceon is reviewing, validating, deploying under explicit
  authorization, or preparing acceptance evidence.
- `挂起待 User`: user judgment or explicit authorization is required.
- `完成关闭`: accepted and closed.
- `失败关闭`: reviewed and closed as failed.
- `取消`: canceled before completion.
- `挂起`: intentionally paused.

Legacy statuses remain valid history, including Lucode-era statuses.

## Active Row Definition For `check task`

For `check task`, an "open row" means both:

- `Next Actor` is `Luceon` or `User`; and
- `Status` is one of the current active statuses that require that actor to act.

Active Luceon statuses:

- `下达待 Luceon 执行`
- `Luceon 规划中`
- `Luceon 执行中`
- `Luceon 验收中`

Active User status:

- `挂起待 User`

`Next Actor` alone is not enough to make a row executable. Legacy returned,
withdrawn, failed, canceled, paused, closed, or Lucode-owned rows such as
`Lucode 已回报待 Luceon 审查`, `下达待 Lucode 执行`, `退回待 Lucode 修正`,
`未接受已退回`, `已撤回合并`, `失败关闭`, `取消`, `挂起`, and `完成关闭` are
historical/non-executable for new `check task` cycles unless a later decision or
task row explicitly reactivates them under Luceon ownership.

## Tracking Columns

`TASK_TRACKING_LIST.md` must keep these control columns:

- `Status`
- `Next Actor`
- `Next Action`
- `Required Output`
- `Task Brief`
- `Report / Review`
- `Branch / HEAD`
- `Notes`

For new active rows, `Next Actor` must be one of `Luceon`, `User`, or `None`.

## Branch And Report Contract

For implementation work, Luceon normally works from:

```text
/Users/concm/Dev_workspace/Luceon2026
```

Default branch pattern:

```text
codex/<task-id-or-short-slug>
```

Implementation reports should include:

- task id and task brief path;
- branch and HEAD when a branch is used;
- files changed;
- implementation/product summary;
- commands run with exit codes;
- skipped checks and exact reasons;
- evidence;
- risks, blockers, and residual debt;
- production/runtime/data operations performed or explicitly not performed.

For changed-file evidence, prefer merge-base / three-dot diffs such as
`git diff --name-status origin/main...HEAD` and
`git diff --check origin/main...HEAD` when working on an implementation branch.

Low-risk docs-only or control-plane-only updates may be committed directly from
the production/control workspace when that is simpler and no business code is
changed.

## Luceon `check task`

When the user says `check task`, Luceon must:

1. synchronize the production/control workspace with GitHub:

   ```bash
   git status --short --branch
   git fetch origin --prune --tags
   git pull --ff-only origin main
   ```

2. read only `TaskAndReport/TASK_TRACKING_LIST.md` first;
3. find the earliest active row with `Next Actor=Luceon`;
4. if no Luceon row exists but a `Next Actor=User` row exists, mention the
   decision id and the decision needed, then stop unless the user asks to
   continue;
5. if no active Luceon/User row exists, reply:

   ```text
   当前无 Luceon 待处理任务
   ```

6. do not run Lucode branch-handoff checks for new work;
7. after finding a Luceon row, read the related task brief, report, evidence,
   changed files, and task-relevant docs;
8. perform the listed `Next Action`, switching to the development workspace for
   code implementation;
9. write a `*_REPORT.md`, `*_LUCEON_REVIEW.md`, or `*_DECISION.md` when the
   action requires durable evidence;
10. update the task ledger;
11. commit and push changes to GitHub.

No-task wakeups must not read the whole repo, run validation, write reports,
update docs, or push.

## Context Hygiene

To keep future runs efficient:

- task briefs should be standalone and include only the context needed for the
  assigned work;
- reports should summarize evidence and link detailed artifacts instead of
  pasting excessive raw logs;
- `PROJECT_STATE.md` and `HANDOFF.md` should stay short and point to detailed
  TaskAndReport evidence;
- stale active instructions should be archived, retired, or replaced, not left
  beside newer rules as active workflow;
- broad documentation cleanup should be done only when it directly improves
  current comprehension or task routing.

## Safety

Do not store secrets, API tokens, raw credentials, generated build outputs, UAT
screenshots, large artifacts, or machine-only files in this folder.

Destructive DB, MinIO, Docker volume, production data, model, secret,
sample-file, production deployment, cloud-server, or external-service operations
require explicit user approval recorded in a task or decision file.
