# TestAcceptanceEngineer Report: P1 MinerU Observation Hardening Exactly One Controlled Upload Validation

- Report time: 2026-05-14T05:42:00+0800
- Role: TestAcceptanceEngineer
- Based on Director task brief: `TaskAndReport/2026-05-14T05-21-59+0800_P1-MinerU-Observation-Hardening-Exactly-One-Controlled-Upload-Validation_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Production HEAD: `159d80e Accept MinerU log observation hardening`
- Recommendation: `PASS_WITH_RESIDUAL_DIAGNOSTIC_PROGRESS_LIMITATION`

## Scope

This report covers exactly one controlled production upload validation after Task 101 MinerU observation hardening was deployed by Task 102.

The validation question was narrow:

Does unreadable/stale MinerU log observation remain diagnostic-only while the MinerU API is still processing/running, instead of producing terminal or operator-misleading false failed task semantics?

This is not a pressure, batch, soak, L3, production-readiness, release-readiness, go-live, or production上线 validation.

## Preflight

Development workspace:

- `git status --short --branch` -> exit 0
  - branch `development-engineer/p0-post-validation-ollama-mineru-blockers`
  - pre-existing dirty/untracked files present; not modified except this report and Task 104 ledger row.

Production workspace:

- `git status --short --branch` -> exit 0
  - `## main...origin/main`
  - known local modification: `docker-compose.override.yml`
- `git log -1 --oneline` -> exit 0
  - `159d80e Accept MinerU log observation hardening`
- `docker compose ps` -> exit 0
  - `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` were up and healthy.
- `bash ops/runtime-ownership-status.sh` -> exit 0
  - upload health ok.
  - runtime env truth included `LOCAL_MINERU_ENDPOINT=http://host.docker.internal:8083`, `OLLAMA_API_URL=http://host.docker.internal:11434`, `OLLAMA_TIER2_MODEL=qwen3.5:9b`, `DISABLE_AI_SKELETON_FALLBACK=true`, `ALLOW_AI_SKELETON_FALLBACK=false`.
  - dependency-health with MinerU submit probe returned `ok=true`, `blocking=false`.
  - MinerU submit probe returned `ok=true`, HTTP `202`.
  - Ollama `qwen3.5:9b` was resident and `chatOk=true`.
  - active-task diagnostics were clean except historical AI failures.
  - MinerU health initially showed `queued_tasks=0`, `processing_tasks=0`.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/active-task` -> exit 0
  - no active/current/queued/drift/takeover work.
- `curl -fsS http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit` -> exit 0
  - circuit `closed`, `open=false`, `activeTaskClean=true`.
- `curl -fsS http://localhost:8081/__proxy/upload/health` -> exit 0
  - `{"ok":true,"service":"upload-server"}`
- `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true&ollamaChatProbe=true'` -> exit 0
  - `ok=true`, `blocking=false`, MinerU submit probe `202`, Ollama `chatOk=true`.

Pre-upload stop conditions were not met.

## Selected Sample

- Path: `/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`
- Size: `530205` bytes
- SHA-256: `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`
- Selection rationale: one small/medium PDF from the Director-authorized production test sample folder. Sample file was read only and not modified.

## Single Upload

Exactly one upload was performed:

```bash
curl -sS -w '\nHTTP_STATUS:%{http_code}\n' \
  -H "X-Request-Id: task104-<timestamp>" \
  -F "file=@/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf;type=application/pdf" \
  -F "materialId=task104-mineru-observation-1778708003" \
  -F "backend=pipeline" \
  'http://localhost:8081/__proxy/upload/tasks'
```

Result:

- exit 0
- HTTP `200`
- task id: `task-1778708005470`
- material id: `task104-mineru-observation-1778708003`
- raw object: `originals/task104-mineru-observation-1778708003/source.pdf`

No second upload was performed.

## Runtime Evidence

Initial live observation while MinerU API was still processing:

- task state: `running`
- task stage: `mineru-processing`
- task progress: `50`
- task message: `MinerU 已提交/正在处理，但暂无可归因业务日志`
- MinerU task id: `c3d3e548-2b4f-4b6e-ae0d-0c11e17bb5a2`
- MinerU API health at that time: `processing_tasks=1`
- `mineruObservedProgress.activityLevel=log-observation-unreadable`
- `mineruObservedProgress.observationStale=true`
- `mineruLogObservationWarning.kind=mineru-log-observation-diagnostic-only`
- warning message: `MinerU API 仍在处理；日志观测不可读或滞后，仅作为诊断告警，不判定解析失败。`
- active-task surface identified this task as active/current processing.

This confirms the core Task 104 behavior: `log-observation-unreadable` occurred while MinerU was processing, but it remained diagnostic-only and did not terminally fail the task.

Terminal state:

- task state: `review-pending`
- task stage: `review`
- task progress: `100`
- task message: `AI 识别完成: review-pending (待人工复核)`
- material status: `reviewing`
- material `mineruStatus=completed`
- material `aiStatus=analyzed`
- parsed prefix: `parsed/task104-mineru-observation-1778708003/`
- parsed files count: `21`
- artifact manifest: `parsed/task104-mineru-observation-1778708003/artifact-manifest.json`
- markdown object: `parsed/task104-mineru-observation-1778708003/full.md`

AI job:

- AI job id: `ai-job-1778708023060-2c3d`
- state: `review-pending`
- provider/model: `ollama` / `qwen3.5:9b`
- progress: `100`
- confidence: `30`
- needsReview: `true`
- message: `AI 识别完成 (77530ms)`
- current phase: `repair-deterministic-succeeded`
- first pass failure kind: `schema_invalid`
- deterministic repair mode: `deterministic-draft-normalization`
- deterministic repair succeeded: `true`
- metadata title: `多边形错题集`
- subject: `数学`
- grade: `八年级`
- material type: `试卷`

Final runtime surfaces:

- active-task diagnostics: no active task, no current processing task, no queued tasks, no drift/takeover work; historical AI failure tasks unchanged.
- admission circuit: `closed`, `open=false`, `activeTaskClean=true`, counts `parsePending=0`, `parseRunning=0`, `aiPending=0`, `aiRunning=0`.
- dependency-health with MinerU submit probe and Ollama chat probe: `ok=true`, `blocking=false`.
- final MinerU health: `queued_tasks=0`, `processing_tasks=0`, `completed_tasks=44`, `failed_tasks=0`.
- Ollama `/api/ps`: `qwen3.5:9b` resident.

## Browser / Operator-Visible Evidence

Playwright browser check:

- `npx pnpm@10.4.1 --dir uat exec node -e <browser observation script>` -> exit 0
- task list screenshot: `/tmp/luceon-task104-list.png`
- task detail screenshot: `/tmp/luceon-task104-detail.png`

Task list displayed:

- file `2025_2026学年春季课程中数G8_提取.pdf`
- `Task: task-17787080054…`
- current status `待复核`
- diagnostics badge `状态一致`
- MinerU line: `MinerU 已完成，但本次未捕获可归因业务进度日志`
- AI line: `AI 识别完成: review-pending (待人工复核)`

Task detail displayed:

- task id `task-1778708005470`
- current state `待复核`
- current stage `review`
- artifact status `已生成 (Markdown)`
- next action `需人工审核`
- message `AI 识别完成: review-pending (待人工复核)`
- internal diagnostics section present: `内部诊断信息 (状态一致性、MinerU 画像、AI 任务、日志观测)`

No operator-visible false `failed` state was observed for this validation task.

## Command Summary

- Development `git status --short --branch` -> 0
- Read required project docs and Task 104 brief -> 0
- Production `git status --short --branch` -> 0
- Production `git log -1 --oneline` -> 0
- `docker compose ps` -> 0
- `bash ops/runtime-ownership-status.sh` -> 0
- `find ... testpdf ...` inventory -> 0
- `curl` upload health -> 0
- `curl` dependency-health with submit/chat probes -> 0
- `curl` admission circuit -> 0
- `curl` active-task -> 0
- `shasum -a 256` selected PDF -> 0
- `stat` selected PDF -> 0
- exactly one `curl -F file=@... /__proxy/upload/tasks` upload -> 0, HTTP 200
- Node polling script for task/material/AI/final runtime evidence -> 0
- Playwright browser observation script -> 0
- `docker logs --tail 200 cms-upload-server | rg ...` -> 0
- final runtime checks -> 0

## Skipped / Not Performed

- No second upload.
- No pressure, batch-concurrent, soak, broad stress, or long-run test.
- No failed-task repair, retry, reparse, re-AI, cleanup, delete, rename, or historical mutation.
- No DB/MinIO/Docker volume/data destructive operation.
- No model pull/delete/replace or config/secret/env mutation.
- No broad restart, rebuild, rollback, or Docker Compose mutation.
- No sample-file mutation.
- No GitHub fetch/pull/push from this TestAcceptanceEngineer task.
- No L3, production-readiness, release-readiness, go-live readiness, or production上线 claim.

## Assessment

Result: `PASS_WITH_RESIDUAL_DIAGNOSTIC_PROGRESS_LIMITATION`.

Within exactly one controlled upload, the defect class targeted by Task 101 did not recur as a terminal or operator-visible false failed state. The validation task did experience `log-observation-unreadable` while MinerU API was processing, and the deployed hardening kept it as `mineru-log-observation-diagnostic-only`. The task continued through MinerU completion, stored 21 parsed artifacts, ran Ollama `qwen3.5:9b`, and reached `review-pending`.

Residual limitation: MinerU progress remains diagnostic rather than business-progress-rich for this sample. The UI still reports `MinerU 已完成，但本次未捕获可归因业务进度日志`, which is accurate but not rich progress evidence. That is not a failure of the Task 104 acceptance boundary.

## Director Decision Needed

Director should decide whether to accept this one-upload validation boundary and whether any further product/observability polish is needed. This report does not authorize broader validation or release decisions.
