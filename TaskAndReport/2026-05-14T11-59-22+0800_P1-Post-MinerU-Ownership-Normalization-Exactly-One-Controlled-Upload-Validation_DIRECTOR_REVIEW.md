# Director Review: P1 Post MinerU Ownership Normalization Exactly One Controlled Upload Validation

- Review time: 2026-05-14T11:59:22+0800
- Reviewed task: `TASK-20260514-113727-P1-Post-MinerU-Ownership-Normalization-Exactly-One-Controlled-Upload-Validation`
- Reviewed report: `TaskAndReport/2026-05-14T11-37-27+0800_P1-Post-MinerU-Ownership-Normalization-Exactly-One-Controlled-Upload-Validation_REPORT.md`
- Reviewer: Director
- Result: `ACCEPTED_ONE_UPLOAD_VALIDATION_PASS_WITH_DETAIL_PROGRESS_AND_CONSOLE_NOISE_DEBT`

## Scope Judgment

Accepted.

TestAcceptanceEngineer stayed within the authorized boundary: exactly one production UI upload was created from `/Users/concm/prod_workspace/Luceon2026/testpdf`, no second upload was created, and no pressure/batch/soak, cleanup, repair/reparse/re-AI, direct DB/MinIO mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, model/config/secret/sample mutation, readiness, L3, pressure PASS, or go-live claim was made.

This review accepts the bounded validation evidence. It does not declare production readiness, L3, pressure PASS, release readiness, or production上线.

## Evidence Accepted

Accepted validation evidence:

- selected sample: `/Users/concm/prod_workspace/Luceon2026/testpdf/走向成功_英语_二模卷16篇.pdf`;
- sample size: `3457503` bytes;
- sample SHA-256: `b3e00ad1c7f7afff4bdae1b484abad941af618fd80b9b5f9f22d69848968eaac`;
- exactly one UI upload created task `task-1778730187749`;
- material id `4282929344122708`;
- MinerU task id `fb5c5774-534c-4a7c-bc7a-d5546857cd1a`;
- AI job id `ai-job-1778730259599-2d2f`;
- final task state `review-pending`, stage `review`, progress `100`;
- final material state `reviewing`, `mineruStatus=completed`, `aiStatus=analyzed`;
- parsed artifact count `25`;
- task state sequence included `pending -> running -> ai-pending -> ai-running -> review-pending`;
- list page surfaced real MinerU progress during processing, including batch/page/phase text such as `批次 1/1，页 24/24`, `表格识别`, `模型识别`, `OCR 检测`, and `OCR 识别`;
- final UI state was coherent and understandable: `待复核`, `review`, `已生成 (Markdown)`, and `需人工审核`.

Director spot-check confirmed:

- production remains at `fb2627c` at review time;
- `luceon-mineru` and `luceon-sidecar` are present;
- PID `61436` remains the single `8083` listener, with cwd `/Users/concm/prod_workspace/Luceon2026` and fd1/fd2 attached to `/Users/concm/ops/logs/mineru-api.log` and `/Users/concm/ops/logs/mineru-api.err.log`;
- MinerU `/health` is healthy with no queued or processing tasks;
- `/__proxy/upload/ops/mineru/admission-circuit` is closed;
- `/__proxy/upload/ops/mineru/active-task` has no active/current/queued/drift/takeover work;
- `/__proxy/upload/ops/dependency-health?ollamaChatProbe=true` is `ok=true`, `blocking=false`, with Ollama `qwen3.5:9b` resident and chat probe OK;
- `/tmp/luceon-task122-observations.json` and the Task 122 screenshots exist;
- the observation artifact contains 26 fresh active-progress global observations and 52 observations attributed to `task-1778730187749`;
- screenshot spot-check confirmed the list page displayed MinerU page/batch progress during processing and the final detail page displayed a coherent `待复核` review state.

## Residual Debt

Two issues remain and should be handled before broader validation or any release-readiness discussion:

1. Detail page progress parity gap:
   - Task list page and canonical observability endpoints showed fine-grained MinerU progress.
   - Task detail page only showed high-level lifecycle state during processing and did not surface fine-grained page/batch/phase progress.

2. Browser console noise:
   - TestAcceptanceEngineer captured repeated `503 Service Unavailable` resource errors and initial `[db-sync]` warnings.
   - They did not block this validation, but they can reduce operator trust and should be diagnosed or narrowed.

## Not Accepted

This review does not accept or authorize:

- pressure, batch, soak, or long-run validation;
- a second upload;
- cleanup, repair, reparse, re-AI, or historical task mutation;
- destructive DB/MinIO/Docker volume/data operations;
- Docker down/down-v;
- MinerU/Ollama/supervisor mutation;
- model/config/secret/sample mutation;
- production readiness;
- release readiness;
- L3;
- pressure PASS;
- go-live readiness or production上线.

## Next Step

Director issues Task 123 to DevelopmentEngineer for a scoped code-level follow-up: make task detail MinerU progress display consistent with list/canonical progress evidence where the data is already available, and diagnose or reduce the repeated browser console `503`/db-sync noise without hiding real backend failures.
