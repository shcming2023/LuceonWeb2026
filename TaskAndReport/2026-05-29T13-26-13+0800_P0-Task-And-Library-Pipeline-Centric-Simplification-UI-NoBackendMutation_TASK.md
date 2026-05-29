# P0 Task And Library Pipeline-Centric Simplification UI NoBackendMutation

Task ID: `TASK-20260529-132613-P0-Task-And-Library-Pipeline-Centric-Simplification-UI-NoBackendMutation`

Issued at: `2026-05-29T13:26:13+0800`

Issued by: Luceon

Assigned execution owner: External development department

Baseline: `main@ab4630cc998aedca4c589dc86db679a42e679d01`

## Mainline Objective

Simplify the user-facing task and library experience around the real product pipeline:

```text
PDF -> MinerU parse -> AI metadata -> toc-rebuild -> Raw Material -> Clean Material
```

The product goal is not to add another dashboard. The goal is to make the current processing state, primary outputs, next action, and evidence trail obvious to an operator who is manually evaluating the full flow.

## Product Principle

Every important page should answer four questions without making the user inspect raw diagnostic internals first:

1. What input asset is this?
2. Which pipeline stage is it currently in?
3. What durable outputs already exist for each completed stage?
4. What is the next valid operator action?

Raw object refs, hashes, event logs, and large diagnostic matrices remain available, but they must be secondary technical evidence, collapsed or visually demoted by default.

## Critical Path Scope

Implement a UI/interaction-only simplification for:

- task list: `/cms/tasks`;
- task detail: `/cms/tasks/:id`;
- results library: `/cms/library`;
- asset detail only where needed for consistency: `/cms/asset/:id`.

The core concept should be an **asset processing packet**:

- PDF original;
- MinerU parsed outputs;
- AI metadata;
- toc-rebuild outputs;
- Raw Material state;
- Clean Material state.

## Required Interaction Changes

### 1. Task Detail Becomes Pipeline-First

The default task detail view must prioritize the pipeline and stage outputs before technical diagnostics.

Required visible sections:

- input PDF / source asset identity;
- pipeline stage strip or vertical stage list;
- MinerU output packet;
- AI metadata summary;
- toc-rebuild output packet;
- Raw Material / Clean Material state;
- next operator action.

Existing tabs may remain, but the user should not have to infer the workflow from scattered tabs and long technical panels.

### 2. Output Packets Use Product Labels

Show user-facing labels consistently:

- `PDF 原件`;
- `MinerU Markdown` for `full.md`;
- `MinerU JSON / Artifacts` for `content_list`, `middle`, images, and zip where present;
- `AI Metadata`;
- `目录重建 readable_tree`;
- `目录重建 rebuilt_markdown`;
- `目录重建 logic_tree`;
- `目录重建 skeleton`;
- `目录重建 provenance`;
- `Raw Material`;
- `Clean Material`.

Do not label `readable_tree.md` as the full rebuilt Markdown. The rebuilt full-text Markdown and readable directory tree must be visually distinct.

### 3. Markdown Comparison Is A Primary Inspection Surface

When both original MinerU Markdown and rebuilt Markdown exist, the UI must offer a clear primary comparison:

```text
left: MinerU Markdown / full.md
right: Rebuilt Markdown / rebuilt_markdown.md
```

`readable_tree.md` should be available as a directory/tree artifact, not mistaken for the reconstructed full document.

### 4. Library Becomes Asset-Packet Oriented

The library should be simpler and more traceable:

- reduce the first-level filter burden;
- make pipeline status the primary scan dimension;
- keep advanced filters collapsed by default;
- show compact per-asset output availability;
- provide clear actions: open PDF, compare Markdown, open output packet, open task/detail.

The library should feel like a material/output management surface, not a dense operational debug page.

### 5. Technical Evidence Moves Behind Disclosure

Move or keep these behind collapsed disclosure / technical evidence panels:

- object refs;
- raw JSON blobs;
- SHA/size details;
- event logs;
- low-level diagnostics;
- full artifact reference tables.

They must remain accessible for review and debugging, but they should not dominate the default operator path.

## Allowed Files / Modules

The implementation should stay within frontend UI and frontend helper code, for example:

- `src/app/pages/TaskManagementPage.tsx`;
- `src/app/pages/TaskDetailPage.tsx`;
- `src/app/pages/ProductsPage.tsx`;
- `src/app/pages/AssetDetailPage.tsx` only if needed for consistency;
- `src/app/components/MainlinePipelinePanel.tsx`;
- `src/app/components/CleanMaterialSummaryCard.tsx`;
- `src/app/components/CleanMaterialArtifactInspector.tsx`;
- `src/app/components/PreviewTabPanel.tsx`;
- new frontend-only components under `src/app/components/`;
- frontend-only formatting helpers under `src/app/utils/`.

Small CSS/styling changes are allowed when required by the UI simplification.

## Forbidden Operations

Do not perform any of the following:

- backend API behavior changes;
- DB schema changes or migrations;
- DB writes, cleanup, or backfill;
- MinIO object writes, deletes, moves, copies, or cleanup;
- Docker rebuild/restart/recreate;
- production deployment;
- runtime POST, submit-probe, or sample processing;
- CleanService / RawMaterial2CleanMaterial algorithm changes;
- broad workflow engine or approval-system implementation;
- readiness, release-readiness, UAT, pressure PASS, or go-live claims;
- changes to local private role files such as `AGENTS.md` or `.agents/**`.

If the desired UI needs backend data that is not currently exposed, stop at a graceful empty state or evidence-based limitation note. Do not invent backend writes or schema changes inside this task.

## Acceptance Criteria

Luceon will review against these criteria:

1. On a live task-detail page, an operator can identify the current pipeline stage, completed stage outputs, and next valid action without opening a technical evidence drawer.
2. On a task with toc-rebuild outputs, the UI clearly exposes `readable_tree`, `rebuilt_markdown`, `logic_tree`, `skeleton`, and `provenance` with correct labels.
3. Original MinerU Markdown and rebuilt full Markdown are compared as primary documents when both exist.
4. Library rows/cards show the asset packet state compactly and make PDF / Markdown comparison / output packet / task-detail actions discoverable.
5. Advanced filters, raw object refs, hashes, event logs, and diagnostics remain available but are not the default visual center.
6. Existing routes still work: `/cms/tasks`, `/cms/tasks/:id`, `/cms/library`, `/cms/asset/:id`, `/metadata`.
7. No backend mutation, DB mutation, MinIO mutation, Docker operation, production deploy, or readiness/go-live language is introduced.

## Required Validation

The execution report must include:

- `npx tsc --noEmit`;
- `npm run build`;
- `git diff --check`;
- browser/manual verification for:
  - `/cms/tasks`;
  - one `/cms/tasks/:id`;
  - `/cms/library`;
  - one `/cms/asset/:id`;
- short evidence that Markdown comparison uses full rebuilt Markdown when available;
- short evidence that `readable_tree.md` is not misrepresented as full rebuilt Markdown;
- a changed-file list and any residual limitations.

Screenshots are recommended but not mandatory if the report gives precise route and DOM/visible-text evidence.

## Stop Rule

Stop and return a report instead of expanding scope if:

- a required artifact cannot be found through existing metadata/API shape;
- the UI simplification requires backend schema/API changes;
- existing data shape cannot distinguish `readable_tree.md` from `rebuilt_markdown.md`;
- any implementation pressure appears to require DB/MinIO/runtime mutation.

## Required Report

Return a report under `TaskAndReport/` containing:

- implementation summary;
- changed files;
- route evidence;
- validation commands and results;
- screenshots or visible-text evidence if available;
- explicit no-backend/no-mutation statement;
- residual issues and recommended next task only if truly needed.

Luceon will then perform review, deployment decision, production restart if explicitly authorized, browser verification, and acceptance analysis.
