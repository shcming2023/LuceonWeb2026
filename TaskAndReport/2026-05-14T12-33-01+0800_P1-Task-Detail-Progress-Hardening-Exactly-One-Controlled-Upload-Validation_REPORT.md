# Test Acceptance Report: P1 Task Detail Progress Hardening Exactly One Controlled Upload Validation

- Task ID: `TASK-20260514-123301-P1-Task-Detail-Progress-Hardening-Exactly-One-Controlled-Upload-Validation`
- Task brief: `TaskAndReport/2026-05-14T12-33-01+0800_P1-Task-Detail-Progress-Hardening-Exactly-One-Controlled-Upload-Validation_TASK.md`
- Role: `TestAcceptanceEngineer`
- Report time: 2026-05-14T12:50:00+0800
- Workspaces used: development and production
- Entered production deployment path: yes
- Validation level: production controlled UI/runtime validation, exactly one authorized upload

## Required Reading

Completed required reading from the task brief:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/test-acceptance-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- current task brief
- `TaskAndReport/2026-05-14T12-17-02+0800_P1-Task-Detail-Progress-Hardening-Production-Deployment-And-Read-Only-Runtime-Validation_REPORT.md`
- `TaskAndReport/2026-05-14T12-29-44+0800_P1-Task-Detail-Progress-Hardening-Production-Deployment-And-Read-Only-Runtime-Validation_DIRECTOR_REVIEW.md`

## Scope

Validated the deployed task-detail progress hardening through one real production CMS UI upload. The validation focused on:

- task detail `当前进展`;
- list/detail progress parity during MinerU processing;
- browser console behavior, especially dependency-repair status polling;
- canonical MinerU observability endpoints;
- final task/material/AI terminal state.

This report does not claim L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.

## Workspace And HEAD Evidence

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Development branch at start: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- Development HEAD observed earlier in this role thread: `005ca96 Hold Task 108 auto progress on GitHub sync`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Production branch/HEAD: `main...origin/main`, `5ca2615 Accept task detail progress hardening`
- Production worktree had pre-existing dirty files: `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, `src/app/pages/SourceMaterialsPage.tsx`, `src/store/appContext.tsx`.
- Development worktree also had pre-existing shared dirty/untracked files. No unrelated files were reverted.

## Commands And Actions

Commands/actions run:

- Development: `git status --short --branch` - exit 0
- Development: ledger/task/doc reads - exit 0
- Production: `git status --short --branch && git log -1 --oneline` - exit 0
- Production: `docker compose ps` - exit 0
- Production: `curl -sS -o /dev/null -w '%{http_code}\n' http://localhost:8081/cms/` - exit 0, HTTP 200
- Production: `curl -fsS http://localhost:8081/__proxy/upload/health` - exit 0
- Production: `curl -i -sS http://localhost:8081/__proxy/upload/ops/dependency-repair/status` - exit 0
- Production: `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?ollamaChatProbe=true'` - exit 0
- Production: `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit` - exit 0
- Production: `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task` - exit 0
- Production: `curl -fsS http://127.0.0.1:8083/health` - exit 0
- Production: `tmux ls` - exit 0
- Production: `lsof -nP -iTCP:8083 -sTCP:LISTEN` - exit 0
- Production: `lsof -a -p 61436 -d cwd,1,2` - exit 0
- Production: sample `stat` and `shasum -a 256` - exit 0
- Production: first Playwright invocation with plain `node` - exit 1, `Cannot find module 'playwright'`; no browser page, file selection, or upload occurred.
- Production: `npx pnpm@10.4.1 --dir uat exec node ...` Playwright validation - exit 0; exactly one `setInputFiles(...)` call and exactly one upload response.
- Production: terminal task/material/AI/status endpoint reads - exit 0
- Production: one malformed post-validation JSON key-search command exited 1 due shell/stdin invocation error; it was read-only and did not mutate runtime. A corrected task metadata query then exited 0.

## Mandatory Preflight Evidence

Preflight passed before the single upload.

- Docker services healthy: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server`.
- Frontend `/cms/`: HTTP `200`.
- Upload health: `{"ok":true,"service":"upload-server"}`.
- Dependency health with Ollama chat probe:
  - `ok=true`
  - `blocking=false`
  - MinIO OK
  - MinerU health OK
  - Ollama model `qwen3.5:9b` present, resident, and `chatOk=true`
- Admission circuit:
  - `open=false`
  - state `closed`
  - parse pending/running `0/0`
  - AI pending/running `0/0`
- Active-task:
  - no active/current/queued/takeover-required work;
  - three historical AI failure tasks remained listed separately and were not modified.
- Direct MinerU `/health`:
  - `status=healthy`
  - queued `0`
  - processing `0`
  - failed `0`
- `tmux ls` included:
  - `luceon-mineru`
  - `luceon-sidecar`
- Port `8083`:
  - exactly one listener, PID `61436`.
- PID `61436` ownership:
  - cwd `/Users/concm/prod_workspace/Luceon2026`
  - stdout `/Users/concm/ops/logs/mineru-api.log`
  - stderr `/Users/concm/ops/logs/mineru-api.err.log`
- Dependency repair status:
  - HTTP `200 OK`
  - body `{"ok":false,"code":"SUPERVISOR_UNAVAILABLE","message":"宿主机修复代理未启动","command":"bash ops/start-luceon-runtime.sh"}`

## Selected Sample

- Path: `/Users/concm/prod_workspace/Luceon2026/testpdf/走向成功_英语_二模卷16篇.pdf`
- Size: `3457503` bytes
- SHA-256: `b3e00ad1c7f7afff4bdae1b484abad941af618fd80b9b5f9f22d69848968eaac`
- Selection reason: small/medium enough for a controlled single-upload validation, but large enough to expose an in-flight MinerU progress window.
- Sample handling: read-only; not copied, moved, renamed, edited, deleted, truncated, or committed.

## Upload Evidence

Exactly one upload was created through the production CMS task UI.

- Upload count: `1`
- Upload response HTTP status: `200`
- Task ID: `task-1778733717808`
- Material ID: `2820074763593700`
- Object name: `originals/2820074763593700/source.pdf`
- Provider: `minio`
- MIME type: `application/pdf`
- MinerU task ID: `9d5a39b1-d098-40d4-a277-a853433bd006`
- AI job ID: `ai-job-1778733759504-ed73`
- Observation artifact: `/tmp/luceon-task126-observations.json`
- Screenshots: `/tmp/luceon-task126-before-upload.png`, `/tmp/luceon-task126-list-0.png`, `/tmp/luceon-task126-list-1.png`, `/tmp/luceon-task126-list-2.png`, `/tmp/luceon-task126-detail-0.png`, `/tmp/luceon-task126-detail-1.png`, `/tmp/luceon-task126-detail-2.png`, `/tmp/luceon-task126-final-list.png`, `/tmp/luceon-task126-final-detail.png`

## Lifecycle And Final State

Polling captured 39 observations from `2026-05-14T04:41:59.124Z` through `2026-05-14T04:44:48.662Z`.

Observed state sequence:

`pending -> running -> ai-pending -> ai-running -> review-pending`

Final task:

- `id=task-1778733717808`
- `state=review-pending`
- `stage=review`
- `progress=100`
- `message=AI 识别完成: review-pending (待人工复核)`
- `materialId=2820074763593700`
- `updatedAt=2026-05-14T04:44:44.276Z`

Final material:

- `id=2820074763593700`
- `title=走向成功_英语_二模卷16篇`
- `status=reviewing`
- `mineruStatus=completed`
- `aiStatus=analyzed`
- subject `英语`
- tags populated by AI metadata

Parsed/artifact evidence from task metadata:

- `parsedFilesCount=25`
- `markdownObjectName=parsed/2820074763593700/full.md`
- `parsedPrefix=parsed/2820074763593700/`
- `artifactManifestObjectName=parsed/2820074763593700/artifact-manifest.json`
- `zipObjectName=parsed/2820074763593700/mineru-result.zip`

AI evidence:

- AI job `ai-job-1778733759504-ed73`
- AI job state `review-pending`
- provider/model `ollama` / `qwen3.5:9b`
- deterministic repair succeeded
- AI completed at `2026-05-14T04:44:44.275Z`

## UI Progress Semantics

Task detail:

- `当前进展` label appeared in all 39 observations.
- Detail page showed fine-grained MinerU progress in 29 of 39 observations.
- Examples observed in `当前进展`:
  - `MinerU 正在解析：backend=pipeline，相位 页面处理，批次 1/1，页 24/24`
  - `AI: 正在使用 ollama (qwen3.5:9b) 进行识别...`
  - final `AI 识别完成: review-pending (待人工复核)`

Task list:

- List page showed fine-grained MinerU progress in 29 of 39 observations.
- List and detail both showed fine-grained progress in the same 29 observations.
- Examples included `版面识别`, `表格识别`, `模型识别`, `OCR 识别`, `批次 1/1`, and `页 24/24`.

Convergence:

- During AI and terminal phases, list/detail remained understandable.
- Final list showed `待复核` and `状态一致`.
- Final detail showed `当前状态=待复核`, `当前阶段=review`, `已产物=已生成 (Markdown)`, `下一步动作=需人工审核`, and `当前进展` with the final AI review-pending message.

Residual nuance:

- Some early and late observations still displayed `MinerU 正在处理，但日志观测滞后` or terminal `MinerU 已完成，但本次未捕获可归因业务进度日志`.
- This did not block operator understanding in this run because the in-flight detail/list views both captured fine-grained progress for most processing observations and the task reached a coherent terminal state.

## Browser Console Evidence

- Browser console warning/error count: `0`
- Dependency-repair status HTTP 503 count: `0`
- Generic HTTP 503 count captured by Playwright response events: `0`
- Observed dependency-repair status events were HTTP `200` only, with structured `SUPERVISOR_UNAVAILABLE`.

This validates the Task 123/124 browser-noise hardening for the dependency-repair status polling path in this controlled upload run.

## Endpoint Evidence During And After Processing

During processing:

- `global-observation` provided fresh attributable progress for `task-1778733717808` in 35 observations.
- Representative progress messages:
  - `MinerU 正在解析：backend=pipeline，相位 页面处理，批次 1/1，页 1/1`
  - `MinerU 正在解析：backend=pipeline，相位 版面识别，批次 1/1，页 24/24`
  - `MinerU 正在解析：backend=pipeline，相位 表格识别，批次 1/1，页 24/24`
  - `MinerU 正在解析：backend=pipeline，相位 模型识别，批次 1/1，页 24/24`
  - `MinerU 正在解析：backend=pipeline，相位 OCR 识别，批次 1/1，页 24/24`
- `log-channel-ownership` selected configured source `MINERU_ERR_LOG_PATH:mineru-api.err.log`.
- `dependency-repair/status` remained HTTP 200 with code `SUPERVISOR_UNAVAILABLE`.

Terminal:

- Admission circuit remained closed; active counts `0`; `activeTaskClean=true`.
- Active-task route showed no active/current/queued/drift/takeover tasks; only historical AI failures remained listed.
- Direct MinerU `/health` after terminal: `healthy`, queued `0`, processing `0`, failed `0`, completed `5`.
- Terminal `log-channel-ownership` summary was `stale`, expected after the parse completed; sidecar remained `observed-recent`.
- Terminal `global-observation` remained attributed to `task-1778733717808` with completed-window backfill and page/batch semantics, but freshness was stale because the task had already reached terminal state.

## Acceptance Judgment

Recommendation: `pass`.

Pass evidence:

- Preflight passed.
- Exactly one UI upload was created.
- No forbidden mutation or second upload occurred.
- Task reached coherent `review-pending`.
- Material reached `reviewing`, MinerU completed, AI analyzed, and parsed artifacts were present.
- Task detail label `当前进展` was present in every observation.
- Task detail and task list both showed fine-grained MinerU progress during real processing, with matched list/detail fine-progress observations.
- Browser console stayed clean for this validation: no warning/error events and no dependency-repair HTTP 503.
- Canonical observability endpoints captured fresh, attributable, real-upload progress during processing.

Residual risks:

- A subset of early/late observations still used stale/terminal diagnostic wording around MinerU progress. This looks acceptable for this task because the deployed hardening did produce fine-grained `当前进展` during the real processing window, and final lifecycle state was coherent.
- Historical AI failures remain listed by `active-task`, unchanged and non-blocking.
- Production worktree remains dirty with pre-existing local files unrelated to this validation.

## Skipped Checks

- No pressure, batch, soak, long-run, or concurrent validation: forbidden by task brief.
- No second upload: forbidden by task brief.
- No failed-task repair, reparse, or re-AI: forbidden by task brief.
- No cleanup or deletion of historical tasks/materials/files: forbidden by task brief.
- No direct DB/MinIO mutation: forbidden by task brief.
- No `docker compose down`, `docker compose down -v`, or Docker volume/data cleanup: forbidden by task brief.
- No MinerU/Ollama/supervisor start/stop/restart/kill/attach/mutation: forbidden by task brief.
- No model pull/delete/replace, config/secret/sample mutation, PRD truth change, role contract change, project state change, or handoff change: forbidden by task brief.
- No L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线 claim: forbidden by task brief.

## Director Decision Needed

Director should review whether to accept this as closing Task 126. My recommendation is `pass`, with the residual stale/terminal diagnostic wording recorded as non-blocking follow-up polish if Director wants tighter copy semantics.
