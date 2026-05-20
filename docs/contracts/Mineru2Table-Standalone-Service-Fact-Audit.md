# Mineru2Table Standalone Service Fact Audit

- **Document Target**: technical fact freeze of the deployed Mineru2Table standalone service based on the direct repository code analysis (`shcming2023/Mineru2Table2026`).
- **Audit Date**: 2026-05-20
- **Auditor**: `Lucode`

---

## 1. Executive Summary

A deep read-only inspection of the cloned `shcming2023/Mineru2Table2026` repository and verification of the local runtime environment have been completed. The audit has revealed a **major, positive shift** in the latest upstream standalone service codebase (`7e9e592`), but also a **critical status mismatch** and design flaws in the current local deployment:

1. **Upstream Source Capability**: Contrary to historical assumptions, the latest upstream standalone service codebase **has already natively implemented over 90% of the CleanService Protocol v1 specification**, including ObjectRef async jobs, atomicity-driven disk storage persistence, HMAC-SHA256 callback webhooks, and MinIO storage isolation controls.
2. **Current Local Deployment State**: The local container currently running (`mineru2table-api`) is built from an older state (HEAD `43754fa`). It does **NOT** expose Protocol v1 endpoints (`/api/v1/jobs` etc.), and only supports legacy synchronous/asynchronous multipart routes.
3. **Critical Storage Allowlist Gap**: While upstream implements bucket-level isolation, a code exception type mismatch exists: `minio_backend.py` raises `PermissionError` but `runner.py` catches `StoragePermissionError`. This makes storage allowlist violations fall through to a generic HTTP 500 error instead of the compliant `forbidden_storage_target` HTTP 403 response.
4. **Artifact & Hygiene Gaps**: Missing `unresolved_anchors.json`, misaligned `metrics.json` naming, and temporary file leakages persist in upstream runner.

These gaps must be frozen in this document as candidates for future Luceon review and external codebase alignment.

---

## 2. API Route & Runtime Reality: Deployed vs. Upstream Source

To ensure absolute fact accuracy, we must strictly separate the **Current Local Deployment State** from the **Upstream Remote Source Codebase State**.

### 2.1 Current Local Deployment State (HEAD `43754fa`)

The local environment running `mineru2table-api` at port `8000` is in an older state:
1. **`GET /health`**
   - Returns: `{"status":"healthy","version":"1.0.0","llm_status":"not_configured"}`
2. **`POST /api/v1/extract`**
   - Supported (Synchronous legacy multipart)
3. **`POST /api/v1/tasks`** & **`GET /api/v1/tasks/{task_id}`**
   - Supported (Asynchronous legacy multipart)
4. **`POST /api/v1/jobs`** & **`GET /api/v1/jobs/{job_id}`** (Protocol v1)
   - **NOT Supported / Missing**. Calling these returns HTTP 404.

*Conclusion: The current local deployment is purely in the legacy multipart generation and is NOT ready for Protocol v1.*

### 2.2 Upstream Remote Source Codebase State (HEAD `7e9e592`)

A read-only inspection of the cloned `shcming2023/Mineru2Table2026` repository shows that the `api_server.py` source code has implemented two distinct generations of endpoints:

#### 2.2.1 CleanService Protocol v1 Endpoints (Active Target in Upstream)
1. **`GET /health`**
   - **Behavior**: Dynamically audits environment variables (`DEEPSEEK_API_KEY`, `MINIO_ACCESS_KEY`, etc.). If any required variable is missing, it returns `"status": "unhealthy"`.
2. **`POST /api/v1/jobs`** & **`POST /api/v1/jobs:from-storage`**
   - **Function**: Asynchronous Job submission using MinIO ObjectRefs.
   - **Idempotency**: Checked against the database store (`JobStore`). If a matching `job_id` exists, it returns HTTP 200 with the existing state; otherwise, it spawns a background `threading.Thread` to execute the pipeline and returns HTTP 202.
3. **`GET /api/v1/jobs/{job_id}`**
   - **Function**: Fetches the state of a queued/processing/completed/failed job.

#### 2.2.2 Deprecated Legacy Multipart Endpoints (Sunset Target: v1.2.0 in Upstream)
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

### 3.2 MinIO Storage Backend & Security: The Allowlist Exception Gap
- **File**: `src/core/storage/minio_backend.py`
- **Fact**: Direct bucket-level authorization controls are designed in the upstream source.
- **Isolate Policies**:
  - Requires `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` from the environment.
  - Enforces `ALLOWED_MINIO_ENDPOINTS`, `ALLOWED_INPUT_BUCKETS` (default `eduassets-raw`), and `ALLOWED_OUTPUT_BUCKETS` (default `eduassets-clean`) allowlists.
- **The Code Defect / Gap**:
  - In `minio_backend.py`, when a job request targets an endpoint or bucket outside the allowlist, the backend throws a Python built-in `PermissionError`.
  - In `src/core/jobs/runner.py` (which executes the background thread), the code wraps execution in a try-except block but specifically catches `StoragePermissionError` to return the `forbidden_storage_target` code (HTTP 403).
  - Because `PermissionError` is **not** a subclass of `StoragePermissionError`, this exception is **never** caught by the designated handler. Instead, it propagates up to the global handler, falling back to a generic `processing_failed_permanent` (HTTP 500) failure.
  - **Conclusion**: This is a **Non-compliant Gap** in error semantics. The allowlist mechanism fails to return the protocol-compliant `forbidden_storage_target` error.
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
| **`forbidden_storage_target`** | **Diverged Error** | **Exception GAP** | The runner fails to map allowlist violations to `forbidden_storage_target` due to `PermissionError` vs. `StoragePermissionError` mismatch. <br>**Corrective Action**: Modify `minio_backend.py` to raise `StoragePermissionError` instead of built-in `PermissionError`. |

### 4.3 Cleanup Hygiene Gap
- **Fact**: Local temp-files downloaded/generated during runner execution (stored under `/tmp/mineru2table_{job_id}/`) **are never deleted** after successful or failed execution.
- **Corrective Action**: The runner must wrap its core logic in a `finally` block and call `shutil.rmtree(temp_dir, ignore_errors=True)` to prevent host filesystem saturation.

---

## 5. Responsibility Split Matrix

| Requirement | Current Mineru2Table | Luceon Target | Owner | Next Action |
| --- | --- | --- | --- | --- |
| **API/Jobs Endpoints** | Implemented in remote `7e9e592`; **Absent in local `43754fa`** | Comply with v1 | **Mineru2Table service** | Deploy the latest remote codebase (`7e9e592`) to local environment to enable Protocol v1. |
| **Job Persistence** | Implemented in remote `7e9e592` (`JOB_STORE_PATH`) | Persistent | **Mineru2Table service** | Config environment variables at deployment. |
| **API Auth Header** | Implemented (`X-API-Key`) | Authorized Ingress | **Mineru2Table service** | Supply `API_KEY` to Docker environment. |
| **HMAC Callbacks** | Implemented in remote `7e9e592` | Signed callback | **Mineru2Table service** | Deploy `7e9e592` to local environment. Luceon callback server must verify signature. |
| **Unresolved Anchors** | Absent in remote `7e9e592` | `unresolved_anchors.json` | **Mineru2Table service** | **Code modification required** in external repo to upload file. |
| **Metrics Artifact** | Written as `token_stats.json` | `metrics.json` | **Mineru2Table service** | **Code modification required** in external repo to rename role and file. |
| **Temporary Cleanup** | Leaked under `/tmp` | Automatic cleanup | **Mineru2Table service** | **Code modification required** in runner `finally` block. |
| **Allowlist Exception Mapping** | **Non-compliant Gap** (Throws `PermissionError`) | `forbidden_storage_target` | **Mineru2Table service** | **Code modification required** in `minio_backend.py` to raise `StoragePermissionError`. |
| **Orchestration Bridge** | Disabled-noop | Feature-flagged Bridge | **Luceon main project** | Implement mock-safe Protocol v1 integration under `CleanServiceWorker`. |

---

## 6. Safe Transition Sequence Recommendation (Lucode Recommended / Candidate for Luceon Approval)

Based on this audit, **Option A (Direct Protocol Alignment Candidate)** is highly recommended by Lucode as the candidate transition path for Luceon approval. Since the remote Mineru2Table codebase already implements 90% of the v1 protocol, we suggest executing the final adaptations in three parallel phases:

### Phase 1: Minor External Code Alignment (Mineru2Table Repo)
The owner of the `shcming2023/Mineru2Table2026` repository must perform surgical edits:
1. **[runner.py]** Modify the artifact upload section to write `metrics.json` instead of `token_stats.json`.
2. **[runner.py]** Add a basic parser to record unresolved anchors (or write `[]` if none) and write them to `unresolved_anchors.json`.
3. **[runner.py]** Wrap processing in a `finally` block to perform `shutil.rmtree()` on `/tmp/mineru2table_{job_id}`.
4. **[minio_backend.py]** Fix the Exception Gap by changing the allowlist validation error from `PermissionError` to `StoragePermissionError`.
5. Push a new tag/commit and tag it (e.g. `v1.1.0`).

### Phase 2: Local Deployment Alignment (Local mineru2table-api Container)
Prior to any orchestrator integration, the local running container must be rebuilt/redeployed using the updated remote codebase (`7e9e592` or later) to resolve the OpenAPI endpoint gap:
1. Pull the latest code of the standalone service in the dev workspace environment.
2. Rebuild the `mineru2table-api` image and restart the container.
3. Verify that `/health` return indicates readiness and that `/api/v1/jobs` is reachable.

### Phase 3: Luceon Integration Bridge (Luceon Main Project)
Once the above are validated and Option A is formally approved by Luceon, the main project can build a mock-safe API Bridge:
1. Implement `CleanServiceWorker` interactions strictly calling `POST /api/v1/jobs` and `GET /api/v1/jobs/{job_id}`.
2. Wire up the callback webhook handler in `upload-server.mjs` to receive terminal state notifications, strictly verifying the HMAC-SHA256 signature against the shared secret.
3. Keep `CLEANSERVICE_ENABLED=false` as the default no-op safety. Build the integration under a dedicated feature flag. Use protocol mock fixtures for unit/smoke tests.
