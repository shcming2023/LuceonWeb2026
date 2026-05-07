# Lucode Diagnosis Report: P0 Production AI JSON Repair Ollama Timeout Diagnosis

Report time: 2026-05-07T10:51:34+0800

## Basis

This diagnosis was based on Lucia task brief:

- `TaskAndReport/2026-05-07T10-41-51+0800_P0-Production-AI-JSON-Repair-Ollama-Timeout-Diagnosis_TASK.md`

Lucode performed read-only diagnosis only. No code, config, task, AI job, DB file, MinIO object, log, container, MinerU process, or Ollama process was mutated or restarted.

## Production Baseline

Production URL:

- `http://localhost:8081/cms/`

Production path and HEAD:

```text
cd /Users/concm/prod_workspace/Luceon2026
git status --short --branch
exit 0
## main...origin/main
 M docker-compose.override.yml

git rev-parse HEAD
exit 0
f02684c3aee392fdc0e6a9e8fd8da911c17db892

curl -sS -o /dev/null -w '%{http_code}' 'http://localhost:8081/cms/'
exit 0
200
```

The local `docker-compose.override.yml` modification is the known production-only runtime override from the deployment task.

## Current Dependency Health

Command:

```text
curl -sS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
exit 0
```

Result at 2026-05-07T10:50+0800:

```json
{
  "ok": true,
  "blocking": false,
  "dependencies": {
    "minio": { "ok": true },
    "mineru": {
      "ok": true,
      "healthOk": true,
      "submitProbe": {
        "enabled": true,
        "ok": true,
        "status": 202,
        "durationMs": 83,
        "taskId": "87996159-9be4-4d06-b19e-3bd29803407d",
        "error": null
      }
    },
    "ollama": {
      "ok": true,
      "chatOk": true,
      "durationMs": 763,
      "model": "qwen3.5:9b",
      "error": null
    }
  }
}
```

Important boundary: this lightweight health result can recover after the long AI request times out. Earlier manual-review evidence showed the same endpoint reporting `ollama.ok=false`, `chatOk=false`, `durationMs=15002`, and `Smoke test failed: The operation was aborted due to timeout` while the repair pass was still blocking.

## Direct Ollama Evidence

Command:

```text
curl -sS -m 5 http://127.0.0.1:11434/api/tags
exit 0
```

Observed model:

```json
{
  "name": "qwen3.5:9b",
  "size": 6594474711,
  "parameter_size": "9.7B",
  "quantization_level": "Q4_K_M"
}
```

Command:

```text
curl -sS -m 20 http://127.0.0.1:11434/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen3.5:9b","messages":[{"role":"user","content":"只回复 OK"}],"stream":false}'
exit 28
```

Result:

```text
curl: (28) Operation timed out after 20006 milliseconds with 0 bytes received
```

Process/resource check:

```text
ps -o pid,ppid,%cpu,%mem,etime,command -p <ollama-pids>
exit 0

PID    %CPU  %MEM  ELAPSED   COMMAND
665     5.7   0.4  16:12:23  ollama serve
764     0.0   0.1  16:12:21  ollama serve
60370   3.4  25.1     59:01  ollama runner ... qwen3.5:9b
```

System snapshot:

```text
Load Avg: 8.16, 8.11, 8.00
PhysMem: 31G used, 9454M compressor, 524M unused
```

Interpretation:

- Ollama is reachable enough for `/api/tags`.
- The required `qwen3.5:9b` chat path is not reliably responsive under a normal short prompt within 20s.
- The machine is memory-pressure/load sensitive, with the Ollama runner occupying a large resident footprint.

## Affected Tasks And Jobs

### `task-1778118934116`

State:

```json
{
  "id": "task-1778118934116",
  "stage": "ai",
  "state": "failed",
  "message": "AI 识别完成: failed",
  "mineruStatus": "completed",
  "parsedFilesCount": 99,
  "aiJobId": "ai-job-1778119321533-4dce"
}
```

AI job:

```json
{
  "id": "ai-job-1778119321533-4dce",
  "state": "failed",
  "message": "AI 识别异常: [AI 严格模式拦截] 不允许降级到骨架模型: AI Provider 调用全部失败: Ollama Provider Error: [TimeoutError] The operation was aborted due to timeout ... Duration: 299998ms, Timeout: 300000ms",
  "metadata": {
    "currentPhase": "first-pass-failed"
  }
}
```

Task event evidence:

```json
{
  "event": "ai-provider-request-started",
  "payload": {
    "timeoutMs": 300000,
    "inputLength": 78083
  }
}
{
  "event": "ai-provider-request-failed",
  "payload": {
    "durationMs": 300027,
    "errorMessage": "Ollama Provider Error: [TimeoutError] ... Duration: 299998ms, Timeout: 300000ms"
  }
}
```

### `task-1778120784621`

State after completion of the repair timeout:

```json
{
  "id": "task-1778120784621",
  "fileName": "走向成功_英语_二模卷16篇.pdf",
  "stage": "ai",
  "state": "failed",
  "message": "AI 识别完成: failed",
  "mineruStatus": "completed",
  "parsedFilesCount": 25,
  "aiJobId": "ai-job-1778120889758-8cab",
  "aiCompletedAt": "2026-05-07T02:36:09.713Z"
}
```

AI job:

```json
{
  "id": "ai-job-1778120889758-8cab",
  "state": "failed",
  "progress": 45,
  "message": "AI 识别异常: [AI 严格模式拦截] 不允许降级到骨架模型: repair 阶段超时 (abort-timeout, duration: 300002ms)，降级为 skeleton 结果",
  "metadata": {
    "currentPhase": "repair-timeout"
  }
}
```

Task event evidence:

```json
{
  "event": "ai-provider-request-started",
  "payload": {
    "timeoutMs": 300000,
    "inputLength": 26545
  }
}
{
  "event": "ai-provider-request-succeeded",
  "payload": {
    "durationMs": 178047,
    "usage": {
      "prompt_tokens": 11692,
      "completion_tokens": 512
    }
  }
}
{
  "event": "ai-provider-repair-failed",
  "payload": {
    "repairProviderDetails": {
      "timeoutKind": "abort-timeout",
      "durationMs": 300002,
      "phaseName": "repair-pass"
    }
  }
}
```

## Upload-Server Logs

Command:

```text
docker compose logs --tail=180 upload-server | rg -n 'ai-job-1778120889758-8cab|task-1778120784621|First pass|repair|TimeoutError|abort-timeout|AI 严格|Provider|completed|failed|JSON'
exit 0
```

Relevant lines:

```text
[ai-worker] Picking up job: ai-job-1778120889758-8cab (parseTask=task-1778120784621)
[ai-worker] First pass JSON parse failed, attempting repair for job ai-job-1778120889758-8cab...
[ai-worker] Provider ollama failed: Ollama Provider Error: [TimeoutError] The operation was aborted due to timeout (BaseURL: http://host.docker.internal:11434, Model: qwen3.5:9b, Duration: 300002ms, Timeout: 300000ms)
[ai-worker] Two-pass JSON repair failed for job ai-job-1778120889758-8cab: Ollama Provider Error: [TimeoutError] ...
[ai-worker] Job ai-job-1778120889758-8cab unexpected error: [AI 严格模式拦截] 不允许降级到骨架模型: repair 阶段超时 (abort-timeout, duration: 300002ms)，降级为 skeleton 结果
```

## Code Observations

- [server/services/ai/metadata-worker.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/services/ai/metadata-worker.mjs:61): strict mode sets `defaultTimeoutMs=300000`.
- [server/services/ai/metadata-worker.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/services/ai/metadata-worker.mjs:345): strict mode forces Ollama `qwen3.5:9b`, `timeoutMs=300000`, `ollamaTwoPassJsonRepair=true`, `temperature=0.1`.
- [server/services/ai/metadata-worker.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/services/ai/metadata-worker.mjs:597): two-pass repair starts when first-pass JSON parse/schema validation fails.
- [server/services/ai/metadata-worker.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/services/ai/metadata-worker.mjs:610): repair pass reuses the provider with the original markdown context and `num_predict=3072`.
- [server/services/ai/metadata-worker.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/services/ai/metadata-worker.mjs:646): repair timeout is caught and recorded as `repair-timeout`.
- [server/services/ai/metadata-worker.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/services/ai/metadata-worker.mjs:771): strict mode throws before skeleton fallback can be used.
- [server/services/ai/providers/ollama.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/services/ai/providers/ollama.mjs:36): Ollama provider sends `/api/chat`, `stream=false`, `think=false`, and `format=json` when JSON is expected.
- [server/services/ai/providers/ollama.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/services/ai/providers/ollama.mjs:58): Undici `headersTimeout`, `bodyTimeout`, and `AbortSignal.timeout` all use the same provider timeout.
- [server/services/ai/metadata-standard-v0.2.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/services/ai/metadata-standard-v0.2.mjs:408): repair prompt embeds the first-pass draft and a full canonical v0.2 schema instruction.
- [server/upload-server.mjs](/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026/server/upload-server.mjs:537): dependency-health Ollama smoke uses only `num_predict=2` and 15s timeout, so it can pass while production-sized metadata prompts still fail.

## Root-Cause Classification

Likely causes:

1. **Repair prompt/input size issue**: `task-1778120784621` first pass succeeded only after 178s with 11,692 prompt tokens and then entered a repair pass that embeds the draft plus full schema guidance. The repair pass uses `num_predict=3072` and timed out at 300s.
2. **Ollama process/model performance issue**: direct `/api/chat` with a trivial prompt timed out at 20s during/after the incident, and the host had high load and memory pressure. The 9B model is alive but not reliably responsive.
3. **Timeout policy mismatch**: dependency-health uses a very small 2-token smoke, while real first-pass/repair calls run for up to 300s. Health can briefly show green without proving production-sized AI metadata requests can complete.
4. **AI job stale-state handling is not the primary cause for these two jobs**: both jobs reached terminal `failed` states after provider timeout; stale recovery did not need to rescue them. However, the stale threshold is tied to `defaultTimeoutMs + 60s`, so a worker crash during a 300s pass could leave a job running until a later scan.

Not supported by current evidence:

- Missing Ollama model: `/api/tags` lists `qwen3.5:9b`.
- Silent skeleton fallback: strict mode threw and failed the job instead.
- MinerU parse failure: both affected tasks had `mineruStatus=completed`.

## Recommended Next Remediation Task

Recommended next task:

`P0 AI Metadata Repair Prompt And Timeout Hardening`

Suggested scope:

- Keep strict no-skeleton semantics.
- Add instrumentation for first-pass and repair prompt sizes, token estimates, and phase durations.
- Bound or simplify repair prompt input, especially when first pass already produced a draft-like object.
- Consider a smaller repair-specific `num_predict` or deterministic non-LLM schema normalization for draft-shaped JSON before invoking a second full LLM pass.
- Align dependency-health or add a separate opt-in AI metadata deep probe so lightweight health does not imply production-sized repair readiness.
- Add focused tests around JSON repair timeout behavior and strict-mode failure messaging.

No immediate restart/retry task is recommended from this evidence alone. Restarting Ollama may temporarily clear blockage, but it does not address the repeatable design risk: production-sized first-pass/repair prompts can consume the full 300s provider timeout and fail under strict mode.

## Review Required

Lucia review is required. Director decision may be required before any timeout-policy or model/prompt-policy change.
