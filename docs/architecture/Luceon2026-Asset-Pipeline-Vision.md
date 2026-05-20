# Luceon2026 Asset Pipeline Vision

Status: Proposed / Candidate architecture direction, aligned with independent CleanService service model (TASK-223)
Last updated: 2026-05-20
Historical owner: Architect; role retired after 6.9.1. Current Lucode updates active.
Related PRD: `docs/prd/Luceon2026-PRD-v0.4.md`, `docs/prd/Luceon2026-PRD-v0.4-Independent-CleanService-Services-Addendum.md`

## 1. Boundary

This document defines the future asset-pipeline direction for introducing CleanService stages such as Mineru2Table `toc-rebuild`.

It does not replace the current PRD v0.4 mainline:

```text
PDF source asset -> Raw Material -> Clean Material
```

Specifically, the Phase 1 trace begins with:
```text
upload -> local MinerU -> MinIO -> Ollama qwen3.5:9b -> AI metadata -> operator review
```

It does not claim CleanService implementation acceptance, production readiness, L3, pressure PASS, release readiness, production go-live, or any current runtime capability.

## 2. Vision

Luceon2026 should evolve from a parse-and-review CMS into a durable educational asset pipeline. In that pipeline, each stage creates assets that can be inspected, versioned, reviewed, and traced.

The project formally establishes the **Independent CleanService Service Model**:
* **Mineru2Table** is the first independent CleanService, responsible for `toc-rebuild` (structural table-of-contents prep). It is developed in its own repository (`shcming2023/Mineru2Table2026`) and deployed as an independent Docker container.
* **RawMaterial2CleanMaterial** is a subsequent, distinct clean stage with a separate repository and deployment boundary, responsible for final block-level cleaning and normalization. It must not be collapsed into Mineru2Table.
* **Collaborative API Model**: Both services are separately developed, separately Docker-deployed, and integrate with Luceon asynchronously using the stable CleanService Protocol API using MinIO ObjectRefs as the hands-off interface.

## 3. Principles

1. Asset first: each important stage output is a durable MinIO asset, not an invisible temporary file.
2. Luceon orchestrates: Luceon owns material identity, task identity, asset version assignment, scheduling, review, audit, admission circuits, cost decisions, and acceptance semantics.
3. Services are isolated: each CleanService is an external service with its own repository, version, health, job state, and failure domain. Both Mineru2Table and RawMaterial2CleanMaterial are strictly independent repos and Docker containers, communicating with Luceon via the CleanService Protocol API.
4. Provenance is mandatory for new CleanService assets: future clean outputs must include enough provenance to explain inputs, service version, options, cost, and output object hashes.
5. Failure is explicit: raw MinerU output, skeleton output, placeholder output, or partial unresolved anchors must never be presented as successful clean output.
6. Current evidence remains separate: future CleanService validation must not overwrite existing pressure-test, AI residual, recovery, or release-boundary evidence.

## 4. Asset Layers

Future new assets may use these layers after implementation is authorized and accepted:

| Layer | Purpose | Example |
| --- | --- | --- |
| Source | Original uploaded PDF/document | original object and upload metadata |
| RawMaterial | **Durable layer** for MinerU parse and current AI metadata outputs | `content_list_v2.json`, `full.md`, AI metadata |
| CleanMaterial (Prep) | Mineru2Table outputs (chapter/TOC/table logical structure) | `toc-rebuild` outputs such as `flooded_content.json` and `logic_tree.json` |
| CleanMaterial (Final) | RawMaterial2CleanMaterial final normalized cleaning | Cleaned and normalized text/blocks ready for downstream |
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
    unresolved_anchors.json
    provenance.json
    metrics.json
  raw2clean/{materialId}/v{N}/ (Proposed / Future)
    clean_blocks.json
    clean_markdown.md
    clean_manifest.json
    quality_report.json
    unresolved_items.json
    provenance.json
    metrics.json
```

This layout is not an immediate migration instruction. Existing buckets and objects remain legacy until a future approved migration plan exists.

## 7. CleanService Registry Contract

To orchestrate independent, Docker-deployed services safely, Luceon maintains a central control plane registry definition. Every registered CleanService must strictly satisfy the fields and data contracts defined below.

### 7.1 Service Registry Schema Definition

| Schema Field | Type | Description |
| --- | --- | --- |
| `serviceName` | String | Unique system identifier for the clean stage. |
| `serviceType` | Enum | Classification of workload (`structural_preparation`, `content_cleaning`, `feature_extraction`). |
| `implementationRepo` | String | Git repository URL of the external service implementation. |
| `containerIdentity` | String | Docker image name and standard container identifier. |
| `endpointBinding` | String | Local loopback or internal Docker network base URL and health path. |
| `protocolVersion` | String | Supported version of the CleanService Protocol (e.g. `v1`). |
| `admissionStatus` | Enum | Control plane activation status (`enabled`, `disabled`, `dry_run`). |
| `inputBucketObjectContract` | String | Strict MinIO bucket and key path pattern allowed for reads. |
| `outputBucketPrefixContract` | String | Strict MinIO bucket and output directory prefix allowed for writes. |
| `costPolicy` | Struct | Cost governance limits: `{ soft_limit_cny, hard_limit_cny }`. |
| `featureFlags` | Array | Toggles and flags enabled for this service runtime configuration. |
| `integrationState` | Enum | Stage of platform validation (`Proposed`, `Sandbox_Active`, `Production_Active`). |
| `owner` | String | Technical team or role responsible for the service. |
| `reviewBoundary` | Struct | UI views and unresolved exception parameters to render for operator triage. |

### 7.2 Active & Proposed Registry Records

| Field | Record 1: Structural Prep (`toc-rebuild`) | Record 2: Content Cleaning (`md-clean`) |
| --- | --- | --- |
| **serviceName** | `toc-rebuild` | `md-clean` |
| **serviceType** | `structural_preparation` | `content_cleaning` |
| **implementationRepo** | `shcming2023/Mineru2Table2026` | `shcming2023/RawMaterial2CleanMaterial2026` (Proposed) |
| **containerIdentity** | `mineru2table-api` | `raw2clean-api` (Proposed) |
| **endpointBinding** | `http://mineru2table-api:8000/api/v1/jobs` | `http://raw2clean-api:8000/api/v1/jobs` (Proposed) |
| **protocolVersion** | `v1` | `v1` |
| **admissionStatus** | `enabled` (Proposed Candidate) | `disabled` (Proposed Future) |
| **inputBucketObjectContract** | `eduassets-raw:mineru/{materialId}/v{N}/content_list_v2.json` | `eduassets-raw:mineru/{materialId}/v{N}/content_list_v2.json`<br>`eduassets-clean:toc-rebuild/{materialId}/v{N}/logic_tree.json` |
| **outputBucketPrefixContract** | `eduassets-clean:toc-rebuild/{materialId}/v{N}/` | `eduassets-clean:raw2clean/{materialId}/v{N}/` |
| **costPolicy** | `soft_limit: ¥5`, `hard_limit: ¥8` | `soft_limit: ¥5`, `hard_limit: ¥8` |
| **featureFlags** | `["enable_table_extraction", "strict_anchors"]` | `["latex_normalization", "tikz_code_standardize"]` |
| **integrationState** | `Sandbox_Active` (Candidate) | `Proposed` |
| **owner** | Lucode (Development) / Luceon (Audit) | Lucode (Development) / Luceon (Audit) |
| **reviewBoundary** | Expose TOC tree diff, unresolved anchor count, and layout cockpit. | Expose markdown diff, TikZ code syntax warnings, block comparison. |

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

Heavy CleanService stages should default to active concurrency `<=1` on the current local single-machine runtime unless a future approved governance process authorizes a broader concurrency model.

## 9. Retention And Cleanup

No fixed old-version retention count is set in this phase.

Future assets must preserve enough structure and provenance to support a later cleanup decision, but automatic cleanup is not part of this foundation. A later approved plan must define:

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

Crossing the soft limit should pause the path for explicit user or future-governance decision. Crossing the hard limit must stop explicitly and must not be silently retried as if normal completion occurred.

Operator review should eventually expose clean-stage state, clean outputs, unresolved anchors, provenance, and cost/token summary in product language.

## 11. Non-Goals

This vision does not authorize:

- implementation of `CleanServiceWorker`;
- Mineru2Table API changes;
- production/runtime/Docker/DB/MinIO/MinerU/Ollama changes;
- migration of existing assets;
- automatic cleanup;
- release or production readiness claims.
