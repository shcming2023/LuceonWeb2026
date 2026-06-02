# P0 Popo Native Pipeline Invocation Restore Report

Reported by: Luceon
Reported at: 2026-06-02T13:39:13+0800
Task ID: TASK-20260602-133913-P0-Popo-Native-Pipeline-Invocation-Restore
Branch: `codex/popo-native-pipeline-restore`

## Result

Status: `IMPLEMENTED_READY_FOR_PRODUCTION_VALIDATION`

Luceon adapter full-background execution now returns to the official MinerU-Popo inference entrypoint.

## Changes

- Removed Luceon-owned `luceon_service/chunk_checkpoint_runner.py`.
- Removed active service usage of chunk checkpoint runner, microchunk profile, chunk-plan cache, and chunk-level MPS release signaling.
- Full-background now calls official `post_processing/run_inference.py` with `--resume`.
- Bounded-preview continues to call official `post_processing/run_inference.py` over bounded normalized input.
- The adapter still handles outer Luceon duties: job state, workdir reuse, timeout/cancel, artifact upload, and read-only progress observation.
- `docker-compose.popo.yml` no longer exports `POPO_FULL_BACKGROUND_CHUNK_SIZE`.

## Verification

Passed:

```bash
PYTHONPATH=. python3 luceon_service/tests/test_popo_invocation_boundary.py
python3 -m py_compile luceon_service/app.py luceon_service/service.py luceon_service/tests/test_popo_invocation_boundary.py
node --check server/lib/task-actions-routes.mjs
npx tsc --noEmit
npm run build
git diff --check
rg -n "chunk_checkpoint_runner|POPO_FULL_BACKGROUND_CHUNK_SIZE|running_inference_chunk|chunk_plan|mps-worker-release" luceon_service docker-compose.popo.yml server src
```

`npm run build` completed with the existing Vite large chunk warning. The `rg` scan returned no active code references.

## Boundaries

- No MinerU-Popo upstream core/model changes.
- No DB/MinIO cleanup.
- No source asset mutation.
- No full large-PDF completion, readiness, release, L3, or go-live claim.

## Next Validation

Rebuild `mineru-popo` in production and submit a full-background job. Expected: active process is official `post_processing/run_inference.py`, not `luceon_service/chunk_checkpoint_runner.py`.
