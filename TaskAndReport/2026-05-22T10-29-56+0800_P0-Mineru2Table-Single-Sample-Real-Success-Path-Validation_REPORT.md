# TASK-20260522-102956-P0-Mineru2Table-Single-Sample-Real-Success-Path-Validation REPORT

## 1. Execution Overview

- **Branch**: `lucode/TASK-20260522-102956`
- **Execution Commit**: `8ecfa4afe6a5d8c2b77e4a01af52dd9be15de5bf`
- **Final Delivery HEAD**: `ee81557348042cb329ec57c56f7f9705591c0991`
- **Final Classification**: `BLOCKED_LLM_RUNTIME_FAILURE`

---

## 2. Safety & Credentials Disclosure Confirmation

- **No Raw Secrets**: We strictly confirm that **no raw API keys, credentials, or secrets** (including local MinIO credentials or DeepSeek API keys) have been printed, logged, or committed to Git.
- **Redacted Env Presence Matrix**:
  - `DEEPSEEK_API_KEY`: `[SET] redacted`
  - `DEEPSEEK_BASE_URL`: `https://api.deepseek.com`
  - `LLM_MODEL`: `deepseek-chat`
  - `MINIO_ACCESS_KEY`: `[SET] redacted`
  - `MINIO_SECRET_KEY`: `[SET] redacted`

---

## 3. Input & Target State Validation (Pre-Submit)

### A. Raw Material Input
- **Bucket**: `eduassets-raw`
- **Object**: `mineru/1842780526581841/v1/content_list_v2.json`
- **Size**: `31543` bytes
- **SHA256**: `f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db`
- **Status**: Match verified, 0 byte drift.

### B. Target Output Prefix
- **Bucket**: `eduassets-clean`
- **Prefix**: `toc-rebuild/1842780526581841/v1/`
- **Pre-Submit Object Count**: `0` (Verified empty before the initial submission)

---

## 4. Standalone Job Submission & Polling

- **Endpoint**: `POST /api/v1/jobs`
- **HTTP Response Status**: `202 Accepted`
- **Job ID**: `luceon-task242-toc-rebuild-1842780526581841-v1-20260522025136`
- **Submission Payload**:
```json
{
  "job_id": "luceon-task242-toc-rebuild-1842780526581841-v1-20260522025136",
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
  "submitted_at": "2026-05-22T02:51:36.595533Z",
  "submitted_by": "luceon2026/task-242-manual-standalone-validation"
}
```

### Polling Timeline
- `2026-05-22T02:51:36Z`: Submitted and accepted (`202 Accepted`).
- `2026-05-22T02:51:36Z`: Transitioned to running (`started_at`).
- `2026-05-22T02:51:39Z`: Job reached terminal state `completed` (`finished_at`).
- **Total Duration**: `3` seconds.

---

## 5. Mainline Defect: False Success on LLM Authentication Failure

During independent audit, container logs for this job run revealed a severe runtime error:
- **Error message**: `HTTP 401 Authorization Required` from DeepSeek chat completions.
- **Root cause**: LLM authentication failure due to an invalid/blocked test API key during the run.

### Crucial Mainline Defect:
Despite the LLM authentication failure, Mineru2Table **incorrectly converted the failure into a success state**, marking the job `completed` in the job store and generating empty/skeletal outputs. This is a severe pipeline control-flow bug that must be resolved before routing real orchestration logic.

---

## 6. Output Verification & Contaminated Prefix Artifacts

Exactly the 7 expected CleanService `toc-rebuild` output artifacts were generated under `eduassets-clean/toc-rebuild/1842780526581841/v1/`. However, due to the LLM failure, these artifacts are skeletal/empty and represent **failed-run evidence**.

### Failed-Run Artifact List & Hashes:
1. **`flooded_content.json`**: Size `14090` bytes | SHA256 `9cda588e28c65085a4928895a6091ab520e2a7d7381766ac2d538f6505567db6`
2. **`logic_tree.json`**: Size `138` bytes | SHA256 `135e32777cd03442827110e179a7c95868c600a3b919d0b3b4aa2830ea2fb2ef` (Only contains a skeletal root node `文档根节点`, status `pending_anchor` with `children: []`)
3. **`readable_tree.md`**: Size `39` bytes | SHA256 `4dce26d3b9c196b3b7003502eebadbc64ffae62a1bb942c5aacb85960d0f0b60` (Only contains a title heading `# 【可视版】重构逻辑树预览\n`)
4. **`skeleton.json`**: Size `21160` bytes | SHA256 `c004915e79dde976f68cbb460ae3e6bf34e81be6b7cc8bdc28d5252d5ec15f9e`
5. **`unresolved_anchors.json`**: Size `2` bytes | SHA256 `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` (Empty JSON array `[]`)
6. **`metrics.json`**: Size `105` bytes | SHA256 `798fe58889e401d53721ed6014a268bd8183c74567f7719057594d6ee55c56d8` (Zero token metrics: `{"tokens": {"prompt": 0, "completion": 0, "total": 0}}` resulting in estimated/actual cost `0.0`)
7. **`provenance.json`**: Size `2050` bytes | SHA256 `b6d938419466cd11de4ce59982508311ef0212e06a0c7e9bce1fbb5afbfa4bd9` (Provenance has `implementation_commit: unknown` and `input size_bytes: 0` which represent quality gaps for later correction).

> [!WARNING]
> **Contamination Warning**: The target prefix `eduassets-clean/toc-rebuild/1842780526581841/v1/` is now contaminated with failed-run evidence. Do not attempt another run into this prefix unless explicitly authorized by the Director to clean/replace the prefix, or unless a new asset version (e.g., `v2`) is specified.

---

## 7. Standalone Database (jobs.json) Sync Verification

The `jobs.json` file contains 2 keys, including the failed task-242 run marked `completed` (due to the false-success defect).

- **Storage Location**: `/workspace/ops/Mineru2Tables/data/jobs.json`
- **Status**:
  - Size: `3581` bytes
  - SHA256: `683bbbb94a13c84e62e6ed2dd6a13c87fb7042efa4e03c9d16920046e80cf330`
  - Key Count: `2`

---

## 8. Absolute Boundaries & Constraints Compliance

We strictly assert that the execution complied with all security and action boundaries.
- **No cleanup or retry done after LLM failure discovery**: Verified.
- **Zero DB writes on Luceon**: Confirmed.
- **No Worker Activation**: CleanService worker remains disabled.
- **No Source Code Mutated**: Confirmed.
- **No Docker Image Rebuild**: Confirmed.
- **No Broad Compose Down**: Confirmed.
- **No Docker Network or Volume Mutation**: Confirmed.
- **No Cleanups / Object Deletions**: Checked. No objects were deleted, overwritten, or modified.
- **No Premature Claims**: This report **does not** claim UAT, L3, release readiness, production readiness, pressure PASS, production上线, or go-live. It represents only standalone success-path verification.

---

## 9. Conclusion

The attempted success-path validation for Mineru2Table was blocked by LLM runtime failure (DeepSeek 401 authentication failure) and exposed a false-success defect in Mineru2Table's control flow. The generated artifacts are skeletal failed-run evidence and do not represent a successful success-path verification. Control is returned to `luceon` with classification `BLOCKED_LLM_RUNTIME_FAILURE`.
