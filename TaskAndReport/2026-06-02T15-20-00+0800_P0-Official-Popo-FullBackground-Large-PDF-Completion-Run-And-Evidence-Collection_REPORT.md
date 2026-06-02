# P0 Official Popo FullBackground Large PDF Completion Run And Evidence Collection Report

Reported by: Luceon
Reported at: 2026-06-02T16:25:00+0800
Task ID: TASK-20260602-152000-P0-Official-Popo-FullBackground-Large-PDF-Completion-Run-And-Evidence-Collection

## Result

Status: `TERMINATED_TIMEOUT_WITH_PARTIAL_RAW_CHUNK_EVIDENCE`

The same large PDF v6 job resumed through the official MinerU-Popo full-background pipeline, but did not complete inside the current Luceon adapter task timeout window.

## Target

- Luceon task: `task-1780291805535`
- Material ID: `4134323036518274`
- Popo job: `luceon-task-1780291805535-toc-rebuild-v6-1780366071573`
- Pipeline: official `/app/post_processing/run_inference.py --resume`
- Normalized scale: `891` pages, `19361` normalized blocks
- Estimated Popo chunks: `264`

## Evidence

Final adapter job status:

```json
{
  "status": "timeout",
  "current_step": "running_inference",
  "elapsed": 3602,
  "error": {
    "code": "timeout",
    "message": "running_inference exceeded maximum execution time",
    "retriable": false
  },
  "normalized_pages": 891,
  "normalized_blocks": 19361,
  "chunks_total": 264,
  "completed": 20,
  "chunks_by_task": {
    "contd": 20
  },
  "active_chunk": "contd_chunk_0029.json",
  "last_completed_chunk": "contd_chunk_0028.json"
}
```

Final release evidence:

```json
{
  "mps_worker_release": {
    "ok": true,
    "status": "terminating",
    "reason": "job-timeout",
    "active_generations": 1,
    "generation_lock_locked": true,
    "message": "worker process will terminate; supervisor/tmux wrapper must restart it"
  }
}
```

Final MPS worker health:

```json
{
  "ok": true,
  "active_generations": 0,
  "generation_count": 0,
  "last_error": null,
  "model_loaded": false,
  "device": "mps",
  "release_supported": true
}
```

Raw chunks present at timeout included:

```text
contd_chunk_0000.json
contd_chunk_0001.json
contd_chunk_0002.json
contd_chunk_0003.json
contd_chunk_0007.json
contd_chunk_0008.json
contd_chunk_0009.json
contd_chunk_0010.json
contd_chunk_0011.json
contd_chunk_0012.json
contd_chunk_0013.json
contd_chunk_0014.json
contd_chunk_0015.json
contd_chunk_0016.json
contd_chunk_0017.json
contd_chunk_0018.json
contd_chunk_0019.json
contd_chunk_0025.json
contd_chunk_0027.json
contd_chunk_0028.json
```

Popo container process state after timeout:

```text
python3 -m uvicorn luceon_service.app:app --host 0.0.0.0 --port 8000
```

No official `run_inference.py` subprocess remained after timeout/release.

## Conclusion

The official MinerU-Popo pipeline is being invoked correctly and can produce real raw chunk outputs on the Home Mac mini MPS setup. The current blocker is the Luceon adapter's whole-job timeout window for the 891-page / 264-chunk workload, not a failure to invoke the official pipeline and not an MPS release leak.

This run did not reach `get_json_tree.py`, did not produce final rebuilt markdown/tree artifacts, and therefore cannot be used for final output-quality assessment.

## Recommended Next Action

Run the same official full-background job with a production long-run timeout profile, or move full-background execution into a durable background lane whose timeout is measured in many hours rather than the current 3600-second adapter limit.

Do not reintroduce adapter chunk scheduling.

## Boundaries

- No MinerU-Popo official pipeline changes.
- No Luceon chunk runner revival.
- No DB/MinIO cleanup.
- No source asset mutation or image hash rename.
- No full large-PDF completion/readiness/release/L3/go-live claim.
