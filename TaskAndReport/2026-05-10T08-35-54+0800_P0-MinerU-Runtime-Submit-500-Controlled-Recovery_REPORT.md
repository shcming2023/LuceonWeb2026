# Lucode Report: P0 MinerU Runtime Submit-500 Controlled Recovery

## Basis

- Based on Lucia task brief: `TaskAndReport/2026-05-10T08-35-54+0800_P0-MinerU-Runtime-Submit-500-Controlled-Recovery_TASK.md`
- Decision context: `TaskAndReport/2026-05-10T08-35-54+0800_P0-MinerU-Runtime-Submit-500-Recovery-Authorization_LUCIA_REVIEW.md`
- Execution role: Lucode
- Production path: `/Users/concm/prod_workspace/Luceon2026`
- Development path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

## Result Classification

`MINERU_RUNTIME_RECOVERED_MANUAL_TEST_PRECHECK_READY`

The production MinerU API runtime was recovered with a MinerU-only tmux session restart. After recovery, upload health passed, dependency-health with `mineruSubmitProbe=true` passed, and active-task diagnostics were clean.

This means Director may decide whether to restart manual PDF testing. It is not a production release-readiness claim.

## Production State

- Production HEAD: `e015cc8`
- Production `origin/main`: `e015cc8`
- Production local dirty file preserved: `docker-compose.override.yml`
- Preserved override diff:

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

No source code, secret, model/provider, timeout-policy, or production override change was made.

## Before-Recovery Evidence

### Production git and upload health

- `git status --short --branch` -> exit 0
  - `## main...origin/main`
  - ` M docker-compose.override.yml`
- `git rev-parse --short HEAD && git rev-parse --short origin/main` -> exit 0
  - `e015cc8`
  - `e015cc8`
- `git diff -- docker-compose.override.yml` -> exit 0; local override inspected and preserved.
- `curl -fsS http://localhost:8081/__proxy/upload/health` -> exit 0

```json
{"ok":true,"service":"upload-server"}
```

### Dependency health with MinerU submit probe

Command:

```bash
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
```

Exit 0:

```json
{
  "ok": false,
  "blocking": true,
  "dependencies": {
    "minio": { "ok": true },
    "mineru": {
      "ok": false,
      "endpoint": "http://192.168.31.33:8083",
      "healthOk": true,
      "error": "submit probe failed: HTTP 500: Internal Server Error",
      "submitProbe": {
        "enabled": true,
        "ok": false,
        "status": 500,
        "durationMs": 10,
        "taskId": null,
        "error": "HTTP 500: Internal Server Error"
      }
    },
    "ollama": {
      "ok": true,
      "durationMs": 373,
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

### MinerU runtime/API status

- `curl -sS --max-time 10 'http://192.168.31.33:8083/health'` -> exit 0

```json
{
  "status": "healthy",
  "version": "3.1.0",
  "queued_tasks": 0,
  "processing_tasks": 0,
  "completed_tasks": 0,
  "failed_tasks": 0,
  "max_concurrent_requests": 1
}
```

- `lsof -nP -iTCP:8083 -sTCP:LISTEN || true` -> exit 0
  - `python3.1` PID `979` listening on `*:8083`
- `ps -p 979 -o pid,ppid,stat,lstart,command` -> exit 0
  - `/Users/concm/miniconda3/envs/mineru/bin/python3.10 /Users/concm/miniconda3/envs/mineru/bin/mineru-api --port 8083 --host 0.0.0.0`
- `tmux list-sessions 2>/dev/null || true` -> exit 0
  - `mineru_api: 1 windows (created Sat May  9 22:42:00 2026)`

Interpretation: the smallest scoped recovery action was a MinerU API tmux-session restart. No other service required mutation.

## Recovery Commands

Executed in production path:

```bash
tmux kill-session -t mineru_api
```

Exit 0.

```bash
tmux new-session -d -s mineru_api "cd '/Users/concm/prod_workspace/Luceon2026' && bash ops/start-mineru-api.sh"
```

Exit 0.

This restarted only the MinerU API runtime wrapper. It did not restart upload-server, Ollama, MinIO, DB, or any broad Docker stack.

## After-Recovery Evidence

### MinerU runtime/API status

Command:

```bash
sleep 5 && tmux list-sessions 2>/dev/null || true && lsof -nP -iTCP:8083 -sTCP:LISTEN || true && curl -sS --max-time 10 'http://127.0.0.1:8083/health'
```

Exit 0:

```text
mineru_api: 1 windows (created Sun May 10 08:44:26 2026)
python3.1 PID 79920 listening on *:8083
```

Health:

```json
{
  "status": "healthy",
  "version": "3.1.0",
  "queued_tasks": 0,
  "processing_tasks": 0,
  "completed_tasks": 0,
  "failed_tasks": 0,
  "max_concurrent_requests": 1
}
```

Process confirmation:

```bash
ps -p 79920 -o pid,ppid,stat,lstart,command
```

Exit 0:

```text
79920 79919 Rs+ Sun May 10 08:44:26 2026 /Users/concm/miniconda3/envs/mineru/bin/python3.10 /Users/concm/miniconda3/envs/mineru/bin/mineru-api --host 0.0.0.0 --port 8083
```

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

Exit 0:

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
      "error": null,
      "submitProbe": {
        "enabled": true,
        "ok": true,
        "status": 202,
        "durationMs": 27,
        "taskId": "3ef74604-9282-4248-bb8f-e2784573ee14",
        "error": null
      }
    },
    "ollama": {
      "ok": true,
      "durationMs": 376,
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

### Final production status

- `git status --short --branch` in production -> exit 0
  - `## main...origin/main`
  - ` M docker-compose.override.yml`
- Development `git diff --check` -> exit 0
- Development `git status --short --branch` before report edits -> exit 0
  - `## main...origin/main`
- Development HEAD before report edits: `bf94edc Record task 68 ledger head`

## Skipped Checks

- No new validation upload was created because Task 68 only authorized runtime recovery and post-recovery prechecks.
- No failed 24-task repair or reprocessing was attempted.
- No DB row, MinIO object, Docker volume, task, material, artifact, log, sample, secret, model/provider, timeout-policy, or production override mutation was performed.
- No broad Docker stack restart/rebuild/rollback was performed.
- No upload-server, Ollama, MinIO, or DB restart was performed.

## Risks / Residual Debt

- The root cause of MinerU accepting `/health` while returning HTTP 500 on `/tasks` appears runtime-state related and was cleared by MinerU API restart, but the underlying MinerU internal failure mode is not repaired in code.
- The recovery created one synthetic MinerU submit-probe task inside MinerU: `3ef74604-9282-4248-bb8f-e2784573ee14`. It did not create Luceon Material, ParseTask, MinIO object, or DB row.
- Manual testing may restart only as a next Director decision; this report does not authorize a validation run by itself.

## Handoff

- Next Actor: Lucia
- Recommended next action: review the recovery evidence and decide whether to ask Director to restart manual PDF testing or require additional guardrails first.
- Production release readiness: not claimed.
