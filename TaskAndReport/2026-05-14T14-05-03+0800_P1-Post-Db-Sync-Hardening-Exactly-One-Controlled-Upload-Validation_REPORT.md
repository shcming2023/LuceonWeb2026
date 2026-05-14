# Test Acceptance Report: P1 Post Db-Sync Hardening Exactly One Controlled Upload Validation

- Task ID: `TASK-20260514-140503-P1-Post-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation`
- Task brief: `TaskAndReport/2026-05-14T14-05-03+0800_P1-Post-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_TASK.md`
- Role: `TestAcceptanceEngineer`
- Report time: 2026-05-14T14:18:00+0800
- Workspaces used: development and production
- Entered production deployment path: yes
- Validation level: production exactly-one controlled UI upload validation

## Required Reading

Completed required reading from the task brief:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/test-acceptance-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- current task brief
- `TaskAndReport/2026-05-14T13-48-08+0800_P1-Db-Sync-Console-Warning-Hardening-Production-Deployment-And-Read-Only-Browser-Validation_REPORT.md`
- `TaskAndReport/2026-05-14T14-02-00+0800_P1-Db-Sync-Console-Warning-Hardening-Production-Deployment-And-Read-Only-Browser-Validation_DIRECTOR_REVIEW.md`
- `TaskAndReport/2026-05-14T14-02-00+0800_P1-Post-Db-Sync-Hardening-One-Upload-Validation-Authorization_DECISION.md`

## Scope

Executed the user-approved Option A boundary:

- exactly one controlled PDF upload
- sample source: `/Users/concm/prod_workspace/Luceon2026/testpdf`
- UI upload path: `http://localhost:8081/cms/tasks`
- observation targets: browser console/network counts, task list/detail progress semantics, final task/material/MinerU/AI state, and post-terminal runtime cleanliness

Not performed: second upload, pressure, batch, soak, L3, release-readiness, go-live claim, cleanup, repair, reparse, re-AI, failed-task mutation, settings/secrets/config/model/sample mutation, Docker down/volume cleanup, service ownership mutation, or source-code change.

## Workspace And HEAD Evidence

Development workspace:

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch during check: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- Worktree: dirty shared role workspace with many pre-existing modified/untracked files and TaskAndReport records.

Production workspace:

- Path: `/Users/concm/prod_workspace/Luceon2026`
- Branch/HEAD: `main...origin/main`, `4eb2e3b Accept db-sync warning hardening`
- Production worktree had pre-existing dirty files: `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, `src/app/pages/SourceMaterialsPage.tsx`.
- No unrelated files were reverted.

## Commands And Exit Codes

Development workspace:

- `git status --short --branch` - exit 0
- task ledger, task brief, role, policy, PRD, report, review, and decision reads - exit 0

Production workspace:

- `git status --short --branch && git log -1 --oneline` - exit 0
- `docker compose ps` - exit 0
- `curl -fsS http://localhost:8081/__proxy/upload/health` - exit 0
- `curl -sS --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?ollamaChatProbe=true'` - exit 0
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit` - exit 0
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task` - exit 0
- `curl -sS --max-time 10 http://127.0.0.1:8083/health` - exit 0
- sample `stat` and `shasum -a 256` - exit 0
- initial Playwright script attempt - exit 1; no upload was created. Cause: the script waited for the hidden file input to become visible instead of attached.
- pre-rerun admission/active-task check - exit 0; no active work existed.
- corrected Playwright UI upload and observation script - exit 0
- post-terminal list/detail read-only browser refreshes - exit 0

## Preflight Evidence

Preflight passed before the upload:

- Production HEAD included accepted db-sync hardening: `4eb2e3b Accept db-sync warning hardening`.
- Docker services healthy: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server`.
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
  - parse/AI pending/running counts `0/0`
  - `activeTaskClean=true`
- Active-task:
  - no active/current/queued/drift/submit-retryable/takeover-required tasks
  - only historical AI failures listed separately
- Direct MinerU:
  - `status=healthy`
  - queued `0`
  - processing `0`
  - failed `0`

## Sample

Selected exactly one small PDF:

- Path: `/Users/concm/prod_workspace/Luceon2026/testpdf/2025.pdf`
- Size: `175841` bytes
- SHA-256: `642599641f3b15e11b19f383379864081464be1f9c79bdd4f1e9334489c4b1ad`

Sample handling: read-only. The sample was not copied, moved, renamed, edited, deleted, truncated, or committed.

## Upload Result

- Upload status: HTTP `200`
- Task ID: `task-1778739091603`
- Material ID: `4487185779409524`
- Raw object: `originals/4487185779409524/source.pdf`
- MinerU task ID: `c3826beb-455a-4ed4-9a9b-5f9b0456bd4d`
- AI job ID: `ai-job-1778739125584-2ef7`
- Observations captured: `142`
- State sequence: `pending -> running -> ai-pending -> ai-running -> review-pending`
- Stage sequence: `upload -> mineru-processing -> complete -> ai -> review`

Final state:

- Task: `review-pending`, stage `review`, progress `100`
- Task message: `AI 识别完成: review-pending (待人工复核)`
- Material: `reviewing`
- `mineruStatus`: `completed`
- `aiStatus`: `analyzed`
- Parsed files count: `8`
- AI job: `review-pending`
- AI model: `qwen3.5:9b`

## Console And Network Evidence

Observed counts during the upload lifecycle:

- Console events total: `2`
- `[db-sync]` console events: `0`
- `/settings/` console events: `0`
- `/secrets` console events: `0`
- `Failed to fetch` console events: `0`
- HTTP `503` console events: `0`
- HTTP `503` network responses: `0`
- PUT `/settings/*` network requests: `0`
- PUT `/secrets` network requests: `0`
- Request failures total: `0`
- Request failures involving `/settings/*` or `/secrets`: `0`

The only console events were hydration logs:

- `[appContext] Hydrated from DB (38 materials, initialized=false)`
- `[appContext] Hydrated from DB (39 materials, initialized=false)`

Result: the Task 128 no-op db-sync settings/secrets warning pattern did not recur during this fresh upload lifecycle.

## Task List And Detail Evidence

Task detail:

- `当前进展` section was present throughout the observation loop: `142/142`.
- Final detail refresh showed:
  - `当前状态`: `待复核`
  - `当前阶段`: `review`
  - `已产物`: `已生成 (Markdown)`
  - `下一步动作`: `需人工审核`
  - `当前进展`: `MinerU 已完成，但本次未捕获可归因业务进度日志`
  - secondary line: `AI 识别完成: review-pending (待人工复核)`

Task list:

- Final task list refresh showed the row for `2025.pdf` with truncated task id `task-17787390916...`, stage `review`, engine `LOCAL-MINERU`, state `待复核`, `状态一致`.
- The list row showed:
  - `MinerU 已完成，但本次未捕获可归因业务进度日志`
  - `AI 识别完成: review-pending (待人工复核)`
- The automated in-flight list-page text sampler did not match the full task id because the UI truncates task IDs in the row. A post-terminal refresh confirmed the row text.

## Final Runtime Idle Evidence

After terminal state:

- Admission circuit: `open=false`, state `closed`, `activeTaskClean=true`.
- Active-task: no active/current/queued/drift/submit-retryable/takeover-required work; only historical AI failures remained listed separately.
- Dependency-health: `ok=true`, `blocking=false`.
- Direct MinerU `/health`: `healthy`, queued `0`, processing `0`, failed `0`, completed `13`.

## Artifacts

- Observation artifact: `/tmp/luceon-task132-observations.json`
- Screenshots:
  - `/tmp/luceon-task132-before-upload.png`
  - `/tmp/luceon-task132-list-1.png`
  - `/tmp/luceon-task132-detail-1.png`
  - `/tmp/luceon-task132-list-5.png`
  - `/tmp/luceon-task132-detail-5.png`
  - `/tmp/luceon-task132-list-141.png`
  - `/tmp/luceon-task132-detail-141.png`
  - `/tmp/luceon-task132-post-final-list-refresh.png`
  - `/tmp/luceon-task132-post-final-detail-refresh.png`

## Skipped Checks And Reasons

- No second upload was run because the task strictly authorized exactly one upload.
- No pressure/batch/soak validation was run because forbidden by the task.
- No cleanup, repair, reparse, re-AI, failed-task mutation, settings/secrets mutation, or runtime/service mutation was run because forbidden by the task.
- No release-readiness, L3, pressure PASS, or go-live conclusion is claimed.

## Risks And Residual Issues

- MinerU business-progress logs were not captured as attributable for this specific small sample; both task list and detail ended with `MinerU 已完成，但本次未捕获可归因业务进度日志`. This is not a terminal correctness failure, but it means this sample does not prove rich in-flight MinerU progress attribution.
- Task-list automated matching by full task ID failed because the UI truncates task IDs; a post-terminal browser refresh confirmed the row by file name, truncated task id, stage, status, and messages.
- Historical AI failures remain listed by active-task diagnostics; they were not part of this task and were not mutated.
- Production and development worktrees remain dirty with pre-existing unrelated changes.

## Acceptance Judgment

Recommendation: `pass with residual risks`.

Rationale:

- Exactly one upload was created.
- No concurrent/batch/pressure behavior was run.
- The fresh upload reached coherent terminal state: task `review-pending`, material `reviewing`, MinerU `completed`, AI `analyzed`, AI job `review-pending`.
- The Task 128 no-op db-sync warning pattern did not recur: `[db-sync]`, settings/secrets console warnings, `Failed to fetch`, HTTP 503, PUT `/settings/*`, and PUT `/secrets` were all `0`.
- Post-terminal runtime returned clean and nonblocking.

Director review is required for final task acceptance and next-step decision.
