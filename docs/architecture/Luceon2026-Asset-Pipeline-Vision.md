# Luceon2026 Asset Pipeline Vision

Status: Canonical architecture direction for future planning  
Last updated: 2026-05-15  
Owner: Architect  
Related PRD: `docs/prd/Luceon2026-PRD-v0.4.md`, `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`

## 1. Boundary

This document defines the future asset-pipeline direction for introducing CleanService stages such as Mineru2Table `toc-rebuild`.

It does not replace the current PRD v0.4 mainline:

```text
upload -> local MinerU -> MinIO -> Ollama qwen3.5:9b -> AI metadata -> operator review
```

It does not claim CleanService implementation acceptance, production readiness, L3, pressure PASS, release readiness, production go-live, or any current runtime capability.

## 2. Vision

Luceon2026 should evolve from a parse-and-review CMS into a durable educational asset pipeline. In that pipeline, each stage creates assets that can be inspected, versioned, reviewed, and traced.

The first future CleanService is expected to be Mineru2Table as `toc-rebuild`: it consumes MinerU `content_list_v2.json` and produces rebuilt table-of-contents / logical structure assets for operator review and downstream educational workflows.

## 3. Principles

1. Asset first: each important stage output is a durable MinIO asset, not an invisible temporary file.
2. Luceon orchestrates: Luceon owns material identity, task identity, asset version assignment, scheduling, review, audit, admission circuits, cost decisions, and acceptance semantics.
3. Services are isolated: each CleanService is an external service with its own repository, version, health, job state, and failure domain.
4. Provenance is mandatory for new CleanService assets: future clean outputs must include enough provenance to explain inputs, service version, options, cost, and output object hashes.
5. Failure is explicit: raw MinerU output, skeleton output, placeholder output, or partial unresolved anchors must never be presented as successful clean output.
6. Current evidence remains separate: future CleanService validation must not overwrite existing pressure-test, AI residual, recovery, or release-boundary evidence.

## 4. Asset Layers

Future new assets may use these layers after implementation is authorized and accepted:

| Layer | Purpose | Example |
| --- | --- | --- |
| Source | Original uploaded PDF/document | original object and upload metadata |
| RawMaterial | MinerU parse and current AI metadata outputs | `content_list_v2.json`, `full.md`, AI metadata |
| CleanMaterial | CleanService outputs | `toc-rebuild` outputs such as `flooded_content.json` and `logic_tree.json` |
| Downstream | Future educational workflows | chapter-aware metadata, exercise extraction, knowledge graph inputs |

Existing `eduassets` / `eduassets-parsed` data remains legacy unless a separate migration task is authorized. No pseudo-provenance should be invented for legacy data.

## 5. Identity Model

The target model for new CleanService assets is:

| ID | Owner | Meaning |
| --- | --- | --- |
| `materialId` | Luceon | logical material identity for a source document |
| `parseTaskId` | Luceon | one processing task or rerun instance |
| `assetVersion` | Luceon | version of a given `(serviceName, materialId)` output |
| `job_id` | Luceon | CleanService job idempotency key |

`assetVersion` must be assigned by Luceon and passed to the CleanService. A CleanService must not independently decide Luceon's asset lifecycle version.

Whether future `materialId` becomes hash-based globally or is introduced only for new CleanService assets remains a product/architecture decision before implementation.

## 6. Target MinIO Layout

For new CleanService-enabled assets only, the target layout is:

```text
eduassets-raw/
  pdfs/{materialId}/
    original.pdf
    meta.json
  mineru/{materialId}/v{N}/
    content_list_v2.json
    content_list_v2.md
    images/...
    provenance.json
  ai-metadata/{materialId}/v{N}/
    metadata.json
    provenance.json

eduassets-clean/
  toc-rebuild/{materialId}/v{N}/
    flooded_content.json
    logic_tree.json
    readable_tree.md
    skeleton.json
    token_stats.json
    provenance.json
```

This layout is not an immediate migration instruction. Existing buckets and objects remain legacy until Director issues and accepts a separate migration plan.

## 7. CleanService Directory

| Service | External implementation | Status | Primary input | Primary outputs |
| --- | --- | --- | --- | --- |
| `toc-rebuild` | `shcming2023/Mineru2Table2026` | future first CleanService | MinerU `content_list_v2.json` | `flooded_content.json`, `logic_tree.json`, `readable_tree.md`, `skeleton.json`, `provenance.json` |
| `md-clean` | TBD | future | raw/clean structure assets | cleaned Markdown and structured blocks |
| `figure-rebuild` | TBD | future | images and structure assets | figure metadata/assets |

Each service must follow `docs/contracts/CleanService-Protocol-v1.md` before Luceon binds production code to it.

## 8. Orchestration Direction

Luceon should introduce a template-based `CleanServiceWorker` rather than embedding Mineru2Table-specific logic inside the existing parse worker.

The worker boundary should include:

- service registration and endpoint configuration;
- health and admission-circuit checks;
- MinIO ObjectRef input discovery;
- Luceon-owned `assetVersion` allocation;
- job submission using `job_id` idempotency;
- callback or polling reconciliation;
- task-event and UI status updates;
- provenance and output verification;
- cost soft-limit pause behavior;
- explicit failure mapping.

Heavy CleanService stages should default to active concurrency `<=1` on the current local single-machine runtime unless Director later authorizes a broader concurrency model.

## 9. Retention And Cleanup

No fixed old-version retention count is set in this phase.

Future assets must preserve enough structure and provenance to support a later cleanup decision, but automatic cleanup is not part of this foundation. A later Director task must define:

- retention count or retention policy;
- archival vs deletion behavior;
- user authorization boundary;
- dry-run and audit output;
- rollback expectations.

Until that task exists, old versions must not be deleted merely because this architecture document exists.

## 10. Cost And Review Boundary

CleanService stages involving LLM calls must be cost-aware.

- Luceon soft limit: `¥5`.
- Service hard limit: `¥8`.

Crossing the soft limit should pause the path for Director/User decision. Crossing the hard limit must stop explicitly and must not be silently retried as if normal completion occurred.

Operator review should eventually expose clean-stage state, clean outputs, unresolved anchors, provenance, and cost/token summary in product language.

## 11. Non-Goals

This vision does not authorize:

- implementation of `CleanServiceWorker`;
- Mineru2Table API changes;
- production/runtime/Docker/DB/MinIO/MinerU/Ollama changes;
- migration of existing assets;
- automatic cleanup;
- release or production readiness claims.

