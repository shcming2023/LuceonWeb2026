# Luceon CleanService Controlled Failure-Mode Loopback Dispatch Report

## 1. Execution Dossier Info

- **Date**: 2026-05-21
- **Branch**: `lucode/task-231-controlled-failure-dispatch`
- **Exact HEAD**: `1ccd21649a9e32dc963423ecc5c5c17a98a245ef`
- **POST Sent**: `no`
- **Job ID Created**: `N/A (Blocked before POST)`
- **Total POST Count**: `0`
- **Final Classification**: `BLOCKED_PAYLOAD_SCHEMA_GAP`

---

## 2. Preflight Gate Validation Results

### Gate A: Loopback Ingress Verification
- **Command Run**: `docker inspect mineru2table-api`
- **Observed Binding**: `127.0.0.1:8000->8000/tcp` (Host port is strictly bound to loopback `127.0.0.1`).
- **Container Network Status**: Healthy, running `uvicorn api_server:...`.
- **Precondition Status**: **PASS**

### Gate B: Dependency Blank Matrix Verification
- **Endpoint Inspected**: `/health` via `http://host.docker.internal:8000/health`
- **Observed Status Payload**:
  ```json
  {
    "status": "unhealthy",
    "service_name": "toc-rebuild",
    "service_version": "1.0.0",
    "protocol_version": "v1",
    "checks": {
      "minio": "unconfigured",
      "llm": "not_configured",
      "dependencies": "ok"
    },
    "timestamp": "2026-05-21T05:31:08.847446Z"
  }
  ```
- **Masked Env Check (inside `mineru2table-api` container)**:
  - `MINIO_ACCESS_KEY`: `empty`
  - `MINIO_SECRET_KEY`: `empty`
  - `DEEPSEEK_API_KEY`: `empty`
  - `TOC_REBUILD_CALLBACK_SECRET`: `empty`
- **Precondition Status**: **PASS** (Dependencies are confirmed 100% unconfigured and blank).

### Gate C: OpenAPI Schema Gate & Payload Comparison
- **Downstream `/openapi.json` Requirement**:
  - `JobSubmitRequest` requires: `['job_id', 'material_id', 'parse_task_id', 'asset_version', 'inputs', 'sink', 'submitted_at', 'submitted_by']`.
  - `SourceRef` (inside `inputs[0].source`) requires: `['type', 'endpoint', 'use_ssl', 'bucket', 'object']`.
  - `SinkRef` (inside `sink`) requires: `['type', 'endpoint', 'use_ssl', 'bucket', 'prefix']`.
- **Luceon Core `buildCleanServiceJobRequest()` Payload Output**:
  ```json
  {
    "job_id": "luceon-optionb-mock-parse-task-toc-rebuild-v1",
    "material_id": "optionb-mock-material",
    "parse_task_id": "optionb-mock-parse-task",
    "asset_version": "v1",
    "inputs": [
      {
        "role": "mineru-content",
        "source": {
          "type": "minio",
          "bucket": "eduassets-raw",
          "object": "mineru/optionb-mock-material/v1/content_list_v2.json"
        },
        "hash": "mock-sha256-hash-value-1234567890abcdef"
      }
    ],
    "sink": {
      "type": "minio",
      "bucket": "eduassets-clean",
      "prefix": "toc-rebuild/optionb-mock-material/v1/"
    },
    "callback_secret_ref": "TOC_REBUILD_CALLBACK_SECRET",
    "options": {
      "max_cost_cny": 8
    }
  }
  ```
- **Schema Validation Gaps Discovered**:
  - `[FAIL] Mismatch at "root": missing required field "submitted_at"`
  - `[FAIL] Mismatch at "root": missing required field "submitted_by"`
  - `[FAIL] Mismatch at "inputs[0].source.": missing required field "endpoint"`
  - `[FAIL] Mismatch at "inputs[0].source.": missing required field "use_ssl"`
  - `[FAIL] Mismatch at "sink.": missing required field "endpoint"`
  - `[FAIL] Mismatch at "sink.": missing required field "use_ssl"`
- **Precondition Status**: **FAIL (BLOCKED_PAYLOAD_SCHEMA_GAP)**

---

## 3. Job-Store Baseline Verification

- **Storage File Path**: `/workspace/ops/Mineru2Tables/data/jobs.json`
- **Baseline File Stats**:
  - **Size**: `2` bytes
  - **Contents**: `{}` (completely empty database)
  - **Job Count**: `0`
- **Post-Preflight Delta**:
  - **Mutation Delta**: `0` bytes / records (No write occurred due to strict block before POST).

---

## 4. Execution Logic & STOP Rule Trigger

As mandated by Task 231 rules, we must stop immediately if the schema gate fails before POST.
No HTTP `POST` was sent to `http://host.docker.internal:8000/api/v1/jobs`. No source code modifications were performed in `Luceon2026` workspace.
The dispatch boundary has been safely guarded against malformed requests.

---

## 5. Risk Assessment & Recommendations

1. **Protocol v1 Interface Gap**:
   Luceon's `buildCleanServiceJobRequest` in `cleanservice-worker.mjs` and the raw material canonical adapter are completely missing required metadata fields (`submitted_at`, `submitted_by`) and infrastructure mapping credentials (`endpoint`, `use_ssl`) for both `inputs` and `sink` structures.
2. **Next Steps**:
   Luceon control plane (`luceon` actor) must review this gap and decide on how to update the Luceon-side generation code or standard contracts to align the schemas in future tasks.
