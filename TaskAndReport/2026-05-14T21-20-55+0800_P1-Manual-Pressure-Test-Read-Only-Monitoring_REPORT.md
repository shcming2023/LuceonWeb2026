# Test Acceptance Report: P1 Manual Pressure Test Read-Only Monitoring

- Task ID: `TASK-20260514-212055-P1-Manual-Pressure-Test-Read-Only-Monitoring`
- Task brief: `TaskAndReport/2026-05-14T21-20-55+0800_P1-Manual-Pressure-Test-Read-Only-Monitoring_TASK.md`
- Role: `TestAcceptanceEngineer`
- Final outcome: `FAILED`
- Recommendation: `fail`
- Report time: `2026-05-15T05:32+0800`
- Heartbeat automation: `luceon2026-testacceptanceengineer-check-task`, same-thread 30-minute monitoring; should stop after this report is handed to Director.

## Scope And Boundaries

- Workspaces used: development workspace and production deployment path.
- Production path entered: yes, read-only.
- GitHub sync: not run.
- No upload, cleanup, repair, reparse, re-AI, DB/MinIO/Docker volume/data mutation, service restart/rebuild, model/config/secret/sample mutation, or readiness/L3/go-live claim was performed.
- Baseline was captured before pressure tasks appeared: production HEAD `89271a1`, services healthy, upload health OK, dependency health non-blocking, active-task idle, direct MinerU idle, task/material counts `50/50`, no pressure-test tasks detected.

## Detection Method

Pressure-test task set was identified as tasks created after baseline newest task:

- Baseline newest task: `task-1778763994124`
- Baseline timestamp: `2026-05-14T13:06:34.255Z`
- Detected pressure-test tasks: `24`

## Monitoring Timeline

| Pass | Local time | Aggregate state | Assessment |
| --- | --- | --- | --- |
| Baseline | 2026-05-14T21:28+0800 | no pressure tasks | idle baseline captured |
| 1-15 | 2026-05-14T21:57 to 2026-05-15T04:30+0800 | progressed from pending/running to `11 review`, `1 running`, `12 pending` | running with progress |
| 16 | 2026-05-15T05:32+0800 | `20 review`, `3 failed/ai`, `1 running` | `FAILED` |

Detailed per-pass observations are in `TaskAndReport/2026-05-14T21-20-55+0800_P1-Manual-Pressure-Test-Read-Only-Monitoring_NOTES.md`.

## Failure Evidence

Final observation found 3 pressure-run terminal AI failures:

| Task | File | Stage | Failure |
| --- | --- | --- | --- |
| `task-1778765409131` | `走向成功_英语_二模卷16篇` | `failed/ai` | Ollama provider timeout at about `179956ms`; strict mode blocked skeleton fallback |
| `task-1778765412523` | `附件三：考务流程培训-纸笔标准考试` | `failed/ai` | Ollama provider timeout at about `180005ms`; strict mode blocked skeleton fallback |
| `task-1778765415701` | `2025` | `failed/ai` | repair stage timeout at about `180004ms`; strict mode blocked skeleton fallback |

The first observed terminal pressure-run failure was `task-1778765409131`, completed at `2026-05-14T21:02:11.292Z`.

## Runtime Evidence

- Upload health remained reachable: `{"ok":true,"service":"upload-server"}`.
- Direct MinerU health at final observation: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=91`, `failed_tasks=0`.
- Active processing task at final observation: `task-1778765417422`, `running/mineru-processing`, file `06第六章 长期股权投资与合营安排`.
- Global MinerU observation for active task remained live: `Table-ocr det`, `65/66`, `98%`, attributed to `task-1778765417422`.
- Direct Ollama checks in the monitoring sequence remained reachable and `qwen3.5:9b` was resident, but pressure-run AI calls still hit strict-mode timeout failures.
- Docker core services remained healthy in the monitoring sequence.

## Boundary Judgment

- `SUCCESS`: not met, because not every pressure-test task reached coherent success/review.
- `FAILED`: met, because one or more pressure-test tasks reached terminal failed state.
- `HUNG_OR_STALLED`: not the final classification, because progress continued and live MinerU progress was observable.
- `MACHINE_OR_SERVICE_DOWN`: not met, because services were reachable enough for normal monitoring.

## Skipped Checks

- Browser UI/console spot-check was not performed in the final failure pass because shell read-only runtime evidence was sufficient to establish the task-defined `FAILED` outcome.
- No source-file hashing was performed during active pressure work to avoid adding unnecessary load.
- No Ollama chat probe was performed during active pressure work.

## Risks And Residuals

- The pressure run exposed AI timeout failures under strict no-skeleton-fallback mode.
- MinerU continued processing and did not itself show direct failures in the final evidence.
- The final active task was still running; this report stops because the task brief defines any terminal pressure-task failure as `FAILED`.
- Director decision is required for whether to dispatch diagnosis/remediation work, retry failed tasks, or continue/stop the remaining active pressure work.
