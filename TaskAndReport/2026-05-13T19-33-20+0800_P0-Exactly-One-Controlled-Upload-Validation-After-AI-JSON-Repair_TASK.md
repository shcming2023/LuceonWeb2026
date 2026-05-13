# Task: P0 Exactly One Controlled Upload Validation After AI JSON Repair

Assignee:
TestAcceptanceEngineer

Issued by:
Director

Issued at:
2026-05-13T19:33:20+0800

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
TaskAndReport/2026-05-13T19-33-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-AI-JSON-Repair_TASK.md

Expected report:
TaskAndReport/2026-05-13T19-33-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-AI-JSON-Repair_REPORT.md

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
- TaskAndReport/2026-05-13T18-31-48+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes_REPORT.md
- TaskAndReport/2026-05-13T19-13-44+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes_DIRECTOR_REVIEW.md
- TaskAndReport/2026-05-13T19-13-44+0800_P0-AI-Metadata-JSON-Repair-And-Schema-Reliability_REPORT.md
- TaskAndReport/2026-05-13T19-26-01+0800_P0-AI-Metadata-JSON-Repair-And-Schema-Reliability_DIRECTOR_REVIEW.md
- TaskAndReport/2026-05-13T19-26-01+0800_P0-AI-JSON-Repair-Production-Deployment-And-Runtime-Validation_REPORT.md
- TaskAndReport/2026-05-13T19-33-20+0800_P0-AI-JSON-Repair-Production-Deployment-And-Runtime-Validation_DIRECTOR_REVIEW.md

## Background

Task 95 proved that the controlled sample still failed after MinerU success and first-pass Ollama success. The failure mechanism was JSON Repair producing invalid JSON string escapes inside LaTeX-style evidence text.

Task 96 implemented and tested deterministic invalid JSON string escape repair while preserving strict no-skeleton behavior.

Task 97 deployed that code path to production and passed non-destructive runtime validation at production HEAD `de2d23f`.

This task validates the deployed behavior with exactly one new controlled upload.

## Objective

Perform exactly one controlled upload of the known production test PDF and observe whether the current deployed production path now reaches a trustworthy non-skeleton AI terminal result.

Specifically answer:

1. Did MinerU complete and store parsed artifacts?
2. Did the previous 30s `UND_ERR_HEADERS_TIMEOUT` recur?
3. Did the Task 95 invalid LaTeX escape JSON Repair failure recur?
4. Did AI reach `review-pending` or another acceptable non-skeleton terminal result?
5. If AI failed, what exact phase and evidence caused failure?
6. Did task-page/task-list UI show useful MinerU and AI semantics during and after processing?
7. Were admission circuit and active-task diagnostics clean after terminal state?

## Authorized Sample

Use exactly this file:

`/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`

Expected read-only sample facts:

- size: `530205` bytes;
- SHA-256: `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`.

Before upload, verify file exists, size, hash, and PDF type. Do not modify, rename, move, copy into the repository, normalize, compress, or delete the sample file.

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

- production HEAD is not `de2d23f` or a later Director-approved fast-forward;
- dependency-health is blocking;
- MinerU admission circuit is open;
- active/current/queued/takeover parse or AI work exists;
- Docker services are unhealthy;
- sample hash or size differs from the authorized facts;
- production local override is unsafe or strict AI/model settings are missing.

## Authorized Upload

Only after safe preflight, perform exactly one upload.

Use a unique material id with prefix:

`validation-json-repair-`

Use:

```bash
ts=$(date +%s); curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  -X POST http://localhost:8081/__proxy/upload/tasks \
  -H "X-Request-Id: tae-task98-${ts}" \
  -F "file=@/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf;type=application/pdf" \
  -F "materialId=validation-json-repair-${ts}" \
  -F "backend=pipeline"
```

Record the exact `taskId`, `materialId`, `objectName`, and HTTP status.

Do not retry the upload if it succeeds and later task processing fails. Do not perform a second upload.

If the upload request itself fails before creating a task, stop and report the exact response and whether any task/material was created.

## Required Observation

Observe until terminal state, or until a clearly justified timeout is reached and reported.

Collect evidence from:

- production task API;
- material API;
- AI job API;
- task events API;
- `/ops/mineru/active-task`;
- `/ops/mineru/admission-circuit`;
- upload-server logs for the created task/job only;
- task page and task list UI under `/cms/`.

UI observation must include task-page/task-list visible wording for:

- current status;
- current stage;
- parse artifact availability;
- MinerU visible progress/diagnostic semantics;
- AI visible message;
- terminal state and next-action wording.

If browser automation is unavailable or times out, record the exact reason and collect the closest API evidence instead. Do not hide UI observation gaps.

## Success / Failure Interpretation

Treat as a successful validation only if:

- exactly one upload was attempted after safe preflight;
- MinerU completed and parsed artifacts exist;
- AI reaches `review-pending`, `confirmed`, or another explicit non-skeleton trusted terminal result;
- strict no-skeleton behavior remains intact;
- no duplicate post-finalization AI processing occurs;
- no forbidden operation occurs.

Treat as failed but useful evidence if:

- MinerU succeeds but AI fails with a new parse/schema/repair/timeout reason;
- the LaTeX escape failure recurs;
- the task page/API semantics are insufficient;
- admission/active-task diagnostics become unsafe.

Do not declare production readiness, L3, pressure PASS, or release readiness in either case.

## Forbidden Actions

Do not perform:

- second upload;
- pressure/batch/soak/24-PDF test;
- failed-task repair;
- reparse or re-AI of historical tasks;
- DB, MinIO, Docker volume, task, artifact, log, or data deletion;
- Docker `down`, `down -v`, prune, broad restart, rollback, or rebuild;
- model pull/delete/replace/restart/kill/reload;
- secret, timeout, override, PRD, role-contract, public API, release truth, or model-selection mutation;
- sample-file mutation or copying samples into the repository;
- production-readiness, L3, pressure PASS, release-readiness, or external/multi-user release claim.

## Required Report

Write:

`TaskAndReport/2026-05-13T19-33-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-AI-JSON-Repair_REPORT.md`

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
- AI finalization and JSON repair evidence;
- whether Task 95 LaTeX escape failure recurred;
- post-terminal admission/active-task evidence;
- skipped checks and exact reasons;
- forbidden actions not performed;
- risks, blockers, and residual debt;
- clear recommendation to Director.

## Acceptance Criteria

The task is acceptable as evidence if:

- exactly one upload is attempted after safe preflight;
- evidence is complete enough to judge MinerU terminal semantics and AI JSON repair/finalization behavior;
- all forbidden operations are avoided;
- pass/fail/blocked status is recorded honestly without production-readiness or pressure claims.
