# P0 MinerU-Popo Host-Mac MPS Worker Integration NoDockerModelInference Report

## Result

COMPLETED_LOCAL_RUNTIME_VALIDATION.

Popo inference was moved out of Docker CPU execution and into a macOS host Python worker using the existing `mineru` conda environment with Apple MPS available. Docker `mineru-popo` now calls the host worker over HTTP for model generation.

## Scope

- Add a host-side Popo generation worker in `/Users/concm/prod_workspace/MineruPopo`.
- Configure the Docker Popo adapter to use the host worker through `host.docker.internal:18083`.
- Keep Popo model resident in the host process after first load.
- Validate with the current small PDF task `task-1780132950215`.

## Implementation Evidence

- Host worker added: `/Users/concm/prod_workspace/MineruPopo/luceon_service/host_mps_worker.py`.
- Popo model utility supports HTTP / host-MPS backend: `/Users/concm/prod_workspace/MineruPopo/post_processing/model_utils.py`.
- Luceon compose points Docker adapter at host worker:
  - `POPO_INFERENCE_BACKEND=host-mps`
  - `POPO_GENERATE_URL=http://host.docker.internal:18083`
  - `POPO_MAX_NEW_TOKENS=256`
  - `POPO_GENERATE_TIMEOUT_SECONDS=900`
- Worker tmux session: `popo-mps-worker`.
- Worker health endpoint: `http://127.0.0.1:18083/health`.

## Runtime Evidence

- Host worker health reported `device=mps`, `mps_available=true`.
- Model preload succeeded in 66.218 seconds.
- Warm `POST /generate` one-token smoke completed in 13.951 seconds.
- Docker container connectivity to host worker succeeded through `host.docker.internal:18083`.
- Docker `mineru-popo` was rebuilt/recreated with the updated host-MPS environment.

## Task Evidence

Validation task:

```text
task-1780132950215
material_id=2787656755020028
job_id=luceon-task-1780132950215-toc-rebuild-v3-1780135742145
```

Observed result:

- DB `metadata.cleanServiceJobs.toc-rebuild.status=completed`.
- Popo adapter `GET /api/v1/jobs/{job_id}` returned `status=completed`.
- Browser task detail page no longer showed running state and displayed:
  - `目录重建：目录结构已完成`
  - `PDF / MinerU / AI Metadata / 目录重建 / Raw Material`
  - `MinerU Markdown (full.md)`
  - `Rebuilt Markdown (rebuilt_markdown.md)`

Generated clean artifacts:

- `toc-rebuild/2787656755020028/v3/flooded_content.json`
- `toc-rebuild/2787656755020028/v3/logic_tree.json`
- `toc-rebuild/2787656755020028/v3/readable_tree.md`
- `toc-rebuild/2787656755020028/v3/skeleton.json`
- `toc-rebuild/2787656755020028/v3/unresolved_anchors.json`
- `toc-rebuild/2787656755020028/v3/metrics.json`
- `toc-rebuild/2787656755020028/v3/rebuilt_markdown.md`
- `toc-rebuild/2787656755020028/v3/provenance.json`

Readback evidence:

- `rebuilt_markdown.md` was readable through the CMS upload proxy.
- `readable_tree.md` was readable through the CMS upload proxy.
- `metrics.json` reported:
  - `engine=mineru-popo`
  - `tokens.total=2841`
  - `input_bytes.pdf=538310`
  - `unresolved_anchor_count=0`

## Boundary

This validates the host-Mac MPS worker route and one small PDF Popo directory rebuild. It does not claim:

- large-PDF Popo performance closure;
- production readiness;
- release readiness;
- go-live approval;
- bounded pressure pass;
- public internet launch readiness.

The host worker is currently managed by tmux, not yet by launchd/system service. A later operational-hardening task should make the worker auto-start and add a health-gated startup check if this route is kept.

