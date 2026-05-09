# P0 24 PDF Pressure Test Failure Field Report

Report time: 2026-05-10T07:45:14+0800  
Reporter: Lucode  
Reviewer: Lucia  
Status: Field evidence submitted for Lucia review  
Branch: `main`  
Base HEAD before report: `20d08d5` (`Record parsed zip review head`)  
Report commit: pending at report creation; see pushed main HEAD after this report is committed.

## Scope

This report records the Director-authorized 24 PDF pressure-test monitoring outcome from the production runtime at:

- Production path: `/Users/concm/prod_workspace/Luceon2026`
- Runtime URL: `http://localhost:8081`
- Batch task prefix: `task-177833`

The monitoring and this report were based on Director's explicit instruction to monitor the submitted 24 PDFs and the later instruction to write the failure report into `TaskAndReport/`.

No code change, DB edit, MinIO cleanup, Docker volume cleanup, task deletion, material deletion, artifact deletion, secret change, model change, timeout change, or provider override change was performed.

## Executive Summary

The 24 PDF pressure test failed completely.

- Total batch tasks identified: 24
- Failed tasks: 24
- Completed / review-pending tasks: 0
- AI metadata jobs for this batch: 0
- Active / queued Luceon tasks after failure: 0
- MinIO: available
- Ollama: available, `qwen3.5:9b` chat probe passed
- MinerU `/health`: still reports healthy
- MinerU `/tasks` submit path: failing with HTTP 500

The failure pattern points to a MinerU half-failed runtime state, not an Ollama or MinIO failure.

## Key Timeline

- 2026-05-09T13:21:40Z to 2026-05-09T13:22:05Z: the 24 PDF batch was created in production DB as tasks `task-1778332899728` through `task-1778332925516`.
- 2026-05-09T13:21:45Z: the first task submitted to MinerU as `5fca4aa1-1169-4be4-b2e0-887dfea6ef59`.
- 2026-05-09T14:10:05Z: last captured useful MinerU business progress for the first large PDF was around `MFR Predict 57%`.
- 2026-05-09T14:21:47Z: Luceon recorded `localTimeoutOccurred=true` for the first task.
- 2026-05-09T14:42:53Z: first task was confirmed failed with message `MinerU 任务记录已丢失 (404)，需人工审计`.
- 2026-05-09T14:42:53Z to 2026-05-09T14:46:33Z: the following 23 tasks failed while trying to submit to MinerU `/tasks`, all with HTTP 500.
- 2026-05-10T07:45:14+0800: final read-only field capture confirmed the batch state remained 24 failed / 0 AI jobs.

## Current Final State

Final status counts from `/__proxy/db/tasks`:

```json
{
  "failed / mineru-processing": 1,
  "failed / execution-failed": 23
}
```

AI jobs:

```json
{
  "aiJobCountForBatch": 0
}
```

Active-task diagnostics:

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

Dependency-health with MinerU submit probe:

```json
{
  "ok": false,
  "blocking": true,
  "dependencies": {
    "minio": {
      "ok": true
    },
    "mineru": {
      "ok": false,
      "healthOk": true,
      "error": "submit probe failed: HTTP 500: Internal Server Error",
      "submitProbe": {
        "enabled": true,
        "ok": false,
        "status": 500,
        "error": "HTTP 500: Internal Server Error"
      }
    },
    "ollama": {
      "ok": true,
      "model": "qwen3.5:9b",
      "chatOk": true
    }
  }
}
```

## First Task Failure

First task:

- Task ID: `task-1778332899728`
- Material ID: `2660403436064804`
- Title: `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express)`
- Size: `52964792` bytes
- MinerU task ID: `5fca4aa1-1169-4be4-b2e0-887dfea6ef59`
- Final state: `failed`
- Final stage: `mineru-processing`
- Last observed phase: `MFR Predict`
- Last observed percent: `57`
- Local timeout: `true`
- Local timeout at: `2026-05-09T14:21:47.617Z`
- Final message: `[failed 已确认] MinerU 任务记录已丢失 (404)，需人工审计`

Interpretation:

The first large PDF did submit to MinerU and began processing. It later entered a stale / timeout / task-record-lost path. Luceon correctly did not silently continue as success and instead marked it failed.

## Subsequent 23 Task Failures

Tasks 2 through 24 did not reach AI and did not receive MinerU task IDs. They all failed at MinerU submission:

```text
[local-mineru] 执行失败: MinerU 提交失败: 500 | Endpoint: http://192.168.31.33:8083/tasks | Body: Internal Server Error | Config: backend=pipeline, parse_method=ocr, zip=true
```

This shows that after the first large PDF failure path, MinerU `/health` could still respond, but the real submit path `/tasks` was no longer usable.

## Batch Task List

| # | Task ID | Material ID | State / Stage | Title |
| ---: | --- | --- | --- | --- |
| 1 | `task-1778332899728` | `2660403436064804` | `failed / mineru-processing` | Cambridge IGCSE(0607) International Mathematics Coursebook_2023(Hodder Express) |
| 2 | `task-1778332900778` | `3785095472957476` | `failed / execution-failed` | Cambridge IGCSE(0607) International Mathematics Coursebook Extended_2018(Haese Mathematics) |
| 3 | `task-1778332901778` | `1861858539766420` | `failed / execution-failed` | Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Hodder Express) |
| 4 | `task-1778332902806` | `798740830861540` | `failed / execution-failed` | Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Cambridge University Press) |
| 5 | `task-1778332904211` | `69302122003892` | `failed / execution-failed` | Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics _2018(Haese Mathematics) |
| 6 | `task-1778332906291` | `3496125056768388` | `failed / execution-failed` | Cambridge IGCSE(0580) Extended Mathematics Student Book_2018(Oxford University Press) |
| 7 | `task-1778332908313` | `4203382399454388` | `failed / execution-failed` | Cambridge IGCSE(0580) Extended Mathematics Practice Book__2023(Cambridge University Press) |
| 8 | `task-1778332910853` | `3433243414059716` | `failed / execution-failed` | Cambridge IGCSE(0580) Core and Extended Mathematics_2023(Hodder Education) |
| 9 | `task-1778332912922` | `1023329163273860` | `failed / execution-failed` | Cambridge IGCSE(0580) Core and Extended Mathematics_2022(Cambridge University Press) |
| 10 | `task-1778332915738` | `3264317226441268` | `failed / execution-failed` | Cambridge IGCSE(0580) Core and Extended Mathematics_2018(Hodder Education) |
| 11 | `task-1778332916962` | `2111484943644980` | `failed / execution-failed` | Cambridge IGCSE(0580) Core and Extended Mathematics_2018(Cambridge University Press) |
| 12 | `task-1778332918153` | `1457070043185492` | `failed / execution-failed` | Cambridge IGCSE(0580) Core Mathematics_2023(Hodder Education) |
| 13 | `task-1778332920006` | `2902439459228852` | `failed / execution-failed` | PDF document-4F18-A8A3-62-0 |
| 14 | `task-1778332920982` | `4068939494100132` | `failed / execution-failed` | G7_Workbook_ready_to_print |
| 15 | `task-1778332921473` | `1101788571106084` | `failed / execution-failed` | 走向成功_英语_二模卷16篇 |
| 16 | `task-1778332921863` | `4200427877673460` | `failed / execution-failed` | 向树叶学习：人工光合作用 |
| 17 | `task-1778332922222` | `1470195118213492` | `failed / execution-failed` | 期末质量分析及建议（曹云童 ） |
| 18 | `task-1778332922585` | `3407622806475268` | `failed / execution-failed` | 蓝月、血月、橙月？月亮为啥还会变色？ |
| 19 | `task-1778332922974` | `2787042895001796` | `failed / execution-failed` | 附件三：考务流程培训-纸笔标准考试 |
| 20 | `task-1778332923690` | `2891671666638340` | `failed / execution-failed` | 出国 |
| 21 | `task-1778332924108` | `360798154234324` | `failed / execution-failed` | 财务回执(￥50,000.00).pdf |
| 22 | `task-1778332924495` | `1474212513467508` | `failed / execution-failed` | 2025 |
| 23 | `task-1778332924901` | `4189308393428388` | `failed / execution-failed` | 2025_2026学年春季课程中数G8_提取 |
| 24 | `task-1778332925516` | `2753886934221700` | `failed / execution-failed` | 06第六章 长期股权投资与合营安排 |

## Commands Run

Commands were read-only except for deleting the obsolete heartbeat automation after the batch reached a failed terminal state and writing this report / tracking-list update after Director authorization.

| Command | Path | Exit | Purpose |
| --- | --- | ---: | --- |
| `git status --short --branch && git fetch origin && git pull --ff-only origin main` | development workspace | 0 | Sync before reporting |
| `curl -sS --max-time 10 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` | production workspace | 0 | Dependency health with real MinerU submit-path probe |
| `curl -sS --max-time 10 http://localhost:8081/__proxy/upload/ops/mineru/active-task` | production workspace | 0 | Active/queued/takeover diagnostics |
| `node - <<'NODE' ... fetch /__proxy/db/tasks, /materials, /ai-metadata-jobs ... NODE` | production workspace | 0 | Batch state summary |
| `codex_app.automation_update mode=delete id=lucode-24-pdf-pressure-monitor` | current thread | 0 | Stop obsolete monitor after all tasks reached failed state |

## Skipped Checks

- No TypeScript/build/smoke tests were run because this was a production field report, not a code implementation task.
- No UAT upload was run because the 24 PDF batch had already been submitted by Director and the report scope was evidence capture only.
- No Docker rebuild/restart was run during report creation.
- No MinerU restart was run during report creation.
- No DB/MinIO/Docker volume/task/material/artifact/log/sample cleanup was run.

## Risks And Follow-Up Recommendations

The strongest technical signal is TD-level runtime resilience debt around MinerU half-failed states:

1. MinerU `/health` can remain healthy while `/tasks` returns HTTP 500.
2. A large first PDF can enter a stale/timeout/task-record-lost path.
3. Subsequent queued tasks can cascade fail at submit time instead of being paused behind a clear dependency-failed gate.
4. The first task's Material remained `processing` while the task was `failed / mineru-processing`, which may require Lucia to decide whether this is acceptable failure-state semantics or a repair target.
5. AI metadata was never reached, so this pressure-test failure should not be attributed to Ollama.

Recommended Lucia review focus:

- Decide whether to issue a P0 task for MinerU half-failed runtime handling and batch queue circuit-breaking.
- Decide whether large-PDF local timeout should pause the remaining queue instead of letting 23 pending tasks fail via `/tasks` 500.
- Decide whether Material status normalization is needed when a MinerU task is confirmed failed after timeout/404.
- Decide whether production operation needs a manual recovery runbook for this exact state.
- Keep production release-readiness unclaimed until this failure mode is addressed or explicitly accepted as out of scope.

## Review Required

Lucia review is required.

Director decision may be required after Lucia determines whether this is:

- a blocking release-readiness failure,
- a scoped large-PDF pressure-test failure to fix before another run,
- or an accepted operational limit with a manual recovery procedure.
