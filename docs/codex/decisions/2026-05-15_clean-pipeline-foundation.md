# ADR-2026-05-15: Clean Pipeline Foundation

Status: Proposed for Director review  
Date: 2026-05-15  
Owner: Architect  
Related:

- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- `docs/contracts/CleanService-Protocol-v1.md`
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`

## 1. Context

Luceon2026 currently operates under PRD v0.4's Phase 1 mainline:

```text
upload -> local MinerU -> MinIO -> Ollama qwen3.5:9b -> AI metadata -> operator review
```

The user supplied source material proposing Mineru2Table2026 as the first CleanService for `toc-rebuild`. ProductManager has accepted a PRD addendum that scopes Mineru2Table as future product direction while preserving current PRD v0.4 boundaries.

This ADR records architecture decisions for future planning. It does not authorize implementation, runtime mutation, production mutation, migration, cleanup, release readiness, L3, pressure PASS, production readiness, or go-live.

## 2. Decisions

### D-1. CleanService is a future pipeline extension

Mineru2Table may be introduced as a future `toc-rebuild` CleanService after MinerU parsing. It is not a current implemented stage.

### D-2. Luceon remains orchestrator

Luceon owns:

- `materialId`;
- `parseTaskId`;
- `assetVersion`;
- CleanService `job_id`;
- scheduling and retries;
- admission circuits;
- task state and task events;
- operator review;
- cost decision pauses;
- audit and acceptance semantics.

CleanServices process assets, but they do not own Luceon's lifecycle authority.

### D-3. New layout applies only to new assets after implementation

Future CleanService-enabled assets may use:

- `eduassets-raw`
- `eduassets-clean`

Existing `eduassets` / `eduassets-parsed` data remains legacy. No immediate migration is implied, and no pseudo-provenance should be created for old data.

### D-4. Luceon assigns `assetVersion`

`assetVersion` is assigned by Luceon and passed to the CleanService in the job request. Services must not allocate Luceon asset versions themselves.

### D-5. Retention count is not fixed in this phase

No fixed old-version retention count is set. The layout and provenance must preserve future cleanup capability, but a later Director task must define any retention count, archive behavior, deletion behavior, and approval boundary.

### D-6. Automatic cleanup is a future task

This foundation does not implement automatic cleanup. Future audit may flag invalid or incomplete assets, but cleanup or deletion requires separate task authorization.

### D-7. Multipart routes are deprecated, not immediately removed

Mineru2Table's existing multipart routes may be deprecated but retained for at least one version cycle. Luceon's canonical integration should target MinIO ObjectRef jobs, not multipart upload.

### D-8. Cost limits are two-layered

- Luceon soft limit: `¥5`.
- Service hard limit: `¥8`.

Crossing Luceon's soft limit requires an explicit Director/User decision path. Crossing the service hard limit must stop explicitly with non-retriable cost-limit failure.

### D-9. Shared protocol must be mirrored byte-identically

`docs/contracts/CleanService-Protocol-v1.md` must be mirrored byte-identically in Mineru2Table2026 once accepted and copied there by an authorized cross-repo task.

## 3. Consequences

Positive:

- clean outputs become durable assets with provenance;
- Mineru2Table integration is separated from current Phase 1 pressure evidence;
- Luceon preserves orchestration and review authority;
- external services can evolve independently behind a stable protocol;
- failure/cost/partial-output semantics become explicit.

Costs:

- Luceon needs new worker, schema, audit, UI, and task-state planning before implementation;
- Mineru2Table must implement an external dependency contract before Luceon production integration;
- cross-repo protocol synchronization becomes a real governance task;
- legacy and new layouts will coexist.

## 4. Rejected Alternatives

| Alternative | Rejection reason |
| --- | --- |
| Immediate migration of all legacy assets | risks pseudo-provenance and unnecessary mutation |
| Service-owned `assetVersion` | breaks Luceon orchestration and cross-service lifecycle consistency |
| Fixed `N=3` retention now | premature; cleanup policy is not yet accepted |
| Automatic cleanup in foundation | deletion needs separate design and explicit authorization |
| Binding Luceon to old multipart Mineru2Table routes | contradicts durable MinIO asset handoff and large-file design |
| Representing raw/skeleton output as clean success | violates no-silent-fallback guardrail |

## 5. Implementation Phases

Recommended future phases:

1. Director review of canonical docs.
2. Architect implementation plan for Luceon CleanServiceWorker.
3. DevelopmentEngineer task for Mineru2Table protocol compatibility or cross-repo dependency preparation.
4. DevelopmentEngineer task for Luceon-side CleanService integration after dependency contract is available.
5. TestAcceptanceEngineer protocol and E2E validation.
6. Separate Director/User decision for any migration, cleanup, release boundary, or production rollout.

## 6. Open Architecture Questions

These remain unresolved and should be handled in later tasks:

1. Whether `toc-rebuild` gates all AI metadata or only future chapter-level workflows.
2. Exact operator-facing state labels for CleanService stages.
3. Whether future hash-based `materialId` becomes global or applies only to new clean assets.
4. How legacy assets are labeled in library views.
5. Cross-repo process for byte-identical protocol synchronization.
6. Exact callback endpoint and task-state mapping in Luceon.

## 7. Non-Authorization

This ADR does not authorize:

- source code changes;
- runtime, Docker, DB, MinIO, MinerU, Ollama, production, or secret/config changes;
- validation uploads, pressure tests, submit probes, retries, reparses, or re-AI;
- data migration or cleanup;
- readiness, L3, pressure PASS, production readiness, release readiness, or go-live claims.

