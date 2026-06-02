# P0 Popo Native Pipeline Invocation Restore Report

Reported by: Luceon
Reported at: 2026-06-02T13:39:13+0800
Task ID: TASK-20260602-133913-P0-Popo-Native-Pipeline-Invocation-Restore
Branch: `codex/popo-native-pipeline-restore`

## Result

Status: `PRODUCTION_ENTRY_VALIDATED`

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

## Production Validation

Performed at: 2026-06-02T13:43-13:46+0800

Evidence:

```bash
docker compose -f docker-compose.yml -f docker-compose.popo.yml up -d --build mineru-popo
curl http://127.0.0.1:18082/health
docker exec mineru-popo sh -lc 'test ! -f /app/luceon_service/chunk_checkpoint_runner.py'
docker top mineru-popo -eo pid,ppid,etime,stat,pcpu,pmem,args
curl http://127.0.0.1:18083/health
```

Observed:

- `mineru-popo` rebuilt and restarted healthy.
- Container-mounted adapter no longer contains `luceon_service/chunk_checkpoint_runner.py`.
- Container-mounted adapter references official `/app/post_processing/run_inference.py`.
- Same large-PDF v6 recoverable job entered `running_inference` with `normalized_pages=891`, `inference_chunks_total=264`, and `active_chunk=contd_chunk_0000.json`.
- Active process was official:

```text
/usr/local/bin/python3 /app/post_processing/run_inference.py --input-dir .../outputs/label_normalization/mineru --model-path /app/models/MinerU-Popo --output-dir .../outputs/inference/mineru --raw-output-root .../outputs/inference_raw --limit 1 --resume
```

- Host MPS worker received the generation request (`active_generations=1`) through `popo_generate`.
- Luceon canceled the job after entry verification to avoid a long interactive large-PDF run.
- After cancel, the Popo subprocess exited. The host MPS worker still reported `active_generations=1`; Luceon restarted only the `popo-mps-worker` tmux session and verified recovery to `active_generations=0`.

Conclusion:

The production invocation boundary is corrected: full-background now enters the official MinerU-Popo `run_inference.py --resume` path. This validation does not prove full 891-page completion on Home Mac mini MPS; it only validates deployment and invocation shape.
