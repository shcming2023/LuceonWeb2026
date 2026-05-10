# Lucode Report: P0 Local Production Service Ownership Unification

## Basis

- Based on Lucia task brief: `TaskAndReport/2026-05-10T14-20-45+0800_P0-Local-Production-Service-Ownership-Unification_TASK.md`
- Related Lucia review: `TaskAndReport/2026-05-10T14-20-45+0800_P0-MinerU-Runtime-Submit-500-Controlled-Recovery_LUCIA_REVIEW.md`
- Execution role: Lucode
- Development path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production path inspected: `/Users/concm/prod_workspace/Luceon2026`

## Result

Task 69 is completed as a repository-backed service ownership contract plus a read-only inspection helper.

No validation upload, pressure test, failed-task repair, DB mutation, MinIO mutation, Docker volume mutation, secret/model/provider/timeout-policy change, production override mutation, or release-readiness claim was performed.

## Files Changed

- `docker-compose.yml`
  - Added production-line runtime endpoint defaults for `LOCAL_MINERU_ENDPOINT`, `OLLAMA_API_URL`, `OLLAMA_TIER2_MODEL`, `DISABLE_AI_SKELETON_FALLBACK`, and `ALLOW_AI_SKELETON_FALLBACK`.
  - Purpose: make runtime env/compose the endpoint truth instead of DB settings.
- `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`
  - New durable ownership contract for MinerU, Ollama, MinIO/Docker, upload-server, db-server, supervisor, and sidecar boundaries.
- `docs/deploy/DEPLOY.md`
  - Linked the ownership contract and recorded that MinerU/Ollama/strict-AI runtime values must not be taken from DB settings.
- `ops/runtime-ownership-status.sh`
  - New read-only status helper for runtime ownership evidence.

## Runtime Ownership Table

| Area | Effective owner | Evidence | Recovery / start boundary |
| --- | --- | --- | --- |
| MinerU API | Host tmux session `mineru_api`, running conda `mineru-api` | `tmux list-sessions` showed `mineru_api`; `python3.1` PID `79920` listened on `*:8083`; command was `/Users/concm/miniconda3/envs/mineru/bin/mineru-api --host 0.0.0.0 --port 8083` | MinerU-only recovery command is the tmux/API wrapper restart using `ops/start-mineru-api.sh`. Supervisor/sidecar are not MinerU owners. |
| Ollama | Host Ollama app/runtime | `ollama` PID `4182`, parent `/Applications/Ollama.app/Contents/MacOS/Ollama`, listened on `*:11434`; `/api/version` returned `0.23.2`; `/api/ps` showed `qwen3.5:9b` loaded | Ollama is host-runtime owned. Do not restart/kill/start/change model without explicit task authorization. |
| MinIO | Docker Compose service `minio`, container `cms-minio` | `docker compose ps` showed `cms-minio` healthy; listener `127.0.0.1:19001`; compose service owns Docker volume `minio-data` | Do not delete, prune, recreate, or mutate data/volumes. Console binding must remain local-only. |
| upload-server | Docker Compose service `upload-server`, container `cms-upload-server` | `docker compose ps` showed healthy; `/__proxy/upload/health` returned OK | Rebuild/restart only under explicit task authorization. Endpoint truth must come from compose/env, not DB settings. |
| db-server | Docker Compose service `db-server`, container `cms-db-server` | `docker compose ps` showed healthy; internal endpoint is `http://db-server:8789` | DB stores application data/settings, but DB settings are not production runtime ownership truth for MinerU/Ollama/model/strict AI. |
| supervisor / sidecar | Optional ops helpers, currently not running | `/ops/dependency-repair/status` returned `SUPERVISOR_UNAVAILABLE`; tmux sessions `luceon-sidecar` and `luceon-supervisor` were absent | They may monitor/report/repair only when explicitly started by task. They are not owners of MinerU/Ollama/MinIO. |

## Endpoint Truth

Required production-line upload-server runtime values are now recorded in `docker-compose.yml` and `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`:

| Variable | Required value |
| --- | --- |
| `LOCAL_MINERU_ENDPOINT` | `http://host.docker.internal:8083` |
| `OLLAMA_API_URL` | `http://host.docker.internal:11434` |
| `OLLAMA_TIER2_MODEL` | `qwen3.5:9b` |
| `DISABLE_AI_SKELETON_FALLBACK` | `true` |
| `ALLOW_AI_SKELETON_FALLBACK` | `false` |

Production container evidence before applying the new compose contract showed an ownership gap:

- present: `OLLAMA_TIER2_MODEL=qwen3.5:9b`
- present: `DISABLE_AI_SKELETON_FALLBACK=true`
- absent: `LOCAL_MINERU_ENDPOINT`
- absent: `OLLAMA_API_URL`
- absent: `ALLOW_AI_SKELETON_FALLBACK=false`

Therefore the code path still had room to rely on defaults and DB settings for endpoint selection in the currently running production container. The repository contract now fixes the intended runtime truth, but this task did not deploy or restart production services to apply the new compose values.

## Process / Listener / Status Evidence

### Production git and local override

- `git status --short --branch` in production -> exit 0:
  - `## main...origin/main`
  - ` M docker-compose.override.yml`
- Production HEAD and origin/main -> exit 0:
  - `e015cc8`
  - `e015cc8`
- `git diff -- docker-compose.override.yml` -> exit 0; local override preserved:
  - strict AI/model settings under `upload-server`
  - MinIO console local-only binding `127.0.0.1:19001:9001`

### Docker services

`docker compose ps` in production -> exit 0:

- `cms-db-server`: healthy
- `cms-frontend`: healthy, `0.0.0.0:8081->80/tcp`
- `cms-minio`: healthy, `127.0.0.1:19001->9001/tcp`
- `cms-upload-server`: healthy

### Listeners

`lsof -nP -iTCP:8081 -iTCP:8083 -iTCP:11434 -iTCP:19001 -sTCP:LISTEN` -> exit 0:

- Docker Desktop: `*:8081`
- Docker Desktop: `127.0.0.1:19001`
- Ollama: `*:11434`
- MinerU: `*:8083`

### Upload / dependency checks

`curl -fsS http://localhost:8081/__proxy/upload/health` -> exit 0:

```json
{"ok":true,"service":"upload-server"}
```

Initial combined dependency-health command timed out once at 15s while Ollama/MinerU checks were being probed. A later direct dependency-health retry passed:

```json
{
  "ok": true,
  "blocking": false,
  "dependencies": {
    "minio": { "ok": true },
    "mineru": {
      "ok": true,
      "endpoint": "http://192.168.31.33:8083",
      "healthOk": true,
      "submitProbe": {
        "enabled": true,
        "ok": true,
        "status": 202,
        "durationMs": 21,
        "taskId": "6f0d2050-d67d-41fa-b004-5497c1a4fd52"
      }
    },
    "ollama": {
      "ok": true,
      "endpoint": "http://host.docker.internal:11434",
      "durationMs": 600,
      "model": "qwen3.5:9b",
      "chatOk": true
    }
  }
}
```

Read-only ownership helper later passed with submit probe task `33b58ec4-242f-4108-a2e2-02d66d9882a7`.

### Active-task diagnostics

`curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'` -> exit 0:

```json
{
  "activeTask": null,
  "currentProcessingTask": null,
  "queuedTasks": [],
  "completedButNotIngestedTasks": [],
  "driftTasks": [],
  "submitRetryableTasks": [
    { "id": "task-1778394120487", "state": "failed", "stage": "submit-failed-retryable", "retries": 6 }
  ],
  "takeoverRequiredTasks": [],
  "historicalAiFailureTasks": [
    { "id": "task-1778388197543", "mineruTaskId": "0ca56201-25ab-436c-bb8c-b14e8abac115", "state": "failed", "stage": "ai" },
    { "id": "task-1778388196668", "mineruTaskId": "1e8c9985-67e3-4868-bc6a-4a017025befd", "state": "failed", "stage": "ai" }
  ]
}
```

This task did not repair or reprocess those tasks.

### MinerU health

`curl -sS --max-time 10 http://127.0.0.1:8083/health` -> exit 0:

```json
{
  "status": "healthy",
  "version": "3.1.0",
  "queued_tasks": 0,
  "processing_tasks": 1,
  "completed_tasks": 23,
  "failed_tasks": 0,
  "max_concurrent_requests": 1
}
```

The `processing_tasks=1` observation occurred after repeated synthetic submit probes and was not accompanied by a Luceon active task.

### Ollama status

- `curl -sS --max-time 10 http://localhost:11434/api/version` -> exit 0: `{"version":"0.23.2"}`
- `curl -sS --max-time 10 http://localhost:11434/api/ps` -> exit 0: `qwen3.5:9b` loaded, expires at `2026-05-10T14:41:27.984357+08:00`
- LaunchAgent inspection showed `gui/501/com.ollama.ollama` submitted by the Ollama app but reported job state `exited`; the active runtime was the app-owned parent process plus `ollama serve`.

No keep-alive setting was found in upload-server runtime env. Current model residency was observable through `/api/ps`, not a durable keep-alive ownership contract.

## Checks Run

- `git status --short --branch` in development -> exit 0
- `git fetch origin` -> exit 0
- `git pull --ff-only origin main` -> exit 0; already up to date
- `git status --short --branch` in production -> exit 0
- `git rev-parse --short HEAD && git rev-parse --short origin/main` in production -> exit 0
- `git diff -- docker-compose.override.yml` in production -> exit 0
- read-only process/listener/status checks for MinerU/Ollama/MinIO/upload-server -> exit 0
- `curl -fsS http://localhost:8081/__proxy/upload/health` -> exit 0
- first dependency-health submit-probe command -> exit 28 timeout after 15s
- dependency-health submit-probe retry -> exit 0, `ok=true`, `blocking=false`
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'` -> exit 0
- `bash ops/runtime-ownership-status.sh /Users/concm/prod_workspace/Luceon2026` -> exit 0
- `docker compose config --quiet` in development -> exit 0
- `git diff --check` -> exit 0

Skipped:

- `npx pnpm@10.4.1 exec tsc --noEmit` and `npx pnpm@10.4.1 run build` were not run because no TypeScript/server code changed.
- No production deploy/rebuild/restart was run because Task 69 asked for governance/ownership unification and did not authorize applying the new compose env to production runtime.
- No validation upload or pressure test was run.

## Residual Gaps Before P1 Activation

- The repository contract is now clear, but production `cms-upload-server` has not been redeployed with the new `LOCAL_MINERU_ENDPOINT`, `OLLAMA_API_URL`, and `ALLOW_AI_SKELETON_FALLBACK=false` env values.
- Current dependency-health still reports MinerU endpoint as `http://192.168.31.33:8083`, showing that DB/settings-derived endpoint truth can still influence the running container until a scoped deployment applies the compose contract or code is changed to reject DB runtime ownership in production.
- Supervisor and sidecar are absent. This is now documented as an optional ops-helper boundary, but no process was started in this task.
- Active-task diagnostics show one `submitRetryableTasks` item and two historical AI failures. They were intentionally not repaired here.
- Ollama model residency is observable through `/api/ps`, but no durable keep-alive runtime contract was implemented in this task.

## Handoff

- Next Actor: Lucia
- Recommended next action: review Task 69 ownership contract and decide whether it is sufficient to activate Task 70, or whether a narrow deployment/config-application task is needed first.
- Production release readiness: not claimed.
