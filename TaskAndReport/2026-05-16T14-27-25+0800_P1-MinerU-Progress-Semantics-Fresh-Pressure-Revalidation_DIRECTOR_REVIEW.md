# P1 MinerU Progress Semantics Fresh Pressure Revalidation Director Review

Review timestamp: 2026-05-16T14:27:25+0800

Task ID: TASK-20260516-084828-P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation

Review result: `ACCEPTED_PROGRESS_SEMANTICS_BOUNDARY_WITH_RESIDUAL_AI_FAILURE_LOG_CHANNEL_HARDENING_REQUIRED`

Reviewed by: Director

## Reviewed Artifacts

- Task brief: `TaskAndReport/2026-05-16T08-48-28+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_TASK.md`
- Final report: `TaskAndReport/2026-05-16T08-48-28+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_REPORT.md`
- Supplemental reports:
  - `TaskAndReport/2026-05-16T08-55-06+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_SUPPLEMENTAL_REPORT.md`
  - `TaskAndReport/2026-05-16T09-02-28+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_SUPPLEMENTAL_REPORT.md`
  - `TaskAndReport/2026-05-16T11-07-20+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_SUPPLEMENTAL_REPORT.md`
  - `TaskAndReport/2026-05-16T13-07-20+0800_P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation_SUPPLEMENTAL_REPORT.md`
- Development HEAD after final report: `081f922`
- Production HEAD observed by report: `0598ca5`

## Director Spot-Check

Director performed read-only checks only:

- `git status --short --branch`: clean `main...origin/main`
- `git fetch origin && git pull --ff-only origin main`: already up to date
- Production `/__proxy/upload/ops/mineru/active-task`: no active/current/queued/drift/result-ingestion-lag/takeover work remained; historical AI failures included fresh `task-1778892903338`
- Production `/__proxy/upload/ops/mineru/admission-circuit`: circuit closed, parse/AI pending/running counts all 0, `activeTaskClean=true`
- Production `/__proxy/upload/ops/dependency-health?mineruSubmitProbe=false`: `ok=true`, `blocking=false`, `progressSnapshot.version=progress-snapshot-v0.1`, readiness-only `lagKind=dependency-health-readiness-only`
- Direct MinerU `/health`: healthy, queued 0, processing 0, completed 96, failed 0
- Read-only DB/API summary for fresh Task 205 records:
  - tasks: 24 total, 23 `review-pending/review`, 1 `failed/ai`
  - materials: 24 total, 23 `reviewing/completed/analyzed`, 1 `failed/completed/failed`
  - AI jobs: 24 total, 23 `review-pending`, 1 `failed`
  - failed item: `task-1778892903338`, material `2077680543704196`, MinerU completed, AI failure kind `strict-no-skeleton-fallback-block`, manual retry eligible

No submit-probe, upload, retry, reparse, re-AI, repair, cancel, reset, restart, rebuild, redeploy, DB/MinIO/Docker/model/config/sample mutation, or destructive operation was performed by Director review.

## Decision

Accepted for the Task 205 monitoring objective only.

The evidence supports that the deployed MinerU progress semantics are now materially usable for long-running active work:

- During active processing, `progressSnapshot.source=direct-mineru` and direct MinerU status prevented stale log-channel diagnostics from being misread as failure.
- Host MinerU logs showed forward progress at 08:55, 09:02, 11:07, and 13:07.
- Final backend state was clean for MinerU: no active, queued, drift, takeover, or ingestion-lag tasks remained, and direct MinerU reported 0 queued / 0 processing / 0 failed.
- The remaining terminal defect is not MinerU parse failure. It is one AI-stage failure after successful MinerU completion.

This review does **not** declare pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

## Residuals

1. Single AI-stage failure:
   - `task-1778892903338`
   - material `2077680543704196`
   - file `蓝月、血月、橙月？月亮为啥还会变色？.pdf`
   - failure kind `strict-no-skeleton-fallback-block`
   - underlying provider error: Ollama model runner unexpectedly stopped
   - manual retry eligible, but retry/re-AI is a production mutation and is not authorized by this review

2. Log-channel ownership/freshness remains incomplete:
   - the active progress semantics handled the stale container log-channel correctly,
   - but detailed human-readable progress still depended on host MinerU logs,
   - therefore MinerU log integration is improved but not fully closed.

## Follow-Up

Director issued Task 206 to DevelopmentEngineer for code-level MinerU log-channel ownership/freshness hardening.

The AI failed item remains a known residual/manual-retry candidate. A retry or re-AI action requires a separate scoped authorization and must not be performed under this review.

## Acceptance Boundary

Task 205 is closed as accepted for progress-semantics monitoring boundary with residuals.

No production readiness, pressure PASS, L3, release readiness, production上线, go-live, data repair, or AI retry is authorized.
