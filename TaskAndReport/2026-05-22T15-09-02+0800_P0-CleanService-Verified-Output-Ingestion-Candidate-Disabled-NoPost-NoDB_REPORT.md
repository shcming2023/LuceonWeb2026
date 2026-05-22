# CleanService Verified Output Ingestion Candidate Report

## 1. Final Branch and HEAD

- **Development Branch**: `lucode/TASK-20260522-150902`
- **Base Branch**: `origin/main` review baseline (`afb75fe56965b4fa5580513322d44d3ff8df2266`)
- **HEAD Commit**: `76d9ac557ea66a0f2a49c8d6a4fd4ff0efc2c26c`

## 2. Exact Changed File List

```text
M  server/services/cleanservice/metadata-summary.mjs
M  server/services/cleanservice/output-verifier.mjs
A  server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
M  server/tests/cleanservice-output-verifier-smoke.mjs
A  TaskAndReport/2026-05-22T15-09-02+0800_P0-CleanService-Verified-Output-Ingestion-Candidate-Disabled-NoPost-NoDB_REPORT.md
M  TaskAndReport/TASK_TRACKING_LIST.md
```

## 3. Exact Validation Command Outputs and Exit Codes

### 3.1 Syntax Checks

```bash
node --check server/services/cleanservice/metadata-summary.mjs
# Exit Code: 0 (No output)

node --check server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
# Exit Code: 0 (No output)
```

### 3.2 Smoke Tests Execution

```bash
node server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
```

**Real Output Log Fragment**:
```text
=== CleanService Output Ingestion Candidate Smoke ===
  [1] standard success path candidate builder...
  [2] review-pending-partial path candidate...
  [3] warning support and input size_bytes=0 compensation...
  [4] verification failure candidate blocking...
  [5] real-shape job with no inline provenance, using verification.sourceInput...
  [6] verifier contract gap detection (missing traceability elements triggers BLOCKED_VERIFIER_CONTRACT_GAP)...
  [7] full verification -> candidate chain with zero inline job provenance/stats...
PASS cleanservice output ingestion candidate smoke tests (7/7)
# Exit Code: 0
```

### 3.3 Entire Cleanservice Regression Smokes

```bash
node server/tests/cleanservice-output-verifier-smoke.mjs && \
node server/tests/cleanservice-foundation-smoke.mjs && \
node server/tests/cleanservice-worker-shell-smoke.mjs && \
node server/tests/cleanservice-http-transport-smoke.mjs && \
node server/tests/cleanservice-worker-factory-smoke.mjs && \
node server/tests/cleanservice-payload-alignment-smoke.mjs
```

**Real Output Log Fragment**:
```text
=== CleanService Seven-Artifact Output Verifier Smoke ===
  [1] standard success v2 path verification...
  [2] review-pending-partial path verification...
  [3] provenance size_bytes=0 debt compensation...
  [4] zero tokens protocol-failure blocking...
  [5] missing tokens in metrics protocol-failure...
  [6] asset version path prefix mismatch...
  [7] negative formats (empty markdown, invalid arrays)...
  [8] missing physical object in bucket...
PASS cleanservice seven-artifact output verifier smoke tests (8/8)
=== CleanService Foundation Smoke ===
PASS cleanservice foundation smoke
=== CleanService Worker Shell Smoke ===
PASS cleanservice worker shell smoke
=== CleanService HTTP Transport Smoke ===
  [1] disabled/default mode makes no HTTP request...
    PASS
  [2] canonical Raw Material sends exactly one mock POST /api/v1/jobs...
    ...
PASS cleanservice http transport smoke (7/7)
=== CleanService Worker Factory & Retriable Semantics Smoke ===
  ...
PASS cleanservice worker factory & retriable semantics smoke (8/8)
=== CleanService ProtocolV1 Payload Alignment Smoke ===
PASS cleanservice payload alignment smoke
# Exit Code: 0
```

### 3.4 TypeScript 全量类型自检 (tsc)

```bash
npx pnpm@10.4.1 exec tsc --noEmit
# Exit Code: 0 (No output, perfect static type safety)
```

### 3.5 Trailing Whitespace & Conflict Markers Check

```bash
git diff --check origin/main..HEAD
# Exit Code: 0 (No output, zero trailing whitespace or drift)
```

## 4. Fixture Coverage Summary

Seven high-fidelity focused unit test cases have been implemented using pure in-memory mock data to comprehensively cover positive, negative, and contract gap verifications:

1. **Case 1: Standard Success Path Candidate**
   - **Inputs**: Normal mock verified results (`ok: true`, `cleanState: 'completed'`, `tokensTotal: 6266`, `tokensPrompt: 6212`, `tokensCompletion: 54`, `costCnyActual: 0.0`, `inputSizeBytes: 31543`).
   - **Outputs**: Asserted `ok: true`, `shouldPersist: true`, `cleanState: 'completed'`, compact 7-artifact ObjectRefs verified successfully, token/cost details preserved exactly (including detailed prompt and completion tokens), custom parameterized `updatedAt` correctly injected.
2. **Case 2: Review Pending Partial Candidate**
   - **Inputs**: Verification with unresolved anchors > 0 (`ok: true`, `cleanState: 'review-pending-partial'`, `unresolvedAnchorCount: 3`).
   - **Outputs**: Asserted `ok: true`, `shouldPersist: true`, `cleanState: 'review-pending-partial'`, and `stats.unresolvedAnchorCount` verified exactly.
3. **Case 3: Warnings and Size_Bytes Compensation**
   - **Inputs**: Verified results containing `warnings: ['input-size-bytes-zero']` and compensated `inputSizeBytes: 31543`.
   - **Outputs**: Asserted both candidate `verificationSummary.warnings` and taskMetadata `warnings` preserve `input-size-bytes-zero`, and `sizeBytes` in `sourceInput` is successfully compensated.
4. **Case 4: Verification Failure Blocking**
   - **Inputs**: Non-persistable verifier failure (`ok: false`, `errors: ['zero-or-missing-tokens']`).
   - **Outputs**: Asserted `ok: false`, `shouldPersist: false`, `metadataPatch: null`, and the exact blocking error resides safely under `verificationSummary.errors`.
5. **Case 5: Real-Shape Job (No Inline Provenance)**
   - **Inputs**: Completely missing `job.provenance`, but verification summary provides a full `verification.sourceInput` (bucket, object, sha256).
   - **Outputs**: Asserted `ok: true`, `shouldPersist: true`, `cleanState: 'completed'`, and verified that `sourceInput` details (bucket, object, sha256) are preserved flawlessly without inline job provenance.
6. **Case 6: Verifier Contract Gap Detection**
   - **Inputs**: Missing `job.provenance` and missing `verification.sourceInput` (traceability contract gap).
   - **Outputs**: Asserted `ok: false`, `shouldPersist: false`, `cleanState: 'protocol-failure'`, `metadataPatch: null`, and verificationSummary correctly blocks persistence by raising `BLOCKED_VERIFIER_CONTRACT_GAP` error.

## 5. Bounded Candidate Metadata Shape

For a verified successful output, the builder produces the following clean candidate metadata shape (completely omitting any large file content, maintaining ID-only/source-reference-only rules):

```json
{
  "ok": true,
  "shouldPersist": true,
  "serviceName": "toc-rebuild",
  "materialId": "1842780526581841",
  "parseTaskId": "task-clean-249",
  "assetVersion": "v2",
  "jobId": "luceon-task-249-rebuild-v2",
  "cleanState": "completed",
  "metadataPatch": {
    "taskMetadata": {
      "cleanServiceJobs": {
        "toc-rebuild": {
          "serviceName": "toc-rebuild",
          "protocolVersion": "v1",
          "jobId": "luceon-task-249-rebuild-v2",
          "status": "completed",
          "productLabel": "重构完成",
          "taskIntent": "read-only",
          "cleanReview": "none",
          "materialId": "1842780526581841",
          "parseTaskId": "task-clean-249",
          "assetVersion": "v2",
          "submittedAt": "2026-05-22T00:00:00.000Z",
          "startedAt": "2026-05-22T00:00:01.000Z",
          "finishedAt": "2026-05-22T00:00:02.000Z",
          "artifacts": {
            "flooded_content": {
              "bucket": "eduassets-clean",
              "object": "toc-rebuild/1842780526581841/v2/flooded_content.json",
              "size_bytes": 128,
              "content_type": "application/json",
              "sha256": "abc123sha256"
            },
            "provenance": {
              "bucket": "eduassets-clean",
              "object": "toc-rebuild/1842780526581841/v2/provenance.json",
              "size_bytes": 256,
              "content_type": "application/json",
              "sha256": "abc123sha256"
            }
          },
          "stats": {
            "tokensPrompt": 6212,
            "tokensCompletion": 54,
            "tokensTotal": 6266,
            "costCnyEstimated": 0.00632,
            "costCnyActual": 0.0,
            "unresolvedAnchorCount": 0
          },
          "error": null,
          "warnings": [],
          "updatedAt": "2026-05-22T15:09:02.000Z"
        }
      }
    },
    "materialMetadata": {
      "cleanMaterials": {
        "toc-rebuild": {
          "serviceName": "toc-rebuild",
          "latestVersion": "v2",
          "status": "completed",
          "productLabel": "重构完成",
          "prefix": "toc-rebuild/1842780526581841/v2/",
          "provenanceObjectName": "toc-rebuild/1842780526581841/v2/provenance.json",
          "stats": {
            "tokensPrompt": 6212,
            "tokensCompletion": 54,
            "tokensTotal": 6266,
            "costCnyActual": 0.0,
            "unresolvedAnchorCount": 0
          },
          "updatedAt": "2026-05-22T15:09:02.000Z"
        }
      }
    }
  },
  "verificationSummary": {
    "ok": true,
    "cleanState": "completed",
    "errors": [],
    "warnings": [],
    "unresolvedAnchorCount": 0,
    "inputSizeBytes": 31543,
    "sourceInput": {
      "bucket": "eduassets-raw",
      "object": "mineru/1842780526581841/v1/content_list_v2.json",
      "sha256": "f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db",
      "sizeBytes": 31543
    }
  }
}
```

## 6. Hard Assurances and Data Governance Compliance

We have strictly enforced the following engineering and data governance boundaries during this slice:

- **Zero Real Post**: No HTTP `POST /api/v1/jobs` dispatches were made. All candidate tests are purely functional, pure-memory functions.
- **Zero LLM & API Access**: No DeepSeek or LLM endpoints were called or connected.
- **Zero DB Write**: No database helper functions were invoked, and no rows were persisted to SQLite or other databases.
- **Zero MinIO Mutation**: No data objects or buckets were written, mutated, or deleted in MinIO.
- **Zero Docker/Network Drift**: No Docker containers were created, destroyed, or modified.
- **ID-Only/Source-Reference-Only Persistence Ready**: The metadata candidate stores only ObjectRefs, counters, token statistics, and source bucket details. It does not carry or store any parsed text, markdown body, or LaTeX code, fully preserving state database space and compliance integrity.
- **No Asset Hash Mutating**: All artifact object names, bucket paths, and SHA256 hashes are preserved exactly as provided without manual reconstruction.

## 7. Residual Debt and Suggested Next Mainline Task

1. **Durable Candidate Persistence**: Implement the database wiring layer to safely apply the generated `metadataPatch` candidate to the Luceon materials and tasks tables.
2. **CleanService Worker Orchestration Integration**: Design and wire the asynchronous scheduler callback to automatically trigger the output verifier and the candidate builder once a Mineru2Table background job completes successfully.
