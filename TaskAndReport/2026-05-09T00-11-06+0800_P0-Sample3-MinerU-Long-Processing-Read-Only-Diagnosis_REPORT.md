# Lucode Diagnosis Report: P0 Sample 3 MinerU Long-Processing Read-Only Diagnosis

Status: `STUCK_REQUIRES_DIRECTOR_DECISION`

## Basis

- Based on Lucia task brief: `TaskAndReport/2026-05-08T23-44-38+0800_P0-Sample3-MinerU-Long-Processing-Read-Only-Diagnosis_TASK.md`
- Target task: `task-1778249434820`
- Target material: `mat-1778249419780`
- Target MinerU task id: `ec9452cc-94e4-4b36-bb64-efba86f38cf6`
- Development workspace HEAD before report: `34acb2566cfa979c66cf55a8491e5d893e74ac12`
- Production workspace HEAD during diagnosis: `8092965c104cee57ff9cb739106e4320dfc22a7d`

## Executive Summary

Sample 3 is no longer legitimately processing in MinerU. Read-only MinerU API evidence shows:

- MinerU `/health`: `processing_tasks=0`, `queued_tasks=0`, `completed_tasks=26`.
- MinerU `/tasks/ec9452cc-94e4-4b36-bb64-efba86f38cf6`: `status=completed`, `completed_at=2026-05-08T15:14:21.454388+00:00`, `error=null`.
- MinerU `/tasks/.../result`: HTTP `200`, `content-type=application/zip`, body length `88604637`.

Luceon DB still shows the task as:

- task state/stage: `running` / `mineru-processing`
- message: `本地等待超时但 MinerU 仍在 processing，后台将继续观测`
- `metadata.mineruStatus=processing`
- `metadata.localTimeoutOccurred=true`
- material status: `processing`
- no AI metadata job for this task/material

Diagnosis: the issue is a terminal-state propagation / result-ingestion stuck state after MinerU completion, with stale observability also present. The safe next action requires Lucia/Director authorization because resolving it would require a write action such as a scoped non-resubmitting result-ingestion/takeover repair for this exact task, or a code fix plus controlled recovery task. I did not perform any repair.

## Current State Evidence

Timestamped read-only refresh at `2026-05-08T16:07:51.211Z`:

```json
{
  "task": {
    "id": "task-1778249434820",
    "state": "running",
    "stage": "mineru-processing",
    "message": "本地等待超时但 MinerU 仍在 processing，后台将继续观测",
    "materialId": "mat-1778249419780",
    "mineruTaskId": "ec9452cc-94e4-4b36-bb64-efba86f38cf6",
    "mineruStatus": "processing",
    "mineruLastStatusAt": "2026-05-08T15:10:39.917Z",
    "localTimeoutOccurred": true
  },
  "material": {
    "id": "mat-1778249419780",
    "status": "processing",
    "fileSize": 39063547,
    "mineruStatus": "processing",
    "objectName": "originals/mat-1778249419780/source.pdf"
  },
  "aiRelatedJobs": 0
}
```

Active counts at the same refresh:

- DB tasks total: `48`
- active tasks: only `task-1778249434820`
- MinerU-active Luceon tasks: `1`
- AI jobs total: `41`
- AI-active jobs: `0`

Short read-only observation window:

| Time UTC | Luceon task state/stage | Luceon mineruStatus | Material status/mineruStatus | MinerU API status |
| --- | --- | --- | --- | --- |
| `2026-05-08T16:09:29.484Z` | `running` / `mineru-processing` | `processing` | `processing` / `processing` | `completed` |
| `2026-05-08T16:09:59.498Z` | `running` / `mineru-processing` | `processing` | `processing` / `processing` | `completed` |
| `2026-05-08T16:10:29.507Z` | `running` / `mineru-processing` | `processing` | `processing` / `processing` | `completed` |
| `2026-05-08T16:10:59.513Z` | `running` / `mineru-processing` | `processing` | `processing` / `processing` | `completed` |

The task kept receiving updated timestamps without changing stage, while MinerU remained completed.

## MinerU API Evidence

Read-only direct checks:

```json
{
  "health": {
    "status": "healthy",
    "version": "3.1.0",
    "queued_tasks": 0,
    "processing_tasks": 0,
    "completed_tasks": 26,
    "failed_tasks": 0,
    "max_concurrent_requests": 1
  },
  "task": {
    "task_id": "ec9452cc-94e4-4b36-bb64-efba86f38cf6",
    "status": "completed",
    "backend": "pipeline",
    "created_at": "2026-05-08T14:10:38.924521+00:00",
    "started_at": "2026-05-08T14:10:38.925389+00:00",
    "completed_at": "2026-05-08T15:14:21.454388+00:00",
    "error": null
  },
  "result": {
    "httpStatus": 200,
    "contentType": "application/zip",
    "bodyLength": 88604637
  }
}
```

The result check was read-only and did not persist the ZIP or any signed URL.

`/__proxy/upload/ops/mineru/active-task?queryApi=true` also returned `mineruApiChecks=[{"mineruTaskId":"ec9452cc-94e4-4b36-bb64-efba86f38cf6","status":"completed","startedAt":"2026-05-08T14:10:38.925389+00:00"}]` while still showing the Luceon active task as `running` / `mineru-processing`.

`/__proxy/upload/ops/mineru/diagnostics` returned:

- MinerU healthy: `true`
- MinerU `processingTasks=0`
- MinerU `queuedTasks=0`
- Luceon `mineruProcessingTasks=["task-1778249434820"]`
- diagnosis: `healthy` / `idle`
- log observation: stale `Processing pages 714/714`, `100%`

## Log Freshness Evidence

Host log files:

- `/Users/concm/ops/logs/mineru-api.err.log`
  - size: `14878245`
  - mtime: `2026-05-08T23:14:19+0800`
  - tail ends around OCR and `Processing pages: 100%|...| 714/714 [00:57<00:00, 12.50it/s]`
- `/Users/concm/ops/logs/mineru-api.log`
  - size: `24001041`
  - mtime: `2026-05-09T00:08:19+0800`
  - latest relevant lines include repeated `GET /tasks/ec9452cc-94e4-4b36-bb64-efba86f38cf6 HTTP/1.1" 200 OK`

`/__proxy/upload/ops/mineru/global-observation` showed:

- phase: `Processing pages`
- progress: `714/714`, `100%`
- activityLevel: `log-observation-stale`
- observationStale: `true`
- observationStaleReason: `host-filesystem MinerU log file is stale while MinerU API is still processing`
- attribution: `task-1778249434820`
- attributionMode: `live-active`

This observation is stale relative to the direct MinerU task state, which is now `completed`.

## Task Event Evidence

`/__proxy/db/task-events?taskId=task-1778249434820` returned `1808` events. The latest tail was repeated timeout/processing observation events, for example:

- `2026-05-08T15:13:47.098Z`: `本地等待超时但 MinerU 仍在 processing，后台将继续观测`
- `2026-05-08T15:14:21.631Z`: `本地等待超时但 MinerU 仍在 processing，后台将继续观测`
- `2026-05-08T15:16:21.308Z`: `本地等待超时但 MinerU 仍在 processing，后台将继续观测`

No event tail evidence showed transition to `result-fetching`, result-store, `ai-pending`, or AI job creation.

Production upload-server log since `2026-05-08T23:10:00+08:00` contained:

```text
[task-worker] Task task-1778249434820: MinerU ec9452cc-94e4-4b36-bb64-efba86f38cf6 仍在 processing，保持 running 等待后续轮询接管
```

No later upload-server log line since `2026-05-09T00:00:00+08:00` matched this task id, MinerU id, `result-fetching`, `completed`, or resume error.

## Process / Runtime Evidence

Read-only process/session inspection:

- tmux sessions present: `luceon-sidecar`, `luceon-supervisor`, `mineru_api`, `mineru_gradio`
- MinerU API process present: `mineru-api --host 0.0.0.0 --port 8083`
- `node ops/mineru-log-observer.mjs` present
- Ollama serve/runner processes present

Dependency health was read-only and non-mutating:

- overall `ok=true`, `blocking=false`
- MinIO `ok=true`
- MinerU `ok=true`, `healthOk=true`, submitProbe disabled
- Ollama `ok=true`, `chatOk=true`, duration `8442ms`, model `qwen3.5:9b`

DB health was `ok=true`.

## Interpretation

The issue is not current MinerU throughput: MinerU is idle and the target MinerU task is completed with a result available.

The issue is not AI metadata execution yet: no AI metadata job exists for `task-1778249434820` / `mat-1778249419780`.

The issue is best classified as terminal-state propagation / result-ingestion stuck after local timeout, with stale log observation as a contributing observability symptom. The Luceon task keeps recording or refreshing `processing` even after the MinerU API reports `completed`.

Likely safe remediation direction, requiring authorization: run or implement a scoped non-resubmitting takeover/reconciliation for exactly `task-1778249434820` that reads the existing MinerU result and proceeds to result ingestion / MinIO parsed artifact storage / AI job creation. This must not re-upload, reparse, delete data, resubmit `/tasks`, alter timeouts/config/model/secrets, or restart services unless separately authorized.

## Commands Run

Development workspace:

| Command | Exit | Summary |
| --- | ---: | --- |
| `git status --short --branch` | 0 | clean, `## main...origin/main` |
| `git fetch origin` | 0 | remote refs synced |
| `git pull --ff-only origin main` | 0 | already up to date |
| `sed` reads of task brief and required docs | 0 | read task and role/policy/context documents |
| `rg` reads of task tracking and code references | 0/1 | found task #45 and relevant diagnostic code; one no-match `rg` returned 1 when no log lines matched after midnight |

Production workspace:

| Command | Exit | Summary |
| --- | ---: | --- |
| `git status --short --branch && git rev-parse HEAD && git rev-parse origin/main` | 0 | local `8092965c104cee57ff9cb739106e4320dfc22a7d`; origin `48df7aabe7383743077ac1cb76b8d23a467a17f1`; local override modified |
| Node read-only DB/API diagnostic script | 0 | task/material/AI job/active counts/MinerU ops/direct MinerU status collected |
| Direct MinerU result availability check | 0 | HTTP 200 `application/zip`, body length `88604637`; no file persisted |
| Host log stat/tail | 0 | err log stale at page progress 714/714; access log fresh with status GETs |
| `docker compose logs --since ... upload-server | rg ...` | 0/1 | one relevant pre-midnight worker line found; no post-midnight relevant match |
| `tmux ls` and `ps` read-only inspection | 0 | supervisor, sidecar, MinerU, Ollama processes present |
| 90-second read-only observation loop | 0 | Luceon remained `running` / `mineru-processing`; MinerU remained `completed` |

## Skipped Checks

- No TypeScript/build/smoke checks were run because this was a production read-only diagnosis task, not implementation.
- No MinerU submit probe was run because dependency-health default read-only check was sufficient and the task forbids creating unnecessary artifacts.
- No reparse, retry, new upload, cleanup, DB/MinIO mutation, service restart, Docker operation, config/model/timeout/secret change, or sample modification was run because all are forbidden by the task brief.

## Guardrail Confirmation

No forbidden mutation occurred:

- no restart, stop, kill, reload, rebuild, redeploy, or Docker/Compose mutation
- no model, timeout, config, secret, production override, code, DB row, MinIO object, Docker volume, task, artifact, log, or sample mutation
- no deletion, pruning, normalizing, moving, renaming, copying, retry, reparse, or new upload
- no signed URL or private credential persisted
- no production release-readiness claim

## Recommended Next Action

Lucia should review this evidence and either:

1. Issue a Director-authorized, narrowly scoped recovery task for `task-1778249434820` that performs non-resubmitting result ingestion from existing MinerU result and creates the downstream AI metadata job if parsed artifacts are stored successfully; or
2. Issue a code-level bugfix task if Lucia determines the stale-timeout takeover path is failing generally when MinerU transitions from `processing` to `completed` after local timeout.

I recommend option 1 first if the goal is to unblock the existing validation artifact, with a separate option 2 follow-up if the recovery exposes a repeatable bug in stale adjudication / resume logic.

Lucia review is required. Director decision is required before any write-side recovery against production task state or artifacts.
