# Lucode Supplemental Report

Task ID: `TASK-20260507-125133-P0-Current-Main-Production-Deployment-And-Manual-Runtime-Regression`

Trigger: Director manual review feedback after deployment.

Reported issue:

- `task-1778130398304` showed no useful MinerU parsing log output during the run.
- UI indicated Ollama AI metadata recognition was blocked/impeded, yet the task eventually produced an AI metadata result.

Scope: read-only production diagnostics. No restart, repair, task mutation, DB cleanup, MinIO cleanup, Docker volume operation, or code change was performed.

## Task Outcome Facts

- Task: `task-1778130398304`
- Material: `2903150174662584`
- File: `向树叶学习：人工光合作用.pdf`
- Final state: `review-pending`
- Final stage: `review`
- Final message: `AI 识别完成: review-pending (待人工复核)`
- MinerU task id: `c2d76a57-b15a-4328-8bf0-e0a1230ea6e6`
- MinerU status: `completed`
- Parsed files count: `8`
- Parsed prefix: `parsed/2903150174662584/`
- Markdown object: `parsed/2903150174662584/full.md`
- Artifact manifest: `parsed/2903150174662584/artifact-manifest.json`
- AI job: `ai-job-1778130435700-d611`
- AI job state: `review-pending`
- AI provider/model: `ollama` / `qwen3.5:9b`
- AI duration: `81655ms`

## MinerU Log Finding

The task did parse successfully, but the task-level log observation did not show meaningful business progress.

Task metadata recorded:

- `mineruObservedProgress.activityLevel=log-observation-no-business-signal`
- `mineruObservedProgress.attribution=task-1778130398304`
- `mineruObservedProgress.attributionMode=live-active`
- `signalSummary.progressCount=0`
- `signalSummary.businessLogCount=0`
- `logSourceSelectedReason=latest-mtime-fallback`

However, host-side MinerU logs did contain relevant business output for the same run:

- `2026-05-07 13:06:48.261 ... Pipeline processing-window multi-file run. doc_count=1, total_pages=4`
- `2026-05-07 13:06:48.428 ... Pipeline processing window batch 1/1: 4/4 pages`
- `Processing pages: 100% ... 4/4`

The strongest diagnostic evidence is Docker bind-mount staleness/inconsistency:

- Host:
  - `/Users/concm/ops/logs/mineru-api.err.log`
  - inode `15046647`
  - size `14173631`
  - mtime `May 7 13:10`
- Container mount:
  - `/host/mineru-logs/mineru-api.err.log`
  - inode `150048`
  - size `14170947`
  - mtime `May 7 05:07`
- Host:
  - `/Users/concm/ops/logs/mineru-api.log`
  - inode `15046646`
  - size `18235113`
  - mtime `May 7 13:10`
- Container mount:
  - `/host/mineru-logs/mineru-api.log`
  - inode `150049`
  - size `18223352`
  - mtime `May 7 05:07`

This means the upload-server container / sidecar-visible log path is not seeing the latest host log inode/content even though `docker-compose.yml` declares:

```text
/Users/concm/ops/logs:/host/mineru-logs:ro,consistent
```

`docker inspect cms-upload-server` showed the running mount as:

```json
{"Type":"bind","Source":"/Users/concm/ops/logs","Destination":"/host/mineru-logs","Mode":"ro","RW":false,"Propagation":"rprivate"}
```

Likely consequence:

- MinerU itself parsed successfully.
- Host logs did contain business lines.
- The container-visible log mount was stale, so sidecar/task metadata saw `log-observation-no-business-signal` during the live task.
- This matches the Director's observation that the task detail did not show useful MinerU parsing logs.

Secondary timing issue:

- Later global observation had valid business signal but became `unattributed`.
- Its `contextTime` was `2026-05-07T05:06:48.000Z`.
- Task `mineruStartedAt` was `2026-05-07T05:06:48.217222+00:00`.
- The observation time is about `217ms` before the recorded start time, so the completed-window attribution guard can reject it as before-start even though it belongs to the same real-world run.
- This is a precision/window-boundary issue separate from the bind-mount staleness.

## AI / Ollama Finding

The AI metadata path was not silently degraded and did not use skeleton as the final provider.

Evidence from `ai-job-1778130435700-d611`:

- `state=review-pending`
- `providerId=ollama`
- `model=qwen3.5:9b`
- `message=AI 识别完成 (81655ms)`
- `result.aiClassificationProvider=ollama`
- `result.aiClassificationModel=qwen3.5:9b`
- `aiClassificationTwoPassAttempted=true`
- `aiClassificationRepairSucceeded=true`
- `aiClassificationDeterministicRepairSucceeded=true`
- `metadata.currentPhase=repair-deterministic-succeeded`
- `rawTrace.firstPass.durationMs=81615`
- `rawTrace.firstPass.failureKind=schema_invalid`

Interpretation:

- Ollama first pass did return a classification draft successfully.
- The draft was not canonical v0.2 schema, so it was marked `schema_invalid`.
- The new deterministic repair path normalized that recoverable draft into v0.2 without a second LLM repair call.
- The final result is low-confidence and `review-pending`, but it is a real Ollama-derived result, not skeleton fallback.

Likely UI/semantics issue:

- If the UI labels this path as "Ollama AI 元数据识别受阻", that wording is too coarse for the new accepted flow.
- `schema_invalid -> deterministic repair succeeded -> review-pending` should be shown as "AI 已完成，自动规范化，待复核" or equivalent, not as a blocking AI failure.
- Current dependency health at investigation time was healthy:
  - `blocking=false`
  - `ollama.ok=true`
  - `ollama.chatOk=true`
  - `ollama.model=qwen3.5:9b`

Related non-blocking ops signal:

- `/ops/dependency-repair/status` returned `sessions.ollama=false` but `services.ollamaReachable=true`.
- If UI treats missing Ollama tmux session as "AI blocked" despite Ollama being reachable, that should be split into an ops-session warning rather than AI dependency failure.

## Commands Run

- `curl -fsS http://localhost:8081/__proxy/db/tasks/task-1778130398304` -> exit `0`.
- `curl -fsS 'http://localhost:8081/__proxy/db/task-events?taskId=task-1778130398304'` -> exit `0`.
- `curl -fsS http://localhost:8081/__proxy/db/ai-metadata-jobs/ai-job-1778130435700-d611` -> exit `0`.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/global-observation` -> exit `0`.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task` -> exit `0`.
- `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` -> exit `0`.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status` -> exit `0`.
- `docker logs cms-upload-server --since '2026-05-07T05:06:30Z' --until '2026-05-07T05:09:10Z' ...` -> exit `0`.
- `tmux capture-pane -pt luceon-sidecar -S -300` -> exit `0`; sidecar pane showed only startup banner, not per-post details.
- `ls -li /Users/concm/ops/logs/mineru-api.log /Users/concm/ops/logs/mineru-api.err.log` -> exit `0`.
- `docker exec cms-upload-server ls -li /host/mineru-logs/mineru-api.log /host/mineru-logs/mineru-api.err.log` -> exit `0`.
- `tail -80 /Users/concm/ops/logs/mineru-api.err.log ...` -> exit `0`.
- `docker inspect cms-upload-server --format '{{json .Mounts}}'` -> exit `0`.

## Recommended Lucia Follow-Up Tasks

1. P0/P1 ops task: fix or redesign MinerU log visibility so the observer reads the same current log inode/content as the host, or stop relying on Docker bind-mounted log files for real-time task logs.
2. P1 attribution task: add a small timestamp tolerance around `mineruStartedAt` for completed-window attribution, because MinerU log timestamps are second-granularity while task start timestamps include sub-second precision.
3. P1 UI semantics task: distinguish `schema_invalid + deterministicRepairSucceeded` from actual AI blocking/failure. Do not show it as AI recognition blocked when provider is `ollama` and final job is `review-pending`.
4. P2 ops-status semantics task: separate "Ollama tmux session absent" from "Ollama service unreachable"; current health says Ollama is reachable and usable.

## Current Readiness Impact

Manual review can continue for functional task completion and metadata review.

Known limitation remains: MinerU task-level live log display is unreliable in the current production runtime because the container-visible log mount is stale/inconsistent.

This is not evidence of MinerU parse failure, and this case is not evidence of AI skeleton fallback. It is evidence of log-observation transport failure plus UI/diagnostic wording ambiguity.
