# TestAcceptanceEngineer Report: P0 Exactly One Controlled Upload Validation After Batched Fixes

- Task ID: `TASK-20260513-183148-P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes`
- Report time: `2026-05-13T19:18:00+0800`
- Role: `TestAcceptanceEngineer`
- Based on task brief: `TaskAndReport/2026-05-13T18-31-48+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes_TASK.md`
- Recommendation: `FAIL_WITH_PARTIAL_FIX_CONFIRMED`

## 1. Scope And Workspaces

This validation executed the Director-assigned exactly-one-upload scope only.

- Development workspace used for task routing and report writeback: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace used for runtime validation: `/Users/concm/prod_workspace/Luceon2026`
- Production HEAD: `50e5621 Review MinerU diagnostics and dispatch deployment`
- Production local override was preserved and not modified.

This report does not claim production readiness, L3, pressure PASS, release readiness, or external/multi-user release suitability.

## 2. Required Reading

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
- prerequisite Task 90 report, Task 90 Director review, Task 94 report, and Task 94 Director review.

## 3. Preflight Evidence

Development preflight:

```bash
git status --short --branch
```

Exit code: `0`

Key output:

- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- Worktree already had unrelated modified/untracked files from previous project revisions. They were not reverted.

Production preflight:

```bash
git status --short --branch
git log -1 --oneline
docker compose ps
bash ops/runtime-ownership-status.sh
curl -fsS http://localhost:8081/__proxy/upload/health
curl -sS --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=1&ollamaChatProbe=1'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
curl -sS --max-time 10 http://127.0.0.1:11434/api/ps
stat -f '%z %N' '/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf'
shasum -a 256 '/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf'
file '/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf'
```

Exit code: `0` for the required preflight commands above.

Key output:

- Production branch: `main...origin/main`, with expected local `docker-compose.override.yml` diff.
- Production HEAD: `50e5621 Review MinerU diagnostics and dispatch deployment`.
- Docker services `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` were healthy.
- Upload health returned `{"ok":true,"service":"upload-server"}`.
- Runtime ownership helper confirmed strict runtime env:
  - `LOCAL_MINERU_ENDPOINT=http://host.docker.internal:8083`
  - `OLLAMA_API_URL=http://host.docker.internal:11434`
  - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
  - `DISABLE_AI_SKELETON_FALLBACK=true`
  - `ALLOW_AI_SKELETON_FALLBACK=false`
- Dependency health returned `ok=true`, `blocking=false`.
- MinerU submit probe succeeded with HTTP `202`; observed probe ids included `eca97f63-ebc7-469d-8a52-88e4cb916a95` and `9d2ea0a3-9771-4eb8-a508-bf8c7bed7083`.
- Ollama `qwen3.5:9b` was resident and chat-ready; `/api/ps` listed the model.
- Admission circuit was `closed`, `open=false`, `activeTaskClean=true`.
- Active-task diagnostics had no active/current/queued/takeover-required work before upload; only historical AI failures were listed.
- Authorized sample facts matched:
  - size: `530205`
  - SHA-256: `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`
  - file type: `PDF document, version 1.7`

Preflight judgment: `PASS`.

## 4. Upload Evidence

Exactly one upload was performed.

Command:

```bash
ts=$(date +%s); curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  -X POST http://localhost:8081/__proxy/upload/tasks \
  -H "X-Request-Id: tae-task95-${ts}" \
  -F "file=@/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf;type=application/pdf" \
  -F "materialId=validation-batched-fixes-${ts}" \
  -F "backend=pipeline"
```

Exit code: `0`

HTTP status: `200`

Created:

- `taskId=task-1778670208778`
- `materialId=validation-batched-fixes-1778670207`
- `objectName=originals/validation-batched-fixes-1778670207/source.pdf`
- `fileName=2025_2026学年春季课程中数G8_提取.pdf`
- `mimeType=application/pdf`

No retry or second upload was performed.

## 5. API Timeline

Evidence commands:

```bash
curl -sS 'http://localhost:8081/__proxy/db/tasks/task-1778670208778'
curl -sS 'http://localhost:8081/__proxy/db/materials/validation-batched-fixes-1778670207'
curl -sS 'http://localhost:8081/__proxy/db/ai-metadata-jobs/ai-job-1778670234560-4a6f'
curl -sS 'http://localhost:8081/__proxy/db/task-events?taskId=task-1778670208778'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
docker compose logs --tail=800 upload-server | rg -n 'task-1778670208778|ai-job-1778670234560-4a6f|UND_ERR_HEADERS_TIMEOUT|headers timeout|JSON Repair|strict|严格|repair'
```

Exit code: `0` for successful evidence commands.

Timeline:

| Time `+0800` | Evidence |
| --- | --- |
| `19:03:28` | Upload task created. |
| `19:03:34` | Worker connected to local MinerU and submitted MinerU task `5a4fa9fb-5d93-40c8-bda9-a06fb77e4bf2`. |
| `19:03:34` | UI/API initially showed `MinerU 已提交/正在处理，但暂无可归因业务日志`; worker briefly marked failed due log-observation unreadability. |
| `19:03:44` | Misjudged failed state corrected; MinerU was still processing. |
| `19:03:54` | Misjudged failed state corrected again; MinerU had completed. |
| `19:03:54` | Parsed artifacts saved to `parsed/validation-batched-fixes-1778670207/`, `parsedFilesCount=21`. |
| `19:03:54` | AI job created: `ai-job-1778670234560-4a6f`. |
| `19:03:57` | AI provider request started with `timeoutMs=180000`, provider `ollama`, model `qwen3.5:9b`, input length `3245`. |
| `19:05:38` | AI provider first pass succeeded after `101519ms`. |
| `19:08:13` | JSON Repair failed after `154520ms`; strict no-skeleton boundary blocked skeleton fallback. |
| `19:08:13` | Task/material/job reached terminal AI failure. |

Final task:

- `state=failed`
- `stage=ai`
- `progress=100`
- `message=AI 识别完成: failed`
- `mineruStatus=completed`
- `parsedFilesCount=21`
- `aiJobId=ai-job-1778670234560-4a6f`

Final material:

- `status=failed`
- `mineruStatus=completed`
- `aiStatus=failed`
- `processingMsg=AI 识别失败`
- parsed artifact pointers present.

Final AI job:

- `state=failed`
- `progress=45`
- `message=AI 识别异常: [AI 严格模式拦截] 不允许降级到骨架模型: AI Provider 二段式 JSON 修复失败，降级为 skeleton 结果`
- `metadata.currentPhase=repair-failed`

## 6. MinerU Evidence

MinerU completed and stored parsed artifacts:

- `mineruTaskId=5a4fa9fb-5d93-40c8-bda9-a06fb77e4bf2`
- `mineruStatus=completed`
- `parsedFilesCount=21`
- `markdownObjectName=parsed/validation-batched-fixes-1778670207/full.md`
- `artifactManifestObjectName=parsed/validation-batched-fixes-1778670207/artifact-manifest.json`
- `zipObjectName=parsed/validation-batched-fixes-1778670207/mineru-result.zip`
- `artifactIncomplete=false`

Task-level metadata still retained the stale in-flight diagnostic:

- `activityLevel=log-observation-unreadable`
- message: `MinerU 已提交/正在处理，但暂无可归因业务日志`

Material-level metadata and task list UI showed the improved terminal diagnostic:

- `activityLevel=fast-complete-no-business-signal`
- `freshness=completed-diagnostic`
- message: `MinerU 已完成，但本次未捕获可归因业务进度日志`

Interpretation: Task 93's terminal wording improvement is visible on the task list/material view, but the task record metadata still carries stale task-level `log-observation-unreadable` evidence. The runtime also briefly misjudged MinerU as failed twice and then corrected it. This is improved from Task 90's visible wording, but still not fully clean terminal semantics.

## 7. AI Evidence

AI did not reach `review-pending`.

Positive evidence:

- The 30-second `UND_ERR_HEADERS_TIMEOUT` did not recur.
- First pass succeeded: `durationMs=101519`, `timeoutMs=180000`.
- Strict no-skeleton behavior was preserved.

Failure evidence:

- Repair pass failed with `Failed to parse JSON from Ollama response, model: qwen3.5:9b`.
- Repair raw content length was `2687`; `rawLooksTruncated=false`; `responseFormatRequested=true`; `expectJson=true`.
- Final failure was strict no-skeleton interception:
  `AI Provider 二段式 JSON 修复失败，降级为 skeleton 结果`.

Duplicate-processing evidence:

- No evidence was found that this AI job was processed again after a successful finalization path.
- The event stream shows one provider first-pass start, one first-pass success, one repair failure, and one strict failure.
- Upload-server logs show one `Picking recovered job` and one `Picking up job` for `ai-job-1778670234560-4a6f`, followed by first-pass parse failure, repair failure, and final strict-mode error.
- Because this run never reached successful finalization, it does not prove the accepted finalization path reaches `review-pending`; it does confirm the Task 90 duplicate-after-success failure pattern did not recur in this failed-repair path.

## 8. UI Evidence

Browser observation used Playwright against production `/cms/`.

Command:

```bash
npx pnpm@10.4.1 --dir uat exec node <playwright-observation-script>
```

Exit code: `0`

Screenshots were saved locally under `/tmp/luceon-task95-*.png` and were not committed.

During AI running, task detail page showed:

- `当前状态`: `AI 分析中`
- `当前阶段`: `ai`
- `已产物`: `已生成 (Markdown)`
- `下一步动作`: `等待系统处理`
- `消息`: `AI: 正在使用 ollama (qwen3.5:9b) 进行识别...`

During AI running, task list row showed:

- `AI 元数据识别中`
- `流转中`
- `100%`
- `MinerU 已完成，但本次未捕获可归因业务进度日志`
- `AI: 正在使用 ollama (qwen3.5:9b) 进行识别...`

After terminal failure, task detail page showed:

- `当前状态`: `失败`
- `当前阶段`: `ai`
- `已产物`: `已生成 (Markdown)`
- `下一步动作`: `需排查或重试`
- `消息`: `AI 识别完成: failed`

After terminal failure, task list row showed:

- `失败`
- `已终止`
- `MinerU 已完成，但本次未捕获可归因业务进度日志`
- `AI 识别完成: failed`

UI observation gap: the task detail overview did not expose the MinerU terminal diagnostic line directly in the captured body; the task list did.

## 9. Post-Terminal Runtime Evidence

Post-terminal active-task diagnostics:

- `activeTask=null`
- `currentProcessingTask=null`
- `queuedTasks=[]`
- `completedButNotIngestedTasks=[]`
- `driftTasks=[]`
- `submitRetryableTasks=[]`
- `takeoverRequiredTasks=[]`
- historical AI failures now include `task-1778670208778`, `task-1778655375028`, and `task-1778651226016`.

Post-terminal admission circuit:

- `state=closed`
- `open=false`
- `activeTaskClean=true`
- counts: `parsePending=0`, `parseRunning=0`, `aiPending=0`, `aiRunning=0`

Ollama `/api/ps` still listed resident `qwen3.5:9b`.

## 10. Specific Questions

1. Did MinerU complete and store parsed artifacts?
   - Yes. `parsedFilesCount=21`, parsed prefix and manifest/zip pointers are present.
2. Did terminal MinerU wording prefer completion/artifact evidence instead of stale in-flight wording?
   - Partially. Task list and material metadata show `MinerU 已完成，但本次未捕获可归因业务进度日志`; task metadata still retains stale `log-observation-unreadable`.
3. Did AI reach `review-pending` or another acceptable non-skeleton terminal result?
   - No. It reached terminal `failed`.
4. If AI failed, is there evidence of duplicate processing of the same AI job after successful finalization?
   - No evidence of duplicate processing after successful finalization; this run never achieved successful finalization.
5. Did any 30s `UND_ERR_HEADERS_TIMEOUT` recur?
   - No. Event text contained zero `UND_ERR_HEADERS_TIMEOUT`; first pass succeeded after `101519ms`.
6. Did the task page provide useful operator semantics during and after processing?
   - Partially. Task list wording is useful for terminal MinerU completion and AI failure; task detail overview shows clear AI state and next action but not the MinerU terminal diagnostic line in the captured overview.
7. Were admission circuit and active-task diagnostics clean after terminal state?
   - Yes. No active/current/queued/takeover work; admission circuit remained closed.

## 11. Skipped Checks And Reasons

- Second upload: skipped because explicitly forbidden.
- Pressure, batch, soak, or 24-PDF validation: skipped because explicitly forbidden.
- Failed-task repair, reparse, or re-AI: skipped because explicitly forbidden.
- DB, MinIO, Docker volume/data cleanup or mutation: skipped because explicitly forbidden.
- Docker restart/rebuild/rollback/down/prune: skipped because explicitly forbidden.
- Model pull/delete/replace/restart/reload: skipped because explicitly forbidden.
- GitHub fetch/pull/push: skipped because TestAcceptanceEngineer was not authorized to sync GitHub in this task.
- Production readiness, L3, pressure PASS, and release-readiness declaration: not claimed because outside scope and explicitly forbidden.

## 12. Risks And Residual Issues

- End-to-end validation still fails at AI metadata JSON repair / strict no-skeleton boundary.
- The previous 30-second Ollama timeout appears fixed for this sample, but AI output schema compliance remains a blocker.
- MinerU terminal UI wording improved on the task list/material side, but task metadata still carries stale `log-observation-unreadable`.
- The worker still briefly marks MinerU failed due log-observation unreadability and then corrects it. That correction prevents terminal parse failure, but the transient false-failed events remain noisy and may confuse operators or diagnostics.
- Task detail overview did not show the MinerU terminal diagnostic in the captured visible text, while task list did.

## 13. Forbidden Actions Confirmation

Not performed:

- second upload;
- pressure/batch/soak/24-PDF test;
- failed-task repair;
- reparse or re-AI;
- DB/MinIO/Docker volume/data deletion or cleanup;
- Docker `down`, `down -v`, prune, broad restart, rebuild, rollback;
- model operation;
- secret, timeout, override, PRD, role-contract, or public API mutation;
- sample mutation or sample copy into repository;
- GitHub push;
- production-readiness, L3, pressure PASS, or release-readiness claim.

## 14. Recommendation To Director

Recommendation: `FAIL_WITH_PARTIAL_FIX_CONFIRMED`.

Accept this report as valid failed-validation evidence if the Director agrees that the exactly-one-upload boundary and evidence requirements were satisfied.

Suggested interpretation:

- MinerU parse and artifact storage: pass.
- Task-list terminal MinerU diagnostic wording: improved, but task-detail/task-metadata semantics remain partial.
- AI 30-second timeout regression: not observed.
- AI finalization: fail, due JSON repair failure and strict no-skeleton interception.
- Duplicate-after-success failure from Task 90: not reproduced in this failed-repair run, but successful finalization remains unproven.

Director decision is required for acceptance and next task dispatch.
