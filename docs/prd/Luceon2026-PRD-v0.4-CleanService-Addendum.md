# Luceon2026 PRD v0.4 CleanService Addendum

- Document status: historical ProductManager draft preserved after 6.9.1 team retirement
- Task: `TASK-20260515-192928-P1-CleanService-Mineru2Table-PRD-Addendum`
- Date: 2026-05-15
- Scope: product requirement addendum for future Mineru2Table `toc-rebuild` CleanService

## 1. Purpose

This addendum records the product-scoped requirement for introducing Mineru2Table as a future `toc-rebuild` CleanService in Luceon2026.

It does not replace PRD v0.4. PRD v0.4 remains the current Phase 1 product contract: upload -> local MinerU -> MinIO -> Ollama `qwen3.5:9b` -> AI metadata -> operator review. This addendum defines the product boundary and acceptance expectations that must be satisfied before any architecture or implementation plan promotes CleanService/Mineru2Table into canonical project direction.

This addendum does not declare current CleanService implementation readiness, production readiness, L3 acceptance, pressure PASS, release readiness, production上线, or go-live.

## 2. Product Value

MinerU currently gives Luceon durable parsed artifacts, but educational assets often still need a cleaner table-of-contents and chapter/section structure before downstream use. Mineru2Table `toc-rebuild` matters because it can turn raw parse artifacts into cleaner learning-asset structure that is easier for operators to review and more useful for later educational workflows.

The expected product value is:

- Better downstream asset quality: rebuilt TOC and anchor structure should reduce manual interpretation work after parsing.
- Better operator confidence: operators can see which clean outputs were produced and which anchors remain unresolved.
- Better future AI quality: chapter-aware and section-aware metadata or exercise extraction should be grounded in cleaner structure rather than raw OCR layout alone.
- Better lifecycle governance: clean outputs become a distinct asset stage instead of being mixed into raw MinerU parse output or AI metadata.

## 3. Relationship To PRD v0.4 Mainline

CleanService is a future pipeline extension after the existing MinerU parse stage. It must not invalidate the current PRD v0.4 mainline or erase current pressure-test, AI-residual, runtime-recovery, or release-boundary evidence.

The intended future product sequence is:

1. Operator uploads a PDF or supported document.
2. Luceon performs the current raw intake and MinerU parse flow.
3. Luceon submits eligible parsed artifacts to a `toc-rebuild` CleanService backed by Mineru2Table.
4. Mineru2Table produces clean TOC/table/anchor outputs through a protocol agreed by Architect and Director.
5. Luceon stores clean outputs as a separate asset stage and exposes them for operator review.
6. Downstream AI metadata or future chapter-level workflows may consume the clean outputs only after the clean stage is accepted or explicitly marked as partial.

This addendum does not decide whether `toc-rebuild` must run before all AI metadata or only before future chapter-level AI extraction. That remains an explicit product/architecture decision before implementation.

## 4. Operator Workflow Impact

The operator-facing workflow should remain task-centered:

- The operator uploads and tracks tasks from the existing task workbench.
- When a task is eligible for CleanService processing, the task detail should show a clean-output stage in product language, such as TOC rebuild / clean structure, rather than raw internal job names alone.
- The operator should see whether the clean stage is pending, running, review-needed, completed, failed, or skipped by policy.
- The operator should be able to inspect clean outputs and unresolved anchors before accepting downstream usage.
- If cost or token limits require owner judgment, the task should pause with a clear decision state instead of silently continuing or failing without context.

The UI must avoid implying that clean output is authoritative when unresolved anchors, partial mapping, or cost-limited output remains.

## 5. Scope

In scope for a future CleanService/Mineru2Table integration:

- Treat Mineru2Table as a future `toc-rebuild` CleanService after MinerU parsing.
- Use durable MinIO object references as the product-level handoff model, not user-facing re-upload.
- Preserve Luceon as the orchestrator for material, version, task, cost decision, review, audit, and acceptance semantics.
- Store raw parse artifacts and clean outputs as separate lifecycle stages.
- Show clean outputs and unresolved anchors to the operator.
- Preserve explicit failure semantics and no-silent-fallback behavior.
- Support cost-aware pausing when Luceon's soft limit is exceeded.
- Keep legacy assets visible but clearly distinct from new CleanService-produced assets.

## 6. Non-Goals

This addendum does not authorize:

- CleanServiceWorker implementation.
- Mineru2Table API implementation.
- Architecture, protocol, ADR, contract, source, runtime, Docker, DB, MinIO, MinerU, Ollama, production, or role-contract edits.
- Raw zip copying into this repository.
- Migration of existing production assets.
- Automatic cleanup of old versions.
- Release readiness, production readiness, L3 acceptance, pressure PASS, production上线, or go-live claims.
- Use of skeleton fallback or silent fallback as a substitute for real clean output.

## 7. Confirmed User Decisions To Preserve

The following user decisions must be reflected in future canonical architecture/contract work:

| Decision area | Product requirement |
| --- | --- |
| Legacy data migration | Existing data remains legacy. New tasks use the new layout only after implementation. No immediate migration is implied. |
| Asset version assignment | Luceon assigns and passes `assetVersion`; Mineru2Table must not own Luceon's asset lifecycle authority. |
| Old-version retention count | No fixed retention count is set in this phase. Retention policy is deferred to a future cleanup decision. |
| Automatic cleanup | Cleanup is a separate future task. Foundation work may flag issues but must not delete or mutate old assets. |
| Old multipart routes | Mineru2Table's old multipart routes may be deprecated but retained for at least one version cycle; Luceon should not bind a production path to those routes as the long-term contract. |
| LLM cost limit | Luceon soft limit is `¥5`; service hard limit is `¥8`. Exceeding the soft limit requires explicit user or future-governance decision behavior; exceeding the hard limit must stop the service path explicitly. |

## 8. Legacy Asset Policy

Existing `eduassets` / `eduassets-parsed` data remains legacy unless a separate migration task is authorized. Legacy assets should remain visible to operators according to existing library behavior, but they must not be backfilled into the new CleanService layout by implication.

After CleanService implementation, new eligible tasks may use a new raw/clean layout such as `eduassets-raw` and `eduassets-clean` only when the architecture contract is accepted. Product wording should make clear whether a material is:

- legacy parse-only;
- new raw parse with no clean stage;
- clean-stage pending/running;
- clean-stage review-needed;
- clean-stage completed;
- clean-stage failed or skipped.

No pseudo-provenance should be invented for legacy assets.

## 9. Cost Policy

CleanService/Mineru2Table must be cost-aware at the product workflow level.

- Luceon soft limit: `¥5`.
- Service hard limit: `¥8`.
- Soft-limit behavior: when projected or actual cost crosses `¥5`, Luceon should pause the clean-stage decision path and require explicit user or future-governance decision before continuing, unless a later approved policy defines a narrower automatic behavior.
- Hard-limit behavior: when projected or actual cost crosses `¥8`, the service must fail or reject the job explicitly with a non-retriable cost-limit state.
- Operators must not see a silent fallback, partial disguised as success, or hidden cost overrun.
- Future contracts should carry enough cost/token metadata for audit, review, and decision records.

## 10. Failure Semantics And No Silent Fallback

CleanService failures must fail explicitly. The system must not:

- represent raw MinerU output as successful clean output when `toc-rebuild` failed;
- silently skip unresolved anchors and mark the clean stage as completed;
- treat skeleton or placeholder structure as real Mineru2Table output;
- hide service hard-limit or protocol failures behind review-pending success wording.

Allowed non-terminal or partial states may exist, but they must be explicit in API, task events, and UI copy. Operator review must be able to distinguish complete clean output from partial output with unresolved anchors.

## 11. UI And Review Expectations

The task detail should eventually expose:

- clean-stage status and latest update time;
- clean output entry point;
- unresolved anchor count and representative unresolved anchors;
- provenance/source reference for clean output;
- cost/token summary when applicable;
- next operator action, such as review clean output, approve downstream use, request rerun, or escalate cost decision.

The task list should not become overloaded with technical service names. It should surface task-health semantics in operator language while preserving detailed diagnostics in folded/internal sections.

## 12. Acceptance Criteria For Future Integration

A future CleanService/Mineru2Table integration can be product-accepted only when Director has reviewed evidence for all of the following:

1. Product flow: operator can understand the clean-stage state and next action from the task list/detail.
2. Legacy boundary: existing assets remain legacy and are not silently migrated.
3. Version boundary: Luceon owns `assetVersion` assignment and can trace clean output to raw parse inputs.
4. Output boundary: clean outputs and unresolved anchors are visible and reviewable.
5. Failure boundary: protocol, service, cost, unresolved-anchor, and timeout failures are explicit.
6. Cost boundary: `¥5` soft-limit and `¥8` hard-limit behavior is observable and recorded.
7. No-silent-fallback boundary: placeholder or raw parse data is never presented as successful clean output.
8. Validation boundary: mock protocol tests, real Mineru2Table E2E, and operator review are all separately evidenced.
9. Release boundary: CleanService evidence is not conflated with current production pressure evidence or current release-readiness claims.

## 13. Validation Boundary

Validation must proceed in layers:

1. Mock protocol validation: Luceon can handle accepted, partial, failed, timeout, and cost-limit CleanService responses without production mutation.
2. Real Mineru2Table E2E: Mineru2Table accepts MinIO-backed job references, returns clean outputs, provenance, unresolved anchors, and structured errors.
3. Operator review validation: the operator can inspect clean output and unresolved anchors and can make a review decision without reading logs.

Passing a mock protocol test is not real Mineru2Table acceptance. Passing one real E2E is not pressure PASS, L3, or release readiness. Release-boundary decisions remain separate.

## 14. Pending Product Questions

These questions should be resolved before implementation planning:

1. Does `toc-rebuild` run before all AI metadata, or only before future chapter-level extraction and educational-asset enrichment?
2. What exact operator-facing state labels should be used for CleanService stages?
3. How should cost soft-limit decisions appear in task detail and task ledger?
4. Should new CleanService material identity remain compatible with current `mat-{timestamp}` IDs, or introduce a future hash/version identity only for new assets?
5. How should legacy assets be labeled in library views so operators understand why they do not have clean-stage outputs?
6. What process keeps shared protocol documentation aligned across Luceon2026 and Mineru2Table2026?

## 15. Recommended Next Step

Future CleanService work should start with a newly approved governance/process decision, then reconcile architecture and contracts from the accepted product boundary and the six preserved user decisions, not by copying the raw source bundle.
