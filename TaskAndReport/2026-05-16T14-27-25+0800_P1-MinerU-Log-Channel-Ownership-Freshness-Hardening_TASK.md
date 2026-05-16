# P1 MinerU Log Channel Ownership Freshness Hardening

Task ID: TASK-20260516-142725-P1-MinerU-Log-Channel-Ownership-Freshness-Hardening

Assignee: DevelopmentEngineer

Issued by: Director

Issued at: 2026-05-16T14:27:25+0800

Project: Luceon2026

Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path: `/Users/concm/prod_workspace/Luceon2026`

GitHub: `https://github.com/shcming2023/Luceon2026`

TaskAndReport record: `TaskAndReport/2026-05-16T14-27-25+0800_P1-MinerU-Log-Channel-Ownership-Freshness-Hardening_TASK.md`

Expected report: `TaskAndReport/2026-05-16T14-27-25+0800_P1-MinerU-Log-Channel-Ownership-Freshness-Hardening_REPORT.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- Task 205 task/report/supplemental reports/director review:
  - `TaskAndReport/2026-05-16T08-48-28+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_TASK.md`
  - `TaskAndReport/2026-05-16T08-48-28+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_REPORT.md`
  - `TaskAndReport/2026-05-16T08-55-06+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_SUPPLEMENTAL_REPORT.md`
  - `TaskAndReport/2026-05-16T09-02-28+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_SUPPLEMENTAL_REPORT.md`
  - `TaskAndReport/2026-05-16T11-07-20+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_SUPPLEMENTAL_REPORT.md`
  - `TaskAndReport/2026-05-16T13-07-20+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_SUPPLEMENTAL_REPORT.md`
  - `TaskAndReport/2026-05-16T14-27-25+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_DIRECTOR_REVIEW.md`

## Background

Task 205 showed that the deployed `progressSnapshot` contract prevented a false failure judgment during a fresh 24-PDF long run. During active parsing, Luceon correctly prioritized direct MinerU API status and used an operator message such as `MinerU API 仍在处理`.

However, Task 205 also preserved a real residual: the configured/container log-channel diagnostics can still report stale/idle while host MinerU logs are fresh and show business progress. That means the project improved progress semantics, but MinerU log integration is not fully closed.

The goal now is to harden the log-channel ownership/freshness contract so future operators can understand why one log source is stale and another is fresh without relying on ad hoc terminal inspection.

## Objective

Implement a scoped code/test-level hardening for MinerU log-channel ownership and freshness diagnostics.

The expected outcome is not a new parsing feature. It is clearer, source-aware observability:

- distinguish configured/container-mounted log-channel freshness from host MinerU log freshness,
- expose which source supplied progress evidence,
- avoid allowing a stale configured channel to obscure host-fresh progress evidence,
- keep direct MinerU API as the authoritative progress fallback when logs are unavailable or unattributable,
- preserve strict no-false-failure semantics.

## Non-Goals

- Do not change PDF parsing behavior.
- Do not change task scheduling, admission circuit, MinIO storage, AI metadata, retry/reparse/re-AI logic, or review workflow.
- Do not implement CleanService or Mineru2Table protocol integration.
- Do not deploy to production.
- Do not run pressure tests or upload files.
- Do not claim pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

## Allowed Files / Modules

Keep the edit scope tight. Likely allowed areas include:

- `server/lib/ops-mineru-diagnostics.mjs`
- MinerU observability routes in `server/upload-server.mjs`, only if required
- MinerU log observer code under `ops/`, only if required
- Focused tests under `server/tests/`
- Narrow documentation notes under `docs/` or `TaskAndReport/` if needed to explain the new diagnostic fields

If a necessary file falls outside this list, explain it in the completion report and keep the diff minimal.

## Forbidden Changes

- Do not modify production workspace files.
- Do not restart/rebuild/redeploy any service.
- Do not run manual submit-probe.
- Do not upload, clear/reset data, retry, reparse, re-AI, repair, cancel, or mutate task/material state.
- Do not mutate DB, MinIO objects/volumes, Docker volumes, model files, secrets, config, or sample files.
- Do not pull/delete/replace Ollama models.
- Do not change PRD truth, role contracts, release judgments, milestone records, or unrelated docs.
- Do not broaden into CleanService/Mineru2Table work.
- Do not hide or remove stale-log diagnostics; make them source-aware instead.

## Suggested Direction

First inspect the current observability implementation and tests. Then implement the smallest contract improvement that makes the Task 205 residual explicit.

Suggested behavior:

- Represent multiple log evidence sources separately, for example configured/container channel versus host MinerU log path.
- When configured/container log source is stale but a host log source is fresh, expose both facts instead of a single flattened `logState=stale`.
- Include source identity, freshness, mtime/observedAt, and any attribution warning in diagnostic output.
- Keep `progressSnapshot.source=direct-mineru` when log evidence is fresh but unattributable to a specific Luceon task.
- If host log path is not configured or unavailable, degrade to source-aware diagnostic warning only; do not mark active processing as failed.
- Preserve the operator-facing principle: stale logs are diagnostic warnings, not parse-failure evidence while direct MinerU API is processing.

Do not invent production-only paths as hard requirements. If local host log probing is environment-specific, make it optional/configured and safe.

## Required Checks

Run the strongest relevant checks available within scope:

- `git diff --check`
- `node --check` on changed `.mjs` files
- focused MinerU diagnostics/progress tests covering:
  - stale configured channel + fresh host log source,
  - no log source + direct MinerU processing,
  - terminal/idle state does not show misleading active progress,
  - existing Task 193/205 progress semantics remain compatible
- `npx pnpm@10.4.1 exec tsc --noEmit` if TypeScript surface is affected or as a final broad check when practical

If a check cannot be run, report the exact reason.

## Required Evidence

Completion report must include:

- Root-cause summary for why Task 205 saw stale log-channel diagnostics while host logs were fresh.
- Files changed.
- Contract fields added/changed, with example output.
- Test coverage added/updated.
- Commands run with exit codes.
- Skipped checks with exact reasons.
- Risks and residual debt.
- Confirmation that no production/runtime/data mutation occurred.

## GitHub Sync Requirements

- Before starting: `git status --short --branch`; fetch/pull only if needed to align with current `origin/main`.
- Use a scoped branch if the role workflow requires it; otherwise keep commits traceable and scoped.
- Commit and push implementation/report changes to GitHub.
- Do not overwrite unrelated local changes.

## Completion Report Requirements

Write the completion report to:

`TaskAndReport/2026-05-16T14-27-25+0800_P1-MinerU-Log-Channel-Ownership-Freshness-Hardening_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md` with:

- status,
- report path,
- branch/HEAD,
- next actor,
- next action,
- required output.

The report must include:

- Confirmation that work was based on this Director task brief.
- Branch and HEAD.
- Files changed.
- Implementation summary.
- Commands run with exit codes.
- Checks skipped and exact reasons.
- Evidence.
- Risks, blockers, and residual debt.
- GitHub sync status.
- Whether Director review is required.

## Acceptance Criteria

Director can accept this task when:

- log-channel diagnostics are source-aware enough to explain the Task 205 stale-container/fresh-host situation,
- direct MinerU API remains authoritative when logs are stale or unattributable,
- focused tests cover the stale/fresh multi-source behavior,
- no parse/AI/business workflow behavior is broadened,
- no production/runtime/data mutation or readiness claim occurs.
