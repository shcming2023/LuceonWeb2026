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

## Production Validation

Validated by Luceon at 2026-06-02T11:39-12:05+0800 on production/control workspace.

Actions:

```bash
docker compose -f docker-compose.yml -f docker-compose.popo.yml up -d --build mineru-popo
POST http://127.0.0.1:18082/api/v1/jobs
GET  http://127.0.0.1:18082/api/v1/jobs/luceon-task-1780291805535-toc-rebuild-v6-1780366071573
GET  http://127.0.0.1:18083/health
```

Observed:

- `mineru-popo` restarted healthy and loaded mounted `luceon_service/chunk_checkpoint_runner.py`.
- Same job resume accepted for `luceon-task-1780291805535-toc-rebuild-v6-1780366071573`.
- Existing raw chunk was preserved and skipped: `contd_chunk_0000.json`.
- New checkpoint moved to `task=contd`, `chunk_index=1`, proving resume continued at `contd_chunk_0001.json`.
- Progress reported `normalized_pages=891`, `inference_chunks_total=264`, `inference_chunks_completed=1`, `active_chunk=contd_chunk_0001.json`, `last_completed_chunk=contd_chunk_0000.json`.
- No partial raw output was written for chunk 1 before completion.
- Chunk 1 exceeded the single chunk timeout after about 907 seconds with error `running_inference_chunk exceeded maximum execution time`.
- After chunk timeout, host MPS worker still showed `active_generations=1`; Luceon restarted the host worker and verified recovery to `active_generations=0`.

Conclusion:

`PRODUCTION_VALIDATION_PARTIAL_PASS_CHECKPOINT_BOUNDARY`: the adapter-side checkpoint/resume boundary works in production and no longer loses the completed first chunk or applies timeout to the whole book. The large PDF still needs a smaller/faster chunk profile or worker-side cancellation/release hardening before full completion can be expected on Home Mac mini MPS.
