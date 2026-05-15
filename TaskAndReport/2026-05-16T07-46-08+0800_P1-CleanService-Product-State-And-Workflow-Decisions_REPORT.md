# ProductManager Report: P1 CleanService Product State And Workflow Decisions

- Task ID: `TASK-20260516-074608-P1-CleanService-Product-State-And-Workflow-Decisions`
- Assignee: `ProductManager`
- Based on Director task brief: `TaskAndReport/2026-05-16T07-46-08+0800_P1-CleanService-Product-State-And-Workflow-Decisions_TASK.md`
- Workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `main`
- HEAD before report changes: `b062f0c`
- Report date: 2026-05-16

## Scope Confirmation

I followed the Director task brief for Task 199.

This is a ProductManager decision report only. I did not implement code, edit production files, mutate runtime, Docker, DB, MinIO, MinerU, Ollama, models, secrets, configs, samples, or external repositories. I did not run submit-probe, upload, pressure, retry, reparse, re-AI, cleanup, repair, validation uploads, or production checks. I do not claim CleanService implementation acceptance, production readiness, release readiness, L3, pressure PASS, production上线, or go-live.

Files changed:

- `TaskAndReport/2026-05-16T07-46-08+0800_P1-CleanService-Product-State-And-Workflow-Decisions_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Evidence Consulted

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/product-manager.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- `docs/contracts/CleanService-Protocol-v1.md`
- `docs/codex/decisions/2026-05-15_clean-pipeline-foundation.md`
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`
- `TaskAndReport/2026-05-15T20-21-23+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_REPORT.md`
- `TaskAndReport/2026-05-16T07-46-08+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_DIRECTOR_REVIEW.md`

## Decision Table

| # | Question | ProductManager recommendation | Requires User/Director decision? |
| ---: | --- | --- | --- |
| 1 | Should `toc-rebuild` gate all AI metadata, or only future chapter-level AI/enrichment workflows? | Conservative default: `toc-rebuild` should not gate the existing PRD v0.4 AI metadata mainline. It should gate only future chapter-level / structure-dependent AI enrichment until real E2E evidence proves it is reliable enough to become a broader gate. Existing upload -> MinerU -> AI metadata -> review remains intact. | Director can accept this default for implementation. User decision is required before making `toc-rebuild` mandatory for all AI metadata. |
| 2 | Exact operator-facing labels for clean-stage states | Use product labels centered on directory/structure rebuild: `未启用`, `不适用`, `等待目录重建`, `目录重建中`, `目录结构待复核`, `目录结构已完成`, `部分完成待复核`, `成本待决策`, `目录重建已跳过`, `目录重建失败`. Technical service names may appear only in folded diagnostics. | Director can accept labels for first implementation; later UI wording can be refined after TestAcceptanceEngineer review. |
| 3 | `¥5` soft-limit pause in task detail, task list, and task ledger | Task list shows a visible badge `成本待决策`. Task detail shows projected/actual cost, token total, soft `¥5`, hard `¥8`, and decision reason. Task ledger should become a Director/User decision row only when continuation requires owner judgment; the product state should not auto-continue. | Director can encode workflow. User decision is required when a real task exceeds the soft limit and continuation is desired. |
| 4 | Future hash-based `materialId`: global or scoped? | Scope hash-based identity to new CleanService-enabled assets only at first. Do not globally replace current `mat-{timestamp}` behavior in the first implementation. Store source hash/fingerprint as metadata for traceability. | User/Director decision required before global material identity migration. |
| 5 | Legacy asset labels in library/task views | Label existing assets as `历史解析资产` or `Legacy parse-only`. This is an informational lifecycle label, not a warning or failure. Legacy assets remain visible in the same library unless a later product task changes filtering/grouping. | Director can accept. User decision required before any migration, cleanup, hiding, or separate legacy library split. |
| 6 | Partial output with unresolved anchors | Keep the current top-level task state model stable. Map partial clean output to existing task-level `review-pending` when operator action is needed, with a clean-specific substatus such as `cleanReview=partial-unresolved-anchors`. UI label: `部分完成待复核`. Do not introduce a new top-level task state in the first foundation unless Architect/DevelopmentEngineer proves the state-machine change is necessary. | Director can accept for first implementation. User decision required only if partial output should be treated as acceptable completion by default. |
| 7 | Cross-repo byte-identical protocol sync ownership | Use Director-owned paired task briefs as the first governance mechanism: one task in Luceon, one task in Mineru2Table2026, with byte-identical diff verification in the reports. A future GitHub workflow can be added later, but should not block the first protocol adoption. Do not rely on ad hoc manual copy without task records. | Director can own paired dispatch. User decision may be needed if a persistent cross-repo automation/workflow is introduced. |
| 8 | Which decisions can PM recommend now? | ProductManager recommends the conservative defaults above. User-owned decisions remain: mandatory all-AI gating, global material ID migration, automatic cleanup/migration, treating partial clean output as completed, release/go-live, and any cross-repo automation with operational risk. | Director review required for this report. User decision required only for the listed owner-level expansions. |

## Recommended Default Path For DevelopmentEngineer Implementation

If Director accepts these product defaults, the safest DevelopmentEngineer path is:

1. Implement a disabled-by-default mock CleanService foundation.
2. Do not change the existing upload -> MinerU -> AI metadata -> operator review mainline.
3. Add bounded task/material metadata for clean-stage summaries without large DB artifacts.
4. Add product-facing label mapping for the clean stage, initially hidden or diagnostics-only unless feature-gated on.
5. Support mock states for pending, running, completed, partial-review, failed, skipped, and cost-decision.
6. Preserve explicit no-silent-fallback semantics.
7. Do not dispatch to real Mineru2Table until protocol evidence is accepted in a separate dependency task.
8. Do not migrate legacy assets, change global material IDs, or perform cleanup.

The first implementation should prove the Luceon orchestration contract without changing production behavior or claiming runtime acceptance.

## Product Acceptance Criteria For First Mock/Disabled Foundation

Director can consider the first mock/disabled CleanService foundation product-acceptable only if:

1. The feature is disabled by default and does not alter current Phase 1 task outcomes.
2. Existing AI metadata flow still works without waiting for `toc-rebuild`.
3. Clean-stage labels are understandable to an operator and avoid raw service jargon in primary UI.
4. Partial/unresolved-anchor output is visible as `部分完成待复核`, not disguised as success.
5. `¥5` soft-limit and `¥8` hard-limit states are representable in task summary and diagnostics.
6. Legacy assets show an informational legacy label and are not migrated or backfilled.
7. Mock protocol coverage includes success, partial, cost-decision, hard-limit failure, timeout, and protocol failure.
8. Reports clearly distinguish mock foundation from real Mineru2Table E2E.
9. No-silent-fallback is preserved: raw MinerU output or placeholder/skeleton output cannot be labeled as clean success.

## Risks And Product Tradeoffs

- Not gating all AI metadata preserves the current working mainline, but means initial AI metadata may not benefit from future clean structure.
- Scoping hash material IDs to new CleanService assets avoids a disruptive migration, but creates a temporary mixed identity model.
- Keeping partial output under top-level `review-pending` avoids state-machine churn, but requires clean substatus/diagnostics to be precise.
- Pausing on `¥5` soft-limit protects cost governance, but adds a possible operator/Director decision interruption.
- Director-owned paired protocol sync is slower than automation, but is more traceable and safer for the first cross-repo protocol adoption.

## User/Director Decisions Still Required

Director can accept the recommended defaults and proceed to a scoped implementation task.

Explicit User decision is still required before:

- making `toc-rebuild` mandatory for all AI metadata;
- globally replacing current material IDs with hash-based IDs;
- migrating, hiding, deleting, or auto-cleaning legacy assets;
- treating partial/unresolved-anchor clean output as completed by default;
- enabling real Mineru2Table production dispatch;
- claiming release readiness, production readiness, L3, pressure PASS, production上线, or go-live.

## Commands Run

| Command | Purpose | Exit |
| --- | --- | ---: |
| `git status --short --branch` | Required repository state check | 0 |
| `sed -n '1,260p' TaskAndReport/TASK_TRACKING_LIST.md` | Read task ledger | 0 |
| `sed -n ...` on required task, role, PRD, codex, architecture, contract, ADR, adaptation, report, and review files | Required reading | 0 |
| `git rev-parse --abbrev-ref HEAD` | Record branch | 0 |
| `git rev-parse --short HEAD` | Record HEAD | 0 |
| `rg -n "\\| ProductManager \\|" TaskAndReport/TASK_TRACKING_LIST.md` | Locate ProductManager task row | 0 |

## Skipped Checks

- TypeScript, build, smoke, UAT, runtime, production, upload, pressure, submit-probe, retry, reparse, re-AI, and browser checks were skipped because this is a product-decision report with no code or runtime change.
- No production workspace command was run.
- No external Mineru2Table2026 repository command was run.
- No GitHub fetch or pull was run because the ProductManager task did not require it and local ledger state was coherent.

## GitHub Sync Status

Repository files were changed, and the task brief requires commit and push to GitHub `main`. ProductManager should commit and push only the report and task-ledger update after local diff validation.

## Director Review

Director review is required. Recommended next actor: `Director`.

Recommended Director action: review the product defaults. If accepted, dispatch a DevelopmentEngineer task for disabled-by-default mock CleanService foundation using these defaults, or dispatch Architect for a narrow state/label contract amendment if Director wants one more design pass before implementation.
