# P0 Remote GPU MinerU-Popo Pipeline API And Luceon Backend Switch Task

Task ID: `TASK-20260603-162717-P0-Remote-GPU-MinerU-Popo-Pipeline-API-And-Luceon-Backend-Switch`

Status: `执行中`

Next Actor: `Luceon`

## Objective

Move the large PDF full-background MinerU/MinerU-Popo path away from the Home Mac mini local MPS backend and onto the validated A800 80GB GPU server path.

The target chain is:

```text
Luceon upload/task
  -> remote GPU MinerU pipeline
  -> remote GPU MinerU-Popo normalization
  -> remote GPU MinerU-Popo inference
  -> remote GPU MinerU-Popo build_tree
  -> Luceon Raw Material / Clean Material artifact ingestion
```

The goal is not to keep optimizing Mac MPS for large PDFs. Mac MPS may remain available for bounded preview and small-sample fallback.

## Current Evidence

Task 322 proved the current Mac MPS full-background boundary:

- official MinerU-Popo `run_inference.py --resume` invoked correctly;
- raw chunks were produced;
- tight host MPS reload absorbed several OOM events;
- large PDF still failed at `87 / 264` chunks;
- final failure was `/generate` read timeout at `900s`;
- no `contd_chunk_0092.json`, `title_chunk_0000.json`, or `image_chunk_0000.json` was produced.

The GPU server runbook proves the remote A800 path:

- GPU: NVIDIA A800-SXM4-80GB;
- MinerU large file test passed;
- 288-page / 123MB PDF end-to-end passed;
- MinerU elapsed: 204s;
- Popo inference elapsed: 1055s;
- normalized blocks: 4702;
- inference entries: 4702;
- build_tree nodes: 1189;
- tree `location` and `block_ids` aligned with inference blocks.

## Scope

Implement a minimal, production-usable remote GPU backend integration.

In scope:

- define a remote GPU Pipeline API contract;
- implement or prepare the remote API service wrapper around the already validated command-line pipeline;
- add Luceon backend configuration for remote GPU MinerU/Popo;
- route large PDF full-background tasks to remote GPU backend;
- preserve existing local Mac paths for bounded preview / fallback;
- collect remote task progress, logs, output refs, and failure reasons;
- ingest outputs into Luceon artifact contracts without inventing source content.

Out of scope:

- further Mac MPS full-background tuning;
- modifying MinerU or MinerU-Popo upstream algorithms;
- front-end direct calls to the GPU service;
- exposing JupyterLab token to Luceon frontend or Git;
- broad UI polish;
- multi-node scheduling;
- auto-scaling;
- high-concurrency pressure claims;
- production go-live claim.

## Environment Matrix And Write Boundary

### Production/control workspace

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed:

- `TaskAndReport/`
- deployment/config documentation
- runtime validation commands when explicitly safe

### Development workspace

```text
/Users/concm/Dev_workspace/Luceon2026
```

Allowed:

- Luceon backend service code;
- CleanService / MinerU adapter routing;
- server-side configuration loader;
- tests and mocks;
- API client wrapper;
- task/report files if implementation branch is used there.

### GPU server

Validated deployment root from runbook:

```text
/workspace/mineru_popo_deploy
```

Allowed after credential/access confirmation:

- create a minimal API wrapper service;
- use task-isolated directories under `/workspace/mineru_popo_deploy/tasks/<task_id>/`;
- run MinerU and Popo official command-line stages;
- collect logs and outputs.

Forbidden:

- writing service tokens into Git-tracked files;
- using JupyterLab URL/token as business runtime dependency;
- deleting historical GPU task outputs outside a task-specific cleanup policy;
- modifying MinerU/MinerU-Popo upstream core algorithm files unless separately authorized.

## Required Remote API Shape

Minimum API:

```text
POST   /api/v1/tasks
GET    /api/v1/tasks/<task_id>
GET    /api/v1/tasks/<task_id>/outputs
GET    /api/v1/tasks/<task_id>/logs
DELETE /api/v1/tasks/<task_id>
```

Minimum status values:

```text
queued
running_mineru
running_normalization
running_inference
running_build_tree
succeeded
failed
cancelled
```

Authentication:

- service token;
- server-side only;
- optional IP allowlist;
- no frontend exposure.

## Output Contract

Successful remote task must expose enough output to build Luceon Raw/Clean artifacts:

- MinerU markdown / `full.md`;
- MinerU `middle.json`;
- MinerU `content_list.json`;
- MinerU result ZIP or equivalent artifact bundle;
- Popo normalized JSON;
- Popo inference JSON;
- Popo build_tree JSON;
- Popo tree TXT preview;
- logs per stage;
- metrics: elapsed time, block count, tree node count, GPU memory evidence where available.

## Data Governance Red Lines

1. ID-only extraction:
   - model-derived structure must preserve block IDs / source references;
   - no invented free-text source truth.

2. Asset hash locking:
   - original image/resource hash names from MinerU outputs must not be renamed or rewritten.

3. Pure layout/code-generation boundary:
   - if later LaTeX/TikZ/layout code is generated, use standard packages only unless separately authorized.

4. Artifact traceability:
   - Luceon metadata must store bounded refs, counters, status, and hashes, not full artifact bodies.

## Positive Acceptance Criteria

1. Remote GPU API can accept one PDF task and expose state transitions through `GET /api/v1/tasks/<task_id>`.
2. Luceon can configure remote GPU backend without hardcoding secrets.
3. Luceon large PDF full-background path routes to remote GPU backend instead of Home Mac mini MPS.
4. Remote output is ingested or made available through Luceon artifact contracts.
5. The same large PDF class that failed on Mac MPS reaches remote Popo `build_tree` output or returns a diagnosable remote failure.
6. Existing bounded-preview local Popo path is not broken.
7. Tests cover remote client contract, failure mapping, and backend selection.

## Negative Acceptance Criteria

1. Do not modify MinerU-Popo official core pipeline.
2. Do not commit tokens, credentials, Jupyter tokens, or private server secrets.
3. Do not make the frontend call the GPU server directly.
4. Do not delete or mutate existing MinIO task artifacts except by explicit task-specific output write.
5. Do not claim production readiness, pressure PASS, release readiness, L3, or go-live from a single integration run.
6. Do not hide remote failures behind local fallback without recording the actual selected backend and failure cause.

## Initial Implementation Plan

1. Close Task 322 as Mac MPS backend-boundary evidence.
2. Implement remote GPU service contract and Luceon remote client with mocked tests.
3. Add backend selection config:

```text
MINERU_BACKEND=local|remote-gpu
POPO_FULL_BACKGROUND_BACKEND=local-mps|remote-gpu
REMOTE_GPU_PIPELINE_BASE_URL
REMOTE_GPU_PIPELINE_TOKEN
```

4. Wire large PDF full-background Popo to remote GPU backend.
5. Run one controlled remote UAT using the known large PDF class.
6. Write report with remote status, outputs, logs, and Luceon artifact evidence.

## Required Report

Write:

```text
TaskAndReport/2026-06-03T16-27-17+0800_P0-Remote-GPU-MinerU-Popo-Pipeline-API-And-Luceon-Backend-Switch_REPORT.md
```

The report must include:

- exact backend selected;
- remote API URL shape without secrets;
- task id and material id;
- stage timings;
- output files and sizes;
- error evidence if failed;
- proof that local bounded preview still works or was not touched;
- no-secret hygiene confirmation.
