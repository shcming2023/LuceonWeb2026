# Lucode Report: P0 Bounded 24 PDF Pressure Restart Under Entry Circuit

## Basis

- Based on Lucia task brief: `TaskAndReport/2026-05-10T15-54-51+0800_P0-Bounded-24-PDF-Pressure-Restart-Under-Entry-Circuit_TASK.md`
- Director authorization: `TaskAndReport/2026-05-10T15-50-52+0800_P0-Next-Validation-Step-After-Entry-Circuit-Deployment_DECISION.md`
- Prior failure field report: `TaskAndReport/2026-05-10T07-45-14+0800_P0-24-PDF-Pressure-Test-Failure-Field-Report_REPORT.md`
- Execution role: Lucode
- Production path: `/Users/concm/prod_workspace/Luceon2026`
- Runtime URL: `http://localhost:8081`

## Result Classification

`PRESSURE_RESTART_INCONCLUSIVE`

The exact same 24-PDF pressure set was identified under production path `testpdf/`, and preflight passed. The run created 20 new validation tasks, then stopped at sample 21 because the local upload command failed before sending the HTTP request:

```text
curl: (26) Failed to open/read local data from file/application
```

The failed sample file exists on disk:

```text
/Users/concm/prod_workspace/Luceon2026/testpdf/财务回执(￥50,000.00).pdf.pdf 96870 bytes
```

This is not a production service HTTP 503, not `MINERU_ADMISSION_CIRCUIT_OPEN`, and not evidence that MinerU submit-path failed. Because the task authorizes one run only and forbids retrying failed uploads, Lucode stopped immediately and did not attempt samples 22-24.

This run is not a pressure PASS and does not establish production release readiness.

## Heads And Runtime Boundary

- Development `main` HEAD: `90ad64a203204702b03e9dc964e591e932047d1d`
- Development `origin/main`: `90ad64a203204702b03e9dc964e591e932047d1d`
- Production deployed HEAD: `cf0466a6ff483745b34376039985eabf291ced3a`
- Production local override preserved and dirty:

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

No secret, model, timeout, strict AI flag, MinIO binding, or override value was changed.

## Exact 24-PDF Set

All 24 files were present in `/Users/concm/prod_workspace/Luceon2026/testpdf` and matched the prior failure report titles.

| # | Source file | Size bytes | New task/material result |
| ---: | --- | ---: | --- |
| 1 | `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express).pdf` | 52964792 | `task-1778400448971` / `pressure-restart-20260510160726-01` |
| 2 | `Cambridge IGCSE(0607) International Mathematics  Coursebook Extended_2018(Haese Mathematics).pdf` | 45247007 | `task-1778400452107` / `pressure-restart-20260510160726-02` |
| 3 | `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Hodder Express).pdf` | 43536275 | `task-1778400454526` / `pressure-restart-20260510160726-03` |
| 4 | `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Cambridge  University Press).pdf` | 40235936 | `task-1778400456661` / `pressure-restart-20260510160726-04` |
| 5 | `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics _2018(Haese Mathematics).pdf` | 91501329 | `task-1778400460190` / `pressure-restart-20260510160726-05` |
| 6 | `Cambridge IGCSE(0580) Extended Mathematics Student Book_2018(Oxford University Press).pdf` | 96516982 | `task-1778400468632` / `pressure-restart-20260510160726-06` |
| 7 | `Cambridge IGCSE(0580) Extended Mathematics Practice Book__2023(Cambridge  University Press).pdf` | 103549160 | `task-1778400473241` / `pressure-restart-20260510160726-07` |
| 8 | `Cambridge IGCSE(0580)  Core and Extended Mathematics_2023(Hodder Education).pdf` | 55782830 | `task-1778400478684` / `pressure-restart-20260510160726-08` |
| 9 | `Cambridge IGCSE(0580)  Core and Extended Mathematics_2022(Cambridge  University Press).pdf` | 102034314 | `task-1778400481740` / `pressure-restart-20260510160726-09` |
| 10 | `Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Hodder Education).pdf` | 39891635 | `task-1778400487246` / `pressure-restart-20260510160726-10` |
| 11 | `Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf` | 39063547 | `task-1778400490743` / `pressure-restart-20260510160726-11` |
| 12 | `Cambridge IGCSE(0580)  Core  Mathematics_2023(Hodder Education).pdf` | 63585444 | `task-1778400493794` / `pressure-restart-20260510160726-12` |
| 13 | `PDF document-4F18-A8A3-62-0.pdf` | 711046 | `task-1778400498868` / `pressure-restart-20260510160726-13` |
| 14 | `G7_Workbook_ready_to_print.pdf` | 15157403 | `task-1778400501915` / `pressure-restart-20260510160726-14` |
| 15 | `走向成功_英语_二模卷16篇.pdf` | 3457503 | `task-1778400507058` / `pressure-restart-20260510160726-15` |
| 16 | `向树叶学习：人工光合作用.pdf` | 86884 | `task-1778400513155` / `pressure-restart-20260510160726-16` |
| 17 | `期末质量分析及建议（曹云童 ）.pdf` | 1041695 | `task-1778400516082` / `pressure-restart-20260510160726-17` |
| 18 | `蓝月、血月、橙月？月亮为啥还会变色？.pdf` | 76797 | `task-1778400518537` / `pressure-restart-20260510160726-18` |
| 19 | `附件三：考务流程培训-纸笔标准考试.pdf` | 5349060 | `task-1778400521108` / `pressure-restart-20260510160726-19` |
| 20 | `出国.pdf` | 33814 | `task-1778400526749` / `pressure-restart-20260510160726-20` |
| 21 | `财务回执(￥50,000.00).pdf.pdf` | 96870 | stopped before HTTP request; `curl` exit `26` |
| 22 | `2025.pdf` | 175841 | not attempted after stop |
| 23 | `2025_2026学年春季课程中数G8_提取.pdf` | 530205 | not attempted after stop |
| 24 | `06第六章 长期股权投资与合营安排.pdf` | 10147571 | not attempted after stop |

Run ID: `pressure-restart-20260510160726`.

## Preflight Evidence

Preflight passed before the run:

- dependency-health HTTP `200`, `blocking=false`;
- MinerU submit probe HTTP `202`, task id `8194700d-738c-4c64-810a-3ce4ff19410b`;
- admission circuit HTTP `200`, `open=false`, `state=closed`;
- active task diagnostics had no active task, no queued tasks, and `takeoverRequiredTasks=[]`;
- Ollama `/api/ps` HTTP `200`, `qwen3.5:9b` resident.

Preflight admission circuit counts:

```json
{
  "parsePending": 0,
  "parseRunning": 0,
  "aiPending": 0,
  "aiRunning": 0
}
```

## Intake Run Evidence

Command class used:

```bash
curl -sS --max-time 180 -w '\nHTTP_STATUS:%{http_code}\n' \
  -F file=@<source-pdf> \
  -F materialId=<pressure-run-material-id> \
  -F backend=pipeline \
  -F parseMethod=ocr \
  http://localhost:8081/__proxy/upload/tasks
```

Samples 1-20 returned HTTP `200` and created tasks. After each accepted upload, stop-rule snapshots showed:

- dependency-health `blocking=false`;
- MinerU submit probe still HTTP `202`;
- admission circuit `open=false`;
- parse running count never exceeded `1`;
- AI running count never exceeded `0`;
- takeover-required count stayed `0`.

Sample 21 stopped the run:

```json
{
  "index": 21,
  "fileName": "财务回执(￥50,000.00).pdf.pdf",
  "exit": 26,
  "httpStatus": 0,
  "stderr": "curl: (26) Failed to open/read local data from file/application"
}
```

No upload request for sample 21 reached the server, and samples 22-24 were not attempted.

## State At Stop

At stop/report capture time, the 20 created tasks were still non-terminal:

```json
{
  "running/mineru-processing": 1,
  "pending/upload": 19
}
```

Per created sample:

| # | Task ID | State | Stage | AI job |
| ---: | --- | --- | --- | --- |
| 1 | `task-1778400448971` | `running` | `mineru-processing` | none |
| 2 | `task-1778400452107` | `pending` | `upload` | none |
| 3 | `task-1778400454526` | `pending` | `upload` | none |
| 4 | `task-1778400456661` | `pending` | `upload` | none |
| 5 | `task-1778400460190` | `pending` | `upload` | none |
| 6 | `task-1778400468632` | `pending` | `upload` | none |
| 7 | `task-1778400473241` | `pending` | `upload` | none |
| 8 | `task-1778400478684` | `pending` | `upload` | none |
| 9 | `task-1778400481740` | `pending` | `upload` | none |
| 10 | `task-1778400487246` | `pending` | `upload` | none |
| 11 | `task-1778400490743` | `pending` | `upload` | none |
| 12 | `task-1778400493794` | `pending` | `upload` | none |
| 13 | `task-1778400498868` | `pending` | `upload` | none |
| 14 | `task-1778400501915` | `pending` | `upload` | none |
| 15 | `task-1778400507058` | `pending` | `upload` | none |
| 16 | `task-1778400513155` | `pending` | `upload` | none |
| 17 | `task-1778400516082` | `pending` | `upload` | none |
| 18 | `task-1778400518537` | `pending` | `upload` | none |
| 19 | `task-1778400521108` | `pending` | `upload` | none |
| 20 | `task-1778400526749` | `pending` | `upload` | none |

## Stop-Time Dependency And Circuit Evidence

Dependency health after stop:

```json
{
  "ok": true,
  "blocking": false,
  "mineru": {
    "healthOk": true,
    "submitProbe": {
      "ok": true,
      "status": 202,
      "taskId": "20d2582f-fbac-437a-a348-72d3a033e2c4"
    },
    "admissionCircuit": {
      "state": "closed",
      "closeCriteria": {
        "submitProbeOk": true,
        "cooldownElapsed": true,
        "activeTaskClean": false,
        "dependencyBlockingClear": true
      },
      "counts": {
        "parsePending": 19,
        "parseRunning": 1,
        "aiPending": 0,
        "aiRunning": 0
      }
    }
  },
  "ollama": {
    "ok": true,
    "model": "qwen3.5:9b",
    "chatOk": true
  }
}
```

Admission circuit endpoint after stop:

```json
{
  "ok": true,
  "open": false,
  "circuit": {
    "state": "closed",
    "activeTaskClean": false,
    "counts": {
      "parsePending": 19,
      "parseRunning": 1,
      "aiPending": 0,
      "aiRunning": 0
    }
  }
}
```

Ollama `/api/ps` after stop:

```json
{
  "models": [
    {
      "name": "qwen3.5:9b",
      "model": "qwen3.5:9b",
      "parameter_size": "9.7B",
      "quantization_level": "Q4_K_M"
    }
  ]
}
```

## Commands Run

| Command | Path | Exit | Purpose |
| --- | --- | ---: | --- |
| `git status --short --branch` | development workspace | 0 | Confirm clean starting state |
| `git fetch origin` | development workspace | 0 | Sync remote refs |
| `git pull --ff-only origin main` | development workspace | 0 | Sync main |
| `sed -n ... TASK.md` | development workspace | 0 | Read Lucia task brief |
| `sed -n ... prior failure report` | development workspace | 0 | Read prior 24-PDF failure evidence |
| `find ... testpdf ...` | production path | 0 | Identify exact same 24 source PDFs |
| `GET dependency-health?mineruSubmitProbe=true` | production runtime | 0 / HTTP 200 | Preflight and stop-time submit-probe evidence |
| `GET /ops/mineru/admission-circuit` | production runtime | 0 / HTTP 200 | Circuit state evidence |
| `GET /ops/mineru/active-task` | production runtime | 0 / HTTP 200 | Heavy-stage and queue evidence |
| `GET /api/ps` | Ollama host runtime | 0 / HTTP 200 | Model residency evidence |
| Upload loop using `curl -F file=@...` | production runtime | stopped at sample 21 | Created samples 1-20; sample 21 local file-read failed before HTTP request |
| `git diff --check` | development workspace | 0 | Report diff hygiene before report writing |

## Skipped / Forbidden Items

- No retry of sample 21 was attempted.
- No samples 22-24 were attempted after stop.
- No failed task was repaired, retried, closed, deleted, or cleaned.
- No DB row, MinIO object, Docker volume, log, sample, or artifact was deleted.
- No secret, model, timeout, config, or override mutation was performed.
- No broad stack restart, rollback, unrelated recovery, or cleanup was performed.
- No production release-readiness, L3, full-site acceptance, or manual pressure-test readiness claim is made.

## Risks And Residuals

- The run left 20 newly created validation tasks in production: 1 `running/mineru-processing` and 19 `pending/upload` at the time of report capture. Lucode did not mutate or repair them because the task forbids cleanup/retry/repair.
- The stop was caused by the test harness command's handling of the sample 21 local filename, not by an observed server-side admission response.
- Because 24/24 were not submitted and created tasks had not reached terminal states, this run cannot be interpreted as pressure PASS or circuit PASS.
- A future retry, if desired, needs a new Lucia/Director task and should use a safer upload harness for filenames containing comma, parentheses, currency symbol, and duplicated `.pdf` suffix.

## Review Requirement

Lucia review is required.

Director decision is required before any retry, continuation, cleanup, failed-task repair, pressure-test restart, or release-readiness promotion.

