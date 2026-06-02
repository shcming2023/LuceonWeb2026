# P0 Popo FullBackground MicroChunk And MPS Release Signal Report

Reported by: Luceon
Reported at: 2026-06-02T12:12:33+0800
Task ID: TASK-20260602-121233-P0-Popo-FullBackground-MicroChunk-And-MPS-Release-Signal
Branch: `codex/popo-microchunk-worker-release`

## Result

Status: `IMPLEMENTED_READY_FOR_PRODUCTION_VALIDATION`

Task 315 proved checkpoint/resume works but `contd_chunk_0001` still timed out after about 907 seconds and left host MPS active. This task narrows the full-background path further without changing MinerU-Popo core.

## Changes

- Added `POPO_FULL_BACKGROUND_CHUNK_SIZE`, defaulting to `4`, in `docker-compose.popo.yml`.
- `run_luceon_job` now passes the full-background chunk size to `chunk_checkpoint_runner.py`.
- `chunk_checkpoint_runner.py` now passes explicit `chunk_size` into MinerU-Popo native `adaptive_chunk`.
- Existing raw chunks from a different or unknown chunk profile are archived under `profile_archive/` before micro-profile resume, preventing mixed chunk plans.
- Progress probing ignores archived raw chunks under `profile_archive/` and reports `contd_chunk_0000.json` when a micro-profile run has no completed chunks yet.
- `service.py` probes `POPO_GENERATE_URL/health` after `running_inference_chunk` timeout.
- If host MPS still reports `active_generations > 0`, the adapter returns `mps-worker-release-required`.
- Focused smoke now verifies micro chunking creates more, smaller chunks than the larger profile.

## Verification

Passed:

```bash
PYTHONPATH=. python3 luceon_service/tests/test_popo_invocation_boundary.py
python3 -m py_compile luceon_service/app.py luceon_service/service.py luceon_service/chunk_checkpoint_runner.py luceon_service/tests/test_popo_invocation_boundary.py
git diff --check
```

```bash
node --check server/lib/task-actions-routes.mjs
npx tsc --noEmit
npm run build
```

`npm run build` completed with the existing Vite large chunk warning.

## Boundaries

- No MinerU-Popo core/model changes.
- No DB/MinIO cleanup or source asset mutation.
- No production deployment or full large-PDF completion claim.

## Next Validation

Rebuild/restart `mineru-popo`, resume the same large PDF job, and confirm the next full-background plan reflects micro chunking. Expected behavior: old v6 raw chunks from the previous profile are archived, a smaller chunk profile is used, timeout errors explicitly identify MPS release-required when the host worker remains active, and new-profile completed raw chunks remain reusable.

## Production Validation

Validated by Luceon at 2026-06-02T12:16-12:25+0800.

Passed:

- `mineru-popo` was rebuilt with `POPO_FULL_BACKGROUND_CHUNK_SIZE=4`.
- Same-job recoverable resume was accepted for `luceon-task-1780291805535-toc-rebuild-v6-1780366071573`.
- Legacy `contd_chunk_0000.json` from the old profile was archived under `profile_archive/chunk-size-4-1780373853/`.
- Progress no longer counted archived chunks as completed: `inference_chunks_completed=0`, `active_chunk=contd_chunk_0000.json`.
- Host MPS worker stayed idle while planning: `active_generations=0`, `last_error=null`.

Blocked:

- The micro-profile runner spent more than 4 minutes at about 99% CPU inside `chunk_checkpoint_runner.py --chunk-size 4` before reaching MPS generation.
- The job was canceled by Luceon before model generation to avoid leaving another long-running validation process active.

Conclusion:

`PRODUCTION_VALIDATION_PARTIAL_PASS_PROFILE_BOUNDARY_CPU_PLANNING_BLOCKER`: profile compatibility and progress semantics are now correct, but full-background cannot yet scale because the runner recomputes the full-document chunk plan for every chunk. The next narrow blocker is to persist/cache the chunk plan once and resume from that plan, instead of rebuilding all full-book task-family chunks on every invocation.
