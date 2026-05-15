# Director Review: P1 CleanServiceWorker Luceon Implementation Plan

- Task ID: `TASK-20260515-202123-P1-CleanServiceWorker-Luceon-Implementation-Plan`
- Reviewed at: `2026-05-16T07:46:08+0800`
- Reviewed by: `Director`
- Report reviewed: `TaskAndReport/2026-05-15T20-21-23+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_REPORT.md`
- Report commit reviewed: `425ce65`
- Result: `ACCEPTED_ARCHITECTURE_PLAN_PRODUCT_DECISIONS_REQUIRED`

## Judgment

Accepted.

The Architect report is a useful implementation plan and stays inside the correct boundary: planning only, no code, no runtime/production mutation, and no readiness claim.

The strongest part of the plan is that it does not bolt CleanService directly onto `ParseTaskWorker` or `AiMetadataWorker`. It proposes a separate CleanService orchestration layer with client/config/circuit/output-verifier/callback/worker modules, bounded DB summaries, Luceon-owned asset versions, MinIO ObjectRefs, explicit provenance validation, and no silent fallback.

Director accepts the proposed sequencing principle:

1. product/state decisions first;
2. external Mineru2Table protocol evidence before real dispatch;
3. Luceon mock protocol foundation while disabled by default;
4. CleanServiceWorker disabled integration;
5. UI read surfaces;
6. only then controlled real E2E and production-boundary decisions.

## Accepted Planning Points

- Current Phase 1 runtime remains upload -> local MinerU -> MinIO -> Ollama `qwen3.5:9b` -> AI metadata -> operator review.
- CleanService / Mineru2Table remains future architecture direction, not current runtime capability.
- Luceon should own task/material/version/review/cost semantics.
- CleanService should use MinIO ObjectRefs and bounded DB summaries, not large DB artifacts.
- Existing assets remain legacy; no automatic migration, cleanup, or pseudo-provenance is authorized.
- `¥5` Luceon soft limit and `¥8` service hard limit remain product/runtime constraints.
- Real Mineru2Table integration must wait for protocol evidence: health, ObjectRef jobs, persistent job state, idempotency, MinIO outputs, provenance, webhook/polling, and cost-limit behavior.

## Remaining Decisions

The report correctly leaves product-level decisions unresolved. These should not be guessed by DevelopmentEngineer:

- whether `toc-rebuild` gates all AI metadata or only later chapter-level AI/enrichment workflows;
- exact operator-facing clean-stage labels;
- how `¥5` soft-limit pause appears in task detail and task ledger;
- whether future hash-based `materialId` is global or scoped to new CleanService-enabled assets;
- how legacy assets are labeled;
- how partial output / unresolved anchors map to review states;
- who owns cross-repo byte-identical protocol sync.

## Director Decision

Task 189 is accepted and closed.

Director issued Task 199 to ProductManager for product/state decision clarification before any Luceon implementation task is dispatched.

This review does not authorize CleanServiceWorker implementation, Mineru2Table external repo changes, runtime/production changes, upload/pressure validation, submit-probe, DB/MinIO/Docker mutation, release readiness, L3, pressure PASS, production readiness, production上线, or go-live.
