# Lucode Report: P0 Pressure Restart Created Tasks Read-Only Terminal Observation

- Task ID: `TASK-20260510-161343-P0-Pressure-Restart-Created-Tasks-Read-Only-Terminal-Observation`
- Based on Lucia task brief: `TaskAndReport/2026-05-10T16-13-43+0800_P0-Pressure-Restart-Created-Tasks-Read-Only-Terminal-Observation_TASK.md`
- Assignee: Lucode
- Observation window: `2026-05-10T16:13:43+0800` to `2026-05-10T17:13:43+0800`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production path observed: `/Users/concm/prod_workspace/Luceon2026`
- Production UI/API base observed: `http://localhost:8081`
- Outcome label: `CREATED_TASKS_OBSERVATION_TIMEOUT`

## Scope

Lucode performed the Lucia-assigned read-only observation for the 20 production validation tasks created by Task 75. No new uploads were created. Sample 21 was not retried, samples 22-24 were not attempted, and no task, material, DB, MinIO object, Docker volume, log file, sample file, model, timeout, secret, override, or runtime configuration was modified.

## Summary

At the 60-minute stop point, the 20 target tasks had not reached terminal/manual-review state:

- `1` task remained `running/mineru-processing`: `task-1778400448971`.
- `19` tasks remained `pending/upload`.
- No AI metadata jobs were created for the target 20 tasks.
- Dependency health stayed non-blocking throughout observation.
- MinerU submit probe stayed successful.
- Admission circuit stayed closed.
- Ollama `qwen3.5:9b` stayed reachable/OK.

The immediate observation result is therefore not a dependency-health block or an admission-circuit block. The active first PDF is a 632-page document that MinerU itself reports as still `processing` under backend `pipeline`. Native MinerU logs show real pipeline activity, but progress is very slow in OCR detection within batch 2/10. The remaining 19 tasks are queued behind the single active MinerU processing slot.

## Target Tasks Observed

Target task IDs from the Lucia brief:

```text
task-1778400448971
task-1778400452107
task-1778400454526
task-1778400456661
task-1778400460190
task-1778400468632
task-1778400473241
task-1778400478684
task-1778400481740
task-1778400487246
task-1778400490743
task-1778400493794
task-1778400498868
task-1778400501915
task-1778400507058
task-1778400513155
task-1778400516082
task-1778400518537
task-1778400521108
task-1778400526749
```

Final observed aggregate at `2026-05-10T17:13:43+0800`:

```json
{
  "counts": {
    "running/mineru-processing": 1,
    "pending/upload": 19
  },
  "allTerminal": false,
  "blocking": false,
  "health": {
    "status": 200,
    "ok": true,
    "blocking": false,
    "mineruOk": true,
    "submitOk": true,
    "ollamaOk": true
  },
  "circuit": {
    "status": 200,
    "open": false,
    "state": "closed",
    "reason": "mineru-submit-recovery-pending",
    "counts": {
      "parsePending": 19,
      "parseRunning": 1,
      "aiPending": 0,
      "aiRunning": 0
    }
  },
  "activeTask": {
    "id": "task-1778400448971",
    "state": "running",
    "stage": "mineru-processing",
    "progress": 50,
    "updatedAt": "2026-05-10T09:13:41.795Z",
    "warn": "mineru-status-query-timeout"
  }
}
```

## Active MinerU Task Evidence

Active Luceon task:

- Task: `task-1778400448971`
- Material: `pressure-restart-20260510160726-01`
- File: `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express).pdf`
- File size recorded in task snapshot: `52964792`
- Luceon state/stage: `running/mineru-processing`
- Luceon progress/message: `50`, `MinerU 正在解析`
- MinerU task id: `802bcc5b-1f0b-4ee6-abf4-833e2e3c8a26`
- Effective backend from task snapshot: `pipeline`
- Parse method: `ocr`
- Warning in Luceon active-task snapshot: `_synthetic_warn=mineru-status-query-timeout`

Direct MinerU task query:

```json
{
  "task_id": "802bcc5b-1f0b-4ee6-abf4-833e2e3c8a26",
  "status": "processing",
  "backend": "pipeline",
  "created_at": "2026-05-10T08:07:32.758441+00:00",
  "started_at": "2026-05-10T08:07:32.759199+00:00",
  "completed_at": null,
  "error": null,
  "queued_ahead": 0
}
```

Direct MinerU health after observation:

```json
{
  "status": "healthy",
  "version": "3.1.0",
  "queued_tasks": 86,
  "processing_tasks": 1,
  "completed_tasks": 37,
  "failed_tasks": 0,
  "max_concurrent_requests": 1,
  "processing_window_size": 64
}
```

Native MinerU log path currently in use:

- `/Users/concm/ops/logs/mineru-api.log`
- `/Users/concm/ops/logs/mineru-api.err.log`

Important native MinerU log evidence:

```text
2026-05-10 16:07:37.498 ... Pipeline processing-window multi-file run. doc_count=1, total_pages=632, window_size=64, total_batches=10
2026-05-10 16:07:41.034 ... Pipeline processing window batch 1/10: 64/632 pages, batch_pages=64, doc_slices=doc0:1-64
2026-05-10 16:20:44.055 ... Pipeline processing window batch 2/10: 128/632 pages, batch_pages=64, doc_slices=doc0:65-128
OCR-det ch: 35%|...| 22/62 [00:37<04:27, 6.70s/it]
OCR-det ch: 39%|...| 24/62 [05:18<54:13, 85.62s/it]
OCR-det ch: 42%|...| 26/62 [13:08<1:48:58, 181.62s/it]
OCR-det ch: 56%|...| 35/62 [20:22<1:01:41, 137.08s/it]
OCR-det ch: 61%|...| 38/62 [29:10<1:22:05, 205.24s/it]
```

Interpretation: MinerU is not merely invisible or completely stopped. The native log shows the `pipeline` backend is active on a large 632-page PDF, and the slowest visible phase is OCR detection within batch 2/10. Because `max_concurrent_requests=1`, the remaining 19 tasks stay behind this active processing task.

## UI Observability Finding

Director noted during observation that the task page previously showed MinerU log/progress semantics that made it possible to judge whether parsing was advancing normally. In this observation, the page/API-facing Luceon task state stayed at generic `MinerU 正在解析` / `50%`, while the actionable runtime semantics were only visible in native MinerU logs:

- `Pipeline processing window batch 2/10`
- page window progress such as `128/632 pages`
- phases such as `MFR Predict`, `Table-ocr`, `OCR-det ch`, `OCR-rec`
- slow phase timings that distinguish slow progress from a dead task

This is a production observability gap requiring Lucia analysis. It should not be treated as proof that MinerU selected the wrong engine: the effective backend is `pipeline`. The gap is that the operator-facing task page no longer exposes enough MinerU phase/batch/page semantics to monitor long-running parse health without shell access to native logs.

## Commands Run

All commands were read-only except writing this report and updating the task tracking list after observation.

```text
git status --short --branch
exit 0: ## main...origin/main

git fetch origin
exit 0

git pull --ff-only origin main
exit 0: Already up to date.

sed -n '1,260p' TaskAndReport/2026-05-10T16-13-43+0800_P0-Pressure-Restart-Created-Tasks-Read-Only-Terminal-Observation_TASK.md
exit 0

date '+%Y-%m-%dT%H:%M:%S%z'
exit 0: 2026-05-10T16:27:06+0800

node read-only observation scripts against:
- http://localhost:8081/__proxy/db/tasks
- http://localhost:8081/__proxy/db/materials
- http://localhost:8081/__proxy/db/ai-metadata-jobs
- http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true
- http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit
- http://localhost:8081/__proxy/upload/ops/mineru/active-task
exit 0

curl -sS --max-time 5 http://localhost:8083/health
exit 0

curl -sS --max-time 8 http://localhost:8083/tasks/802bcc5b-1f0b-4ee6-abf4-833e2e3c8a26
exit 0

ps aux | rg -i 'mineru|magic-pdf|uvicorn|fastapi' || true
exit 0

tail -n 240 /Users/concm/ops/logs/mineru-api.log
exit 0

tail -n 240 /Users/concm/ops/logs/mineru-api.err.log
exit 0

rg -n 'Pipeline processing window batch|Pipeline processing-window|OCR-det ch|MFR Predict|Table-ocr det|Processing pages' /Users/concm/ops/logs/mineru-api.err.log | tail -40
exit 0
```

## Checks Skipped

- No TypeScript/build/smoke checks were run. The Lucia brief was a read-only production observation task, not an implementation task.
- No validation uploads were run. The brief explicitly forbade new uploads, retrying sample 21, or attempting samples 22-24.
- No repair/retry/cleanup was run. The brief explicitly forbade task/material/DB/MinIO/Docker/log/sample/artifact mutation.

## Risks And Residual Issues

- The 20 created tasks did not reach terminal/manual-review state within the assigned 60-minute window.
- The first active task is large and slow: `632` pages, batch processing with `window_size=64`, and visible slow OCR detection spans in native logs.
- `max_concurrent_requests=1` means one very large PDF can block all later queued parse tasks for a long time.
- Luceon dependency health and admission circuit remain green while operator-visible task progress remains generic, so readiness checks alone do not expose long-running per-task progress quality.
- Operator-facing task page observability appears insufficient for pressure-test supervision; native MinerU logs currently carry the useful phase/batch/page semantics.
- No AI recognition conclusion can be made for this run because no target task reached parsed-output/AI-job creation during the observation window.

## Lucia Review Required

Lucia review is required. Recommended review focus:

- whether this should be classified as acceptable slow processing for a very large PDF, or as a production-line throughput/governance blocker;
- whether task-page MinerU log semantics must be restored or redesigned before further pressure validation;
- whether large-PDF admission, timeout, progress, queue fairness, or batch/window observability rules should become new Lucia task briefs;
- whether future pressure validation should separate "submit-path health", "active processing liveness", "queue drain", and "operator-visible parse progress" as distinct gates.

