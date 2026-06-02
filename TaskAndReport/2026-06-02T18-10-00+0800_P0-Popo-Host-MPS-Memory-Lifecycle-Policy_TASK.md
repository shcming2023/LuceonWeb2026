# P0 Popo Host MPS Memory Lifecycle Policy Task

Issued by: Luceon
Issued at: 2026-06-02T18:10:00+0800
Task ID: TASK-20260602-181000-P0-Popo-Host-MPS-Memory-Lifecycle-Policy

## Objective

Fix the real blocker exposed by Task 321: the official Popo full-background run crossed the old 3600-second timeout boundary, but later failed because the host MPS worker accumulated/fragmented memory across many generations and hit MPS OOM.

This is a host worker memory lifecycle task, not a Popo algorithm or scheduler task.

## Scope

Allowed:

- `/Users/concm/prod_workspace/MineruPopo/luceon_service/host_mps_worker.py`
- `/Users/concm/prod_workspace/MineruPopo/scripts/run_host_mps_worker_loop.sh`
- `TaskAndReport/**`

Forbidden:

- MinerU-Popo official `post_processing/label_normalization.py`, `post_processing/run_inference.py`, `post_processing/get_json_tree.py`, or inference algorithm changes.
- Luceon chunk runner revival.
- DB/MinIO cleanup or object deletion.
- Source asset mutation or image hash rename.

## Requirements

- Clean intermediate tensors after each host MPS `/generate`.
- Empty MPS cache after each generation.
- Periodically unload/reload model state after N generations to reduce memory fragmentation.
- On MPS OOM, unload model and clear cache so the worker does not remain in a poisoned memory state.
- Expose memory lifecycle evidence in `/health`.
- Resume the same official full-background job through `run_inference.py --resume`.

## Acceptance

Positive:

- Host worker Python compile passes.
- Worker startup script syntax passes.
- `/health` exposes memory lifecycle policy.
- A small `/generate` smoke records cleanup evidence.
- The same v6 large PDF job resumes from existing raw chunks under official `run_inference.py --resume`.

Negative:

- No official Popo pipeline changes.
- No adapter chunk scheduling.
- No broad cleanup, readiness, release, L3, or go-live claim.
