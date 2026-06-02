# P0 Popo FullBackground Progress Aware LongRun Timeout Policy Task

Issued by: Luceon
Issued at: 2026-06-02T16:35:00+0800
Task ID: TASK-20260602-163500-P0-Popo-FullBackground-Progress-Aware-LongRun-Timeout-Policy

## Objective

Replace the current fixed whole-job timeout for official Popo full-background runs with a progress-aware long-run policy.

Task 320 proved that the official MinerU-Popo pipeline is invoked correctly and keeps producing raw chunks, but the 891-page job was killed at 3600 seconds despite making progress.

## Scope

Allowed:

- `luceon_service/service.py`
- `luceon_service/tests/test_popo_invocation_boundary.py`
- `docker-compose.popo.yml`
- `TaskAndReport/**`

Forbidden:

- MinerU-Popo official pipeline changes.
- Luceon chunk runner revival.
- DB/MinIO cleanup or object deletion.
- Source asset mutation or image hash rename.

## Requirements

- Keep bounded-preview on the short interactive timeout path.
- For `full-background` `running_inference`, do not kill only because total elapsed time exceeds `POPO_JOB_TIMEOUT_SECONDS`.
- Track progress using read-only evidence:
  - raw chunk completion count / last completed chunk;
  - current progress signature;
  - MPS worker generation activity;
  - official subprocess liveness.
- Stop only when no progress is observed for `POPO_FULL_BACKGROUND_STALL_TIMEOUT_SECONDS`.
- Preserve timeout/release evidence if the job stalls.
- Record a soft long-run checkpoint after `POPO_FULL_BACKGROUND_SOFT_CHECKPOINT_SECONDS`; this must not kill an active job.

## Acceptance

Positive:

- Focused Python tests pass.
- Python compile passes.
- `git diff --check` passes.
- Node/TypeScript/build gates pass.
- Production validation shows the same large PDF can run beyond the old 3600-second whole-job wall without being killed solely for total elapsed time.

Negative:

- No official Popo pipeline changes.
- No adapter chunk scheduling.
- No completion/readiness/release/L3/go-live claim from this policy change alone.
