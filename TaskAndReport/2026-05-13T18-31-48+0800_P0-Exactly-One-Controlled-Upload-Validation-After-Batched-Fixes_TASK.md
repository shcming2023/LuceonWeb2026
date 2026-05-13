# Task: P0 Exactly One Controlled Upload Validation After Batched Fixes

Assignee:
TestAcceptanceEngineer

Issued by:
Director

Issued at:
2026-05-13T18:31:48+0800

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

Production test PDF source:
/Users/concm/prod_workspace/Luceon2026/testpdf

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-13T18-31-48+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes_TASK.md

Expected report:
TaskAndReport/2026-05-13T18-31-48+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes_REPORT.md

## Required Reading Before Execution

- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/test-acceptance-engineer.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- docs/codex/TEST_POLICY.md
- docs/codex/TEST_MATRIX.md
- docs/codex/REPOSITORY_STRUCTURE.md
- docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md
- TaskAndReport/README.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-13T14-46-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment_REPORT.md
- TaskAndReport/2026-05-13T15-17-15+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment_DIRECTOR_REVIEW.md
- TaskAndReport/2026-05-13T16-31-04+0800_P0-Batched-AI-And-MinerU-Fixes-Production-Deployment-And-Runtime-Validation_REPORT.md
- TaskAndReport/2026-05-13T18-31-48+0800_P0-Batched-AI-And-MinerU-Fixes-Production-Deployment-And-Runtime-Validation_DIRECTOR_REVIEW.md

## Background

Task 90 performed exactly one controlled upload after Task 87 deployment. It produced useful failed-validation evidence:

- MinerU completed and stored 21 parsed artifacts.
- The previous 30s Ollama `UND_ERR_HEADERS_TIMEOUT` did not recur.
- AI produced real Ollama responses and one JSON repair success.
- The same AI job later ran another pass and failed strict no-skeleton repair, leaving task/material failed.
- Task-page/API MinerU semantics surfaced diagnostic evidence, but the final visible wording was still not ideal for terminal completed parse evidence.

Task 91 then fixed the AI duplicate-processing risk at code/test level.

Task 93 then fixed terminal MinerU diagnostic precedence at code/test level.

Task 94 deployed both fixes to production and passed non-destructive runtime validation at production HEAD `50e5621`.

This task verifies the deployed production behavior with exactly one new controlled upload.

## Objective

Perform exactly one controlled upload of the known production test PDF and observe whether the current deployed production path now behaves correctly:

1. MinerU parse completes and stores parsed artifacts.
2. Task page/API semantics show terminal MinerU completion or the improved terminal diagnostic wording when parse is complete.
3. AI metadata processing does not process the same job twice after an accepted finalization path.
4. The terminal task/material state and AI job evidence are recorded clearly, whether pass or fail.

This is a validation task only. It is not a pressure test and not a production-readiness declaration.

## Authorized Sample

Use exactly this file:

`/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`

Expected read-only sample facts from prior validation:

- size: `530205` bytes
- SHA-256: `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`

Before upload, verify the file exists, size, hash, and PDF type. Do not modify, rename, move, copy into the repository, normalize, compress, or delete the sample file.

## Required Preflight

In development workspace:

```bash
git status --short --branch
```

Do not fetch, pull, push, merge, or reset GitHub from the TestAcceptanceEngineer thread unless a Director task explicitly requires it. Director owns routine GitHub synchronization.

In production deployment path:

```bash
git status --short --branch
git log -1 --oneline
docker compose ps
curl -fsS http://localhost:8081/__proxy/upload/health
curl -sS --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=1&ollamaChatProbe=1'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
curl -sS --max-time 10 http://127.0.0.1:11434/api/ps
stat -f '%z %N' '/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf'
shasum -a 256 '/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf'
file '/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf'
```

Stop and write a blocked report if any of the following is true:

- production HEAD is not `50e5621` or a later Director-approved fast-forward;
- dependency-health is blocking;
- MinerU admission circuit is open;
- active/current/queued/takeover parse or AI work exists;
- Docker services are unhealthy;
- sample hash or size differs from the authorized facts;
- production local override is unsafe or strict AI/model settings are missing.

## Authorized Upload

Only after safe preflight, perform exactly one upload.

Use a unique material id with prefix:

`validation-batched-fixes-`

Use the same endpoint pattern as Task 90:

```bash
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  -X POST http://localhost:8081/__proxy/upload/tasks \
  -H "X-Request-Id: tae-task95-$(date +%s)" \
  -F "file=@/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf;type=application/pdf" \
  -F "materialId=validation-batched-fixes-$(date +%s)" \
  -F "backend=pipeline"
```

Record the exact `taskId`, `materialId`, `objectName`, and HTTP status.

Do not retry the upload if it succeeds and later task processing fails. Do not perform a second upload.

If the upload request itself fails before creating a task, stop and report the exact response and whether any task/material was created.

## Required Observation

Observe the task until a terminal state is reached, or until a clearly justified timeout is hit and reported.

Collect evidence from:

- production task API;
- material API;
- AI job/event evidence if exposed by existing endpoints or reports;
- `/ops/mineru/active-task`;
- `/ops/mineru/admission-circuit`;
- task page and task list UI under `/cms/`.

The UI observation is important. The report must include task-page/task-list visible wording for:

- current status;
- current stage;
- parse artifact availability;
- MinerU visible progress/diagnostic semantics;
- AI visible message;
- terminal state and next-action wording.

If browser automation is not available or times out, record the exact reason and collect the closest API evidence instead. Do not hide the UI observation gap.

## Specific Questions To Answer

1. Did MinerU complete and store parsed artifacts?
2. Did terminal MinerU wording prefer completion/artifact evidence instead of stale `log-observation-unreadable` in-flight wording?
3. Did AI reach `review-pending` or another acceptable non-skeleton terminal result?
4. If AI failed, is there evidence of duplicate processing of the same AI job after successful finalization?
5. Did any 30s `UND_ERR_HEADERS_TIMEOUT` recur?
6. Did the task page provide useful operator semantics during and after processing?
7. Were admission circuit and active-task diagnostics clean after terminal state?

## Forbidden Actions

Do not perform:

- second upload;
- pressure test, 24-PDF test, soak test, or batch test;
- failed-task repair;
- reparse or re-AI of historical tasks;
- DB, MinIO, Docker volume, task, artifact, log, or data deletion;
- Docker `down`, `down -v`, prune, broad restart, rollback, or rebuild;
- model pull/delete/replace/restart/kill/reload;
- secret, timeout, override, PRD, role-contract, or public API mutation;
- sample-file mutation or copying samples into the repository;
- production-readiness, L3, pressure PASS, release-readiness, or external/multi-user release claim.

## Required Report

Write:

`TaskAndReport/2026-05-13T18-31-48+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md` locally with:

- status `已回报待 Director 审查` or blocked/failed equivalent;
- `Next Actor=Director`;
- report path;
- task id/material id/AI job id if created;
- concise evidence summary;
- explicit statement that no forbidden action was performed.

Do not push to GitHub from the TestAcceptanceEngineer thread. Director will review and synchronize task records.

Report must include:

- based-on task brief path;
- development branch/status;
- production HEAD;
- preflight evidence;
- exact upload command and exit code;
- task/material/AI ids;
- task-page/task-list visible evidence;
- API timeline;
- final task/material/AI status;
- MinerU artifact and semantic evidence;
- AI duplicate-processing evidence or absence;
- post-terminal admission/active-task evidence;
- skipped checks and exact reasons;
- forbidden actions not performed;
- risks, blockers, and residual debt;
- clear recommendation to Director.

## Acceptance Criteria

The task is acceptable as evidence if:

- exactly one upload is attempted after safe preflight;
- evidence is complete enough to judge MinerU terminal semantics and AI finalization behavior;
- all forbidden operations are avoided;
- pass/fail/blocked status is recorded honestly without production-readiness or pressure claims.
