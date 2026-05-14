# TestAcceptanceEngineer Report: P1 Upload-Time Db-Sync Hardening Exactly One Controlled Upload Validation

## Based On

- Director task brief: `TaskAndReport/2026-05-14T20-57-42+0800_P1-Upload-Time-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_TASK.md`
- Based user decision: `TaskAndReport/2026-05-14T19-54-24+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-Decision_DECISION.md`
- Based deployment review: `TaskAndReport/2026-05-14T20-57-42+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`

## Required Reading Completed

Read or re-read before execution:

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
- This task brief
- `TaskAndReport/2026-05-14T20-38-00+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-And-Read-Only-Validation_REPORT.md`
- `TaskAndReport/2026-05-14T20-57-42+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`

## Workspaces

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production UI: `http://localhost:8081/cms/`
- Production upload proxy base: `http://localhost:8081/__proxy/upload`
- Test PDF source directory: `/Users/concm/prod_workspace/Luceon2026/testpdf`
- Entered production deployment path: yes, because the task explicitly required production runtime validation with exactly one controlled upload.

## Scope

Executed exactly one controlled small/medium PDF upload in production to validate upload-time db-sync console/network behavior after Task 146 hardening was deployed and accepted by Task 148.

This report does not claim L3, pressure PASS, release readiness, production readiness, go-live readiness, or production上线.

## Preflight Evidence

- Development `git status --short --branch`: exit `0`; branch `development-engineer/p0-post-validation-ollama-mineru-blockers`; dirty shared worktree with existing modified/untracked project files.
- Production `git status --short --branch`: exit `0`; branch `main...origin/main`; existing local modifications: `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, `src/app/pages/SourceMaterialsPage.tsx`.
- Production `git log -1 --oneline`: exit `0`; `89271a1 Dispatch db-sync hardening production deployment`.
- Production `docker compose ps`: exit `0`; `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` were healthy.
- Frontend `/cms/`: exit `0`; HTTP `200`.
- Upload health: exit `0`; `{"ok":true,"service":"upload-server"}`.
- Marker check: exit `0`; production source contains `dbSyncPageLifecycleEnding`, `cancelled during page lifecycle change`, and `db-sync-page-lifecycle-noise`.
- Dependency health with Ollama chat probe and MinerU submit probe: exit `0`; `ok=true`, `blocking=false`; MinerU submit probe HTTP `202`; admission circuit closed; Ollama `chatOk=true`, model `qwen3.5:9b`, resident before chat.
- Direct MinerU `/health` immediately after safe submit probe showed `processing_tasks=1`, attributable to the submit probe.
- After `sleep 5`, direct MinerU `/health`: exit `0`; `queued_tasks=0`, `processing_tasks=0`, `failed_tasks=0`.
- After `sleep 5`, active-task: exit `0`; no active/current/queued/takeover-required work; only 3 historical AI failure tasks remained.
- After `sleep 5`, admission circuit: exit `0`; `open=false`, state `closed`, counts `parsePending=0`, `parseRunning=0`, `aiPending=0`, `aiRunning=0`.
- Test PDF source directory existed and contained reasonable small/medium PDFs.

Preflight passed. No stop condition was hit.

## Sample Selection

- Chosen file: `/Users/concm/prod_workspace/Luceon2026/testpdf/PDF document-4F18-A8A3-62-0.pdf`
- Size: `711046` bytes (`694K` from `ls -lh`)
- SHA-256: `bb491c5782c001a60e9af1c8d531cbf3ce9807f0db341af765c31cc2d75e56f4`
- Rationale: small/medium controlled PDF, large enough to exercise upload, MinerU, MinIO, AI metadata, task detail, and task list behavior, but small enough to avoid pressure/soak or long-running validation scope.

The sample file was read only. It was not copied, modified, moved, renamed, deleted, or polluted.

## Execution Evidence

- Browser/runtime harness: Playwright via `npx pnpm@10.4.1 --dir uat exec node`.
- First harness attempt: exit `2`; no upload occurred. It waited for the hidden upload input to become visible and timed out. Evidence: `uploadCount=0`, no new task, no new material. This attempt is recorded as a harness issue, not as a validation upload.
- Corrected harness attempt: exit `0`; exactly one `setInputFiles` call was made after waiting for the hidden input to be attached.
- Exact upload count: `1`.
- Evidence file outside repo: `/tmp/luceon-task149-browser-evidence.json`.
- Validation window: `2026-05-14T13:06:30.082Z` to `2026-05-14T13:08:26.110Z`.
- Task count before upload: `49`.
- New task created: `task-1778763994124`.
- New material created: `178015320076052`.
- Initial new task state: `pending`, stage `upload`, message `任务已创建待处理`.

## Terminal-State Evidence

- Final task id: `task-1778763994124`.
- Final material id: `178015320076052`.
- MinerU task id: `0705d847-51f2-4444-ab12-defa9256da5c`.
- AI job id: `ai-job-1778764001335-531c`.
- Final task state/stage/progress: `review-pending` / `review` / `100`.
- Final task message: `AI 识别完成: review-pending (待人工复核)`.
- Final material state: `status=reviewing`, `mineruStatus=completed`, `aiStatus=analyzed`.
- Parsed artifact count: `9`.
- AI metadata job: `state=review-pending`, `progress=100`, `providerId=ollama`, `model=qwen3.5:9b`, message `AI 识别完成 (92847ms)`, current phase `repair-deterministic-succeeded`.
- Runtime returned idle/non-blocking:
  - active-task: no active/current/queued/takeover-required work; historical AI failure count remained `3`.
  - admission circuit: `open=false`, state `closed`, counts `parsePending=0`, `parseRunning=0`, `aiPending=0`, `aiRunning=0`.
  - dependency-health with Ollama chat probe: `ok=true`, `blocking=false`, MinerU OK, Ollama OK, `chatOk=true`, model `qwen3.5:9b`.
  - direct MinerU `/health`: `queued_tasks=0`, `processing_tasks=0`, `failed_tasks=0`.

## Upload Lifecycle / UI Evidence

- Task detail terminal refresh showed:
  - current state `待复核`;
  - current stage `review`;
  - generated artifact `已生成 (Markdown)`;
  - next action `需人工审核`;
  - progress text: `MinerU 已完成，解析产物 9 个；最后可见进度：backend=pipeline，相位 页面处理，批次 1/1，页 1/1`;
  - AI message: `AI 识别完成: review-pending (待人工复核)`.
- Task list terminal refresh showed the same new task at the top with:
  - status `待复核`;
  - diagnostics badge `状态一致`;
  - progress text: `MinerU 已完成，解析产物 9 个；最后可见进度：backend=pipeline，相位 页面处理，批次 1/1，页 1/1`;
  - AI message: `AI 识别完成: review-pending (待人工复核)`.
- The old no-attributed-log diagnostic was not appended as `最后可见进度` in task detail or task list.
- Operator-facing UI remained understandable for this bounded validation path.

## Db-Sync Console / Network Evidence

Browser console/network capture during upload, task detail navigation, polling, terminal detail refresh, and terminal list refresh:

- `[db-sync] POST /materials failed`: `0`.
- `[db-sync] PUT /asset-details/... failed`: `0`.
- All `[db-sync]` signals: `0`.
- db-sync warning count: `0`.
- db-sync lifecycle-cancelled debug count: `0`; no lifecycle-cancelled db-sync message was visible in this run.
- `/settings` signals: `0`.
- `/secrets` signals: `0`.
- `Failed to fetch` signals: `0`.
- HTTP `5xx`: `0`.
- Non-stream request failures: `0`.
- Stream request failures: `3`, all `eventsource` `net::ERR_ABORTED` from `/__proxy/upload/tasks/stream` during navigation/teardown:
  - `http://localhost:8081/__proxy/upload/tasks/stream`
  - `http://localhost:8081/__proxy/upload/tasks/stream?taskId=task-1778763994124`
  - `http://localhost:8081/__proxy/upload/tasks/stream?taskId=task-1778763994124`
- Console logs were limited to expected hydration logs:
  - `[appContext] Hydrated from DB (49 materials, initialized=false)`
  - `[appContext] Hydrated from DB (50 materials, initialized=false)` repeated across refreshes.

The Task 145 upload-time db-sync warning class did not recur in this exactly-one-upload run.

## Commands Run And Exit Codes

- `git status --short --branch` in development workspace: exit `0`.
- `sed -n '1,260p' TaskAndReport/2026-05-14T20-57-42+0800_P1-Upload-Time-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_TASK.md`: exit `0`.
- `sed -n '145,158p' TaskAndReport/TASK_TRACKING_LIST.md`: exit `0`.
- Required-reading `sed` reads for role docs, project docs, Task 148 report, and Director review: exit `0`.
- `git status --short --branch` in production: exit `0`.
- `git log -1 --oneline` in production: exit `0`.
- `docker compose ps`: exit `0`.
- `rg -n "dbSyncPageLifecycleEnding|cancelled during page lifecycle change|db-sync-page-lifecycle-noise" ...`: exit `0`.
- `find /Users/concm/prod_workspace/Luceon2026/testpdf ... | xargs -0 ls -lh`: exit `0`.
- `curl -fsS -o /tmp/luceon-task149-cms-pre.html -w 'HTTP %{http_code}\n' http://localhost:8081/cms/`: exit `0`.
- `curl -fsS http://localhost:8081/__proxy/upload/health`: exit `0`.
- `curl -sS --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?ollamaChatProbe=true&mineruSubmitProbe=true'`: exit `0`.
- `curl -sS --max-time 10 http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit`: exit `0`.
- `curl -sS --max-time 10 http://localhost:8081/__proxy/upload/ops/mineru/active-task`: exit `0`.
- `curl -sS --max-time 10 http://127.0.0.1:8083/health`: exit `0`.
- `sleep 5; curl .../health`, `sleep 5; curl .../active-task`, `sleep 5; curl .../admission-circuit`: exit `0`.
- `stat -f '%z bytes %N' ...; shasum -a 256 ...`: exit `0`.
- `npx pnpm@10.4.1 --dir uat exec node -e "import('playwright')..."`: exit `0`.
- `curl -sS --max-time 10 'http://localhost:8081/__proxy/db/tasks' | head -c 1200`: exit `0` for the shell pipeline; curl printed a broken-pipe warning because `head` closed early. This was read-only endpoint shape inspection.
- `curl -sS --max-time 10 'http://localhost:8081/__proxy/db/ai-metadata-jobs' | head -c 800`: exit `0` for the shell pipeline; curl printed a broken-pipe warning because `head` closed early. This was read-only endpoint shape inspection.
- First Playwright harness attempt: exit `2`; no upload occurred (`uploadCount=0`), hidden input visibility wait timed out.
- Corrected Playwright harness attempt: exit `0`; exactly one upload occurred (`uploadCount=1`) and reached terminal state.
- Post-terminal endpoint summary curl bundle: exit `0`.
- Evidence summarizer `node` command reading `/tmp/luceon-task149-browser-evidence.json`: exit `0`.

No `git fetch`, `git pull`, `git push`, service restart, Docker build/up/down, cleanup, repair, reparse, or re-AI command was run by this TestAcceptanceEngineer task.

## Skipped Checks And Exact Reasons

- Second upload: skipped, explicitly forbidden.
- Batch/intake/pressure/soak/broader serial validation: skipped, explicitly forbidden.
- Cleanup, deletion, repair, failed-task repair, reparse, or re-AI: skipped, explicitly forbidden.
- Direct DB or MinIO mutation: skipped, explicitly forbidden.
- `docker compose down`, `docker compose down -v`, Docker volume/data cleanup, Docker rebuild/restart/up/down: skipped, explicitly forbidden for this role task.
- MinerU/Ollama/supervisor start/stop/restart/kill/attach/mutation: skipped, explicitly forbidden.
- Model pull/delete/replace and config/secret/sample mutation: skipped, explicitly forbidden.
- Readiness/L3/pressure PASS/release-readiness/production-readiness/go-live claim: skipped, explicitly forbidden.

## Risks / Residual Issues

- This is exactly one controlled fresh upload only. It is not batch, pressure, soak, L3, release-readiness, or broad production-readiness evidence.
- Browser captured 3 `eventsource` stream aborts during navigation/teardown. These were stream request failures for `/__proxy/upload/tasks/stream`, not non-stream db-sync, settings, secrets, Failed-to-fetch, or HTTP 5xx failures.
- Historical AI failure rows remain visible in active-task output (`3` historical AI failures). They were pre-existing and not created by this validation run.
- Production workspace still has pre-existing local modifications reported in preflight. They were not changed or reverted by this task.
- The first harness attempt failed before upload due to a hidden file input visibility wait. It created no task/material and is recorded so Director can distinguish harness noise from runtime evidence.

## Recommendation

`PASS_WITH_STREAM_ABORT_NOTE`

The exactly-one-upload validation passed the assigned acceptance boundary:

- exactly one new task/material was created;
- `[db-sync] POST /materials failed` did not recur;
- `[db-sync] PUT /asset-details/... failed` did not recur;
- no settings/secrets/Failed-to-fetch/HTTP 5xx/non-stream request-failed noise was observed;
- task, material, MinerU, AI, and UI states converged coherently to `review-pending`;
- terminal task detail/list progress stayed clean and did not append the old no-attributed-log diagnostic;
- runtime returned idle/non-blocking.

Director review is required for final acceptance and any next-step decision.

## Boundaries Confirmed

No second upload, batch/intake/pressure/soak/broader serial validation, cleanup/repair/reparse/re-AI, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, model/config/secret/sample mutation, PRD/project-state/handoff/role-contract change, GitHub sync, readiness claim, L3 claim, pressure PASS claim, release-readiness claim, production-readiness claim, go-live claim, or production上线 claim was made.

