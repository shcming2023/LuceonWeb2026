# TASK-20260517-151654-P1-Operational-Menu-And-Settings-Governance-Correction

## 1. Task Summary

- Task ID: `TASK-20260517-151654-P1-Operational-Menu-And-Settings-Governance-Correction`
- Issued at: `2026-05-17T15:16:54+0800`
- Issuer: `Luceon`
- Next Actor: `Lucode`
- Priority: `P1`
- Suggested branch: `lucode/task-213-operational-menu-governance-correction`
- Expected report path: `TaskAndReport/2026-05-17T15-16-54+0800_P1-Operational-Menu-And-Settings-Governance-Correction_REPORT.md`

## 2. Context

Task 212 was reviewed at `8c07084` and was not accepted.

Review path:

`TaskAndReport/2026-05-17T15-16-54+0800_P1-Operational-Menu-And-Settings-Governance-Cleanup_LUCEON_REVIEW.md`

The implementation contains useful partial UI cleanup, but blocking issues remain:

- unauthorized global `AGENTS.md` rewrite with incorrect local path/mapping facts;
- unauthorized `pnpm-workspace.yaml` and `pnpm-lock.yaml` changes;
- `git diff --check f716c57..HEAD` fails;
- Settings-page consistency/orphan cleanup UI and logic are still present;
- `PROJECT_HISTORY.md` still contains active-looking LaTeX entry text;
- the report states checks passed where repository evidence does not support that.

## 3. Required Workspace

Use the mounted Lucode development workspace:

- Host: `/Users/concm/Dev_workspace/Luceon2026`
- Container: `/workspace/dev/Luceon2026`

Do not use `/home/home_dev/Luceon2026` for this task.

Production validation workspace remains:

- Host: `/Users/concm/prod_workspace/Luceon2026`
- Container: `/workspace/ops/Luceon2026`

Do not modify production runtime or data.

## 4. Required Corrections

### 4.1 Revert Unauthorized Global Rule And Package Metadata Changes

Revert these files to the pre-Task-212 state from `f716c57`:

```bash
git restore --source=f716c57 -- AGENTS.md pnpm-workspace.yaml pnpm-lock.yaml
```

If Lucode believes any of these files must remain changed, stop and report the reason instead of silently retaining the change.

### 4.2 Complete Settings Consistency Cleanup

In `src/app/pages/SettingsPage.tsx`, remove normal Settings-page consistency/orphan cleanup UI and logic so that the page no longer exposes orphan scan/cleanup as a normal setting.

Required cleanup targets:

- Remove `consistency` from `ActiveTab`.
- Remove `consistency` from valid tabs.
- Remove the `switchTab('consistency')` tab button and visible `一致性检查` label.
- Remove unused orphan cleanup state and handlers:
  - `orphanStats`
  - `orphanLoading`
  - `cleaningOrphans`
  - `orphanConfirmOpen`
  - `handleScanOrphans`
  - `handleCleanupOrphans`
- Ensure `SettingsPage.tsx` no longer calls:
  - `/__proxy/upload/audit/orphans`
  - `/__proxy/upload/audit/cleanup-orphans`

Do not delete backend audit or repair routes.

### 4.3 Fix LaTeX Documentation Contradiction

Update active documentation so it does not advertise LaTeX as a current retained CMS entry.

At minimum, fix the top summary in:

- `docs/codex/PROJECT_HISTORY.md`

Historical references may remain if they are clearly historical/deprecated and do not imply an active current route or active tool.

### 4.4 Preserve Accepted Partial Cleanup

Keep the valid Task 212 cleanup that does not conflict with this correction:

- removed active LaTeX route/nav/component;
- read-only audit wording improvements;
- removed mutating repair buttons from `DependencyHealthBanner`;
- improved health semantics in `OpsHealthPage`;
- Settings backup/import danger-zone separation, as long as checks pass and no task boundary is violated.

### 4.5 Fix Whitespace And Report Accuracy

Fix all `git diff --check` failures.

Update the Task 213 report truthfully. Do not claim a check passed unless it was actually run after the correction and exited 0.

## 5. Explicit Non-Goals

Do not:

- perform production deployment;
- restart services;
- run submit-probe;
- upload files;
- run pressure tests;
- clean DB, MinIO, Docker volumes, logs, models, or sample files;
- change secrets or runtime config;
- delete backend audit/repair routes;
- declare production readiness, L3, pressure PASS, release readiness, or go-live readiness;
- rewrite role/workflow/global project rules beyond reverting unauthorized Task 212 changes.

## 6. Required Checks

Run and report exact commands plus exit codes:

```bash
git diff --check f716c57..HEAD
git diff --check
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Run these search checks and include relevant output summary:

```bash
rg -n "backup/latex|LatexToolPage|LaTeX 工具" src docs/deploy docs/codex
rg -n "cleanup-orphans|audit/orphans|orphanStats|handleScanOrphans|handleCleanupOrphans|switchTab\\('consistency'\\)|activeTab === 'consistency'|一致性检查" src/app/pages/SettingsPage.tsx
rg -n "set this to true or false|allowBuilds" pnpm-workspace.yaml pnpm-lock.yaml
```

Expected:

- First search may still find historical/deprecated references in history docs, but active UI/source must not expose LaTeX.
- Second search should produce no normal Settings-page orphan cleanup UI/handler hits.
- Third search should produce no placeholder package-manager config hits.

If Playwright/page smoke is not run, record the exact reason.

## 7. Required Report

Write:

`TaskAndReport/2026-05-17T15-16-54+0800_P1-Operational-Menu-And-Settings-Governance-Correction_REPORT.md`

The report must include:

- task brief path;
- branch and HEAD;
- files changed;
- correction summary;
- commands run with exit codes;
- skipped checks and exact reasons;
- grep/search evidence summary;
- risks/blockers/residual debt;
- whether Luceon review is required.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Task 213 status: `Lucode 已回报待 Luceon 审查`
- Task 213 Next Actor: `Luceon`
- Include report path and HEAD.

Use a scoped branch if possible. If working directly on current `main` because the previous bad commit already landed on `main`, say so explicitly in the report and do not rewrite history.

