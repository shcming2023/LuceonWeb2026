# Task Report: CleanService ProtocolV1 JobSubmitRequest Payload Alignment

## 1. Environment & Branch Context

- **Workspace Path**: `/workspace/dev/Luceon2026`
- **Active Branch**: `lucode/task-232-payload-alignment`
- **Execution Target**: Task 232 (`TASK-20260521-134732-P0-CleanService-ProtocolV1-JobSubmitRequest-Payload-Alignment`)

## 2. Changed Files

- `[MODIFY] [config.mjs](file:///workspace/dev/Luceon2026/server/services/cleanservice/config.mjs)`
  > Added `storageEndpoint` (default `'minio:9000'`), `storageUseSsl` (default `false`), and `submittedBy` (default `'luceon2026/cleanservice-worker'`) load parameters from environment.
- `[MODIFY] [cleanservice-worker.mjs](file:///workspace/dev/Luceon2026/server/services/cleanservice/cleanservice-worker.mjs)`
  > Updated `buildCleanServiceJobRequest` signature and payload structure to output all required missing schema fields (`submitted_at`, `submitted_by`, `endpoint`/`use_ssl` for both `inputs[0].source` and `sink`). Also updated `CleanServiceWorker.tickOnce()` to pass the deterministic `observedAt` time as `submittedAt` option.
- `[NEW] [cleanservice-payload-alignment-smoke.mjs](file:///workspace/dev/Luceon2026/server/tests/cleanservice-payload-alignment-smoke.mjs)`
  > Created a new focused payload contract validation test to verify that the generated payload complies with the live OpenAPI schema required fields, ensuring default fields and deterministic configuration.

## 3. Payload Contract Alignment (Before/After Excerpts)

Below is a comparison of the generated job submit payload before and after this task's implementation:

### Before Alignment (Task 231 Blocked Schema Shape)
```json
{
  "job_id": "luceon-task-clean-1-toc-rebuild-v1",
  "material_id": "mat-clean-1",
  "parse_task_id": "task-clean-1",
  "asset_version": "v1",
  "inputs": [
    {
      "role": "mineru-content",
      "source": {
        "type": "minio",
        "bucket": "eduassets-raw",
        "object": "mineru/mat-clean-1/v1/content_list_v2.json"
      }
    }
  ],
  "sink": {
    "type": "minio",
    "bucket": "eduassets-clean",
    "prefix": "toc-rebuild/mat-clean-1/v1/"
  },
  "callback_secret_ref": "TOC_REBUILD_CALLBACK_SECRET",
  "options": {
    "max_cost_cny": 8
  }
}
```

### After Alignment (Task 232 Schema Compliant Shape)
```json
{
  "job_id": "luceon-task-clean-1-toc-rebuild-v1",
  "material_id": "mat-clean-1",
  "parse_task_id": "task-clean-1",
  "asset_version": "v1",
  "submitted_at": "2026-05-21T14:00:00.000Z",
  "submitted_by": "luceon2026/cleanservice-worker",
  "inputs": [
    {
      "role": "mineru-content",
      "source": {
        "type": "minio",
        "bucket": "eduassets-raw",
        "object": "mineru/mat-clean-1/v1/content_list_v2.json",
        "endpoint": "minio:9000",
        "use_ssl": false
      }
    }
  ],
  "sink": {
    "type": "minio",
    "bucket": "eduassets-clean",
    "prefix": "toc-rebuild/mat-clean-1/v1/",
    "endpoint": "minio:9000",
    "use_ssl": false
  },
  "callback_secret_ref": "TOC_REBUILD_CALLBACK_SECRET",
  "options": {
    "max_cost_cny": 8
  }
}
```

## 4. Test Verification Results

We verified that the contract alignment does not regress any mock worker factory or transport logic, and all tests run in complete safety:

### Smokes Executed
```bash
for f in server/tests/cleanservice-*.mjs; do node "$f"; done
```
Output Logs:
```text
Running server/tests/cleanservice-asset-version-smoke.mjs...
=== Asset Version Allocator Smoke ===
PASS asset version allocator smoke
Running server/tests/cleanservice-foundation-smoke.mjs...
=== CleanService Foundation Smoke ===
PASS cleanservice foundation smoke
Running server/tests/cleanservice-http-transport-smoke.mjs...
=== CleanService HTTP Transport Smoke ===
  [1] disabled/default mode makes no HTTP request... PASS
  [2] canonical Raw Material sends exactly one mock POST /api/v1/jobs... PASS
  [3] legacy parsed-only skipped-policy makes no HTTP request... PASS
  [4] mock 4xx response is recorded as explicit dispatch failure... PASS
  [5] mock 5xx response is recorded as explicit failure with retriable... PASS
  [6] timeout/network failure is bounded and reported... PASS
  [7] no test calls real 127.0.0.1:8000... PASS
PASS cleanservice http transport smoke (7/7)
Running server/tests/cleanservice-payload-alignment-smoke.mjs...
=== CleanService ProtocolV1 Payload Alignment Smoke ===
PASS cleanservice payload alignment smoke
Running server/tests/cleanservice-raw-material-adapter-smoke.mjs...
=== Raw Material Adapter Smoke ===
PASS raw material adapter smoke
Running server/tests/cleanservice-worker-factory-smoke.mjs...
=== CleanService Worker Factory & Retriable Semantics Smoke ===
  [1] disabled/default factory path makes zero HTTP requests... PASS
  [2] enabled mock factory path submits exactly one POST /api/v1/jobs... PASS
  [3] missing endpoint makes zero HTTP requests and reports explicit failure... PASS
  [4] legacy parsed-only task makes zero HTTP requests... PASS
  [5] 4xx result is non-retriable at normalized client result... PASS
  [6] 5xx result is retriable at normalized client result... PASS
  [7] timeout remains retriable at normalized client result... PASS
  [8] no test targets 127.0.0.1:8000... PASS
PASS cleanservice worker factory & retriable semantics smoke (8/8)
Running server/tests/cleanservice-worker-shell-smoke.mjs...
=== CleanService Worker Shell Smoke ===
PASS cleanservice worker shell smoke
```

### TypeScript Validation
```bash
npx pnpm@10.4.1 exec tsc --noEmit
```
- **Exit Code**: `0` (Success, no errors)

### Git Diff Syntax & Whitespace Check
```bash
git diff --check origin/main..HEAD
```
- **Exit Code**: `0` (Success, no trailing whitespace)

---

## 5. Security & Red-Line Commitments

- **No Real HTTP Dispatch**: Verified that no real `POST /api/v1/jobs` requests were made to `127.0.0.1:8000`. All transport smokes were executed against local, ephemeral mock HTTP servers.
- **No State Mutation**: No database, MinIO objects, LLM endpoints, Docker metadata, or container volumes were altered or configured.
- **Credentials Isolation**: endpoint and bucket names mapped to non-sensitive default parameters only. No real or secret credentials were included in any request payloads or test environments.
- **Disabled-by-Default / Legacy Intact**: Verified that legacy parsed-only objects still transition to `skipped-policy` naturally, and `CLEANSERVICE_ENABLED` defaults to `false`.

---

## 6. Residual Risks & Next Action

- **Task 231 Option B Re-Authorization**: Option B real loopback dispatch may be retried only after:
  1. Luceon successfully merges this payload contract alignment.
  2. The Director-authorized failure-mode loopback dispatch remains valid or is explicitly reconfirmed.
