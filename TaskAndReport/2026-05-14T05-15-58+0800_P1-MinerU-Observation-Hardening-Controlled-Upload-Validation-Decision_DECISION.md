# User Decision: P1 MinerU Observation Hardening Controlled Upload Validation

- Recorded at: 2026-05-14T05:15:58+0800
- Role: Director
- Decision ID: `TASK-20260514-051558-P1-MinerU-Observation-Hardening-Controlled-Upload-Validation-Decision`
- Trigger: Task 102 Director review accepted scoped production deployment and non-destructive runtime-surface validation, but live upload behavior is not yet evidenced.
- Current production HEAD: `159d80e Accept MinerU log observation hardening`
- Sample source available for proposed validation: `/Users/concm/prod_workspace/Luceon2026/testpdf`
- Next Actor: User

## Current Facts

Task 101 fixed MinerU log-observation adjudication at code/test level: when MinerU API still says queued/pending/processing/running, unreadable or stale log observation should be diagnostic warning metadata instead of a terminal failure.

Task 102 deployed that accepted code path to production upload-server and confirmed non-destructive runtime surfaces:

- upload health ok;
- dependency-health `ok=true`, `blocking=false`;
- MinerU submit-probe `ok=true`, `status=202`;
- admission circuit closed/open=false;
- active-task clean except historical AI failures;
- Ollama `qwen3.5:9b` resident and `chatOk=true`;
- production source/container markers confirmed.

Task 102 did not upload a validation PDF because that was explicitly forbidden by the task brief.

## Decision Needed

The remaining question is whether to run a single controlled upload to verify the operator-visible behavior after the MinerU observation hardening deployment.

This matters because the original defect was not merely a health endpoint issue. It appeared on real tasks as transient false failed/self-corrected events and confusing task-page semantics. Deployment health alone cannot prove that the live page behavior is fixed.

## Options

### Option A: Authorize Exactly One Controlled Upload Validation (Director Recommended)

Assign TestAcceptanceEngineer one scoped validation task:

- use `/Users/concm/prod_workspace/Luceon2026/testpdf` as read-only sample source;
- inventory PDFs and choose one small/medium suitable PDF;
- run preflight health/admission/active-task checks first;
- upload exactly one PDF;
- observe task list/detail/page semantics until terminal state or clear failure;
- specifically check whether `log-observation-unreadable` stays diagnostic-only while MinerU API is processing/running;
- record terminal outcome, task/material/AI job ids, evidence, and screenshots/log excerpts if available.

Forbidden in this option:

- pressure/batch-concurrent/soak;
- second upload;
- failed-task repair, reparse, re-AI, cleanup, delete, rename, or historical mutation;
- destructive DB/MinIO/Docker volume/data operations;
- model pull/delete/replace or secret/config changes;
- broad restart/rollback;
- sample-file mutation;
- L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线 declaration.

Why recommended:

This is the smallest evidence-producing step that directly tests the defect class Task 101 was created to fix. It keeps the project moving without jumping back to pressure testing.

### Option B: Hold After Deployment

Do not run any upload validation now. Keep Task 102 as the latest accepted deployment/runtime-surface evidence and wait for manual observation or a later validation window.

Risk:

The code may be deployed correctly while the operator-facing task semantics remain unproven. This can leave the project stalled in a "healthy endpoints but uncertain task behavior" state.

### Option C: Skip To Pressure Or Broader Batch Validation

Not recommended.

Risk:

The project would mix a narrow MinerU observability verification with broader throughput questions. If anything fails, the evidence will be harder to interpret, and the root behavioral fix may remain ambiguous.

## Director Recommendation

Choose Option A.

If this decision item remains unanswered for two consecutive Director heartbeat/check-task cycles, Director may follow the standing no-long-term-blocker rule and issue a conservative, scoped TestAcceptanceEngineer task for Option A only if production preflight surfaces are still clean. The resulting task must preserve all forbidden-operation boundaries above and must not declare readiness.

## User Decision

- Decision time: 2026-05-14T05:21:59+0800
- User response: "同意 Option A，不进入压力测试。"
- Recorded decision: `USER_APPROVED_OPTION_A`

Director issued Task 104 to TestAcceptanceEngineer for exactly one controlled upload validation from `/Users/concm/prod_workspace/Luceon2026/testpdf`.

Explicitly not authorized:

- pressure, batch-concurrent, soak, broad stress, or long-run tests;
- second upload;
- failed-task repair, reparse, re-AI, cleanup, delete, rename, or historical mutation;
- destructive DB/MinIO/Docker volume/data operations;
- model pull/delete/replace, secret/config/env mutation, broad restart/rebuild/rollback;
- sample-file mutation;
- L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线 declaration.
