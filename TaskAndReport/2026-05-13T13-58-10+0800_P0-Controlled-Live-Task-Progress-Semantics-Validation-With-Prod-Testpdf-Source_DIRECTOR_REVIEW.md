# Director Review: P0 Controlled Live Task Progress Semantics Validation With Prod Testpdf Source

Task:
`TASK-20260513-134116-P0-Controlled-Live-Task-Progress-Semantics-Validation-With-Prod-Testpdf-Source`

Reviewer:
Director

Review file:
`TaskAndReport/2026-05-13T13-58-10+0800_P0-Controlled-Live-Task-Progress-Semantics-Validation-With-Prod-Testpdf-Source_DIRECTOR_REVIEW.md`

Reviewed report:
`TaskAndReport/2026-05-13T13-41-16+0800_P0-Controlled-Live-Task-Progress-Semantics-Validation-With-Prod-Testpdf-Source_REPORT.md`

Review result:
`ACCEPTED_FAILED_VALIDATION_EVIDENCE_WITH_FOLLOW_UP_REQUIRED`

## Evidence Reviewed

- TestAcceptanceEngineer report for Task 86.
- Read-only production API recheck of task `task-1778651226016`.
- Read-only production API recheck of material `validation-progress-1778651225`.
- Read-only production API recheck of task events via `/__proxy/db/task-events?taskId=task-1778651226016`.
- Read-only production API recheck of `/__proxy/upload/ops/mineru/active-task?queryApi=true`.
- Code-path read of current progress observation and Ollama provider timeout handling:
  - `server/services/mineru/local-adapter.mjs`
  - `server/upload-server.mjs`
  - `server/services/ai/providers/ollama.mjs`

## Scope Judgment

Accepted. TestAcceptanceEngineer stayed inside the authorized boundary:

- exactly one upload was performed;
- the sample came from the user-corrected source `/Users/concm/prod_workspace/Luceon2026/testpdf`;
- preflight passed before upload;
- sample file was not mutated;
- no pressure test, second upload, failed-task repair, cleanup, destructive DB/MinIO/Docker volume/data mutation, model operation, broad restart, L3, pressure PASS, or release-readiness claim occurred.

## Validation Judgment

Failed validation evidence accepted.

The run is useful because it separates the current production-line blockers:

1. MinerU parse/storage path passed for the one controlled sample.
2. Operator-facing MinerU progress semantics were not demonstrated.
3. AI metadata recognition failed in the strict no-skeleton path because the Ollama provider request hit `UND_ERR_HEADERS_TIMEOUT` after about 30 seconds, despite the job-level provider timeout being `180000ms`.

## Accepted Facts

- Selected sample:
  `/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`
- Sample size: `530205` bytes.
- Sample SHA-256:
  `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`
- Upload created:
  - task `task-1778651226016`
  - material `validation-progress-1778651225`
  - object `originals/validation-progress-1778651225/source.pdf`
- MinerU completed:
  - `mineruTaskId=ae1231ab-a00c-481f-97b9-43acf3364959`
  - `markdownObjectName=parsed/validation-progress-1778651225/full.md`
  - `parsedFilesCount=21`
  - `artifactIncomplete=false`
- Final task state:
  - `state=failed`
  - `stage=ai`
  - `progress=100`
  - `message=AI 识别完成: failed`
- Final material state:
  - `status=failed`
  - `mineruStatus=completed`
  - `aiStatus=failed`
  - `metadata.processingMsg=AI 识别失败`
- Task metadata did not contain `mineruObservedProgress` or `mineruObservedProgress.progressSemantics` when rechecked.
- Task/material only retained generic `progressEventKey` values with `logStatus=missing` and empty activity/phase/window/page fields.
- Task events show two Ollama provider requests failed with `errorCauseCode=UND_ERR_HEADERS_TIMEOUT` at about 30 seconds:
  - first request duration about `30247ms`;
  - second request duration about `30506ms`;
  - request body path used provider `ollama`, model `qwen3.5:9b`, base URL `http://host.docker.internal:11434`, job timeout `180000ms`, and input length `3240`.
- Strict no-skeleton behavior was preserved. The AI failure did not silently degrade into skeleton metadata.
- Active-task diagnostics correctly classify the terminal task as historical AI failure and show no active/queued parse work.

## Rejected Or Pending Claims

Rejected for this run:

- task-page/API MinerU progress semantics are production-validated;
- Ollama residency plus dependency-health short smoke proves real metadata recognition readiness;
- this controlled upload is a release-readiness, L3, or pressure PASS signal.

Pending:

- production validation of useful task-page MinerU progress semantics;
- production validation that a small real PDF can complete the full upload -> MinerU -> MinIO -> Ollama -> review-pending path on the current accepted code path;
- any pressure retry or release-readiness decision.

## Director Diagnosis

This should not be treated as another sample-selection problem. The corrected sample path worked, and MinerU completed.

The AI failure has a concrete engineering signature: `server/services/ai/providers/ollama.mjs` currently creates an undici `Agent` with `headersTimeout: 30000` while the provider-level timeout is `180000ms`. For non-streaming `/api/chat`, a 30-second headers timeout can become the effective inference deadline if Ollama does not send response headers until generation completes. That explains why the events show `Timeout: 180000ms` but actual failure at about 30 seconds. Dependency-health uses a much smaller synthetic chat path and cannot substitute for this real metadata call.

The progress-semantics failure is separate. The live parse completed quickly, but the task should still provide explicit operator-facing truth: either real structured MinerU log progress, or a structured, provenance-bearing diagnostic that no business progress signal was captured for a fast completed task. A null `mineruObservedProgress` leaves the task page unable to explain whether the parsing was genuinely progressing, too fast to observe, or disconnected from the log observer.

## Required Follow-Up

Director issued:

- `TASK-20260513-135810-P0-Post-Validation-Ollama-And-MinerU-Progress-Blockers`

Assigned role:

- `DevelopmentEngineer`

## Next Actor

`DevelopmentEngineer`

## Next Action

Implement scoped code/test fixes for the two observed blockers:

1. align the Ollama provider runtime timeout contract so real non-streaming metadata inference is not unintentionally capped at 30 seconds;
2. ensure live task API/UI state exposes truthful MinerU progress semantics or a structured no-business-signal / fast-complete diagnostic rather than silently omitting `mineruObservedProgress`.

## Required Output

DevelopmentEngineer completion report with changed files, focused implementation summary, checks, evidence, skipped checks, residual risks, branch/HEAD, GitHub sync status, and whether another scoped production validation task is required.
