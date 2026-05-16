# Director Review: P1 CleanService Product State And Workflow Decisions

- Task ID: `TASK-20260516-074608-P1-CleanService-Product-State-And-Workflow-Decisions`
- Reviewed at: `2026-05-16T08:02:16+0800`
- Reviewed by: `Director`
- Report reviewed: `TaskAndReport/2026-05-16T07-46-08+0800_P1-CleanService-Product-State-And-Workflow-Decisions_REPORT.md`
- Report commit reviewed: `62b9b3a`
- Result: `ACCEPTED_PRODUCT_DECISIONS_MOCK_FOUNDATION_IMPLEMENTATION_READY`

## Judgment

Accepted.

The ProductManager report answers the product/state questions that should not be guessed by DevelopmentEngineer. Director accepts the conservative defaults for the first Luceon-side CleanService foundation:

- `toc-rebuild` must not gate the current PRD v0.4 AI metadata mainline.
- `toc-rebuild` may gate only future chapter-level or structure-dependent enrichment until real E2E evidence supports broader gating.
- Clean-stage operator labels should use directory/structure rebuild language, not raw service jargon.
- `¥5` remains the soft decision threshold; `¥8` remains the hard stop.
- Hash-based identity is scoped to new CleanService-enabled assets first, not global material ID migration.
- Existing assets remain visible as `历史解析资产` / `Legacy parse-only`; no migration, hiding, cleanup, or pseudo-provenance is authorized.
- Partial clean output with unresolved anchors maps to existing `review-pending` plus clean-specific substatus, not a new top-level task state in the first foundation.
- Cross-repo protocol sync should start with Director-owned paired task briefs and byte-identical verification before any workflow automation is introduced.

## Accepted Boundaries

This acceptance is product-decision acceptance only. It does not accept or imply a real CleanService runtime, real Mineru2Table integration, production deployment, pressure PASS, L3, production readiness, release readiness, production上线, or go-live.

Real Mineru2Table dispatch remains blocked until protocol evidence is accepted for health, ObjectRef jobs, persistent job state, idempotency, MinIO outputs, provenance, webhook/polling behavior, and cost-limit behavior.

## Director Decision

Task 199 is accepted and closed.

Director issued Task 200 to DevelopmentEngineer for a disabled-by-default Luceon-side CleanService mock/protocol foundation. The next implementation must prove local orchestration contracts and product state mapping without changing the current Phase 1 runtime.

The next task must not mutate production, upload files, run pressure validation, run submit-probe, dispatch to real Mineru2Table, migrate legacy assets, replace global material IDs, weaken no-silent-fallback behavior, or claim readiness.

