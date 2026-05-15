# Architect Report: P1 CleanService Mineru2Table Docs Absorption

- Task ID: `TASK-20260515-192113-P1-CleanService-Mineru2Table-Docs-Absorption`
- Assignee: Architect
- Based on Director task brief: `TaskAndReport/2026-05-15T19-21-13+0800_P1-CleanService-Mineru2Table-Docs-Absorption_TASK.md`
- Workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `main`
- HEAD: `8124c62`
- Report date: 2026-05-15

## Scope Confirmation

This report is architecture/document absorption only. I did not implement code, promote canonical docs, copy the raw zip into the repository, mutate runtime/production, run upload/pressure/submit-probe/cleanup/restart/redeploy/retry/reparse/re-AI, or claim readiness/L3/pressure PASS/go-live.

Repository changes made by this task are limited to:

- this report file;
- the task-ledger row for Task 182.

## Commands Run

| Command | Purpose | Exit |
| --- | --- | --- |
| `git status --short --branch` | Required first repository state check | 0 |
| `rg -n "\\| Architect \\|" TaskAndReport/TASK_TRACKING_LIST.md` | Locate Architect task row | 0 |
| `sed -n ...` on required repo docs and task brief | Required reading | 0 |
| `unzip -l <source zip>` | Inventory source bundle | 0 |
| `unzip -p <source zip> <member>` for each source markdown file | Read source files without extracting into repo | 0 |
| `find docs -maxdepth 3 ...` and `test -e <target paths>` | Check current repo gaps and target doc existence | 0 |
| `git rev-parse --short HEAD` | Record current HEAD | 0 |

No GitHub sync command, runtime command, production command, or submit-probe command was run during analysis.

## Source Bundle Inventory

Source zip read from:

`/Users/concm/Library/Containers/com.tencent.WeWorkMac/Data/Documents/Profiles/9F6D6C5415707EC04A6FE091F21E329F/Caches/Files/2026-05/23189c0bfaea54aefaf7bcfd57a308b3/fri_may_15_2026_overview_of_luceon_2026_and_mineru_2.zip`

Readable members:

| File | Size | Readable | Role |
| --- | ---: | --- | --- |
| `fri_may_15_2026_overview_of_luceon_2026_and_mineru_2.md` | 111445 | Yes | Copilot conversation export, including final six user decisions and placement guidance |
| `v1_docs/architecture/Luceon2026-Asset-Pipeline-Vision.md` | 13423 | Yes | Draft architecture vision |
| `v1_docs/contracts/CleanService-Protocol-v1.md` | 14390 | Yes | Draft shared service protocol |
| `v1_docs/codex/decisions/2026-05-15_clean-pipeline-foundation.md` | 8453 | Yes | Draft ADR |
| `v1_Docs/CleanService-Adaptation-Plan.md` | 15236 | Yes | Draft Mineru2Table adaptation plan |

All expected files were readable. The zip should remain an external source; do not copy it or raw extracted content into this repository.

## Current Repo Gaps

The proposed canonical target documents do not currently exist in this workspace:

| Target path | Exists now | Comment |
| --- | --- | --- |
| `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md` | No | `docs/architecture/` itself is not present |
| `docs/contracts/CleanService-Protocol-v1.md` | No | `docs/contracts/` itself is not present |
| `docs/codex/decisions/2026-05-15_clean-pipeline-foundation.md` | No | `docs/codex/decisions/` itself is not present |
| `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md` | No | would be the Luceon orchestration-side copy |

This means promotion can be cleanly introduced as new canonical docs, but only after reconciliation. Direct copy of the draft files is not safe.

## Architecture Fit

The source direction fits Luceon2026 in these ways:

- Mineru2Table consumes MinerU `content_list_v2.json`, which naturally belongs after the current MinerU parse stage and before downstream AI/metadata expansion.
- MinIO object references are the correct integration primitive. They avoid multipart re-upload, preserve durable asset truth, and align with Luceon's MinIO-centered artifact model.
- Luceon should remain orchestrator: it owns `materialId`, `parseTaskId`, `assetVersion`, scheduling, task state, admission circuit, audit, review semantics, and user decision rows.
- A `CleanServiceWorker` template with per-service configuration fits better than embedding Mineru2Table logic into `ParseTaskWorker`.
- Per-service admission circuits match current MinerU admission-circuit philosophy: `/health` alone must not be treated as enough for write-path readiness.
- Explicit failure/no silent fallback is compatible with both Luceon guardrails and the proposed CleanService protocol.
- The local single-machine reality requires conservative defaults: heavy-stage concurrency `<=1`, explicit service ownership, observable health, and no assumed HA.

The direction conflicts with or extends current truth in these ways:

- PRD v0.4 currently defines the Phase 1 mainline as upload -> local MinerU -> MinIO -> Ollama `qwen3.5:9b` -> AI metadata -> operator review. It does not yet define CleanService, RawMaterial/CleanMaterial, or Mineru2Table as an accepted product requirement.
- Current production uses `eduassets` / `eduassets-parsed`; the draft proposes `eduassets-raw` / `eduassets-clean`.
- Current validation/pressure evidence must remain separate. A future CleanService plan must not overwrite the existing pressure-test history, AI residual decisions, or release-readiness boundary.
- Current `PROJECT_STATE.md` / `HANDOFF.md` still contain some historical role/status material; canonical promotion should not rely on those stale sections without Director cleanup.

## Stale Or Unapproved Draft Issues

The draft documents need reconciliation before canonical promotion:

1. ADR still has `Open Questions`.
   - The conversation later records final user answers for Q-1 through Q-6.
   - Canonical ADR should replace `Open Questions` with `Decisions`.

2. Vision still hardcodes old-version retention as `N=3`.
   - User chose Q-3 option `(d)`: do not fix retention count in this phase.
   - Canonical Vision should say retention count is deferred to a later cleanup task while preserving provenance/layout support for future cleanup.

3. Contract missing `options.max_cost_cny` / `options.max_tokens_total`.
   - User chose Q-6 `(a)+(d)` with soft limit `¥5` and hard service limit `¥8`.
   - Canonical protocol should add these option fields and define cost-limit behavior.

4. Adaptation plan needs cost-policy alignment.
   - Current plan includes cost/token stats, but must explicitly align with `¥5` Luceon soft decision boundary and `¥8` service hard cutoff.
   - Error model should include cost hard-limit behavior, likely `quota_exceeded` with `retriable=false`.

5. Multipart deprecation needs explicit final boundary.
   - User chose Q-5 `(c)`: old Mineru2Table multipart routes are deprecated but retained for at least one version cycle.
   - Adaptation plan should mark old `POST /api/v1/extract` and `POST /api/v1/tasks` as deprecated with response/header markers and retention through at least `v1.2.0`.

6. Bucket migration wording must be new-assets-only.
   - User chose Q-1 `(b)`: legacy data stays legacy; new tasks use the new layout.
   - Canonical docs must not imply immediate migration or pseudo-provenance for existing data.

7. Contract mirroring must be explicit.
   - `CleanService-Protocol-v1.md` is intended to be byte-identical in Luceon2026 and Mineru2Table2026.
   - This creates a cross-repo synchronization obligation and should be handled by Director-dispatched docs tasks, not casual manual copy.

## Six User Decisions Reconciliation

| Decision | User answer from source conversation | Canonical absorption requirement |
| --- | --- | --- |
| Q-1 legacy data migration | `(b)` new tasks use new buckets; existing legacy data retained | Vision/ADR must introduce `eduassets-raw` and `eduassets-clean` only for new assets; old `eduassets` / `eduassets-parsed` remain legacy/read-only unless separately migrated |
| Q-2 assetVersion assignment | `(a)` Luceon assigns and passes `assetVersion` | Protocol must keep `asset_version` required; Luceon CleanServiceWorker owns version allocation and idempotency boundary |
| Q-3 old-version retention count | `(d)` not fixed in this phase | Vision must remove fixed `N=3`; retention policy deferred to later cleanup task |
| Q-4 automatic cleanup | `(b)` separate future task | ADR must not include cleanup worker in foundation implementation; audit may flag illegal/incomplete assets, not delete old versions |
| Q-5 old multipart routes | `(c)` deprecated but retained at least one version cycle | Mineru2Table adaptation must retain old routes with deprecation markers through at least one version cycle, suggested `v1.2.0` anchor |
| Q-6 LLM cost limit | `(a)+(d)`, hard threshold changed to `¥8` | Luceon soft limit `¥5` triggers Director/User decision; service hard limit `¥8` should be passed as `options.max_cost_cny`; add `options.max_tokens_total` |

## Proposed Canonical Document Set

After ProductManager/Director confirmation, promote a reconciled set, not the raw drafts:

| Path | Owner | Purpose | Required reconciliation before writing |
| --- | --- | --- | --- |
| `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md` | Architect | Long-term asset pipeline vision | New-assets-only layout; retention count deferred; no readiness claim |
| `docs/contracts/CleanService-Protocol-v1.md` | Architect | Shared CleanService API/data/provenance/error protocol | Add cost options; keep byte-identical mirror requirement; clarify MinIO credential boundary |
| `docs/codex/decisions/2026-05-15_clean-pipeline-foundation.md` | Architect + Director | ADR for Clean Pipeline foundation | Replace open questions with final decisions; record non-goals and phase boundary |
| `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md` | Architect | Luceon-side orchestration copy of Mineru2Table adaptation | Align old route deprecation, cost limits, from-storage/jobs contract, provenance outputs |
| `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md` or PRD section update | ProductManager | Product-scope confirmation and acceptance criteria | Required before architecture docs become accepted product truth |

## Does ProductManager Need A PRD Addendum First?

Yes. ProductManager should write a PRD addendum or scoped PRD update before these architecture/contract docs are accepted as canonical implementation direction.

Reason:

- CleanService/Mineru2Table changes product workflow, task states, operator review expectations, cost decision points, and asset lifecycle.
- PRD v0.4 does not currently authorize Mineru2Table as a pipeline stage.
- The six user decisions include product/operation choices, not just technical details.

Architect may draft reconciled docs next, but Director should not mark them as accepted product truth until ProductManager has recorded:

- user value and operator workflow;
- scope and non-goals;
- acceptance criteria;
- cost-decision behavior;
- legacy asset handling;
- release/validation boundary.

## External Dependency Boundary

Mineru2Table API changes should be treated as an external dependency task before Luceon implementation.

Recommended dependency path:

1. Mineru2Table implements `POST /api/v1/jobs`, `GET /api/v1/jobs/{job_id}`, MinIO read/write, idempotent job store, provenance, structured errors, webhook, cost hard limit, and deprecated old routes.
2. Luceon integrates only against the frozen `CleanService-Protocol-v1`.
3. Luceon implementation should not start with assumptions that the current Mineru2Table multipart API is sufficient.

Short-term exception: a DevelopmentEngineer may create a thin client/prototype against mocked protocol fixtures, but not a production path bound to the old multipart API.

## Suggested Phase Ordering

1. ProductManager PRD addendum.
   - Scope: product workflow, cost decision, legacy data policy, acceptance criteria.

2. Architect canonical docs reconciliation.
   - Scope: write the four reconciled docs under target paths; no code/runtime change.

3. Director/User review of canonical docs.
   - Scope: accept, return, or narrow the CleanService foundation.

4. DevelopmentEngineer external dependency task for Mineru2Table2026.
   - Scope: implement/verify CleanService Protocol v1 in that repository or prepare a cross-repo implementation task.

5. Architect implementation plan for Luceon CleanServiceWorker.
   - Scope: module boundaries, db schema extension, task state mapping, admission circuit, audit extension, rollout guardrails.

6. DevelopmentEngineer Luceon implementation.
   - Scope: CleanServiceWorker template, configuration, db schema, callback handler, audit, UI status surfaces as assigned.

7. TestAcceptanceEngineer validation plan and execution.
   - Scope: protocol-level mock tests first, then real Mineru2Table E2E, then controlled UAT; keep separate from existing pressure evidence and release-readiness track.

## Unresolved Questions

These should be resolved by Director/User or ProductManager before implementation:

1. Exact operator UX for cost soft-limit pause and User decision flow.
2. Whether `toc-rebuild` runs before all AI metadata or only before future chapter-level AI extraction.
3. Exact task-state names in Luceon UI/API for CleanService stages.
4. Whether new `materialId` hash model replaces current `mat-{timestamp}` only for new CleanService assets or becomes the global Material ID going forward.
5. Whether legacy assets remain visible in the same library views and how to label them.
6. Cross-repo process for keeping `CleanService-Protocol-v1.md` byte-identical.

## Recommended Next Tasks

1. ProductManager task: `CleanService/Mineru2Table PRD Addendum`.
   - Output: PRD addendum with workflow, value, acceptance criteria, cost decision path, and legacy data boundary.

2. Architect task: `Clean Pipeline Canonical Docs Reconciliation`.
   - Output: four reconciled docs at the proposed target paths, incorporating the six user decisions.

3. Architect task after docs acceptance: `Luceon CleanServiceWorker Implementation Plan`.
   - Output: module/API/data/runtime plan for DevelopmentEngineer.

4. DevelopmentEngineer task in Mineru2Table2026 or cross-repo track: `CleanService Protocol v1 External Dependency Implementation`.
   - Output: protocol-compatible Mineru2Table service evidence.

5. TestAcceptanceEngineer task: `CleanService Protocol And E2E Validation Plan`.
   - Output: validation matrix that does not conflate future CleanService E2E with current production pressure evidence.

## Final Judgment

The source bundle is valuable and directionally aligned with Luceon2026, but it is not yet canonical. The correct next step is ProductManager PRD addendum plus reconciled architecture/contract docs. Directly copying the draft files into canonical docs would preserve stale decisions and create future confusion.

