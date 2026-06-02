# P0 Popo FullBackground Progress Aware LongRun Timeout Policy Report

Reported by: Luceon
Reported at: 2026-06-02T18:05:00+0800
Task ID: TASK-20260602-163500-P0-Popo-FullBackground-Progress-Aware-LongRun-Timeout-Policy
Branch: `codex/popo-fullbackground-progress-aware-timeout`
Main commit: `7eac9f9`

## Result

Status: `PRODUCTION_VALIDATED_OLD_TIMEOUT_PASSED_NEW_MPS_OOM_BLOCKER`

The full-background timeout policy was changed from fixed whole-job timeout to progress-aware long-run monitoring. Production validation proved the policy crossed the previous 3600-second kill boundary while the official MinerU-Popo pipeline was still making progress.

The run later failed for a different blocker: host Mac MPS out-of-memory during generation.

## Changes

- `bounded-preview` keeps the normal short whole-job timeout behavior.
- `full-background` `running_inference` now uses progress-aware waiting.
- Progress-aware policy tracks:
  - raw chunk progress;
  - last completed chunk;
  - active chunk;
  - MPS worker generation count/activity;
  - subprocess liveness.
- Full-background stops on no-progress stall, not total elapsed time.
- A 5-hour soft checkpoint is recorded but does not kill an active job.

## Verification

Development gates passed:

```bash
PYTHONPATH=. python3 luceon_service/tests/test_popo_invocation_boundary.py
python3 -m py_compile luceon_service/app.py luceon_service/service.py luceon_service/tests/test_popo_invocation_boundary.py
node --check server/lib/task-actions-routes.mjs
npx tsc --noEmit
npm run build
git diff --check
```

## Production Evidence

The same large PDF v6 job resumed:

```text
luceon-task-1780291805535-toc-rebuild-v6-1780366071573
```

It ran official:

```text
/app/post_processing/run_inference.py --resume
```

At the old 3600-second boundary, the job was still running:

```json
{
  "status": "running",
  "elapsed": 3681,
  "completed": 44,
  "chunks_by_task": {
    "contd": 44
  },
  "active_chunk": "contd_chunk_0077.json",
  "last_completed_chunk": "contd_chunk_0076.json",
  "long_run_policy": {
    "mode": "progress-aware",
    "seconds_since_progress": 0
  }
}
```

This proves the old fixed 3600-second whole-job timeout was no longer killing an active full-background job.

The run later failed:

```json
{
  "status": "failed",
  "elapsed": 4225,
  "error": {
    "code": "popo-command-failed",
    "message": "requests.exceptions.ReadTimeout: HTTPConnectionPool(host='host.docker.internal', port=18083): Read timed out. (read timeout=900)"
  },
  "completed": 48,
  "chunks_by_task": {
    "contd": 48
  },
  "active_chunk": "contd_chunk_0084.json",
  "last_completed_chunk": "contd_chunk_0083.json"
}
```

Host MPS worker final error:

```json
{
  "type": "RuntimeError",
  "message": "MPS backend out of memory (MPS allocated: 33.61 GiB, other allocations: 12.69 GiB, max allowed: 42.43 GiB). Tried to allocate 21.50 KiB on private pool.",
  "generation_id": 92
}
```

After failure, Luceon called host worker `/release`:

```json
{
  "status": "released",
  "reason": "post-failure-mps-oom-release",
  "active_generations": 0,
  "model_loaded": false
}
```

## Conclusion

Task 321 achieved its policy objective: full-background is no longer killed simply because the whole job exceeds 3600 seconds while making progress.

The next blocker is separate: long official Popo full-background runs on Home Mac mini MPS can accumulate/fragment MPS memory and eventually fail with MPS OOM. That should be addressed as a host worker memory lifecycle policy, not by reintroducing adapter chunk scheduling or changing the official MinerU-Popo pipeline.

## Recommended Next Action

Add a narrow host MPS worker memory lifecycle policy for official full-background runs:

- after every successful `/generate`, optionally clear MPS cache;
- after N generations or after MPS allocation crosses a threshold, restart/reload the host worker cleanly;
- preserve official `run_inference.py --resume`;
- rely on raw chunk files and `--resume` for continuation after worker recovery.

## Boundaries

- No MinerU-Popo official pipeline changes.
- No Luceon chunk runner revival.
- No DB/MinIO cleanup.
- No source asset mutation or image hash rename.
- No full large-PDF completion/readiness/release/L3/go-live claim.
