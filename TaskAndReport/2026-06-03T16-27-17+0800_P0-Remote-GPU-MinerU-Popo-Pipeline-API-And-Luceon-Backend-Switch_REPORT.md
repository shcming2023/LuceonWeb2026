# P0 Remote GPU MinerU-Popo Pipeline API And Luceon Backend Switch Report

Task ID: `TASK-20260603-162717-P0-Remote-GPU-MinerU-Popo-Pipeline-API-And-Luceon-Backend-Switch`

Status: `CODE_LEVEL_READY_REMOTE_UAT_BLOCKED_ON_GPU_API_ENDPOINT`

Branch: `codex/task-323-remote-gpu-pipeline-client`

## Summary

Implemented the Luceon-side remote GPU Pipeline API contract and backend client boundary.

This is intentionally not a Mac MPS optimization task. The large-PDF full-background path can now be configured to use a server-side `remote-gpu` backend instead of defaulting to the Home Mac mini local MinerU/MPS path.

No production readiness, L3, pressure PASS, or go-live claim is made.

## Backend Selected

Configured backend selector:

```text
MINERU_BACKEND=remote-gpu
MINERU_MODE=remote-gpu
REMOTE_GPU_PIPELINE_ENABLED=true
POPO_FULL_BACKGROUND_BACKEND=remote-gpu
```

Effective Luceon backend:

```text
remote-gpu-pipeline
```

Remote API URL shape:

```text
POST /api/v1/tasks
GET  /api/v1/tasks/<task_id>
GET  /api/v1/tasks/<task_id>/outputs
GET  /api/v1/tasks/<task_id>/logs
```

Secrets:

```text
REMOTE_GPU_PIPELINE_BASE_URL=<server-side only>
REMOTE_GPU_PIPELINE_TOKEN=<server-side only>
```

No token, Jupyter token, or GPU credential was written to Git-tracked files.

## Implementation

Added:

```text
server/services/gpu-pipeline/config.mjs
server/services/gpu-pipeline/client.mjs
server/services/gpu-pipeline/remote-adapter.mjs
server/tests/remote-gpu-pipeline-client-smoke.mjs
```

Updated:

```text
server/services/queue/task-worker.mjs
```

Core behavior:

- `REMOTE_GPU_PIPELINE_ENABLED=true` or `MINERU_MODE/MINERU_BACKEND=remote-gpu` selects the remote GPU adapter.
- Remote submit uses server-side Bearer token auth and multipart PDF upload.
- Remote status values are mapped into Luceon stages:
  - `queued` / `pending` -> `remote-gpu-queued`
  - `running_mineru` -> `remote-gpu-mineru`
  - `running_normalization` -> `remote-gpu-normalization`
  - `running_inference` -> `remote-gpu-inference`
  - `running_build_tree` -> `remote-gpu-build-tree`
- Existing remote `mineruTaskId` tasks resume by polling the remote pipeline and do not call the local MinerU endpoint.
- Remote outputs are saved into Luceon parsed artifact contracts:
  - `parsed/<materialId>/full.md`
  - `parsed/<materialId>/mineru-result.zip`
  - manifest entries for zip contents use `source=zip-entry`, `zipObjectName`, and `zipEntryPath`, matching the existing local zip-source semantics.

## Evidence

Focused smoke:

```text
$ node server/tests/remote-gpu-pipeline-client-smoke.mjs
=== Remote GPU Pipeline Client Smoke ===
  [1] client sends Bearer auth and multipart submit contract...
    PASS
  [2] missing endpoint/token fails closed without network...
    PASS
  [3] adapter polls remote task and stores markdown/zip artifacts...
    PASS
All remote GPU pipeline client smoke cases passed successfully!
```

Syntax / diff hygiene:

```text
$ node --check server/services/gpu-pipeline/config.mjs
$ node --check server/services/gpu-pipeline/client.mjs
$ node --check server/services/gpu-pipeline/remote-adapter.mjs
$ node --check server/services/queue/task-worker.mjs
$ node --check server/tests/remote-gpu-pipeline-client-smoke.mjs
$ git diff --check
# all passed
```

Project gates:

```text
$ npx tsc --noEmit
# passed

$ npm run build
# passed
```

## Remote UAT Status

Real remote GPU UAT was not executed in this implementation pass.

Diagnosable blocker:

```text
The A800 command-line pipeline is validated by runbook evidence, but a stable
business API endpoint/token has not yet been provided to Luceon.
```

This is the next external/deployment step, not a Mac MPS blocker.

## Acceptance Mapping

Positive criteria met:

- Remote API contract defined in Luceon client.
- Luceon remote backend selection config implemented.
- Large PDF full-background path can be switched away from Mac MPS through server-side env.
- Remote output ingestion shape implemented and mock-verified.
- Failure to configure endpoint/token fails closed without real network call.
- Existing local bounded preview code path was not modified.

Positive criteria pending:

- One controlled real remote large-PDF UAT against the A800 API service.
- Real remote stage timings and output file sizes.

Negative criteria preserved:

- No MinerU-Popo official core pipeline modification.
- No frontend direct GPU call.
- No secrets committed.
- No DB/MinIO cleanup or historical artifact mutation.
- No local fallback hiding selected backend/failure cause.
- No readiness/L3/go-live claim.

## Next Action

Deploy or provide the remote GPU Pipeline API wrapper on the A800 host, then run a controlled UAT using the known large PDF class:

```text
task: task-1780291805535
material: 4134323036518274
expected backend: remote-gpu-pipeline
```

The UAT should record remote task id, stage timings, output artifact sizes, Popo tree/build evidence, and Luceon parsed artifact ingestion evidence.
