# Task: P1 CleanService Mineru2Table Docs Absorption

- Task ID: `TASK-20260515-192113-P1-CleanService-Mineru2Table-Docs-Absorption`
- Assignee: `Architect`
- Issued by: `Director`
- Issued at: 2026-05-15T19:21:13+0800
- Priority: P1
- Project: Luceon2026
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- GitHub: `https://github.com/shcming2023/Luceon2026`
- Task brief: `TaskAndReport/2026-05-15T19-21-13+0800_P1-CleanService-Mineru2Table-Docs-Absorption_TASK.md`
- Expected report: `TaskAndReport/2026-05-15T19-21-13+0800_P1-CleanService-Mineru2Table-Docs-Absorption_REPORT.md`

## Required Reading

Before execution, read:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/architect.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Source Bundle

Read this user-provided zip bundle, if still available on the local machine:

`/Users/concm/Library/Containers/com.tencent.WeWorkMac/Data/Documents/Profiles/9F6D6C5415707EC04A6FE091F21E329F/Caches/Files/2026-05/23189c0bfaea54aefaf7bcfd57a308b3/fri_may_15_2026_overview_of_luceon_2026_and_mineru_2.zip`

Known members from Director's first read:

- `fri_may_15_2026_overview_of_luceon_2026_and_mineru_2.md`
- `v1_docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- `v1_docs/contracts/CleanService-Protocol-v1.md`
- `v1_docs/codex/decisions/2026-05-15_clean-pipeline-foundation.md`
- `v1_Docs/CleanService-Adaptation-Plan.md`

If the zip cache path is no longer available, stop and write a blocked report. Do not reconstruct the source from memory.

## Background

User supplied a Copilot conversation export and draft documents about integrating `Mineru2Table2026` into Luceon2026 as the first `CleanService` for `toc-rebuild`.

Director's initial read found the proposed direction valuable but not yet canonical:

- Mineru2Table should read MinerU `content_list_v2.json` from MinIO by object reference rather than multipart upload.
- Mineru2Table should write `flooded_content.json`, `logic_tree.json`, `readable_tree.md`, `skeleton.json`, and `provenance.json` back to MinIO.
- Luceon should remain the orchestrator and own `materialId`, `parseTaskId`, `assetVersion`, scheduling, task state, admission circuit, audit, and review semantics.
- The draft documents still contain stale or unresolved sections and must not be copied directly into canonical docs without reconciliation.

Known user decisions from the source conversation that must be folded into any proposed final version:

- Q-1: existing legacy data should be retained as legacy; new tasks use the new layout.
- Q-2: `assetVersion` is assigned by Luceon.
- Q-3: old-version retention count is not fixed in this phase; defer to a later cleanup task.
- Q-4: automatic cleanup is not implemented in this ADR phase; handle as a separate future task.
- Q-5: old Mineru2Table multipart routes are deprecated but retained at least one version cycle.
- Q-6: Luceon soft cost limit is `¥5`; service hard cost limit is `¥8`.

## Objective

Produce a decision-ready architecture absorption report for the CleanService/Mineru2Table material.

This task is for architectural/document absorption only. It must not implement code, deploy, mutate production, or directly promote the draft source documents into canonical docs.

## Scope

You must:

1. Read the source bundle and inventory its contents.
2. Compare the source material with current Luceon repository truth and PRD v0.4.
3. Identify which parts are already consistent with current Luceon architecture and which parts conflict, are stale, or remain unapproved.
4. Reconcile the known six user decisions listed above with the draft docs.
5. Propose a clean document absorption plan with exact target paths, likely including:
   - `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
   - `docs/contracts/CleanService-Protocol-v1.md`
   - `docs/codex/decisions/2026-05-15_clean-pipeline-foundation.md`
   - `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`
6. Identify whether ProductManager must first write a PRD addendum before these architecture/contract docs are promoted.
7. Identify the next role task(s) needed after Director review.

## Non-Goals

Do not:

- add or edit canonical docs under `docs/architecture`, `docs/contracts`, `docs/codex/decisions`, or `docs/prd`;
- copy the zip bundle or its raw contents into the repository;
- implement CleanServiceWorker, Mineru2Table integration, MinIO bucket migration, provenance generation, webhook, or cost controls;
- change PRD truth, `PROJECT_STATE`, `HANDOFF`, role contracts, source code, Docker files, production files, DB, MinIO, MinerU, Ollama, or runtime configuration;
- perform upload, pressure testing, submit-probe, cleanup, restart, rebuild, redeploy, retry, reparse, or re-AI;
- declare CleanService architecture accepted, release readiness, production readiness, L3, pressure PASS, production上线, or go-live.

## Required Analysis Points

Your report must explicitly cover:

- source bundle file list and whether all files were readable;
- current repo gaps: whether the proposed target docs already exist in Luceon2026;
- exact stale draft issues, including at minimum:
  - ADR still using `Open Questions` instead of finalized `Decisions`;
  - Vision still using a fixed `N=3` old-version retention rule;
  - Contract missing `options.max_cost_cny` / `options.max_tokens_total`;
  - Adaptation plan needing alignment with `¥5` soft / `¥8` hard cost policy and multipart deprecation;
- architectural fit with current Luceon constraints:
  - strict explicit failure / no silent fallback;
  - MinIO as durable asset truth;
  - Director-dispatched task workflow;
  - local single-machine MinerU/Ollama/MinIO realities;
  - current pressure-test evidence is separate and must not be overwritten by future architecture plans;
- whether the proposed `eduassets-raw` / `eduassets-clean` layout is compatible with current production state or should be introduced only for new assets;
- whether Mineru2Table API changes should be treated as an external dependency task before Luceon implementation;
- suggested phase ordering and role assignment.

## Required Output

Write:

`TaskAndReport/2026-05-15T19-21-13+0800_P1-CleanService-Mineru2Table-Docs-Absorption_REPORT.md`

The report must include:

- confirmation that it was based on this Director task brief;
- branch and HEAD;
- commands run and exit codes;
- source files read;
- summarized findings;
- proposed canonical document set and target paths;
- reconciliation table for the six known user decisions;
- unresolved questions, if any;
- recommended next task(s), with role and scope;
- explicit statement that no canonical docs/source/runtime/production files were changed except the report and task ledger.

## Task Ledger Update

After writing the report, update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查`
- Next Actor: `Director`
- Next Action: Director reviews architecture absorption report and decides whether to dispatch ProductManager PRD addendum, canonical docs drafting, or implementation planning.
- Required Output: Director review.

Commit and push the report and task-ledger update to GitHub `main`.

## Acceptance Criteria

Director can accept this task only if:

- the source bundle was actually read from the local path;
- the report distinguishes draft source material from current project truth;
- stale/unfinalized draft sections are called out;
- the six known user decisions are incorporated into the proposed absorption plan;
- no implementation or production mutation was performed;
- the recommended next step is precise enough for Director to dispatch without re-reading the entire zip.
