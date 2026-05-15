# ProductManager Report: P1 CleanService Mineru2Table PRD Addendum

- Task ID: `TASK-20260515-192928-P1-CleanService-Mineru2Table-PRD-Addendum`
- Assignee: `ProductManager`
- Based on Director task brief: `TaskAndReport/2026-05-15T19-29-28+0800_P1-CleanService-Mineru2Table-PRD-Addendum_TASK.md`
- Workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `main`
- HEAD at report time: `0de9512`
- Report date: 2026-05-15

## Scope Confirmation

I executed this as a ProductManager task based on the Director task brief.

The work is product documentation only. I did not edit business code, architecture contracts, source/runtime/production files, role contracts, Docker, DB, MinIO, MinerU, Ollama, secrets, configs, samples, or the raw external zip. I did not run validation, mutate production, perform upload/pressure/submit-probe/retry/reparse/re-AI, or claim CleanService readiness, pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

## Files Changed

- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`
- `TaskAndReport/2026-05-15T19-29-28+0800_P1-CleanService-Mineru2Table-PRD-Addendum_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Evidence Consulted

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/product-manager.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-15T19-21-13+0800_P1-CleanService-Mineru2Table-Docs-Absorption_REPORT.md`
- `TaskAndReport/2026-05-15T19-29-28+0800_P1-CleanService-Mineru2Table-Docs-Absorption_DIRECTOR_REVIEW.md`

## Addendum Summary

The PRD addendum defines Mineru2Table as a future `toc-rebuild` CleanService product direction, while preserving PRD v0.4 as the current mainline.

It covers:

- product value for operator review and downstream educational asset quality;
- operator workflow impact and UI/review expectations;
- scope and non-goals;
- relationship to the current upload -> MinerU -> MinIO -> Ollama -> AI metadata -> review mainline;
- legacy asset policy: existing data remains legacy; new tasks use the new layout only after implementation;
- six user decisions from the Architect absorption report;
- cost policy: Luceon soft limit `¥5`, service hard limit `¥8`, and explicit Director/User decision behavior;
- acceptance criteria for future CleanService/Mineru2Table integration;
- explicit failure semantics and no silent fallback;
- validation boundary across mock protocol, real Mineru2Table E2E, and operator review;
- release boundary: this addendum is not readiness or go-live evidence.

## Confirmed Requirements

- Mineru2Table is product-scoped as a future `toc-rebuild` CleanService, not a current implemented stage.
- Luceon remains the orchestrator for material/version/task/review/cost/audit semantics.
- Clean output must be a distinct lifecycle stage, not silently mixed into raw MinerU artifacts.
- Legacy assets remain legacy unless a separate migration task is authorized.
- New clean-layout behavior applies only after future implementation.
- Cost soft/hard limits must be visible and enforceable in product flow.
- Partial/unresolved anchors must be visible to the operator.
- CleanService failure must be explicit; no skeleton/raw-output silent fallback may be represented as clean success.

## Pending Product Questions

1. Whether `toc-rebuild` runs before all AI metadata or only before future chapter-level extraction.
2. Exact operator-facing state labels for CleanService stages.
3. Exact UX for `¥5` soft-limit pause and Director/User decision flow.
4. Whether new identity/versioning remains compatible with `mat-{timestamp}` or introduces a new identity model for new assets.
5. How legacy assets are labeled in library views.
6. Cross-repo protocol synchronization process with Mineru2Table2026.

## Commands And Checks Run

| Command | Purpose | Result |
| --- | --- | --- |
| `git status --short --branch` | Required ProductManager check-task state check | Passed |
| `sed -n ...` on required docs/task files | Required reading | Passed |
| `git rev-parse --abbrev-ref HEAD` | Record branch | Passed |
| `git rev-parse --short HEAD` | Record HEAD | Passed |
| `rg -n "CleanService|Mineru2Table|toc-rebuild|¥5|8|legacy|multipart|silent fallback|silent|fallback" ...` | Cross-check product terms and prior evidence | Passed |

## Skipped Checks

- No TypeScript/build/runtime/UAT checks were run because this task is product documentation only.
- No production/runtime checks were run because the task forbids validation and production mutation.
- No GitHub fetch/pull was run because ProductManager check-task rules prohibit routine GitHub synchronization.

## Recommended Next Role Task

Recommended next actor: `Director`.

Recommended next action: Director reviews the PRD addendum. If accepted, dispatch Architect for canonical CleanService architecture/contract reconciliation based on this addendum and the accepted six user decisions. The Architect task should write reconciled docs rather than copying the raw source bundle.

## GitHub Sync Status

The Director task brief asks to commit and push the addendum, report, and ledger update to GitHub `main`. ProductManager will perform that only within the task-brief authorization and after local diff validation.
