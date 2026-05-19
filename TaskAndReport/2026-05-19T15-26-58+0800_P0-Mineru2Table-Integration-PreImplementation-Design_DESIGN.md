# P0 Mineru2Table Integration Pre-Implementation Design

## 1. Current-State Inventory

The current repository contains a disabled foundation for CleanService (`server/services/cleanservice/`). The relevant modules are:
- **CleanService Config (`config.mjs`)**: Uses `CLEANSERVICE_ENABLED` to disable the service by default. Defines protocol version `v1`, default service name `toc-rebuild`, and sets soft/hard cost limits. It verifies basic requirements like endpoint and API key.
- **Worker Shell (`cleanservice-worker.mjs`)**: Scans for eligible tasks (states like `review-pending`, `completed`, `done`) and builds a job request. However, it currently relies on legacy input selection (`artifactManifestObjectName`, `markdownObjectName`, `parsedPrefix`) rather than the canonical `content_list_v2.json`. The worker is **not** wired into the actual runtime startup (`upload-server.mjs`).
- **Client & Protocol (`protocol.mjs`)**: Normalizes protocol responses and manages job state mapping. The `transport` function is currently just an injected mock/placeholder; there is no real HTTP client performing `POST /api/v1/jobs`.
- **States & Output Verifier (`states.mjs`, `output-verifier.mjs`)**: Maps states like `pending/running/completed/protocol-failure` to product labels (e.g., `等待目录重建`). The output verifier requires a `provenance.json` but may need alignment with the full Protocol v1 output requirements.
- **Smoke Tests**: `cleanservice-foundation-smoke.mjs` and `cleanservice-worker-shell-smoke.mjs` exist and prove basic mock interactions, but no real protocol interaction.
- **Task & Material Metadata**: Current AI extraction stops at `review-pending` or `done` states. There is no version allocator for `assetVersion` (`cleanServiceNextVersion` is currently assumed as `'v1'`).

## 2. Gap Matrix

| Requirement | Current evidence | Gap | Future task needed |
| --- | --- | --- | --- |
| **Raw Material ObjectRef** | Uses legacy `eduassets-parsed` and `parsedPrefix`. | Does not target canonical `content_list_v2.json` as required by Protocol v1. | Raw Material Input Selection Update |
| **Job Identifiers (`assetVersion`)**| Assumes `cleanServiceNextVersion` or defaults to `v1`. | No authoritative asset version allocator. | Asset Version Allocator Implementation |
| **MinIO Input/Output Refs** | Uses custom `role` strings and legacy buckets. | Protocol requires `mineru-content` role and `eduassets-raw/mineru/` bucket. | Request Builder Alignment |
| **HTTP Transport** | Injected function placeholder. | No real HTTP client for `POST /api/v1/jobs` and `GET /api/v1/jobs/{job_id}`. | Real HTTP Transport Module |
| **Callback/HMAC Route** | None. | No route in `upload-server.mjs` to receive Mineru2Table webhooks. | Webhook Receiver Route Implementation |
| **Service Admission Circuit** | None. | Must check `GET /health` before dispatching to external service. | Pre-flight Admission Circuit |
| **Output/Provenance Verifier**| Basic `provenance.json` check. | Missing checks for `flooded_content.json`, `logic_tree.json`, etc. | Strict Output Verifier Update |
| **Cost Behavior** | Evaluated in `states.mjs`. | `cost-decision` state lacks UI presentation and authorization flow. | UI Cost Authorization Flow |
| **Partial/Unresolved-anchor** | Protocol mapping exists (`review-pending-partial`). | UI mapping for partial success is missing. | UI State Mapping Extension |
| **Retry/Reparse/Re-AI Boundary**| None. | CleanService jobs must be canceled if a task is reparsed or re-AI'd. | CleanService Cancel/Re-AI Interaction |
| **UI Read Surface** | None. | Task list/detail do not natively render `cleanServiceJobs`. | Task UI Read Surface Integration |
| **External Dependency** | Stubbed out. | External Mineru2Table repo does not yet support CleanService Protocol v1. | External Repo Protocol V1 Compliance (Blocked) |

## 3. Proposed Implementation Sequence

To safely approach integration, work must be split into strictly mock/safe tasks before any real dispatch:

- **Task A: Raw Material Canonical Adapter (Mock-Safe)**
  - *Purpose*: Update `buildInputObjectRef` to select `content_list_v2.json` strictly from `eduassets-raw/mineru/{materialId}/v{N}/`. Add version allocator logic.
  - *Boundary*: `cleanservice-worker.mjs`, `config.mjs`.
  - *Acceptance*: Fails on legacy `parsedPrefix`. Outputs correct Protocol v1 request shape.

- **Task B: Real HTTP Transport & Admission Circuit (Mock-Safe)**
  - *Purpose*: Implement the real `fetch`-based HTTP transport for `POST /api/v1/jobs`, including `/health` pre-flight checks.
  - *Boundary*: `protocol.mjs`, `transport.mjs` (new).
  - *Acceptance*: Tested via mock server (e.g. `nock`). Handles `200`, `202`, `4xx`, `503`, and timeouts.

- **Task C: Webhook Callback Route (Mock-Safe)**
  - *Purpose*: Implement a public route to receive HMAC-signed job updates.
  - *Boundary*: `upload-server.mjs`, new `cleanservice-routes.mjs`.
  - *Acceptance*: Rejects invalid HMAC. Updates internal `cleanServiceJobs` state idempotently.

- **Task D: Cross-Boundary Safety (Re-AI & Reparse Interactions)**
  - *Purpose*: Ensure `progressSnapshot` and Re-AI/retry actions properly cancel or ignore active `toc-rebuild` jobs.
  - *Boundary*: `task-actions-routes.mjs`, `progress-snapshot.mjs`.
  - *Acceptance*: Triggering Re-AI sets clean state to `canceled` or creates a new version.

- **Task E: UI State Surface (Read-Only)**
  - *Purpose*: Expose `toc-rebuild` state, cost decisions, and partial success in the UI.
  - *Boundary*: `src/app/utils/taskView.ts`, frontend components.
  - *Acceptance*: Clean states are correctly colored and labeled in Task Management.

- **Task F: Real Mineru2Table Integration (Blocked)**
  - *Purpose*: Wire `CleanServiceWorker` into `upload-server.mjs` startup and test against a compliant Mineru2Table instance.
  - *Blocked By*: External Mineru2Table repository compliance.

## 4. Data And State Contract

**Task Metadata (`task.metadata.cleanServiceJobs.toc-rebuild`)**:
```json
{
  "jobId": "luceon-pt_abc123-toc-rebuild-v1",
  "cleanState": "running",
  "assetVersion": "v1",
  "submittedAt": "2026-05-19T10:00:00Z",
  "costCny": 0.0,
  "error": null
}
```

**Material Metadata (`material.metadata.cleanMaterials.toc-rebuild`)**:
```json
{
  "assetVersion": "v1",
  "provenanceHash": "sha256:abc...",
  "status": "completed",
  "outputs": {
    "floodedContent": "toc-rebuild/mat_123/v1/flooded_content.json",
    "logicTree": "toc-rebuild/mat_123/v1/logic_tree.json",
    "readableTree": "toc-rebuild/mat_123/v1/readable_tree.md",
    "skeleton": "toc-rebuild/mat_123/v1/skeleton.json"
  }
}
```
*Note: Large artifacts remain in MinIO. Only ObjectRefs and metadata are stored in DB.*

## 5. Raw Material ObjectRef Decision

- **Selection Logic**: The pipeline must exclusively use the canonical layout: `eduassets-raw/mineru/{materialId}/v{N}/content_list_v2.json`.
- **Legacy Rejection**: Legacy parsed layouts (`eduassets-parsed/parsed/...`) must **not** be bridged or supported. If an old asset needs cleaning, it must be re-parsed through the updated pipeline to generate the v2 manifest. This prevents pseudo-provenance and enforces strict traceability.
- **Evidence Required**: Dispatch is only allowed if `content_list_v2.json` existence is verified (via MinIO `statObject` or equivalent metadata confirmation) prior to dispatch.

## 6. Runtime And Safety Gates

- **Disabled by Default**: `CLEANSERVICE_ENABLED=false` remains the hard default. Startup is bypassed unless `true`.
- **Identity Enforcement**: Dispatch halts immediately if `CLEANSERVICE_ENDPOINT` or `CLEANSERVICE_API_KEY` are missing.
- **Admission Circuit**: No job is submitted unless `GET /health` returns HTTP 200 `status="healthy"`.
- **Concurrency Limit**: Active `toc-rebuild` jobs per material must be `<=1`.
- **No Phase 1 Blocking**: CleanService operates completely asynchronously and must not block the core AI extraction completion.
- **No Automatic Retry**: If a job fails due to hard cost limits or a non-retriable protocol error, it enters a terminal failure or `cost-decision` state. Retry requires explicit Luceon/User action.

## 7. Test And Verification Plan

1. **Unit & Smoke Tests**: Verify `buildCleanServiceJobRequest`, state normalization, and cost calculation.
2. **Mock Transport E2E**: Test the HTTP client and webhook receiver using local mocks (e.g., fastify test server or `nock`). Verify HMAC validation.
3. **No-Op Startup Tests**: Ensure `CleanServiceWorker` cleanly skips initialization when disabled.
4. **Idempotency Tests**: Simulate duplicate webhook deliveries and confirm DB state does not corrupt.
5. **UI Component Tests**: Snapshot tests for the various `cleanState` labels.
6. **External E2E**: Explicitly deferred. Real validation will require a localized, v1-compliant Mineru2Table container.

## 8. Open Decisions

- **Lucode Recommendation**: Reject legacy `eduassets-parsed` compatibility completely for CleanService. Enforce clean re-parsing for any asset entering `toc-rebuild`.
- **Luceon Acceptance Required**: The specific algorithm for `assetVersion` allocation (e.g., strict monotonic `v1`, `v2`, or mapping to existing `mineru_version`).
- **Director / User Decision Required**: The resolution flow for jobs entering the `cost-decision` state (i.e., how a user authorizes an override for a hard cost limit).
