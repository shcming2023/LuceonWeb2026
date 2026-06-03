# P0 Popo Host MPS Memory Lifecycle Policy Report

Task ID: `TASK-20260602-181000-P0-Popo-Host-MPS-Memory-Lifecycle-Policy`

## Summary

Task 322 validated the Home Mac mini Apple MPS host worker as a full-background MinerU-Popo backend for the 891-page large PDF job:

```text
luceon-task-1780291805535-toc-rebuild-v6-1780366071573
task-1780291805535
material 4134323036518274
```

The official MinerU-Popo pipeline invocation was preserved:

```text
/app/post_processing/run_inference.py --resume
```

No MinerU-Popo official pipeline or model code was changed.

## Implemented Host Worker Changes

Local MinerU-Popo overlay commits:

- `3eb05b2 feat: manage host mps generation memory lifecycle`
- `a19fa7d fix: tighten host mps reload and error evidence`

Host worker changes:

- added per-generation MPS cache cleanup;
- added model unload/reload policy;
- tightened default reload interval from 40 generations to 5 generations;
- added reload-after-error behavior;
- added `/health` memory and error evidence fields;
- preserved `error_history` with generation id, input sizes, MPS memory snapshots, and traceback.

Validation checks passed before runtime testing:

```text
python -m py_compile luceon_service/host_mps_worker.py
bash -n scripts/run_host_mps_worker_loop.sh
git diff --check
```

## Production Validation Evidence

The same large PDF full-background job was resumed through the official pipeline after the host worker policy change.

Observed partial progress:

- official `run_inference.py --resume` active during the run;
- raw `contd_chunk_*.json` files were produced under `outputs/inference_raw/mineru/4134323036518274/`;
- the run reached `87 / 264` chunks;
- `contd_chunk_0087.json` through `contd_chunk_0091.json` were present after the tight-reload run;
- `contd_chunk_0092.json` was not produced;
- `title_chunk_0000.json` and `image_chunk_0000.json` were not produced.

The host worker successfully converted several MPS OOM events into recoverable events during the run. `error_history` captured MPS OOM events with request sizes and memory snapshots, and the official pipeline continued after several of them.

Final failure:

```text
requests.exceptions.ReadTimeout:
HTTPConnectionPool(host='host.docker.internal', port=18083): Read timed out. (read timeout=900)
```

The final state was:

- job status: `failed`;
- current step: `failed`;
- completed chunks: `87 / 264`;
- task family: `contd=87`;
- no transition to `title` or `image` family.

## Conclusion

The MPS memory lifecycle policy improved observability and reduced immediate OOM-induced process failure, but it did not make Home Mac mini MPS a stable full-background backend for this large PDF.

The current production evidence supports this boundary:

- Home Mac mini MPS remains usable for bounded-preview and smaller samples.
- Home Mac mini MPS is not reliable for 891-page large PDF full-background MinerU-Popo processing.
- The next mainline path should move large PDF full-background processing to the validated A800 GPU server backend.

This is not accepted as a MinerU-Popo upstream failure. The official pipeline can run and produce chunks. The blocker is the current Apple MPS deployment backend's resource and latency boundary.

## Final Status

`CLOSED_WITH_MPS_BACKEND_BOUNDARY_CONFIRMED`

No DB/MinIO cleanup, source hash rename, upstream MinerU-Popo core change, production readiness, L3, pressure PASS, release-readiness, or go-live claim.
