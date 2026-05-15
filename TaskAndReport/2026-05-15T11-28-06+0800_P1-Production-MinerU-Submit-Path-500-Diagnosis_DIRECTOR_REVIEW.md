# Director Review: P1 Production MinerU Submit-Path 500 Read-Only Diagnosis And Recovery Plan

- Task ID: `TASK-20260515-111251-P1-Production-MinerU-Submit-Path-500-Read-Only-Diagnosis-And-Recovery-Plan`
- Reviewed at: 2026-05-15T11:28:06+0800
- Reviewer: Director
- Reviewed report: `TaskAndReport/2026-05-15T11-12-51+0800_P1-Production-MinerU-Submit-Path-500-Read-Only-Diagnosis-And-Recovery-Plan_REPORT.md`
- Result: `ACCEPTED_DIAGNOSIS_USER_DECISION_REQUIRED`

## Summary

Director accepts the DevelopmentEngineer read-only diagnosis.

The accepted finding is that production currently has a live MinerU submit-path blocker:

- direct MinerU `/health` is healthy;
- upload-server can reach MinerU health;
- active-task diagnostics show no current parse queue or takeover work;
- admission circuit is open because the last authorized submit-probe returned HTTP `500`;
- the open circuit is not stale-only; code requires a later successful submit-probe to close;
- current MinerU log channels are stale, so production can detect the submit-path failure but cannot currently expose a useful stack trace for it.

The diagnosis classifies the primary condition as `MINERU_SUBMIT_API_BROKEN`, with `SERVICE_OWNERSHIP_OR_CONFIG_MISMATCH` as a secondary observability risk because the configured log channel is stale and sidecar is not observed.

## Director Spot Check

Director rechecked only non-mutating endpoints:

- `GET /__proxy/upload/health`: HTTP 200, `ok=true`.
- `GET /__proxy/upload/ops/dependency-health` without submit probe: HTTP 200, `ok=true`, `blocking=false`, MinerU health OK, Ollama `resident-chat-succeeded`.
- The same dependency response reports admission circuit `state=open`, `reason=mineru-submit-probe-HTTP 500`.
- `GET /__proxy/upload/ops/mineru/admission-circuit`: HTTP 200, `open=true`, last submit probe status `500`, error `HTTP 500: Internal Server Error`.
- `GET /__proxy/upload/ops/mineru/active-task`: HTTP 200, no active task; historical AI failure count remains visible.
- Direct MinerU `/health`: HTTP 200, `status=healthy`, no queued/processing/failed tasks.

Director did not run submit-probe, upload, close/reset circuit, restart, recovery, deploy, rollback, cleanup, retry, reparse, re-AI, or any production mutation.

## Accepted Risk Framing

This blocks release-boundary progression. It does not mean the whole system is broken, but it does mean the current production PDF/MinerU intake path is not ready.

The next meaningful step requires owner approval because the recommended recovery path mutates runtime state and then performs exactly one submit-path verification.

## Decision Required

Director records Task 172 as a user decision.

Recommended option: authorize a narrowly scoped MinerU-only recovery:

1. Confirm active-task diagnostics are clean.
2. Capture current process/listener/log state.
3. Restart or relaunch only the host MinerU API session/process.
4. Verify direct MinerU `/health`.
5. Run exactly one authorized dependency-health submit-probe.
6. Do not upload files.
7. Stop and report, whether the circuit closes or remains open.

## Boundaries

This review does not authorize the recovery itself.

No pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness is declared.

No submit-probe retry, upload, close/reset circuit, restart/stop/kill/attach/start services, deploy/rebuild/rollback/pull production, cleanup/cancel/repair/retry/reparse/re-AI, DB/MinIO/Docker volume/data mutation, restore/import, config/secret/model/sample mutation, skeleton fallback weakening, or readiness claim was performed.
