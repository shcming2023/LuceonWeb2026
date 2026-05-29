# Luceon Review: P0 Task And Library Pipeline-Centric Simplification UI NoBackendMutation

Task ID: `TASK-20260529-132613-P0-Task-And-Library-Pipeline-Centric-Simplification-UI-NoBackendMutation`

Reviewed at: `2026-05-29T14:03:29+0800`

Reviewed branch: `origin/codex/clean-material-empty-cta@8ccbb32`

Baseline: `origin/main@9f7c7a1`

Decision: `RETURNED_BLOCKED_CONTROL_PLANE_AND_DIFFCHECK`

## Summary

The implementation direction is broadly aligned with the requested pipeline-centric UI simplification, but the branch cannot be accepted, merged, deployed, or manually validated yet.

The blocking issues are control-plane integrity and required validation failure:

1. The branch is not based on current `origin/main` and would remove the task brief / task-list row that define this task.
2. `git diff --check` fails on the reviewed branch.
3. The execution report does not include the full required validation set from the task brief.

No deployment or runtime browser acceptance was performed.

## Blocking Findings

### B1. Branch Would Delete The Current Task Control Plane

Evidence:

```text
git diff --name-status origin/main..origin/codex/clean-material-empty-cta

A TaskAndReport/2026-05-29T13-26-13+0800_P0-Task-And-Library-Pipeline-Centric-Simplification-UI-NoBackendMutation_REPORT.md
D TaskAndReport/2026-05-29T13-26-13+0800_P0-Task-And-Library-Pipeline-Centric-Simplification-UI-NoBackendMutation_TASK.md
M TaskAndReport/TASK_TRACKING_LIST.md
M src/app/pages/ProductsPage.tsx
M src/app/pages/TaskDetailPage.tsx
M src/app/pages/TaskManagementPage.tsx
```

Additional evidence:

```text
git show origin/codex/clean-material-empty-cta:TaskAndReport/TASK_TRACKING_LIST.md | rg -n "TASK-20260529|Last updated"

3:Last updated: 2026-05-26
```

The reviewed branch does not contain task row #305 and does not contain the task brief file from `origin/main@9f7c7a1`. A merge from this state would damage the project control plane.

Required fix:

- Rebase or recreate the implementation branch from current `origin/main`.
- Preserve:
  - `TaskAndReport/TASK_TRACKING_LIST.md` row #305;
  - `TaskAndReport/2026-05-29T13-26-13+0800_P0-Task-And-Library-Pipeline-Centric-Simplification-UI-NoBackendMutation_TASK.md`.
- Add only the execution report and implementation changes on top.

### B2. Required Diff Check Fails

Evidence:

```text
git diff --check origin/main...origin/codex/clean-material-empty-cta

src/app/pages/TaskDetailPage.tsx:1448: trailing whitespace.
+              
```

The task brief explicitly requires `git diff --check`.

Required fix:

- Remove the trailing whitespace.
- Rerun `git diff --check origin/main...<branch>` after rebasing.

### B3. Required Validation Evidence Is Incomplete

The task brief requires:

- `npx tsc --noEmit`;
- `npm run build`;
- `git diff --check`;
- browser/manual verification for `/cms/tasks`, one `/cms/tasks/:id`, `/cms/library`, and one `/cms/asset/:id`;
- evidence that full rebuilt Markdown is used when available;
- evidence that `readable_tree.md` is not misrepresented as full rebuilt Markdown.

The submitted report records only Vite build success and a general statement that UI is aligned with `mainlinePipeline.ts`. It does not provide:

- `npx tsc --noEmit` result;
- `git diff --check` result;
- route-level browser/manual verification;
- explicit readable_tree vs rebuilt_markdown evidence.

Required fix:

- Update the execution report with the full validation set after the branch is rebased and `diff --check` passes.

## Product Review Notes

Positive direction:

- `TaskDetailPage.tsx` introduces a pipeline-first entry using `MainlinePipelinePanel`.
- Markdown comparison now targets `rebuilt_markdown` rather than `readable_tree`.
- `ProductsPage.tsx` reduces visible filter clutter and introduces output-packet tags.
- `TaskManagementPage.tsx` surfaces simple PDF / MD / AI Meta / Clean Mat packet tags.

Residual review risk after the blockers are fixed:

- The UI still needs live browser verification against real task/material examples, especially tasks with toc-rebuild artifacts.
- The library still exposes destructive test-environment cleanup affordances prominently; this may be pre-existing, but it should be checked during product QA for whether it conflicts with the simplified operator surface.

## Required Resubmission

Return a revised branch that:

1. is based on current `origin/main`;
2. preserves the #305 task brief and task tracking row;
3. passes `git diff --check`;
4. includes `npx tsc --noEmit`, `npm run build`, and browser/manual route evidence in the report;
5. keeps the no-backend/no-mutation boundary.

Luceon will not deploy or accept this branch until those blockers are cleared.
