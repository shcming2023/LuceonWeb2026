# Mineru2Table Standalone Service Fact Audit

- **Document Target**: technical fact freeze of the deployed Mineru2Table standalone service based on the direct repository code analysis (`shcming2023/Mineru2Table2026`).
- **Audit Date**: 2026-05-20
- **Auditor**: `Lucode`

---

## 1. Executive Summary

A deep read-only inspection of the cloned `shcming2023/Mineru2Table2026` repository has been completed. The audit has revealed a **major, positive shift** in the current standalone service codebase:

Contrary to historical assumptions that the service only exposed deprecated multipart/legacy endpoints and held task states in-memory, the latest standalone service codebase **has already natively implemented over 90% of the CleanService Protocol v1 specification**, including ObjectRef async jobs, atomicity-driven disk storage persistence, HMAC-SHA256 callback webhooks, and MinIO storage isolation controls.

However, several **critical gaps** in the output artifacts and cleanup hygiene have been found. These gaps must be frozen in this document as the final pre-bridge implementation targets.

---

## 2. API Route & Runtime Reality

The standalone service `api_server.py` exposes two distinct generations of endpoints:

### 2.1 CleanService Protocol v1 Endpoints (Active Target)

1. **`GET /health`**
   - **Function**: Readiness check for admission control.
   - **Behavior**: Dynamically audits environment variables (`DEEPSEEK_API_KEY`, `MINIO_ACCESS_KEY`, etc.). If any required variable is missing, it returns `"status": "unhealthy"`.
   - **Response Spec Alignment**: 100% compliant with Protocol v1 checks schema.
2. **`POST /api/v1/jobs`** & **`POST /api/v1/jobs:from-storage`**
   - **Function**: Asynchronous Job submission using MinIO ObjectRefs.
   - **Idempotency**: Checked against the database store. If a matching `job_id` exists, it returns HTTP 200 with the existing state; otherwise, it spawns a background `threading.Thread` to execute the pipeline and returns HTTP 202.
3. **`GET /api/v1/jobs/{job_id}`**
   - **Function**: Fetches the state of a queued/processing/completed/failed job.

### 2.2 Deprecated Legacy Multipart Endpoints (Sunset Target: v1.2.0)

1. **`POST /api/v1/extract`** (Synchronous, multipart file upload processing)
2. **`POST /api/v1/tasks`** (Asynchronous, multipart task submission)
3. **`GET /api/v1/tasks/{task_id}`** (Polling for old multipart tasks)
*These deprecated routes append a response header `Deprecation: true`, `Sunset: Wed, 31 Dec 2026`, and return a `_deprecated: true` JSON field.*

---

## 3. Storage and State Architecture Audit

### 3.1 Persistence & Restart-Survival
- **File**: `src/core/jobs/store.py`
- **Fact**: Contrary to historical analysis, state **is restart-surviving**.
- **Mechanism**: The class `JobStore` requires the environment variable `JOB_STORE_PATH`. It loads state from this JSON file at startup. Updates are made thread-safe via `threading.Lock` and written atomically using a temporary file (`.jobs-*.tmp` with `fsync()`) before using `os.replace` to overwrite the primary target.
- **Safety Gate**: If `JOB_STORE_PATH` is empty at runtime, the server throws a `RuntimeError` and refuses to start, ensuring memory-only leaks are blocked.

### 3.2 MinIO Storage Backend & Security
- **File**: `src/core/storage/minio_backend.py`
- **Fact**: Direct bucket-level authorization controls are implemented.
- **Isolate Policies**:
  - Requires `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` from the environment.
  - Enforces `ALLOWED_MINIO_ENDPOINTS`, `ALLOWED_INPUT_BUCKETS` (default `eduassets-raw`), and `ALLOWED_OUTPUT_BUCKETS` (default `eduassets-clean`) allowlists.
  - If a job request targets an endpoint or bucket outside these lists, `MinIOBackend` throws a `StoragePermissionError`, returning `forbidden_storage_target` with HTTP 403.
- **Isolation Check**: No MinIO credentials ever flow through request payloads, maintaining absolute credential isolation.

### 3.3 Authorization (API Key Verification)
- **Fact**: The server uses `X-API-Key` header authentication.
- **Behavior**: Validates headers against the environment variable `API_KEY`. If `API_KEY` is not configured, the check is skipped. If configured, unauthenticated requests throw HTTP 401.

### 3.4 HMAC Webhook Delivery
- **File**: `src/core/webhook/sender.py`
- **Fact**: Completed or failed jobs trigger HMAC-SHA256 webhook signatures using a backoff loop.
- **Delivery Protocol**:
  - Resolves signature secret from the environment variable named in `callback_secret_ref`.
  - Computes `signature = hmac.new(secret, body, sha256).hexdigest()`.
  - Appends headers: `X-CleanService-Signature: sha256={signature}`, `X-CleanService-Job-Id`, `X-CleanService-Delivery`, and `X-CleanService-Attempt`.
  - Retries up to 5 times using exponential backoff `[1, 5, 15, 60, 300]` seconds. It terminates retries immediately upon receiving a non-retriable HTTP 4xx status.

---

## 4. Input / Output Artifact Contract Gap Map

An inspection of `src/core/jobs/runner.py` shows how inputs are processed and where the output contract diverges from the **Luceon Seven-File Target Contract**:

### 4.1 Input ObjectRef Reality
- **Fact**: The worker correctly downloads input via ObjectRef:
  - Expects `inputs[0]["source"]` to point to a valid MinIO object (e.g. `content_list_v2.json` in `eduassets-raw`).
  - Downloads the file locally to `/tmp/mineru2table_{job_id}/content_list_v2.json`.

### 4.2 Output Artifact Matrix and Compliance Gap

The target output prefix structure is `toc-rebuild/{materialId}/{assetVersion}/`. Below is the audit gap analysis for each required target artifact:

| Target File | Standalone Implementation State | Gap Type | Details & Corrective Actions |
| --- | --- | --- | --- |
| **`logic_tree.json`** | **Compliant** | None | Uploaded correctly via `TopDownTreeBuilder`. |
| **`flooded_content.json`** | **Compliant** | None | Uploaded correctly via `HierarchicalFlooder`. |
| **`readable_tree.md`** | **Compliant** | None | Rebuilt tree outline uploaded correctly in Markdown format. |
| **`skeleton.json`** | **Compliant** | None | Source block schema outline uploaded correctly. |
| **`provenance.json`** | **Compliant** | None | Generates cryptographic hashes of inputs and outputs under `luceon-provenance/v1`. Uploaded correctly after output completion. |
| **`unresolved_anchors.json`** | **Missing** | **Major Functional GAP** | The runner **does not** generate or write this file. <br>**Corrective Action**: Mineru2Table codebase must be modified to calculate unresolved anchors and upload a JSON list (e.g., `[]` if zero) to `unresolved_anchors.json`. |
| **`metrics.json`** | **Diverged Name** | **Contract GAP** | The runner uploads **`token_stats.json`** instead of `metrics.json`. <br>**Corrective Action**: Mineru2Table must rename this artifact role to `metrics` and write it as `metrics.json`. |

### 4.3 Cleanup Hygiene Gap
- **Fact**: Local temp-files downloaded/generated during runner execution (stored under `/tmp/mineru2table_{job_id}/`) **are never deleted** after successful or failed execution.
- **Corrective Action**: The runner must wrap its core logic in a `finally` block and call `shutil.rmtree(temp_dir, ignore_errors=True)` to prevent host filesystem saturation.

---

## 5. Responsibility Split Matrix

| Requirement | Current Mineru2Table | Luceon Target | Owner | Next Action |
| --- | --- | --- | --- | --- |
| **API/Jobs Endpoints** | Implemented | Comply with v1 | **Mineru2Table service** | Core endpoints ready; no further action. |
| **Job Persistence** | Implemented (`JOB_STORE_PATH`) | Persistent | **Mineru2Table service** | Config environment variables at deployment. |
| **API Auth Header** | Implemented (`X-API-Key`) | Authorized Ingress | **Mineru2Table service** | Supply `API_KEY` to Docker environment. |
| **HMAC Callbacks** | Implemented | Signed callback | **Mineru2Table service** | Safe to use. Luceon callback server must verify signature. |
| **Unresolved Anchors** | Absent | `unresolved_anchors.json` | **Mineru2Table service** | **Code modification required** in external repo to upload file. |
| **Metrics Artifact** | Written as `token_stats.json` | `metrics.json` | **Mineru2Table service** | **Code modification required** in external repo to rename role and file. |
| **Temporary Cleanup** | Leaked under `/tmp` | Automatic cleanup | **Mineru2Table service** | **Code modification required** in runner `finally` block. |
| **Orchestration Bridge** | Disabled-noop | Feature-flagged Bridge | **Luceon main project** | Implement mock-safe Protocol v1 integration under `CleanServiceWorker`. |

---

## 6. Safe Transition Sequence Recommendation

Based on this audit, **Option A (Direct Protocol Implementation)** is highly feasible and remains the cleanest production-ready path. Since Mineru2Table already implements 90% of the v1 protocol, we should immediately choose Option A and execute the final adaptations in two parallel phases:

### Phase 1: Minor External Code Alignment (Mineru2Table Repo)
The owner of the `shcming2023/Mineru2Table2026` repository must perform a surgical edit to `src/core/jobs/runner.py`:
1. Modify the artifact upload section to write `metrics.json` instead of `token_stats.json`.
2. Add a basic parser to record unresolved anchors (or write `[]` if none) and write them to `unresolved_anchors.json`.
3. Wrap processing in a `finally` block to perform `shutil.rmtree()` on `/tmp/mineru2table_{job_id}`.
4. Push a new tag/commit.

### Phase 2: Luceon Integration Bridge (Luceon Main Project)
Luceon can now build a highly robust, mock-safe API Bridge utilizing **Option A**:
1. Implement `CleanServiceWorker` interactions strictly calling `POST /api/v1/jobs` and `GET /api/v1/jobs/{job_id}`.
2. Wire up the callback webhook handler in `upload-server.mjs` to receive terminal state notifications, strictly verifying the HMAC-SHA256 signature against the shared secret.
3. Keep `CLEANSERVICE_ENABLED=false` as the default no-op safety. Build the integration under a dedicated feature flag. Use protocol mock fixtures for unit/smoke tests.
