# Test Acceptance Report: P1 Small Serial Validation After Task Detail Progress Pass

- Task ID: `TASK-20260514-125814-P1-Small-Serial-Validation-After-Task-Detail-Progress-Pass`
- Task brief: `TaskAndReport/2026-05-14T12-58-14+0800_P1-Small-Serial-Validation-After-Task-Detail-Progress-Pass_TASK.md`
- Role: `TestAcceptanceEngineer`
- Report time: 2026-05-14T13:16:00+0800
- Workspaces used: development and production
- Entered production deployment path: yes
- Validation level: production small serial UI/runtime validation

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
- `TaskAndReport/2026-05-14T12-33-01+0800_P1-Task-Detail-Progress-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`
- `TaskAndReport/2026-05-14T12-54-36+0800_P1-Task-Detail-Progress-Hardening-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`

## Scope

Ran the user-approved Option A small serial validation:

- maximum allowed uploads: `3`
- actual uploads: `3`
- mode: strictly serial; each task reached terminal state and runtime returned clean before the next upload
- no concurrent upload, pressure, batch-concurrent, soak, L3, release-readiness, or go-live validation

## Workspace And HEAD Evidence

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Development branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Production branch/HEAD: `main...origin/main`, `5ca2615 Accept task detail progress hardening`
- Production worktree had pre-existing dirty files: `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, `src/app/pages/SourceMaterialsPage.tsx`, `src/store/appContext.tsx`.
- No unrelated files were reverted.

## Commands And Actions

Commands/actions run:

- Development: `git status --short --branch` - exit 0
- Development: ledger/task/report/doc reads - exit 0
- Production: `git status --short --branch && git log -1 --oneline` - exit 0
- Production: `docker compose ps` - exit 0
- Production: frontend `/cms/` HTTP check - exit 0, HTTP `200`
- Production: upload health - exit 0
- Production: dependency-repair status - exit 0, HTTP `200`
- Production: dependency-health with Ollama chat probe - exit 0
- Production: admission circuit - exit 0
- Production: active-task - exit 0
- Production: direct MinerU `/health` - exit 0
- Production: `tmux ls` - exit 0
- Production: `lsof -nP -iTCP:8083 -sTCP:LISTEN` - exit 0
- Production: `lsof -a -p 61436 -d cwd,1,2` - exit 0
- Production: sample `stat` and `shasum -a 256` - exit 0
- Production: serial Playwright validation via `npx pnpm@10.4.1 --dir uat exec node ...` - exit 0
- Production: post-run task/material/AI/runtime endpoint reads - exit 0

## Global Preflight Evidence

Preflight passed before the first upload:

- Docker services healthy: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server`.
- Frontend `/cms/`: HTTP `200`.
- Upload health: `{"ok":true,"service":"upload-server"}`.
- Dependency-health:
  - `ok=true`
  - `blocking=false`
  - MinIO OK
  - MinerU health OK
  - Ollama `qwen3.5:9b` present, resident, and `chatOk=true`
- Admission circuit:
  - `open=false`
  - state `closed`
  - parse/AI pending/running `0/0`
- Active-task:
  - no active/current/queued/takeover-required work;
  - only historical AI failures listed separately.
- Direct MinerU:
  - `status=healthy`
  - queued `0`
  - processing `0`
  - failed `0`
- `tmux ls`: `luceon-mineru` and `luceon-sidecar`.
- Port `8083`: exactly one listener, PID `61436`.
- PID `61436`:
  - cwd `/Users/concm/prod_workspace/Luceon2026`
  - stdout `/Users/concm/ops/logs/mineru-api.log`
  - stderr `/Users/concm/ops/logs/mineru-api.err.log`
- Dependency-repair status:
  - HTTP `200`
  - structured `SUPERVISOR_UNAVAILABLE`.

## Sample Selection

Selected three PDFs from `/Users/concm/prod_workspace/Luceon2026/testpdf`, all distinct from Task 126 sample.

| Label | Path | Size | SHA-256 | Suitability |
| --- | --- | ---: | --- | --- |
| s1 | `/Users/concm/prod_workspace/Luceon2026/testpdf/PDF document-4F18-A8A3-62-0.pdf` | `711046` | `bb491c5782c001a60e9af1c8d531cbf3ce9807f0db341af765c31cc2d75e56f4` | Small enough for serial validation; enough pages to expose some progress window. |
| s2 | `/Users/concm/prod_workspace/Luceon2026/testpdf/期末质量分析及建议（曹云童 ）.pdf` | `1041695` | `c2b15ff6cfdd13e7c7cad7ea898bcd0ad98d33b6afde7c3d3e55773916b256e8` | Small/medium local document; useful variety beyond English worksheet/test PDF. |
| s3 | `/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf` | `530205` | `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb` | Small known sample; useful for comparing against earlier validation history. |

Sample handling: read-only. No sample was copied, moved, renamed, edited, deleted, truncated, or committed.

## Per-Upload Results

### s1

- File: `PDF document-4F18-A8A3-62-0.pdf`
- Upload status: HTTP `200`
- Task ID: `task-1778735078407`
- Material ID: `3919509266864708`
- MinerU task ID: `e9cffc28-a916-45e8-9c14-371ca3971ffe`
- AI job ID: `ai-job-1778735097861-642b`
- Observations: `29`
- State sequence: `pending -> running -> ai-pending -> ai-running -> review-pending`
- Final task: `review-pending`, stage `review`, progress `100`
- Final material: `reviewing`, `mineruStatus=completed`, `aiStatus=analyzed`
- Parsed files: `9`
- AI provider/model: `ollama` / `qwen3.5:9b`
- Detail `当前进展`: `29/29`
- Detail fine progress: `23/29`
- List fine progress: `23/29`
- Both list/detail fine progress: `23/29`
- Fresh attributable global progress: `26`
- Dependency-repair 503: `0`
- Generic 503: `0`
- Browser warning/error: `0`
- Runtime clean after terminal: yes

Representative progress:

- `MinerU 正在解析：backend=pipeline，相位 页面处理，批次 1/1，页 1/1`
- `MinerU 正在解析：backend=pipeline，相位 版面识别，批次 1/1，页 1/1`
- `MinerU 正在解析：backend=pipeline，相位 OCR 检测，批次 1/1，页 1/1`

### s2

- File: `期末质量分析及建议（曹云童 ）.pdf`
- Upload status: HTTP `200`
- Task ID: `task-1778735173585`
- Material ID: `3487422674907588`
- MinerU task ID: `1598736f-d865-4b31-8c6d-d6b156cc8c2f`
- AI job ID: `ai-job-1778735204757-96cd`
- Observations: `44`
- State sequence: `pending -> running -> ai-pending -> ai-running -> review-pending`
- Final task: `review-pending`, stage `review`, progress `100`
- Final material: `reviewing`, `mineruStatus=completed`, `aiStatus=analyzed`
- Parsed files: `21`
- AI provider/model: `ollama` / `qwen3.5:9b`
- Detail `当前进展`: `44/44`
- Detail fine progress: `3/44`
- List fine progress: `3/44`
- Both list/detail fine progress: `3/44`
- Fresh attributable global progress: `8`
- Dependency-repair 503: `0`
- Generic 503: `0`
- Browser warning/error: `6`
- Runtime clean after terminal: yes

Representative progress:

- `MinerU 正在解析：backend=pipeline，相位 版面识别，批次 1/1，页 6/6`
- `MinerU 正在解析：backend=pipeline，相位 表格识别，批次 1/1，页 6/6`
- `MinerU 正在解析：backend=pipeline，相位 模型识别，批次 1/1，页 6/6`
- `MinerU 正在解析：backend=pipeline，相位 OCR 检测，批次 1/1，页 6/6`

Browser warning/error details:

- 6 warnings, all `[db-sync] PUT ... failed: Failed to fetch`.
- Affected routes included `/settings/mineruConfig`, `/settings/minioConfig`, `/settings/aiConfig`, and `/secrets`.
- No dependency-repair HTTP 503 was observed.

### s3

- File: `2025_2026学年春季课程中数G8_提取.pdf`
- Upload status: HTTP `200`
- Task ID: `task-1778735316270`
- Material ID: `2192186025491300`
- MinerU task ID: `39a1a119-799f-4321-8abd-f1de7be4a136`
- AI job ID: `ai-job-1778735332632-76c8`
- Observations: `28`
- State sequence: `pending -> running -> ai-pending -> ai-running -> review-pending`
- Final task: `review-pending`, stage `review`, progress `100`
- Final material: `reviewing`, `mineruStatus=completed`, `aiStatus=analyzed`
- Parsed files: `21`
- AI provider/model: `ollama` / `qwen3.5:9b`
- Detail `当前进展`: `28/28`
- Detail fine progress: `1/28`
- List fine progress: `2/28`
- Both list/detail fine progress: `1/28`
- Fresh attributable global progress: `5`
- Dependency-repair 503: `0`
- Generic 503: `0`
- Browser warning/error: `6`
- Runtime clean after terminal: yes

Representative progress:

- `MinerU 正在解析：backend=pipeline，相位 页面处理，批次 1/1，页 6/6`
- `MinerU 正在解析：backend=pipeline，相位 公式/版面模型识别，批次 1/1，页 3/3`
- `MinerU 正在解析：backend=pipeline，相位 OCR 检测，批次 1/1，页 3/3`
- `MinerU 正在解析：backend=pipeline，相位 OCR 识别，批次 1/1，页 3/3`

Browser warning/error details:

- 6 warnings, all `[db-sync] PUT ... failed: Failed to fetch`.
- Affected routes included `/settings/mineruConfig`, `/settings/minioConfig`, `/settings/aiConfig`, and `/secrets`.
- No dependency-repair HTTP 503 was observed.

## Final Runtime Idle Evidence

After the third terminal state:

- Admission circuit: `open=false`, state `closed`, parse/AI pending/running `0/0`, `activeTaskClean=true`.
- Active-task: no active/current/queued/drift/takeover work; only historical AI failures remained listed separately.
- Direct MinerU `/health`: `healthy`, queued `0`, processing `0`, failed `0`, completed `11`.
- Dependency-health: `ok=true`, `blocking=false`, Ollama `qwen3.5:9b` resident and `chatOk=true`.

## Artifacts

- Observation artifact: `/tmp/luceon-task128-observations.json`
- Screenshots:
  - `/tmp/luceon-task128-s1-before-upload.png`
  - `/tmp/luceon-task128-s1-list-0.png`
  - `/tmp/luceon-task128-s1-list-1.png`
  - `/tmp/luceon-task128-s1-detail-0.png`
  - `/tmp/luceon-task128-s1-detail-1.png`
  - `/tmp/luceon-task128-s1-final-list.png`
  - `/tmp/luceon-task128-s1-final-detail.png`
  - `/tmp/luceon-task128-s2-before-upload.png`
  - `/tmp/luceon-task128-s2-list-0.png`
  - `/tmp/luceon-task128-s2-list-1.png`
  - `/tmp/luceon-task128-s2-detail-0.png`
  - `/tmp/luceon-task128-s2-detail-1.png`
  - `/tmp/luceon-task128-s2-final-list.png`
  - `/tmp/luceon-task128-s2-final-detail.png`
  - `/tmp/luceon-task128-s3-before-upload.png`
  - `/tmp/luceon-task128-s3-list-0.png`
  - `/tmp/luceon-task128-s3-list-1.png`
  - `/tmp/luceon-task128-s3-detail-0.png`
  - `/tmp/luceon-task128-s3-detail-1.png`
  - `/tmp/luceon-task128-s3-final-list.png`
  - `/tmp/luceon-task128-s3-final-detail.png`

## Acceptance Judgment

Recommendation: `pass with residual risks`.

Pass evidence:

- All 3 authorized serial uploads completed.
- Each upload waited for terminal state before the next upload.
- All 3 tasks reached coherent `review-pending`.
- All 3 materials reached `reviewing`, MinerU completed, AI analyzed.
- Parsed artifacts were present for all 3 samples: `9`, `21`, `21`.
- Runtime returned clean after each sample and after the final sample.
- Dependency-repair status polling produced no HTTP 503 in any sample.
- Canonical global observation captured fresh attributable MinerU progress for all 3 samples.
- Task detail `当前进展` was visible throughout each observation window.

Residual risks:

- Fine-grained list/detail page progress was strong for s1, but sparse for s2 and s3. Endpoint/global-observation did capture fresh attributable progress for those samples, but the browser polling only caught a few fine-grained list/detail frames before MinerU completed.
- Browser console warnings remain for s2 and s3: `[db-sync] PUT /settings/*` and `/secrets` failed with `Failed to fetch`. These are not dependency-repair HTTP 503 regressions, but they are still operator-console noise and should be considered follow-up debt.
- Historical AI failure rows remain in active-task output as historical evidence and were not changed.
- Production worktree remains dirty with pre-existing local files unrelated to this validation.

## Stop Condition

No early stop occurred. All 3 authorized uploads were completed.

## Skipped Checks

- No concurrent upload: forbidden by task brief.
- No pressure, batch-concurrent, soak, or long-run validation: forbidden by task brief.
- No failed-task repair, reparse, or re-AI: forbidden by task brief.
- No cleanup, deletion, or mutation of historical tasks/materials/files: forbidden by task brief.
- No direct DB/MinIO mutation: forbidden by task brief.
- No `docker compose down`, `docker compose down -v`, or Docker volume/data cleanup: forbidden by task brief.
- No MinerU/Ollama/supervisor start/stop/restart/kill/attach/mutation: forbidden by task brief.
- No model pull/delete/replace, config/secret/sample mutation, PRD truth change, role contract change, project state change, or handoff change: forbidden by task brief.
- No L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线 claim: forbidden by task brief.

## Director Decision Needed

Director should decide whether to accept this small serial validation as a bounded pass with residual risks. My recommendation is `pass with residual risks`, specifically to track remaining db-sync console warnings and sparse browser-captured fine-progress windows for fast MinerU tasks as follow-up debt rather than blockers for this task.
