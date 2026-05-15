# Architect Report: P1 CleanService Canonical Architecture Docs Reconciliation

- Task ID: `TASK-20260515-194038-P1-CleanService-Canonical-Architecture-Docs-Reconciliation`
- Assignee: Architect
- Based on Director task brief: `TaskAndReport/2026-05-15T19-40-38+0800_P1-CleanService-Canonical-Architecture-Docs-Reconciliation_TASK.md`
- Workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `main`
- HEAD before this report commit: `0c3b1bf`
- Report date: 2026-05-15

## Scope Confirmation

I executed this as the Architect task assigned by Director.

The work is documentation-only and limited to the allowed canonical architecture/contract docs, this report, and the task ledger. I did not edit source code, runtime, production files, Docker, DB, MinIO, MinerU, Ollama, role contracts, `PROJECT_STATE`, or `HANDOFF`. I did not copy the raw zip into the repository, implement CleanServiceWorker, implement Mineru2Table API changes, mutate production, run validation, run upload/pressure/submit-probe/retry/reparse/re-AI, or claim implementation acceptance, readiness, L3, pressure PASS, production readiness, release readiness, production上线, or go-live.

## Files Changed

Created:

- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- `docs/contracts/CleanService-Protocol-v1.md`
- `docs/codex/decisions/2026-05-15_clean-pipeline-foundation.md`
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`
- `TaskAndReport/2026-05-15T19-40-38+0800_P1-CleanService-Canonical-Architecture-Docs-Reconciliation_REPORT.md`

Updated:

- `TaskAndReport/TASK_TRACKING_LIST.md`

## Canonical Doc Summaries

### Asset Pipeline Vision

`docs/architecture/Luceon2026-Asset-Pipeline-Vision.md` records the future asset-pipeline direction. It preserves PRD v0.4 as the current mainline and scopes CleanService as a future extension. It defines the target asset layers, Luceon-owned identity/version model, future `eduassets-raw` / `eduassets-clean` layout for new assets, CleanServiceWorker orchestration direction, no fixed retention count, no automatic cleanup, and `¥5` / `¥8` cost boundaries.

### CleanService Protocol v1

`docs/contracts/CleanService-Protocol-v1.md` defines the shared target protocol for CleanService implementations. It specifies service identity, health, `POST /api/v1/jobs`, job state, MinIO ObjectRef inputs/outputs, Luceon-owned `asset_version`, webhook signing, required provenance, structured errors, `quota_exceeded`, cost hard limit fields `options.max_cost_cny` and `options.max_tokens_total`, multipart deprecation, observability, and byte-identical mirror obligation with implementation repositories.

### Clean Pipeline ADR

`docs/codex/decisions/2026-05-15_clean-pipeline-foundation.md` records the accepted architecture decisions from the PRD addendum and prior absorption report. It replaces open questions with concrete decisions: legacy retained, Luceon assigns `assetVersion`, no fixed retention count, no automatic cleanup, multipart deprecated/retained, `¥5` soft and `¥8` hard cost limits, and byte-identical protocol mirroring.

### Mineru2Table Adaptation Plan

`docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md` describes the external dependency work needed in Mineru2Table2026 before Luceon implementation. It covers MinIO storage, persistent jobs, protocol endpoints, outputs, provenance, webhook, structured errors, cost hard limit, deprecated old multipart routes, Docker/config expectations, test expectations, and Luceon-side dependency evidence.

## Reconciliation Coverage

Confirmed in the new docs:

- PRD addendum boundary: current PRD v0.4 mainline remains current.
- Q-1: legacy data retained; new layout applies only after implementation.
- Q-2: Luceon assigns `assetVersion`.
- Q-3: no fixed old-version retention count.
- Q-4: no automatic cleanup in this phase.
- Q-5: old multipart routes deprecated but retained for at least one version cycle.
- Q-6: Luceon soft cost limit `¥5`, service hard limit `¥8`.
- Explicit failure/no silent fallback semantics.
- MinIO ObjectRef handoff.
- Byte-identical protocol obligation with Mineru2Table2026.
- Clear statement that these docs are future architecture direction, not current runtime/readiness evidence.

## Commands And Checks Run

| Command | Purpose | Result |
| --- | --- | --- |
| `git status --short --branch` | Required Architect check-task state check | Passed |
| `rg -n "\\| Architect \\|" TaskAndReport/TASK_TRACKING_LIST.md` | Locate Architect task row | Passed |
| `sed -n ...` on required task, PRD, reports, reviews, and role docs | Required reading | Passed |
| `mkdir -p docs/architecture docs/contracts docs/codex/decisions` | Create allowed docs directories | Passed |
| `rg -n "¥5|¥8|max_cost_cny|..." <new docs>` | Reconciliation keyword check | Passed |
| `wc -l <new docs>` | Confirm created docs have content | Passed |
| `git log -1 --oneline && git rev-parse --short HEAD` | Record pre-commit HEAD | Passed |

## Skipped Checks

- No TypeScript, build, UAT, runtime, production, upload, pressure, or submit-probe checks were run because this task is docs-only and explicitly forbids validation/runtime mutation.
- No external Mineru2Table repository check was run because this task is confined to the Luceon2026 workspace.
- No raw zip copy or extraction into the repository was performed.

## Unresolved Architecture Questions

Remaining questions for later Director-dispatched work:

1. Whether `toc-rebuild` gates all AI metadata or only future chapter-level workflows.
2. Exact operator-facing state labels for CleanService stages.
3. Whether hash-based `materialId` becomes global or applies only to future clean assets.
4. How legacy assets are labeled in library views.
5. The cross-repo operational process for keeping `CleanService-Protocol-v1.md` byte-identical.
6. Exact Luceon callback endpoint, task-state mapping, and audit schema.

## Recommended Next Role Task

Recommended next actor: `Director`.

Recommended Director decision: review the four canonical docs and either accept them, return them for revision, or dispatch the next Architect task for `Luceon CleanServiceWorker Implementation Plan`.

If accepted, the next practical sequence should be:

1. Architect implementation plan for Luceon CleanServiceWorker.
2. DevelopmentEngineer or cross-repo task for Mineru2Table CleanService Protocol v1 compatibility.
3. DevelopmentEngineer Luceon implementation only after protocol dependency scope is accepted.
4. TestAcceptanceEngineer validation plan separating mock protocol, real Mineru2Table E2E, operator review, and release boundary.

## GitHub Sync Status

Pending at report-write time. The Director task brief requires commit and push to GitHub `main`; I will perform that after local diff/status validation.

