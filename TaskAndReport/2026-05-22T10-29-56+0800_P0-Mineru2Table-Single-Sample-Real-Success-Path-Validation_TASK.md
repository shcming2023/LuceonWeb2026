# TASK-20260522-102956-P0-Mineru2Table-Single-Sample-Real-Success-Path-Validation

## 1. Task Summary

Run one controlled real Mineru2Table success-path validation against the already
seeded canonical Raw Material sample.

This is the first task allowed to send one real Mineru2Table job POST, call the
LLM once through the standalone service, and write CleanService outputs under
the single authorized `eduassets-clean` target prefix.

This is not Luceon orchestrator wiring and does not authorize CleanService worker
activation or Luceon DB writes.

## 2. Mainline Objective

Answer the critical-path question:

> Can the standalone Mineru2Table service process the canonical Raw Material
> object and produce the required `toc-rebuild` CleanService output artifacts in
> MinIO?

This task should produce real evidence about the Mineru2Table technical route
before more Luceon-side wiring is built.

## 3. Director Authorization

The Director authorized Task 242 after Task 241 closed with
`BLOCKED_CREDENTIALS_UNAVAILABLE`.

The Director has privately provided a DeepSeek test API key for this validation.
Do not write, print, commit, or report the raw key. Reports may only state:

```text
DEEPSEEK_API_KEY=[SET] redacted
```

No callback secret is required for this task. Use standalone submit plus polling
mode. If the live schema accepts null callback fields, submit with:

```json
"callback_url": null,
"callback_secret_ref": null
```

If the live runtime unexpectedly requires callback configuration for this test,
stop and report:

```text
BLOCKED_CALLBACK_REQUIRED_FOR_STANDALONE_VALIDATION
```

## 4. Current Evidence From Luceon

Luceon reviewed current state before issuing this task:

- Luceon `main` and `origin/main`:
  `ae8853dadf6a17406286f95751cd32950dd11a0f`.
- Task 241 is closed as:
  `ACCEPTED_BLOCKED_CREDENTIALS_UNAVAILABLE_WITH_LUCEON_HEAD_CORRECTION`.
- `mineru2table-api` is Docker-healthy.
- Host loopback binding remains `127.0.0.1:8000->8000/tcp`.
- Live OpenAPI exposes `POST /api/v1/jobs` and
  `GET /api/v1/jobs/{job_id}`.
- Live `JobSubmitRequest` requires:
  `job_id`, `material_id`, `parse_task_id`, `asset_version`, `inputs`,
  `sink`, `submitted_at`, and `submitted_by`.
- Live schema permits `callback_url` and `callback_secret_ref` to be null.
- Current selected Raw Material input:
  - bucket: `eduassets-raw`
  - object: `mineru/1842780526581841/v1/content_list_v2.json`
  - size: `31543` bytes
  - sha256:
    `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`
- Current target clean prefix:
  - bucket: `eduassets-clean`
  - prefix: `toc-rebuild/1842780526581841/v1/`
  - current object count: `0`
- Current Mineru2Table job store:
  - path:
    `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json`
  - size: `718` bytes
  - sha256:
    `29d5621bcca3d626b8f27289caabd13ba6cd835913a76b9e2cbd8fd8d4577413`
  - current key count: `1`

## 5. Critical Path Scope

Do only this:

1. Confirm the DeepSeek test key is available through a private Director-approved
   local channel. Do not print it.
2. Update only the Mineru2Table deployment environment needed to replace the
   placeholder LLM credential with the test key.
3. Reload only the standalone Mineru2Table service using the compose service
   name:

   ```bash
   docker compose up -d --force-recreate --no-deps --no-build mineru2table
   ```

4. Verify `/health` still reports `minio=ok`, `llm=configured`, and
   `protocol_version=v1`.
5. Confirm the selected Raw Material object still matches the expected size and
   SHA256.
6. Confirm the target output prefix is empty before submission.
7. Submit exactly one job to:

   ```text
   POST /api/v1/jobs
   ```

8. Poll only that job through:

   ```text
   GET /api/v1/jobs/{job_id}
   ```

9. If the job completes, verify the output artifacts under:

   ```text
   eduassets-clean/toc-rebuild/1842780526581841/v1/
   ```

10. Write a report and update the ledger.

## 6. Required Job Payload Shape

Use a single unique job id:

```text
luceon-task242-toc-rebuild-1842780526581841-v1-<timestamp>
```

Use this semantic payload shape, adjusted only for exact timestamp and live
schema requirements:

```json
{
  "job_id": "luceon-task242-toc-rebuild-1842780526581841-v1-<timestamp>",
  "material_id": "1842780526581841",
  "parse_task_id": "task-1779085089451",
  "asset_version": "v1",
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
    "prefix": "toc-rebuild/1842780526581841/v1/"
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
  "submitted_by": "luceon2026/task-242-manual-standalone-validation"
}
```

Do not include MinIO credentials, LLM credentials, or callback secrets in the
payload.

## 7. Expected Output Contract

On completed success, the target prefix must contain the seven required
CleanService `toc-rebuild` artifacts:

```text
flooded_content.json
logic_tree.json
readable_tree.md
skeleton.json
unresolved_anchors.json
provenance.json
metrics.json
```

Validation requirements:

- `metrics.json` must exist.
- `token_stats.json` must not be used as the required metrics artifact.
- `unresolved_anchors.json` must exist and be valid JSON, even if it is `[]`.
- `provenance.json` must record enough source and output evidence to trace back
  to the input ObjectRef and input SHA256.
- JSON artifacts must parse as JSON.
- Markdown artifact must be non-empty.
- Record size and SHA256 for every output object.
- Record any extra object under the target prefix. Extra objects are not
  automatically accepted; they must be highlighted for Luceon review.

## 8. Environment And Write Boundary

Allowed Luceon2026 files:

- `TaskAndReport/2026-05-22T10-29-56+0800_P0-Mineru2Table-Single-Sample-Real-Success-Path-Validation_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Allowed external deployment file:

- `/Users/concm/prod_workspace/Mineru2Tables/.env`

Allowed runtime/data operations:

- set the Director-authorized DeepSeek test key in Mineru2Table runtime
  environment, with no raw value printed;
- single-service no-build recreate of Compose service `mineru2table`;
- one `POST /api/v1/jobs`;
- polling for that one job only;
- one real LLM call path initiated by that job;
- MinIO reads of the selected input object;
- MinIO writes produced by that job only under:

  ```text
  eduassets-clean/toc-rebuild/1842780526581841/v1/
  ```

Forbidden file changes:

- No `server/**` or `src/**` in Luceon2026.
- No `docker-compose*.yml`.
- No `.env*` in Luceon2026.
- No package or lock files.
- No PRD, architecture, or contract docs.
- No AGENTS.md or `.agents/**`.
- No external Mineru2Table source code, tests, Dockerfile, compose file, docs,
  package files, or lock files.

Forbidden runtime/data operations:

- No more than one `POST /api/v1/jobs`.
- No CleanService worker tick or scheduler activation.
- No `CLEANSERVICE_ENABLED=true`.
- No Luceon DB write.
- No Luceon upload-server restart or rebuild.
- No Docker image build.
- No broad `docker compose down`.
- No dependency service restart/recreate.
- No Docker network mutation.
- No Docker volume cleanup/prune.
- No source PDF overwrite, move, rename, or deletion.
- No legacy parsed ZIP overwrite, move, rename, or deletion.
- No write outside the single authorized target prefix.
- No MinIO object delete, rename, move, cleanup, or migration.
- No manual job-store edit or cleanup.
- No raw secret printing in reports, terminal excerpts, ledger notes, or logs.

## 9. Stop Rules

Stop immediately and report a specific blocked classification if:

1. The Director-authorized DeepSeek test key is not available to Lucode through a
   private local channel:

   ```text
   BLOCKED_TEST_LLM_KEY_NOT_AVAILABLE
   ```

2. The key can only be used by printing or committing it:

   ```text
   BLOCKED_SECRET_HANDLING_UNSAFE
   ```

3. The target output prefix is not empty before submit:

   ```text
   BLOCKED_TARGET_PREFIX_NOT_EMPTY
   ```

4. The canonical input object size/SHA256 does not match:

   ```text
   BLOCKED_CANONICAL_INPUT_DRIFT
   ```

5. Applying the key requires Docker image build, broad compose down, dependency
   restart, network mutation, or volume mutation:

   ```text
   BLOCKED_RUNTIME_RELOAD_BOUNDARY
   ```

6. The live schema rejects null callback fields and requires callback wiring:

   ```text
   BLOCKED_CALLBACK_REQUIRED_FOR_STANDALONE_VALIDATION
   ```

7. The job is not terminal within 15 minutes:

   ```text
   BLOCKED_JOB_TIMEOUT
   ```

8. The job fails due to LLM authentication, quota, or model error:

   ```text
   BLOCKED_LLM_RUNTIME_FAILURE
   ```

9. The job succeeds but required artifacts are missing or malformed:

   ```text
   BLOCKED_OUTPUT_CONTRACT_MISMATCH
   ```

10. Any forbidden operation becomes necessary.

Do not widen scope to repair a blocker.

## 10. Positive Acceptance Criteria

Luceon can accept a successful Task 242 if:

- exactly one job was submitted;
- the job reaches terminal `completed`;
- exactly the selected Raw Material input was used;
- the seven required output artifacts exist under the authorized target prefix;
- every JSON artifact parses;
- `readable_tree.md` is non-empty;
- `provenance.json` ties outputs to the selected input ObjectRef and input hash;
- `metrics.json` records token/cost evidence or equivalent service metrics;
- target prefix did not contain objects before submit;
- no object outside the target prefix was written;
- `jobs.json` changed only by adding/updating this one job record;
- no Luceon DB write, CleanService worker activation, source edit, Docker build,
  broad compose down, dependency recreate, network mutation, volume cleanup, or
  object cleanup occurred;
- report contains no raw secrets;
- `git diff --check` passes.

Luceon can also accept a blocked result if the task stops exactly at one of the
Stop Rules with evidence and no forbidden operation.

## 11. Negative Acceptance Criteria

The task fails if:

- more than one job is submitted;
- raw secrets appear in Git, report, ledger, shell transcript, or logs;
- the target prefix is cleaned, deleted, overwritten, or migrated;
- a second sample is attempted;
- Luceon DB is written;
- CleanService worker or scheduler is activated;
- business source code is changed;
- Docker image build, broad compose down, dependency service restart, network
  mutation, or volume cleanup occurs;
- the report claims UAT, L3, release-readiness, production-readiness, pressure
  PASS, production上线, or go-live.

## 12. AI/Data Governance Red Lines

1. ID-only / source-reference discipline: provenance and unresolved anchor
   evidence must point back to source ObjectRefs and source/block references;
   do not invent source truth.
2. Asset hash locking: do not rename, rewrite, move, or delete source assets.
3. Pure structure boundary: this task validates structural `toc-rebuild`
   artifacts only; it does not create final Clean Material or run
   RawMaterial2CleanMaterial.

## 13. Report Requirements

Create:

```text
TaskAndReport/2026-05-22T10-29-56+0800_P0-Mineru2Table-Single-Sample-Real-Success-Path-Validation_REPORT.md
```

The report must include:

- Branch and exact HEAD.
- Confirmation that raw secrets were not printed or committed.
- Redacted env presence matrix for LLM and MinIO credentials.
- Exact one-job id.
- Exact POST endpoint and status code.
- Polling timeline and terminal state.
- Input ObjectRef size/SHA before submit.
- Target prefix pre-submit object count.
- Target prefix post-submit object list with size/SHA for each object.
- `jobs.json` before/after size, SHA256, and key count.
- `metrics.json` token/cost summary, if present.
- Any LLM/API error or quota signal, if blocked.
- Confirmation of no DB write, no worker activation, no source edit, no Docker
  build, no broad compose down, no dependency restart, no network mutation, no
  object cleanup, and no UAT/L3/readiness/go-live claim.
- Final classification:
  - `MINERU2TABLE_SINGLE_SAMPLE_SUCCESS_PATH_COMPLETED`, or
  - a specific blocked classification from the Stop Rules.

## 14. Review Boundary

Acceptance means only that the standalone Mineru2Table service either:

- produced one valid `toc-rebuild` output set for the selected sample, or
- reached an honest, well-evidenced blocker.

Acceptance does not mean:

- Luceon CleanService orchestration is wired.
- Luceon DB references clean outputs.
- Operator review UI is updated.
- RawMaterial2CleanMaterial has run.
- Clean Material is complete.
- UAT, L3, pressure PASS, release readiness, production readiness,
  production上线, or go-live.
