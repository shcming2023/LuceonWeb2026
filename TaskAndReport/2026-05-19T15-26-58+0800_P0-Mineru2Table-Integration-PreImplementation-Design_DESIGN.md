# P0 Mineru2Table Integration Pre-Implementation Design

## 1. Current-State Inventory

The current repository contains a disabled foundation for CleanService (`server/services/cleanservice/`). The relevant modules are:
- **CleanService Config (`config.mjs`)**: Uses `CLEANSERVICE_ENABLED` to disable the service by default. Defines protocol version `v1`, default service name `toc-rebuild`, and sets soft/hard cost limits. It verifies basic requirements like endpoint and API key.
- **Worker Shell (`cleanservice-worker.mjs`)**: Scans for eligible tasks (states like `review-pending`, `completed`, `done`) and builds a job request. However, it currently relies on legacy input selection (`artifactManifestObjectName`, `markdownObjectName`, `parsedPrefix`) rather than the canonical `content_list_v2.json`. The worker is **not** wired into the actual runtime startup (`upload-server.mjs`).
- **Client & Protocol (`protocol.mjs`)**: Normalizes protocol responses and manages job state mapping. The `transport` function is currently just an injected mock/placeholder; there is no real HTTP client performing `POST /api/v1/jobs`.
- **States & Output Verifier (`states.mjs`, `output-verifier.mjs`)**: Maps states like `pending/running/completed/protocol-failure` to product labels (e.g., `等待目录重建`). The output verifier requires a `provenance.json` but needs alignment with the full Protocol v1 output requirements.
- **Smoke Tests**: `cleanservice-foundation-smoke.mjs` and `cleanservice-worker-shell-smoke.mjs` exist and prove basic mock interactions, but no real protocol interaction.
- **Task & Material Metadata**: Current AI extraction stops at `review-pending` or `done` states. There is no version allocator for `assetVersion`.

## 2. Gap Matrix

| Requirement | Current evidence | Gap | Future task needed |
| --- | --- | --- | --- |
| **Raw Material ObjectRef** | Uses legacy `eduassets-parsed` and `parsedPrefix`. | Does not target canonical `content_list_v2.json` as required by Protocol v1. | Task A |
| **Job Identifiers (`assetVersion`)**| Assumes `cleanServiceNextVersion` or defaults to `v1`. | No authoritative asset version allocator. | Task A |
| **MinIO Input/Output Refs** | Uses custom `role` strings and legacy buckets. | Protocol requires `mineru-content` role and `eduassets-raw/mineru/` bucket. | Task A |
| **HTTP Transport** | Injected function placeholder. | No real HTTP client for `POST /api/v1/jobs` and `GET /api/v1/jobs/{job_id}`. | Task B |
| **Callback/HMAC Route** | None. | No route in `upload-server.mjs` to receive Mineru2Table webhooks. | Task C |
| **Service Admission Circuit** | None. | Must check `GET /health` before dispatching to external service. | Task B |
| **Output/Provenance Verifier**| Basic `provenance.json` check. | Missing checks for `flooded_content.json`, `logic_tree.json`, etc. | Task D |
| **Cost Behavior** | Evaluated in `states.mjs`. | Soft/hard costs are mapped but UI flow for `cost-decision` and `quota_exceeded` is incomplete. | Task E |
| **Partial/Unresolved-anchor** | Protocol mapping exists (`review-pending-partial`). | UI mapping for partial success is missing. | Task F |
| **Retry/Reparse/Re-AI Boundary**| None. | CleanService jobs must be canceled if a task is reparsed or re-AI'd. | Task E |
| **UI Read Surface** | None. | Task list/detail do not natively render `cleanServiceJobs`. | Task F |

## 3. Proposed Implementation Sequence

To safely approach integration, work must be split into strictly mock/safe tasks before any real dispatch:

### Task A: Raw Material Canonical Adapter (Mock-Safe)
- **Purpose**: Update `buildInputObjectRef` to select `content_list_v2.json` strictly from `eduassets-raw/mineru/{materialId}/v{N}/` and implement the asset version allocator.
- **Write Boundary**: `server/services/cleanservice/cleanservice-worker.mjs`, `server/services/cleanservice/config.mjs`.
- **Feature Flag Posture**: Must remain disabled by `CLEANSERVICE_ENABLED=false`. Code runs only in unit tests.
- **Positive Acceptance**: Worker outputs the exact Protocol v1 request shape. Correctly identifies canonical input paths.
- **Negative Acceptance**: Legacy `parsedPrefix` inputs are gracefully skipped (`skipped-policy`). No DB/MinIO mutation.
- **Minimum Tests**: Unit tests verifying request payload schema and valid/invalid inputs.
- **Non-Goals**: No actual HTTP transport. No UI changes.

### Task B: Real HTTP Transport & Admission Circuit (Mock-Safe)
- **Purpose**: Implement the fetch-based HTTP transport for `POST /api/v1/jobs` and `GET /api/v1/jobs/{job_id}`, including `/health` pre-flight checks.
- **Write Boundary**: `server/services/cleanservice/protocol.mjs`, `server/services/cleanservice/transport.mjs` (new).
- **Feature Flag Posture**: Mock-only gate; transport runs against `nock` or local fastify test server.
- **Positive Acceptance**: Successfully maps `202`, `200`, `4xx`, `503`, and timeout responses to correct internal states. Admission circuit halts dispatch if `/health` fails.
- **Negative Acceptance**: Service must not retry on non-retriable `4xx`. Must not attempt to reach external network during tests.
- **Minimum Tests**: Mock HTTP tests covering network timeout, `503` admission failure, and success loops.
- **Non-Goals**: No integration into `upload-server.mjs`. No webhook receiver.

### Task C: Webhook Callback Route (Mock-Safe)
- **Purpose**: Implement a public route to receive HMAC-signed job updates from CleanService.
- **Write Boundary**: `server/upload-server.mjs`, `server/lib/cleanservice-routes.mjs`.
- **Feature Flag Posture**: Route is registered but protected by HMAC verification and `CLEANSERVICE_ENABLED`.
- **Positive Acceptance**: Rejects invalid HMAC payloads. Updates internal `cleanServiceJobs` idempotently on valid webhook.
- **Negative Acceptance**: No unauthorized webhook can mutate task state. Malformed payloads return `400`.
- **Minimum Tests**: HTTP endpoint integration tests sending mock signed payloads and verifying DB patch logic.
- **Non-Goals**: No real external Mineru2Table traffic.

### Task D: Strict Output Verifier Update
- **Purpose**: Update `output-verifier.mjs` to strictly enforce Protocol v1 outputs and extract Data Governance checks.
- **Write Boundary**: `server/services/cleanservice/output-verifier.mjs`.
- **Feature Flag Posture**: Unit-test isolated.
- **Positive Acceptance**: Verifier validates presence of `flooded_content.json`, `logic_tree.json`, `readable_tree.md`, `skeleton.json`, and `provenance.json`.
- **Negative Acceptance**: Rejects outputs missing required artifacts as `protocol-failure`. No modification to DB records yet.
- **Minimum Tests**: Fixture-based tests providing complete and incomplete mock outputs.
- **Non-Goals**: No downloading of actual large artifacts; only MinIO ObjectRef verification via metadata `stat`.

### Task E: Cross-Boundary Safety & State Contracts
- **Purpose**: Ensure `progressSnapshot` cancels active `toc-rebuild` jobs upon Re-AI/retry actions, and implement strict soft/hard cost semantics.
- **Write Boundary**: `server/lib/task-actions-routes.mjs`, `server/lib/progress-snapshot.mjs`, `server/services/cleanservice/states.mjs`.
- **Feature Flag Posture**: Tested via existing task action routes.
- **Positive Acceptance**: Triggering Re-AI safely transitions any active clean job to `canceled`. Hard limit (`¥8`) results in terminal `failed`/`quota_exceeded`, while soft limit (`¥5`) enters `cost-decision`.
- **Negative Acceptance**: Hard cost limit crossing must not use the `cost-decision` override flow.
- **Minimum Tests**: Regression tests on Re-AI cancelling clean jobs.
- **Non-Goals**: No external state syncing. No UI elements for the cost override flow.

### Task F: UI State Surface (Read-Only)
- **Purpose**: Render `toc-rebuild` state, cost decisions, and partial success in the UI.
- **Write Boundary**: `src/app/utils/taskView.ts`, `src/app/utils/taskTerms.ts`, frontend components.
- **Feature Flag Posture**: Frontend changes active but only visible if data exists.
- **Positive Acceptance**: Clean states (`等待目录重建`, `成本待决策`, `部分完成待复核`, `quota_exceeded`) are correctly labeled and styled.
- **Negative Acceptance**: No functional frontend changes (no new buttons to mutate state).
- **Minimum Tests**: Unit/Snapshot tests for `taskView` utility functions mapping new states.
- **Non-Goals**: No UI buttons for cost override or retry.

## 4. Exact Data And State Contract

**Note**: All large text artifacts (JSON trees, MD files) MUST remain in MinIO. Only ObjectRefs and structural summaries are persisted via the existing DB/API metadata abstraction (task/material metadata).

### 4.1 Job Request Record Shape
Dispatched as JSON payload to `POST /api/v1/jobs`. Not stored entirely in DB; only `jobId` and state are synced.
```json
{
  "job_id": "luceon-pt_abc123-toc-rebuild-v1",
  "material_id": "sha256:a1b2c3d4e5f60718",
  "parse_task_id": "pt_abc123",
  "asset_version": "v1",
  "inputs": [
    {
      "role": "mineru-content",
      "source": {
        "type": "minio",
        "endpoint": "minio:9000",
        "use_ssl": false,
        "bucket": "eduassets-raw",
        "object": "mineru/sha256:a1b2c3d4e5f60718/v1/content_list_v2.json"
      }
    }
  ],
  "sink": {
    "type": "minio",
    "endpoint": "minio:9000",
    "use_ssl": false,
    "bucket": "eduassets-clean",
    "prefix": "toc-rebuild/sha256:a1b2c3d4e5f60718/v1/"
  },
  "callback_url": "https://luceon.local/api/v1/cleanservice/callback",
  "callback_secret_ref": "TOC_REBUILD_CALLBACK_SECRET",
  "options": {
    "max_cost_cny": 8.0
  }
}
```

### 4.2 Task Metadata Summary (DB Persisted)
In `task.metadata.cleanServiceJobs.toc-rebuild`:
```json
{
  "jobId": "luceon-pt_abc123-toc-rebuild-v1",
  "cleanState": "running",
  "service": "toc-rebuild",
  "protocol": "v1",
  "assetVersion": "v1",
  "parseTaskId": "pt_abc123",
  "materialId": "sha256:a1b2c3d4e5f60718",
  "input": {
    "role": "mineru-content",
    "bucket": "eduassets-raw",
    "object": "mineru/sha256:a1b2c3d4e5f60718/v1/content_list_v2.json"
  },
  "sink": {
    "bucket": "eduassets-clean",
    "prefix": "toc-rebuild/sha256:a1b2c3d4e5f60718/v1/"
  },
  "submittedAt": "2026-05-19T10:00:00Z",
  "costCny": 0.0,
  "error": null,
  "isRetriable": true
}
```

### 4.3 Material Metadata Summary (DB Persisted)
In `material.metadata.cleanMaterials.toc-rebuild`:
```json
{
  "jobId": "luceon-pt_abc123-toc-rebuild-v1",
  "assetVersion": "v1",
  "service": "toc-rebuild",
  "protocol": "v1",
  "status": "completed",
  "costCny": 4.5,
  "completedAt": "2026-05-19T10:05:00Z",
  "provenanceHash": "sha256:1a2b3c...",
  "outputs": {
    "provenanceRef": "toc-rebuild/sha256:a1b2c3d4e5f60718/v1/provenance.json",
    "floodedContentRef": "toc-rebuild/sha256:a1b2c3d4e5f60718/v1/flooded_content.json"
  }
}
```

### 4.4 Output/Provenance Summary (MinIO Stored)
Written to MinIO as `provenance.json` in the sink directory:
```json
{
  "service_name": "toc-rebuild",
  "service_version": "1.0.0",
  "protocol_version": "v1",
  "job_id": "luceon-pt_abc123-toc-rebuild-v1",
  "inputs": [
    {
      "role": "mineru-content",
      "object": "mineru/sha256:a1b2c3d4e5f60718/v1/content_list_v2.json",
      "hash": "sha256:abcd..."
    }
  ],
  "outputs": {
    "floodedContent": {
      "object": "toc-rebuild/sha256:a1b2c3d4e5f60718/v1/flooded_content.json",
      "hash": "sha256:f123..."
    },
    "logicTree": {
      "object": "toc-rebuild/sha256:a1b2c3d4e5f60718/v1/logic_tree.json",
      "hash": "sha256:f456..."
    }
  }
}
```

### 4.5 Clean-Stage Task-Event Payload (HMAC Secured)
Received via Webhook callback `POST /api/v1/cleanservice/callback`.

**HTTP Headers**:
- `X-CleanService-Job-Id`: `luceon-pt_abc123-toc-rebuild-v1`
- `X-CleanService-Delivery`: `uuid-v4`
- `X-CleanService-Attempt`: `1`
- `X-CleanService-Signature`: `hmac-sha256=hex_signature`

**Raw JSON Terminal Job-State Body**:
```json
{
  "job_id": "luceon-pt_abc123-toc-rebuild-v1",
  "service_name": "toc-rebuild",
  "protocol_version": "v1",
  "status": "completed",
  "stats": {
    "cost_cny": 4.5,
    "duration_ms": 300000
  },
  "error": null
}
```

**Verification Requirement**:
The signature verification **must** use the raw body bytes and the secret reference `callback_secret_ref`. The system must reject malformed or missing signature headers with HTTP `401`/`403` before any internal DB mutation occurs. Once verified, this payload is mapped to internal task events.

## 5. Mandatory Data-Governance Red Lines

Because this task concerns AI data processing and future clean outputs, the following rules are non-negotiable and must be verified in Task D (Strict Output Verifier):

1. **ID-Only Extraction**: Service/model choices must cite stable block IDs or source references. They must **not** invent, rewrite, or hallucinate free text as if it were source truth. Verification: Protocol output must contain source anchor references.
2. **Asset Hash Locking**: Original resource hash names (images/audio) must be locked and preserved through the pipeline. Services must not rename original resource hashes by convenience.
3. **Pure Layout/Code-Generation Boundary**: Any later LaTeX/TikZ or code-like clean output must use standard packages and avoid custom macros unless separately authorized.

## 6. Soft/Hard Cost Semantics

The implementation must preserve distinct semantics for cost limits:
- **Soft Limit (¥5)**: Enters the `cost-decision` state. The job pauses pending human decision.
- **Hard Limit (¥8)**: Crosses the absolute threshold. The job is explicitly stopped and enters a non-retriable `quota_exceeded` or terminal `failed` state. This must **not** use the `cost-decision` override flow.

## 7. Raw Material ObjectRef Decision

- **Selection Logic**: The pipeline targets the canonical layout: `eduassets-raw/mineru/{materialId}/v{N}/content_list_v2.json`.
- **Legacy Recommendation**: Lucode recommends rejecting legacy `eduassets-parsed` compatibility completely for CleanService pending Luceon acceptance.
- **Safe Behavior for Legacy Assets**: Legacy assets without `content_list_v2.json` should safely fall into a `skipped-policy` or `not-applicable` state.
- **Strict Limitation**: No existing asset reparse, migration, backfill, deletion, or pseudo-provenance creation is authorized by this design.

## 8. Runtime And Safety Gates

- **Disabled by Default**: `CLEANSERVICE_ENABLED=false` remains the hard default.
- **Admission Circuit**: No job is submitted unless `GET /health` returns HTTP 200 `status="healthy"`.
- **Concurrency Limit**: Active `toc-rebuild` jobs per material must be `<=1`.
- **No Phase 1 Blocking**: CleanService operates completely asynchronously and must not block core AI extraction.
- **No Automatic Retry**: Terminal states require explicit user intervention.

## 9. Open Decisions

- **Luceon Acceptance Required**: The specific algorithm for `assetVersion` allocation (e.g., strict monotonic `v1`, `v2`, or mapping to existing `mineru_version`) before Task A is scheduled.
- **Luceon Acceptance Required**: Confirming the recommendation to treat legacy parsed assets as `skipped-policy`.
- **Director / User Decision Required**: If an override concept is desired after a hard cost limit (`quota_exceeded`) failure, this must be decided by product, but it cannot override the `¥8` limit on the flight.
