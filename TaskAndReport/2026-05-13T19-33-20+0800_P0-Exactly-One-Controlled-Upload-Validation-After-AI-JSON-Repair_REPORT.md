# TASK-20260513-193320-P0-Exactly-One-Controlled-Upload-Validation-After-AI-JSON-Repair Report

- Role: TestAcceptanceEngineer
- Report time: 2026-05-13T19:42:14+0800
- Task brief: `TaskAndReport/2026-05-13T19-33-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-AI-JSON-Repair_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Production entered: yes, read-only validation plus the exactly one upload authorized by the task brief.
- Recommendation: pass for the assigned validation boundary; Director decides acceptance and any release decision.

## Validation Scope

Executed the task brief's exactly-one controlled upload validation for:

- Sample: `/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`
- Expected size: `530205`
- Observed SHA-256: `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`
- Production HEAD observed before upload: `de2d23f Accept AI JSON repair and dispatch deployment`

No second upload, pressure/batch/soak test, failed-task repair, reparse, re-AI, cleanup, destructive mutation, model operation, sample mutation, L3 validation, production-readiness claim, or release-readiness claim was performed.

## Commands And Exit Codes

| Command | Workspace | Exit | Key output |
| --- | --- | ---: | --- |
| `git status --short --branch` | development | 0 | Branch `development-engineer/p0-post-validation-ollama-mineru-blockers`; dirty pre-existing workspace observed. |
| Required docs and task brief reads | development | 0 | Read role docs, PRD, test policy/matrix, repository structure, task ledger, task brief, and prerequisite reports/reviews. |
| `git status --short --branch` | production | 0 | `## main...origin/main`; `M docker-compose.override.yml`. |
| `git log -1 --oneline` | production | 0 | `de2d23f Accept AI JSON repair and dispatch deployment`. |
| `docker compose ps` | production | 0 | `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy. |
| `bash ops/runtime-ownership-status.sh` | production | 0 | Upload env matched expected MinerU/Ollama/fallback settings; dependency health blocking false; Ollama chat ok; active-task clean except historical AI failures. |
| `curl -fsS http://localhost:8081/__proxy/upload/health` | production | 0 | `{"ok":true,"service":"upload-server"}`. |
| `curl .../ops/dependency-health?mineruSubmitProbe=true` | production | 0 | `ok=true`, `blocking=false`, MinerU submit probe 202, Ollama `chatOk=true`. |
| `curl .../ops/mineru/active-task` | production | 0 | No active/current/queued/drift/takeover tasks; only historical AI failures listed. |
| `curl .../ops/mineru/admission-circuit` | production | 0 | Circuit `closed`, `open=false`, counts all zero after validation. |
| `curl -sS http://127.0.0.1:11434/api/ps` | production | 0 | `qwen3.5:9b` resident. |
| `stat`, `shasum -a 256`, `file` on sample | production | 0 | Size `530205`, expected SHA-256 matched, PDF 1.7. |
| Authorized single `POST /__proxy/upload/tasks` with `materialId=validation-json-repair-1778672290` | production | 0 | HTTP 200, created task `task-1778672291622`. |
| API polling via `GET /__proxy/db/tasks/:id`, `/materials/:id`, `/ai-metadata-jobs/:id`, task events, active-task, admission-circuit | production | 0 | Final task/material/AI job reached review boundary. |
| Playwright UI reads for task detail/list | production | 0 | Final detail/list both displayed review-pending wording. Screenshots saved under `/tmp/luceon-task98-*.png`. |
| `docker compose logs --tail=300 upload-server | rg ...` | production | 0 | Found task/job lifecycle, misjudged failed correction, artifact manifest write, AI job completion/backfill. |

## Runtime Evidence

Exactly one upload was performed:

- Task: `task-1778672291622`
- Material: `validation-json-repair-1778672290`
- Object: `originals/validation-json-repair-1778672290/source.pdf`
- MinerU task: `4affdec7-13aa-4a28-806d-07e71aad536d`
- AI job: `ai-job-1778672312564-0b2f`

Final DB/API state:

- Task: `state=review-pending`, `stage=review`, `progress=100`, message `AI 识别完成: review-pending (待人工复核)`.
- Material: `status=reviewing`, `mineruStatus=completed`, `aiStatus=analyzed`, processing stage `review`, processing message `AI 识别完成，待人工复核`.
- AI job: `state=review-pending`, `progress=100`, provider `ollama`, model `qwen3.5:9b`, message `AI 识别完成 (106485ms)`, `needsReview=true`, confidence `30`.
- AI output was non-skeleton metadata: title `多边形错题集`, subject `数学`, grade `八年级`, material type `试卷`.
- Repair evidence: first pass had `failureKind=schema_invalid`, `schemaInvalid=true`; deterministic repair mode `deterministic-draft-normalization`; `aiClassificationRepairSucceeded=true`; `aiClassificationDeterministicRepairSucceeded=true`; AI job phase `repair-deterministic-succeeded`.

Task event timeline:

- `2026-05-13T11:38:12.948Z`: MinerU submitted, internal ID `4affdec7-13aa-4a28-806d-07e71aad536d`.
- `2026-05-13T11:38:12.997Z`: transient worker failed due `log-observation-unreadable`.
- `2026-05-13T11:38:22.381Z`: misjudged failed corrected; MinerU still processing.
- `2026-05-13T11:38:22.401Z`: second transient resume failure with same log-observation issue.
- `2026-05-13T11:38:32.417Z`: misjudged failed corrected again; MinerU completed and result pull started.
- `2026-05-13T11:38:32.556Z`: parsed artifacts saved under `parsed/validation-json-repair-1778672290/`, count `21`.
- `2026-05-13T11:38:32.565Z`: AI job created.
- `2026-05-13T11:38:42.457Z`: Ollama `qwen3.5:9b` request started.
- `2026-05-13T11:40:28.925Z`: Ollama response succeeded.
- `2026-05-13T11:40:28.934Z`: `ai-provider-repair-deterministic-succeeded`.
- `2026-05-13T11:40:28.937Z`: `ai-provider-success`, terminal review-pending.

Final UI evidence:

- Task detail page `/cms/tasks/task-1778672291622`: `当前状态=待复核`, `当前阶段=review`, `下一步动作=需人工审核`, message `AI 识别完成: review-pending (待人工复核)`.
- Task list page `/cms/tasks`: top task shows `待复核`, `状态一致`, `MinerU 已完成，但本次未捕获可归因业务进度日志`, `AI 识别完成: review-pending (待人工复核)`; counters showed `处理中 0`, `待复核 25`, `已失败 3`.

Final operational evidence:

- MinerU active-task diagnostics clean: no active task, current task, queued tasks, drift tasks, submit-retryable tasks, or takeover-required tasks.
- Admission circuit closed: `open=false`, counts `parsePending=0`, `parseRunning=0`, `aiPending=0`, `aiRunning=0`, `activeTaskClean=true`.
- Ollama `/api/ps` showed `qwen3.5:9b` resident.

## Findings

1. The Task 95 LaTeX/invalid JSON repair failure did not recur in this validation. The first Ollama pass was schema-invalid, but deterministic draft normalization repaired it and the job reached `review-pending`.
2. The terminal AI result is non-skeleton and reviewable: it contains concrete title/subject/grade/type metadata and controlled classification fields, with human review required because of low confidence/taxonomy mismatches.
3. MinerU completed and persisted 21 parsed artifacts, but the progress semantics remain imperfect: the UI and metadata still report `MinerU 已完成，但本次未捕获可归因业务进度日志`, and the task experienced transient false `worker-failed` events caused by `log-observation-unreadable`. The recovery path corrected those false failures without manual repair.
4. Runtime ended clean after the validation: no active parse/AI task remained and the admission circuit was closed.

## Not Executed

- No second upload or broader sample run: explicitly forbidden by the task brief.
- No failed-task repair, reparse, re-AI, cleanup, destructive command, service restart, rebuild, model operation, or volume mutation: outside TestAcceptanceEngineer authorization.
- No production-readiness or release-readiness declaration: Director-owned decision.

## Risks And Residual Issues

- MinerU progress/log observability still has a diagnostic-only boundary for this fast-complete sample. It did not block final success here, but it can still create transient false failed events and confusing operator-visible history.
- The AI result is intentionally `review-pending` with `needsReview=true` and confidence `30`; this is a pass for reaching the safe review boundary, not an auto-acceptance of metadata quality.
- Historical failed AI tasks remain visible in diagnostics; they were not repaired or retried.

## Recommendation

Pass recommendation for the assigned validation boundary:

- Exactly one authorized upload was executed.
- The task reached `review-pending`.
- The AI JSON repair/finalization path succeeded after a schema-invalid first pass.
- The result is non-skeleton and preserved for human review.
- Runtime was clean at the end of validation.

Director review is required for final acceptance and any next task or release decision.
