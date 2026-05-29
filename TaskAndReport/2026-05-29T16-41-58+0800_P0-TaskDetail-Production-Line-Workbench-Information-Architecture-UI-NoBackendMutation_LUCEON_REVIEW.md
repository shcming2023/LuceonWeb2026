# Luceon Review: P0 TaskDetail Production-Line Workbench Information Architecture UI NoBackendMutation

Task ID: `TASK-20260529-145101-P0-TaskDetail-Production-Line-Workbench-Information-Architecture-UI-NoBackendMutation`

Reviewed at: `2026-05-29T16:41:58+0800`

Reviewed branch: `origin/codex/task-detail-workbench@118029373ed99f5dbabae851deda6c78eab343b4`

Baseline: `origin/main@0c778347c61ea8eccae05d4e9aad6f6bfc67741a`

Decision: `RETURNED_NARROW_PRODUCT_SEMANTICS_FIX`

## Summary

The implementation direction is substantially correct and the page now reads much more like a production-line workbench:

- Layer 1 current conclusion is visible at the top.
- Layer 2 primary inspection surface shows PDF / MinerU Markdown / Rebuilt Markdown.
- Layer 3 evidence drawer demotes technical diagnostics.
- Secondary actions are moved into `更多操作`.

However, the branch is returned for one narrow product semantics fix before acceptance.

## Checks Passed

Scope and hygiene:

```text
git merge-base origin/main origin/codex/task-detail-workbench
=> 0c778347c61ea8eccae05d4e9aad6f6bfc67741a

git diff --name-status origin/main...origin/codex/task-detail-workbench
=> A TaskAndReport/..._REPORT.md
=> M src/app/pages/TaskDetailPage.tsx

git diff --check origin/main...origin/codex/task-detail-workbench
=> passed
```

Development workspace:

```text
npx tsc --noEmit
=> passed

npm run build
=> passed
=> 1655 modules transformed
=> built in 1.06s
```

Browser verification on branch frontend at `http://127.0.0.1:5175/cms/`:

- `task-1779854322261`: current conclusion, next action, primary inspection, evidence drawer, `full.md`, `rebuilt_markdown.md`, and no readable-tree/full-markdown confusion all visible.
- `task-1779850030062`: no-`rebuilt_markdown` case truthfully shows missing rebuilt full Markdown and mentions directory tree/readable-tree evidence.

No backend/API/DB/MinIO/Docker/deploy mutation was observed in the branch.

## Blocking Finding

### B1. Current Conclusion Omits Raw Material Even Though The Task Is Past Raw-Material Evidence

On `task-1779854322261`, the current conclusion block shows:

```text
已完成：PDF / MinerU / AI Metadata / 目录重建
未完成：Clean Material 最终接受
```

But the task brief explicitly asked the first conclusion block to make the stage boundary clear:

```text
已完成：PDF / MinerU / AI Metadata / 目录重建 / Raw Material
未完成：Clean Material 最终接受
```

The existing live data has parsed evidence and toc-rebuild evidence:

- `parsedFilesCount = 99`;
- `markdownObjectName = parsed/3926938009250504/full.md`;
- `cleanMaterials.toc-rebuild.status = completed`;
- the previous pipeline view labels Raw Material output as traceable evidence.

So omitting `Raw Material` in the top conclusion makes the pipeline look like it jumps from `目录重建` directly to final `Clean Material`, which is exactly the kind of cognitive ambiguity this task was meant to remove.

Required fix:

- In `TaskDetailPage.tsx`, derive Raw Material completion from existing frontend-visible evidence, not only `material.metadata.rawMaterial`.
- Acceptable signals include existing parsed evidence such as `markdownObjectName`, `parsedPrefix`, `artifactManifestObjectName`, `zipObjectName`, or positive `parsedFilesCount`, plus any established helper already used by the pipeline view.
- For `task-1779854322261`, top conclusion must show:

```text
已完成：PDF / MinerU / AI Metadata / 目录重建 / Raw Material
未完成：Clean Material 最终接受
```

Do not add backend fields or mutate stored metadata.

## Required Resubmission

Return a revised branch that:

1. fixes Raw Material completion display in the top current-conclusion block;
2. keeps the current three-layer workbench architecture;
3. passes:
   - `git diff --check origin/main...<branch>`;
   - `npx tsc --noEmit`;
   - `npm run build`;
4. updates the execution report with the corrected visible-text evidence.

Luceon will then rerun browser verification and proceed to acceptance if no new regression appears.
