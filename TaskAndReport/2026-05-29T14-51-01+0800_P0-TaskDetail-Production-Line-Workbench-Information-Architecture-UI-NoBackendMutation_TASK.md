# P0 TaskDetail Production-Line Workbench Information Architecture UI NoBackendMutation

Task ID: `TASK-20260529-145101-P0-TaskDetail-Production-Line-Workbench-Information-Architecture-UI-NoBackendMutation`

Issued at: `2026-05-29T14:51:01+0800`

Issued by: Luceon

Assigned execution owner: External development department

Baseline: `main@9780ac7841caf1d4b896d5be618cf5874e692dc7`

Reference page for product review:

```text
http://152.136.183.144:28081/cms/tasks/task-1779854322261
```

## Mainline Objective

Redesign the task detail page information architecture so it reads as a production-line workbench, not an engineering audit dump.

The target operator mental model is:

```text
current conclusion -> primary document comparison -> evidence drawer
```

Do not add more pipeline features. Reorder, simplify, and clarify the existing task-detail experience so an operator can immediately understand:

1. what this PDF is;
2. where it is in the pipeline;
3. what outputs are trustworthy enough to inspect now;
4. what the next human action is.

## Product Diagnosis

The current page already exposes the right materials, but its narrative is weak:

- buttons, pipeline, packets, Clean Material card, artifact refs, operator preview, and diagnostics all compete for attention;
- `NEXT OPERATOR ACTION` is correct but not visually dominant enough;
- the Markdown comparison is the most important inspection surface, but it is buried inside the Clean Material section;
- readable tree / JSON / provenance artifacts are useful evidence, but they should not compete with document comparison;
- the page feels like an audit sheet rather than a task workbench.

## Required Design Direction

Restructure the default task detail overview into three clear layers.

### Layer 1: Current Conclusion

At the top of the page, show a concise task conclusion block:

```text
当前：待人工复核
已完成：PDF / MinerU / AI Metadata / 目录重建 / Raw Material
未完成：Clean Material 最终接受
下一步：检查 Markdown 对比 + 确认元数据
```

This must be the first thing an operator sees after the title/action bar.

Required behavior:

- keep the current task state and stage visible;
- make the single recommended next action visually primary;
- demote retry/reparse/re-AI/destructive or rollback-like actions into secondary menus or lower-emphasis controls;
- do not hide necessary existing actions, but stop presenting all actions as equal.

### Layer 2: Primary Inspection Surface

Make document comparison the central work area.

For a task with both original MinerU Markdown and `rebuilt_markdown.md`, default overview should prominently show or directly link to:

```text
PDF 原件 | MinerU Markdown full.md | Rebuilt Markdown rebuilt_markdown.md
```

The operator should be able to inspect the PDF and compare the two Markdown versions without first understanding artifact refs.

Rules:

- `MinerU Markdown` means `full.md`;
- `Rebuilt Markdown` means `rebuilt_markdown.md`;
- `readable_tree.md` must not be presented as full rebuilt Markdown;
- if `rebuilt_markdown.md` is missing, show a truthful empty state such as `暂无完整重建 Markdown，仅有目录树产物` instead of fabricating a comparison pane.

### Layer 3: Evidence Drawer

Move detailed technical artifacts below or behind explicit disclosure:

- `readable_tree.md`;
- `logic_tree.json`;
- `skeleton.json`;
- `provenance.json`;
- object refs;
- SHA / size / job id;
- event logs;
- optionsSnapshot;
- technical diagnostics;
- mock-safe operator decision preview.

These must remain accessible, but they should feel like evidence after the main inspection path, not the page's main content.

## Scope

Allowed scope:

- frontend-only UI/interaction changes;
- primarily `src/app/pages/TaskDetailPage.tsx`;
- related task-detail components if needed:
  - `src/app/components/CleanMaterialSummaryCard.tsx`;
  - `src/app/components/CleanMaterialArtifactInspector.tsx`;
  - `src/app/components/PreviewTabPanel.tsx`;
  - `src/app/components/MainlinePipelinePanel.tsx`;
  - new frontend-only components under `src/app/components/`.

Avoid changing `ProductsPage.tsx` and `TaskManagementPage.tsx` unless a tiny shared helper extraction is truly necessary.

## Explicit Non-Goals

Do not:

- build a new approval system;
- add backend APIs;
- change DB schema or persisted metadata shape;
- run uploads, parsing jobs, submit-probe, CleanService POST, or RawMaterial2CleanMaterial execution;
- write, delete, move, copy, or clean MinIO objects;
- change Docker, deployment, SSH tunnel, server config, or ports;
- make readiness, UAT, pressure PASS, production readiness, release readiness, or go-live claims.

## Acceptance Criteria

Luceon will review against the public deployed example and at least one local task detail route.

Required outcomes:

1. On `task-1779854322261`, the first screen makes the current conclusion and next action obvious.
2. Retry/reparse/re-AI style actions no longer visually compete with the recommended next operator action.
3. The primary inspection surface makes PDF / MinerU Markdown / Rebuilt Markdown easy to find.
4. The page truthfully distinguishes:
   - `full.md`;
   - `rebuilt_markdown.md`;
   - `readable_tree.md`;
   - JSON/provenance evidence.
5. Technical evidence remains available but is visually secondary.
6. The no-`rebuilt_markdown` case remains truthful and does not fabricate rebuilt full Markdown.
7. Existing tabs/routes do not regress:
   - `/cms/tasks/:id`;
   - Markdown tab;
   - original PDF preview;
   - metadata tab;
   - events tab.

## Required Validation

The execution report must include:

- `git diff --check origin/main...<branch>`;
- `npx tsc --noEmit`;
- `npm run build`;
- browser/manual verification for:
  - `http://152.136.183.144:28081/cms/tasks/task-1779854322261` or equivalent local deployed route after Luceon deploys;
  - one task that has `rebuilt_markdown.md`;
  - one task that lacks `rebuilt_markdown.md`, if available;
- visible-text evidence for the conclusion block;
- visible-text evidence for the Markdown comparison labels;
- visible-text evidence that `readable_tree.md` is evidence/tree, not full rebuilt Markdown.

## Required Report

Return a report under `TaskAndReport/` containing:

- changed files;
- implementation summary;
- before/after information architecture explanation;
- validation command results;
- browser/manual route evidence;
- explicit no-backend/no-mutation statement;
- residual risks or follow-up suggestions.

## Stop Rule

Stop and report instead of expanding scope if:

- existing frontend data cannot distinguish `rebuilt_markdown.md` from `readable_tree.md`;
- the desired layout requires backend API changes;
- the task starts drifting into broad dashboard redesign or approval workflow implementation.

Luceon will review, merge if acceptable, and perform deployment/restart/testing only after acceptance.
