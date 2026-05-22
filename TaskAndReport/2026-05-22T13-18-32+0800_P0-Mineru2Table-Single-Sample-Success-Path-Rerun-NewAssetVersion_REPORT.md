# TASK-20260522-131832-P0-Mineru2Table-Single-Sample-Success-Path-Rerun-NewAssetVersion Report

## 1. Final Classification

`MINERU2TABLE_SINGLE_SAMPLE_SUCCESS_PATH_COMPLETED_WITH_RESIDUAL_PROVENANCE_SIZE_GAP`

Standalone Mineru2Table processed the canonical Raw Material sample through the real LLM path and produced exactly the seven required `toc-rebuild` artifacts under the new `v2` prefix.

Residual quality gap: `provenance.json` correctly records the input ObjectRef and input SHA256, but still records `input size_bytes=0`. This does not block the Task 245 mainline result, but it must be fixed before promoting provenance quality as complete.

## 2. Execution Boundary

- Luceon workspace: `/Users/concm/prod_workspace/Luceon2026`
- Mineru2Table workspace: `/Users/concm/prod_workspace/Mineru2Tables`
- Luceon execution base HEAD: `53e1c3aaff689998db3c67de8004fc1c366dfb74`
- Runtime container: `mineru2table-api`
- Container ID: `376b46ab3e79f48626ff265860666d914475f52b25b5ffab26de3839f72d2300`
- Container state: `running healthy`
- Loopback binding: `127.0.0.1:8000->8000/tcp`

Credential handling:

- `DEEPSEEK_API_KEY`: `[SET] redacted`
- `MINIO_ACCESS_KEY`: `[SET] redacted`
- `MINIO_SECRET_KEY`: `[SET] redacted`
- no key value, prefix, suffix, length, hash, account balance, or provider response body is recorded.

No forbidden operation was performed:

- no cleanup/reuse of the contaminated `v1` prefix;
- no more than one job POST;
- no Luceon DB write;
- no CleanService worker activation;
- no `CLEANSERVICE_ENABLED=true`;
- no source-code edit;
- no Docker image build;
- no broad `docker compose down`;
- no dependency service restart/recreate;
- no Docker network or volume mutation;
- no MinIO write outside the job-produced `v2` prefix;
- no raw secret printing or committing.

## 3. Pre-Submit Baseline

### Runtime Health

`GET http://127.0.0.1:8000/health` returned:

```json
{
  "status": "healthy",
  "service_name": "toc-rebuild",
  "service_version": "1.0.0",
  "protocol_version": "v1",
  "checks": {
    "minio": "ok",
    "llm": "configured",
    "dependencies": "ok"
  }
}
```

### Canonical Raw Material Input

- Bucket: `eduassets-raw`
- Object: `mineru/1842780526581841/v1/content_list_v2.json`
- Stat size: `31543` bytes
- Stream size: `31543` bytes
- SHA256: `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`

### Locked Failed-Run Prefix

Task 242's contaminated prefix was not cleaned, reused, or modified:

```text
eduassets-clean/toc-rebuild/1842780526581841/v1/
```

Pre-submit `v1` object count: `7`

### New Target Prefix

Task 245 target prefix:

```text
eduassets-clean/toc-rebuild/1842780526581841/v2/
```

Pre-submit `v2` object count: `0`

### Job Store Baseline

- Path: `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json`
- Size: `3581` bytes
- SHA256: `683bbbb94a13c84e62e6ed2dd6a13c87fb7042efa4e03c9d16920046e80cf330`
- Key count: `2`
- Existing keys:
  - `luceon-optionb-mock-job-1779399902295`
  - `luceon-task242-toc-rebuild-1842780526581841-v1-20260522025136`

## 4. Job Submission And Polling

Exactly one job was submitted.

- POST endpoint: `http://127.0.0.1:8000/api/v1/jobs`
- HTTP response: `202 Accepted`
- Job ID: `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230`
- Submitted at: `2026-05-22T05:22:30.408747Z`
- Submitted by: `luceon2026/task-245-manual-standalone-validation`
- Asset version: `v2`
- Sink prefix: `toc-rebuild/1842780526581841/v2/`

Polling timeline:

| Poll | State | started_at | finished_at |
| --- | --- | --- | --- |
| 1 | `processing` | `2026-05-22T05:22:30Z` | `null` |
| 2 | `completed` | `2026-05-22T05:22:30Z` | `2026-05-22T05:22:32Z` |

Terminal state: `completed`

Runtime logs for this job show:

- exactly one `POST /api/v1/jobs` access line;
- two DeepSeek `chat/completions` requests, both `HTTP/1.1 200 OK`;
- no `401` authentication failure;
- no quota failure;
- seven uploads under `eduassets-clean/toc-rebuild/1842780526581841/v2/`.

## 5. Output Artifact Verification

The `v2` prefix contains exactly seven objects and no `token_stats.json`.

| File | Size | SHA256 | Parse/Content |
| --- | ---: | --- | --- |
| `flooded_content.json` | `20054` | `e1a8355a80a5014b5a616ed441a4d0851c47d6a3d6092711ce765ffe11eea7b7` | JSON list parses |
| `logic_tree.json` | `375` | `b61ee669b63bccb597f9ff31e5773ac1cc53a7bf6d6ef7a5ba73d467c7267665` | JSON object parses |
| `readable_tree.md` | `106` | `bba5cf360fa7c0d92a9489ce84dfc40458de6072f812d7ab5d381b8e828946d7` | non-empty, 3 lines |
| `skeleton.json` | `21160` | `c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e` | JSON object parses |
| `unresolved_anchors.json` | `2` | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` | JSON list parses |
| `metrics.json` | `129` | `add72cb0a0c0dcb2fe051961795da8c151181022df79770583d5fb75c7ed9718` | JSON object parses |
| `provenance.json` | `2108` | `4762b30f5ab344b1eec0a46b4541b9fa1df314ca756eb837b4622b43169104eb` | JSON object parses |

`eduassets-clean` total object count after the task: `14`

- `v1`: `7` locked failed-run evidence objects;
- `v2`: `7` Task 245 output objects.

No other clean-output prefix/object was observed.

## 6. Metrics

`metrics.json` and job-store stats agree:

- prompt tokens: `6212`
- completion tokens: `54`
- total tokens: `6266`
- estimated cost CNY: `0.006319999999999999`
- actual cost CNY: `0.0`

The actual cost value is reported as emitted by the service. No provider account balance or response body is recorded.

## 7. Provenance Check

`provenance.json` contains:

- schema/service/job/options/stats sections;
- one input entry;
- six output entries;
- job id: `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230`;
- input bucket: `eduassets-raw`;
- input object: `mineru/1842780526581841/v1/content_list_v2.json`;
- input SHA256: `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`.

Residual gap:

- `provenance.json` records `input size_bytes=0`, while independent pre-submit verification confirmed `31543` bytes.

This is a provenance-quality defect for a later narrow service task. It does not erase the Task 245 mainline evidence that the service used the expected ObjectRef and input hash and produced a valid `v2` output set.

## 8. Job Store After Run

- Size: `6469` bytes
- SHA256: `882471ce941d20182c83237df9dc65969bc7c9b47a6c13d717d2c0c53cedf6f0`
- Key count: `3`
- New key: `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230`
- Task 245 job status: `completed`
- Task 245 artifact keys:
  - `flooded_content`
  - `logic_tree`
  - `metrics`
  - `provenance`
  - `readable_tree`
  - `skeleton`
  - `unresolved_anchors`

## 9. Residual Debt

Mainline evidence now supports moving forward to integration planning. Keep these as follow-up, not Task 245 blockers:

1. Fix provenance input size recording (`input size_bytes=0`).
2. Decide whether `provenance.outputs` should self-reference `provenance.json` or intentionally list only generated content artifacts.
3. Keep the Task 242 false-success defect as a guardrail-hardening task before broader automation.
4. Later evaluate structural quality of the generated tree; Task 245 only validates the success-path mechanics and artifact contract.

## 10. Review Boundary

Acceptance of this task means only:

```text
Standalone Mineru2Table completed one real, single-sample toc-rebuild job under the new v2 prefix and produced the required artifact set.
```

It does not mean:

- Luceon CleanService orchestration is wired;
- Luceon DB references clean outputs;
- operator review is updated;
- RawMaterial2CleanMaterial has run;
- Clean Material is complete;
- structural quality has been product-accepted;
- UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.
