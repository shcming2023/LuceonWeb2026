# TestAcceptanceEngineer Report: P0 Controlled Live Task Progress Semantics Validation With Prod Testpdf Source

- Task ID: `TASK-20260513-134116-P0-Controlled-Live-Task-Progress-Semantics-Validation-With-Prod-Testpdf-Source`
- Report time: `2026-05-13T13:50:15+0800`
- Role: `TestAcceptanceEngineer`
- Task brief: `TaskAndReport/2026-05-13T13-41-16+0800_P0-Controlled-Live-Task-Progress-Semantics-Validation-With-Prod-Testpdf-Source_TASK.md`
- Recommendation: `FAIL_FOR_PROGRESS_SEMANTICS_AND_AI_TERMINAL_STATE`

## 1. Basis And Scope

This validation was executed from the Director task brief above after reading the required project, role, testing, runtime-ownership, prior report, and Director-review documents.

Assigned objective: perform exactly one controlled small/medium production upload from `/Users/concm/prod_workspace/Luceon2026/testpdf`, then observe task-page/API MinerU progress semantics and terminal or bounded ongoing state.

Actual outcome:

- Exactly one controlled upload was performed after preflight passed.
- MinerU parsed successfully and stored parsed artifacts.
- API observation did not show `mineruObservedProgress.progressSemantics`.
- The task reached terminal `failed` at AI stage after strict no-skeleton AI failures.

This report does not claim production release readiness, L3, pressure PASS, or full acceptance.

## 2. Workspaces

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Entered production deployment path: yes.
- Production HEAD: `301e4da Record production validation sync remediation`
- Production local override status: `docker-compose.override.yml` modified locally, preserved.
- Repository file changes made by this role: this report and the task-tracking row only.

Development workspace status before execution:

```text
## development-engineer/p0-ai-metadata-smoke-timeout-semantics-alignment
```

The development workspace already had unrelated modified and untracked files. They were not reverted or edited by this validation task, except for this report and the task-tracking row.

## 3. Selected Sample

Selected sample:

```text
/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf
```

Selection reason: 3-page, 530205-byte PDF from the corrected authorized `testpdf` source; small enough for bounded observation and larger than the very small single-document samples.

Evidence commands:

```bash
stat -f 'size=%z path=%N' "$S"
shasum -a 256 "$S"
file "$S"
mdls -name kMDItemNumberOfPages -name kMDItemContentType -name kMDItemFSSize "$S"
```

Exit code: `0`

Evidence:

- Size: `530205` bytes
- SHA-256: `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`
- File type: `PDF document, version 1.7`
- macOS metadata: `kMDItemNumberOfPages = 3`, `kMDItemContentType = "com.adobe.pdf"`

Sample file was not moved, renamed, edited, normalized, deleted, or copied into the repository.

## 4. Production Preflight

Command group:

```bash
git status --short --branch
git log -1 --oneline
docker compose ps
curl -fsS http://localhost:8081/__proxy/upload/health
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
curl -sS --max-time 10 http://127.0.0.1:11434/api/ps
```

Exit code: `0`

Key evidence:

- Production branch: `main...origin/main`
- Production HEAD: `301e4da Record production validation sync remediation`
- Docker services: `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` up and healthy.
- Upload health: `ok=true`.
- Dependency health: `ok=true`, `blocking=false`.
- MinerU submit probe: `ok=true`, HTTP `202`, task id `47880970-c2be-4946-a0b3-89f92f06dd78`.
- Admission circuit: `state=closed`, `open=false`, `activeTaskClean=true`.
- Active-task diagnostics before upload: no active task, no current processing task, no queued tasks, no takeover-required tasks.
- Ollama `/api/ps`: `qwen3.5:9b` resident.

Preflight judgment: `PASS`.

## 5. Upload Evidence

Command:

```bash
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  -X POST http://localhost:8081/__proxy/upload/tasks \
  -H "X-Request-Id: tae-task86-$(date +%s)" \
  -F "file=@/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf;type=application/pdf" \
  -F "materialId=validation-progress-1778651225" \
  -F "backend=pipeline"
```

Exit code: `0`

HTTP status: `200`

Upload response:

- `ok=true`
- `taskId=task-1778651226016`
- `materialId=validation-progress-1778651225`
- `objectName=originals/validation-progress-1778651225/source.pdf`
- `fileName=2025_2026学年春季课程中数G8_提取.pdf`
- `mimeType=application/pdf`

Exactly one upload was created.

## 6. State Timeline

Observation method: API polling through production proxy, plus task/material/events queries.

Timeline:

| Time `+0800` | Task state | Stage | Progress | Message / evidence |
| --- | --- | --- | ---: | --- |
| `13:47:21` | `running` | `mineru-processing` | `50` | `MinerU 正在解析`; active-task showed `task-1778651226016`. |
| `13:47:31` | `ai-pending` | `complete` | `100` | `MinerU 解析完成，产物已落库，等待 AI 元数据识别`; material had `markdownObjectName=parsed/validation-progress-1778651225/full.md`. |
| `13:47:42` | `ai-running` | `ai` | `100` | `AI: 正在使用 ollama (qwen3.5:9b) 进行识别...`. |
| `13:48:12` | `ai-running` | `ai` | `100` | Material already showed `status=failed`, `aiStatus=failed`, `processingMsg=AI 识别失败`. |
| `13:48:43` | `failed` | `ai` | `100` | Terminal task message: `AI 识别完成: failed`. |
| `13:49:13` | `failed` | `ai` | `100` | Terminal state stable; no active parse/AI queue. |

Final task:

- `state=failed`
- `stage=ai`
- `progress=100`
- `message=AI 识别完成: failed`
- `mineruStatus=completed`
- `aiJobId=ai-job-1778651249894-5e15`

Final material:

- `status=failed`
- `mineruStatus=completed`
- `aiStatus=failed`
- `metadata.processingStage=ai`
- `metadata.processingMsg=AI 识别失败`

## 7. MinerU Artifact Evidence

Task metadata after terminal state:

- `mineruTaskId=ae1231ab-a00c-481f-97b9-43acf3364959`
- `mineruStatus=completed`
- `mineruQueuedAhead=0`
- `mineruStartedAt=2026-05-13T05:47:08.534478+00:00`
- `mineruLastStatusAt=2026-05-13T05:47:28.264Z`
- `markdownObjectName=parsed/validation-progress-1778651225/full.md`
- `parsedPrefix=parsed/validation-progress-1778651225/`
- `parsedFilesCount=21`
- `artifactManifestObjectName=parsed/validation-progress-1778651225/artifact-manifest.json`
- `zipObjectName=parsed/validation-progress-1778651225/mineru-result.zip`
- `artifactIncomplete=false`

MinerU parse/storage judgment: `PASS`.

## 8. Progress Semantics Evidence

API observation did not show:

- `task.metadata.mineruObservedProgress`
- `task.metadata.mineruObservedProgress.progressSemantics`

Observed related metadata instead:

```text
task.metadata.progressEventKey=state=pending|stage=upload|message=解析完成，提取结果...|logStatus=missing|activity=|phase=|window=|page=|unitType=
material.metadata.progressEventKey=state=running|stage=mineru-processing|message=MinerU 正在解析|logStatus=missing|activity=|phase=|window=|page=|unitType=
```

User-facing progress messages observed through API:

- `MinerU 正在解析`
- `MinerU 解析完成，产物已落库，等待 AI 元数据识别`
- `AI: 正在使用 ollama (qwen3.5:9b) 进行识别...`
- `AI 识别完成: failed`

Progress semantics judgment: `FAIL_NOT_OBSERVED`.

Important boundary: this was a fast 3-page sample. The absence of `progressSemantics` may mean the deployed semantics path was not populated for this fast task, or that the observer/log attribution path did not produce structured progress before completion. It still means the requested live-task semantics evidence was not demonstrated by this run.

## 9. AI Terminal Evidence

Task events recorded two AI provider failures and strict no-skeleton blocking:

- `AI Provider 调用失败: Ollama Provider Error: [TypeError] fetch failed ... Duration: 30247ms, Timeout: 180000ms`
- `AI 识别异常: [AI 严格模式拦截] 不允许降级到骨架模型 ... 严格模式禁止骨架兜底`
- Second attempt failed similarly with `Duration: 30506ms`.

AI job:

- `ai-job-1778651249894-5e15`
- `state=failed`

Post-observation active-task diagnostics:

- no active task;
- no queued tasks;
- no takeover-required tasks;
- `historicalAiFailureTasks` includes `task-1778651226016`.

AI judgment: `FAIL_TERMINAL_AI_FAILED`, while strict no-skeleton behavior was preserved.

## 10. Checks Skipped

- Browser UI observation was skipped because the task brief allowed task detail page and/or API state, and API evidence was sufficient to identify terminal state and absence of `progressSemantics`.
- No second sample was attempted because the task allows exactly one upload.
- No repair/retry/reparse was attempted because the task forbids it.

## 11. Forbidden Actions Not Performed

The following were not performed:

- multiple uploads;
- batch, pressure, stress, concurrency, or 24-PDF retry;
- failed-task repair, reparse, rerun, or cleanup;
- DB, MinIO, Docker volume, task, artifact, log, model, secret, timeout, override, PRD, role-contract, or public API mutation;
- MinerU/Ollama/MinIO/DB restart;
- GitHub push;
- production release-readiness, L3, pressure PASS, or full acceptance declaration.

## 12. Risks And Residual Gaps

- Live `progressSemantics` remains unproven in production after this authorized upload.
- The selected small sample may have parsed too quickly to emit structured MinerU progress semantics, but the task's requested evidence was still absent.
- AI failed despite preflight dependency health showing Ollama resident and chat OK. The failure signature is container-to-host Ollama `fetch failed` around 30 seconds, not a MinerU parse failure.
- The production line now contains one new controlled validation task/material in terminal failed state, as authorized by this task.

## 13. Recommendation To Director

Recommendation: `FAIL_FOR_PROGRESS_SEMANTICS_AND_AI_TERMINAL_STATE`.

Director review should decide whether to:

1. return to DevelopmentEngineer/Architect to inspect why `progressSemantics` was not populated for this live task; and
2. separately diagnose the AI provider `fetch failed` terminal failure if it is considered release-blocking for the current validation track.

This report does not recommend production release readiness, L3, or pressure PASS.
