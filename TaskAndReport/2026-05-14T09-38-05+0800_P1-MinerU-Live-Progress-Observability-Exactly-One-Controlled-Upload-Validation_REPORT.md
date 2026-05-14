# TestAcceptanceEngineer Report: P1 MinerU Live Progress Observability Exactly One Controlled Upload Validation

- Task ID: `TASK-20260514-093805-P1-MinerU-Live-Progress-Observability-Exactly-One-Controlled-Upload-Validation`
- Report time: 2026-05-14T09:58:00+0800
- Role: TestAcceptanceEngineer
- Based on Director task brief: `TaskAndReport/2026-05-14T09-38-05+0800_P1-MinerU-Live-Progress-Observability-Exactly-One-Controlled-Upload-Validation_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Entered production workspace: yes

## Result

Exactly one authorized PDF upload was performed after preflight passed.

The task reached `review-pending`, material reached `reviewing`, MinerU completed, parsed artifacts were produced, and AI metadata completed to human review.

Recommendation: `PASS_WITH_RESIDUAL_OBSERVABILITY_GAP`.

The validation did not prove live attributable MinerU business-progress observability after sidecar attach. During the live parse, the operator-visible task stayed understandable and did not falsely fail, but MinerU progress remained diagnostic-only:

- configured log-channel ownership stayed `summaryState=empty`;
- `luceon-sidecar` stayed `observed-recent`;
- task/material first showed `log-observation-empty` while MinerU API was processing;
- final material recorded `fast-complete-no-business-signal`;
- global observation continued to use stale fallback `uat/scratch/mineru-api.log` content and was marked stale/diagnostic.

This is a bounded one-upload validation only. It is not pressure, batch, soak, L3, production readiness, release readiness, go-live readiness, or production上线.

## Branch / HEAD

Development workspace:

- `git status --short --branch` exit 0.
- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`.
- Existing modified/untracked files were present from the shared multi-role workspace.

Production workspace:

- `git status --short --branch` exit 0: `## main...origin/main`, with local modified `docker-compose.override.yml`.
- `git log -1 --oneline` exit 0: `a516546 Dispatch live MinerU progress validation`.

## Selected Sample

- Path: `/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`
- Size: `530205` bytes
- SHA-256: `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`
- Qualification: small/medium PDF from the authorized production `testpdf` folder; chosen to avoid pressure, long-run, or batch validation.

## Preflight Evidence

All stop-condition checks passed before upload:

- `docker compose ps` exit 0: `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` healthy.
- `tmux ls || true` exit 0: `luceon-sidecar` present.
- `lsof -nP -iTCP:8081 -iTCP:8083 -iTCP:11434 -iTCP:19001 -sTCP:LISTEN || true` exit 0: upload on `8081`, MinerU on `8083`, Ollama on `11434`, MinIO console on local-only `127.0.0.1:19001`.
- `curl -fsS http://localhost:8081/__proxy/upload/health` exit 0: upload-server OK.
- `curl -fsS '.../ops/dependency-health?mineruSubmitProbe=true&ollamaChatProbe=true'` exit 0: `ok=true`, `blocking=false`, MinerU submit probe `202`, Ollama `qwen3.5:9b` resident and `chatOk=true`.
- `curl -fsS .../ops/mineru/admission-circuit` exit 0: circuit `closed`, `open=false`.
- `curl -fsS .../ops/mineru/active-task` exit 0: no active/current/queued/drift/takeover tasks; only unchanged historical AI failures.
- `curl -fsS .../ops/mineru/log-channel-ownership` exit 0: `summaryState=empty`, configured logs empty/readable, `sidecar.runningState=observed-recent`.
- `curl -fsS .../ops/mineru/global-observation` exit 0: stale fallback observation from `uat/scratch/mineru-api.log`, `activityLevel=log-observation-stale`, `attribution=unattributed`.
- `curl -fsS http://127.0.0.1:8083/health` exit 0: MinerU `healthy`, queued `0`, processing `0`.
- `curl -fsS http://127.0.0.1:11434/api/version` exit 0: Ollama `0.23.2`.
- `curl -fsS http://127.0.0.1:11434/api/ps` exit 0: `qwen3.5:9b` resident.

## Upload

Upload command:

```bash
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  -H "X-Request-Id: task115-live-progress-$(date +%s)" \
  -F "materialId=task115-live-progress-1778723642" \
  -F "backend=pipeline" \
  -F "file=@/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf;type=application/pdf" \
  http://localhost:8081/__proxy/upload/tasks
```

Result:

- Exit 0
- HTTP status `200`
- Task ID: `task-1778723642905`
- Material ID: `task115-live-progress-1778723642`
- Raw object: `originals/task115-live-progress-1778723642/source.pdf`

Exactly one PDF upload was performed.

## Runtime Evidence

Initial live observation during MinerU processing:

- Task state: `running`
- Stage: `mineru-processing`
- Progress: `50`
- Message: `MinerU 已提交/正在处理，但暂无可归因业务日志`
- MinerU task ID: `7a6f3b04-0bf3-493c-96d8-6eed86250331`
- `mineruObservedProgress.activityLevel=log-observation-empty`
- `observationStale=true`, reason `log file exists but is empty`
- `mineruLogObservationWarning.kind=mineru-log-observation-diagnostic-only`
- `log-channel-ownership.summaryState=empty`
- `sidecar.runningState=observed-recent`
- `global-observation.activityLevel=log-observation-unattributed`, stale fallback, attributed live-active to this task only as a diagnostic stale signal.

Polling transition:

- MinerU completed quickly and the task moved to `ai-running`.
- Parsed artifacts were produced before AI: `parsedFilesCount=21`.
- No active MinerU task remained after MinerU completion.
- AI ran through Ollama `qwen3.5:9b`.

Terminal state:

- Task state: `review-pending`
- Task stage: `review`
- Task progress: `100`
- Task message: `AI 识别完成: review-pending (待人工复核)`
- Material status: `reviewing`
- Material `mineruStatus=completed`
- Material `aiStatus=analyzed`
- AI job ID: `ai-job-1778723655852-cdb7`
- AI job state: `review-pending`
- AI job message: `AI 识别完成 (63907ms)`
- AI confidence: `30`, `needsReview=true`
- Parsed prefix: `parsed/task115-live-progress-1778723642/`
- Markdown object: `parsed/task115-live-progress-1778723642/full.md`
- Artifact manifest: `parsed/task115-live-progress-1778723642/artifact-manifest.json`
- ZIP object: `parsed/task115-live-progress-1778723642/mineru-result.zip`
- Parsed files count: `21`

Final observability evidence:

- `/ops/mineru/log-channel-ownership`: `summaryState=empty`; configured stdout/stderr logs empty/readable; `sidecar.runningState=observed-recent`.
- `/ops/mineru/global-observation`: stale fallback `uat/scratch/mineru-api.log`; `activityLevel=log-observation-stale`; `attribution=task-1778723642905`; `attributionMode=completed-window-backfill`; `terminalTaskState=review-pending`; `nonMutating=true`.
- Material terminal diagnostic: `fast-complete-no-business-signal`, reason `MinerU completed before Luceon captured an attributable business progress signal`.
- A stale `Predict 99%` fallback line was still present, but it was diagnostic/stale and not reliable live progress proof.

Final runtime surfaces:

- `curl -fsS '.../ops/dependency-health?mineruSubmitProbe=true&ollamaChatProbe=true'` exit 0: `ok=true`, `blocking=false`, MinerU submit probe `202`, Ollama resident and `chatOk=true`.
- `curl -fsS http://127.0.0.1:8083/health` exit 0: MinerU `healthy`, queued `0`, processing `0`.
- `curl -fsS .../ops/mineru/admission-circuit` exit 0: circuit `closed`, `open=false`.
- `curl -fsS .../ops/mineru/active-task` exit 0: no active/current/queued/drift/takeover tasks; only unchanged historical AI failures.
- `tmux ls || true` exit 0: `luceon-sidecar` still present.
- `docker compose ps` exit 0: core Docker services healthy.

## Browser-Visible Evidence

Browser check used Playwright against `http://localhost:8081/cms/tasks`.

- First `networkidle` attempt timed out with two 503 resource messages; rerun with `domcontentloaded` succeeded.
- List page HTTP status: `200`.
- List page showed the new task row:
  - file `2025_2026学年春季课程中数G8_提取.pdf`
  - task `task-17787236429...`
  - stage `review`
  - status `待复核`
  - badge `状态一致`
  - message `MinerU 已完成，但本次未捕获可归因业务进度日志`
  - message `AI 识别完成: review-pending (待人工复核)`
- Detail page URL: `http://localhost:8081/cms/tasks/task-1778723642905`.
- Detail page showed:
  - current state `待复核`
  - current stage `review`
  - artifact status `已生成 (Markdown)`
  - next action `需人工审核`
  - message `AI 识别完成: review-pending (待人工复核)`
  - internal diagnostics area includes state consistency, MinerU profile, AI task, and log observation.
- Screenshots:
  - `/tmp/luceon-task115-list.png`
  - `/tmp/luceon-task115-detail.png`

Interpretation: operator-facing list/detail semantics are understandable and not a false failure. They still explicitly communicate that MinerU completed without attributable business-progress logs.

## Pass / Fail / Block Recommendation

Recommendation to Director: `PASS_WITH_RESIDUAL_OBSERVABILITY_GAP`.

Pass boundary:

- exactly one PDF was uploaded;
- preflight was clean;
- task reached `review-pending`;
- material reached `reviewing`;
- MinerU completed and produced 21 parsed artifacts;
- AI metadata reached `review-pending`;
- browser list/detail showed understandable terminal state and no false terminal failed state.

Residual gap:

- sidecar attachment did not produce live attributable business-progress evidence for this sample;
- configured MinerU logs remained empty;
- global observation still depended on stale fallback content;
- final material recorded `fast-complete-no-business-signal`.

## Skipped Checks And Reasons

- No second upload: explicitly forbidden.
- No pressure, batch, soak, or long-run validation: explicitly forbidden.
- No cleanup, repair, reparse, re-AI, retry of historical tasks, or failed-task mutation: explicitly forbidden.
- No Docker restart/rebuild/down, DB/MinIO/Docker volume/data mutation, MinerU restart/ownership normalization, Ollama mutation, supervisor attach, config/secret/model/sample mutation: explicitly forbidden.
- No source build/lint/typecheck: no source code was modified and task did not require code validation.
- No L3, production-readiness, release-readiness, go-live, or production上线 claim: explicitly outside scope.

## Risks / Residual Issues / Next Suggestions

- The core runtime path works for this one sample, but the live business-progress observability objective remains unresolved.
- The sidecar is alive, but its configured log inputs remain empty; this points to MinerU stdout/stderr ownership or log-writer routing rather than task-state failure.
- Stale fallback `uat/scratch/mineru-api.log` can still confuse global observation unless surfaced strictly as stale diagnostic.
- Director decision is needed on whether to dispatch a scoped DevelopmentEngineer/Architect follow-up for MinerU log writer ownership, stale fallback exclusion, or MinerU runtime ownership normalization.

## Forbidden Operations Statement

No forbidden operation was performed: no second upload, no pressure/batch/soak, no cleanup/repair/reparse/re-AI, no historical task/material/artifact mutation, no destructive DB/MinIO/Docker volume/data operation, no MinerU restart/kill/ownership normalization, no Ollama mutation, no supervisor attach, no config/secret/model/sample mutation, no source/PRD/role/release truth change, no GitHub push, and no readiness/go-live claim.

