# TASK-20260517-094644-P1-Operational-Menu-And-Settings-Governance-Cleanup

## 1. Task Summary

- Task ID: `TASK-20260517-094644-P1-Operational-Menu-And-Settings-Governance-Cleanup`
- Issued at: `2026-05-17T09:46:44+0800`
- Issuer: `Luceon`
- Next Actor: `Lucode`
- Priority: `P1`
- Target branch suggestion: `lucode/task-212-operational-menu-settings-governance`
- Expected report path: `TaskAndReport/2026-05-17T09-46-44+0800_P1-Operational-Menu-And-Settings-Governance-Cleanup_REPORT.md`

## 2. Background

The user and Luceon reviewed the current CMS menu areas for:

- `LaTeX 工具`
- `一致性审计`
- `系统健康`
- `系统设置`

The agreed direction is repository/UI governance, not new product capability. The current mainline has moved beyond the standalone LaTeX browser tool, and several ops/settings surfaces still expose stale, duplicated, or risky controls that do not match the current production flow.

Current production mainline remains:

`upload -> local MinerU -> MinIO -> Ollama qwen3.5:9b -> AI metadata -> operator review`

This task should make the UI and active docs match that reality more clearly.

## 3. Goal

Clean up the CMS operational menu and settings surfaces so that:

1. The migrated LaTeX tool is removed from active navigation and routing.
2. Consistency audit is clearly read-only in the normal UI.
3. System health reflects current dependency/admission/progress semantics instead of stale legacy health assumptions.
4. System settings no longer make legacy or dangerous operations look like normal production controls.

Keep existing core upload, parse, AI, MinIO, and review behavior unchanged.

## 4. Required Scope

### 4.1 Remove Active LaTeX Tool Surface

Please:

- Remove the `LaTeX 工具` navigation entry from `src/app/components/Layout.tsx`.
- Remove the `/backup/latex` route and `LatexToolPage` import from `src/app/App.tsx`.
- Delete `src/app/pages/backup/LatexToolPage.tsx`.
- Delete `src/app/pages/backup/` only if it becomes empty and no imports remain.
- Update active documentation that still advertises LaTeX as an active CMS feature, especially:
  - `docs/deploy/DEPLOY.md`
  - `docs/codex/PROJECT_HISTORY.md`, if needed to mark the feature as retired/migrated rather than currently active.

Important:

- Do not remove `jszip`. It is still used by server-side ZIP parsing/full backup paths and tests.
- Historical task reports and archived history may retain old LaTeX references for traceability.

### 4.2 Make Consistency Audit Normal UI Read-Only

Please:

- Keep the `/audit` route and `AuditPage` as the canonical read-only consistency audit surface.
- Remove or relabel misleading `自动修复`, `READY`, or similar wording in `AuditPage` that implies the page is an active repair console.
- Prefer wording such as read-only finding, repair suggestion, manual handling required, or operator review required.
- Remove the settings page `一致性检查` tab from normal primary settings navigation, or reduce it to clearly non-destructive browser/local-cache utilities only.
- Remove or hide normal UI controls for orphan-object cleanup or repair/apply actions.

Do not delete these backend routes in this task:

- `/audit/consistency`
- `/audit/consistency/apply`
- `/audit/orphans`
- `/audit/cleanup-orphans`
- `/check-orphaned-files`
- `/repair-consistency`

Those endpoints may remain for explicit future task-authorized ops, tests, or compatibility.

### 4.3 Refresh System Health Semantics

Please rework the normal `系统健康` page so it reflects current runtime truth more accurately.

Preferred sources:

- `/__proxy/upload/ops/dependency-health`
- `/__proxy/upload/ops/mineru/admission-circuit`
- `/__proxy/upload/ops/mineru/diagnostics`
- `/__proxy/upload/ops/mineru/active-task`, if useful and already available

Required semantics:

- Keep the page read-only.
- Remove hardcoded stale version labels such as old UAT version strings, or replace them with neutral runtime/build text where a reliable field exists.
- MinerU display must distinguish:
  - simple `/health`
  - admission/submit readiness
  - active/queued work
  - diagnostics/log-observation state
- Do not imply MinerU `/health` alone means new intake is safe.
- Ollama display should use dependency-health fields where present, such as:
  - `readinessState`
  - `readinessSeverity`
  - `warmState`
  - `failureKind`
  - `probeTimeoutMs`
  - `recommendedClientTimeoutMs`
- MinIO display should come from current runtime/dependency health evidence where available, not stale UI assumptions.
- Do not call submit-probe from this page.
- Do not add start/restart/repair buttons.

For `DependencyHealthBanner`:

- Remove or hide one-click repair/start/restart action buttons from normal UI.
- Keep read-only dependency status and clear operator-facing advice.
- If command suggestions remain, they must be informational only and must not mutate runtime state from the page.

### 4.4 Simplify System Settings To Current Mainline

Please keep normal settings focused on current production-mainline configuration:

- Local MinerU endpoint/timeout/backend where still used.
- OCR/formula/table options if still used.
- MinIO core settings if still used by the app.
- Dictionary/tags configuration.
- Capacity/status information.
- Non-destructive export backup.

Please hide, clearly mark as compatibility-only, or remove from normal primary settings:

- Official/cloud MinerU API mode and fields, unless clearly marked legacy/compatibility.
- `tmpfiles` storage backend choice, unless clearly marked legacy/compatibility.
- AI multi-provider priority/fallback UI if it is not authoritative in strict production. The UI must not imply fallback behavior that the strict production worker does not use.
- High-risk restore/import/replace controls from normal settings. If retained, they must be placed behind clear advanced/danger wording and must not be made easier to trigger.

## 5. Explicit Non-Goals

Do not:

- Modify upload, parse, AI metadata, MinIO, or review business logic.
- Delete backend audit or repair routes.
- Change public API contracts unless strictly necessary to remove dead frontend usage, and document any such necessity.
- Perform production deployment, service restart, Docker action, DB operation, MinIO cleanup, data reset, sample mutation, submit-probe, upload, pressure test, or runtime validation.
- Claim production readiness, L3, pressure PASS, release readiness, or go-live readiness.
- Restore deprecated heuristic chapter preprocessing.
- Add skeleton fallback or silent degradation.

## 6. Suggested Files To Inspect

Likely files:

- `src/app/components/Layout.tsx`
- `src/app/App.tsx`
- `src/app/pages/backup/LatexToolPage.tsx`
- `src/app/pages/AuditPage.tsx`
- `src/app/pages/OpsHealthPage.tsx`
- `src/app/pages/SettingsPage.tsx`
- `src/app/components/DependencyHealthBanner.tsx`
- `uat/tests/pages-smoke.spec.ts`
- `docs/deploy/DEPLOY.md`
- `docs/codex/PROJECT_HISTORY.md`

Possible supporting files:

- `server/upload-server.mjs`
- `server/lib/consistency-routes.mjs`
- `server/lib/ops-mineru-diagnostics.mjs`
- `src/store/types.ts`
- `src/store/seedData.ts`
- `package.json`

Inspect supporting files only as needed to avoid stale assumptions.

## 7. Required Checks

Run and report exit codes:

```bash
git diff --check
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Also run the most relevant existing UI/static smoke when feasible. Recommended:

```bash
npx pnpm@10.4.1 --dir uat exec playwright test uat/tests/pages-smoke.spec.ts
```

If local runtime requirements make the Playwright smoke infeasible, record the exact reason and any alternate static check used.

Recommended search checks:

```bash
rg -n "backup/latex|LatexToolPage|LaTeX 工具" src docs/deploy docs/codex
rg -n "cleanup-orphans|repair-consistency|自动修复|READY" src/app
```

Historical references in old reports may remain. Active UI/docs should not advertise retired functionality as current.

## 8. Required Lucode Report

Write:

`TaskAndReport/2026-05-17T09-46-44+0800_P1-Operational-Menu-And-Settings-Governance-Cleanup_REPORT.md`

The report must include:

- Task brief path.
- Branch and HEAD.
- Files changed.
- Implementation/product summary.
- Commands run with exit codes.
- Skipped checks with exact reasons.
- Evidence, including before/after grep or route/menu evidence where useful.
- Risks, blockers, residual debt.
- Whether Luceon review is required.

Update `TaskAndReport/TASK_TRACKING_LIST.md` to `Lucode 已回报待 Luceon 审查` when done, with report path, branch/HEAD, and `Next Actor=Luceon`.

Push the implementation branch and report/ledger updates to GitHub for Luceon review.

