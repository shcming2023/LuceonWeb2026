# CleanService Mineru2Table Adaptation Plan

Status: Architecture planning document for future external dependency work  
Last updated: 2026-05-15  
Historical owner: Architect; role retired after 6.9.1
External repository: `shcming2023/Mineru2Table2026`

## 1. Boundary

This document describes how Mineru2Table2026 should adapt to `docs/contracts/CleanService-Protocol-v1.md` before Luceon2026 implements a production integration.

It does not implement or verify Mineru2Table changes. It does not authorize Luceon runtime, production, Docker, DB, MinIO, MinerU, Ollama, or source-code changes.

## 2. Target Role

Mineru2Table2026 becomes the first Clean Material preparation service:

| Field | Target |
| --- | --- |
| `service_name` | `toc-rebuild` |
| Primary input | MinerU `content_list_v2.json` by MinIO ObjectRef |
| Primary output | rebuilt TOC / anchor structure |
| Output bucket | `eduassets-clean` |
| Output prefix | `toc-rebuild/{materialId}/{assetVersion}/` |
| Protocol | `CleanService Protocol v1` |

Luceon remains orchestrator and owns `materialId`, `parseTaskId`, `assetVersion`, job submission, review, audit, cost decisions, and task state. The outputs of this service, along with the original Raw Material, will be consumed by the subsequent `RawMaterial2CleanMaterial` stage to produce final Clean Material.

## 3. Current Known Gap

Mineru2Table2026 is developed as an independent service in repository `shcming2023/Mineru2Table2026` (deployed as Docker container `mineru2table-api` exposing port `8000`).
The current exposed API shape observed from OpenAPI/source is multipart-oriented:
- `/health` (returns basic status; currently exposes `llm_status=not_configured`)
- `POST /api/v1/extract` (synchronous file-upload extraction)
- `POST /api/v1/tasks` (asynchronous multipart-upload task submission)
- `GET /api/v1/tasks/{task_id}` (polling endpoint returning JSON extraction)

The target CleanService Protocol v1 required for production Luceon integration demands a massive shift to ObjectRef-based processing:
- MinIO ObjectRef input (`eduassets-raw/.../content_list_v2.json`);
- MinIO ObjectRef outputs (written to assigned prefixes under `eduassets-clean/...`);
- Durable, persistent job state machine and `/api/v1/jobs` endpoints;
- Stable callback webhooks signed with HMAC-SHA256 signatures;
- Strict cost limits (`¥8` hard stop via `quota_exceeded`);
- Immutable `provenance.json` generation.

### 3.1 Transition Strategy & Recommendation Matrix

To bridge the gap between Mineru2Table's current standalone API and the target CleanService Protocol v1, the following transition strategies are evaluated:

| Option | Description | Pros | Cons | Recommendation |
| --- | --- | --- | --- | --- |
| **Option A (Recommended)** | **Direct Protocol Implementation**: Modify the external Mineru2Table service codebase directly to implement CleanService Protocol v1 (MinIO ObjectRefs, `/api/v1/jobs` endpoints, persistent jobs, environment-based credentials). | • Zero file-copy network overhead.<br>• Guaranteed immutable provenance.<br>• Cleanest, production-ready architecture. | • Requires development effort in the external Python repository. | **Highly Recommended**. This is the only option approved for stable production integration and scale deployment. |
| **Option B (Rejected)** | **Luceon-Side Multipart Adapter**: Luceon's `CleanServiceWorker` downloads files from MinIO locally, creates a multipart HTTP request to Mineru2Table's `/api/v1/tasks`, polls it, downloads output files, and writes them back to MinIO. | • No changes needed in Mineru2Table codebase. | • Severe network and local disk bottleneck (double-copy).<br>• High risk of silent failure and provenance corruption.<br>• Exposes temporary local files to host volume. | **Strictly Rejected**. Not safe for production or multi-user pipelines due to file isolation and provenance risks. |
| **Option C (Temporary Gate)** | **Hybrid Local Sidecar Adapter**: Deploy a lightweight local sidecar next to Mineru2Table that exposes Protocol v1 to Luceon and translates it internally to Mineru2Table's multipart API. | • Allows early prototyping of Luceon control plane without Python changes. | • High architectural complexity.<br>• Overhead of managing an extra container.<br>• Remains subject to double-copy network overhead. | **Staged Prototyping Only**. Permitted strictly as a temporary development gate under rigid Sunset Controls. |

#### Strict Sunset Controls for Temporary Option C:
If Option C (Hybrid Sidecar Adapter) is utilized for initial sandbox verification, the following binding constraints apply:
1. **Developer Sandbox Only**: The adapter must **never** be deployed or wired into production or production-UAT environments.
2. **Hard Sample Ceiling**: The sandbox runtime must limit total processed assets to at most **5 unique materials**. Attempting to process more must throw a `quota_exceeded` error.
3. **Hard Date Sunset**: The sidecar code and registration must be fully retired and deleted (Sunset) by **2026-06-15** or upon the initiation of Task 224 (whichever comes first), shifting exclusively to Option A.
4. **No Write Privilege**: The sidecar must have zero write access to the Phase 1 mainline buckets (`eduassets-raw`, `eduassets-parsed`) to avoid dirty-source contamination.

## 4. Required External Changes

### M-1. Storage Layer

Add a MinIO storage abstraction that can:

- fetch input ObjectRefs from allowed buckets;
- write output ObjectRefs to allowed buckets/prefixes;
- compute SHA-256 while reading/writing;
- enforce endpoint and bucket allowlists.

Credentials must come from environment variables, not request bodies.

### M-2. Job Model And Store

Add a persistent job model keyed by `job_id`.

Required behavior:

- repeated `POST /api/v1/jobs` with same `job_id` returns existing job state;
- non-terminal and terminal job states survive service restart;
- status fields align with protocol: `queued`, `processing`, `completed`, `failed`, optional `canceled`.

### M-3. Protocol Endpoints

Implement:

- `GET /health`;
- `POST /api/v1/jobs`;
- `GET /api/v1/jobs/{job_id}`;
- optional `POST /api/v1/jobs:from-storage` only as identical alias.

### M-4. Outputs

At minimum, write exactly these 7 files to the output prefix:

- `flooded_content.json` (logical structure mapping)
- `logic_tree.json` (rebuilt tree representation)
- `readable_tree.md` (markdown table-of-contents outline)
- `skeleton.json` (fallback basic schema outline)
- `unresolved_anchors.json` (unmapped section/anchor records)
- `provenance.json` (mandatory cryptographic pipeline lineage)
- `metrics.json` (replacing legacy `token_stats.json` for token and cost audit metadata)

If a subset cannot be produced, the job must fail or explicitly report partial state. It must not report successful clean output with missing required artifacts.

### M-5. Provenance

Generate `provenance.json` after all outputs are complete. Include:

- service name/version/protocol;
- implementation repo and commit;
- Luceon job/task/material/version identifiers;
- input object refs and hashes;
- output object refs and hashes;
- options;
- token/cost stats.

### M-6. Webhook

If Luceon supplies `callback_url`, send terminal job state at least once.

Use HMAC-SHA256 signing when `callback_secret_ref` is supplied. Include:

- `X-CleanService-Job-Id`;
- `X-CleanService-Delivery`;
- `X-CleanService-Attempt`;
- `X-CleanService-Signature`.

### M-7. Error And Cost Model

Implement structured errors matching `CleanService-Protocol-v1`.

Cost policy:

- Luceon soft limit: `¥5` handled by Luceon decision flow.
- Mineru2Table service hard limit: `¥8`, passed as `options.max_cost_cny`.
- Optional token hard limit: `options.max_tokens_total`.

If the hard cost/token limit is reached, terminate explicitly with `quota_exceeded` and `retriable=false`.

### M-8. Deprecated Multipart Routes

Keep old multipart HTTP routes for at least one version cycle, but mark them deprecated after protocol support exists.

Expected behavior:

- add `Deprecation: true`;
- add `Sunset` header anchored to at least `v1.2.0` or later policy;
- add response field `_deprecated: true`;
- log one startup warning;
- preserve CLI/sample workflows where possible.

Luceon must not use these routes as the long-term canonical integration.

### M-9. Docker And Configuration

Mineru2Table should expose:

- `MINIO_ACCESS_KEY`;
- `MINIO_SECRET_KEY`;
- `ALLOWED_MINIO_ENDPOINTS`;
- `ALLOWED_INPUT_BUCKETS`;
- `ALLOWED_OUTPUT_BUCKETS`;
- `TOC_REBUILD_CALLBACK_SECRET`;
- `API_KEY`;
- `JOB_STORE_PATH`;
- service version / implementation commit metadata.

## 5. Luceon-Side Dependency Expectations

Before Luceon implementation starts, the future approved governance process should require evidence that Mineru2Table supports:

- health format with service identity;
- job submission by MinIO ObjectRef;
- idempotency;
- successful write of all required outputs;
- provenance;
- structured terminal failure;
- `quota_exceeded` for hard limit;
- deprecated old routes retained;
- integration tests against a MinIO fixture or equivalent.

## 6. Test Expectations

Mineru2Table implementation should include:

- storage allowlist tests;
- idempotency tests;
- provenance schema tests;
- cost hard-limit tests;
- webhook signature tests;
- E2E test using a real or representative `content_list_v2.json`;
- backward compatibility test for old multipart routes.

Luceon validation remains separate and should start with mock protocol fixtures before any real runtime integration.

## 7. Non-Goals

This adaptation plan does not cover:

- Luceon CleanServiceWorker implementation;
- Luceon DB schema changes;
- Luceon UI changes;
- production rollout;
- migration of old assets;
- cleanup/deletion policy;
- release readiness or go-live decisions.
