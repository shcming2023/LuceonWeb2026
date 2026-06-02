# P0 Popo FullBackground MicroChunk And MPS Release Signal Task

Issued by: Luceon
Issued at: 2026-06-02T12:12:33+0800
Task ID: TASK-20260602-121233-P0-Popo-FullBackground-MicroChunk-And-MPS-Release-Signal

## Objective

Close the immediate blocker exposed by Task 315 production validation: the same large PDF can resume at the next raw chunk, but `contd_chunk_0001` still exceeds the single chunk time window and leaves the host MPS worker active.

## Scope

Allowed files:

- `docker-compose.popo.yml`
- `luceon_service/service.py`
- `luceon_service/chunk_checkpoint_runner.py`
- `luceon_service/tests/test_popo_invocation_boundary.py`
- `TaskAndReport/**`

Forbidden:

- MinerU-Popo upstream core/model changes.
- DB, MinIO, sample cleanup, or source asset mutation.
- UI polish or broad performance refactor.

## Requirements

- Keep bounded-preview behavior separate from full-background behavior.
- Add a full-background-only micro chunk profile so the checkpoint runner can use a smaller chunk size than interactive preview.
- Ensure the checkpoint runner explicitly passes the chosen chunk size into MinerU-Popo native `adaptive_chunk`.
- On single chunk timeout, probe host MPS worker health.
- If MPS still reports active generation, surface a clear release-required error instead of a generic timeout.

## Acceptance

Positive:

- Focused Python smoke passes.
- Python compile passes.
- `git diff --check` passes.
- TypeScript/build gates pass.
- The implementation remains adapter/deployment-boundary only.

Negative:

- Do not rename source image/PDF/asset hash paths.
- Do not modify MinerU-Popo model or core algorithm.
- Do not claim full large-PDF completion, pressure readiness, release, L3, or go-live.
