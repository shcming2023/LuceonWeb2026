# Test Acceptance Report: P1 Post MinerU Ownership Normalization Exactly One Controlled Upload Validation

- Task ID: `TASK-20260514-113727-P1-Post-MinerU-Ownership-Normalization-Exactly-One-Controlled-Upload-Validation`
- Task brief: `TaskAndReport/2026-05-14T11-37-27+0800_P1-Post-MinerU-Ownership-Normalization-Exactly-One-Controlled-Upload-Validation_TASK.md`
- Role: `TestAcceptanceEngineer`
- Report time: 2026-05-14T12:00:00+0800
- Workspaces used: development and production
- Entered production deployment path: yes, read-only runtime validation plus exactly one authorized UI upload

## Scope

Executed the Director-authorized Option A validation: one and only one controlled small/medium PDF upload through the production CMS task UI, with strict preflight and canonical MinerU observability checks.

This report does not declare production readiness, L3 readiness, release readiness, pressure PASS, or go-live readiness.

## Workspace And HEAD Evidence

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Development branch/HEAD: `development-engineer/p0-post-validation-ollama-mineru-blockers`, `005ca96 Hold Task 108 auto progress on GitHub sync`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Production branch/HEAD: `main...origin/main`, `fb2627c Dispatch post-MinerU ownership upload validation`
- Both worktrees had pre-existing dirty/untracked files. No unrelated files were reverted.

## Commands And Actions

All commands below exited `0` unless noted.

- Development: `git status --short --branch`
- Production: `git status --short --branch && git log -1 --oneline`
- Production: `docker compose ps`
- Production: `tmux ls`
- Production: `lsof -nP -iTCP:8083 -sTCP:LISTEN`
- Production: `ps -p 61436 -o pid=,ppid=,command=`
- Production: `lsof -p 61436 -a -d cwd,1,2 -Fn`
- Production: `curl -fsS http://127.0.0.1:8083/health`
- Production: `curl -fsS http://localhost:8081/__proxy/upload/health`
- Production: `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?ollamaChatProbe=true'`
- Production: `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit`
- Production: `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task`
- Production: `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership`
- Production: `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/global-observation`
- Production UI action: Playwright opened `http://localhost:8081/cms/tasks`, selected the hidden attached input `data-testid=task-upload-file-input`, and called `setInputFiles(...)` exactly once.
- One preliminary Playwright locator attempt exited `1` because it waited for the hidden upload input to become visible. It did not set a file, did not call the upload endpoint, and did not create a task.

## Mandatory Preflight Result

Preflight passed before upload.

- Docker services were healthy: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server`.
- `tmux ls` showed both `luceon-mineru` and `luceon-sidecar`.
- Port `8083` had exactly one listener: PID `61436`.
- PID `61436` command: `/Users/concm/miniconda3/envs/mineru/bin/python3.10 ... mineru-api --host 0.0.0.0 --port 8083`.
- PID `61436` cwd: `/Users/concm/prod_workspace/Luceon2026`.
- PID `61436` stdout/stderr: `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log`.
- MinerU `/health`: `healthy`, queued `0`, processing `0`, failed `0`.
- Upload health: `{"ok":true,"service":"upload-server"}`.
- Dependency health: `ok=true`, `blocking=false`; Ollama `qwen3.5:9b` reachable, resident, and chat probe OK.
- Admission circuit: `state=closed`, `open=false`, parse/AI active counts `0`.
- Active task: no active/current/queued/drift/takeover tasks.
- Canonical log-channel and global-observation routes were reachable.
- Sample directory existed and contained PDFs.

## Selected Sample

- Path: `/Users/concm/prod_workspace/Luceon2026/testpdf/走向成功_英语_二模卷16篇.pdf`
- Size: `3457503` bytes
- SHA-256: `b3e00ad1c7f7afff4bdae1b484abad941af618fd80b9b5f9f22d69848968eaac`
- Sample handling: read-only; not copied, moved, renamed, edited, deleted, or committed.

## Upload Evidence

Exactly one upload was created through the production CMS task UI.

- Upload response: `ok=true`, HTTP `200`
- Task ID: `task-1778730187749`
- Material ID: `4282929344122708`
- Object name: `originals/4282929344122708/source.pdf`
- Provider: `minio`
- MIME type: `application/pdf`
- MinerU task ID: `fb5c5774-534c-4a7c-bc7a-d5546857cd1a`
- AI job ID: `ai-job-1778730259599-2d2f`
- Observation artifact: `/tmp/luceon-task122-observations.json`
- Screenshot artifacts: `/tmp/luceon-task122-before-upload.png`, `/tmp/luceon-task122-list-0.png`, `/tmp/luceon-task122-list-1.png`, `/tmp/luceon-task122-list-2.png`, `/tmp/luceon-task122-detail-0.png`, `/tmp/luceon-task122-detail-1.png`, `/tmp/luceon-task122-detail-2.png`, `/tmp/luceon-task122-final-list.png`, `/tmp/luceon-task122-final-detail.png`

## Observed Lifecycle

Polling captured 53 observations from 2026-05-14T03:43:09.990Z through 2026-05-14T03:49:18.476Z.

- First observed task state: `pending`, stage `upload`, progress `0`, message `任务已创建待处理`.
- Observed state sequence: `pending -> running -> ai-pending -> ai-running -> review-pending`.
- Final task state: `review-pending`, stage `review`, progress `100`, message `AI 识别完成: review-pending (待人工复核)`.
- Final material state: `status=reviewing`, `mineruStatus=completed`, `aiStatus=analyzed`.
- Parsed artifact count: `25`.
- Material metadata was populated, including subject `英语` and AI-generated tags.

Final DB task evidence:

- `id=task-1778730187749`
- `state=review-pending`
- `stage=review`
- `progress=100`
- `message=AI 识别完成: review-pending (待人工复核)`
- `materialId=4282929344122708`
- `aiJobId=ai-job-1778730259599-2d2f`
- `updatedAt=2026-05-14T03:49:16.406Z`

## UI Semantics

Task list page:

- During MinerU processing, the list page showed understandable lifecycle state (`LOCAL-MINERU`, `流转中`, `50%`) and intermittently surfaced fresh MinerU progress text.
- Captured list messages included real page/batch/phase semantics such as `批次 1/1，页 24/24`, `表格识别`, `模型识别`, `OCR 检测`, and `OCR 识别`.
- During AI, the list page showed `AI 元数据识别中`, then final `待复核` and `状态一致`.

Task detail page:

- The detail page showed understandable high-level lifecycle state: `解析中`, then `AI 分析中`, then final `待复核`.
- The detail page did not display the fine-grained fresh MinerU page/batch/phase progress captured by the canonical global observation endpoint. In the 53-poll capture, detail fine-grained progress poll count was `0`.
- Final detail page was coherent: `当前状态=待复核`, `当前阶段=review`, `已产物=已生成 (Markdown)`, `下一步动作=需人工审核`.

Browser console:

- Playwright captured 111 console messages, including 109 repeated `503 Service Unavailable` resource errors and initial `[db-sync]` failed warnings.
- These console messages did not prevent the upload from completing to `review-pending`, but they are residual runtime/UI noise for Director review.

## Observability Endpoint Evidence

During processing:

- `global-observation` captured fresh attributable progress for the real upload. Summary count: 27 fresh global observations, 26 attributed to `task-1778730187749`.
- Task-specific observed progress was fresh in 20 polls.
- Representative progress messages:
  - `MinerU 正在解析：backend=pipeline，相位 页面处理，批次 1/1，页 1/1`
  - `MinerU 正在解析：backend=pipeline，批次 1/1，页 24/24`
  - `MinerU 正在解析：backend=pipeline，相位 Fetching 1 files，批次 1/1，页 24/24`
  - `MinerU 正在解析：backend=pipeline，相位 表格识别，批次 1/1，页 24/24`
  - `MinerU 正在解析：backend=pipeline，相位 模型识别，批次 1/1，页 24/24`
  - `MinerU 正在解析：backend=pipeline，相位 OCR 检测，批次 1/1，页 24/24`
  - `MinerU 正在解析：backend=pipeline，相位 OCR 识别，批次 1/1，页 24/24`

After terminal state:

- Admission circuit remained closed, active counts `0`, `activeTaskClean=true`.
- Active-task route showed no active/current/queued/drift/takeover tasks.
- MinerU `/health` showed queued `0`, processing `0`, completed `3`, failed `0`.
- `log-channel-ownership` was reachable, with selected configured source `MINERU_ERR_LOG_PATH:mineru-api.err.log`; terminal-time summary was `stale`, with sidecar `observed-recent`.
- `global-observation` at terminal time was stale/unattributed because MinerU processing had already completed and the log was no longer updating. This is acceptable as terminal evidence but should not be confused with in-flight progress evidence.

## Acceptance Judgment

Recommendation: `pass with residual risks`.

Pass evidence:

- Exactly one upload was created.
- No forbidden mutation or second upload occurred.
- The task reached coherent `review-pending`.
- MinerU completed, AI analyzed, parsed artifacts were present, and material entered reviewing.
- Canonical configured-log observability captured fresh, attributable, real-upload MinerU progress during processing with page/batch/phase semantics.
- Post-run runtime was nonblocking: admission closed, no active parse/AI work, MinerU healthy.

Residual risks:

- Task detail page did not surface fine-grained page/batch/phase progress during MinerU processing, even though the list page and canonical endpoints did.
- During and after the AI phase, UI/list messages fell back to `MinerU 已完成，但本次未捕获可归因业务进度日志`; this is understandable after MinerU terminal state, but may look pessimistic beside the captured in-flight endpoint evidence.
- Browser console had repeated `503 Service Unavailable` resource errors and initial db-sync warnings. They did not block this validation but deserve Director triage if they affect operator trust.

## Skipped Checks

- No pressure, batch, soak, or long-run validation: forbidden by task brief.
- No second upload: forbidden by task brief.
- No cleanup, repair, reparse, or re-AI: forbidden by task brief.
- No direct DB or MinIO mutation: forbidden by task brief.
- No Docker down/down-v, volume cleanup, or data cleanup: forbidden by task brief.
- No MinerU/Ollama/supervisor mutation: forbidden by task brief.
- No source code, PRD, role contract, project state, handoff, secret, config, sample, model, or log-file mutation: forbidden by task brief.
- No readiness, L3, pressure PASS, release readiness, go-live, or production上线 claim: forbidden by task brief.

## Director Decision Needed

Director should decide whether to accept this as closing the post-ownership-normalization one-upload validation, with the residual detail-page progress display and console `503` noise recorded as follow-up debt.
