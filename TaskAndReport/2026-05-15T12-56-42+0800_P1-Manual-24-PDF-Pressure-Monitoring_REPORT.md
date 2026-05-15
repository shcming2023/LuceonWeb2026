# Test Acceptance Report: P1 Manual 24-PDF Pressure Monitoring

- Task ID: `TASK-20260515-125642-P1-Manual-24-PDF-Pressure-Monitoring`
- Based on Director task brief: `TaskAndReport/2026-05-15T12-56-42+0800_P1-Manual-24-PDF-Pressure-Monitoring_TASK.md`
- Assignee role: `TestAcceptanceEngineer`
- Report time: 2026-05-15T19:10:42+0800
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Recommendation: `blocked`

## Boundary

This report covers read-only monitoring of the User-submitted 24-PDF pressure window after the User-reported frontend reset. It does not claim pressure PASS, L3, release readiness, production readiness, production上线, or go-live readiness.

No upload, cleanup/reset, manual or extra MinerU submit-probe, retry, reparse, re-AI, cancel, repair, service restart, rebuild, redeploy, config mutation, secret mutation, model mutation, sample mutation, DB/MinIO/Docker mutation, Docker down/down-v/prune, or volume operation was performed by TestAcceptanceEngineer.

## Branch And Runtime State

Development branch/status at monitoring pass:

```text
## main...origin/main
```

Development HEAD observed during the monitoring pass:

```text
74bdd32
```

Production branch/status:

```text
## main...origin/main
 M .gitignore
 M docker-compose.override.yml
 M docs/codex/TEST_MATRIX.md
 M docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md
 M ops/runtime-ownership-status.sh
 M server/db-server.mjs
 M server/tests/worker-smoke.mjs
 M src/app/components/BatchUploadModal.tsx
 M src/app/pages/SourceMaterialsPage.tsx
```

Production HEAD:

```text
1716add
```

The production workspace was dirty before this report and was treated as runtime evidence only.

## Read-Only Commands And Endpoints Used

All commands and endpoints below were read-only:

- `git status --short --branch`
- `git rev-parse --short HEAD`
- `curl -fsS http://localhost:8081/__proxy/upload/health`
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=false'`
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit`
- `curl -sS --max-time 20 http://localhost:8081/__proxy/upload/ops/mineru/active-task`
- `curl -sS --max-time 20 http://localhost:8081/__proxy/db/tasks`
- `curl -sS --max-time 20 http://localhost:8081/__proxy/db/materials`
- `curl -sS --max-time 20 http://localhost:8081/__proxy/db/ai-metadata-jobs`
- `curl -sS --max-time 10 http://127.0.0.1:8083/health`
- `curl -sS --max-time 15 http://127.0.0.1:8083/tasks/f8e44788-db97-4273-89da-dc5bbfa29d71`
- `lsof -nP -iTCP:8083 -sTCP:LISTEN`
- `tmux list-sessions`
- `tail -n` on `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log`
- HTTP accessibility check for `/cms/tasks`

No `mineruSubmitProbe=true` endpoint was called.

## Pressure Window Identification

The observed pressure window used tasks submitted after `2026-05-15T12:56:42+0800`. Twenty-four pressure-run tasks were visible in the DB. The first observed submissions were around `2026-05-15T05:07:37Z` to `2026-05-15T05:08:09Z`.

## Snapshot Timeline

| Time +0800 | Observed State |
| --- | --- |
| 13:08 | 24 total: 1 running, 23 pending. Dependency and admission checks did not show a terminal pressure result. |
| 13:40 | 24 total: 1 review-pending, 1 running, 22 pending. |
| 14:10 | 24 total: 1 review-pending, 1 running, 22 pending. MinerU logs still showed progress, so the active task was not treated as hung. |
| 14:40 | 24 total: 1 review-pending, 1 running, 22 pending. Active-task diagnostics showed local timeout, but logs still showed progress. |
| 15:10 | 24 total: 2 review-pending, 1 running, 21 pending. |
| 15:40 | 24 total: 3 review-pending, 1 running, 20 pending. |
| 16:10 | 24 total: 4 review-pending, 1 running, 19 pending. |
| 16:55 | 24 total: 4 review-pending, 1 running, 19 pending. The 91.5 MB task had local timeout evidence but later continued into AI. |
| 17:25 | 24 total: 4 review-pending, 1 AI-running, 1 MinerU-running, 18 pending. |
| 17:43 | 24 total: 5 review-pending, 1 MinerU-running, 18 pending. The 91.5 MB file reached review-pending. |
| 18:34 | 24 total: 5 review-pending, 1 MinerU-running, 18 pending. Direct MinerU health was unreachable, no listener on 8083 was visible, and no tmux server was visible, while stale logs still contained earlier progress. |
| 19:10 | 24 total: 5 review-pending, 1 MinerU-running, 18 pending. Upload health stayed OK, but dependency-health reported MinerU `connect ECONNREFUSED`, direct MinerU health and task API failed, no 8083 listener was visible, and no tmux session was visible. This is the stop-condition snapshot for system-level blocking. |

## Final Counts

Pressure-run DB task count:

```json
{
  "total": 24,
  "byState": {
    "review-pending": 5,
    "running": 1,
    "pending": 18
  },
  "byStage": {
    "review": 5,
    "mineru-processing": 1,
    "upload": 18
  },
  "failed": 0
}
```

AI metadata jobs:

```json
{
  "total": 5,
  "byState": {
    "review-pending": 5
  },
  "running": 0,
  "failed": 0
}
```

Completed/review-pending examples included:

- `Cambridge IGCSE(0607) International Mathematics Coursebook_2023(Hodder Express).pdf`, 52,964,792 bytes, `review-pending`
- `Cambridge IGCSE(0607) International Mathematics Coursebook Extended_2018(Haese Mathematics).pdf`, 45,247,007 bytes, `review-pending`
- `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Hodder Express).pdf`, 43,536,275 bytes, `review-pending`
- `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Cambridge University Press).pdf`, 40,235,936 bytes, `review-pending`
- `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics _2018(Haese Mathematics).pdf`, 91,501,329 bytes, `review-pending`

No task-level `failed` records were observed at the final snapshot. The blocked recommendation is therefore based on system/runtime observability and MinerU availability, not on declaring the 24 PDFs as content-level failed.

## Active MinerU Evidence

The final active backend task was:

```text
taskId: task-1778821666605
materialId: 2299860817314472
file: Cambridge IGCSE(0580) Extended Mathematics Student Book_2018(Oxford University Press).pdf
sizeBytes: 96516982
stage: mineru-processing
state: running
mineruTaskId: f8e44788-db97-4273-89da-dc5bbfa29d71
```

Active-task diagnostics reported:

```text
message: MinerU 正在处理，但日志观测滞后：backend=pipeline，相位 OCR 检测，批次 1/10，页 64/578
progress: 50
log phase: OCR-det ch
log percent: 52
log current/total: 36/69
logUpdatedAt: 2026-05-15T10:26:09.721Z
localTimeoutOccurred: true
synthetic warning: mineru-status-query-timeout
```

At the final stop-condition snapshot:

- direct MinerU `/health` failed with connection refused;
- direct MinerU `/tasks/f8e44788-db97-4273-89da-dc5bbfa29d71` failed with connection refused;
- `lsof -nP -iTCP:8083 -sTCP:LISTEN` returned no listener;
- `tmux list-sessions` reported no tmux server;
- `dependency-health?mineruSubmitProbe=false` reported `mineru.ok=false`, `healthOk=false`, `connect ECONNREFUSED`, and `blocking=true`.

## Dependency And Admission Findings

Upload health remained reachable:

```json
{"ok":true,"service":"upload-server"}
```

Final dependency-health without submit probe reported:

```json
{
  "ok": false,
  "blocking": true,
  "dependencies": {
    "minio": {"ok": true},
    "mineru": {
      "ok": false,
      "healthOk": false,
      "error": "connect ECONNREFUSED",
      "submitProbe": {"enabled": false}
    },
    "ollama": {
      "ok": true,
      "readinessState": "resident-chat-succeeded",
      "model": "qwen3.5:9b"
    }
  }
}
```

Admission circuit was closed, with counts showing the queue still blocked behind MinerU processing:

```json
{
  "state": "closed",
  "counts": {
    "parsePending": 18,
    "parseRunning": 1,
    "aiPending": 0,
    "aiRunning": 0
  }
}
```

## UI And Operator Semantics

`/cms/tasks` remained HTTP-accessible at the final snapshot. However, the operator-facing semantics were not sufficient to confidently understand the run without backend and log correlation:

- The backend active task still reported `running` / `mineru-processing`.
- The active-task message said MinerU was processing but logs were stale.
- Direct MinerU APIs and direct health were unreachable.
- Host-level evidence showed no visible listener on 8083 and no expected tmux session.
- Dependency-health marked MinerU as unavailable and blocking.

This mismatch makes the page/backend/log semantics hard for a human operator to interpret during a long pressure run. The problem is not just page wording: current health, direct API, process/listener, and queued task evidence disagree in a way that requires engineering diagnosis.

## AI/Ollama Findings

Ollama readiness stayed healthy in the final dependency-health check:

```text
readinessState: resident-chat-succeeded
model: qwen3.5:9b
durationMs: 408
```

Five AI metadata jobs were observed and all were `review-pending`. No AI job failure was observed in the final pressure-window DB snapshot. The final blocker is MinerU/runtime availability and observability, not AI/Ollama failure.

## Failed Tasks And Retry Candidates

No task-level `failed` records were observed in the final snapshot. There were no concrete failed retry candidates to classify.

The remaining 19 non-terminal tasks should not be classified as content failures from this evidence:

- 1 task was still recorded as `running` / `mineru-processing`;
- 18 tasks remained `pending` / `upload`;
- the system-level MinerU service path became unavailable before the pressure window reached terminal completion.

## Acceptance Boundary

The 24-PDF pressure window did not reach terminal completion. It also did not show isolated task-level failures that could simply be retried while the rest of the run continued normally. Instead, the monitoring reached a system-level blocked condition:

- MinerU host service became unreachable by direct health and direct task API;
- no host listener on 8083 was visible;
- no expected tmux session was visible;
- dependency-health reported MinerU `connect ECONNREFUSED` and `blocking=true`;
- 18 tasks remained queued and 1 task remained running in backend state.

Recommendation: `blocked`. Director should review this report and decide whether to issue an engineering follow-up for MinerU runtime ownership/recovery, worker-state reconciliation, and operator progress semantics before any release-boundary decision.

## Recommended Next Engineering Work

Suggested follow-up scope for Director consideration:

1. Reconcile MinerU runtime ownership: expected tmux/session/process/port evidence versus actual production runtime.
2. Make active-task and dependency-health semantics incorporate direct MinerU API, host listener/process evidence, and log freshness clearly.
3. Improve `/cms/tasks` operator semantics so stale log progress, backend running state, and service-unreachable state are visually distinguishable.
4. Preserve the important distinction that successfully completed large files are positive task-level evidence, while the current run still blocks on system observability and MinerU availability.

## Director Decision Needed

Yes. Director should decide whether this task is accepted as a blocked pressure-monitoring result, whether to dispatch engineering recovery/observability work, and whether any further pressure validation should wait until MinerU runtime ownership and progress semantics are corrected.
