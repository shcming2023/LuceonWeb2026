# Director Review: P1 MinerU-Only Recovery And Submit-Path Verification

- Task ID: `TASK-20260515-113628-P1-MinerU-Only-Recovery-And-Submit-Path-Verification`
- Reviewed report: `TaskAndReport/2026-05-15T11-36-28+0800_P1-MinerU-Only-Recovery-And-Submit-Path-Verification_REPORT.md`
- Review time: 2026-05-15T11:47:04+0800
- Reviewer: `Director`
- Result: `ACCEPTED_RECOVERED_SUBMIT_PATH_RUNTIME_ONLY`

## Judgment

Accepted.

DevelopmentEngineer stayed inside the user-approved Option A boundary: confirm idle, restart/relaunch only the host MinerU API, run exactly one authorized submit-path probe, and report. The reported evidence and Director read-only spot-check support that the production MinerU submit path recovered and the durable admission circuit is currently closed.

This acceptance is runtime recovery evidence only. It is not PDF upload validation, pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live approval.

## Evidence Reviewed

- Pre-recovery active-task diagnostics were clean: no active parse task, no queued parse work, no takeover-required work.
- Direct MinerU `/health` was healthy before recovery, but durable admission circuit was open because the previous submit-probe returned HTTP `500`.
- Process ownership was clear enough for a MinerU-only action: one `tmux` session `mineru_api` owned the listener on port `8083`.
- Recovery action was scoped to:
  - `tmux kill-session -t mineru_api`;
  - relaunch via `bash ops/start-mineru-api.sh` from the production workspace.
- No Docker, DB, MinIO, upload-server, frontend, Ollama, supervisor, sidecar, model, config, secret, sample, data, deploy, rollback, cleanup, repair, retry, reparse, or re-AI mutation was performed.
- Exactly one authorized submit-probe returned HTTP `202`:
  - MinerU task id: `f7e76bf6-579f-49d0-a15d-46b7b854762f`;
  - duration: `25ms`;
  - error: `null`.
- The synthetic probe task later reached `status="completed"`, `error=null`.
- Admission circuit closed through the successful submit-probe, not by manual reset.

Director read-only spot-check after the report confirmed:

- upload health: `ok=true`;
- dependency-health without submit-probe: `ok=true`, `blocking=false`;
- MinerU admission circuit endpoint: `open=false`, `state="closed"`;
- active-task diagnostics: no active/current/queued/takeover-required work;
- direct MinerU `/health`: `status="healthy"`, `queued_tasks=0`, `processing_tasks=0`, `completed_tasks=1`, `failed_tasks=0`.

## Remaining Boundaries

- New PDF/non-Markdown intake is no longer blocked by the admission circuit at the time of review.
- This did not validate a real PDF upload after recovery.
- Historical `failed/ai` tasks remain visible and are not hidden, repaired, retried, or counted as successful.
- The recovery fixed the live symptom by restarting the host MinerU API; if submit-path HTTP `500` recurs, it remains a reliability signal requiring follow-up.
- Task 170 exposed an engineering hygiene problem: `ops/runtime-ownership-status.sh` is treated as a status helper but currently runs a side-effecting MinerU submit-probe by default. That must be corrected before future read-only evidence tasks rely on it.

## Next Step

Issue a scoped DevelopmentEngineer hardening task:

- make `ops/runtime-ownership-status.sh` no-submit/read-only by default;
- require explicit opt-in for the MinerU submit-probe;
- clarify submit-probe/admission wording and documentation so future role threads do not confuse health reads with side-effecting verification.

No upload, pressure/batch/soak/fresh serial validation, production deployment, broad restart, Docker/DB/MinIO/Ollama mutation, failed-task repair, retry/reparse/re-AI, model/config/secret/sample mutation, or readiness claim is authorized by this review.
