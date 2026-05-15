# CleanService Mineru2Table Adaptation Plan

Status: Architecture planning document for future external dependency work  
Last updated: 2026-05-15  
Owner: Architect  
External repository: `shcming2023/Mineru2Table2026`

## 1. Boundary

This document describes how Mineru2Table2026 should adapt to `docs/contracts/CleanService-Protocol-v1.md` before Luceon2026 implements a production integration.

It does not implement or verify Mineru2Table changes. It does not authorize Luceon runtime, production, Docker, DB, MinIO, MinerU, Ollama, or source-code changes.

## 2. Target Role

Mineru2Table2026 becomes the first CleanService:

| Field | Target |
| --- | --- |
| `service_name` | `toc-rebuild` |
| Primary input | MinerU `content_list_v2.json` by MinIO ObjectRef |
| Primary output | rebuilt TOC / anchor structure |
| Output bucket | `eduassets-clean` |
| Output prefix | `toc-rebuild/{materialId}/{assetVersion}/` |
| Protocol | `CleanService Protocol v1` |

Luceon remains orchestrator and owns `materialId`, `parseTaskId`, `assetVersion`, job submission, review, audit, cost decisions, and task state.

## 3. Current Known Gap

The source material describes Mineru2Table's current API as multipart-oriented:

- `POST /api/v1/extract`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`

The future Luceon integration requires:

- MinIO ObjectRef input;
- MinIO ObjectRef output;
- durable job idempotency;
- `provenance.json`;
- webhook or pollable terminal status;
- structured errors;
- cost hard-limit enforcement;
- deprecated but retained old routes.

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

At minimum, write:

- `flooded_content.json`;
- `logic_tree.json`;
- `readable_tree.md`;
- `skeleton.json`;
- `token_stats.json`;
- `provenance.json`.

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

Before Luceon implementation starts, Director should require evidence that Mineru2Table supports:

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

