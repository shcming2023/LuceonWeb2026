# TestAcceptanceEngineer Report: P0 Exactly One Controlled Upload Validation After Task 87 Deployment

- Task ID: `TASK-20260513-144620-P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment`
- Report time: `2026-05-13T15:07:30+0800`
- Role: `TestAcceptanceEngineer`
- Task brief: `TaskAndReport/2026-05-13T14-46-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment_TASK.md`
- Recommendation: `FAIL_WITH_PARTIAL_FIX_CONFIRMED`

## 1. Basis And Scope

This validation was executed from the Director task brief above after reading the required project, role, testing, runtime-ownership, previous validation, DevelopmentEngineer deployment, and Director-review records.

Assigned objective: after Task 87 production deployment, perform exactly one controlled upload of the authorized sample, observe task-page/API MinerU progress semantics or fast-complete diagnostic, and check whether the Ollama AI stage avoids the prior `UND_ERR_HEADERS_TIMEOUT` behavior.

Actual outcome:

- Exactly one controlled upload was performed after preflight passed.
- API and task list exposed `mineruObservedProgress.progressSemantics`.
- The exposed progress semantics were diagnostic, not page/batch business progress: `activityLevel=log-observation-unreadable`, message `MinerU 已提交/正在处理，但暂无可归因业务日志`.
- MinerU parsed successfully and stored parsed artifacts.
- The previous `UND_ERR_HEADERS_TIMEOUT` around 30 seconds did not recur.
- The task still reached terminal `failed` at AI stage after a later two-pass JSON repair / strict no-skeleton failure.

This report does not claim production release readiness, L3, pressure PASS, or full acceptance.

## 2. Workspaces And HEADs

Development workspace:

```text
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026
```

Development preflight:

```bash
git status --short --branch
git log -1 --oneline
git ls-remote origin refs/heads/main
```

Exit code: `0`

Key output:

- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- Local HEAD: `dea8df9 Review production deployment and dispatch upload validation`
- Remote `origin/main`: `dea8df983ae569a1fed4f18338da71198004d1cd`

Production deployment path:

```text
/Users/concm/prod_workspace/Luceon2026
```

Production HEAD:

```text
51f21d0 Record Option A deployment authorization
```

Production local override status:

```text
## main...origin/main
 M docker-compose.override.yml
```

The local override remained preserved and was not modified by this task.

## 3. Sample Evidence

Authorized sample:

```text
/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf
```

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

The sample file was not moved, renamed, edited, normalized, deleted, or copied into the repository.

## 4. Required Preflight

Production preflight command group:

```bash
git status --short --branch
git log -1 --oneline
docker compose ps
curl -fsS http://localhost:8081/__proxy/upload/health
curl -sS --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=1&ollamaChatProbe=1'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
curl -sS --max-time 10 http://127.0.0.1:11434/api/ps
ls -lh '/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf'
```

Exit code: `0`

Preflight evidence:

- Docker services `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` were up and healthy.
- Upload health returned `ok=true`.
- Dependency health returned `ok=true`, `blocking=false`.
- MinerU submit probe returned HTTP `202`, task id `6bc08559-1477-45d3-97ef-f517c9913f08`.
- Ollama chat probe returned `chatOk=true`; `qwen3.5:9b` was resident.
- Admission circuit was `closed`, `open=false`, `activeTaskClean=true`.
- Active-task diagnostics had no active/current/queued/takeover-required work. It only retained historical AI failure `task-1778651226016`.
- Sample file existed at `518K`.

Preflight judgment: `PASS`.

## 5. Upload Evidence

Upload command:

```bash
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  -X POST http://localhost:8081/__proxy/upload/tasks \
  -H "X-Request-Id: tae-task90-$(date +%s)" \
  -F "file=@/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf;type=application/pdf" \
  -F "materialId=validation-postfix-1778655374" \
  -F "backend=pipeline"
```

Exit code: `0`

HTTP status: `200`

Upload response:

- `ok=true`
- `taskId=task-1778655375028`
- `materialId=validation-postfix-1778655374`
- `objectName=originals/validation-postfix-1778655374/source.pdf`
- `fileName=2025_2026学年春季课程中数G8_提取.pdf`
- `mimeType=application/pdf`

Exactly one upload was created.

## 6. Task-Page Visible Evidence

Browser automation used Playwright against production UI. Initial `networkidle` navigation timed out, so the page was read with `domcontentloaded`, which succeeded.

During `ai-running`, the task detail page showed:

- `当前状态`: `AI 分析中`
- `当前阶段`: `ai`
- `已产物`: `已生成 (Markdown)`
- `消息`: `AI: 正在使用 ollama (qwen3.5:9b) 进行识别...`

During the same observation window, the task list row showed:

- status: `AI 元数据识别中`
- progress: `100%`
- visible MinerU diagnostic message: `MinerU 已提交/正在处理，但暂无可归因业务日志`
- visible AI message: `AI: 正在使用 ollama (qwen3.5:9b) 进行识别...`

After terminal failure, the task detail page showed:

- `当前状态`: `失败`
- `当前阶段`: `ai`
- `已产物`: `已生成 (Markdown)`
- `下一步动作`: `需排查或重试`
- `消息`: `AI 识别完成: failed`

After terminal failure, the task list row showed:

- status: `失败`
- terminal marker: `已终止`
- visible MinerU diagnostic message: `MinerU 已提交/正在处理，但暂无可归因业务日志`
- visible AI message: `AI 识别完成: failed`

Screenshots were captured under `/tmp/luceon-task90-*.png` for local reference only and were not committed.

## 7. API State Timeline

Observation method: production API polling plus task/material/AI/event queries.

| Time `+0800` | Task state | Stage | Message | Key evidence |
| --- | --- | --- | --- | --- |
| `14:56:49` | `ai-running` | `ai` | `AI: 正在使用 ollama (qwen3.5:9b) 进行识别...` | MinerU already completed; `progressSemantics` present with `log-observation-unreadable`. |
| `14:57:51` | `ai-running` | `ai` | `AI: 正在进行 JSON Repair...` | First Ollama response had succeeded; JSON repair phase started. |
| `15:01:10` | `ai-running` | `ai` | `AI: 正在进行 JSON Repair...` | AI job still running, no 30s header-timeout terminal failure. |
| `15:03:11` | `failed` | `ai` | `AI 识别完成: failed` | Terminal failure after two-pass JSON repair / strict no-skeleton boundary. |

Final task:

- `state=failed`
- `stage=ai`
- `progress=100`
- `message=AI 识别完成: failed`
- `mineruStatus=completed`
- `aiJobId=ai-job-1778655391785-6d94`

Final material:

- `status=failed`
- `mineruStatus=completed`
- `aiStatus=failed`
- parsed artifact pointers present.

## 8. MinerU Semantics And Artifact Evidence

Task metadata included:

- `mineruTaskId=5cc6acce-061f-4418-a29b-b862af8306a6`
- `mineruStatus=completed`
- `mineruQueuedAhead=0`
- `mineruStartedAt=2026-05-13T06:56:21.692983+00:00`
- `markdownObjectName=parsed/validation-postfix-1778655374/full.md`
- `parsedPrefix=parsed/validation-postfix-1778655374/`
- `parsedFilesCount=21`
- `artifactManifestObjectName=parsed/validation-postfix-1778655374/artifact-manifest.json`
- `zipObjectName=parsed/validation-postfix-1778655374/mineru-result.zip`
- `artifactIncomplete=false`

`mineruObservedProgress.progressSemantics` was present:

```json
{
  "freshness": "missing",
  "activityLevel": "log-observation-unreadable",
  "source": "host-mineru-log-observer",
  "message": "MinerU 已提交/正在处理，但暂无可归因业务日志",
  "pages": {
    "current": null,
    "total": null,
    "start": null,
    "end": null
  }
}
```

Log-source diagnostic:

- `logSourcePath=/host/mineru-logs/mineru-api.err.log`
- `logSourceExists=true`
- `logSourceReadable=false`
- `logSourceSize=0`
- `logSourceSelectedReason=unreadable-or-empty`
- `observationStale=true`
- `observationStaleReason=log file is unreadable or empty`

MinerU judgment:

- Parse/artifact path: `PASS`
- Meaningful page/batch progress: `NOT_OBSERVED`
- Diagnostic semantics / fast-observation boundary: `OBSERVED_AS_LOG_UNREADABLE_DIAGNOSTIC`

Additional event evidence:

- The task briefly recorded a local false-failure due to unreadable log observation:
  `MinerU 日志活性异常判定卡死: activityLevel=log-observation-unreadable...`
- It then corrected itself:
  `Luceon 误判 failed 已纠正：MinerU 5cc6acce-061f-4418-a29b-b862af8306a6 实际已完成，开始拉取结果`
- Parsed artifacts were then saved successfully.

## 9. AI / Ollama Evidence

Event evidence:

- `AI Provider (ollama) 响应成功` at `2026-05-13T06:57:41.601Z`
- `AI Provider (ollama) JSON Repair 成功` at `2026-05-13T06:59:51.370Z`
- `AI 识别完成 (199441ms)` at `2026-05-13T06:59:51.374Z`
- A subsequent AI run started at `2026-05-13T06:59:51.383Z`
- `AI Provider (ollama) 响应成功` at `2026-05-13T07:01:02.962Z`
- `AI Provider (ollama) JSON Repair 失败: Failed to parse JSON from Ollama response, model: qwen3.5:9b` at `2026-05-13T07:02:56.608Z`
- Terminal exception:
  `AI 识别异常: [AI 严格模式拦截] 不允许降级到骨架模型: AI Provider 二段式 JSON 修复失败，降级为 skeleton 结果`

Raw trace highlights:

- First pass duration: `69655ms`
- Repair pass duration: `129742ms`
- First pass failure kind: `json_parse_failed`
- Repair pass raw output was captured.
- `aiClassificationRepairSucceeded=true` exists in task metadata, but final task state still became `failed` after a later strict no-skeleton repair failure.

AI judgment:

- Prior `UND_ERR_HEADERS_TIMEOUT` around 30 seconds: `NOT_REPRODUCED`
- Ollama response after Task 87 timeout fix: `PARTIAL_PASS`
- Final AI terminal state: `FAIL`, due JSON repair / strict no-skeleton boundary.

## 10. Post-Run Runtime Evidence

Post-run active-task diagnostics:

- no active task;
- no current processing task;
- no queued tasks;
- no takeover-required tasks;
- historical AI failures now include `task-1778655375028` and prior `task-1778651226016`.

Post-run dependency health with Ollama chat probe and no MinerU submit probe:

- `ok=true`
- `blocking=false`
- MinerU health OK
- Ollama `chatOk=true`
- `qwen3.5:9b` resident

Post-run admission circuit:

- `state=closed`
- `open=false`
- `activeTaskClean=true`

## 11. Commands Run

All command groups below exited `0` unless noted:

- Development preflight: `git status --short --branch`; `git log -1 --oneline`; `git ls-remote origin refs/heads/main`.
- Production preflight: `git status --short --branch`; `git log -1 --oneline`; `docker compose ps`; upload health; dependency-health with `mineruSubmitProbe=1&ollamaChatProbe=1`; admission circuit; active task; Ollama `/api/ps`; sample `ls -lh`.
- Sample evidence: `stat`; `shasum -a 256`; `file`; `mdls`.
- Upload: one `curl -X POST http://localhost:8081/__proxy/upload/tasks` with the exact authorized file.
- Observation: repeated API polling of task/material/AI job/active-task plus Playwright task-detail and task-list reads.
- Post-run evidence: active-task, dependency-health with `ollamaChatProbe=1`, admission circuit.

Browser `networkidle` navigation timed out on the first attempt, likely due normal frontend background requests. The follow-up `domcontentloaded` read succeeded and supplied task-page-visible evidence.

## 12. Skipped Checks

- No second upload was attempted because the task explicitly allows exactly one upload.
- No repair, reparse, re-AI, cleanup, or retry was attempted because the task forbids it.
- No production restart/rebuild/config/model operation was performed because the task did not authorize it.
- No L3, pressure, or release-readiness validation was attempted.

## 13. Forbidden Actions Not Performed

The following were not performed:

- second upload;
- pressure test, stress test, concurrency test, or 24-PDF retry;
- failed-task repair, reparse, rerun, re-AI, deletion, or cleanup;
- DB, MinIO, Docker volume, log, model, secret, timeout, override, PRD, role-contract, public API, or sample-file mutation outside the natural single-upload task/artifact creation;
- MinerU/Ollama/MinIO/DB restart;
- model pull/delete/replace/reload;
- broad rollback;
- production release-readiness, L3, pressure PASS, or full acceptance declaration.

## 14. Risks And Residual Gaps

- The deployed Task 87 fix improved evidence visibility: `progressSemantics` is now present and task-page-visible as a diagnostic message.
- The diagnostic is still not page/batch/stage business progress because the selected log source is unreadable or empty.
- The task briefly entered a false failed MinerU state due log-observation unreadable, then recovered and ingested artifacts. That self-correction is useful but still exposes a runtime/log-ownership fragility.
- AI no longer fails with the earlier 30-second `UND_ERR_HEADERS_TIMEOUT`, but the end-to-end task still fails in AI because JSON repair can produce a result that later triggers strict no-skeleton failure.
- Metadata shows evidence of an apparently successful AI classification / repair path while final task and material are failed. Director should treat this as a task-state / AI-job finalization consistency risk.

## 15. Recommendation To Director

Recommendation: `FAIL_WITH_PARTIAL_FIX_CONFIRMED`.

Accepted by this report as observed evidence:

- exactly one upload was performed;
- MinerU parse/artifact storage succeeded;
- `progressSemantics` surfaced as a log-unreadable diagnostic on API and task list;
- previous `UND_ERR_HEADERS_TIMEOUT` did not recur.

Not accepted as pass:

- no meaningful page/batch MinerU progress was observed;
- final task state is `failed`;
- AI terminal behavior still needs follow-up;
- this is not production release readiness.

Recommended next routing:

1. DevelopmentEngineer or Architect should inspect the AI finalization path where repair success evidence coexists with terminal failed state.
2. DevelopmentEngineer or ops owner should inspect why the production log source is `log-observation-unreadable` and whether task-page semantics should show this diagnostic as a known limitation or a recoverable ops issue.
