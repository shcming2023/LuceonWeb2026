# CleanService Mineru2Table Adaptation Plan

Status: Accepted docs-level architecture planning document for future external dependency work; no runtime implementation or production activation
Last updated: 2026-05-20
Historical owner: Architect; role retired after 6.9.1
External repository: `shcming2023/Mineru2Table2026`

---

## 1. Boundary

This document describes how `shcming2023/Mineru2Table2026` must be adapted to align with `docs/contracts/CleanService-Protocol-v1.md` prior to executing a production-level integration in Luceon2026.

It does not implement or verify Mineru2Table changes. It does not authorize Luceon runtime, production, Docker, DB, MinIO, MinerU, Ollama, or source-code changes.

---

## 2. Target Role

Mineru2Table2026 is designated as the first Clean Material preparation service (Stage 1 structure rebuild):

| Field | Target |
| --- | --- |
| `service_name` | `toc-rebuild` |
| Primary input | MinerU `content_list_v2.json` by MinIO ObjectRef |
| Primary output | rebuilt TOC / anchor structure |
| Output bucket | `eduassets-clean` |
| Output prefix | `toc-rebuild/{materialId}/{assetVersion}/` |
| Protocol | `CleanService Protocol v1` |

Luceon remains the orchestrator and owns `materialId`, `parseTaskId`, `assetVersion`, job submission, review, audit, cost decisions, and task state. The outputs of this service, along with the original Raw Material, will be consumed by the subsequent `RawMaterial2CleanMaterial` stage to produce the final Clean Material.

---

## 3. Current Audited Gaps & Transition Strategy

A technical fact audit performed on 2026-05-20 against the `shcming2023/Mineru2Table2026` repository has revealed that **over 90% of the CleanService Protocol v1 specification is already natively implemented** (including MinIO storage allowlisting, ObjectRef-based async `/api/v1/jobs` endpoints, atomic state persistence, and signed HMAC-SHA256 callbacks).

The remaining compliance gaps have been narrowed down to **three precise technical fixes** in the external Mineru2Table repository, and **one orchestrator implementation** on the Luceon side.

### 3.1 Transition Strategy & Recommendation Matrix

| Option | Description | Pros | Cons | Recommendation |
| --- | --- | --- | --- | --- |
| **Option A (Lucode Recommended / Candidate for Luceon approval)** | **Direct Protocol Alignment**: Modify the external Mineru2Table service codebase directly to fix the remaining artifact and exception gaps (rename stats, upload unresolved anchors, add temp-file cleanup, fix allowlist exception class). | • Zero double-copy overhead.<br>• Native, compliant provenance.<br>• Cleanest long-term service architecture. | • Requires minor Python file changes in the external repo. | **Highly Recommended**. This is the recommended candidate transition strategy for stable integration pending final Luceon approval. |
| **Option B (Rejected)** | **Luceon-Side Multipart Adapter**: Luceon's worker downloads MinIO files, creates a multipart HTTP request to Mineru2Table's deprecated `/api/v1/tasks`, and downloads results back. | • No changes in Mineru2Table codebase. | • High network/disk bottleneck.<br>• Risk of silent failure.<br>• Volatile provenance lineage. | **Strictly Rejected**. Not safe for production due to network overhead and lack of storage isolation. |
| **Option C (Deprecated)** | **Hybrid Local Sidecar Adapter**: Deploy a local proxy next to Mineru2Table that exposes Protocol v1 and translates it internally to the deprecated multipart API. | • Permitted only for early prototyping. | • Deprecated by the emergence of native Protocol v1 support in Mineru2Table. | **Deprecated**. Shifting exclusively to Option A. |

---

## 4. Required External Code Alignments (Mineru2Table Repo)

The following surgical modifications are required in `shcming2023/Mineru2Table2026` to achieve 100% compliance:

### M-1. Artifact Compliance and Renaming (Gap Fix)
- **File**: `src/core/jobs/runner.py`
- **Correction 1 (Metrics)**: Rename the generated metadata artifact role and filename from `token_stats.json` (role `token_stats`) to `metrics.json` (role `metrics`).
- **Correction 2 (Unresolved Anchors)**: Generate `unresolved_anchors.json` (even if empty `[]` when no unresolved anchors exist) and upload it to the output prefix, satisfying the Seven-File Target Output Contract.

### M-2. Disk Cleanup Hygiene (Gap Fix)
- **File**: `src/core/jobs/runner.py`
- **Correction**: Wrap the runner pipeline in a `try...finally` block, ensuring that `shutil.rmtree(temp_dir, ignore_errors=True)` is explicitly called at the end of job execution to delete temporary directories under `/tmp/mineru2table_{job_id}` and prevent disk saturation.

### M-3. Environmental Configuration Unification
- Ensure the Docker deployment environment correctly exposes and mounts:
  - `JOB_STORE_PATH` pointing to a writable, persistent JSON path (e.g. `/app/data/jobs.json`).
  - `API_KEY` for secure ingress control.
  - `ALLOWED_MINIO_ENDPOINTS`, `ALLOWED_INPUT_BUCKETS`, and `ALLOWED_OUTPUT_BUCKETS` to maintain storage access isolation.

### M-4. Allowlist Exception Mapping Alignment (Gap Fix)
- **File**: `src/core/storage/minio_backend.py`
- **Correction**: Change the exception raised during allowlist validation from the built-in Python `PermissionError` to the project's custom `StoragePermissionError`. This ensures the background job runner's try-except block can correctly catch it and return the protocol-compliant `forbidden_storage_target` error payload (HTTP 403) instead of leaking a generic HTTP 500 error.

---

## 5. Luceon-Side Integration Expectations

Prior to wiring the integration into production pipelines, the Luceon project must verify:

1. **Protocol-Compliant API Client**: Implement a mock-safe API bridge inside `cleanservice-worker.mjs` strictly utilizing the `/api/v1/jobs` endpoints.
2. **Signature Verification**: Implement signature validation on the webhook callback route in `upload-server.mjs` to cryptographically verify terminal state notifications using HMAC-SHA256.
3. **Safety Isolation**: Ensure the `CLEANSERVICE_ENABLED=false` default state is preserved. All testing and prototyping must operate under mock environments or developer sandbox flags.
