# P0 Popo Host MPS Worker Cancel Release Boundary Hardening Report

Reported by: Luceon
Reported at: 2026-06-02T15:18:00+0800
Task ID: TASK-20260602-140000-P0-Popo-Host-MPS-Worker-Cancel-Release-Boundary-Hardening
Luceon branch: `codex/popo-mps-worker-release-boundary`
Luceon main: `1ffcfd3`
MinerU-Popo local overlay commit: `3cf8180`

## Result

Status: `PRODUCTION_VALIDATED_CANCEL_RELEASE_BOUNDARY`

Task 319 hardened the boundary exposed by Task 318: official MinerU-Popo `run_inference.py --resume` is still the active pipeline, and Luceon now has an explicit host MPS worker release path after cancel/timeout.

## Changes

Luceon adapter:

- Calls host worker `/release` after Popo job cancel.
- Calls host worker `/release` after `running_inference` timeout.
- Stores release evidence under `progress.mps_worker_release`.
- Adds delayed release-evidence patching to avoid terminal job-store write races.
- Keeps full-background on official `/app/post_processing/run_inference.py --resume`.

MinerU-Popo Luceon host-worker overlay:

- Adds `POST /release`.
- Idle release unloads model state and clears device cache.
- Busy release reports `restart-required` unless `force_terminate_if_busy=true`.
- Forced busy release returns `status=terminating` and terminates the worker process.
- Adds `scripts/run_host_mps_worker_loop.sh`, used from tmux so intentional worker termination is automatically restarted.

## Verification

Development gates:

```bash
PYTHONPATH=. python3 luceon_service/tests/test_popo_invocation_boundary.py
python3 -m py_compile luceon_service/app.py luceon_service/service.py luceon_service/tests/test_popo_invocation_boundary.py
node --check server/lib/task-actions-routes.mjs
npx tsc --noEmit
npm run build
git diff --check
```

MinerU-Popo overlay gates:

```bash
/Users/concm/miniconda3/envs/mineru/bin/python -m py_compile luceon_service/host_mps_worker.py
bash -n scripts/run_host_mps_worker_loop.sh
git diff --check
```

Production validation:

```bash
docker compose -f docker-compose.yml -f docker-compose.popo.yml up -d --build mineru-popo
tmux new-session -d -s popo-mps-worker "cd /Users/concm/prod_workspace/MineruPopo && bash scripts/run_host_mps_worker_loop.sh ..."
curl http://127.0.0.1:18083/health
POST http://127.0.0.1:18082/api/v1/jobs
POST http://127.0.0.1:18082/api/v1/jobs/luceon-task-1780291805535-toc-rebuild-v6-1780366071573:cancel
```

Observed:

- `mineru-popo` healthy and idle before validation.
- Host MPS worker healthy with `release_supported=true` and `active_generations=0`.
- Idle `POST /release` returned `status=released`, `active_generations=0`.
- Large PDF v6 recoverable job entered official:

```text
/usr/local/bin/python3 /app/post_processing/run_inference.py ... --raw-output-root .../outputs/inference_raw --limit 1 --resume
```

- During the run, host worker reported `active_generations=1`.
- After cancel, job reached `status=canceled`.
- Final stored job progress preserved:

```json
{
  "mps_worker_release": {
    "ok": true,
    "status": "terminating",
    "reason": "job-canceled",
    "active_generations": 1,
    "generation_lock_locked": true,
    "message": "worker process will terminate; supervisor/tmux wrapper must restart it"
  }
}
```

- After tmux wrapper restart, host worker health returned to `active_generations=0`, `generation_count=0`, `last_error=null`, `model_loaded=false`.
- `docker top mineru-popo` showed only the adapter uvicorn process; no `run_inference.py` subprocess remained.

## Boundaries

- No MinerU-Popo official pipeline files were changed.
- No Luceon chunk runner was reintroduced.
- No DB/MinIO cleanup, object deletion, source asset rewrite, or image hash rename.
- No full 891-page completion, production readiness, release readiness, L3, or go-live claim.
