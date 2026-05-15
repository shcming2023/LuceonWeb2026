# Director Review: P1 Manual Clean 24-PDF Pressure Monitoring

- Review time: 2026-05-16T06:01:21+0800
- Reviewed task: `TASK-20260515-202908-P1-Manual-Clean-24-PDF-Pressure-Monitoring`
- Reviewed report: `TaskAndReport/2026-05-15T20-29-08+0800_P1-Manual-Clean-24-PDF-Pressure-Monitoring_REPORT.md`
- Reviewer: Director
- Result: `ACCEPTED_TERMINAL_PRESSURE_EVIDENCE_WITH_AI_RESIDUAL_AND_OBSERVABILITY_FOLLOWUP_REQUIRED`

## Evidence Reviewed

The TestAcceptanceEngineer report confirms the task was executed from the Director task brief and stayed read-only:

- no extra upload;
- no reset/cleanup;
- no manual MinerU submit-probe;
- no retry/reparse/re-AI;
- no cancel/repair;
- no service restart/rebuild/redeploy;
- no DB/MinIO/Docker/config/secret/model/sample mutation;
- no pressure PASS, L3, release-readiness, production-readiness, or go-live claim.

Reported terminal state:

- 24 observed pressure-window tasks;
- 23 `review-pending/review`;
- 1 `failed/ai`;
- 24 material `mineruStatus=completed`;
- 23 material `aiStatus=analyzed`;
- 1 material `aiStatus=failed`;
- 0 active/running/queued/AI-pending pressure tasks at final snapshot;
- direct MinerU final health healthy with queued 0 / processing 0 / completed 48 / failed 0;
- admission circuit closed;
- dependency-health without submit-probe ok and non-blocking.

The residual failed item is:

- task `task-1778848110965`;
- material `1161333216880605`;
- file `Cambridge IGCSE(0607) International Mathematics Coursebook Extended_2018(Haese Mathematics).pdf`;
- final state/stage `failed/ai`;
- MinerU task `3e6a4a27-1066-4ddf-bc7f-2e71cd9b1df1`;
- material MinerU status `completed`;
- AI job `ai-job-1778854627880-0a6f`;
- failure class: strict no-skeleton-fallback block after Ollama timeout.

## Director Spot-Checks

Director spot-checks matched the report:

- `/__proxy/db/tasks`: 23 `review-pending/review`, 1 `failed/ai`;
- `/__proxy/db/materials`: 23 `completed/analyzed`, 1 `completed/failed`;
- `/__proxy/db/ai-metadata-jobs`: 23 `review-pending`, 1 `failed`;
- direct MinerU `/health`: healthy, queued 0, processing 0, completed 48, failed 0;
- dependency-health no-submit: `ok=true`, `blocking=false`, MinerU ok, Ollama readiness `resident-chat-succeeded`;
- admission circuit: closed, parse/AI pending/running all 0;
- active-task diagnostics: no active/current/queued/takeover tasks; 1 historical AI failure retained;
- log-channel ownership: selected configured stderr source contains business progress but is now stale after the terminal run; sidecar not observed.

## Judgment

Accepted as terminal pressure-monitoring evidence with residuals.

This evidence supports:

- the manually started clean 24-PDF pressure run reached terminal observed state;
- MinerU completed all 24 pressure-window materials;
- large and small PDFs both reached review-pending outputs;
- the remaining failure is isolated to AI recognition after MinerU completion;
- the system was observable enough to reconstruct progress and final state with backend/API/log evidence.

This evidence does not support:

- pressure PASS;
- L3;
- release readiness;
- production readiness;
- production上线;
- go-live;
- claim that operator-facing progress semantics are fully adequate.

## Residuals

1. Operator-facing progress semantics remain weaker than backend evidence during long-running work.
   - UI and active-task wording can lag direct MinerU API/log progress.
   - Dependency-health no-submit may time out during active heavy work while direct MinerU is still progressing.
   - Log-channel state becomes `stale` after terminal/idle state and sidecar is not observed.

2. One isolated AI-stage residual failure remains.
   - It is not a MinerU or parse failure.
   - It should be treated as a visible manual retry/review candidate, not as whole-run system failure.

## Next Action

Director issued a scoped DevelopmentEngineer follow-up:

- `TASK-20260516-060121-P1-Pressure-Progress-Semantics-And-AI-Residual-Visibility-Hardening`

That task is code/test level only. It must improve operator-facing progress semantics and residual AI-failure visibility without retrying/reparsing/re-AIing existing tasks and without mutating production.

