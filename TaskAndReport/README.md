# Luceon2026 Task And Report Registry

Last updated: 2026-05-16

`TaskAndReport/` is the active GitHub-mediated control plane for post-6.9.1 Luceon/Lucode collaboration and the permanent historical evidence registry for earlier work.

Historical task briefs, reports, reviews, decisions, and ledger rows must remain queryable. Do not delete or rewrite them merely because the role model changed.

## Active Roles After 6.9.1

- `Luceon`: Codex-side project director, architecture reviewer, test/acceptance engineer, production validation/deployment coordinator, and task-ledger owner.
- `Lucode`: external IDE-side product/implementation role. Lucode's full local role instructions are user-managed outside this repository, but the GitHub interface contract below is authoritative for shared project coordination.
- `User`: owner decisions, scope choices, destructive-operation approvals, and release/go-live judgment.
- `None`: no next action.

Retired roles such as ProductManager, Architect, DevelopmentEngineer, TestAcceptanceEngineer, Lucia, and legacy Lucode rows remain historical only.

## Required Files

- `TASK_TRACKING_LIST.md`: ordered task ledger and status list.
- `*_TASK.md`: Luceon-authored task briefs.
- `*_REPORT.md`: Lucode implementation reports, Luceon validation reports, or blocked reports.
- `*_LUCEON_REVIEW.md`: Luceon review records for new work.
- `*_DIRECTOR_REVIEW.md` and `*_LUCIA_REVIEW.md`: historical review records.
- `*_DECISION.md`: user decision request, final decision, milestone decision, or workflow decision records.

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

- `下达待 Lucode 执行`: Luceon has issued a task to external Lucode.
- `Lucode 执行中`: Lucode has started implementation or product work.
- `Lucode 已回报待 Luceon 审查`: Lucode has pushed a branch/report and Luceon must review it.
- `Luceon 规划中`: Luceon owns the next planning, task-brief, architecture, or decision step.
- `Luceon 验收中`: Luceon is reviewing, testing, validating, deploying, or preparing acceptance evidence.
- `退回待 Lucode 修正`: Luceon returned the task for scoped correction.
- `挂起待 User`: user judgment is required.
- `完成关闭`: accepted and closed.
- `失败关闭`: reviewed and closed as failed.
- `取消`: canceled before completion.
- `挂起`: intentionally paused.

Legacy statuses remain valid history.

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

For new active rows, `Next Actor` must be one of `Luceon`, `Lucode`, `User`, or `None`.

## GitHub Branch And Report Contract

Lucode normally works on a scoped branch, for example:

```text
lucode/<task-id-or-short-slug>
```

Lucode completion reports should include:

- task id and task brief path;
- branch and HEAD;
- files changed;
- implementation/product summary;
- commands run with exit codes;
- skipped checks and exact reasons;
- evidence;
- risks, blockers, and residual debt;
- whether Luceon review/production validation is required.

Lucode should not mutate production data, run production deployment, or merge to `main` unless a task brief explicitly authorizes that. Luceon is responsible for acceptance review and final merge/ledger closure unless the user gives different instructions.

## Luceon `check task`

When the user says `check task` in the Luceon thread, Luceon must:

1. synchronize with GitHub (`git fetch origin --prune --tags`, then fast-forward `main` when safe);
2. read `TaskAndReport/TASK_TRACKING_LIST.md`;
3. find the earliest open row with `Next Actor=Luceon`;
4. read the related task brief, Lucode report, branch, and evidence;
5. perform the listed `Next Action`;
6. write a `*_LUCEON_REVIEW.md`, `*_REPORT.md`, or `*_DECISION.md` when the action requires durable evidence;
7. update the task ledger;
8. commit and push changes to GitHub.

If there is no open `Next Actor=Luceon` row, Luceon should report that clearly. If there are `Next Actor=User` rows, Luceon should summarize the decision needed and recommend a path.

## Safety

Do not store secrets, API tokens, raw credentials, generated build outputs, UAT screenshots, large artifacts, or machine-only files in this folder.

Destructive DB, MinIO, Docker volume, production data, model, secret, or sample-file operations require explicit user approval recorded in a task or decision file.
