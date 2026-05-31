# P0 Popo Deployment Invocation Boundary Diagnosis And Minimal Stabilization Report

Task ID: `TASK-20260531-093334-P0-Popo-Deployment-Invocation-Boundary-Diagnosis-And-Minimal-Stabilization`

Reported at: `2026-05-31T10:12:00+0800`

Executor: Luceon

Result:

```text
BLOCKED_HOST_MPS_BACKEND_SINGLE_CHUNK_CAPACITY_LIMIT
```

## Summary

Task 311 confirmed that the current blocker is in Luceon's MinerU-Popo deployment/invocation boundary, not in the upstream MinerU-Popo pipeline itself.

The original pipeline is being invoked:

```text
label_normalization.py
-> run_inference.py
-> inference.py
-> get_json_tree.py
```

Luceon's adapter does not bypass all upstream chunking. The known v3/v4 sample also proved the normalized input is identical after removing job-specific paths.

The minimal Luceon overlay stabilization implemented in the local MinerU-Popo workspace:

```text
/Users/concm/prod_workspace/MineruPopo/luceon_service/host_mps_worker.py
commit bd7b1d1 Serialize Luceon host MPS generation
```

This wrapper change serializes `/generate` calls inside the host-MPS worker and exposes generation state/error details in `/health`. It does not modify upstream `post_processing/*` pipeline files.

Result after stabilization:

```text
known small real sample passed after clean restart/preload
larger real sample still failed on single-chunk MPS/Qwen3-VL visual attention buffer allocation
```

Therefore Task 311 cannot honestly claim `PASS_LUCEON_POPO_INVOCATION_BOUNDARY_STABILIZED`.

## Root Cause Classification

Primary blocker class:

```text
host-MPS backend single-chunk capacity limit
```

Contributing boundary issue:

```text
original inference.py uses asyncio.gather for multiple chunks;
Luceon's host-MPS worker originally allowed concurrent generation against one long-lived MPS model instance.
```

The serialization patch corrected the concurrency mismatch, but the second real sample still failed because a single generated visual chunk can exceed the current Mac MPS/transformers backend capacity.

## Upstream Pipeline Evidence

Read-only review confirmed:

```text
MinerU-Popo remote: https://github.com/opendatalab/MinerU-Popo.git
origin/master: 0484604 Update README_zh.md
local overlay before this task: 3c3eb6a Add Luceon host MPS worker backend
local overlay after this task: bd7b1d1 Serialize Luceon host MPS generation
```

Original README describes:

```text
Task-Oriented Data Engine
Dynamic Chunking and Synchronization
Document Enrichment
```

Original `post_processing/inference.py` includes:

```text
adaptive_chunk(...)
asyncio.gather(...)
popo_generate(...)
```

No upstream core algorithm file was changed in this task.

## Adapter Invocation Evidence

Luceon adapter path:

```text
mineru-result.zip
-> extract *_content_list.json and *_origin.pdf
-> label_normalization.py
-> run_inference.py
-> get_json_tree.py
```

Known sample v3/v4 normalized input comparison:

```text
materialId=2787656755020028
page_count=3
block_count=35
canonical normalized sha256=d2cb085634607ff4da11456415ed7c2039836706b43590ffa9cb480354814ee6
```

Selected small sample visual shape:

```text
PDF pages=3
composite size ~= 596x2536
processor image_grid_thw=[[1,158,38]]
pixel_values shape=(6004,1536)
```

## Runtime Actions

Initial worker condition before restart:

```text
Popo adapter /health ok=true busy=false
host worker /health timed out once after prior MPS RuntimeError history
```

Manual worker restart and preload:

```text
tmux kill-session -t popo-mps-worker
tmux new-session -d -s popo-mps-worker ...
POST http://127.0.0.1:18083/load
```

Observed preload:

```text
load_seconds=123.678 before patch
load_seconds=113.587 after patch
device=mps
model_loaded=true
```

## Stabilization Implemented

Changed local Luceon overlay file:

```text
/Users/concm/prod_workspace/MineruPopo/luceon_service/host_mps_worker.py
```

Change summary:

```text
added model load lock
added generate lock
added generation counters
added active generation state
added last_error in /health
converted unhandled generation exceptions into structured HTTP 500 detail
```

Validation:

```bash
/Users/concm/miniconda3/envs/mineru/bin/python -m py_compile /Users/concm/prod_workspace/MineruPopo/luceon_service/host_mps_worker.py
```

Result:

```text
PASS
```

## Real Sample 1: Known Sample Recovered

Sample:

```text
taskId=task-1780132950215
materialId=2787656755020028
jobId=luceon-task-1780132950215-toc-rebuild-v5-1780191936951
assetVersion=v5
```

Result:

```text
status=completed
artifacts=8
```

Artifacts:

```text
flooded_content.json
logic_tree.json
readable_tree.md
skeleton.json
unresolved_anchors.json
metrics.json
rebuilt_markdown.md
provenance.json
```

Proxy readback:

```text
rebuilt_markdown.md status=200 size=3296
readable_tree.md status=200 size=297
logic_tree.json status=200 size=13681
metrics.json status=200 size=237
provenance.json status=200 size=740
```

Task metadata:

```text
status=completed
jobId=luceon-task-1780132950215-toc-rebuild-v5-1780191936951
assetVersion=v5
```

Material metadata:

```text
status=completed
latestVersion=v5
prefix=toc-rebuild/2787656755020028/v5/
```

## Real Sample 2: Larger Sample Still Blocked

Sample:

```text
taskId=task-1779854322261
materialId=3926938009250504
```

Input shape:

```text
page_count=87
block_count=957
```

Pre-patch run:

```text
jobId=luceon-task-1779854322261-toc-rebuild-v3-1780192515655
status=failed
error=popo-command-failed
failure path=process_contd -> asyncio.gather -> popo_generate -> HTTP 500
```

Post-patch run:

```text
jobId=luceon-task-1779854322261-toc-rebuild-v4-1780193243023
status=failed
error=popo-command-failed
failure path=process_contd -> asyncio.gather -> popo_generate -> HTTP 500
```

Host worker health after post-patch run:

```json
{
  "model_loaded": true,
  "active_generations": 0,
  "generation_count": 2,
  "serialized_generation": true,
  "last_error": {
    "type": "RuntimeError",
    "message": "Invalid buffer size: 120.93 GiB",
    "generation_id": 2
  }
}
```

Task metadata:

```text
status=failed
cleanState=failed
jobId=luceon-task-1779854322261-toc-rebuild-v4-1780193243023
assetVersion=v4
```

## Interpretation

The first successful sample proves:

```text
Luceon adapter input construction is not generally broken.
The original pipeline can still produce readable rebuilt_markdown.md through the host-MPS backend for small real samples.
```

The second failed sample proves:

```text
Serializing /generate is necessary but not sufficient.
The current Mac MPS + transformers host worker cannot reliably process larger native Popo visual chunks.
```

This points to one of the following next decisions:

```text
1. move Popo inference to the upstream-recommended vLLM/GPU/service backend;
2. or authorize a Luceon-side visual input budget/downsample/smaller-chunk adaptation;
3. or constrain the current phase proof to small real samples only, explicitly excluding larger workbook-class PDFs.
```

Option 1 is the cleanest architectural direction if available.

Option 2 is a Luceon deployment/invocation adaptation and must be treated carefully because it changes the visual evidence delivered to the model, even if it does not mutate source assets.

Option 3 would be a narrowed phase claim, not full real Raw Material repeatability.

## Checks

Project/control repo:

```bash
git diff --check
```

External local overlay:

```bash
/Users/concm/miniconda3/envs/mineru/bin/python -m py_compile /Users/concm/prod_workspace/MineruPopo/luceon_service/host_mps_worker.py
```

Full TypeScript/build checks were not run because no Luceon2026 business code was changed.

## Boundary

No upstream MinerU-Popo core pipeline mutation was performed.

No DB/MinIO cleanup, object deletion, source asset rewrite, image hash rename, bulk rerun, UI polish, launchd hardening, pressure test, readiness, release-readiness, L3, public launch, or go-live claim was performed.

## Recommended Next Action

Do not continue tuning UI or historical task state.

Pick one explicit Popo runtime strategy:

```text
Preferred: provision/use upstream-compatible vLLM/GPU/service backend and rerun Task 310 samples.
Fallback: authorize a Luceon-side input-budget adaptation for host-MPS and retest both samples.
Narrowest: declare host-MPS small-sample-only and defer workbook-class Popo closure.
```
