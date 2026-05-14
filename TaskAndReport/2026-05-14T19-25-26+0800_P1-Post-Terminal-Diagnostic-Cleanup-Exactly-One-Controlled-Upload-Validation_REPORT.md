# TestAcceptanceEngineer Report: P1 Post Terminal Diagnostic Cleanup Exactly One Controlled Upload Validation

## Based On

- Director task brief: `TaskAndReport/2026-05-14T19-25-26+0800_P1-Post-Terminal-Diagnostic-Cleanup-Exactly-One-Controlled-Upload-Validation_TASK.md`
- User decision: `TaskAndReport/2026-05-14T19-21-07+0800_P1-Next-Validation-Scope-After-Terminal-Diagnostic-Cleanup_DECISION.md`
- Director review: `TaskAndReport/2026-05-14T19-21-07+0800_P1-MinerU-Terminal-Diagnostic-Cleanup-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`

## Required Reading Completed

Read before execution:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/test-acceptance-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/TEST_MATRIX.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- Task 143 report and Director review listed above

## Scope

- Workspaces used: development workspace and production deployment path.
- Entered production deployment path: yes, for task-authorized preflight, exactly one UI upload, and read-only runtime/browser validation.
- Validation level: bounded production runtime/UAT evidence for one fresh upload only.
- Explicit non-goals: no second upload, no batch/intake/pressure/soak, no cleanup/repair/reparse/re-AI, no destructive DB/MinIO/Docker volume/data mutation, no Docker down/volume cleanup, no MinerU/Ollama/supervisor mutation, no settings/secrets/config/model/sample mutation, no readiness/L3/pressure PASS/release-readiness/production-readiness/go-live claim.

## Sample

- Selected sample: `/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`
- Size: `530205` bytes
- SHA-256: `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`
- Selection reason: small/medium PDF, large enough to expose MinerU progress semantics without widening into pressure or large-file validation.

## Preflight Evidence

- Development `git status --short --branch`: exit 0. Branch `development-engineer/p0-post-validation-ollama-mineru-blockers`; dirty shared workspace already contained many modified/untracked files.
- Production `git status --short --branch && git log -1 --oneline`: exit 0. Branch `main...origin/main`; HEAD `58f1437 Authorize terminal diagnostic cleanup deployment`; pre-existing local modifications remained in `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, `src/app/pages/SourceMaterialsPage.tsx`.
- `docker compose ps`: exit 0. `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` were healthy.
- `curl -fsS -o /tmp/luceon-task145-cms.html -w 'HTTP %{http_code}\n' http://localhost:8081/cms/`: exit 0, HTTP 200.
- `curl -fsS http://localhost:8081/__proxy/upload/health`: exit 0, `{"ok":true,"service":"upload-server"}`.
- `curl -sS --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?ollamaChatProbe=true&mineruSubmitProbe=true'`: exit 0, `ok=true`, `blocking=false`, MinerU submit probe `ok=true`/HTTP 202, admission circuit closed, Ollama `chatOk=true`, model `qwen3.5:9b` resident.
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit`: exit 0, `open=false`.
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/active-task`: exit 0, no active/current/queued/takeover-required work; historical AI failures remained limited to prior failed AI rows.
- `curl -sS --max-time 10 http://127.0.0.1:8083/health`: initial check after submit probe showed `processing_tasks=1`; after `sleep 5`, exit 0 with `queued_tasks=0`, `processing_tasks=0`, `failed_tasks=0`.

No active parse/AI work, open admission circuit, blocking dependency, unhealthy core service, or missing sample directory blocked the upload.

## Execution Evidence

- UI automation artifact: `/tmp/luceon-task145-observations.json`
- Screenshots:
  - `/tmp/luceon-task145-before-upload.png`
  - `/tmp/luceon-task145-final-detail.png`
  - `/tmp/luceon-task145-final-list.png`
  - `/tmp/luceon-task145-post-terminal-detail-refresh.png`
  - `/tmp/luceon-task145-post-terminal-list-refresh.png`
- First UI script attempt: exit 1 before upload because `/cms/tasks` `networkidle` timed out; `uploadCount=0`, no task/material created.
- Corrected UI script: exit 0; used `/cms/tasks` with `domcontentloaded`; set exactly one file on `data-testid="task-upload-file-input"`.
- Exact upload count: `1`.

Created identifiers:

- Task ID: `task-1778758370859`
- Material ID: `3380327087858932`
- MinerU task ID: `204b8692-8e2f-4aa8-9fe6-f9de62e1fd35`
- AI job ID: `ai-job-1778758387317-1ccb`

Observed state sequence:

- `pending/upload`: task created and detail page showed `当前进展` / `等待中`.
- `running/mineru-processing`: detail page showed `当前进展`; early API/log fallback text appeared, then live progress became visible.
- `ai-running/ai`: task detail showed `MinerU 正在解析：backend=pipeline，相位 页面处理，批次 1/1，页 3/3` plus `AI: 正在使用 ollama (qwen3.5:9b) 进行识别...`.
- `review-pending/review`: terminal success after about `83.4s`.

Terminal refreshed browser evidence:

- Task detail `当前进展`:
  - `MinerU 已完成，解析产物 21 个；最后可见进度：backend=pipeline，相位 页面处理，批次 1/1，页 3/3`
  - `AI 识别完成: review-pending (待人工复核)`
- Task list row for the same task showed:
  - `待复核`
  - `状态一致`
  - `MinerU 已完成，解析产物 21 个；最后可见进度：backend=pipeline，相位 页面处理，批次 1/1，页 3/3`
  - `AI 识别完成: review-pending (待人工复核)`

The old no-attributed-log diagnostic sentence was not appended as terminal `最后可见进度` for this fresh successful task.

## Final Runtime Evidence

Task/material/AI API evidence:

- Task final state: `state=review-pending`, `stage=review`, `message=AI 识别完成: review-pending (待人工复核)`.
- Task MinerU metadata: `mineruStatus=completed`, `parsedFilesCount=21`, `markdownObjectName=parsed/3380327087858932/full.md`.
- Material final state: `status=reviewing`, `mineruStatus=completed`, `aiStatus=analyzed`, `parsedFilesCount=21`, `markdownObjectName=parsed/3380327087858932/full.md`, `aiClassificationProvider=ollama`.
- AI job final state: `state=review-pending`, `progress=100`, `model=qwen3.5:9b`, `message=AI 识别完成 (65200ms)`.

Final runtime checks:

- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/active-task`: exit 0, no active/current/queued/takeover-required work.
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit`: exit 0, `open=false`, activeTaskClean true.
- `curl -sS --max-time 10 http://127.0.0.1:8083/health`: exit 0, `queued_tasks=0`, `processing_tasks=0`, `failed_tasks=0`.
- `curl -fsS http://localhost:8081/__proxy/upload/health`: exit 0, `ok=true`.
- `curl -sS --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?ollamaChatProbe=true'`: exit 0, `ok=true`, `blocking=false`, MinerU health OK, admission closed, Ollama `chatOk=true`, model resident.

No new MinerU failed task was observed. Historical AI failure rows remained pre-existing.

## Browser Console / Network Evidence

During the upload lifecycle automation, browser console captured two relevant non-blocking warnings:

- `[db-sync] POST /materials failed (count=1): Failed to fetch`
- `[db-sync] PUT /asset-details/3380327087858932 failed (silent): Failed to fetch`

The same run captured repeated `GET /__proxy/db/settings` and `GET /__proxy/db/secrets` `net::ERR_ABORTED` request failures while the script navigated between detail/list pages for polling. HTTP 5xx count was `0`.

After terminal state, a fresh read-only browser pass over the task detail and list showed:

- relevant console logs: `0`
- relevant request failures: `0`
- HTTP 5xx: `0`

Interpretation: the upload lifecycle reached a coherent terminal state, and post-terminal UI is clean on refresh, but the two upload-time `[db-sync]` Failed-to-fetch warnings are real residual console noise that should be reviewed by Director.

## Skipped Checks

- Second upload: skipped, explicitly forbidden.
- Batch/intake/pressure/soak/broader serial validation: skipped, explicitly forbidden.
- Cleanup/repair/reparse/re-AI: skipped, explicitly forbidden.
- Destructive DB/MinIO/Docker volume/data mutation and Docker down/volume cleanup: skipped, explicitly forbidden.
- MinerU/Ollama/supervisor start/stop/restart/kill/attach/mutation: skipped, explicitly forbidden.
- Settings/secrets/config/model/sample mutation: skipped, explicitly forbidden.
- L3, pressure PASS, release-readiness, production-readiness, go-live claim: skipped, explicitly forbidden.
- Browser-context direct `http://127.0.0.1:8083/health` fetch was not used as final evidence because browser `page.evaluate` direct fetch failed; shell `curl` direct MinerU health evidence was used instead.

## Recommendation

`PASS_WITH_RESIDUAL_CONSOLE_NOISE`

The fresh post-cleanup upload lifecycle passed the assigned functional and terminal-progress boundary:

- exactly one UI upload was performed;
- one new task/material was created;
- task/material/MinerU/AI states converged coherently to `review-pending` / `reviewing` / `completed` / `analyzed`;
- parsed artifact count was `21`;
- terminal task detail and task list showed clean primary progress with real backend/pipeline/page progress and did not append the old no-attributed-log diagnostic as `最后可见进度`;
- runtime returned idle and non-blocking afterward.

Residual issue for Director review: upload-time browser console emitted two `[db-sync] ... Failed to fetch` warnings for `POST /materials` and `PUT /asset-details/<materialId>`. They did not block the task and were absent on post-terminal refresh, but they are relevant console noise under the task brief and may justify a narrow follow-up.

Director decision required: yes. TestAcceptanceEngineer recommends acceptance of the bounded validation with the residual console-noise caveat, and defers final task acceptance / next scope to Director.
