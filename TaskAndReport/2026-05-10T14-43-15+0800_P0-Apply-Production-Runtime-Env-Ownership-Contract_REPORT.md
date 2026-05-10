# Lucode Report: P0 Apply Production Runtime Env Ownership Contract

## Basis

- Based on Lucia task brief: `TaskAndReport/2026-05-10T14-43-15+0800_P0-Apply-Production-Runtime-Env-Ownership-Contract_TASK.md`
- Related Lucia review: `TaskAndReport/2026-05-10T14-43-15+0800_P0-Local-Production-Service-Ownership-Unification_LUCIA_REVIEW.md`
- Execution role: Lucode
- Development path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production path: `/Users/concm/prod_workspace/Luceon2026`

## Result Classification

`RUNTIME_ENV_CONTRACT_APPLIED_READY_FOR_P1`

The accepted runtime env ownership contract is now applied to the running production `cms-upload-server` container. All five required runtime env values are present, upload health is OK, dependency-health with MinerU submit probe is non-blocking, and no forbidden mutation was performed.

This is not a production release-readiness claim.

## Production HEAD And Override

- Production HEAD before sync: `e015cc8`
- Production `origin/main` before sync: `0981202`
- Production HEAD after sync/apply: `0981202`
- Production local dirty file preserved: `docker-compose.override.yml`

Production override summary, inspected but not changed:

```diff
services:
  upload-server:
    environment:
      - DISABLE_AI_SKELETON_FALLBACK=true
      - OLLAMA_TIER2_MODEL=qwen3.5:9b

  minio:
    ports:
      - "127.0.0.1:19001:9001"
```

## Before Apply Evidence

### Running upload-server env before apply

Command:

```bash
docker inspect cms-upload-server --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E '^(LOCAL_MINERU_ENDPOINT|OLLAMA_API_URL|OLLAMA_TIER2_MODEL|DISABLE_AI_SKELETON_FALLBACK|ALLOW_AI_SKELETON_FALLBACK)=' || true
```

Exit 0:

```text
OLLAMA_TIER2_MODEL=qwen3.5:9b
DISABLE_AI_SKELETON_FALLBACK=true
```

Missing before apply:

- `LOCAL_MINERU_ENDPOINT`
- `OLLAMA_API_URL`
- `ALLOW_AI_SKELETON_FALLBACK`

### Health checks before apply

Upload health:

```json
{"ok":true,"service":"upload-server"}
```

Dependency health with submit probe:

```json
{
  "ok": true,
  "blocking": false,
  "dependencies": {
    "mineru": {
      "ok": true,
      "endpoint": "http://192.168.31.33:8083",
      "healthOk": true,
      "submitProbe": {
        "enabled": true,
        "ok": true,
        "status": 202,
        "durationMs": 59,
        "taskId": "7d3836c4-da67-47d9-868c-35be3ccab98d"
      }
    },
    "ollama": {
      "ok": true,
      "endpoint": "http://host.docker.internal:11434",
      "durationMs": 451,
      "model": "qwen3.5:9b",
      "chatOk": true
    }
  }
}
```

Active-task diagnostics before apply:

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
    { "id": "task-1778388197543", "state": "failed", "stage": "ai" },
    { "id": "task-1778388196668", "state": "failed", "stage": "ai" }
  ]
}
```

## Apply Command

Production sync:

```bash
git pull --ff-only origin main
```

Exit 0; fast-forwarded `e015cc8..0981202`.

Compose validation:

```bash
docker compose config --quiet
```

Exit 0.

Apply command:

```bash
docker compose up -d --build upload-server
```

Exit 0. Only `cms-upload-server` was recreated. `cms-minio` was observed as running/healthy because of compose dependency wait, but MinIO was not recreated or restarted. The command emitted an orphan `cms-minio-init` warning; no `--remove-orphans` or cleanup command was run.

## After Apply Evidence

### Running upload-server env after apply

Command:

```bash
docker inspect cms-upload-server --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E '^(LOCAL_MINERU_ENDPOINT|OLLAMA_API_URL|OLLAMA_TIER2_MODEL|DISABLE_AI_SKELETON_FALLBACK|ALLOW_AI_SKELETON_FALLBACK)=' | sort
```

Exit 0:

```text
ALLOW_AI_SKELETON_FALLBACK=false
DISABLE_AI_SKELETON_FALLBACK=true
LOCAL_MINERU_ENDPOINT=http://host.docker.internal:8083
OLLAMA_API_URL=http://host.docker.internal:11434
OLLAMA_TIER2_MODEL=qwen3.5:9b
```

### Upload health after apply

Command:

```bash
curl -fsS http://localhost:8081/__proxy/upload/health
```

Exit 0:

```json
{"ok":true,"service":"upload-server"}
```

### Dependency health after apply

Command:

```bash
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
```

Exit 0:

```json
{
  "ok": true,
  "blocking": false,
  "dependencies": {
    "minio": { "ok": true },
    "mineru": {
      "ok": true,
      "endpoint": "http://host.docker.internal:8083",
      "healthOk": true,
      "submitProbe": {
        "enabled": true,
        "ok": true,
        "status": 202,
        "durationMs": 29,
        "taskId": "6a6a4076-83e5-4a8e-a066-17731b6cdf16"
      }
    },
    "ollama": {
      "ok": true,
      "endpoint": "http://host.docker.internal:11434",
      "durationMs": 583,
      "model": "qwen3.5:9b",
      "chatOk": true
    }
  }
}
```

Key evidence: MinerU endpoint is now explicit runtime env truth `http://host.docker.internal:8083`, not DB/settings-derived `http://192.168.31.33:8083`.

### Active-task diagnostics after apply

Command:

```bash
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
```

Exit 0:

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
    { "id": "task-1778388197543", "state": "failed", "stage": "ai" },
    { "id": "task-1778388196668", "state": "failed", "stage": "ai" }
  ]
}
```

The later ownership helper observed one additional submit-retryable pending row, `task-1778393912016`, after repeated synthetic submit probes. This task did not repair or reprocess any listed task.

### Runtime ownership helper summary

Command:

```bash
bash ops/runtime-ownership-status.sh /Users/concm/prod_workspace/Luceon2026
```

Exit 0. Summary:

- production git: `0981202`, dirty only `docker-compose.override.yml`
- tmux: `mineru_api=present`, `luceon-mineru/sidecar/supervisor=absent`
- listeners:
  - Docker: `*:8081`
  - Docker: `127.0.0.1:19001`
  - Ollama: `*:11434`
  - MinerU: `*:8083`
- Docker services healthy, including recreated `cms-upload-server`
- upload-server env truth included all required values
- upload health OK
- dependency-health with submit probe OK, blocking false, submit probe HTTP 202, task `53807dc1-a8ed-42c4-b055-cc4d8fcb3134`
- Ollama version `0.23.2`, `qwen3.5:9b` loaded

## Checks Run

- Development `git status --short --branch` -> exit 0
- Development `git fetch origin` -> exit 0
- Development `git pull --ff-only origin main` -> exit 0
- Production `git status --short --branch` -> exit 0
- Production `git fetch origin` -> exit 0
- Production `git rev-parse --short HEAD && git rev-parse --short origin/main` -> exit 0
- Production `git diff -- docker-compose.override.yml` -> exit 0
- Running upload-server env before apply -> exit 0
- `curl -fsS http://localhost:8081/__proxy/upload/health` before/after -> exit 0
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` before/after -> exit 0
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'` before/after -> exit 0
- `git pull --ff-only origin main` in production -> exit 0
- `docker compose config --quiet` in production -> exit 0
- `docker compose up -d --build upload-server` -> exit 0
- Running upload-server env after apply -> exit 0
- `bash ops/runtime-ownership-status.sh /Users/concm/prod_workspace/Luceon2026` -> exit 0
- `docker compose ps upload-server` -> exit 0
- Development `git diff --check` -> exit 0

## Skipped Checks

- No TypeScript/build checks were run because Task 71 made no source-code changes in development; it applied already accepted compose/env contract to production.
- No validation upload was created.
- No pressure test was run.
- No failed-task repair or reprocessing was attempted.
- No DB rows, MinIO objects, Docker volumes, tasks, materials, artifacts, logs, samples, secrets, model/provider selection, timeout policy, or production override settings were mutated.
- MinerU, Ollama, MinIO, DB, frontend, and broad Docker stack were not restarted.

## Task 70 Activation Recommendation

Lucode recommendation: Lucia may activate Task 70 from the runtime env ownership perspective.

The P0 runtime env contract is now applied to the running production upload-server, and dependency-health no longer reports DB/settings-derived MinerU endpoint truth.

Residual caveat for Lucia: active-task diagnostics still list pre-existing retryable/historical failure rows. They were outside Task 71 scope and should be treated as known residual diagnostics, not as evidence that env contract application failed.

## Handoff

- Next Actor: Lucia
- Recommended next action: review this report and decide whether Task 70 can move from staged to active Lucode execution.
- Production release readiness: not claimed.
