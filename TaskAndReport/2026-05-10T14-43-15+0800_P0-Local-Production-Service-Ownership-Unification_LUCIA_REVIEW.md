# Lucia Review: P0 Local Production Service Ownership Unification

- Review Time: `2026-05-10T14:43:15+0800`
- Reviewer: Lucia
- Task ID: `TASK-20260510-142045-P0-Local-Production-Service-Ownership-Unification`
- Task Brief: `TaskAndReport/2026-05-10T14-20-45+0800_P0-Local-Production-Service-Ownership-Unification_TASK.md`
- Lucode Report: `TaskAndReport/2026-05-10T14-20-45+0800_P0-Local-Production-Service-Ownership-Unification_REPORT.md`
- Review Decision: `ACCEPTED_CONTRACT_WITH_RUNTIME_APPLICATION_GAP`

## Judgment

Lucode completed the repository-backed service ownership contract and produced useful read-only runtime evidence. This is accepted as the P0 ownership contract baseline.

However, P1 entry-circuit work must not be activated yet. The currently running production `cms-upload-server` has not applied the new compose/env contract, and dependency-health still reports the MinerU endpoint as `http://192.168.31.33:8083`. That means endpoint truth can still be influenced by legacy defaults or DB/settings-derived values in the current production container.

Before P1 durable admission-state work starts, Lucode must apply the P0 runtime env contract to production upload-server and prove the running container uses the explicit env values.

## Accepted Evidence

Accepted repository changes:

- `docker-compose.yml` now records production-line defaults for:
  - `LOCAL_MINERU_ENDPOINT=http://host.docker.internal:8083`
  - `OLLAMA_API_URL=http://host.docker.internal:11434`
  - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
  - `DISABLE_AI_SKELETON_FALLBACK=true`
  - `ALLOW_AI_SKELETON_FALLBACK=false`
- `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md` documents service ownership and endpoint truth.
- `docs/deploy/DEPLOY.md` links the runtime ownership contract and states DB settings are not production runtime truth for MinerU/Ollama/model/strict AI.
- `ops/runtime-ownership-status.sh` provides a read-only inspection helper.

Accepted runtime observations:

- MinerU owner: host tmux session `mineru_api` running conda MinerU API.
- Ollama owner: host Ollama app/runtime, model `qwen3.5:9b` observable through `/api/ps`.
- MinIO owner: Docker Compose `minio`, console bound local-only at `127.0.0.1:19001`.
- upload-server owner: Docker Compose `upload-server`.
- supervisor/sidecar are optional ops helpers and not owners of MinerU/Ollama/MinIO.
- DB settings are application data and must not be production runtime ownership truth.

Lucia independently re-ran the read-only ownership helper. It confirmed:

- production git clean except local `docker-compose.override.yml`;
- MinerU tmux session present;
- `luceon-sidecar` and `luceon-supervisor` absent;
- Docker services healthy;
- upload health OK;
- dependency-health with MinerU submit probe OK at the time of check;
- active-task diagnostics show one `submitRetryableTasks` item and two historical AI failures, with no active/takeover-required tasks;
- MinerU `/health` OK with `max_concurrent_requests=1`;
- Ollama `0.23.2`, `qwen3.5:9b` loaded.

## Blocking Runtime Application Gap

Current production container env still shows:

- present: `OLLAMA_TIER2_MODEL=qwen3.5:9b`
- present: `DISABLE_AI_SKELETON_FALLBACK=true`
- absent: `LOCAL_MINERU_ENDPOINT`
- absent: `OLLAMA_API_URL`
- absent: `ALLOW_AI_SKELETON_FALLBACK=false`

Current dependency-health still reports:

- MinerU endpoint: `http://192.168.31.33:8083`
- Ollama endpoint: `http://host.docker.internal:11434`

Therefore, the repository contract is accepted, but production runtime has not yet applied it. P1 must wait.

## Decision

Task 69 is closed as accepted with a runtime application gap. Lucia is issuing Task 71 for a narrow production upload-server redeploy/config-application step.

Task 70 remains staged and must not be activated until Task 71 is completed and accepted.

## Release Boundary

No validation upload, pressure test, failed-task repair, DB/MinIO/Docker volume mutation, secret/model/timeout/override mutation, L3 claim, or production release-readiness claim is authorized.

