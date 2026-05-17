# P0 Large-PDF Soak Validation Report

Author: Lucode
Report time: 2026-05-08T14:44:54+0800
Based on Lucia task brief: `TaskAndReport/2026-05-08T14-24-33+0800_P0-Large-PDF-Soak-Validation_TASK.md`

## Decision

FAIL.

The large-PDF soak reached a terminal `failed` state at the AI metadata stage. MinerU parsing completed successfully, MinIO parsed artifacts were written, and strict AI no-skeleton semantics were preserved. The terminal failure was an Ollama `qwen3.5:9b` provider timeout after about 300 seconds.

Production release readiness remains unclaimed.

## Branch And Runtime Baseline

- Development workspace branch before report commit: `main`
- Development workspace HEAD before report commit: `b7c1892 docs: record local sample library policy`
- Production workspace branch/status: `main...origin/main [behind 2]`, local `M docker-compose.override.yml`
- Production workspace HEAD: `4cc6d3e docs: accept observation semantics and assign deployment validation`
- Production manual-review URL: `http://localhost:8081/cms/`

Production override pre-check confirmed:

```yaml
services:
  upload-server:
    environment:
      - DISABLE_AI_SKELETON_FALLBACK=true
      - OLLAMA_TIER2_MODEL=qwen3.5:9b

  minio:
    ports:
      - "127.0.0.1:19001:9001"
```

Effective compose config included:

```text
host_ip: 127.0.0.1
target: 9001
published: "19001"
DISABLE_AI_SKELETON_FALLBACK: "true"
OLLAMA_TIER2_MODEL: qwen3.5:9b
```

## Test File

- Path: `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
- Size: `15157403` bytes
- SHA-256: `672c96f6125ab3afcf0dcd63b858a2584fa4cdd427000df40870f52aa477435b`
- Selection reason: Lucia listed `G7_Workbook_ready_to_print.pdf` as the preferred previously used large sample. It is a representative educational workbook PDF and has already exposed large-PDF Phase 1 behavior in prior manual-review evidence.

## Pre-Checks

Development sync:

```text
git status --short --branch -> ## main...origin/main
git fetch origin -> exit 0
git pull --ff-only origin main -> Already up to date
```

Production containers:

```text
cms-db-server       Up (healthy)
cms-frontend        Up (healthy) 0.0.0.0:8081->80/tcp
cms-minio           Up (healthy) 127.0.0.1:19001->9001/tcp
cms-upload-server   Up (healthy)
```

No active parse / AI work before upload:

```text
tasks.rows=43
tasks.states={"completed":1,"failed":8,"review-pending":34}
active.count=0
```

Dependency health before upload:

```text
status=200 durationMs=817 blocking=false
minio.ok=true
mineru.ok=true
mineru.healthOk=true submit.enabled=true submit.ok=true submit.status=202 submit.taskId=4da1118f-4f0b-4484-9051-86fcac77d8c7
ollama.ok=true
```

CMS reachability before upload:

```text
cms_url=http://localhost:8081/cms/ http_code=200 exit=0
```

## Upload Path

Path used: production upload API.

Reason UI path was not used: this session did not expose a reliable browser automation tool with `setInputFiles`-style control for the hidden upload file input. The available generic app-control tool would require operating the system file picker and was less reproducible for this evidence task. The API path is the same production upload endpoint behind the CMS proxy and is explicitly allowed by the task brief when browser automation is blocked.

Upload command created one controlled validation task:

```text
UPLOAD_START_ISO=2026-05-08T06:33:46Z
MATERIAL_ID=mat-lucode-large-soak-20260508143346
HTTP_CODE=200
taskId=task-1778222027064
objectName=originals/mat-lucode-large-soak-20260508143346/source.pdf
provider=minio
```

## State Transitions

Observed task ID: `task-1778222027064`
Material ID: `mat-lucode-large-soak-20260508143346`

Key transitions:

```text
2026-05-08T06:34:08.998Z elapsed=0s   state=running    stage=mineru-processing progress=50 message=MinerU 正在解析
2026-05-08T06:38:29.310Z elapsed=260s state=ai-pending stage=complete          progress=100 message=MinerU 解析完成，产物已落库，等待 AI 元数据识别
2026-05-08T06:38:39.332Z elapsed=270s state=ai-running stage=ai                progress=100 message=AI: 正在使用 ollama (qwen3.5:9b) 进行识别...
2026-05-08T06:43:39.756Z elapsed=571s state=failed     stage=ai                progress=100 message=AI 识别完成: failed
```

Wall-clock duration from upload start to terminal state:

- Upload start: `2026-05-08T06:33:46Z`
- Terminal state observed: `2026-05-08T06:43:39.756Z`
- Approximate elapsed: 594 seconds from upload start, 571 seconds from poll start.

## Terminal DB Evidence

Task summary:

```text
id=task-1778222027064
materialId=mat-lucode-large-soak-20260508143346
state=failed
stage=ai
progress=100
message=AI 识别完成: failed
createdAt=2026-05-08T06:33:47.212Z
updatedAt=2026-05-08T06:43:32.614Z
completedAt=2026-05-08T06:43:32.613Z
parsedPrefix=parsed/mat-lucode-large-soak-20260508143346/
markdownObjectName=parsed/mat-lucode-large-soak-20260508143346/full.md
artifactManifestObjectName=parsed/mat-lucode-large-soak-20260508143346/artifact-manifest.json
parsedFilesCount=99
artifactIncomplete=false
artifactStorageMode=zip-source
aiJobId=ai-job-1778222304130-c204
```

Material summary:

```text
id=mat-lucode-large-soak-20260508143346
status=failed
mineruStatus=completed
aiStatus=failed
fileName=G7_Workbook_ready_to_print.pdf
fileSize=15157403
objectName=originals/mat-lucode-large-soak-20260508143346/source.pdf
processingStage=ai
processingMsg=AI 识别失败
```

Post-terminal task table:

```text
tasks.rows=44
tasks.states={"completed":1,"failed":9,"review-pending":34}
soak.task=task-1778222027064 state=failed stage=ai materialId=mat-lucode-large-soak-20260508143346
```

## Artifact Evidence

Original source object read-only evidence:

```text
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Length: 15157403
Content-Disposition: inline; filename="source.pdf"; filename*=UTF-8''source.pdf
Accept-Ranges: bytes
```

Parsed object listing under `parsed/mat-lucode-large-soak-20260508143346/`:

```text
total=3
artifact-manifest.json size=43797
full.md size=105254
mineru-result.zip size=18206930
```

Artifact manifest read-only evidence:

```text
version=artifact-manifest.v0.1
materialId=mat-lucode-large-soak-20260508143346
artifactCount=99
artifactStorageMode=zip-source
first artifacts:
- mineru-result.zip size=18206930 mimeType=application/zip
- G7_Workbook_ready_to_print/ocr/G7_Workbook_ready_to_print.md size=105254 mimeType=text/markdown; charset=utf-8
- G7_Workbook_ready_to_print/ocr/G7_Workbook_ready_to_print_middle.json size=5020080 mimeType=application/json; charset=utf-8
- G7_Workbook_ready_to_print/ocr/G7_Workbook_ready_to_print_model.json size=1035161 mimeType=application/json; charset=utf-8
- G7_Workbook_ready_to_print/ocr/G7_Workbook_ready_to_print_content_list.json size=284505 mimeType=application/json; charset=utf-8
```

MinerU observation evidence:

```text
task.metadata.mineruObservedProgress:
observer=host-mineru-log-observer
phase=Processing pages
percent=100
current=90
total=90
rawLine="Processing pages: 100%|...| 90/90 [00:10<00:00,  8.97it/s]"
attribution=task-1778222027064
attributionMode=completed-window-backfill
logSourcePath=/Users/concm/ops/logs/mineru-api.err.log
logSourceContext=host-filesystem
```

## AI Failure Evidence

AI events:

```text
2026-05-08T06:38:32.581Z ai-content-truncated:
Markdown 内容过长已按策略抽样截断 (104823 -> 78084 字符)

2026-05-08T06:38:32.582Z ai-provider-request-started:
正在使用 ollama (qwen3.5:9b) 进行识别...

2026-05-08T06:43:32.606Z ai-provider-request-failed:
AI Provider 调用失败: Ollama Provider Error: [TimeoutError] The operation was aborted due to timeout (BaseURL: http://host.docker.internal:11434, Model: qwen3.5:9b, Duration: 300014ms, Timeout: 300000ms)

2026-05-08T06:43:32.610Z ai-provider-failed:
AI 识别异常: [AI 严格模式拦截] 不允许降级到骨架模型: AI Provider 调用全部失败: Ollama Provider Error: [TimeoutError] The operation was aborted due to timeout (BaseURL: http://host.docker.internal:11434, Model: qwen3.5:9b, Duration: 300014ms, Timeout: 300000ms)；严格模式禁止骨架兜底
```

Upload-server logs:

```text
[task-worker] Picked up task: task-1778222027064 (local-mineru)
[task-worker] Wrote artifact manifest: parsed/mat-lucode-large-soak-20260508143346/artifact-manifest.json (99 items, 42.8 KB)
[metadata-job-client] Created AI Metadata Job: ai-job-1778222304130-c204 for parseTask=task-1778222027064
[ai-worker] Picking up job: ai-job-1778222304130-c204 (parseTask=task-1778222027064)
[ai-worker] Provider ollama failed: Ollama Provider Error: [TimeoutError] The operation was aborted due to timeout (BaseURL: http://host.docker.internal:11434, Model: qwen3.5:9b, Duration: 300014ms, Timeout: 300000ms)
[ai-worker] Job ai-job-1778222304130-c204 failed after attempts: Ollama Provider Error: [TimeoutError] The operation was aborted due to timeout (BaseURL: http://host.docker.internal:11434, Model: qwen3.5:9b, Duration: 300014ms, Timeout: 300000ms)
[ai-worker] Job ai-job-1778222304130-c204 unexpected error: [AI 严格模式拦截] 不允许降级到骨架模型: AI Provider 调用全部失败 ... 严格模式禁止骨架兜底
```

AI classification provider evidence:

- No `aiClassificationProvider=skeleton` was recorded as a successful result.
- Strict mode blocked skeleton fallback and moved the task/material to explicit AI failure.

## Post-Terminal Health Evidence

Dependency health after terminal state:

```text
status=200 durationMs=1009 blocking=false
minio.ok=true
mineru.ok=true
mineru.healthOk=true submit.enabled=true submit.ok=true submit.status=202 submit.taskId=6cb570c5-8e20-4185-9946-1af9ec507b57
ollama.ok=true
```

CMS reachability after terminal state:

```text
cms_url=http://localhost:8081/cms/ http_code=200 exit=0
```

Dependency repair / ops status:

```text
ok=true
message=Supervisor running
sessions.sidecar=true
services.mineruReachable=true
services.ollamaReachable=true
ownership.ollama.warning=Ollama service reachable but not managed by luceon-ollama tmux session
```

## Classification

The failure is product/runtime-capacity related in the AI metadata stage:

- Not a MinerU submit-path failure: MinerU accepted work, completed parsing, and produced a 99-entry artifact manifest.
- Not a MinIO storage failure: raw source, `full.md`, `mineru-result.zip`, and `artifact-manifest.json` are readable.
- Not a dependency-health outage at the check level: post-terminal dependency-health is non-blocking and reports `ollama.ok=true`.
- It is an Ollama provider execution timeout under the current 300000 ms provider timeout for a large parsed Markdown input.

## Commands Run

- `git status --short --branch` in dev: exit 0
- `git fetch origin`: exit 0
- `git pull --ff-only origin main`: exit 0
- `rg` task-list scan: exit 0, found task 29
- Required reading via `sed` / `rg`: exit 0
- `git status --short --branch && git log -1 --oneline` in production: exit 0
- `sed -n '1,80p' docker-compose.override.yml` in production: exit 0
- `docker compose ps`: exit 0
- Broad `find` for preferred sample: stopped after finding preferred sample; output included `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
- Exact active-work pre-check: exit 0, active count 0
- Pre-upload dependency-health with submit probe: exit 0, `blocking=false`
- Pre-upload CMS reachability: exit 0, HTTP 200
- `docker compose config | rg ...`: exit 0
- `stat` / `shasum -a 256` for test PDF: exit 0
- Upload API `curl -F file=@... http://localhost:8081/__proxy/upload/tasks`: exit 0, HTTP 200
- Polling script for task state: exit 0, terminal `failed` after 571 seconds from poll start
- DB task/material/events/AI-job evidence script: exit 0
- MinIO parsed listing script: exit 0
- Original object `proxy-file` HEAD: exit 0
- Artifact manifest read: exit 0
- Upload-server log extraction: exit 0
- Post-terminal dependency-health with submit probe: exit 0, `blocking=false`
- Post-terminal CMS reachability: exit 0, HTTP 200
- `/ops/mineru/global-observation`: exit 0
- `/ops/dependency-repair/status`: exit 0
- Post-terminal task table read: exit 0

## Skipped Checks

- UI upload path was skipped because reliable browser file-input automation was not available in this session. The API upload fallback was used and labeled.

No task-required runtime health, DB, artifact, or log evidence check was skipped.

## Artifact Preservation And Forbidden Operations

Created validation artifacts are intentionally preserved:

- DB task: `task-1778222027064`
- DB material: `mat-lucode-large-soak-20260508143346`
- Raw object: `originals/mat-lucode-large-soak-20260508143346/source.pdf`
- Parsed prefix: `parsed/mat-lucode-large-soak-20260508143346/`
- Parsed objects: `full.md`, `mineru-result.zip`, `artifact-manifest.json`
- AI job: `ai-job-1778222304130-c204`
- Task events: `150`

Confirmed not performed:

- No DB row deletion.
- No MinIO object deletion.
- No Docker volume deletion or pruning.
- No secret change.
- No broad deploy, rebuild, rollback, or production sync.
- No production configuration change.
- No production release-readiness claim.
- No validation artifact cleanup.

## Risks / Residual Debt

- Large-PDF Phase 1 chain currently fails at AI metadata recognition for this preferred sample due to Ollama `qwen3.5:9b` timeout.
- Dependency-health `ollama.ok=true` proves reachability, not enough execution capacity for large parsed inputs.
- The AI job record itself did not retain provider/model fields, but task events and upload-server logs explicitly show `ollama (qwen3.5:9b)` and the 300000 ms timeout.
- MinerU global observation after the task showed a later unattributed observation, while the task metadata contains completed-window backfill attribution for this task. This is not the terminal failure cause but remains an observability nuance for Lucia review.
- Lucia review is required before deciding the next task, likely AI large-input timeout/capacity handling or validation-scope adjustment.

