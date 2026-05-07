# Lucode Supplemental Report: Post-Recovery Manual Review Findings

Report time: 2026-05-07T10:34:23+0800

## Basis

This is a supplemental Lucode report for the already reported task:

- `TaskAndReport/2026-05-07T10-13-05+0800_P0-Production-Ops-Sidecar-Supervisor-Recovery_TASK.md`
- Primary report: `TaskAndReport/2026-05-07T10-23-55+0800_P0-Production-Ops-Sidecar-Supervisor-Recovery_REPORT.md`

The Director reported after recovery that the UI still did not show expected MinerU parse logs and still showed Ollama recognition blocked. Lucode performed a read-only follow-up check and is recording the result here so Lucia can see it through `Lucia, check task`.

No implementation, retry, re-AI, reparse, task mutation, service restart, Docker cleanup, data deletion, PRD update, project ledger update, or release judgment was performed.

## Current User-Facing URL

- `http://localhost:8081/cms/`
- Current browser page observed by Director: `http://localhost:8081/cms/library`

## Findings

### 1. Ollama Is Currently Still Blocking AI Recognition

Dependency health with MinerU submit probe reported:

```json
{
  "ok": false,
  "blocking": false,
  "dependencies": {
    "minio": { "ok": true },
    "mineru": {
      "ok": true,
      "healthOk": true,
      "submitProbe": {
        "enabled": true,
        "ok": true,
        "status": 202
      }
    },
    "ollama": {
      "ok": false,
      "chatOk": false,
      "durationMs": 15002,
      "model": "qwen3.5:9b",
      "error": "Smoke test failed: The operation was aborted due to timeout"
    }
  }
}
```

Direct Ollama observations:

- `/api/tags` returned and listed `qwen3.5:9b`.
- A simple `/api/chat` request with `qwen3.5:9b` timed out after 20 seconds with no response.

Interpretation:

- Ollama is reachable at the process/API level.
- The required `qwen3.5:9b` chat path is currently too slow or blocked.
- The UI warning "Ollama AI 元数据识别受阻" reflects a real current condition, not only a stale browser cache.

### 2. New Task Is Stuck In AI JSON Repair

New task observed after recovery:

```json
{
  "id": "task-1778120784621",
  "fileName": "走向成功_英语_二模卷16篇.pdf",
  "materialId": "812663997452769",
  "stage": "ai",
  "state": "ai-running",
  "message": "AI: 正在进行 JSON Repair...",
  "mineruStatus": "completed",
  "parsedFilesCount": 25,
  "aiJobId": "ai-job-1778120889758-8cab"
}
```

AI job:

```json
{
  "id": "ai-job-1778120889758-8cab",
  "parseTaskId": "task-1778120784621",
  "state": "running",
  "progress": 40,
  "message": "正在进行 JSON Repair...",
  "metadata": {
    "currentPhase": "repair-pass-running"
  }
}
```

Upload-server log:

```text
[ai-worker] Picking up job: ai-job-1778120889758-8cab (parseTask=task-1778120784621)
[ai-worker] First pass JSON parse failed, attempting repair for job ai-job-1778120889758-8cab...
```

Interpretation:

- MinerU parse completed.
- AI did get far enough to enter first-pass output parsing, but the first pass produced invalid JSON.
- The JSON Repair pass is now running through Ollama and appears blocked/slow enough to make dependency health fail its 15s chat smoke.

### 3. MinerU Raw Logs Exist, But Task-Level Observation Did Not Backfill The Useful Progress

Host raw MinerU logs contain the expected progress for the new 24-page task:

```text
2026-05-07 10:26:26.513 ... total_pages=24
Layout Predict: 100%|...| 24/24
Table-ocr det: 100%|...| 13/13
Table-ocr rec ch: 100%|...| 148/148
OCR-det ch: 100%|...| 32/32
OCR-rec Predict: 100%|...| 451/451
Processing pages: 100%|...| 24/24
```

Global observation after sidecar recovery is non-null, but currently stale/unattributed:

```json
{
  "observer": "host-mineru-log-observer",
  "source": "mineru-log",
  "activityLevel": "log-observation-stale",
  "observationStale": true,
  "attribution": "unattributed",
  "unattributedReason": "not exactly 1 active task"
}
```

Task-level `mineruObservedProgress` for `task-1778120784621` remained at an early low-signal observation:

```json
{
  "activityLevel": "log-observation-no-business-signal",
  "signalSummary": {
    "progressCount": 0,
    "businessLogCount": 0
  }
}
```

Interpretation:

- MinerU key logs are not missing from the host.
- The sidecar is running, but the useful business-progress lines were not properly attributed/backfilled into the task before the task completed MinerU parsing.
- The user-facing symptom "no MinerU parse logs output" is therefore likely a task-level log attribution/backfill gap for fast-completing tasks, not a MinerU runtime logging failure.

## Commands Run

```text
curl -sS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
exit 0

curl -sS 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
exit 0

curl -sS 'http://localhost:8081/__proxy/upload/ops/mineru/global-observation'
exit 0

curl -sS 'http://localhost:8081/__proxy/upload/ops/dependency-repair/status'
exit 0

docker compose logs --tail=260 upload-server | rg -n 'ollama|Ollama|ai-worker|metadata|TimeoutError|Provider|严格|AI|task-1778118934116|failed|qwen'
exit 0

curl -sS 'http://localhost:8081/__proxy/db/tasks/task-1778120784621'
exit 0

curl -sS 'http://localhost:8081/__proxy/db/ai-metadata-jobs/ai-job-1778120889758-8cab'
exit 0

curl -sS http://127.0.0.1:11434/api/tags
exit 0

curl -sS -m 20 http://127.0.0.1:11434/api/chat ...
exit 28

tail -80 /Users/concm/ops/logs/mineru-api.err.log
exit 0
```

## Checks Skipped

- No tests/build/UAT were run because this was a live production manual-review diagnostic follow-up, not an implementation or validation task.
- No repair actions were run because the current task did not authorize retry/re-AI/reparse/Ollama restart or log-attribution code changes.

## Recommended Lucia Follow-Up

Lucia should review and decide whether to issue new scoped tasks for:

1. `P0 AI JSON Repair / Ollama qwen3.5:9b timeout diagnosis`
   - Determine whether repair prompts/input size/model load/timeout policy are causing repeated AI blocking.
   - Preserve strict no-skeleton semantics unless Director changes product policy.

2. `P1/P0 MinerU sidecar task-level log attribution for fast-complete tasks`
   - Ensure raw host business-progress lines can be shown in task detail even when MinerU completes quickly.
   - Avoid falsely showing "no logs" when host logs contain valid progress.

## Review Required

Lucia review is required. Director decision may be required for any restart, retry, Re-AI, timeout-policy, or product-semantics change.
