# TASK-20260522-131832-P0-Mineru2Table-Single-Sample-Success-Path-Rerun-NewAssetVersion

## 1. Mainline Objective

Task 242 attempted the standalone Mineru2Table success path but was blocked by a DeepSeek runtime authentication failure and contaminated:

```text
eduassets-clean/toc-rebuild/1842780526581841/v1/
```

Task 244 then proved that the Director-authorized DeepSeek credential can authenticate from inside the Mineru2Table runtime.

This task answers the next critical-path question:

```text
Can standalone Mineru2Table produce a valid toc-rebuild output set for the canonical single sample when the runtime credential is known-good?
```

## 2. Director Authorization

The Director explicitly approved:

```text
Task 245: use a new assetVersion/prefix for a single-sample real Mineru2Table success-path rerun, while continuing to forbid cleanup or reuse of Task 242's contaminated v1 prefix.
```

This task is Luceon-executed because it involves a real LLM call path and the credential remains under Luceon's host/runtime boundary.

## 3. Critical Path Scope

Do only this:

1. Confirm current Mineru2Table runtime health.
2. Confirm the canonical Raw Material input still matches the accepted size/hash.
3. Confirm the old `v1` prefix is treated as locked failed-run evidence and is not modified.
4. Confirm the new `v2` target prefix is empty before submission.
5. Submit exactly one job to `POST /api/v1/jobs`.
6. Poll only that job with `GET /api/v1/jobs/{job_id}` until terminal state or timeout.
7. If completed, verify the seven required `toc-rebuild` artifacts under the `v2` prefix.
8. Record the result honestly as success or a specific blocker.

## 4. True Preconditions

- Task 240 canonical input exists:

  ```text
  eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
  ```

- Expected input size:

  ```text
  31543
  ```

- Expected input SHA256:

  ```text
  f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
  ```

- Task 242 contaminated prefix must remain untouched:

  ```text
  eduassets-clean/toc-rebuild/1842780526581841/v1/
  ```

- Task 245 target prefix must be empty before POST:

  ```text
  eduassets-clean/toc-rebuild/1842780526581841/v2/
  ```

- Task 244 auth probe passed from inside `mineru2table-api`.

## 5. Required Job Payload

Use one unique job id:

```text
luceon-task245-toc-rebuild-1842780526581841-v2-<timestamp>
```

Payload shape:

```json
{
  "job_id": "luceon-task245-toc-rebuild-1842780526581841-v2-<timestamp>",
  "material_id": "1842780526581841",
  "parse_task_id": "task-1779085089451",
  "asset_version": "v2",
  "inputs": [
    {
      "role": "mineru-content",
      "source": {
        "type": "minio",
        "endpoint": "minio:9000",
        "use_ssl": false,
        "bucket": "eduassets-raw",
        "object": "mineru/1842780526581841/v1/content_list_v2.json"
      }
    }
  ],
  "sink": {
    "type": "minio",
    "endpoint": "minio:9000",
    "use_ssl": false,
    "bucket": "eduassets-clean",
    "prefix": "toc-rebuild/1842780526581841/v2/"
  },
  "callback_url": null,
  "callback_secret_ref": null,
  "options": {
    "max_workers": 1,
    "enable_virtual_anchor": true,
    "max_cost_cny": 8.0,
    "max_tokens_total": 500000
  },
  "submitted_at": "<ISO-8601 timestamp>",
  "submitted_by": "luceon2026/task-245-manual-standalone-validation"
}
```

Do not include MinIO credentials, LLM credentials, callback secrets, or Luceon DB identifiers in the payload.

## 6. Expected Output Contract

On success, the target prefix must contain these seven required files:

```text
flooded_content.json
logic_tree.json
readable_tree.md
skeleton.json
unresolved_anchors.json
metrics.json
provenance.json
```

Validation requirements:

- every JSON artifact parses as JSON;
- `readable_tree.md` is non-empty;
- `metrics.json` exists and records non-zero token usage or equivalent service metrics;
- `token_stats.json` must not replace `metrics.json`;
- `unresolved_anchors.json` exists and is valid JSON, even if it is `[]`;
- `provenance.json` ties the output back to the selected input ObjectRef and input SHA256;
- output object size and SHA256 are recorded for every artifact;
- extra objects under the target prefix are recorded as review findings, not silently accepted.

## 7. Environment And Write Boundary

### Luceon Workspace

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed writes:

- this task brief;
- Task 245 report;
- `TaskAndReport/TASK_TRACKING_LIST.md`.

Forbidden:

- `server/**`;
- `src/**`;
- package manifests or lockfiles;
- Docker/Compose files;
- `.env*`;
- PRD/architecture/contract docs;
- private role files (`AGENTS.md`, `.agents/**`).

### Mineru2Table Deployment Workspace

```text
/Users/concm/prod_workspace/Mineru2Tables
```

Allowed runtime/data operations:

- read-only health checks;
- read-only MinIO input/output listing and object verification;
- exactly one `POST /api/v1/jobs`;
- polling the one submitted job;
- one real LLM call path initiated by that job;
- MinIO writes produced by that job only under:

  ```text
  eduassets-clean/toc-rebuild/1842780526581841/v2/
  ```

Forbidden operations:

- any cleanup, deletion, overwrite, move, rename, or migration of `v1`;
- any write outside the `v2` prefix produced by the one job;
- manual job-store edit or cleanup;
- source-code edits;
- Docker image build;
- broad `docker compose down`;
- dependency service restart/recreate;
- Docker network or volume mutation;
- Luceon DB write;
- CleanService worker tick or scheduler activation;
- `CLEANSERVICE_ENABLED=true`;
- more than one job submission;
- raw secret printing or committing.

## 8. Stop Rules

Stop immediately and report a blocker if:

- `v2` target prefix is not empty before submission: `BLOCKED_TARGET_PREFIX_NOT_EMPTY`;
- canonical input size/hash drifts: `BLOCKED_CANONICAL_INPUT_DRIFT`;
- runtime health is not acceptable for this test: `BLOCKED_RUNTIME_HEALTH_NOT_READY`;
- live schema rejects the payload: `BLOCKED_PAYLOAD_SCHEMA_GAP`;
- job does not reach terminal state within 15 minutes: `BLOCKED_JOB_TIMEOUT`;
- job fails due to LLM authentication, quota, provider, or model error: `BLOCKED_LLM_RUNTIME_FAILURE`;
- job succeeds but required artifacts are missing or malformed: `BLOCKED_OUTPUT_CONTRACT_MISMATCH`;
- `v1` prefix must be cleaned or reused to proceed: `BLOCKED_CONTAMINATED_PREFIX_REUSE_REQUIRED`;
- any forbidden operation becomes necessary.

Do not widen scope to repair a blocker.

## 9. Deferrable Side Work

Do not handle these in Task 245:

- fixing the false-success defect exposed by Task 242;
- Luceon orchestrator wiring;
- Luceon DB clean-output metadata persistence;
- operator UI/review integration;
- RawMaterial2CleanMaterial;
- cleanup or migration of failed `v1` artifacts.

Record them as follow-up debt if still relevant after this run.

## 10. Report Requirements

Create:

```text
TaskAndReport/2026-05-22T13-18-32+0800_P0-Mineru2Table-Single-Sample-Success-Path-Rerun-NewAssetVersion_REPORT.md
```

The report must include:

- exact Luceon HEAD;
- exact job id;
- redacted credential presence only, with no raw key, prefix, suffix, length, hash, or account balance;
- pre-submit input size/SHA;
- pre-submit `v1` locked-prefix object count;
- pre-submit `v2` object count;
- POST endpoint and HTTP status;
- polling timeline and terminal state;
- `jobs.json` before/after size, SHA256, key count, and new job delta;
- output object list with size and SHA256;
- JSON parse status and Markdown non-empty status;
- metrics token/cost summary without exposing provider account details;
- provenance source ObjectRef/hash check;
- explicit statement that no UAT/L3/release-readiness/production-readiness/pressure PASS/go-live claim is made.

## 11. Review Boundary

Acceptance of Task 245 means only:

```text
Standalone Mineru2Table either produced one valid toc-rebuild output set for the canonical sample under v2, or reached an honest blocker.
```

It does not mean:

- Luceon CleanService orchestration is wired;
- Luceon DB references clean outputs;
- operator review is updated;
- RawMaterial2CleanMaterial has run;
- Clean Material is complete;
- UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.
