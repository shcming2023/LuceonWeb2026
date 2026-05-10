# Lucode Report: P0 MinerU Submit Circuit Breaker Production Deployment And Manual Test Prep

## Basis

- Based on Lucia task brief: `TaskAndReport/2026-05-10T08-19-06+0800_P0-MinerU-Submit-Circuit-Breaker-Production-Deployment-And-Manual-Test-Prep_TASK.md`
- Decision context: `TaskAndReport/2026-05-10T08-19-06+0800_P0-MinerU-Submit-Path-500-Production-Deployment-Recovery-Decision_LUCIA_REVIEW.md`
- Execution role: Lucode
- Production path: `/Users/concm/prod_workspace/Luceon2026`
- Development path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

## Result Classification

`DEPLOYED_BUT_MINERU_SUBMIT_STILL_BLOCKED`

Production `upload-server` was updated to accepted main and rebuilt successfully, but the explicit MinerU submit-path dependency probe still fails with HTTP 500 while MinerU `/health` is OK. Manual PDF pressure/manual testing should not restart as a normal validation pass until Lucia/Director decide how to recover or replace the current MinerU runtime state.

This report does not claim production release readiness.

## Production Deployment Evidence

- Production HEAD before sync: `20d08d5`
- Production HEAD after sync/deploy: `e015cc8ed8de60eae27d0883ed6e3fa22d5d59fd`
- Production status before sync: `## main...origin/main [behind 9]` plus local modified `docker-compose.override.yml`
- Production status after deploy: `## main...origin/main` plus local modified `docker-compose.override.yml`
- Local dirty file preserved: `docker-compose.override.yml`

The local override diff remained limited to existing runtime-local config:

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

Remote update did not include `docker-compose.override.yml`, so `git pull --ff-only origin main` preserved the local override.

## Commands Run

### Development workspace

- `git status --short --branch` -> exit 0; output: `## main...origin/main`
- `git fetch origin` -> exit 0
- `git pull --ff-only origin main` -> exit 0; already up to date before execution
- `git diff --check` -> exit 0

### Production workspace

- `git status --short --branch` -> exit 0; before sync: `## main...origin/main [behind 9]`, ` M docker-compose.override.yml`
- `git diff -- docker-compose.override.yml` -> exit 0; local override inspected and preserved
- `git fetch origin` -> exit 0; origin/main advanced from `20d08d5` to `e015cc8`
- `git rev-parse --short HEAD && git rev-parse --short origin/main` -> exit 0; output: `20d08d5`, `e015cc8`
- `git diff --name-only HEAD..origin/main` -> exit 0; upstream changed TaskAndReport/docs/server files, not `docker-compose.override.yml`
- `git pull --ff-only origin main` -> exit 0; fast-forwarded `20d08d5..e015cc8`
- `git status --short --branch` -> exit 0; after sync: `## main...origin/main`, ` M docker-compose.override.yml`
- `git log -1 --oneline` -> exit 0; output: `e015cc8 Record task 66 ledger head`
- `docker compose up -d --build upload-server` -> exit 0; rebuilt image and recreated only `cms-upload-server`; warning observed for orphan `cms-minio-init`, no orphan cleanup was run
- `docker compose ps upload-server` -> exit 0; `cms-upload-server` status `Up ... (healthy)`
- `git rev-parse HEAD` -> exit 0; output: `e015cc8ed8de60eae27d0883ed6e3fa22d5d59fd`

Non-blocking helper note: `git rev-parse --short HEAD origin/main` returned exit 128 because `--short` needs one revision per invocation; the corrected split command above passed.

## Health And Dependency Evidence

### Upload health

Command:

```bash
curl -fsS http://localhost:8081/__proxy/upload/health
```

Exit 0:

```json
{"ok":true,"service":"upload-server"}
```

### Dependency health with MinerU submit probe

Command:

```bash
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
```

Exit 0, service response:

```json
{
  "ok": false,
  "blocking": true,
  "dependencies": {
    "minio": {
      "ok": true,
      "requiredFor": ["upload", "parse"]
    },
    "mineru": {
      "ok": false,
      "requiredFor": ["parse"],
      "endpoint": "http://192.168.31.33:8083",
      "healthOk": true,
      "error": "submit probe failed: HTTP 500: Internal Server Error",
      "submitProbe": {
        "enabled": true,
        "ok": false,
        "status": 500,
        "durationMs": 11,
        "taskId": null,
        "error": "HTTP 500: Internal Server Error"
      }
    },
    "ollama": {
      "ok": true,
      "requiredFor": ["ai"],
      "blockingParse": false,
      "endpoint": "http://host.docker.internal:11434",
      "error": null,
      "durationMs": 409,
      "model": "qwen3.5:9b",
      "chatOk": true
    }
  }
}
```

### Active-task diagnostics

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
  "submitRetryableTasks": [],
  "takeoverRequiredTasks": [],
  "historicalAiFailureTasks": []
}
```

## Interpretation

- The accepted Task 64 circuit-breaker code is now deployed in production `upload-server`.
- The deploy itself is not blocked: upload-server is healthy after rebuild.
- The runtime remains blocked at the real MinerU submit path: `/health` is OK but POST `/tasks` returns HTTP 500.
- The new dependency-health gate correctly reports `blocking=true` and `mineru.ok=false` for this condition.
- Ollama is currently reachable from the upload-server path and passed the health chat check.
- No active upload-server queue/takeover issue was present at the time of this report.

## Skipped Checks

- No manual PDF upload was run because the required submit-probe gate failed.
- No MinerU, Ollama, MinIO, DB, broad Docker stack, volume, task, material, artifact, log, sample, secret, provider, model, timeout, or override mutation was performed.
- No failed 24-pressure-test task repair or reprocessing was performed.

## Risks / Blockers / Residual Debt

- Release-blocking runtime condition remains: MinerU submit path returns HTTP 500 while `/health` is OK.
- Manual testing should not restart as a normal validation run until MinerU submit-path recovery is explicitly authorized and verified, or Lucia/Director choose a different recovery path.
- Production local `docker-compose.override.yml` remains intentionally dirty as local runtime config and was preserved.
- This report does not diagnose or repair the MinerU runtime internals; Task 66 only authorized deployment of accepted upload-server code and read-only checks.

## Handoff

- Next Actor: Lucia
- Recommended next action: review this deployment evidence, classify the remaining MinerU runtime submit-path blocker, and decide whether to authorize MinerU runtime recovery/restart or another remediation task before manual testing restarts.
