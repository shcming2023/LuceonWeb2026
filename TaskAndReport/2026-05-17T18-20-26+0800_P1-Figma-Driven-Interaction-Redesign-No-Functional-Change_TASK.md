# TASK-20260517-182026-P1-Figma-Driven-Interaction-Redesign-No-Functional-Change

## 1. Task Summary

- Task ID: `TASK-20260517-182026-P1-Figma-Driven-Interaction-Redesign-No-Functional-Change`
- Task row: `218`
- Issued at: `2026-05-17T18:20:26+0800`
- Issuer: `Luceon`
- Next Actor: `Lucode`
- Priority: `P1`
- Suggested branch: `lucode/task-218-figma-interaction-redesign`
- Expected report path: `TaskAndReport/2026-05-17T18-20-26+0800_P1-Figma-Driven-Interaction-Redesign-No-Functional-Change_REPORT.md`
- Figma baseline: `https://www.figma.com/design/CRfnwKnA6zwZkF0uvoBvLV`

## 2. Context

The user requested introducing Figma to refactor the current project interaction so the product becomes clearer, more user-friendly, and easier to operate, while explicitly preserving existing functionality.

Luceon created an initial Figma design baseline:

- File: `Luceon2026 Interaction Redesign Baseline`
- File key: `CRfnwKnA6zwZkF0uvoBvLV`
- URL: `https://www.figma.com/design/CRfnwKnA6zwZkF0uvoBvLV`
- Pages:
  - `00 Interaction Contract`
  - `01 Current And Target IA`
  - `02 Key Wireframes`
  - `03 Implementation Acceptance`

Current product anchors from `origin/main@68656d81de8ab23166ed792f971623edc418e0a8`:

- Main task route: `/tasks`
- Task detail route: `/tasks/:id`
- Library route: `/library`
- Governance routes: `/audit`, `/ops/health`, `/settings`
- Phase 1 mainline: `upload -> MinIO -> local MinerU -> parsed artifacts -> Ollama qwen3.5:9b -> AI metadata -> operator review`

Tasks 213-217 already advanced on GitHub before this task could be pushed. Treat this as Task 218 and do not start it until the current earliest open Luceon/Lucode task is completed, reviewed, and merged or otherwise explicitly cleared by Luceon.

## 3. Goal

Implement a Figma-driven interaction refactor that improves clarity and operator ergonomics without changing product functionality.

The redesign should make these flows easier to understand:

- create or upload parsing tasks;
- observe queue/progress and dependency signals;
- distinguish `pending`, `running`, `result-store`, `ai-pending`, `ai-running`, `review-pending`, `completed`, `failed`, and `canceled`;
- open task detail and review Markdown/PDF, metadata, events, and evidence;
- recover from failure using existing retry/reparse/re-AI/cancel actions;
- search completed assets in the library;
- keep audit, health, and settings clearly separated from daily task work.

## 4. Hard Scope Boundary

This is an interaction/UI refactor only.

Allowed:

- layout, spacing, typography, grouping, visual hierarchy, responsive behavior;
- navigation copy and page titles when they preserve existing route/function meaning;
- button grouping and destructive-action confirmation affordances using existing actions;
- empty/loading/error states for existing data;
- status explanations that reflect existing backend semantics;
- component extraction or local UI helper cleanup if it only supports the redesign.

Forbidden unless Luceon issues a separate task:

- adding new business features;
- changing backend routes, request payloads, response schemas, DB fields, task state machine, MinIO semantics, or worker behavior;
- deleting backend audit/repair/ops endpoints;
- changing upload, retry, reparse, re-AI, cancel, backup/import/export, or cleanup semantics;
- production deployment, service restart, upload validation, submit-probe, pressure test, DB/MinIO/Docker cleanup, secret/model/sample mutation;
- declaring production readiness, release readiness, L3, pressure PASS, or go-live readiness.

If implementing the desired interaction appears to require a functional or backend change, stop and report the required change instead of making it.

## 5. Required Implementation Targets

Read the Figma baseline first, then inspect the current React/Tailwind implementation.

Minimum UI surfaces to consider:

- `src/app/components/Layout.tsx`
- `src/app/pages/TaskManagementPage.tsx`
- `src/app/pages/TaskDetailPage.tsx`
- `src/app/pages/ProductsPage.tsx`
- `src/app/pages/AssetDetailPage.tsx`
- `src/app/pages/AuditPage.tsx`
- `src/app/pages/OpsHealthPage.tsx`
- `src/app/pages/SettingsPage.tsx`
- relevant shared components under `src/app/components/`

Required outcomes:

1. The daily operator path should read as task-first: create/upload task, monitor task, review result, use library.
2. Governance surfaces should feel secondary and should not compete with task work.
3. Status, dependency health, and task progress must be visually distinct.
4. Destructive or high-risk existing actions must be grouped and labeled so they cannot be mistaken for routine actions.
5. Empty, loading, failure, and review-pending states should be understandable without changing behavior.
6. The implementation should preserve current API calls and action handlers unless a separate Luceon task authorizes functional work.

## 6. Required Checks

Run and report exact commands plus exit codes:

```bash
git diff --check
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Also run targeted grep checks and summarize results:

```bash
rg -n "fetch\\(|/__proxy|EventSource|new WebSocket|localStorage|sessionStorage" src/app
rg -n "retry|reparse|re-ai|cancel|backup|import|export|cleanup|reset" src/app/pages src/app/components
```

Expected:

- existing API/action call sites may remain;
- no new backend endpoint or state-machine dependency should be introduced;
- any changed call site must be explicitly justified as UI-only and behavior-preserving.

If a browser/UI smoke is run, include the URL, viewport, routes checked, and screenshot summary. If it is skipped, record the exact reason.

## 7. Required Report

Write:

`TaskAndReport/2026-05-17T18-20-26+0800_P1-Figma-Driven-Interaction-Redesign-No-Functional-Change_REPORT.md`

The report must include:

- task brief path;
- Figma file URL used;
- branch and HEAD;
- files changed;
- implementation summary by page/surface;
- explicit confirmation that no functional/API/backend/state-machine change was made, or a precise exception report if blocked;
- commands run with exit codes;
- grep evidence summary;
- browser/UI smoke evidence or skipped reason;
- risks/blockers/residual debt;
- whether Luceon review is required.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Task 218 status: `Lucode 已回报待 Luceon 审查`
- Task 218 Next Actor: `Luceon`
- Include report path and HEAD.

Use a scoped branch from current `origin/main` after the earlier active task queue is closed or explicitly cleared.
