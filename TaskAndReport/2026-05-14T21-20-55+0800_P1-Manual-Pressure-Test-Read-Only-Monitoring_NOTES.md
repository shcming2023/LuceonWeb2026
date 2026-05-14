# Monitoring Notes: P1 Manual Pressure Test Read-Only Monitoring

Task: `TASK-20260514-212055-P1-Manual-Pressure-Test-Read-Only-Monitoring`

Expected final report: `TaskAndReport/2026-05-14T21-20-55+0800_P1-Manual-Pressure-Test-Read-Only-Monitoring_REPORT.md`

## Monitoring Contract

- Heartbeat automation id: `luceon2026-testacceptanceengineer-check-task`
- Heartbeat cadence: every 30 minutes
- Updated in same thread: yes
- Scope: read-only monitoring of user-submitted manual pressure test
- Forbidden: upload, cleanup, repair, reparse, re-AI, DB/MinIO/Docker volume/data mutation, service restart/rebuild, model/config/secret/sample mutation, GitHub sync, readiness/L3/go-live claim

## Pass 0 - Baseline / Waiting For User Submission

- Timestamp: `2026-05-14T21:28+0800` (`2026-05-14T13:28Z` evidence window)
- User manual submission observed: no
- Pressure-test task set identified: not yet
- Baseline captured before user submission: likely yes, because no new pending/running/upload pressure-test tasks were visible

### Development Workspace

- `git status --short --branch`: exit `0`
- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- Status: dirty shared role workspace with existing modified/untracked files; no GitHub sync run

### Production Baseline

- Production path: `/Users/concm/prod_workspace/Luceon2026`
- `git status --short --branch`: exit `0`; branch `main...origin/main`
- Production local modifications present: `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, `src/app/pages/SourceMaterialsPage.tsx`
- `git log -1 --oneline`: exit `0`; `89271a1 Dispatch db-sync hardening production deployment`
- `docker compose ps`: exit `0`; `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` all healthy
- Frontend `/cms/`: exit `0`; HTTP `200`
- Upload health: exit `0`; `{"ok":true,"service":"upload-server"}`
- Dependency health without explicit probe params: exit `0`; `ok=true`, `blocking=false`; MinerU OK; Ollama OK, `chatOk=true`, model `qwen3.5:9b`, resident
- Admission circuit: exit `0`; `open=false`, state `closed`, counts `parsePending=0`, `parseRunning=0`, `aiPending=0`, `aiRunning=0`
- Active-task: exit `0`; no active/current/queued/takeover-required work; 3 historical AI failure tasks
- Direct MinerU `/health`: exit `0`; `queued_tasks=0`, `processing_tasks=0`, `failed_tasks=0`

### Baseline Task / Material Counts

- Task count: `50`
- Material count: `50`
- AI job count: `50`
- Aggregate task states:
  - `review-pending/review`: `47`
  - `failed/ai`: `3`
- Newest task before pressure run: `task-1778763994124`, file `PDF document-4F18-A8A3-62-0.pdf`, state `review-pending`, created `2026-05-14T13:06:34.255Z`

### UI / Browser Spot Check

- Route: `http://localhost:8081/cms/tasks`
- Title: `教育内容管理平台 UI`
- UI counts visible: total `50`, waiting `0`, processing `0`, review-pending `47`, completed `0`, failed `3`, canceled `0`
- Browser console: one hydration log only
- `[db-sync]`: `0`
- `/settings`: `0`
- `/secrets`: `0`
- `Failed to fetch`: `0`
- HTTP `5xx`: `0`
- Non-stream request failures: `0`
- Stream request failures: `0`
- UI remained responsive and operator-readable

### Host / Runtime Resource Snapshot

- `uptime`: up `3 days, 20:22`; load averages `5.32 6.23 6.16`
- Disk:
  - `/`: `1.9Ti`, used `12Gi`, available `1.3Ti`, capacity `1%`
  - `/System/Volumes/Data`: `1.9Ti`, used `537Gi`, available `1.3Ti`, capacity `29%`
- VM snapshot: free pages `3896`, pages in compressor `3002069`, pageouts `1562093`, swapouts `4346486`
- Key processes observed:
  - Ollama serve and qwen runner present
  - Docker Desktop backend present
  - `luceon-sidecar` / `ops/mineru-log-observer.mjs` present
  - MinerU API process present: `/Users/concm/miniconda3/envs/mineru/bin/mineru-api --host 0.0.0.0 --port 8083`
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.18%`, memory `7.684MiB / 11.67GiB`
  - `cms-upload-server`: CPU `1.58%`, memory `44.7MiB / 4GiB`
  - `cms-db-server`: CPU `4.87%`, memory `30.79MiB / 512MiB`
  - `cms-minio`: CPU `0.10%`, memory `145.2MiB / 1GiB`

### Assessment

- Status: `WAITING_FOR_USER_MANUAL_SUBMISSION`
- No pressure-test tasks detected yet.
- Runtime baseline is reachable, healthy, idle, and non-blocking.
- Next monitoring pass should identify new tasks created after `task-1778763994124` or after the user reports manual submission.

## Pass 1 - User Submission Detected

- Timestamp: `2026-05-14T21:30+0800` (`2026-05-14T13:30Z` evidence window)
- User manual submission observed: yes; user reported `已经提交了`
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`
- Total AI job count: `50`

### Aggregate State

- `running/mineru-processing`: `1`
- `pending/upload`: `23`
- AI jobs for this pressure run: `0` at this pass
- Current active task: `task-1778765376492`
- Current active material: `571622079952718`
- Active file: `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express).pdf`
- Active file size: `52964792`
- Active MinerU task id: `6c89e0cf-02db-4db1-bbf7-a1f8601e1f8e`
- Active state/stage/progress: `running` / `mineru-processing` / `50`
- Active message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`

### Detected Pressure-Test Tasks

| Task | File | Size | State | Stage | Progress |
| --- | --- | ---: | --- | --- | ---: |
| `task-1778765376492` | `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express).pdf` | `52964792` | `running` | `mineru-processing` | `50` |
| `task-1778765377823` | `Cambridge IGCSE(0607) International Mathematics  Coursebook Extended_2018(Haese Mathematics).pdf` | `45247007` | `pending` | `upload` | `0` |
| `task-1778765378939` | `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Hodder Express).pdf` | `43536275` | `pending` | `upload` | `0` |
| `task-1778765380166` | `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Cambridge  University Press).pdf` | `40235936` | `pending` | `upload` | `0` |
| `task-1778765382204` | `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics _2018(Haese Mathematics).pdf` | `91501329` | `pending` | `upload` | `0` |
| `task-1778765385568` | `Cambridge IGCSE(0580) Extended Mathematics Student Book_2018(Oxford University Press).pdf` | `96516982` | `pending` | `upload` | `0` |
| `task-1778765390120` | `Cambridge IGCSE(0580) Extended Mathematics Practice Book__2023(Cambridge  University Press).pdf` | `103549160` | `pending` | `upload` | `0` |
| `task-1778765393188` | `Cambridge IGCSE(0580)  Core and Extended Mathematics_2023(Hodder Education).pdf` | `55782830` | `pending` | `upload` | `0` |
| `task-1778765397977` | `Cambridge IGCSE(0580)  Core and Extended Mathematics_2022(Cambridge  University Press).pdf` | `102034314` | `pending` | `upload` | `0` |
| `task-1778765401421` | `Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Hodder Education).pdf` | `39891635` | `pending` | `upload` | `0` |
| `task-1778765403100` | `Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf` | `39063547` | `pending` | `upload` | `0` |
| `task-1778765405253` | `Cambridge IGCSE(0580)  Core  Mathematics_2023(Hodder Education).pdf` | `63585444` | `pending` | `upload` | `0` |
| `task-1778765407138` | `PDF document-4F18-A8A3-62-0.pdf` | `711046` | `pending` | `upload` | `0` |
| `task-1778765408050` | `G7_Workbook_ready_to_print.pdf` | `15157403` | `pending` | `upload` | `0` |
| `task-1778765409131` | `走向成功_英语_二模卷16篇.pdf` | `3457503` | `pending` | `upload` | `0` |
| `task-1778765409984` | `向树叶学习：人工光合作用.pdf` | `86884` | `pending` | `upload` | `0` |
| `task-1778765410767` | `期末质量分析及建议（曹云童 ）.pdf` | `1041695` | `pending` | `upload` | `0` |
| `task-1778765411612` | `蓝月、血月、橙月？月亮为啥还会变色？.pdf` | `76797` | `pending` | `upload` | `0` |
| `task-1778765412523` | `附件三：考务流程培训-纸笔标准考试.pdf` | `5349060` | `pending` | `upload` | `0` |
| `task-1778765414107` | `出国.pdf` | `33814` | `pending` | `upload` | `0` |
| `task-1778765414954` | `财务回执(￥50,000.00).pdf.pdf` | `96870` | `pending` | `upload` | `0` |
| `task-1778765415701` | `2025.pdf` | `175841` | `pending` | `upload` | `0` |
| `task-1778765416562` | `2025_2026学年春季课程中数G8_提取.pdf` | `530205` | `pending` | `upload` | `0` |
| `task-1778765417422` | `06第六章 长期股权投资与合营安排.pdf` | `10147571` | `pending` | `upload` | `0` |

### Runtime / Endpoint Snapshot

- Upload health: OK
- Active-task: one active/current processing task, `task-1778765376492`
- Admission circuit: `open=false`, state `closed`
- Admission counts: `parsePending=23`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`
- Dependency health without extra probe params: `ok=true`, `blocking=false`; MinerU OK; Ollama OK, model resident
- Direct MinerU `/health`: `queued_tasks=20`, `processing_tasks=1`, `failed_tasks=0`
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy

### Resource Snapshot

- `uptime`: up `3 days, 20:24`; load averages `10.15 7.48 6.65`
- Disk at production path: `1.9Ti`, used `538Gi`, available `1.3Ti`, capacity `29%`
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.23%`, memory `7.762MiB / 11.67GiB`
  - `cms-upload-server`: CPU `9.35%`, memory `69.22MiB / 4GiB`
  - `cms-db-server`: CPU `12.86%`, memory `27.99MiB / 512MiB`
  - `cms-minio`: CPU `0.00%`, memory `173.3MiB / 1GiB`

### Assessment

- Status: `RUNNING`
- Pressure-test task set has started and contains `24` tasks.
- The system is progressing: one MinerU task is active and direct MinerU reports one processing task plus queue.
- No failure/stall/down outcome is established at this pass.
- Next heartbeat should compare task states, active MinerU task, AI job creation, and progress timestamps against this pass.

## Pass 2 - Read-Only Monitoring

- Timestamp: `2026-05-14T21:58+0800` (`2026-05-14T13:57Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `28m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`
- Total AI job count: `50`

### Aggregate State

- `running/mineru-processing`: `1`
- `pending/upload`: `23`
- AI jobs for this pressure run: `0` at this pass
- Current active task: `task-1778765376492`
- Current active material: `571622079952718`
- Active file: `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express).pdf`
- Active file size: `52964792`
- Active MinerU task id: `6c89e0cf-02db-4db1-bbf7-a1f8601e1f8e`
- Active state/stage/progress: `running` / `mineru-processing` / `50`
- Active message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
- Active `updatedAt`: `2026-05-14T13:57:52.640Z`
- Active `mineruLastStatusAt`: `2026-05-14T13:57:52.639Z`

### Runtime / Endpoint Snapshot

- Upload health: OK
- Active-task: one active/current processing task, `task-1778765376492`
- Active-task observation notes:
  - `mineruObservedProgress.activityLevel`: `log-observation-unattributed`
  - `observationStale`: `true`
  - Stale reason: `log file mtime is older than task start time, likely from previous task`
  - Log source: `/host/mineru-logs/mineru-api.log`
  - Log mtime: `2026-05-14T13:06:38.191Z`
- Admission circuit: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`
- Admission counts: `parsePending=23`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`
- Dependency health request without explicit extra probe params timed out after `10s` with no response in this pass.
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=69`, `failed_tasks=0`
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy

### Resource Snapshot

- `uptime`: up `3 days, 20:52`; load averages `5.06 6.04 6.67`
- Disk at production path: `1.9Ti`, used `538Gi`, available `1.3Ti`, capacity `29%`
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.08%`, memory `7.695MiB / 11.67GiB`
  - `cms-upload-server`: CPU `2.29%`, memory `79.29MiB / 4GiB`
  - `cms-db-server`: CPU `5.63%`, memory `27.84MiB / 512MiB`
  - `cms-minio`: CPU `0.05%`, memory `173.5MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_SAME_ACTIVE_MINERU_TASK`
- Pressure-test task set remains active: one task is still in MinerU processing and `23` remain pending behind it.
- The active task is still the same task observed in Pass 1 and still reports progress `50`.
- A final stall/hung conclusion is not yet established in this pass because this is the first 30-minute comparison after submission and the task has fresh `updatedAt` / `mineruLastStatusAt` values, even though semantic progress and task id did not change.
- Watch item for next pass: if the same task remains nonterminal with unchanged state/stage/progress/message and no attributable MinerU/AI progress, evaluate against the task brief's two-consecutive-pass `HUNG_OR_STALLED` criterion.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 3 - Read-Only Monitoring

- Timestamp: `2026-05-14T22:28+0800` (`2026-05-14T14:27-14:28Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `59m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`
- Total AI job count: `50`

### Aggregate State

- `review-pending/review`: `1`
- `running/mineru-processing`: `1`
- `pending/upload`: `22`
- Pressure-run material aggregate:
  - `material:reviewing mineru:completed ai:analyzed`: `1`
  - `material:processing mineru:pending ai:pending`: `23`
- AI jobs for this pressure run: `1` observed on completed first task.

### Per-Task Progress Delta

- First pressure-test task completed MinerU + AI and reached review:
  - Task: `task-1778765376492`
  - Material: `571622079952718`
  - File: `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express).pdf`
  - File size: `52964792`
  - Final observed state/stage/progress: `review-pending` / `review` / `100`
  - Message: `AI 识别完成: review-pending (待人工复核)`
  - MinerU task id: `6c89e0cf-02db-4db1-bbf7-a1f8601e1f8e`
  - AI job id: `ai-job-1778767110100-26ff`
  - `updatedAt`: `2026-05-14T14:00:39.475Z`
  - `completedAt`: `2026-05-14T14:00:39.474Z`
- Current active task moved to the second pressure-test task:
  - Task: `task-1778765377823`
  - Material: `3480255763751915`
  - File: `Cambridge IGCSE(0607) International Mathematics  Coursebook Extended_2018(Haese Mathematics).pdf`
  - File size: `45247007`
  - Active MinerU task id: `8fe16937-f181-4085-84da-178ff07b9665`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - `updatedAt`: `2026-05-14T14:28:49.472Z`
  - `mineruLastStatusAt`: `2026-05-14T14:28:49.460Z`
- Remaining pressure-test tasks: `22` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint returned one active/current processing task, `task-1778765377823`.
- Active-task live observation at `2026-05-14T14:27Z`:
  - `activityLevel`: `active-progress`
  - Phase: `OCR-rec Predict`
  - Progress signal: `1476/2868`, `51%`
  - `lastProgressObservedAt`: `2026-05-14T14:26:39.000Z`
  - Log source: `/Users/concm/ops/logs/mineru-api.err.log`
  - Log source selected reason: `latest-valid-business-signal`
  - `observationStale`: `false`
  - Attribution: `task-1778765377823`, `live-active`
- Later DB task summary at `2026-05-14T14:28:49Z` still showed the active task as running with fresh `updatedAt`, but its compact observed payload had a diagnostic stale-log warning. This was recorded as an observability inconsistency/watch item, not as a terminal failure.
- Admission circuit: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=22`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health request without explicit extra probe params timed out after `10s` with no response in this pass.
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=69`, `failed_tasks=0`.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check: `200` in `0.007430s`.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `3 days, 21:22`; load averages `5.07 4.65 4.88`.
- Disk at production path: `1.9Ti`, used `538Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.00%`, memory `7.699MiB / 11.67GiB`
  - `cms-upload-server`: CPU `5.66%`, memory `73.4MiB / 4GiB`
  - `cms-db-server`: CPU `2.47%`, memory `34.34MiB / 512MiB`
  - `cms-minio`: CPU `0.00%`, memory `187.4MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_PROGRESS`
- The pressure-test run made real progress since Pass 2: first large PDF reached `review-pending/review`, and the second large PDF is now the active MinerU task.
- Stall/hang criteria are not met in this pass because task state changed, AI job evidence appeared, active task changed, and active-task endpoint showed a live MinerU OCR progress signal.
- No explicit pressure-run task failure was observed.
- Runtime endpoints and core Docker services remained reachable/healthy enough for monitoring.
- Watch item for next pass: continue comparing `task-1778765377823` active progress, particularly the difference between active-task live progress evidence and the later compact stale-log warning in task metadata.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 4 - Read-Only Monitoring

- Timestamp: `2026-05-14T22:58+0800` (`2026-05-14T14:58Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `89m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`

### Aggregate State

- `review-pending/review`: `1`
- `running/mineru-processing`: `1`
- `pending/upload`: `22`
- Pressure-run material aggregate:
  - `material:reviewing mineru:completed ai:analyzed`: `1`
  - `material:processing mineru:pending ai:pending`: `23`
- AI jobs for this pressure run: `1` observed on completed first task.

### Per-Task Progress Delta

- First pressure-test task remains terminal review:
  - Task: `task-1778765376492`
  - File: `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express).pdf`
  - State/stage/progress: `review-pending` / `review` / `100`
  - AI job id: `ai-job-1778767110100-26ff`
  - `completedAt`: `2026-05-14T14:00:39.474Z`
- Current active task remains the second pressure-test task but shows fresh live progress:
  - Task: `task-1778765377823`
  - Material: `3480255763751915`
  - File: `Cambridge IGCSE(0607) International Mathematics  Coursebook Extended_2018(Haese Mathematics).pdf`
  - File size: `45247007`
  - Active MinerU task id: `8fe16937-f181-4085-84da-178ff07b9665`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Task-level message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - `updatedAt`: `2026-05-14T14:58:20.734Z`
  - `mineruLastStatusAt`: `2026-05-14T14:58:20.158Z`
  - MinerU observed phase: `MFR Predict`
  - MinerU observed progress: `1824/1852`, `98%`
  - `lastProgressObservedAt`: `2026-05-14T14:54:34.000Z`
  - Log source: `/Users/concm/ops/logs/mineru-api.err.log`
  - `observationStale`: `false`
  - Attribution: `task-1778765377823`, `live-active`
- Remaining pressure-test tasks: `22` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint returned one active/current processing task, `task-1778765377823`.
- Admission circuit: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=22`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health without explicit extra probe params returned `ok=false`, `blocking=false` due to Ollama tags timeout:
  - MinIO OK.
  - MinerU OK, health OK, submit probe disabled for this request.
  - Ollama reported `serviceReachable=false`, `tagsOk=false`, `modelPresent=false`, `modelResident=false`, `failureKind=tags-error`, error `The operation was aborted due to timeout`.
- Follow-up lightweight Ollama read-only checks, without chat inference load:
  - `/api/version`: `{"version":"0.23.2"}`
  - `/api/ps`: `qwen3.5:9b` present/resident, `size_vram=9738673088`, `context_length=32768`, expiry `2026-05-15T22:28:15.905223+08:00`
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=69`, `failed_tasks=0`.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check: `200` in `0.002391s`.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `3 days, 21:52`; load averages `4.33 4.45 4.75`.
- Disk at production path: `1.9Ti`, used `538Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.06%`, memory `7.699MiB / 11.67GiB`
  - `cms-upload-server`: CPU `1.25%`, memory `82.36MiB / 4GiB`
  - `cms-db-server`: CPU `5.47%`, memory `33.6MiB / 512MiB`
  - `cms-minio`: CPU `0.03%`, memory `187.6MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_PROGRESS`
- The pressure-test run has not reached a final success/fail/stall/down outcome.
- Stall/hang criteria are not met in this pass because the active second task still has fresh MinerU progress evidence, including phase movement to `MFR Predict` and observed progress `98%`.
- No explicit pressure-run task failure was observed.
- Runtime core services remained reachable/healthy enough for monitoring.
- Watch item for next pass: dependency-health timed out on the Ollama tags check while direct Ollama version/ps remained reachable and `qwen3.5:9b` resident. This is not a parse-blocking failure in this pass, but it may affect AI stage if it recurs when the second task reaches AI.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 5 - Read-Only Monitoring

- Timestamp: `2026-05-14T23:28+0800` (`2026-05-14T15:28Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `119m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`

### Aggregate State

- `review-pending/review`: `2`
- `running/mineru-processing`: `1`
- `pending/upload`: `21`
- Pressure-run material aggregate:
  - `material:reviewing mineru:completed ai:analyzed`: `2`
  - `material:processing mineru:pending ai:pending`: `22`
- AI jobs for this pressure run: `2` observed on completed first and second tasks.

### Per-Task Progress Delta

- First pressure-test task remains terminal review:
  - Task: `task-1778765376492`
  - File: `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express).pdf`
  - State/stage/progress: `review-pending` / `review` / `100`
  - AI job id: `ai-job-1778767110100-26ff`
  - `completedAt`: `2026-05-14T14:00:39.474Z`
- Second pressure-test task completed MinerU + AI and reached review:
  - Task: `task-1778765377823`
  - Material: `3480255763751915`
  - File: `Cambridge IGCSE(0607) International Mathematics  Coursebook Extended_2018(Haese Mathematics).pdf`
  - File size: `45247007`
  - State/stage/progress: `review-pending` / `review` / `100`
  - Message: `AI 识别完成: review-pending (待人工复核)`
  - MinerU task id: `8fe16937-f181-4085-84da-178ff07b9665`
  - AI job id: `ai-job-1778771343370-1190`
  - `updatedAt`: `2026-05-14T15:11:30.445Z`
  - `completedAt`: `2026-05-14T15:11:30.445Z`
  - MinerU completion/backfill observation: `Processing pages`, `736/736`, `100%`, `lastProgressObservedAt=2026-05-14T15:09:03.464Z`
- Current active task moved to the third pressure-test task:
  - Task: `task-1778765378939`
  - Material: `1452447880586254`
  - File: `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Hodder Express).pdf`
  - File size: `43536275`
  - Active MinerU task id: `ed12a6a4-0ded-450e-b7e0-ab5c1111d9b9`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Task-level message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - `updatedAt`: `2026-05-14T15:28:42.147Z`
  - `mineruLastStatusAt`: `2026-05-14T15:28:33.997Z`
- Remaining pressure-test tasks: `21` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint returned one active/current processing task, `task-1778765378939`.
- Active-task live observation:
  - `activityLevel`: `active-progress`
  - Phase: `OCR-det ch`
  - Progress signal: `46/52`, `88%`
  - `lastProgressObservedAt`: `2026-05-14T15:23:48.000Z`
  - Log source: `/Users/concm/ops/logs/mineru-api.err.log`
  - Log source selected reason: `latest-valid-business-signal`
  - `observationStale`: `false`
  - Attribution: `task-1778765378939`, `live-active`
- Admission circuit: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=21`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health request without explicit extra probe params timed out after `10s` with no response in this pass.
- Follow-up lightweight Ollama read-only checks, without chat inference load:
  - `/api/version`: `{"version":"0.23.2"}`
  - `/api/ps`: `qwen3.5:9b` present/resident, `size_vram=9738673088`, `context_length=32768`, expiry `2026-05-15T23:28:57.821381+08:00`
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=70`, `failed_tasks=0`.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check: `200` in `0.006010s`.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `3 days, 22:23`; load averages `3.97 4.72 4.72`.
- Disk at production path: `1.9Ti`, used `539Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.02%`, memory `7.758MiB / 11.67GiB`
  - `cms-upload-server`: CPU `0.77%`, memory `106.2MiB / 4GiB`
  - `cms-db-server`: CPU `0.00%`, memory `43.39MiB / 512MiB`
  - `cms-minio`: CPU `0.00%`, memory `189MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_PROGRESS`
- The pressure-test run made real progress since Pass 4: the second large PDF reached `review-pending/review`, AI job evidence appeared, and the third large PDF became the active MinerU task.
- Stall/hang criteria are not met because task state changed, the active task changed, and the current active task has fresh MinerU progress evidence.
- No explicit pressure-run task failure was observed.
- Runtime core services remained reachable/healthy enough for monitoring.
- Watch item for next pass: dependency-health without extra probe params timed out again, while direct Ollama version/ps remained reachable and `qwen3.5:9b` resident. Continue watching AI-stage behavior for subsequent completed MinerU tasks.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 6 - Read-Only Monitoring

- Timestamp: `2026-05-14T23:58+0800` (`2026-05-14T15:58Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `149m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`

### Aggregate State

- `review-pending/review`: `3`
- `running/mineru-processing`: `1`
- `pending/upload`: `20`
- AI jobs for this pressure run: at least `3` observed on completed first, second, and third tasks.

### Per-Task Progress Delta

- First pressure-test task remains terminal review:
  - Task: `task-1778765376492`
  - File: `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express).pdf`
  - State/stage/progress: `review-pending` / `review` / `100`
  - AI job id: `ai-job-1778767110100-26ff`
  - `completedAt`: `2026-05-14T14:00:39.474Z`
- Second pressure-test task remains terminal review:
  - Task: `task-1778765377823`
  - File: `Cambridge IGCSE(0607) International Mathematics  Coursebook Extended_2018(Haese Mathematics).pdf`
  - State/stage/progress: `review-pending` / `review` / `100`
  - AI job id: `ai-job-1778771343370-1190`
  - `completedAt`: `2026-05-14T15:11:30.445Z`
- Third pressure-test task completed MinerU + AI and reached review:
  - Task: `task-1778765378939`
  - Material: `1452447880586254`
  - File: `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Hodder Express).pdf`
  - File size: `43536275`
  - State/stage/progress: `review-pending` / `review` / `100`
  - Message: `AI 识别完成: review-pending (待人工复核)`
  - MinerU task id: `ed12a6a4-0ded-450e-b7e0-ab5c1111d9b9`
  - AI job id: observed in task metadata during this pass
- Current active task moved to the fourth pressure-test task:
  - Task: `task-1778765380166`
  - Material: `2564754058850154`
  - File: `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Cambridge  University Press).pdf`
  - File size: `40235936`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Task-level message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - Active MinerU evidence observed from active-task endpoint in this pass.
- Remaining pressure-test tasks: `20` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint returned one active/current processing task, the fourth pressure-test task `task-1778765380166`.
- Admission circuit: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=20`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health request without explicit extra probe params timed out after `10s` with no response in this pass.
- Follow-up lightweight Ollama read-only checks, without chat inference load:
  - `/api/version`: `{"version":"0.23.2"}`
  - `/api/ps`: `qwen3.5:9b` present/resident, `size_vram=9738673088`, `context_length=32768`, expiry `2026-05-15T23:39:06.837388+08:00`
- Direct MinerU `/health`: healthy, `processing_tasks=1`, no failed MinerU tasks observed.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check remained reachable.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `3 days, 22:23`; load averages `3.97 4.72 4.72`.
- Disk at production path: `1.9Ti`, used `539Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.02%`, memory `7.758MiB / 11.67GiB`
  - `cms-upload-server`: CPU `0.77%`, memory `106.2MiB / 4GiB`
  - `cms-db-server`: CPU `0.00%`, memory `43.39MiB / 512MiB`
  - `cms-minio`: CPU `0.00%`, memory `189MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_PROGRESS`
- The pressure-test run made real progress since Pass 5: the third large PDF reached `review-pending/review`, and the fourth large PDF became the active MinerU task.
- Stall/hang criteria are not met because task state changed, the active task changed, and terminal review evidence increased from `2` to `3` tasks.
- No explicit pressure-run task failure was observed.
- Runtime core services remained reachable/healthy enough for monitoring.
- Watch item for next pass: dependency-health without extra probe params continued to time out, while direct Ollama version/ps remained reachable and `qwen3.5:9b` resident. Continue watching whether AI-stage completion remains successful for subsequent MinerU completions.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 7 - Read-Only Monitoring

- Timestamp: `2026-05-15T00:28+0800` (`2026-05-14T16:28Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `179m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`

### Aggregate State

- `review-pending/review`: `4`
- `running/mineru-processing`: `1`
- `pending/upload`: `19`
- Pressure-run material aggregate:
  - `material:reviewing mineru:completed ai:analyzed`: `4`
  - `material:processing mineru:pending ai:pending`: `20`
- AI jobs for this pressure run: at least `4` observed on completed first through fourth tasks.

### Per-Task Progress Delta

- First through third pressure-test tasks remain terminal review:
  - `task-1778765376492`: `review-pending/review/100`, AI job `ai-job-1778767110100-26ff`
  - `task-1778765377823`: `review-pending/review/100`, AI job `ai-job-1778771343370-1190`
  - `task-1778765378939`: `review-pending/review/100`, AI job `ai-job-1778773022772-b3e4`
- Fourth pressure-test task completed MinerU + AI and reached review:
  - Task: `task-1778765380166`
  - Material: `2564754058850154`
  - File: `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics Coursebook_2023(Cambridge  University Press).pdf`
  - File size: `40235936`
  - State/stage/progress: `review-pending` / `review` / `100`
  - Message: `AI 识别完成: review-pending (待人工复核)`
  - MinerU task id: `21b66e85-58f4-4ced-bed4-f1f579bc8019`
  - AI job id: `ai-job-1778775067966-dc2c`
  - `updatedAt`: `2026-05-14T16:13:34.144Z`
  - `completedAt`: `2026-05-14T16:13:34.142Z`
  - MinerU completion/backfill observation: `Processing pages`, `496/496`, `100%`, `lastProgressObservedAt=2026-05-14T16:11:16.800Z`
- Current active task moved to the fifth pressure-test task:
  - Task: `task-1778765382204`
  - Material: `4413655764085495`
  - File: `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics _2018(Haese Mathematics).pdf`
  - File size: `91501329`
  - Active MinerU task id: `110919d1-13eb-4c16-9594-09a3c77da8df`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Task-level message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - `updatedAt`: `2026-05-14T16:28:24.627Z`
  - `mineruLastStatusAt`: `2026-05-14T16:28:24.625Z`
- Remaining pressure-test tasks: `19` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint returned one active/current processing task, `task-1778765382204`.
- Active-task observation for `task-1778765382204`:
  - `mineruSubmittedAt`: `2026-05-14T16:11:16.993Z`
  - `mineruStartedAt`: `2026-05-14T16:11:17.014624+00:00`
  - `activityLevel`: `log-observation-unattributed`
  - `observationStale`: `true`
  - Stale reason: `log file mtime is older than task start time, likely from previous task`
  - Log source selected reason: `latest-mtime-fallback`
  - Log source path: `/host/mineru-logs/mineru-api.log`
  - Log source mtime: `2026-05-14T16:06:40.789Z`
  - API noise count: `174`
  - No error signal observed in the active-task payload.
- Admission circuit: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=19`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health request without explicit extra probe params timed out after `10s` with no response in this pass.
- Follow-up lightweight Ollama read-only checks, without chat inference load:
  - `/api/version`: `{"version":"0.23.2"}`
  - `/api/ps`: `qwen3.5:9b` present/resident, `size_vram=9738673088`, `context_length=32768`, expiry `2026-05-15T23:39:06.837388+08:00`
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=72`, `failed_tasks=0`.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check: `200` in `0.006992s`.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `3 days, 23:22`; load averages `3.76 4.47 4.56`.
- Disk at production path: `1.9Ti`, used `539Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.06%`, memory `7.699MiB / 11.67GiB`
  - `cms-upload-server`: CPU `2.15%`, memory `107.9MiB / 4GiB`
  - `cms-db-server`: CPU `4.82%`, memory `33.76MiB / 512MiB`
  - `cms-minio`: CPU `0.03%`, memory `187MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_PROGRESS`
- The pressure-test run made real progress since Pass 6: the fourth large PDF reached `review-pending/review`, and the fifth large PDF became the active MinerU task.
- Stall/hang criteria are not met because task state changed, the active task changed, and terminal review evidence increased from `3` to `4` tasks.
- No explicit pressure-run task failure was observed.
- Runtime core services remained reachable/healthy enough for monitoring.
- Watch item for next pass: the current fifth task has stale/unattributed MinerU log observation, although direct MinerU still reports one processing task and no failures. Compare the same task on the next pass before considering stall criteria.
- Dependency-health without extra probe params continued to time out, while direct Ollama version/ps remained reachable and `qwen3.5:9b` resident.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 11 - Read-Only Monitoring

- Timestamp: `2026-05-15T02:30+0800` (`2026-05-14T18:29Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `300m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`

### Aggregate State

- `review-pending/review`: `7`
- `running/mineru-processing`: `1`
- `pending/upload`: `16`
- Pressure-run material aggregate:
  - `material:reviewing mineru:completed ai:analyzed`: `7`
  - `material:processing mineru:pending ai:pending`: `17`
- AI jobs for this pressure run: at least `7` observed on completed first through seventh tasks.

### Per-Task Progress Delta

- First through seventh pressure-test tasks are terminal review.
- Sixth pressure-test task completed MinerU + AI and reached review:
  - Task: `task-1778765385568`
  - Material: `3995882041044285`
  - File: `Cambridge IGCSE(0580) Extended Mathematics Student Book_2018(Oxford University Press).pdf`
  - File size: `96516982`
  - State/stage/progress: `review-pending` / `review` / `100`
  - AI job id: `ai-job-1778781534940-6458`
  - `completedAt`: `2026-05-14T18:01:17.795Z`
- Seventh pressure-test task completed MinerU + AI and reached review:
  - Task: `task-1778765390120`
  - Material: `7949669109936191`
  - File: `Cambridge IGCSE(0580) Extended Mathematics Practice Book__2023(Cambridge  University Press).pdf`
  - File size: `103549160`
  - State/stage/progress: `review-pending` / `review` / `100`
  - AI job id: `ai-job-1778782444223-0913`
  - `completedAt`: `2026-05-14T18:16:15.075Z`
- Current active task moved to the eighth pressure-test task:
  - Task: `task-1778765393188`
  - Material: `2840047402983096`
  - File: `Cambridge IGCSE(0580)  Core and Extended Mathematics_2023(Hodder Education).pdf`
  - File size: `55782830`
  - Active MinerU task id: `145620af-4293-4ffa-b483-6ed29d4c9bf1`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Task-level message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - `updatedAt`: `2026-05-14T18:29:02.000Z`
  - `mineruLastStatusAt`: `2026-05-14T18:29:01.436Z`
  - Latest observed MinerU progress: phase `Layout Predict`, `44/64`, `69%`, `lastProgressObservedAt=2026-05-14T18:28:54.000Z`
  - `logUpdatedAt`: `2026-05-14T18:29:01.859Z`
  - Observation stale: `false`
- Remaining pressure-test tasks: `16` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint confirmed the eighth pressure-test task `task-1778765393188` as active/current processing with live MinerU progress.
- Active-task observation for `task-1778765393188`:
  - `activityLevel`: `active-progress`
  - Phase: `Layout Predict`
  - Progress signal: `44/64`, `69%`
  - `lastProgressObservedAt`: `2026-05-14T18:28:54.000Z`
  - `logUpdatedAt`: `2026-05-14T18:29:01.859Z`
  - `observationStale`: `false`
  - No terminal error signal observed in the active-task payload.
- Admission circuit: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=16`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health request without explicit extra probe params timed out after `10s` with no response in this pass.
- Follow-up lightweight Ollama read-only checks, without chat inference load:
  - `/api/version`: `{"version":"0.23.2"}`
  - `/api/ps`: `qwen3.5:9b` present/resident, `size_vram=9738673088`, `context_length=32768`, expiry `2026-05-16T02:16:14.843579+08:00`
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=75`, `failed_tasks=0`.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check: `200` in `0.004452s`.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `4 days, 1:23`; load averages `5.25 4.43 4.51`.
- Disk at production path: `1.9Ti`, used `541Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.09%`, memory `7.703MiB / 11.67GiB`
  - `cms-upload-server`: CPU `2.14%`, memory `88.88MiB / 4GiB`
  - `cms-db-server`: CPU `3.67%`, memory `34.89MiB / 512MiB`
  - `cms-minio`: CPU `0.00%`, memory `182.3MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_PROGRESS`
- The pressure-test run made real progress since Pass 10: the sixth and seventh large PDFs reached `review-pending/review`, and the eighth large PDF became the active MinerU task with fresh live progress.
- Stall/hang criteria are not met because task state changed, the active task changed, terminal review evidence increased from `5` to `7` tasks, and current MinerU evidence is live and non-stale.
- No explicit pressure-run task failure was observed.
- Runtime core services remained reachable/healthy enough for monitoring.
- Dependency-health without extra probe params continued to time out, while direct Ollama version/ps remained reachable and `qwen3.5:9b` resident.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 10 - Read-Only Monitoring

- Timestamp: `2026-05-15T01:59+0800` (`2026-05-14T17:58-17:59Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `270m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`

### Aggregate State

- `review-pending/review`: `5`
- `running/mineru-processing`: `1`
- `pending/upload`: `18`
- Pressure-run material aggregate:
  - `material:reviewing mineru:completed ai:analyzed`: `5`
  - `material:processing mineru:pending ai:pending`: `19`
- AI jobs for this pressure run: at least `5` observed on completed first through fifth tasks.

### Per-Task Progress Delta

- First through fifth pressure-test tasks are terminal review:
  - `task-1778765376492`: `review-pending/review/100`, AI job `ai-job-1778767110100-26ff`
  - `task-1778765377823`: `review-pending/review/100`, AI job `ai-job-1778771343370-1190`
  - `task-1778765378939`: `review-pending/review/100`, AI job `ai-job-1778773022772-b3e4`
  - `task-1778765380166`: `review-pending/review/100`, AI job `ai-job-1778775067966-dc2c`
  - `task-1778765382204`: `review-pending/review/100`, AI job `ai-job-1778779185910-40c8`, `completedAt=2026-05-14T17:22:21.175Z`
- Current active task remains the sixth pressure-test task:
  - Task: `task-1778765385568`
  - Material: `3995882041044285`
  - File: `Cambridge IGCSE(0580) Extended Mathematics Student Book_2018(Oxford University Press).pdf`
  - File size: `96516982`
  - Active MinerU task id: `604e1d2e-5691-4f4d-9150-149e3a559f14`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Task-level message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - Latest corrective active-task re-sample at `2026-05-14T17:29:05Z` showed `updatedAt=2026-05-14T17:29:04.314Z` and `mineruLastStatusAt=2026-05-14T17:29:04.312Z`
  - Compact observation: `activity=log-observation-unattributed`, `observationStale=true`, `logUpdatedAt=2026-05-14T17:06:42.094Z`
- Remaining pressure-test tasks: `18` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint initially returned stale-window evidence for the previous fifth task, but a corrective re-sample confirmed the current active task is `task-1778765385568`.
- Admission circuit: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=18`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health request without explicit extra probe params timed out after `10s` with no response in this pass.
- Follow-up lightweight Ollama read-only checks, without chat inference load:
  - `/api/version`: `{"version":"0.23.2"}`
  - `/api/ps`: `qwen3.5:9b` present/resident, `size_vram=9738673088`, `context_length=32768`, expiry `2026-05-16T01:22:21.140352+08:00`
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=73`, `failed_tasks=0`.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check remained reachable.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `3 days, 23:52`; load averages `5.06 4.95 4.96`.
- Disk at production path: `1.9Ti`, used `539Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `1.78%`, memory `7.695MiB / 11.67GiB`
  - `cms-upload-server`: CPU `5.21%`, memory `73.88MiB / 4GiB`
  - `cms-db-server`: CPU `2.92%`, memory `36.24MiB / 512MiB`
  - `cms-minio`: CPU `0.02%`, memory `187.3MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_PROGRESS`
- The pressure-test run made real progress since Pass 9: the fifth large PDF reached `review-pending/review`, and the sixth large PDF became the active MinerU task.
- Stall/hang criteria are not met because task state changed, the active task changed, terminal review evidence increased from `5` at the corrective sample, and direct MinerU reports one active processing task with no failures.
- No explicit pressure-run task failure was observed.
- Runtime core services remained reachable/healthy enough for monitoring.
- Watch item for next pass: the sixth task currently has stale/unattributed MinerU log observation; compare next pass for fresh `updatedAt` / `mineruLastStatusAt`, task transition, or new MinerU progress before considering stall criteria.
- Dependency-health without extra probe params continued to time out, while direct Ollama version/ps remained reachable and `qwen3.5:9b` resident.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 8 - Read-Only Monitoring

- Timestamp: `2026-05-15T00:58+0800` (`2026-05-14T16:58Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `209m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`

### Aggregate State

- `review-pending/review`: `4`
- `running/mineru-processing`: `1`
- `pending/upload`: `19`
- Pressure-run material aggregate:
  - `material:reviewing mineru:completed ai:analyzed`: `4`
  - `material:processing mineru:pending ai:pending`: `20`
- AI jobs for this pressure run: at least `4` observed on completed first through fourth tasks.

### Per-Task Progress Delta

- First through fourth pressure-test tasks remain terminal review:
  - `task-1778765376492`: `review-pending/review/100`, AI job `ai-job-1778767110100-26ff`
  - `task-1778765377823`: `review-pending/review/100`, AI job `ai-job-1778771343370-1190`
  - `task-1778765378939`: `review-pending/review/100`, AI job `ai-job-1778773022772-b3e4`
  - `task-1778765380166`: `review-pending/review/100`, AI job `ai-job-1778775067966-dc2c`
- Current active task remains the fifth pressure-test task:
  - Task: `task-1778765382204`
  - Material: `4413655764085495`
  - File: `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics _2018(Haese Mathematics).pdf`
  - File size: `91501329`
  - Active MinerU task id: `110919d1-13eb-4c16-9594-09a3c77da8df`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Task-level message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - `updatedAt`: `2026-05-14T16:58:27.660Z`
  - `mineruLastStatusAt`: `2026-05-14T16:58:27.623Z`
  - Latest observed progress evidence: phase `MFR Predict`, `1424/1455`, `98%`, `lastProgressObservedAt=2026-05-14T16:38:43.000Z`
  - Observation stale: `true`, stale reason `host-filesystem MinerU log file is stale while MinerU API is still processing`
- Remaining pressure-test tasks: `19` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint returned one active/current processing task, `task-1778765382204`.
- Active-task observation for `task-1778765382204`:
  - `activityLevel`: `log-observation-stale`
  - Phase: `MFR Predict`
  - Progress signal: `1424/1455`, `98%`
  - `lastProgressObservedAt`: `2026-05-14T16:38:43.000Z`
  - `logUpdatedAt`: `2026-05-14T16:40:54.376Z`
  - `observerCheckedAt`: `2026-05-14T16:58:27.644Z`
  - Attribution: `task-1778765382204`, `live-active`
  - No error signal observed in the active-task payload.
- Admission circuit: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=19`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health without explicit extra probe params returned `ok=false`, `blocking=false` due to Ollama tags timeout:
  - MinIO OK.
  - MinerU OK, health OK, submit probe disabled for this request.
  - Ollama reported `serviceReachable=false`, `tagsOk=false`, `modelPresent=false`, `modelResident=false`, `failureKind=tags-error`, error `The operation was aborted due to timeout`.
- Follow-up lightweight Ollama read-only checks, without chat inference load:
  - `/api/version`: `{"version":"0.23.2"}`
  - `/api/ps`: `qwen3.5:9b` present/resident, `size_vram=9738673088`, `context_length=32768`, expiry `2026-05-16T00:28:41.085504+08:00`
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=72`, `failed_tasks=0`.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check: `200` in `0.031368s`.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `3 days, 23:52`; load averages `5.06 4.95 4.96`.
- Disk at production path: `1.9Ti`, used `539Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `1.78%`, memory `7.695MiB / 11.67GiB`
  - `cms-upload-server`: CPU `5.21%`, memory `73.88MiB / 4GiB`
  - `cms-db-server`: CPU `2.92%`, memory `36.24MiB / 512MiB`
  - `cms-minio`: CPU `0.02%`, memory `187.3MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_STALE_PROGRESS_OBSERVATION`
- The pressure-test run has not reached a final success/fail/stall/down outcome.
- No additional task reached review since Pass 7, but the current active task has fresh `updatedAt` / `mineruLastStatusAt` and direct MinerU still reports one processing task with no failures.
- Stall/hang criteria are not yet met because this is the first pass where the fifth task stayed active without terminal progression; the brief requires two consecutive 30-minute passes with no state/stage/progress/message/updatedAt/MinerU/AI evidence changes and no clear active MinerU/AI progress.
- No explicit pressure-run task failure was observed.
- Runtime core services remained reachable/healthy enough for monitoring.
- Watch item for next pass: if `task-1778765382204` remains nonterminal with unchanged state/stage/progress/message, no new `updatedAt`/`mineruLastStatusAt`, and no fresh MinerU/AI progress, evaluate against `HUNG_OR_STALLED`.
- Dependency-health without extra probe params continued to time out on Ollama tags, while direct Ollama version/ps remained reachable and `qwen3.5:9b` resident.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 9 - Read-Only Monitoring

- Timestamp: `2026-05-15T01:29+0800` (`2026-05-14T17:29Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `240m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`

### Aggregate State

- `review-pending/review`: `5`
- `running/mineru-processing`: `1`
- `pending/upload`: `18`
- Pressure-run material aggregate:
  - `material:reviewing mineru:completed ai:analyzed`: `5`
  - `material:processing mineru:pending ai:pending`: `19`
- AI jobs for this pressure run: at least `5` observed on completed first through fifth tasks.

### Per-Task Progress Delta

- First through fourth pressure-test tasks remain terminal review:
  - `task-1778765376492`: `review-pending/review/100`, AI job `ai-job-1778767110100-26ff`
  - `task-1778765377823`: `review-pending/review/100`, AI job `ai-job-1778771343370-1190`
  - `task-1778765378939`: `review-pending/review/100`, AI job `ai-job-1778773022772-b3e4`
  - `task-1778765380166`: `review-pending/review/100`, AI job `ai-job-1778775067966-dc2c`
- Fifth pressure-test task completed MinerU + AI and reached review:
  - Task: `task-1778765382204`
  - Material: `4413655764085495`
  - File: `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics _2018(Haese Mathematics).pdf`
  - File size: `91501329`
  - State/stage/progress: `review-pending` / `review` / `100`
  - Message: `AI 识别完成: review-pending (待人工复核)`
  - MinerU task id: `110919d1-13eb-4c16-9594-09a3c77da8df`
  - AI job id: `ai-job-1778779185910-40c8`
  - `updatedAt`: `2026-05-14T17:22:21.177Z`
  - `completedAt`: `2026-05-14T17:22:21.175Z`
  - MinerU completion/backfill observation: `Processing pages`, `500/500`, `100%`, `lastProgressObservedAt=2026-05-14T17:19:50.315Z`
- Current active task moved to the sixth pressure-test task:
  - Task: `task-1778765385568`
  - Material: `3995882041044285`
  - File: `Cambridge IGCSE(0580) Extended Mathematics Student Book_2018(Oxford University Press).pdf`
  - File size: `96516982`
  - Active MinerU task id: `604e1d2e-5691-4f4d-9150-149e3a559f14`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Task-level message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - `updatedAt`: `2026-05-14T17:29:45.129Z`
  - `mineruLastStatusAt`: `2026-05-14T17:29:45.127Z`
- Remaining pressure-test tasks: `18` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint confirmed the sixth pressure-test task `task-1778765385568` as active/current processing after a corrective re-sample.
- Active-task observation for `task-1778765385568`:
  - `activityLevel`: `log-observation-unattributed`
  - `observationStale`: `true`
  - `lastProgressObservedAt`: `2026-05-14T17:29:45.127Z`
  - `logUpdatedAt`: `2026-05-14T17:06:42.094Z`
  - No terminal error was observed in the compact active-task payload.
- Admission circuit: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=18`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health request without explicit extra probe params timed out after `10s` with no response in this pass.
- Follow-up lightweight Ollama read-only checks, without chat inference load:
  - `/api/version`: `{"version":"0.23.2"}`
  - `/api/ps`: `qwen3.5:9b` present/resident, `size_vram=9738673088`, `context_length=32768`, expiry `2026-05-16T01:22:21.140352+08:00`
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=73`, `failed_tasks=0`.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check remained reachable.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `3 days, 23:52`; load averages `5.06 4.95 4.96`.
- Disk at production path: `1.9Ti`, used `539Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `1.78%`, memory `7.695MiB / 11.67GiB`
  - `cms-upload-server`: CPU `5.21%`, memory `73.88MiB / 4GiB`
  - `cms-db-server`: CPU `2.92%`, memory `36.24MiB / 512MiB`
  - `cms-minio`: CPU `0.02%`, memory `187.3MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_PROGRESS`
- The pressure-test run made real progress since Pass 8: the fifth large PDF reached `review-pending/review`, and the sixth large PDF became the active MinerU task.
- Stall/hang criteria are not met because task state changed, the active task changed, terminal review evidence increased from `4` to `5` tasks, and direct MinerU reports one active processing task with no failures.
- No explicit pressure-run task failure was observed.
- Runtime core services remained reachable/healthy enough for monitoring.
- Watch item for next pass: the new sixth task currently has stale/unattributed MinerU log observation shortly after becoming active; compare on the next pass before considering stall criteria.
- Dependency-health without extra probe params continued to time out, while direct Ollama version/ps remained reachable and `qwen3.5:9b` resident.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 12 - Read-Only Monitoring

- Timestamp: `2026-05-15T03:00+0800` (`2026-05-14T18:59-19:00Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `330m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`
- Total AI metadata job count: `58`

### Aggregate State

- `review-pending/review`: `8`
- `running/mineru-processing`: `1`
- `pending/upload`: `15`
- Pressure-run material aggregate:
  - `material:reviewing mineru:completed ai:analyzed`: `8`
  - `material:processing mineru:pending ai:pending`: `16`
- AI jobs for this pressure run: at least `8` observed on completed first through eighth tasks.

### Per-Task Progress Delta

- First through eighth pressure-test tasks are terminal review.
- Eighth pressure-test task completed MinerU + AI and reached review:
  - Task: `task-1778765393188`
  - Material: `2840047402983096`
  - File size: `53.2 MB`
  - State/stage/progress: `review-pending` / `review` / `100`
  - Message: `AI 识别完成: review-pending (待人工复核)`
  - MinerU task id: `145620af-4293-4ffa-b483-6ed29d4c9bf1`
  - AI job id: `ai-job-1778783794555-3d8c`
  - `completedAt`: `2026-05-14T18:38:59.408Z`
  - MinerU completion observation: phase `Processing pages`, `578/578`, `100%`, `lastProgressObservedAt=2026-05-14T18:36:23.000Z`
- Current active task moved to the ninth pressure-test task:
  - Task: `task-1778765397977`
  - Material: `1348196068935539`
  - File size: `97.3 MB`
  - Active MinerU task id: `3dc49227-3399-4491-9a4d-01568e308eeb`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Task-level message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - `updatedAt`: `2026-05-14T19:00:03.268Z`
  - `mineruLastStatusAt`: `2026-05-14T18:59:59.611Z`
  - Active-task task-local observation: `activityLevel=log-observation-unattributed`, `observationStale=true`, `logUpdatedAt=2026-05-14T18:06:44.810Z`
  - Global MinerU observation resolved fresh live progress for this active task: attribution `task-1778765397977`, phase `MFR Predict`, `80/743`, `11%`, `lastProgressObservedAt=2026-05-14T18:59:43.000Z`, `logUpdatedAt=2026-05-14T19:00:09.222Z`, `observationStale=false`, `activityLevel=active-progress`
- Remaining pressure-test tasks: `15` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint confirmed the ninth pressure-test task `task-1778765397977` as active/current processing.
- Admission circuit endpoint: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=15`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health request without explicit extra probe params timed out after `10s` with no response in this pass.
- Follow-up lightweight Ollama read-only checks, without chat inference load:
  - `/api/version`: `{"version":"0.23.2"}`
  - `/api/ps`: `qwen3.5:9b` present/resident, `size_vram=9738673088`, `context_length=32768`, expiry `2026-05-16T02:38:59.292687+08:00`
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=76`, `failed_tasks=0`.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check: `200` in `0.006650s`.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `4 days, 1:53`; load averages `3.67 3.71 4.18`.
- Disk at production path: `1.9Ti`, used `541Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.00%`, memory `7.707MiB / 11.67GiB`
  - `cms-upload-server`: CPU `0.02%`, memory `76.98MiB / 4GiB`
  - `cms-db-server`: CPU `0.01%`, memory `36.41MiB / 512MiB`
  - `cms-minio`: CPU `0.00%`, memory `179.9MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_PROGRESS`
- The pressure-test run made real progress since Pass 11: the eighth large PDF reached `review-pending/review`, and the ninth large PDF became the active MinerU task.
- Stall/hang criteria are not met because task state changed, the active task changed, terminal review evidence increased from `7` to `8` tasks, and global MinerU observation shows fresh live progress for the active task.
- No explicit pressure-run task failure was observed.
- Runtime core services remained reachable/healthy enough for monitoring.
- Watch item for next pass: active-task task-local log attribution was stale/unattributed, but global MinerU observation was fresh and attributed to the active task. Recompare task-local and global observation next pass.
- Dependency-health without extra probe params continued to time out, while direct Ollama version/ps remained reachable and `qwen3.5:9b` resident.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 13 - Read-Only Monitoring

- Timestamp: `2026-05-15T03:30+0800` (`2026-05-14T19:29Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `360m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`
- Total AI metadata job count: `59`

### Aggregate State

- `review-pending/review`: `9`
- `running/mineru-processing`: `1`
- `pending/upload`: `14`
- Pressure-run material aggregate:
  - `material:reviewing mineru:completed ai:analyzed`: `9`
  - `material:processing mineru:pending ai:pending`: `15`
- AI jobs for this pressure run: at least `9` observed on completed first through ninth tasks.

### Per-Task Progress Delta

- First through ninth pressure-test tasks are terminal review.
- Ninth pressure-test task completed MinerU + AI and reached review:
  - Task: `task-1778765397977`
  - Material: `1348196068935539`
  - File size: `97.3 MB`
  - State/stage/progress: `review-pending` / `review` / `100`
  - Message: `AI 识别完成: review-pending (待人工复核)`
  - MinerU task id: `3dc49227-3399-4491-9a4d-01568e308eeb`
  - AI job id: `ai-job-1778786201966-23d9`
  - `completedAt`: `2026-05-14T19:19:05.853Z`
  - MinerU completion observation: phase `Processing pages`, `891/891`, `100%`, `lastProgressObservedAt=2026-05-14T19:16:45.321Z`
- Current active task moved to the tenth pressure-test task:
  - Task: `task-1778765401421`
  - Material: `1912467100915936`
  - File: `Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Hodder Education).pdf`
  - File size: `38.0 MB`
  - Active MinerU task id: `fe50cf75-05a9-4b43-abe0-c17b8b0dc81a`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Task-level message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - `updatedAt`: `2026-05-14T19:29:43.532Z`
  - `mineruLastStatusAt`: `2026-05-14T19:29:42.312Z`
  - Active-task task-local observation: `activityLevel=log-observation-unattributed`, `observationStale=true`, `logUpdatedAt=2026-05-14T19:06:45.168Z`
  - Global MinerU observation resolved fresh live progress for this active task: attribution `task-1778765401421`, phase `MFR Predict`, `384/883`, `43%`, `lastProgressObservedAt=2026-05-14T19:29:02.000Z`, `logUpdatedAt=2026-05-14T19:29:42.575Z`, `observationStale=false`, `activityLevel=active-progress`
- Remaining pressure-test tasks: `14` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint confirmed the tenth pressure-test task `task-1778765401421` as active/current processing.
- Admission circuit endpoint: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=14`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health request without explicit extra probe params timed out after `10s` with no response in this pass.
- Follow-up lightweight Ollama read-only checks, without chat inference load:
  - `/api/version`: `{"version":"0.23.2"}`
  - `/api/ps`: `qwen3.5:9b` present/resident, `size_vram=9738673088`, `context_length=32768`, expiry `2026-05-16T03:19:05.811332+08:00`
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=77`, `failed_tasks=0`.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check: `200` in `0.009259s`.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `4 days, 2:24`; load averages `4.71 4.44 4.63`.
- Disk at production path: `1.9Ti`, used `542Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.11%`, memory `7.703MiB / 11.67GiB`
  - `cms-upload-server`: CPU `4.54%`, memory `78.81MiB / 4GiB`
  - `cms-db-server`: CPU `4.31%`, memory `35.49MiB / 512MiB`
  - `cms-minio`: CPU `0.05%`, memory `182MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_PROGRESS`
- The pressure-test run made real progress since Pass 12: the ninth large PDF reached `review-pending/review`, and the tenth PDF became the active MinerU task.
- Stall/hang criteria are not met because task state changed, the active task changed, terminal review evidence increased from `8` to `9` tasks, and global MinerU observation shows fresh live progress for the active task.
- No explicit pressure-run task failure was observed.
- Runtime core services remained reachable/healthy enough for monitoring.
- Watch item for next pass: active-task task-local log attribution was stale/unattributed again, but global MinerU observation was fresh and attributed to the active task. Recompare task-local and global observation next pass.
- Dependency-health without extra probe params continued to time out, while direct Ollama version/ps remained reachable and `qwen3.5:9b` resident.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 14 - Read-Only Monitoring

- Timestamp: `2026-05-15T04:00+0800` (`2026-05-14T19:59Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `390m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`
- Total AI metadata job count: `60`

### Aggregate State

- `review-pending/review`: `10`
- `running/mineru-processing`: `1`
- `pending/upload`: `13`
- Pressure-run material aggregate:
  - `material:reviewing mineru:completed ai:analyzed`: `10`
  - `material:processing mineru:pending ai:pending`: `14`
- AI jobs for this pressure run: at least `10` observed on completed first through tenth tasks.

### Per-Task Progress Delta

- First through tenth pressure-test tasks are terminal review.
- Tenth pressure-test task completed MinerU + AI and reached review:
  - Task: `task-1778765401421`
  - Material: `1912467100915936`
  - File: `Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Hodder Education).pdf`
  - File size: `38.0 MB`
  - State/stage/progress: `review-pending` / `review` / `100`
  - Message: `AI 识别完成: review-pending (待人工复核)`
  - MinerU task id: `fe50cf75-05a9-4b43-abe0-c17b8b0dc81a`
  - AI job id: `ai-job-1778787698876-bef3`
  - `completedAt`: `2026-05-14T19:44:31.003Z`
  - MinerU completion observation: phase `Processing pages`, `560/560`, `100%`, `lastProgressObservedAt=2026-05-14T19:40:49.000Z`
- Current active task moved to the eleventh pressure-test task:
  - Task: `task-1778765403100`
  - Material: `147911139785683`
  - File: `Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf`
  - File size: `37.3 MB`
  - Active MinerU task id: `8d36cf2f-91a7-4186-b47c-4debf78562d8`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Task-level message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - `updatedAt`: `2026-05-14T19:59:37.925Z`
  - `mineruLastStatusAt`: `2026-05-14T19:59:37.924Z`
  - Active-task task-local observation: `activityLevel=log-observation-unattributed`, `observationStale=true`, `logUpdatedAt=2026-05-14T19:06:45.168Z`
  - Global MinerU observation resolved fresh live progress for this active task: attribution `task-1778765403100`, phase `MFR Predict`, `800/830`, `96%`, `lastProgressObservedAt=2026-05-14T19:57:33.000Z`, `logUpdatedAt=2026-05-14T19:58:54.471Z`, `observationStale=false`, `activityLevel=active-progress`
- Remaining pressure-test tasks: `13` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint confirmed the eleventh pressure-test task `task-1778765403100` as active/current processing.
- Admission circuit endpoint: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=13`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health request without explicit extra probe params timed out after `10s` with no response in this pass.
- Follow-up lightweight Ollama read-only checks, without chat inference load:
  - `/api/version`: `{"version":"0.23.2"}`
  - `/api/ps`: `qwen3.5:9b` present/resident, `size_vram=9738673088`, `context_length=32768`, expiry `2026-05-16T03:44:30.798443+08:00`
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=78`, `failed_tasks=0`.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check: `200` in `0.017132s`.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `4 days, 2:54`; load averages `3.66 4.19 4.68`.
- Disk at production path: `1.9Ti`, used `542Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.54%`, memory `7.703MiB / 11.67GiB`
  - `cms-upload-server`: CPU `0.51%`, memory `81MiB / 4GiB`
  - `cms-db-server`: CPU `2.79%`, memory `46.57MiB / 512MiB`
  - `cms-minio`: CPU `0.01%`, memory `183.2MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_PROGRESS`
- The pressure-test run made real progress since Pass 13: the tenth PDF reached `review-pending/review`, and the eleventh PDF became the active MinerU task.
- Stall/hang criteria are not met because task state changed, the active task changed, terminal review evidence increased from `9` to `10` tasks, and global MinerU observation shows fresh live progress for the active task.
- No explicit pressure-run task failure was observed.
- Runtime core services remained reachable/healthy enough for monitoring.
- Watch item for next pass: active-task task-local log attribution remained stale/unattributed, but global MinerU observation was fresh and attributed to the active task. Recompare task-local and global observation next pass.
- Dependency-health without extra probe params continued to time out, while direct Ollama version/ps remained reachable and `qwen3.5:9b` resident.
- No final report was written and the task row was not returned to Director in this pass.

## Pass 16 - Final Read-Only Monitoring

- Timestamp: `2026-05-15T05:32+0800` (`2026-05-14T21:32Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `482m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`

### Aggregate State

- `review-pending/review`: `20`
- `failed/ai`: `3`
- `running/mineru-processing`: `1`

### First Failure Evidence

- First pressure-run terminal failure observed in this pass:
  - Task: `task-1778765409131`
  - Material: `3785564880839595`
  - File: `走向成功_英语_二模卷16篇`
  - File size: `3.3 MB`
  - State/stage/progress: `failed` / `ai` / `100`
  - Message: `AI 识别完成: failed`
  - MinerU task id: `0d55a13b-2753-4fbc-a722-8951cf11f9fd`
  - AI job id: `ai-job-1778792166467-9699`
  - Failure detail: `[AI 严格模式拦截] 不允许降级到骨架模型: AI Provider 调用全部失败: Ollama Provider Error: [TimeoutError] The operation was aborted due to timeout (BaseURL: http://host.docker.internal:11434, Model: qwen3.5:9b, Duration: 179956ms, Timeout: 180000ms)；严格模式禁止骨架兜底`
  - `completedAt`: `2026-05-14T21:02:11.292Z`
- Additional pressure-run terminal AI failures observed:
  - `task-1778765412523`, file `附件三：考务流程培训-纸笔标准考试`, AI job `ai-job-1778792264103-56b5`, completed `2026-05-14T21:11:39.537Z`, failure detail: Ollama provider timeout at about `180005ms`; strict mode blocked skeleton fallback.
  - `task-1778765415701`, file `2025`, AI job `ai-job-1778792291124-94e7`, completed `2026-05-14T21:19:29.003Z`, failure detail: repair stage timeout at about `180004ms`; strict mode blocked skeleton fallback.

### Remaining Active Work

- One pressure-run task was still non-terminal at final observation:
  - Task: `task-1778765417422`
  - File: `06第六章 长期股权投资与合营安排`
  - State/stage/progress: `running` / `mineru-processing` / `50`
  - MinerU task id: `dcdb27f3-fac6-4ede-b456-a96fe358b0da`
  - Active-task message: `MinerU 正在处理，但日志观测滞后：backend=pipeline，相位 表格识别，批次 1/1，页 62/62`
  - Global observation: attribution `task-1778765417422`, phase `Table-ocr det`, `65/66`, `98%`, `observationStale=false`, `activityLevel=active-progress`

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint confirmed `task-1778765417422` as active/current processing.
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=91`, `failed_tasks=0`.
- Docker Compose services remained healthy in the prior same heartbeat sampling window.
- Dependency health without extra probe params continued to time out; direct Ollama `/api/version` and `/api/ps` remained reachable in the same monitoring sequence, with `qwen3.5:9b` resident.

### Assessment

- Final outcome: `FAILED`
- Reason: Task brief states `FAILED` when one or more pressure-test tasks reaches terminal failed state. Three pressure-run tasks reached terminal `failed/ai`.
- This is not a machine/service-down result: upload health, direct MinerU health, and service status remained reachable enough for monitoring.
- This is not a stall/hang result: the run continued to make progress, and one MinerU task still had live global progress.
- Final report was written and the task row was returned to Director for review.

## Pass 15 - Read-Only Monitoring

- Timestamp: `2026-05-15T04:30+0800` (`2026-05-14T20:29Z` evidence window)
- Approximate elapsed time since first pressure-test task creation: `420m`
- Development workspace command first run: `git status --short --branch` only; branch remained `development-engineer/p0-post-validation-ollama-mineru-blockers` with existing local modifications/untracked files.
- Production workspace GitHub sync: not run.
- Pressure-test task set identification method: tasks created after baseline newest task `task-1778763994124` / `2026-05-14T13:06:34.255Z`
- Pressure-test task count detected: `24`
- Total task count: `74`
- Total material count: `74`
- Total AI metadata job count: `61`

### Aggregate State

- `review-pending/review`: `11`
- `running/mineru-processing`: `1`
- `pending/upload`: `12`
- Pressure-run material aggregate:
  - `material:reviewing mineru:completed ai:analyzed`: `11`
  - `material:processing mineru:pending ai:pending`: `13`
- AI jobs for this pressure run: at least `11` observed on completed first through eleventh tasks.

### Per-Task Progress Delta

- First through eleventh pressure-test tasks are terminal review.
- Eleventh pressure-test task completed MinerU + AI and reached review:
  - Task: `task-1778765403100`
  - Material: `147911139785683`
  - File: `Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf`
  - File size: `37.3 MB`
  - State/stage/progress: `review-pending` / `review` / `100`
  - Message: `AI 识别完成: review-pending (待人工复核)`
  - MinerU task id: `8d36cf2f-91a7-4186-b47c-4debf78562d8`
  - AI job id: `ai-job-1778790035894-a3d6`
  - `completedAt`: `2026-05-14T20:23:14.033Z`
  - MinerU completion observation: phase `Processing pages`, `714/714`, `100%`, `lastProgressObservedAt=2026-05-14T20:20:15.000Z`
- Current active task moved to the twelfth pressure-test task:
  - Task: `task-1778765405253`
  - Material: `1159591343520524`
  - File: `Cambridge IGCSE(0580)  Core  Mathematics_2023(Hodder Education).pdf`
  - File size: `60.6 MB`
  - Active MinerU task id: `d9108ff5-dc8e-4a04-81e0-1142d04c3865`
  - Active state/stage/progress: `running` / `mineru-processing` / `50`
  - Task-level message: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - `updatedAt`: `2026-05-14T20:29:47.649Z`
  - `mineruLastStatusAt`: `2026-05-14T20:29:47.648Z`
  - Active-task task-local observation: `activityLevel=log-observation-unattributed`, `observationStale=true`, `logUpdatedAt=2026-05-14T20:06:46.645Z`
  - Global MinerU observation resolved fresh live progress for this active task: attribution `task-1778765405253`, phase `Table-wired Predict`, `17/28`, `61%`, batch `1/6`, pages `64/380`, `lastProgressObservedAt=2026-05-14T20:20:57.000Z`, `logUpdatedAt=2026-05-14T20:29:46.776Z`, `observationStale=false`, `activityLevel=active-progress`
- Remaining pressure-test tasks: `12` still `pending/upload` with progress `0`.

### Runtime / Endpoint Snapshot

- Upload health: OK.
- Active-task endpoint confirmed the twelfth pressure-test task `task-1778765405253` as active/current processing.
- Admission circuit endpoint: `open=false`, state `closed`, reason `mineru-submit-recovery-pending`.
- Admission counts: `parsePending=12`, `parseRunning=1`, `aiPending=0`, `aiRunning=0`.
- Dependency health request without explicit extra probe params timed out after `10s` with no response in this pass.
- Follow-up lightweight Ollama read-only checks, without chat inference load:
  - `/api/version`: `{"version":"0.23.2"}`
  - `/api/ps`: `qwen3.5:9b` present/resident, `size_vram=9738673088`, `context_length=32768`, expiry `2026-05-16T04:23:14.016001+08:00`
- Direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=1`, `completed_tasks=79`, `failed_tasks=0`.
- Docker Compose: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- Production `/cms/tasks` HTTP spot-check: `200` in `0.005249s`.

### Resource Snapshot

- Production HEAD: `89271a1 Dispatch db-sync hardening production deployment`.
- Production git status: local modifications still present in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx`.
- `uptime`: up `4 days, 3:24`; load averages `4.70 4.33 4.50`.
- Disk at production path: `1.9Ti`, used `543Gi`, available `1.3Ti`, capacity `30%`.
- Docker stats for Luceon services:
  - `cms-frontend`: CPU `0.00%`, memory `7.703MiB / 11.67GiB`
  - `cms-upload-server`: CPU `0.04%`, memory `79.61MiB / 4GiB`
  - `cms-db-server`: CPU `0.77%`, memory `61.85MiB / 512MiB`
  - `cms-minio`: CPU `0.02%`, memory `183.1MiB / 1GiB`

### Assessment

- Status: `RUNNING_WITH_PROGRESS`
- The pressure-test run made real progress since Pass 14: the eleventh PDF reached `review-pending/review`, and the twelfth PDF became the active MinerU task.
- Stall/hang criteria are not met because task state changed, the active task changed, terminal review evidence increased from `10` to `11` tasks, and global MinerU observation shows fresh live progress for the active task.
- No explicit pressure-run task failure was observed.
- Runtime core services remained reachable/healthy enough for monitoring.
- Watch item for next pass: active-task task-local log attribution remained stale/unattributed, but global MinerU observation was fresh and attributed to the active task. Recompare task-local and global observation next pass.
- Dependency-health without extra probe params continued to time out, while direct Ollama version/ps remained reachable and `qwen3.5:9b` resident.
- No final report was written and the task row was not returned to Director in this pass.
