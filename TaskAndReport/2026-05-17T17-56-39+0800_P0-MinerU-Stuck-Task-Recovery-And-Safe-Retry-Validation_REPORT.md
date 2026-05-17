# P0 MinerU Stuck Task Recovery And Safe Retry Validation Report

## Result

Status: `COMPLETED_NO_RESTART_NO_RETRY_REQUIRED`

Luceon executed the approved scoped recovery preflight for `task-1779010154264`. No MinerU stop/restart, safe retry, upload, cleanup, code change, or data mutation was performed, because the originally suspected stuck MinerU task completed naturally before any recovery mutation was needed.

This was not a production readiness, L3, pressure PASS, or go-live validation.

## Scope Boundary

- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Luceon ParseTask: `task-1779010154264`
- Material: `696446087521346`
- File: `曹云童八年级咬文嚼字.pdf`
- File size: `321137` bytes
- MinerU task: `935081dc-b871-45ba-95ff-d836d5e9731d`
- Original options: `backend=pipeline`, `enableOcr=false`, `enableFormula=true`, `enableTable=true`, `localTimeout=3600`, `maxPages=1000`

Forbidden actions were not performed: no pressure test, no additional upload, no DB/MinIO/Docker volume cleanup, no `docker compose down -v`, no broad restart, no code modification, no model/secret/sample mutation.

## Before Recovery Facts

The task originally appeared stuck during the manual single-PDF regression:

- Direct MinerU API had shown `status=processing`, `completed_at=null`, `error=null`, `queued_ahead=0`.
- Luceon DB had shown `running / mineru-processing / 50`.
- Host stderr business progress had appeared stopped near `Table-ocr rec ch: 0/2`.
- Diagnosis against milestone `v6.9` found no submit-path parameter regression in:
  - `server/services/mineru/local-adapter.mjs`
  - `server/lib/ops-mineru-log-parser.mjs`
  - `src/app/utils/mineruTaskOptions.ts`
  - `src/store/seedData.ts`

The first actionable conclusion was therefore a suspected long-running MinerU table OCR phase plus a separate log-observation channel problem.

## Recovery Preflight

At the recovery preflight, direct MinerU evidence showed the task had completed:

```text
GET http://127.0.0.1:8083/health
status=healthy
queued_tasks=0
processing_tasks=0
completed_tasks=2
failed_tasks=0
max_concurrent_requests=1
```

```text
GET http://127.0.0.1:8083/tasks/935081dc-b871-45ba-95ff-d836d5e9731d
status=completed
created_at=2026-05-17T09:29:22.387217+00:00
started_at=2026-05-17T09:29:22.387964+00:00
completed_at=2026-05-17T09:57:26.644479+00:00
error=null
queued_ahead=0
```

The apparent stuck phase was real work, not a terminal hang:

```text
Table-ocr rec ch: 100%|██████████| 2/2 [27:45<00:00, 832.85s/it]
Table-wireless Predict: 100%|██████████| 1/1
Table-wired Predict: 100%|██████████| 1/1
OCR-det ch: 100%|██████████| 34/34
OCR-rec Predict: 100%|██████████| 222/222
Processing pages: 100%|██████████| 8/8
```

## Final Task State

The Luceon task completed end-to-end:

```text
ParseTask task-1779010154264
state=review-pending
stage=review
progress=100
message=AI 识别完成: review-pending (待人工复核)
mineruStatus=completed
parsedFilesCount=10
aiJobId=ai-job-1779011847294-ba47
completedAt=2026-05-17T10:00:34.550Z
```

AI metadata recognition also completed:

```text
AI job ai-job-1779011847294-ba47
state=review-pending
model=qwen3.5:9b
first pass duration=73975ms
first pass failureKind=json_parse_failed
repair pass duration=105107ms
repair succeeded=true
final message=AI 识别完成 (179146ms)
```

The first AI output was truncated / JSON-parse failed, but the bounded repair pass succeeded. This is not a MinerU failure and does not require parse retry.

## Active Work Check

After completion:

```text
GET /__proxy/upload/ops/mineru/active-task
activeTask=null
currentProcessingTask=null
queuedTasks=[]
completedButNotIngestedTasks=[]
driftTasks=[]
submitRetryableTasks=[]
takeoverRequiredTasks=[]
historicalAiFailureTasks=[]
resultIngestionLagTasks=[]
diagnosticMode.taskSource=db-derived
diagnosticMode.directMineruChecked=true
```

Dependency health was non-blocking at the final read-only check:

```text
GET /__proxy/upload/ops/dependency-health?mineruSubmitProbe=false
ok=true
blocking=false
MinerU healthOk=true
MinerU admissionCircuit.state=closed
Ollama readinessState=resident-chat-succeeded
Ollama readinessSeverity=info
```

No submit-probe was run during this P0 closure.

## Runtime Ownership

MinerU remained owned by the expected host tmux session:

```text
tmux session: luceon-mineru
PID 60627: tmux new-session -d -s luceon-mineru ... bash ops/start-mineru-api.sh
PID 60629: /Users/concm/miniconda3/envs/mineru/bin/python3.10 ... mineru-api --host 0.0.0.0 --port 8083
```

Docker services relevant to Luceon remained healthy:

```text
cms-frontend       Up (healthy)
cms-upload-server  Up (healthy)
cms-db-server      Up (healthy)
cms-minio          Up (healthy)
```

## Log Observation Evidence

The original business issue completed, but the observation-chain defect remains:

Host logs:

```text
HOST_ERR inode=15046647 size=12212893 mtime=2026-05-17 17:57:26 +0800 /Users/concm/ops/logs/mineru-api.err.log
HOST_OUT inode=15046646 size=7788878  mtime=2026-05-17 18:02:29 +0800 /Users/concm/ops/logs/mineru-api.log
```

Upload-server container bind-mounted view:

```text
CTR_ERR inode=115547 size=12206074 mtime=2026-05-17 09:29:22.367685564 +0000 /host/mineru-logs/mineru-api.err.log
CTR_OUT inode=115548 size=7654480  mtime=2026-05-17 09:29:22.402451237 +0000 /host/mineru-logs/mineru-api.log
```

`/ops/mineru/global-observation` returned `{"observation":null}`, and no `mineru-log-observer.mjs` host sidecar process was running.

Conclusion: the page/upload-server path can still see stale container-mounted MinerU logs, even when the host log has newer truth. This is the root observation defect and remains assigned to Task 217.

## Actions Taken

- Ran read-only preflight and final runtime checks.
- Recorded the original task and MinerU final state.
- Did not stop or restart MinerU.
- Did not start the sidecar in this P0 closure, because the target task had already completed and Task 217 owns the durable sidecar-first fix.
- Did not run the `enableTable=false` safe retry, because the original parse completed successfully and AI reached review-pending.
- Did not upload, reparse, re-AI, pressure test, clean data, or mutate DB/MinIO/Docker volumes.

## Commands Run

Commands completed successfully unless noted:

```bash
git status --short --branch
rg -n "TASK-20260517-175639|task-1779010154264|Host-MinerU-Log-Sidecar|Stuck-Task-Recovery" TaskAndReport/TASK_TRACKING_LIST.md TaskAndReport
date '+%Y-%m-%d %H:%M:%S %z'
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
curl -sS --max-time 8 http://127.0.0.1:8083/health
curl -sS --max-time 8 http://127.0.0.1:8083/tasks/935081dc-b871-45ba-95ff-d836d5e9731d
stat -f 'HOST_ERR inode=%i size=%z mtime=%Sm path=%N' -t '%Y-%m-%d %H:%M:%S %z' /Users/concm/ops/logs/mineru-api.err.log
stat -f 'HOST_OUT inode=%i size=%z mtime=%Sm path=%N' -t '%Y-%m-%d %H:%M:%S %z' /Users/concm/ops/logs/mineru-api.log
curl -sS --max-time 10 http://127.0.0.1:8081/__proxy/upload/ops/mineru/active-task
curl -sS --max-time 10 'http://127.0.0.1:8081/__proxy/db/tasks?limit=10'
docker exec cms-upload-server sh -lc "stat -c 'CTR_ERR inode=%i size=%s mtime=%y path=%n' /host/mineru-logs/mineru-api.err.log; stat -c 'CTR_OUT inode=%i size=%s mtime=%y path=%n' /host/mineru-logs/mineru-api.log"
ps -p 60627,60629,68325,68326,68380,74610 -o pid,ppid,%cpu,%mem,stat,lstart,command
tail -n 80 /Users/concm/ops/logs/mineru-api.err.log
curl -sS --max-time 20 'http://127.0.0.1:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=false'
curl -sS --max-time 10 http://127.0.0.1:8081/__proxy/upload/ops/mineru/global-observation
ps aux | grep -E 'mineru-log-observer|ops/mineru-log-observer' | grep -v grep
```

Two exploratory URL checks returned expected 404-style HTML because those were not valid routes:

```bash
curl -sS --max-time 10 http://127.0.0.1:8081/__proxy/upload/tasks/active
curl -sS --max-time 8 'http://127.0.0.1:8081/__proxy/db/ai-jobs?limit=10'
```

These did not mutate runtime state.

## Risks And Residual Debt

1. MinerU table OCR can spend a long time in a single progress unit. In this case `Table-ocr rec ch 2/2` took about 27m45s. The UI must not treat a single stale-looking table OCR phase as terminal failure without direct MinerU/API/log evidence.
2. The Docker bind-mounted log view is stale and cannot be trusted as the authoritative live progress source.
3. The host sidecar was absent during the incident, so `/ops/mineru/global-observation` had no authoritative host-filesystem snapshot.
4. Task 217 remains required: make the host sidecar / structured observation path authoritative, make sidecar absence explicit, and stop letting container-mounted log staleness drive user-facing progress semantics.

## Closure

Task 216 is closed as operationally recovered without mutation. The original PDF reached `review-pending`, and no safe retry was needed.

Task 217 remains open for Lucode as the code-level root fix for MinerU progress observability.
