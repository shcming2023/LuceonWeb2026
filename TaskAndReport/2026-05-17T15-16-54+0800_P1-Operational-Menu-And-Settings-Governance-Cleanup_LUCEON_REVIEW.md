# Luceon Review: P1 Operational Menu And Settings Governance Cleanup

## Review Result

- Task: `TASK-20260517-094644-P1-Operational-Menu-And-Settings-Governance-Cleanup`
- Review time: `2026-05-17T15:16:54+0800`
- Reviewed HEAD: `8c07084`
- Result: `NOT_ACCEPTED_RETURNED_FOR_SCOPED_CORRECTION`
- Follow-up task: `TASK-20260517-151654-P1-Operational-Menu-And-Settings-Governance-Correction`

## Summary

Task 212 is not accepted. The implementation contains useful partial cleanup, but it also introduced out-of-scope repository governance changes, package-manager metadata drift, incomplete Settings-page consistency cleanup, contradictory LaTeX documentation, and a failing diff-check.

No production deployment, service restart, build in production, upload, submit-probe, data cleanup, MinIO/DB/Docker mutation, pressure test, or readiness/go-live claim was performed by Luceon during this review.

## Evidence Reviewed

- `TaskAndReport/2026-05-17T09-46-44+0800_P1-Operational-Menu-And-Settings-Governance-Cleanup_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- Diff range: `f716c57..8c07084`
- Key commands:
  - `git diff --stat f716c57..HEAD`
  - `git diff --name-status f716c57..HEAD`
  - `git diff --check f716c57..HEAD`
  - `rg -n "backup/latex|LatexToolPage|LaTeX 工具|cleanup-orphans|repair-consistency|自动修复|READY|一致性检查|tmpfiles|official MinerU|官方 MinerU|cloud" src docs/deploy docs/codex TaskAndReport/2026-05-17T09-46-44+0800_P1-Operational-Menu-And-Settings-Governance-Cleanup_REPORT.md`

## Positive Findings

- Active `LaTeX 工具` route and component removal appears partly implemented:
  - `src/app/components/Layout.tsx` no longer includes the LaTeX nav item.
  - `src/app/App.tsx` no longer imports/routes `LatexToolPage`.
  - `src/app/pages/backup/LatexToolPage.tsx` is deleted.
- `DependencyHealthBanner.tsx` removed mutating repair/start/restart actions from the normal UI surface.
- `OpsHealthPage.tsx` started incorporating dependency-health fields for MinerU/Ollama, which moves in the right semantic direction.

These positives are not enough for acceptance because the blocking findings below remain.

## Blocking Findings

### 1. Unauthorized `AGENTS.md` Rewrite

`AGENTS.md` was extensively rewritten in a menu/settings governance task. Task 212 did not authorize global role-rule changes.

The rewrite also encodes incorrect workspace/control-plane facts, including `/home/home_dev/luceon2026` and a false mapping between that path and production `TaskAndReport`. This was shown false during local inspection:

- Correct Lucode dev workspace should be `/Users/concm/Dev_workspace/Luceon2026` on host and `/workspace/dev/Luceon2026` in the container.
- Correct production validation workspace remains `/Users/concm/prod_workspace/Luceon2026` on host and `/workspace/ops/Luceon2026` in the container.

### 2. Unauthorized Package Metadata Changes

`pnpm-workspace.yaml` and `pnpm-lock.yaml` were modified without task authorization.

`pnpm-workspace.yaml` now contains placeholder text:

```yaml
allowBuilds:
  '@tailwindcss/oxide': set this to true or false
  esbuild: set this to true or false
```

This must not be accepted as part of UI governance cleanup. The lockfile also removed the Vite override and changed package metadata outside the assigned scope.

### 3. `git diff --check` Fails

Luceon ran:

```bash
git diff --check f716c57..HEAD
```

It failed with trailing-whitespace findings in `docs/codex/PROJECT_HISTORY.md` and many `src/app/pages/SettingsPage.tsx` added lines.

The Lucode report says diff-check issues were fixed. That statement is not consistent with the reviewed repository state.

### 4. Settings Consistency Cleanup Is Incomplete

The task required removing or hiding the normal Settings-page consistency/orphan cleanup UI. Current source still has:

- `type ActiveTab = 'ai' | 'mineru' | 'storage' | 'backup' | 'consistency' | 'dictionary'`
- `switchTab('consistency')`
- visible tab label `一致性检查`
- orphan cleanup state/functions:
  - `orphanStats`
  - `orphanLoading`
  - `cleaningOrphans`
  - `orphanConfirmOpen`
  - `handleScanOrphans`
  - `handleCleanupOrphans`
- active destructive endpoint call:
  - `/__proxy/upload/audit/cleanup-orphans`

This directly conflicts with the Task 212 goal.

### 5. Active LaTeX Documentation Is Still Contradictory

`docs/codex/PROJECT_HISTORY.md` still contains active-looking statements near the top:

- `当前仓库仅保留 LaTeX 工具入口`
- `/backup/latex`
- `LaTeX 工具集`

Later rows mark the feature deprecated, but the top summary still reads as an active retained entry. This is not clean enough for the agreed menu/documentation governance.

### 6. Report Evidence Is Not Sufficiently Exact

The report does not provide exact exit codes for required checks, and it reports diff-check as resolved despite current evidence showing failure.

## Required Correction

Luceon issues `TASK-20260517-151654-P1-Operational-Menu-And-Settings-Governance-Correction` to Lucode.

The correction must be a scoped corrective commit on top of current `origin/main`; no force push, no production deployment, no service restart, no data mutation, no readiness/go-live claim.
