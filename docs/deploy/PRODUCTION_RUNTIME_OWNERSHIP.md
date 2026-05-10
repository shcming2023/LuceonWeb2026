# Production Runtime Ownership

Last updated: 2026-05-10

This document records the local production-line runtime ownership contract for Luceon2026 Phase 1. It is a running口径 for local production operations, not a production release-readiness declaration.

## Scope

Current Phase 1 mainline remains:

`upload -> MinIO -> local MinerU -> parsed artifacts -> Ollama qwen3.5:9b -> AI metadata -> operator review`

This contract governs local production service ownership and endpoint truth. It must not be used to authorize pressure tests, validation uploads, failed-task repair, DB/MinIO/Docker-volume mutation, secret changes, model/provider changes, timeout-policy changes, or release-readiness claims.

## Ownership Table

| Area | Owner | Expected Runtime Form | Recovery / Start Command | Endpoint Truth |
| --- | --- | --- | --- | --- |
| MinerU API | Host tmux session `luceon-mineru` running conda `mineru` `mineru-api` | Host process listening on `*:8083` | `tmux kill-session -t luceon-mineru` then `tmux new-session -d -s luceon-mineru "cd '/Users/concm/prod_workspace/Luceon2026' && bash ops/start-mineru-api.sh"` | Host: `http://127.0.0.1:8083`; container/upload-server: `http://host.docker.internal:8083` |
| MinerU monitoring | `ops/mineru-log-observer.mjs` when a sidecar tmux session is intentionally started | Reads `/Users/concm/ops/logs/mineru-api*.log`; writes observations through upload-server ops endpoint | `UPLOAD_SERVER_URL=http://127.0.0.1:8081/__proxy/upload node ops/mineru-log-observer.mjs` | Observer is not MinerU owner and must not be treated as recovery authority |
| Ollama | Host Ollama app/runtime | `/Applications/Ollama.app/.../ollama serve` listening on `*:11434` | Start/stop is host-runtime ownership and requires explicit task authorization | Host: `http://127.0.0.1:11434`; container/upload-server: `http://host.docker.internal:11434`; required model: `qwen3.5:9b` |
| MinIO | Docker Compose service `minio` / container `cms-minio` | Docker service, data in Docker volume | `docker compose up -d minio` only when explicitly authorized | Internal: `http://minio:9000`; console must bind local-only as `127.0.0.1:19001:9001` |
| upload-server | Docker Compose service `upload-server` / container `cms-upload-server` | Docker service behind `/__proxy/upload` | `docker compose up -d --build upload-server` only when explicitly authorized | Browser/proxy: `http://localhost:8081/__proxy/upload`; container dependencies come from compose/env |
| db-server | Docker Compose service `db-server` / container `cms-db-server` | Docker service, data in Docker volume | Do not restart or mutate unless task authorizes it | Internal: `http://db-server:8789`; DB settings are application data, not production runtime ownership truth |
| supervisor / repair agent | `ops/luceon-dependency-supervisor.mjs` when intentionally started | Optional ops helper, not owner of MinerU/Ollama/MinIO | Start only under explicit task authorization | `/ops/dependency-repair/status` reports availability |

## Endpoint And Environment Truth

For production-line upload-server behavior, these values must be fixed by runtime environment or compose configuration:

| Variable | Required production-line value | Why |
| --- | --- | --- |
| `LOCAL_MINERU_ENDPOINT` | `http://host.docker.internal:8083` | Container-to-host MinerU API endpoint. Do not infer from DB settings. |
| `OLLAMA_API_URL` | `http://host.docker.internal:11434` | Container-to-host Ollama endpoint. Do not infer from DB settings. |
| `OLLAMA_TIER2_MODEL` | `qwen3.5:9b` | Current Phase 1 Standard model. |
| `DISABLE_AI_SKELETON_FALLBACK` | `true` | Strict AI mode; skeleton fallback must not be represented as recognition. |
| `ALLOW_AI_SKELETON_FALLBACK` | `false` | Strict AI mode; explicit no-skeleton boundary. |

DB settings may be useful UI/application configuration, but they are not production runtime ownership truth for MinerU, Ollama, strict AI mode, or model selection. If the production runtime env omits these values, the omission is an ownership gap that must be fixed by a scoped ops/config task before pressure validation.

## Health And Admission Checks

Before accepting a manual pressure/validation run, the local production line must show:

- upload-server health: `curl -fsS http://localhost:8081/__proxy/upload/health`
- dependency health with submit probe: `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`
- active-task diagnostics: `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'`
- MinerU health: `curl -sS --max-time 10 http://127.0.0.1:8083/health`
- Ollama version / loaded model state: `curl -sS --max-time 10 http://127.0.0.1:11434/api/version` and `/api/ps`
- Docker service state: `docker compose ps`
- listener state: `lsof -nP -iTCP:8081 -iTCP:8083 -iTCP:11434 -iTCP:19001 -sTCP:LISTEN`

MinerU `/health` 200 alone is insufficient. The submit path must be healthy, meaning dependency-health submit probe returns HTTP `202`, a task id, and `blocking=false`.

## Recovery Boundaries

- MinerU recovery authority is the MinerU tmux/API wrapper only, not upload-server, sidecar, supervisor, or DB settings.
- Ollama recovery is separate host-runtime ownership and must not be bundled into MinerU recovery unless a task explicitly authorizes it.
- MinIO and DB data volumes must not be deleted, pruned, recreated, or mutated by service-ownership checks.
- Failed pressure-test tasks must not be repaired or reprocessed under this contract.
- No service ownership check may create a validation upload.

## Inspection Helper

Run the read-only helper from the production workspace:

```bash
bash ops/runtime-ownership-status.sh
```

The helper reports runtime ownership evidence without changing DB rows, MinIO objects, Docker volumes, tasks, materials, artifacts, logs, samples, secrets, model/provider selection, timeout policy, or production override settings.
