# P0 Popo FullBackground Chunk Checkpoint Runner Report

Reported by: Luceon
Reported at: 2026-06-02T11:35:29+0800
Task ID: TASK-20260602-113529-P0-Popo-FullBackground-Chunk-Checkpoint-Runner
Branch: `codex/popo-chunk-checkpoint-runner`

## Result

Status: `IMPLEMENTED_READY_FOR_PRODUCTION_VALIDATION`

The Luceon adapter now has a dedicated chunk checkpoint runner for full-background Popo jobs. MinerU-Popo core files were not modified.

## Changes

- Added `luceon_service/chunk_checkpoint_runner.py`.
- Full-background execution now loops through the adapter runner one missing chunk at a time.
- The runner writes `checkpoint.json` and raw chunk records under `outputs/inference_raw/mineru/<material_id>/`.
- Existing `*_chunk_*.json` files are skipped, allowing same-job resume.
- Chunk timeout uses `POPO_CHUNK_TIMEOUT_SECONDS`, defaulting to `POPO_GENERATE_TIMEOUT_SECONDS`, instead of the full job timeout.
- Adapter progress now exposes `chunk_checkpoint`.
- `POST /api/v1/jobs` now allows a terminal recoverable job (`timeout`, `failed`, `canceled`) to resume with the same `job_id` and work directory.

## Verification

Passed:

```bash
PYTHONPATH=. python3 luceon_service/tests/test_popo_invocation_boundary.py
python3 -m py_compile luceon_service/app.py luceon_service/service.py luceon_service/chunk_checkpoint_runner.py luceon_service/tests/test_popo_invocation_boundary.py
node --check server/lib/task-actions-routes.mjs
npx tsc --noEmit
npm run build
git diff --check
```

`npm run build` completed with the existing Vite large chunk warning.

## Boundaries

- No MinerU-Popo core/model changes.
- No DB/MinIO cleanup or secret mutation.
- No production deployment, readiness, pressure, release, L3, or go-live claim.

## Next Validation

Deploy/rebuild `mineru-popo` and run a same-job full-background resume test on the v6 large PDF workdir. Expected result: existing `contd_chunk_0000.json` is skipped and the job continues at `contd_chunk_0001.json`.
