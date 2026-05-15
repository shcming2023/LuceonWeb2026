# TestAcceptanceEngineer Report: P1 One Real PDF Post-Recovery Validation

- Task ID: `TASK-20260515-123250-P1-One-Real-PDF-Post-Recovery-Validation`
- Based on task brief: `TaskAndReport/2026-05-15T12-32-50+0800_P1-One-Real-PDF-Post-Recovery-Validation_TASK.md`
- Based on user decision: `TaskAndReport/2026-05-15T12-27-04+0800_P1-Release-Boundary-Decision-After-Final-Refresh_DECISION.md`
- Report time: 2026-05-15T12:44:00+0800
- Role: `TestAcceptanceEngineer`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`

## Outcome

`ONE_REAL_PDF_REVIEW_READY_WITH_BOUNDARY_NOTE`

Exactly one real PDF was uploaded through the production upload endpoint and reached manual review state:

- Source file: `/Users/concm/prod_workspace/Luceon2026/testpdf/向树叶学习：人工光合作用.pdf`
- Size: `86884` bytes
- SHA-256: `2230acbb40524e1de80f1ebe57a13c5f41db353e15c6727f5ebb97383154e16c`
- Upload time: `2026-05-15T12:37:05+0800`
- Created task: `task-1778819826484`
- Created material: `mat-1778819825152`
- MinerU task: `d57e4095-ef63-41b2-b060-35fda4ac5db1`
- AI job: `ai-job-1778819849438-1c43`
- Final task state: `state=review-pending`, `stage=review`, `progress=100`
- Final material state: `status=reviewing`, `mineruStatus=completed`, `aiStatus=analyzed`

Recommendation: `pass` for this task's one-real-PDF post-recovery validation boundary. Director still owns final acceptance and any release decision.

## Boundary Note For Director

I did not manually call `dependency-health?mineruSubmitProbe=true`, did not run `RUN_MINERU_SUBMIT_PROBE=1`, and did not run the helper with `--submit-probe`.

However, the production non-Markdown upload route itself performs a hard dependency gate with `mineruSubmitProbe: true` before accepting a PDF upload. This is visible in `server/upload-server.mjs` around the `POST /tasks` dependency gate:

```js
const requiresMineruSubmitAdmission = extLower !== 'md';
const health = await checkDependencyHealth(undefined, {
  mineruSubmitProbe: requiresMineruSubmitAdmission,
});
```

Runtime evidence confirms this internal gate created a synthetic MinerU health-probe task at upload start:

- Admission circuit `lastSubmitProbe.taskId`: `a9c55f8a-10c0-440c-97f0-ab5098155a7a`
- Probe file name: `luceon-health-probe`
- Probe status: `completed`
- Probe created/completed: `2026-05-15T04:37:05.198572Z` to `2026-05-15T04:37:06.059028Z`
- Admission circuit remained `state=closed`

This means the Director should explicitly decide how to record the task-brief boundary: the tester did not run an extra/manual submit-probe, but the authorized real PDF upload path currently includes one internal submit-probe by design for non-Markdown admission.

## Preflight

Development workspace:

- `git status --short --branch` -> exit `0`, `## main...origin/main`.

Production workspace:

- `git status --short --branch && git log -1 --oneline` -> exit `0`.
- Branch/HEAD: `main...origin/main`, `1716add Dispatch dependency health production validation`.
- Existing production dirty files were observed and not modified.

Read-only production preflight before upload:

- `GET /__proxy/upload/health` -> exit `0`, `{"ok":true,"service":"upload-server"}`.
- `GET /__proxy/upload/ops/dependency-health?ollamaChatProbe=true` -> exit `0`, `ok=true`, `blocking=false`, MinerU submit probe `enabled=false`, Ollama `resident-chat-succeeded`.
- `GET /__proxy/upload/ops/mineru/admission-circuit` -> exit `0`, `open=false`, `state=closed`.
- `GET /__proxy/upload/ops/mineru/active-task` -> exit `0`, no active/current/queued/takeover-required work; historical AI failures remained visible.
- Direct MinerU `/health` -> exit `0`, `status=healthy`, `queued_tasks=0`, `processing_tasks=0`.

No preflight blocker was found.

## Execution Evidence

PDF source listing:

- `find testpdf -maxdepth 1 -type f -iname '*.pdf' -exec stat -f '%z %N' {} \; | sort -n` -> exit `0`.
- Selected one small real PDF: `testpdf/向树叶学习：人工光合作用.pdf`, `86884` bytes.

Hash:

- `shasum -a 256 'testpdf/向树叶学习：人工光合作用.pdf'` -> exit `0`.
- SHA-256: `2230acbb40524e1de80f1ebe57a13c5f41db353e15c6727f5ebb97383154e16c`.

Exactly one upload:

```bash
curl -sS --fail-with-body --max-time 120 \
  -X POST \
  -F "file=@testpdf/向树叶学习：人工光合作用.pdf;type=application/pdf" \
  http://localhost:8081/__proxy/upload/tasks
```

- Exit: `0`.
- Response: `ok=true`.
- `taskId=task-1778819826484`
- `materialId=mat-1778819825152`
- `objectName=originals/mat-1778819825152/source.pdf`
- `fileName=向树叶学习：人工光合作用.pdf`
- `provider=minio`
- `mimeType=application/pdf`

## Runtime Progress Evidence

Initial observation after upload:

- Active task: `task-1778819826484`
- `state=running`, `stage=mineru-processing`, `progress=50`
- MinerU task: `d57e4095-ef63-41b2-b060-35fda4ac5db1`
- Direct MinerU `/tasks/d57e4095-ef63-41b2-b060-35fda4ac5db1`: `status=processing`, `error=null`.
- Direct MinerU `/health`: `processing_tasks=1`.
- UI/task message said `MinerU 正在处理，但日志观测滞后：backend=pipeline`; metadata marked this as a diagnostic warning, not failure.

MinerU completion:

- Direct MinerU task became `status=completed`, `error=null`.
- Completion time: `2026-05-15T04:37:29.339718Z`.
- DB task moved to `state=ai-running`, `stage=ai`, `progress=100`.
- Material moved to `mineruStatus=completed`, `processingMsg=MinerU 解析完成，等待 AI 元数据识别`.

AI completion:

- Polling reached terminal/manual-review state at about `60` seconds after observation start.
- DB task: `state=review-pending`, `stage=review`, `progress=100`, `message=AI 识别完成: review-pending (待人工复核)`.
- Material: `status=reviewing`, `mineruStatus=completed`, `aiStatus=analyzed`.
- AI job: `state=review-pending`, `progress=100`, `providerId=ollama`, `model=qwen3.5:9b`, `message=AI 识别完成 (61563ms)`, `needsReview=true`.
- Parsed artifacts were recorded:
  - `markdownObjectName=parsed/mat-1778819825152/full.md`
  - `parsedFilesCount=8`
  - `artifactManifestObjectName=parsed/mat-1778819825152/artifact-manifest.json`
  - `zipObjectName=parsed/mat-1778819825152/mineru-result.zip`
- AI metadata was recorded with `confidence=30`, `needsReview=true`, and proposed-new-tags review requirement. This is consistent with manual review readiness rather than automatic final acceptance.

Final runtime cleanup/readiness observation:

- `GET /__proxy/upload/ops/mineru/active-task` -> no active/current/queued/takeover-required task.
- Direct MinerU `/health` -> `status=healthy`, `queued_tasks=0`, `processing_tasks=0`, `completed_tasks=3`, `failed_tasks=0`.
- `GET /__proxy/upload/ops/dependency-health?ollamaChatProbe=true` -> `ok=true`, `blocking=false`, MinerU submit probe `enabled=false`, Ollama `resident-chat-succeeded`.

## Not Executed

- No second PDF upload.
- No pressure, batch, soak, or large-file run.
- No cleanup, cancel, repair, retry, reparse, or re-AI.
- No Docker Compose action, rebuild, restart, DB/MinIO/Ollama/MinerU mutation, config/secret/model/sample mutation, GitHub fetch/pull/push, PRD/PROJECT_STATE/HANDOFF/role-contract edit, or readiness/L3/pressure PASS/go-live claim.
- No UI/browser UAT was performed because the task allowed terminal observation and the DB/runtime state reached manual review.

## Risks / Residual Issues

- The real post-recovery path works for this one small PDF, but this is not pressure, batch, large-file, L3, production-readiness, or go-live evidence.
- The non-Markdown upload path internally runs a MinerU submit-probe as an admission gate. This should be reviewed against task wording and future acceptance-task wording so "no submit-probe" does not conflict with "upload a real PDF through the production route".
- The MinerU log observer still recorded `fast-complete-no-business-signal` for this small file because MinerU completed before an attributable business progress log was captured. This did not block completion, but it remains an observability limitation for manual progress interpretation.
- AI result required manual review with low confidence and proposed new tags. This is acceptable for review-ready validation but not an automatic catalog acceptance.
- Historical `failed/ai` tasks remain visible and were not repaired or retried.

## Director Decision Needed

Yes.

Director should decide whether to accept this as `ONE_REAL_PDF_REVIEW_READY` within the authorized boundary, and separately how to record the internal submit-probe side effect of the production PDF upload route.
